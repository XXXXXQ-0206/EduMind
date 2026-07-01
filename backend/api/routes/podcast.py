"""
播客 API 路由
与原 Node.js 版本完全兼容
"""
import asyncio
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote, unquote, urlparse
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from agents.podcast_agent import PodcastAgent, PodcastInput
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.object_store import create_object_store
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.auth import require_auth, require_websocket_auth, get_request_user, resolve_user_from_token
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import derive_podcast_status, json_storage, list_files_for_user, list_podcasts, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()
PODCAST_TASKS: Dict[str, asyncio.Task[Any]] = {}


def _build_podcast_urls(pid: str, filename: str) -> Dict[str, str]:
    safe_name = Path(filename).name
    static_url = create_object_store().url_for(f"podcasts/{pid}/{safe_name}")
    return {
        "static": static_url,
        "file": f"/podcast/download/{pid}/{safe_name}",
    }


def _audio_filename_from_meta(meta: Dict[str, Any]) -> Optional[str]:
    for key in ("static", "file"):
        raw = str(meta.get(key) or "").strip()
        if not raw:
            continue
        try:
            parsed = urlparse(raw)
            candidate = parsed.path or raw
        except Exception:
            candidate = raw
        name = Path(unquote(candidate)).name
        if name:
            return name
    return None


def _media_type_for_audio(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".m4a":
        return "audio/mp4"
    if suffix == ".wav":
        return "audio/wav"
    return "audio/mpeg"


def _audio_download_response(content: bytes, filename: str) -> Response:
    safe_filename = Path(filename).name or "podcast.mp3"
    return Response(
        content=content,
        media_type=_media_type_for_audio(Path(safe_filename)),
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}"},
    )


class PodcastRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    length: Optional[str] = "medium"


def _podcast_channel(pid: str) -> str:
    return f"podcast:{pid}"


async def _send_podcast_event(pid: str, message: Dict[str, Any]) -> None:
    try:
        await publish_live_event(_podcast_channel(pid), message)
    except Exception as exc:
        print(f"[podcast] publish failed pid={pid}: {exc}")


async def _safe_send_podcast(websocket: WebSocket, message: Dict[str, Any], pid: str) -> bool:
    try:
        await websocket.send_json(message)
        return True
    except Exception as exc:
        print(f"[podcast] safe_send failed pid={pid}: {exc}")
        return False


