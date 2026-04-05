"""
教学视频配音：用 Edge TTS 按讲解脚本生成音频，与即梦视频用 ffmpeg 合成有声版，并保存到 storage。
"""
import asyncio
import math
import os
import subprocess
from pathlib import Path
from typing import Optional
import textwrap

import aiofiles
import httpx
from config import config
from PIL import Image, ImageDraw, ImageFont

from utils.tts import text_to_speech
from utils.tts import _find_ffmpeg


# 教学讲解默认优先使用更自然的中文神经语音。
TEACHING_VOICE_ZH = "zh-CN-XiaoxiaoNeural"

SLIDE_DURATION_SEC = 60
VIDEO_SIZE = (1280, 720)


def _teaching_font_path() -> str:
    project_root = Path(__file__).resolve().parents[2]
    windir = os.environ.get("WINDIR", "C:/Windows")
    candidates = [
        str(project_root / "assets" / "fonts" / "NotoSans.ttf"),
        str(project_root / "assets" / "fonts" / "Inter.ttf"),
        str(project_root / "assets" / "fonts" / "Lexend.ttf"),
        str(Path(windir) / "Fonts" / "msyh.ttc"),
        str(Path(windir) / "Fonts" / "msyh.ttf"),
        str(Path(windir) / "Fonts" / "simhei.ttf"),
        str(Path(windir) / "Fonts" / "simsun.ttc"),
        str(Path(windir) / "Fonts" / "arial.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"no suitable font found for teaching video slides (tried {len(candidates)} candidates)")


def _wrap_lines(text: str, width: int, limit: int) -> list[str]:
    content = (text or "").replace("\r", "").strip()
    if not content:
        return []
    wrapped = textwrap.wrap(content, width=width, break_long_words=False, break_on_hyphens=False)
    return wrapped[:limit]


def _script_sentences(script: str) -> list[str]:
    raw = [part.strip() for part in __import__("re").split(r"[。！？!?；;\n]+", script or "") if part.strip()]
    return [part for part in raw if len(part) >= 4]


def _slide_specs(title: str, script: str) -> list[dict]:
    sentences = _script_sentences(script)
    bullets = sentences[:3] or ["围绕主题建立知识框架", "结合课堂讲解提炼关键概念", "用简洁结构帮助学生理解重点"]
    middle = max(2, math.ceil(len(sentences) / 3)) if sentences else 2
    chunk_a = "。".join(sentences[:middle]) or "从整体概念入手，帮助学生先建立认知地图。"
    chunk_b = "。".join(sentences[middle: middle * 2]) or "再围绕核心规律、结构与关系展开讲解，强化课堂理解。"
    chunk_c = "。".join(sentences[middle * 2:]) or "最后回到应用与总结，让学生知道这一知识点如何被真正用起来。"
    return [
        {
            "eyebrow": "AI Teaching Video",
            "heading": title or "智能微课",
            "body": "这是一段自动生成的课堂讲解视频，已将脚本内容整理为适合观看的微课画面。",
            "chips": bullets,
            "tone": ("#0f172a", "#1d4ed8"),
        },
        {
            "eyebrow": "Part 01",
            "heading": "知识框架",
            "body": chunk_a,
            "chips": bullets[:2],
            "tone": ("#0f172a", "#2563eb"),
        },
        {
            "eyebrow": "Part 02",
            "heading": "核心讲解",
            "body": chunk_b,
            "chips": bullets[1:] or bullets,
            "tone": ("#1e1b4b", "#6d28d9"),
        },
        {
            "eyebrow": "Part 03",
            "heading": "课堂总结",
            "body": chunk_c,
            "chips": [title or "课程主题", "关键概念回顾", "课后继续巩固"],
            "tone": ("#082f49", "#0891b2"),
        },
    ]


def _draw_gradient_background(width: int, height: int, start_hex: str, end_hex: str) -> Image.Image:
    start = tuple(int(start_hex[i:i + 2], 16) for i in (1, 3, 5))
    end = tuple(int(end_hex[i:i + 2], 16) for i in (1, 3, 5))
    image = Image.new("RGBA", (width, height), start + (255,))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(int(start[idx] + (end[idx] - start[idx]) * ratio) for idx in range(3))
        draw.line([(0, y), (width, y)], fill=color + (255,))
    return image


def _render_slide(slide_path: Path, title: str, spec: dict) -> None:
    width, height = VIDEO_SIZE
    image = _draw_gradient_background(width, height, spec["tone"][0], spec["tone"][1])
    draw = ImageDraw.Draw(image, "RGBA")
    font_path = _teaching_font_path()
    eyebrow_font = ImageFont.truetype(font_path, 26)
    title_font = ImageFont.truetype(font_path, 64)
    heading_font = ImageFont.truetype(font_path, 46)
    body_font = ImageFont.truetype(font_path, 28)
    chip_font = ImageFont.truetype(font_path, 24)

    draw.ellipse((width - 300, 40, width - 60, 280), fill=(255, 255, 255, 26))
    draw.ellipse((60, height - 260, 320, height - 40), fill=(255, 255, 255, 18))
    draw.rounded_rectangle((64, 68, width - 64, height - 68), radius=40, fill=(6, 10, 24, 86), outline=(255, 255, 255, 36), width=2)
    draw.text((108, 112), spec["eyebrow"], font=eyebrow_font, fill=(191, 219, 254, 255))
    draw.text((108, 154), title or "智能微课", font=title_font, fill=(255, 255, 255, 255))
    draw.text((108, 246), spec["heading"], font=heading_font, fill=(224, 231, 255, 255))

    body_lines = _wrap_lines(spec["body"], width=24, limit=7)
    body_y = 320
    for line in body_lines:
        draw.text((108, body_y), line, font=body_font, fill=(226, 232, 240, 255))
        body_y += 40

    chip_y = height - 156
    chip_x = 108
    for chip in spec.get("chips", [])[:3]:
        label = chip[:26]
        text_width = draw.textbbox((0, 0), label, font=chip_font)[2]
        chip_w = text_width + 42
        draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + 46), radius=22, fill=(255, 255, 255, 34), outline=(255, 255, 255, 54), width=1)
        draw.text((chip_x + 20, chip_y + 11), label, font=chip_font, fill=(248, 250, 252, 255))
        chip_x += chip_w + 14

    footer = "LinkEdu AI Micro Lesson"
    footer_width = draw.textbbox((0, 0), footer, font=chip_font)[2]
    draw.text((width - footer_width - 110, height - 120), footer, font=chip_font, fill=(191, 219, 254, 230))
    slide_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(slide_path, "PNG")


