"""
TTS (Text-to-Speech) 工具模块
支持 Edge TTS, ElevenLabs, Google TTS
音频拼接: 优先使用 ffmpeg，回退到 pydub 纯 Python 方案
"""
import asyncio
import subprocess
import re
import sys
import shutil
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
import aiofiles

from config import config


def _find_ffmpeg() -> Optional[str]:
    """查找 ffmpeg 可执行文件路径"""
    custom = config.ffmpeg_path
    if custom:
        custom_path = Path(custom)
        if custom_path.exists():
            if custom_path.is_dir():
                for name in ("ffmpeg.exe", "ffmpeg"):
                    candidate = custom_path / name
                    if candidate.exists():
                        return str(candidate)
            return str(custom_path)
        # 兼容仅配置可执行名时的场景
        looked_up = shutil.which(custom)
        if looked_up:
            return looked_up
    common_paths = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files (x86)/ffmpeg/bin/ffmpeg.exe"),
        Path("/opt/homebrew/bin/ffmpeg"),
        Path("/opt/homebrew/opt/ffmpeg/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
    ]
    try:
        local_appdata = Path(__import__("os").environ.get("LOCALAPPDATA", ""))
        if local_appdata:
            common_paths.extend([
                local_appdata / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-7.1-full_build" / "bin" / "ffmpeg.exe",
                local_appdata / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
            ])
    except Exception:
        pass
    for candidate in common_paths:
        if candidate.exists():
            return str(candidate)
    cellar_root = Path("/opt/homebrew/Cellar/ffmpeg")
    if cellar_root.exists():
        versions = sorted(cellar_root.iterdir(), reverse=True)
        for version_dir in versions:
            candidate = version_dir / "bin" / "ffmpeg"
            if candidate.exists():
                return str(candidate)
    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and Path(bundled).exists():
            return bundled
    except Exception:
        pass
    found = shutil.which("ffmpeg")
    if found:
        return found
    return None


async def _emit(emit_callback: Optional[Callable], payload: Dict[str, Any]) -> None:
    if not emit_callback:
        return
    try:
        result = emit_callback(payload)
        if asyncio.iscoroutine(result):
            await result
    except Exception:
        return


async def text_to_speech(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """
    将文本转换为语音并拼接成单个音频文件

    Args:
        segments: 音频段列表，每个包含 "text" 和可选的 "voice"
        output_path: 输出音频文件路径
        emit_callback: 可选的进度回调函数

    Returns:
        生成的音频文件路径
    """
    provider = config.tts_provider.lower()

    print(f"[tts] start provider={provider} segments={len(segments)} output={output_path}")
    try:
        if provider == "edge":
            return await _synthesize_edge(segments, output_path, emit_callback)
        elif provider == "eleven":
            return await _synthesize_eleven(segments, output_path, emit_callback)
        elif provider == "google":
            return await _synthesize_google(segments, output_path, emit_callback)
        else:
            # 默认使用 Edge TTS
            return await _synthesize_edge(segments, output_path, emit_callback)
    except Exception as e:
        msg = str(e).strip() or repr(e)
        print(f"[tts] failed provider={provider} error={msg}")
        fallback = await _synthesize_system_fallback(segments, output_path, emit_callback)
        if fallback:
            print(f"[tts] system fallback ok output={fallback}")
            return fallback
        raise Exception(f"TTS {provider} failed: {msg}")


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text or "")