async def _update_podcast_meta(
    pid: str,
    status: str,
    *,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    def updater(current: Any) -> Dict[str, Any]:
        meta = dict(current if isinstance(current, dict) else {"id": pid})
        meta["id"] = meta.get("id") or pid
        meta["status"] = status
        meta["updated_at"] = datetime.now().isoformat()
        if error:
            meta["error"] = error
        else:
            meta.pop("error", None)
        if extra:
            meta.update(extra)
        return meta

    updated = await json_storage.update(f"podcast:{pid}", updater, default={"id": pid})
    return updated if isinstance(updated, dict) else {"id": pid, "status": status}


async def _podcast_still_exists(pid: str) -> bool:
    return isinstance(await json_storage.get(f"podcast:{pid}"), dict)


def _is_podcast_task_running(pid: str) -> bool:
    task = PODCAST_TASKS.get(pid)
    return bool(task and not task.done())


async def _build_podcast_material_context(pid: str, ids: List[str]) -> str:
    if not ids:
        return ""
    meta = await json_storage.get(f"podcast:{pid}") or {}
    owner_id = int(meta.get("owner_id") or 0)
    owner_username = str(meta.get("owner_username") or "")
    files = await list_files_for_user(owner_id, owner_username, "student")
    return await build_selected_files_context(files, ids, max_chars=40000, snippet_chars=40000)


async def _send_podcast_snapshot(websocket: WebSocket, pid: str) -> bool:
    meta = await json_storage.get(f"podcast:{pid}") or {}
    script = await json_storage.get(f"podcast:{pid}:script")
    if not isinstance(meta, dict):
        return True

    status = derive_podcast_status(meta, script)
    if isinstance(script, dict):
        await _safe_send_podcast(websocket, {"type": "script", "data": script}, pid)

    audio_file_name = _audio_filename_from_meta(meta)
    if audio_file_name:
        urls = _build_podcast_urls(pid, audio_file_name)
        await _safe_send_podcast(
            websocket,
            {
                "type": "audio",
                "file": urls["file"],
                "filename": audio_file_name,
                "staticUrl": urls["static"],
            },
            pid,
        )

    if status == "ready":
        if meta.get("error") and not audio_file_name:
            await _safe_send_podcast(
                websocket,
                {"type": "warn", "message": f"{meta['error']}，已保留播客脚本。"},
                pid,
            )
        await _safe_send_podcast(websocket, {"type": "done"}, pid)
        return True

    if status == "error":
        await _safe_send_podcast(websocket, {"type": "error", "error": meta.get("error") or "generation failed"}, pid)
        return True

    if status in {"pending", "generating"}:
        await _safe_send_podcast(websocket, {"type": "phase", "value": "generating"}, pid)
    return False


async def _run_podcast_generation(pid: str) -> None:
    data = await json_storage.get(f"podcast:{pid}:payload")
    if not isinstance(data, dict):
        err_msg = "podcast payload not found"
        await _update_podcast_meta(pid, "error", error=err_msg)
        await _send_podcast_event(pid, {"type": "error", "error": err_msg})
        return

    meta = await json_storage.get(f"podcast:{pid}") or {}
    script = await json_storage.get(f"podcast:{pid}:script")
    if derive_podcast_status(meta if isinstance(meta, dict) else {}, script) == "ready":
        if isinstance(script, dict):
            await _send_podcast_event(pid, {"type": "script", "data": script})
        audio_file_name = _audio_filename_from_meta(meta if isinstance(meta, dict) else {})
        if audio_file_name:
            urls = _build_podcast_urls(pid, audio_file_name)
            await _send_podcast_event(
                pid,
                {
                    "type": "audio",
                    "file": urls["file"],
                    "filename": audio_file_name,
                    "staticUrl": urls["static"],
                },
            )
        elif isinstance(meta, dict) and meta.get("error"):
            await _send_podcast_event(pid, {"type": "warn", "message": f"{meta['error']}，已保留播客脚本。"})
        await _send_podcast_event(pid, {"type": "done"})
        return

    topic = str(data.get("topic") or "").strip()
    include_materials = bool(data.get("includeMaterials"))
    material_ids = data.get("materialIds") or []
    length = data.get("length") or "medium"
    has_materials = include_materials and bool(material_ids)
    if not topic and has_materials:
        topic = "基于学习资料的深度解读"
    if not topic and not has_materials:
        err_msg = "topic required"
        await _update_podcast_meta(pid, "error", error=err_msg)
        await _send_podcast_event(pid, {"type": "error", "error": err_msg})
        return

    print(
        f"[podcast] run pid={pid} topic_len={len(topic)} "
        f"includeMaterials={include_materials} materialIds={len(material_ids)} length={length}"
    )
    await _update_podcast_meta(pid, "generating")
    await _send_podcast_event(pid, {"type": "phase", "value": "generating"})

    materials_text = ""
    if include_materials and material_ids:
        materials_text = await _build_podcast_material_context(pid, material_ids)
        print(f"[podcast] materials pid={pid} chars={len(materials_text)}")

    agent = PodcastAgent()
    input_data = PodcastInput(
        topic=topic,
        length=length,
        pid=pid,
        materials_text=materials_text if materials_text else None,
    )

    async def emit_callback(msg: Dict[str, Any]) -> None:
        try:
            msg_type = msg.get("type") if isinstance(msg, dict) else None
        except Exception:
            msg_type = None
        if msg_type:
            print(f"[podcast] emit pid={pid} type={msg_type}")
        if msg_type == "script" and isinstance(msg.get("data"), dict):
            await json_storage.set(f"podcast:{pid}:script", msg["data"])
            await _update_podcast_meta(pid, "generating")
        await _send_podcast_event(pid, msg)

    try:
        result = await agent.execute(input_data, emit_callback=emit_callback)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        err_msg = str(exc).strip() or "podcast generation failed"
        print(f"[podcast] generate failed pid={pid}: {err_msg}")
        await _update_podcast_meta(pid, "error", error=err_msg)
        await _send_podcast_event(pid, {"type": "error", "error": err_msg})
        return

    print(f"[podcast] result pid={pid} success={result.success} audio_path={'yes' if result.audio_path else 'no'}")
    script_data = result.data.get("script") if isinstance(result.data, dict) else None
    if not isinstance(script_data, dict):
        saved_script = await json_storage.get(f"podcast:{pid}:script")
        script_data = saved_script if isinstance(saved_script, dict) else None
    if isinstance(script_data, dict):
        await json_storage.set(f"podcast:{pid}:script", script_data)
        segs = script_data.get("segments") or []
        print(f"[podcast] script pid={pid} segments={len(segs)}")

    if not await _podcast_still_exists(pid):
        return

    if result.success and result.audio_path:
        file_name = Path(result.audio_path).name
        try:
            await create_object_store().put_file(
                f"podcasts/{pid}/{file_name}",
                Path(result.audio_path),
            )
        except Exception as upload_exc:
            print(f"[podcast] object-store upload failed pid={pid}: {upload_exc}")
        try:
            audio_size = Path(result.audio_path).stat().st_size
            print(f"[podcast] audio ready: {file_name} ({audio_size} bytes)")
        except Exception as stat_exc:
            print(f"[podcast] audio stat failed: {stat_exc}")

        urls = _build_podcast_urls(pid, file_name)
        await _update_podcast_meta(pid, "ready", extra={"file": urls["file"], "static": urls["static"]})
        await _send_podcast_event(
            pid,
            {
                "type": "audio",
                "file": urls["file"],
                "filename": file_name,
                "staticUrl": urls["static"],
            },
        )
        await _send_podcast_event(pid, {"type": "done"})
        return

    if script_data:
        err_msg = (result.error or "").strip() or "Audio synthesis failed"
        await _update_podcast_meta(pid, "ready", error=err_msg)
        print(f"[podcast] warn pid={pid} message={err_msg}")
        await _send_podcast_event(pid, {"type": "warn", "message": f"{err_msg}，已保留播客脚本。"})
        await _send_podcast_event(pid, {"type": "done"})
        return

    err_msg = (result.error or "").strip() or "Audio synthesis failed"
    await _update_podcast_meta(pid, "error", error=err_msg)
    print(f"[podcast] error pid={pid} message={err_msg}")
    await _send_podcast_event(pid, {"type": "error", "error": err_msg})


async def _ensure_podcast_generation(pid: str) -> None:
    if _is_podcast_task_running(pid):
        return

    lease = await acquire_task_lease(f"podcast:{pid}")
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _run_podcast_generation(pid)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            err_msg = str(exc).strip() or "podcast generation failed"
            await _update_podcast_meta(pid, "error", error=err_msg)
            await _send_podcast_event(pid, {"type": "error", "error": err_msg})
            import traceback
            print(f"[podcast] runner failed pid={pid}: {type(exc).__name__}: {exc!r}")
            traceback.print_exc()
        finally:
            await release_task_lease(lease)
            PODCAST_TASKS.pop(pid, None)

    PODCAST_TASKS[pid] = asyncio.create_task(_runner())


async def _run_podcast_generation_worker(pid: str) -> None:
    lease = await acquire_task_lease(f"podcast:{pid}")
    if not lease:
        return
    try:
        await _run_podcast_generation(pid)
    finally:
        await release_task_lease(lease)


def crypto_random() -> str:
    """生成随机 ID（兼容原 Node.js 版本）"""
    import random
    import re

    def replace_uuid(match):
        c = match.group(0)
        if c == "x":
            return "0123456789abcdef"[random.randint(0, 15)]
        else:  # c == "y"
            return "0123456789ab"[random.randint(0, 3)]

    return re.sub(r"[xy]", replace_uuid, "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")


@router.post("/podcast")
async def create_podcast(request: PodcastRequest, user: AuthUser = Depends(require_auth)):
    """创建播客"""
    try:
        topic = request.topic.strip()
        has_materials = bool(request.includeMaterials) and bool(request.materialIds)

        if not topic and not has_materials:
            return JSONResponse({"error": "topic required"}, status_code=400)

        # 选择了学习资料但没输入topic时，自动设置默认topic
        if not topic and has_materials:
            topic = "基于学习资料的深度解读"

        pid = crypto_random()
        now = datetime.now().isoformat()
        payload = {
            "topic": topic,
            "includeMaterials": bool(request.includeMaterials),
            "materialIds": request.materialIds or [],
            "length": request.length or "medium",
        }
        print(f"[podcast] create: pid={pid} topic_len={len(topic)} includeMaterials={payload['includeMaterials']} materialIds={len(payload['materialIds'])} length={payload['length']}")

        await json_storage.set(f"podcast:{pid}", {
            "id": pid,
            "title": topic[:100],
            "length": request.length or "medium",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            **owner_payload(user.id, user.username),
        })
        await json_storage.set(f"podcast:{pid}:payload", payload)
        await dispatch_generation_task("podcast", pid, _ensure_podcast_generation)

        return JSONResponse(
            content={
                "ok": True,
                "pid": pid,
                "stream": f"/ws/podcast?pid={pid}",
                "events": f"/tasks/podcast/{pid}/events",
            },
            status_code=202,
        )

    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.websocket("/ws/podcast")
async def podcast_websocket(websocket: WebSocket):
    """播客 WebSocket 端点"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    query_params = dict(websocket.query_params)
    pid = query_params.get("pid")

    if not pid:
        await websocket.close(code=1008, reason="pid required")
        return

    meta = await json_storage.get(f"podcast:{pid}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        await websocket.close(code=1008, reason="not found")
        return

    print(f"[podcast] ws connect pid={pid} client={websocket.client}")
    forwarder = asyncio.create_task(forward_live_events(websocket, _podcast_channel(pid)))
    await asyncio.sleep(0)

    try:
        await _safe_send_podcast(websocket, {"type": "ready", "pid": pid}, pid)
        done = await _send_podcast_snapshot(websocket, pid)
        if not done:
            await dispatch_generation_task("podcast", pid, _ensure_podcast_generation)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"[podcast] ws disconnect pid={pid}")
        return
    except Exception as e:
        print(f"[podcast] ws error pid={pid}: {e}")
        await _update_podcast_meta(pid, "error", error=str(e))
        try:
            await _safe_send_podcast(websocket, {"type": "error", "error": str(e)}, pid)
        except Exception:
            return
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/podcast/download/{pid}/{filename}")
async def download_podcast(
    pid: str,
    filename: str,
    token: Optional[str] = Query(default=None),
    user: Optional[AuthUser] = Depends(get_request_user),
):
    """下载播客音频文件"""
    try:
        auth_user = user or resolve_user_from_token(token)
        if not auth_user:
            return JSONResponse({"detail": "请先登录后再访问"}, status_code=401)

        meta = await json_storage.get(f"podcast:{pid}")
        if not meta or not record_belongs_to_user(meta, auth_user.id, auth_user.username):
            return JSONResponse({"error": "File not found"}, status_code=404)

        requested_name = Path(filename).name
        object_store = create_object_store()
        try:
            content = await object_store.get_bytes(f"podcasts/{pid}/{requested_name}")
            return _audio_download_response(content, requested_name)
        except Exception:
            pass

        dir_path = config.storage_dir / "podcasts" / pid

        if not dir_path.exists():
            return JSONResponse({"error": "File not found"}, status_code=404)

        # 查找文件（不区分大小写）
        files = []
        for pattern in ("*.mp3", "*.m4a", "*.mp4", "*.wav"):
            files = [f for f in dir_path.glob(pattern) if not f.name.startswith("segment_")]
            if files:
                break
        matching_file = None

        for file in files:
            if file.name.lower() == filename.lower():
                matching_file = file
                break

        # 如果精确匹配不到，返回目录中第一个非 segment 的 mp3
        if not matching_file and files:
            matching_file = files[0]

        if not matching_file:
            return JSONResponse({"error": "File not found"}, status_code=404)

        object_key = f"podcasts/{pid}/{matching_file.name}"
        await object_store.put_file(object_key, matching_file)
        content = await object_store.get_bytes(object_key)
        return _audio_download_response(content, matching_file.name)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/podcasts")
async def list_podcasts_handler(user: AuthUser = Depends(require_auth)):
    """列出播客历史"""
    try:
        podcasts = await list_podcasts(user.id, user.username)
        return {"ok": True, "podcasts": podcasts}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.get("/podcasts/{pid}")
async def get_podcast_handler(pid: str, user: AuthUser = Depends(require_auth)):
    """获取播客详情"""
    try:
        if not pid or pid in {"undefined", "null"}:
            return JSONResponse({"ok": False, "error": "Invalid pid"}, status_code=400)
        meta = await json_storage.get(f"podcast:{pid}")
        script = await json_storage.get(f"podcast:{pid}:script")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)

        audio_file_name = _audio_filename_from_meta(meta)
        if audio_file_name:
            meta.update(_build_podcast_urls(pid, audio_file_name))

        # 如果 meta 中没有 file/static URL，尝试从文件系统查找
        if not meta.get("file") and not meta.get("static"):
            podcast_dir = config.storage_dir / "podcasts" / pid
            if podcast_dir.exists():
                audio_file = None
                for pattern in ("*.mp3", "*.m4a", "*.mp4", "*.wav"):
                    files = [f for f in podcast_dir.glob(pattern) if not f.name.startswith("segment_")]
                    if files:
                        audio_file = files[0]
                        break
                if audio_file:
                    meta.update(_build_podcast_urls(pid, audio_file.name))

        await json_storage.set(f"podcast:{pid}", meta)

        meta["id"] = pid
        meta["status"] = derive_podcast_status(meta, script)
        if meta["status"] in {"pending", "generating"}:
            await dispatch_generation_task("podcast", pid, _ensure_podcast_generation)

        return {"ok": True, "podcast": meta, "script": script}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.delete("/podcasts/{pid}")
async def delete_podcast_handler(pid: str, user: AuthUser = Depends(require_auth)):
    """删除播客"""
    from utils.storage import delete_podcast

    try:
        if not pid or pid in {"undefined", "null"}:
            return JSONResponse({"ok": False, "error": "Invalid pid"}, status_code=400)
        meta = await json_storage.get(f"podcast:{pid}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        task = PODCAST_TASKS.pop(pid, None)
        if task and not task.done():
            task.cancel()
        await delete_podcast(pid)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


register_task_handler("podcast", _run_podcast_generation_worker)