def _build_teaching_slideshow_sync(video_id: str, title: str, script: str, audio_path: Path, ffmpeg_path: str) -> Optional[str]:
    base = config.storage_dir / "teaching_videos" / video_id
    slides_dir = base / "slides"
    slideshow_video = base / "slideshow.mp4"
    output_video = base / "video_with_audio.mp4"
    concat_file = base / "slides.txt"

    specs = _slide_specs(title, script)
    slide_paths: list[Path] = []
    for index, spec in enumerate(specs):
        slide_path = slides_dir / f"slide_{index:02d}.png"
        _render_slide(slide_path, title, spec)
        slide_paths.append(slide_path)

    concat_lines: list[str] = []
    for slide_path in slide_paths:
        concat_lines.append(f"file '{slide_path.as_posix()}'")
        concat_lines.append(f"duration {SLIDE_DURATION_SEC}")
    if slide_paths:
        concat_lines.append(f"file '{slide_paths[-1].as_posix()}'")
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")

    create_cmd = [
        ffmpeg_path,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-vf", "fps=24,format=yuv420p",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(slideshow_video),
    ]
    merge_cmd = [
        ffmpeg_path,
        "-y",
        "-i", str(slideshow_video),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        str(output_video),
    ]

    try:
        first = subprocess.run(create_cmd, capture_output=True, timeout=300)
        if first.returncode != 0 or not slideshow_video.exists():
            print(f"[teaching_video_audio] slideshow create failed: {(first.stderr or b'').decode(errors='replace')[:500]}")
            return None
        second = subprocess.run(merge_cmd, capture_output=True, timeout=300)
        if second.returncode != 0 or not output_video.exists():
            print(f"[teaching_video_audio] slideshow merge failed: {(second.stderr or b'').decode(errors='replace')[:500]}")
            return None
    except Exception as exc:
        print(f"[teaching_video_audio] slideshow build error: {exc}")
        return None

    rel = output_video.relative_to(config.storage_dir)
    return str(rel).replace("\\", "/")


async def download_video(url: str, dest_path: Path) -> None:
    """将远程视频下载到本地文件"""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("GET", url) as r:
            if r.status_code != 200:
                raise RuntimeError(f"download failed: {r.status_code}")
            async with aiofiles.open(dest_path, "wb") as f:
                async for chunk in r.aiter_bytes(chunk_size=65536):
                    await f.write(chunk)