@lru_cache(maxsize=1)
def _macos_voices() -> List[str]:
    if sys.platform != "darwin":
        return []
    say_bin = shutil.which("say")
    if not say_bin:
        return []
    try:
        result = subprocess.run(
            [say_bin, "-v", "?"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    voices: List[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        voice = line.split()[0]
        if voice:
            voices.append(voice)
    return voices


def _pick_macos_voice(text: str) -> Optional[str]:
    voices = _macos_voices()
    if not voices:
        return None
    preferred = (
        ["Tingting", "Meijia", "Sin-ji", "Li-mu", "Yu-shu"]
        if _has_cjk(text)
        else ["Samantha", "Ava", "Allison", "Alex", "Daniel"]
    )
    for voice in preferred:
        if voice in voices:
            return voice
    return voices[0]


def _macos_afconvert_args(output_path: str) -> Optional[List[str]]:
    suffix = Path(output_path).suffix.lower()
    if suffix in {".m4a", ".mp4"}:
        return ["-f", "m4af", "-d", "aac"]
    if suffix == ".wav":
        return ["-f", "WAVE", "-d", "LEI16"]
    return None


def _synthesize_macos_say_sync(
    segments: List[Dict[str, str]],
    output_path: str,
) -> Optional[str]:
    if sys.platform != "darwin":
        return None
    say_bin = shutil.which("say")
    afconvert_bin = shutil.which("afconvert")
    if not say_bin or not afconvert_bin:
        return None

    combined = "\n".join(
        (seg.get("text") or "").strip()
        for seg in segments
        if (seg.get("text") or "").strip()
    ).strip()
    if not combined:
        raise Exception("No text to synthesize")

    requested_output = Path(output_path)
    actual_output = requested_output
    if requested_output.suffix.lower() == ".mp3":
        actual_output = requested_output.with_suffix(".m4a")
    actual_output.parent.mkdir(parents=True, exist_ok=True)
    temp_aiff = actual_output.parent / f"{actual_output.stem}_fallback.aiff"
    voice = _pick_macos_voice(combined)
    say_cmd = [say_bin]
    if voice:
        say_cmd.extend(["-v", voice])
    say_cmd.extend(["-o", str(temp_aiff), combined])

    try:
        say_result = subprocess.run(say_cmd, capture_output=True, timeout=240)
        if say_result.returncode != 0 or not temp_aiff.exists():
            err = say_result.stderr.decode(errors="replace") if say_result.stderr else "macOS say failed"
            raise Exception(err)

        af_args = _macos_afconvert_args(str(actual_output))
        if not af_args:
            temp_aiff.replace(actual_output)
            return str(actual_output)

        convert_cmd = [afconvert_bin, str(temp_aiff), "-o", str(actual_output), *af_args]
        convert_result = subprocess.run(convert_cmd, capture_output=True, timeout=240)
        if convert_result.returncode != 0 or not actual_output.exists():
            err = convert_result.stderr.decode(errors="replace") if convert_result.stderr else "afconvert failed"
            raise Exception(err)
        return str(actual_output)
    finally:
        try:
            if temp_aiff.exists():
                temp_aiff.unlink()
        except Exception:
            pass


async def _synthesize_system_fallback(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> Optional[str]:
    if sys.platform != "darwin":
        return None
    try:
        await _emit(emit_callback, {"type": "audio_progress", "i": 0, "len": max(1, len(segments))})
        result = await asyncio.to_thread(_synthesize_macos_say_sync, segments, output_path)
        await _emit(emit_callback, {"type": "audio_progress", "i": max(1, len(segments)), "len": max(1, len(segments))})
        return result
    except Exception as e:
        print(f"[tts] system fallback failed: {e}")
        return None


async def _synthesize_edge(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 Edge TTS 合成音频"""
    try:
        return await _synthesize_edge_async(segments, output_path, emit_callback)
    except NotImplementedError as e:
        print(f"[tts] edge NotImplementedError, falling back to CLI: {e}")
        return await _synthesize_edge_cli(segments, output_path, emit_callback)


async def _synthesize_edge_async(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 Edge TTS 合成音频（async 实现）"""
    try:
        import edge_tts
    except Exception as e:
        raise Exception(f"edge_tts not available: {e}")

    voice_a = config.tts_voice_edge or "en-US-AvaNeural"
    voice_b = config.tts_voice_alt_edge or "en-US-AndrewNeural"

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成临时音频文件
    temp_files = []

    for i, seg in enumerate(segments):
        voice = seg.get("voice") or (voice_b if i % 2 else voice_a)
        text = seg.get("text", "")
        if not text.strip():
            print(f"[tts] edge empty text segment={i}")

        temp_file = output_dir / f"segment_{i}.mp3"

        # 重试逻辑
        max_retries = 3
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(temp_file))

                # 验证文件不为空
                if temp_file.stat().st_size > 0:
                    break
                else:
                    raise Exception("Generated file is empty")

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = min(1000 * (2 ** attempt), 5000)  # 指数退避
                    await asyncio.sleep(wait_time / 1000)
                else:
                    raise Exception(f"Failed to convert segment {i} after {max_retries} attempts: {e}")

        temp_files.append(str(temp_file))
        await _emit(emit_callback, {"type": "audio_progress", "i": i, "len": len(segments)})

    # 使用 ffmpeg 拼接音频
    await _concatenate_audio(temp_files, output_path, emit_callback)
    print(f"[tts] edge concat done files={len(temp_files)} output={output_path}")

    # 清理临时文件
    for temp_file in temp_files:
        try:
            Path(temp_file).unlink()
        except Exception:
            pass

    return output_path


def _synthesize_edge_cli_sync(
    segments: List[Dict[str, str]],
    output_path: str,
) -> List[str]:
    """
    使用 edge-tts CLI 合成音频（纯同步，在线程中运行）
    返回临时文件列表
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    voice_a = config.tts_voice_edge or "en-US-AvaNeural"
    voice_b = config.tts_voice_alt_edge or "en-US-AndrewNeural"

    temp_files = []

    for i, seg in enumerate(segments):
        voice = seg.get("voice") or (voice_b if i % 2 else voice_a)
        text = seg.get("text", "")
        if not text.strip():
            print(f"[tts] edge cli empty text segment={i}")
            continue

        temp_file = output_dir / f"segment_{i}.mp3"
        text_file = output_dir / f"segment_{i}.txt"

        # 同步写入文本文件
        text_file.write_text(text, encoding="utf-8")

        cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            "--text-file", str(text_file),
            "--write-media", str(temp_file),
        ]
        print(f"[tts] edge cli segment={i}/{len(segments)} voice={voice}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            print(f"[tts] edge cli timeout segment={i}")
            raise Exception(f"edge-tts cli timeout on segment {i}")

        if result.returncode != 0:
            err = result.stderr.decode(errors="replace") if result.stderr else "unknown error"
            print(f"[tts] edge cli failed segment={i} code={result.returncode} err={err}")
            raise Exception(f"edge-tts cli failed (code {result.returncode}): {err}")

        if not temp_file.exists() or temp_file.stat().st_size == 0:
            raise Exception(f"edge-tts cli empty output for segment {i}")

        print(f"[tts] edge cli segment={i} ok size={temp_file.stat().st_size}")
        temp_files.append(str(temp_file))

    if not temp_files:
        raise Exception("edge-tts cli produced no audio files")

    return temp_files


async def _synthesize_edge_cli(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 edge-tts CLI 合成音频（Windows 兼容回退 — subprocess.run 在线程中执行）"""
    print(f"[tts] edge cli start segments={len(segments)}")

    # 在线程池中运行同步子进程，彻底绕过事件循环 subprocess 限制
    temp_files = await asyncio.to_thread(
        _synthesize_edge_cli_sync, segments, output_path,
    )

    # 拼接音频
    await _concatenate_audio(temp_files, output_path, emit_callback)
    print(f"[tts] edge cli concat done files={len(temp_files)} output={output_path}")

    # 清理临时文件
    output_dir = Path(output_path).parent
    for temp_file in temp_files:
        try:
            Path(temp_file).unlink()
        except Exception:
            pass
    for i in range(len(segments)):
        try:
            (output_dir / f"segment_{i}.txt").unlink()
        except Exception:
            pass

    return output_path


async def _synthesize_eleven(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 ElevenLabs 合成音频"""
    import httpx

    if not config.eleven_api_key:
        raise ValueError("ELEVEN_API_KEY not set")

    voice_a = config.eleven_voice_a
    voice_b = config.eleven_voice_b or voice_a

    if not voice_a:
        raise ValueError("ELEVEN_VOICE_A not set")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, seg in enumerate(segments):
            voice = seg.get("voice") or (voice_b if i % 2 else voice_a)
            text = seg.get("text", "")

            temp_file = output_dir / f"segment_{i}.mp3"

            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                headers={
                    "xi-api-key": config.eleven_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
                },
            )

            if response.status_code != 200:
                raise Exception(f"ElevenLabs API error: {response.status_code}")

            async with aiofiles.open(temp_file, "wb") as f:
                await f.write(response.content)

            temp_files.append(str(temp_file))

            await _emit(emit_callback, {"type": "audio_progress", "i": i, "len": len(segments)})

    # 使用 ffmpeg 拼接音频
    await _concatenate_audio(temp_files, output_path, emit_callback)

    # 清理临时文件
    for temp_file in temp_files:
        try:
            Path(temp_file).unlink()
        except Exception:
            pass

    return output_path


async def _synthesize_google(
    segments: List[Dict[str, str]],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 Google TTS 合成音频"""
    from google.cloud import texttospeech

    if not config.google_credentials:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")

    client = texttospeech.TextToSpeechClient()

    voice_a = config.tts_voice_google or "en-US-Neural2-F"
    voice_b = config.tts_voice_alt_google or "en-US-Neural2-D"

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []

    for i, seg in enumerate(segments):
        voice = seg.get("voice") or (voice_b if i % 2 else voice_a)
        text = seg.get("text", "")

        temp_file = output_dir / f"segment_{i}.mp3"

        # 提取语言代码
        lang_code = "-".join(voice.split("-")[:2])

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )

        async with aiofiles.open(temp_file, "wb") as f:
            await f.write(response.audio_content)

        temp_files.append(str(temp_file))

        await _emit(emit_callback, {"type": "audio_progress", "i": i, "len": len(segments)})

    # 使用 ffmpeg 拼接音频
    await _concatenate_audio(temp_files, output_path, emit_callback)

    # 清理临时文件
    for temp_file in temp_files:
        try:
            Path(temp_file).unlink()
        except Exception:
            pass

    return output_path


async def _concatenate_audio(
    input_files: List[str],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 ffmpeg 或 pydub 拼接音频文件"""
    if not input_files:
        raise Exception("No audio files to concatenate")

    # 如果只有一个文件，直接复制
    if len(input_files) == 1:
        import shutil as _shutil
        _shutil.copy2(input_files[0], output_path)
        return output_path

    ffmpeg_path = _find_ffmpeg()

    if ffmpeg_path:
        return await _concatenate_with_ffmpeg(input_files, output_path, ffmpeg_path, emit_callback)
    else:
        print("[tts] ffmpeg not found, falling back to pydub for audio concatenation")
        return await _concatenate_with_pydub(input_files, output_path, emit_callback)


def _concatenate_ffmpeg_sync(
    input_files: List[str],
    output_path: str,
    ffmpeg_path: str,
) -> bool:
    """同步 ffmpeg 拼接（在线程中运行），成功返回 True"""
    output_dir = Path(output_path).parent
    list_file = output_dir / "list.txt"

    # 创建文件列表 - 使用正斜杠避免 Windows 路径转义问题
    lines = []
    for f in input_files:
        safe_path = f.replace("\\", "/")
        lines.append(f"file '{safe_path}'")
    list_file.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        ffmpeg_path,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path,
    ]

    print(f"[tts] ffmpeg cmd: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"[tts] ffmpeg exec error: {exc}")
        try:
            list_file.unlink()
        except Exception:
            pass
        return False

    try:
        list_file.unlink()
    except Exception:
        pass

    if result.returncode != 0:
        error_msg = result.stderr.decode(errors="replace") if result.stderr else "Unknown"
        print(f"[tts] ffmpeg failed (code {result.returncode}): {error_msg}")
        return False

    print(f"[tts] ffmpeg concat ok output={output_path}")
    return True


async def _concatenate_with_ffmpeg(
    input_files: List[str],
    output_path: str,
    ffmpeg_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 ffmpeg 拼接音频文件（subprocess.run 在线程中执行）"""
    ok = await asyncio.to_thread(
        _concatenate_ffmpeg_sync, input_files, output_path, ffmpeg_path,
    )
    if not ok:
        print("[tts] ffmpeg failed, falling back to pydub")
        return await _concatenate_with_pydub(input_files, output_path, emit_callback)
    return output_path


async def _concatenate_with_pydub(
    input_files: List[str],
    output_path: str,
    emit_callback: Optional[Callable] = None,
) -> str:
    """使用 pydub 拼接音频文件（纯 Python 回退方案，不依赖 ffmpeg）"""
    try:
        from pydub import AudioSegment
        from pydub.utils import which as _pydub_which
    except ImportError:
        # pydub 也没有，尝试同步 pip install
        print("[tts] pydub not found, attempting to install...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pydub"],
                capture_output=True, timeout=60,
            )
        except Exception:
            pass
        try:
            from pydub import AudioSegment
        except ImportError:
            # 最后回退：直接拼接二进制 MP3 数据（不完美但可用）
            print("[tts] pydub install failed, using binary concatenation fallback")
            return await _concatenate_binary(input_files, output_path)

    # pydub 依赖 ffmpeg 进行解码/编码
    if not _pydub_which("ffmpeg") and not _pydub_which("avconv"):
        print("[tts] pydub found but ffmpeg/avconv missing, using binary concatenation fallback")
        return await _concatenate_binary(input_files, output_path)

    def do_concat():
        combined = AudioSegment.empty()
        for f in input_files:
            try:
                seg = AudioSegment.from_mp3(f)
                combined += seg
            except Exception as e:
                print(f"[tts] pydub failed to read {f}: {e}")
                # 尝试作为 raw 音频读取
                try:
                    seg = AudioSegment.from_file(f)
                    combined += seg
                except Exception:
                    continue
        combined.export(output_path, format="mp3", bitrate="192k")
        return output_path

    # 在线程池中运行避免阻塞事件循环
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_concat)


async def _concatenate_binary(
    input_files: List[str],
    output_path: str,
) -> str:
    """最终回退：直接拼接 MP3 二进制数据"""
    async with aiofiles.open(output_path, "wb") as out:
        for f in input_files:
            try:
                async with aiofiles.open(f, "rb") as inp:
                    data = await inp.read()
                    await out.write(data)
            except Exception as e:
                print(f"[tts] binary concat skip {f}: {e}")
    return output_path
