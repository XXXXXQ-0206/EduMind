"""
教学视频 API 路由
流程：DeepSeek 生成脚本文案 → 后续接入即梦文生视频
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import List, Optional
import aiofiles
from fastapi import APIRouter, Depends, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import httpx

from agents.teaching_video_agent import TeachingVideoAgent, TeachingVideoInput
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.object_store import create_object_store
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.auth import get_bearer_token, require_auth, require_websocket_auth, resolve_user_from_token
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import (
    delete_teaching_video,
    json_storage,
    list_files_for_user,
    list_teaching_videos,
    owner_payload,
    record_belongs_to_user,
)
from utils.jiemeng_video import (
    VideoGenerationError,
    VideoGenerationProfile,
    get_configured_provider,
    is_gateway_configured,
    is_configured as jiemeng_video_configured,
    submit_text_to_video,
    wait_for_video,
)
from utils.teaching_video_audio import (
    add_audio_to_teaching_video,
    build_teaching_audio,
    build_teaching_slideshow_video,
    cache_remote_teaching_video,
)
from config import config


router = APIRouter()
logger = logging.getLogger(__name__)
TEACHING_VIDEO_TASKS: dict[str, asyncio.Task] = {}


def _video_channel(video_id: str) -> str:
    return f"video:{video_id}"


async def _send_video_event(video_id: str, message: dict) -> None:
    await publish_live_event(_video_channel(video_id), message)


def _is_teaching_video_task_running(video_id: str) -> bool:
    task = TEACHING_VIDEO_TASKS.get(video_id)
    return bool(task and not task.done())


class TeachingVideoRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    role: Optional[str] = "teacher"  # 教学视频默认教师端


def _resolve_video_source(video_url: str, local_video_url: str, local_audio_url: str) -> str:
    if local_video_url and video_url:
        return "jimeng_local_merge"
    if video_url:
        return "jimeng_remote"
    if local_video_url:
        return "fallback_local"
    if local_audio_url:
        return "audio_only"
    return "script_only"


def _video_profile(agent: TeachingVideoAgent, topic: str, script: str) -> VideoGenerationProfile:
    recommended = agent.recommend_video_profile(topic, script)
    return VideoGenerationProfile(
        student_type=(config.jimeng_video_student_type or recommended.get("student_type") or "mixed_age").strip(),
        teaching_style=(config.jimeng_video_teaching_style or recommended.get("teaching_style") or "vivid_fun").strip(),
        voice_type=(config.jimeng_video_voice_type or recommended.get("voice_type") or "zh_female_linjianvhai_moon_bigtts").strip(),
    )


def _format_video_error(exc: Exception) -> str:
    if isinstance(exc, VideoGenerationError):
        if exc.provider == "visual" and exc.code == "50400":
            return (
                "即梦 Visual 视频接口鉴权失败：当前 AK/SK 没有开通或没有权限调用“即梦AI-视频生成”能力。"
                " 处理建议：1) 到火山引擎控制台为该账号开通即梦AI视频能力；"
                "2) 或改用知识点视频生成智能体，在 .env 配置 JIMENG_VIDEO_GATEWAY_API_KEY，"
                "并设置 JIMENG_VIDEO_PROVIDER=gateway（或 auto 且已配置 Gateway Key）。"
                + (f" request_id={exc.request_id}" if exc.request_id else "")
            )
        if exc.provider == "visual" and exc.code == "50412":
            return (
                "即梦 Visual 文本风控未通过（Text Risk Not Pass）。"
                " 处理建议：将提示词改为更中性的教学描述，避免政治冲突、暴力对抗等敏感表达；"
                "或改用知识点视频生成智能体（gateway）。"
                + (f" request_id={exc.request_id}" if exc.request_id else "")
            )
        if exc.provider == "gateway" and exc.status_code == 401:
            return (
                "知识点视频生成智能体鉴权失败：请检查 JIMENG_VIDEO_GATEWAY_API_KEY 是否有效，"
                "并确认该 Key 已绑定知识点视频生成智能体。"
                + (f" request_id={exc.request_id}" if exc.request_id else "")
            )
        return exc.to_user_message()
    return str(exc)


def _is_visual_text_risk_error(exc: Exception) -> bool:
    return isinstance(exc, VideoGenerationError) and exc.provider == "visual" and exc.code == "50412"


def _build_visual_safe_retry_prompt(topic: str, script: str) -> str:
    """在 visual 文本风控拦截时，使用更中性的教学提示词重试一次。"""
    def _sanitize(text: str) -> str:
        value = (text or "").strip()
        replacements = {
            "革命": "历史变革",
            "战争": "历史事件",
            "起义": "社会变革",
            "政权": "社会结构",
            "武装": "历史过程",
            "推翻": "变迁",
        }
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value

    safe_topic = _sanitize(topic) or "历史知识点"
    script_sentences = [
        part.strip()
        for part in __import__("re").split(r"[。！？!?；;\n]+", script or "")
        if part and part.strip()
    ]
    safe_summary = "；".join(_sanitize(part) for part in script_sentences[:3])[:220]
    return (
        f"中学历史课堂教学微课，主题：{safe_topic}。"
        "以客观、中性、科普方式呈现时代背景、关键知识点和社会变化，"
        "采用课堂讲解动画、时间线图示、地图与资料插图风格，"
        "避免冲突对抗、暴力画面和敏感叙事。"
        f" 讲解要点：{safe_summary or '围绕历史背景、事件过程与影响进行课堂讲解。'}"
    ).strip()


@router.post("/teaching-video")
async def create_teaching_video(request: TeachingVideoRequest, user: AuthUser = Depends(require_auth)):
    """创建教学视频任务（先生成文案，即梦接口后续接入）"""
    try:
        topic = (request.topic or "").strip()
        include_materials = bool(request.includeMaterials)
        material_ids = request.materialIds or []
        scope = (request.role or "teacher").strip().lower()
        if scope not in ("student", "teacher"):
            scope = "teacher"

        if not topic:
            return JSONResponse(
                content={"ok": False, "error": "topic required"},
                status_code=400,
            )

        video_id = str(uuid.uuid4())
        await json_storage.set(f"video:{video_id}:topic", topic)
        await json_storage.set(
            f"video:{video_id}:materials",
            {"include": include_materials, "ids": material_ids},
        )
        await json_storage.set(
            f"video:{video_id}",
            {
                "id": video_id,
                "title": topic[:100],
                "scope": scope,
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "updated_at": __import__("datetime").datetime.now().isoformat(),
                **owner_payload(user.id, user.username),
            },
        )
        await json_storage.set(f"video:{video_id}:run_state", "pending")
        await json_storage.set(f"video:{video_id}:phase", "pending")
        await dispatch_generation_task("teaching_video", video_id, _ensure_teaching_video_generation)

        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "videoId": video_id,
                "stream": f"/ws/teaching-video?videoId={video_id}",
            },
        )
    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500,
        )


async def _stream_file(path: Path):
    """流式读取本地文件"""
    async with aiofiles.open(path, "rb") as f:
        while True:
            chunk = await f.read(65536)
            if not chunk:
                break
            yield chunk


def _object_url(key: str) -> str:
    url = create_object_store().url_for(key)
    return f"{config.backend_url.rstrip('/')}{url}" if url.startswith("/") else url


async def _ensure_media_object(relative_path: Optional[str]) -> str:
    key = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not key:
        return ""
    object_store = create_object_store()
    try:
        await object_store.get_bytes(key)
        return key
    except Exception:
        pass

    local_path = (config.storage_dir / key).resolve()
    storage_root = config.storage_dir.resolve()
    if local_path.exists() and (local_path == storage_root or storage_root in local_path.parents):
        await object_store.put_file(key, local_path)
        return key
    return ""


async def _stream_object(key: str):
    content = await create_object_store().get_bytes(key)
    yield content


async def _read_sidecar_text(file_path: str) -> str:
    txt_path = Path(file_path + ".txt")
    if not txt_path.exists():
        return ""
    try:
        async with aiofiles.open(txt_path, "r", encoding="utf-8") as f:
            return await f.read()
    except Exception:
        return ""


async def _build_material_context(ids: List[str], owner_id: int, owner_username: str, role: str) -> str:
    if not ids:
        return ""
    files = await list_files_for_user(owner_id, owner_username, role)
    return await build_selected_files_context(files, ids, max_chars=8000, snippet_chars=8000)


async def _send_teaching_video_snapshot(video_id: str) -> tuple[bool, bool]:
    saved_script = await json_storage.get(f"video:{video_id}:script")
    saved_video = await json_storage.get(f"video:{video_id}:video_url")
    saved_local = await json_storage.get(f"video:{video_id}:local_path")
    saved_audio = await json_storage.get(f"video:{video_id}:audio_path")
    saved_error = await json_storage.get(f"video:{video_id}:video_error")
    saved_phase = await json_storage.get(f"video:{video_id}:phase")

    if isinstance(saved_phase, str) and saved_phase.strip():
        await _send_video_event(video_id, {"type": "phase", "value": saved_phase.strip()})
    if isinstance(saved_script, str) and saved_script.strip():
        await _send_video_event(video_id, {"type": "script", "script": saved_script})
    if isinstance(saved_audio, str) and saved_audio.strip():
        await _send_video_event(video_id, {"type": "local_audio", "audioPath": saved_audio})
    if isinstance(saved_video, str) and saved_video.strip():
        await _send_video_event(video_id, {"type": "video", "videoUrl": saved_video})
    if isinstance(saved_local, str) and saved_local.strip():
        await _send_video_event(video_id, {"type": "local_video", "localPath": saved_local})
    if isinstance(saved_error, str) and saved_error.strip():
        await _send_video_event(video_id, {"type": "video_error", "error": saved_error})

    has_final = bool(
        (saved_video and str(saved_video).strip())
        or (saved_local and str(saved_local).strip())
        or (saved_audio and str(saved_audio).strip())
        or (saved_error and str(saved_error).strip())
    )
    has_script = bool(saved_script and str(saved_script).strip())
    return has_final, has_script


async def _ensure_teaching_video_generation(video_id: str) -> None:
    if _is_teaching_video_task_running(video_id):
        return

    lease = await acquire_task_lease(f"video:{video_id}")
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _run_teaching_video_generation(video_id)
        finally:
            await release_task_lease(lease)
            TEACHING_VIDEO_TASKS.pop(video_id, None)

    TEACHING_VIDEO_TASKS[video_id] = asyncio.create_task(_runner())


async def _run_teaching_video_generation_worker(video_id: str) -> None:
    lease = await acquire_task_lease(f"teaching_video:{video_id}")
    if not lease:
        return
    try:
        await _run_teaching_video_generation(video_id)
    finally:
        await release_task_lease(lease)


async def _run_teaching_video_generation(video_id: str) -> None:
    topic = await json_storage.get(f"video:{video_id}:topic")
    materials_cfg = await json_storage.get(f"video:{video_id}:materials") or {}
    use_materials = bool(materials_cfg.get("include"))
    material_ids = list(materials_cfg.get("ids") or [])
    meta = await json_storage.get(f"video:{video_id}") or {}
    scope = (meta.get("scope") or "teacher").strip().lower()
    if scope not in ("student", "teacher"):
        scope = "teacher"
    owner_id = int(meta.get("owner_id") or 0)
    owner_username = str(meta.get("owner_username") or "")

    if not topic:
        await _send_video_event(video_id, {"type": "error", "error": "Topic not found"})
        return

    run_state = str(await json_storage.get(f"video:{video_id}:run_state") or "").strip().lower()
    if run_state in {"done", "failed"}:
        has_final, has_script = await _send_teaching_video_snapshot(video_id)
        if has_final or has_script:
            await _send_video_event(video_id, {"type": "done"})
            return

    await json_storage.set(f"video:{video_id}:run_state", "running")
    await json_storage.set(f"video:{video_id}:phase", "script")
    await _send_video_event(video_id, {"type": "phase", "value": "script"})

    materials_context = ""
    if use_materials and material_ids:
        materials_context = await _build_material_context(material_ids, owner_id, owner_username, scope)

    agent = TeachingVideoAgent()
    result = await agent.execute(TeachingVideoInput(topic=topic, materials_context=materials_context or None))
    if not result.success or not result.script:
        await json_storage.set(f"video:{video_id}:run_state", "failed")
        await json_storage.set(f"video:{video_id}:phase", "error")
        await _send_video_event(video_id, {"type": "error", "error": result.error or "script_failed"})
        return

    if not isinstance(await json_storage.get(f"video:{video_id}"), dict):
        return
    await json_storage.set(f"video:{video_id}:script", result.script)
    await json_storage.set(f"video:{video_id}:video_error", "")
    meta = await json_storage.get(f"video:{video_id}") or {}
    if isinstance(meta, dict):
        meta["updated_at"] = __import__("datetime").datetime.now().isoformat()
        await json_storage.set(f"video:{video_id}", meta)
    await _send_video_event(video_id, {"type": "script", "script": result.script})

    provider_name = get_configured_provider()
    profile = _video_profile(agent, topic, result.script)

    if provider_name != "gateway":
        await json_storage.set(f"video:{video_id}:phase", "audio")
        await _send_video_event(video_id, {"type": "phase", "value": "audio"})
        audio_path = await build_teaching_audio(video_id, result.script)
        if audio_path:
            await _ensure_media_object(audio_path)
            await json_storage.set(f"video:{video_id}:audio_path", audio_path)
            await _send_video_event(video_id, {"type": "local_audio", "audioPath": audio_path})

    async def build_fallback() -> None:
        if not config.jimeng_video_allow_fallback:
            return
        await json_storage.set(f"video:{video_id}:phase", "video_pending")
        await _send_video_event(video_id, {"type": "phase", "value": "video_pending"})
        try:
            fallback_path = await build_teaching_slideshow_video(video_id, topic, result.script)
            if fallback_path:
                await _ensure_media_object(fallback_path)
                await json_storage.set(f"video:{video_id}:local_path", fallback_path)
                await json_storage.set(f"video:{video_id}:video_source", "fallback_local")
                await _send_video_event(video_id, {"type": "local_video", "localPath": fallback_path})
        except Exception as fallback_exc:
            logger.error("teaching_video fallback failed video_id=%s error=%s", video_id, fallback_exc)

    if jiemeng_video_configured():
        await json_storage.set(f"video:{video_id}:phase", "video")
        await _send_video_event(video_id, {"type": "phase", "value": "video"})
        try:
            provider_candidates: List[str] = []
            if provider_name:
                provider_candidates.append(provider_name)
            if provider_name == "visual" and is_gateway_configured():
                provider_candidates.append("gateway")
            if not provider_candidates:
                provider_candidates = ["gateway", "visual"]

            task = None
            last_exc: Optional[Exception] = None
            for idx, provider_choice in enumerate(provider_candidates):
                try:
                    if provider_choice == "gateway":
                        video_prompt = agent.build_gateway_video_prompt(topic, result.script)
                    else:
                        video_prompt = await agent.script_to_video_prompt(result.script)
                    task = await submit_text_to_video(
                        video_prompt,
                        duration_sec=10,
                        aspect_ratio="16:9",
                        profile=profile,
                        provider=provider_choice,
                    )
                    provider_name = provider_choice
                    break
                except Exception as provider_exc:
                    if provider_choice == "visual" and _is_visual_text_risk_error(provider_exc):
                        try:
                            safe_prompt = _build_visual_safe_retry_prompt(topic, result.script)
                            task = await submit_text_to_video(
                                safe_prompt,
                                duration_sec=10,
                                aspect_ratio="16:9",
                                profile=profile,
                                provider=provider_choice,
                            )
                            provider_name = provider_choice
                            break
                        except Exception as retry_exc:
                            provider_exc = retry_exc
                    last_exc = provider_exc
                    if idx < len(provider_candidates) - 1:
                        continue
                    raise provider_exc

            if task is None:
                raise last_exc or RuntimeError("submit video task failed")

            await json_storage.set(f"video:{video_id}:video_provider", task.provider)
            await json_storage.set(f"video:{video_id}:video_task_id", task.task_id)
            if task.request_id:
                await json_storage.set(f"video:{video_id}:video_request_id", task.request_id)

            status, video_url, request_id = await wait_for_video(task, poll_interval=6.0, max_wait_sec=600.0)
            if request_id:
                await json_storage.set(f"video:{video_id}:video_request_id", request_id)
            if status == "done" and video_url:
                await json_storage.set(f"video:{video_id}:video_url", video_url)
                await json_storage.set(f"video:{video_id}:video_error", "")
                await json_storage.set(f"video:{video_id}:video_source", "jimeng_remote")
                await _send_video_event(video_id, {"type": "video", "videoUrl": video_url})

                local_path = await cache_remote_teaching_video(video_id, video_url) if task.provider == "gateway" else await add_audio_to_teaching_video(video_id, video_url, result.script)
                if local_path:
                    await _ensure_media_object(local_path)
                    if task.provider != "gateway":
                        await json_storage.set(f"video:{video_id}:video_source", "jimeng_local_merge")
                    await json_storage.set(f"video:{video_id}:local_path", local_path)
                    await _send_video_event(video_id, {"type": "local_video", "localPath": local_path})
            else:
                raise VideoGenerationError(
                    f"视频生成未成功: {status}",
                    provider=task.provider,
                    request_id=request_id,
                    retryable=status not in ("failed", "expired", "not_found"),
                )
        except Exception as exc:
            error_message = _format_video_error(exc)
            logger.error("teaching_video generate failed topic=%s provider=%s error=%s", topic, provider_name or "none", error_message)
            await json_storage.set(f"video:{video_id}:video_error", error_message)
            await _send_video_event(video_id, {"type": "video_error", "error": error_message})
            await build_fallback()
    else:
        error_message = "未配置教学视频生成凭证：请配置 JIMENG_VIDEO_GATEWAY_API_KEY 或可用的即梦视频凭证。"
        await json_storage.set(f"video:{video_id}:video_error", error_message)
        await _send_video_event(video_id, {"type": "video_error", "error": error_message})
        await build_fallback()

    await json_storage.set(f"video:{video_id}:run_state", "done")
    await json_storage.set(f"video:{video_id}:phase", "done")
    await _send_video_event(video_id, {"type": "done"})


@router.websocket("/ws/teaching-video")
async def teaching_video_websocket(websocket: WebSocket):
    """教学视频 WebSocket：先生成脚本，即梦文生视频后续接入"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return
    query_params = dict(websocket.query_params)
    video_id = query_params.get("videoId")

    if not video_id:
        await websocket.close(code=1008, reason="videoId required")
        return

    meta = await json_storage.get(f"video:{video_id}") or {}
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        await websocket.close(code=1008, reason="not found")
        return

    forwarder = asyncio.create_task(forward_live_events(websocket, _video_channel(video_id)))
    await asyncio.sleep(0)
    await websocket.send_json({"type": "ready", "videoId": video_id})

    try:
        run_state = str(await json_storage.get(f"video:{video_id}:run_state") or "").strip().lower()
        has_final, has_script = await _send_teaching_video_snapshot(video_id)
        if run_state in {"done", "failed"} and (has_final or has_script):
            await _send_video_event(video_id, {"type": "done"})
        else:
            await dispatch_generation_task("teaching_video", video_id, _ensure_teaching_video_generation)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/teaching-videos")