def _merge_video_audio_sync(
    video_path: str,
    audio_path: str,
    output_path: str,
    ffmpeg_path: str,
) -> bool:
    """同步：将视频与音频合成，以音频时长为准，视频不足时循环。"""
    cmd = [
        ffmpeg_path,
        "-y",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


async def build_teaching_audio(
    video_id: str,
    script: str,
) -> Optional[str]:
    """
    根据脚本生成教学讲解音频，保存到 storage/teaching_videos/{video_id}/audio.mp3。
    返回相对 storage_dir 的路径，失败返回 None。
    """
    if not script or not script.strip():
        return None
    base = config.storage_dir / "teaching_videos" / video_id
    base.mkdir(parents=True, exist_ok=True)
    audio_path = base / "audio.mp3"
    if audio_path.exists() and audio_path.stat().st_size > 0:
        rel = audio_path.relative_to(config.storage_dir)
        return str(rel).replace("\\", "/")

    try:
        actual_audio_path = await text_to_speech(
            [{"text": script.strip(), "voice": config.tts_voice_edge or TEACHING_VOICE_ZH}],
            str(audio_path),
        )
    except Exception as e:
        print(f"[teaching_video_audio] TTS failed: {e}")
        return None

    audio_path = Path(actual_audio_path)
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        return None
    rel = audio_path.relative_to(config.storage_dir)
    return str(rel).replace("\\", "/")


async def add_audio_to_teaching_video(
    video_id: str,
    video_url: str,
    script: str,
) -> Optional[str]:
    """
    下载即梦视频，用 Edge TTS 根据 script 生成音频，合成有声版并保存到 storage/teaching_videos/{video_id}/。
    返回相对路径，如 teaching_videos/{video_id}/video_with_audio.mp4，失败返回 None。
    """
    if not script or not script.strip():
        return None
    base = config.storage_dir / "teaching_videos" / video_id
    base.mkdir(parents=True, exist_ok=True)
    video_silent = base / "video_silent.mp4"
    audio_path = base / "audio.mp3"
    video_with_audio = base / "video_with_audio.mp4"

    try:
        await download_video(video_url, video_silent)
    except Exception as e:
        print(f"[teaching_video_audio] download failed: {e}")
        return None

    audio_rel = await build_teaching_audio(video_id, script)
    if not audio_rel:
        return None
    audio_path = config.storage_dir / audio_rel

    ffmpeg_path = _find_ffmpeg()
    if not ffmpeg_path:
        print("[teaching_video_audio] ffmpeg not found, skip local video merge")
        return None
    ok = await asyncio.to_thread(
        _merge_video_audio_sync,
        str(video_silent),
        str(audio_path),
        str(video_with_audio),
        ffmpeg_path,
    )
    if not ok or not video_with_audio.exists():
        print("[teaching_video_audio] ffmpeg merge failed")
        return None

    # 返回相对 storage_dir 的路径，便于拼接 /storage/...
    rel = video_with_audio.relative_to(config.storage_dir)
    return str(rel).replace("\\", "/")


async def cache_remote_teaching_video(
    video_id: str,
    video_url: str,
    *,
    filename: str = "video_with_audio.mp4",
) -> Optional[str]:
    """
    将远程已带音频的视频保存到本地 storage/teaching_videos/{video_id}/。
    适用于知识点视频生成智能体这类已返回完整成片的 provider。
    """
    if not video_url or not video_url.strip():
        return None
    base = config.storage_dir / "teaching_videos" / video_id
    base.mkdir(parents=True, exist_ok=True)
    output_path = base / filename
    try:
        await download_video(video_url, output_path)
    except Exception as e:
        print(f"[teaching_video_audio] cache remote video failed: {e}")
        return None
    if not output_path.exists() or output_path.stat().st_size == 0:
        return None
    rel = output_path.relative_to(config.storage_dir)
    return str(rel).replace("\\", "/")


async def build_teaching_slideshow_video(
    video_id: str,
    title: str,
    script: str,
) -> Optional[str]:
    """
    当远程视频服务不可用时，使用脚本与配音本地生成一个教学微课 MP4。
    """
    if not script or not script.strip():
        return None
    ffmpeg_path = _find_ffmpeg()
    if not ffmpeg_path:
        print("[teaching_video_audio] ffmpeg not found, skip slideshow fallback")
        return None
    audio_rel = await build_teaching_audio(video_id, script)
    if not audio_rel:
        return None
    audio_path = config.storage_dir / audio_rel
    return await asyncio.to_thread(
        _build_teaching_slideshow_sync,
        video_id,
        title,
        script,
        audio_path,
        ffmpeg_path,
    )