async def list_teaching_videos_handler(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    """列出教学视频历史"""
    try:
        scope = (role or "").strip().lower() or None
        if scope is not None and scope not in ("student", "teacher"):
            scope = None
        videos = await list_teaching_videos(scope=scope, user_id=user.id, username=user.username)
        return {"ok": True, "videos": videos}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


register_task_handler("teaching_video", _run_teaching_video_generation_worker)


@router.get("/teaching-videos/{video_id}")
async def get_teaching_video_handler(video_id: str, user: AuthUser = Depends(require_auth)):
    """获取教学视频详情（含脚本）"""
    try:
        if not video_id or video_id in ("undefined", "null"):
            return JSONResponse(content={"ok": False, "error": "Invalid videoId"}, status_code=400)
        meta = await json_storage.get(f"video:{video_id}")
        script = await json_storage.get(f"video:{video_id}:script")
        video_url = await json_storage.get(f"video:{video_id}:video_url")
        local_path = await json_storage.get(f"video:{video_id}:local_path")
        audio_path = await json_storage.get(f"video:{video_id}:audio_path")
        video_error = await json_storage.get(f"video:{video_id}:video_error")
        local_video_url = ""
        local_audio_url = ""
        if local_path:
            local_key = await _ensure_media_object(local_path)
            if local_key:
                local_video_url = _object_url(local_key)
        if audio_path:
            audio_key = await _ensure_media_object(audio_path)
            if audio_key:
                local_audio_url = _object_url(audio_key)
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        video_source = await json_storage.get(f"video:{video_id}:video_source")
        if not video_source:
            video_source = _resolve_video_source(video_url or "", local_video_url, local_audio_url)
        video_provider = await json_storage.get(f"video:{video_id}:video_provider")
        video_task_id = await json_storage.get(f"video:{video_id}:video_task_id")
        video_request_id = await json_storage.get(f"video:{video_id}:video_request_id")
        return {
            "ok": True,
            "video": meta,
            "script": script or "",
            "videoUrl": video_url or "",
            "localVideoUrl": local_video_url,
            "localAudioUrl": local_audio_url,
            "videoError": video_error or "",
            "videoSource": video_source,
            "videoProvider": video_provider or "",
            "videoTaskId": video_task_id or "",
            "videoRequestId": video_request_id or "",
        }
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.get("/teaching-videos/{video_id}/video")
async def stream_teaching_video_handler(
    video_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """
    优先返回本地有声版（storage/teaching_videos/{id}/video_with_audio.mp4），
    若无则代理即梦 CDN 流（约 1 小时有效）。
    """
    token = request.query_params.get("token") or get_bearer_token(authorization)
    user = resolve_user_from_token(token)
    if not user:
        return JSONResponse(content={"ok": False, "error": "unauthorized"}, status_code=401)
    if not video_id or video_id in ("undefined", "null"):
        return JSONResponse(content={"ok": False, "error": "Invalid videoId"}, status_code=400)
    meta = await json_storage.get(f"video:{video_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    local_path = await json_storage.get(f"video:{video_id}:local_path")
    if local_path:
        local_key = await _ensure_media_object(local_path)
        if local_key:
            return StreamingResponse(
                _stream_object(local_key),
                media_type="video/mp4",
                headers={"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=86400"},
            )
    video_url = await json_storage.get(f"video:{video_id}:video_url")
    if not video_url or not isinstance(video_url, str):
        return JSONResponse(content={"ok": False, "error": "video not found or expired"}, status_code=404)

    async def _stream_cdn():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", video_url) as r:
                if r.status_code != 200:
                    return
                async for chunk in r.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        _stream_cdn(),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600"},
    )


@router.delete("/teaching-videos/{video_id}")
async def delete_teaching_video_handler(video_id: str, user: AuthUser = Depends(require_auth)):
    """删除教学视频"""
    try:
        if not video_id or video_id in ("undefined", "null"):
            return JSONResponse(content={"ok": False, "error": "Invalid videoId"}, status_code=400)
        meta = await json_storage.get(f"video:{video_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        await delete_teaching_video(video_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)

