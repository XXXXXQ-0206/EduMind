"""
播客 API 路由
与原 Node.js 版本完全兼容
"""
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import unquote, urlparse
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import aiofiles

from agents.podcast_agent import PodcastAgent, PodcastInput
from utils.auth import require_auth, require_websocket_auth, get_request_user, resolve_user_from_token
from utils.auth_db import AuthUser
from utils.storage import derive_podcast_status, json_storage, list_files_for_user, list_podcasts, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()


def _build_podcast_urls(pid: str, filename: str) -> Dict[str, str]:
    safe_name = Path(filename).name
    return {
        "static": f"/storage/podcasts/{pid}/{safe_name}",
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


class PodcastRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    length: Optional[str] = "medium"


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

        return JSONResponse(
            content={"ok": True, "pid": pid, "stream": f"/ws/podcast?pid={pid}"},
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

    print(f"[podcast] ws connect pid={pid} client={websocket.client}")
    async def safe_send(message: Dict[str, Any]) -> None:
        try:
            await websocket.send_json(message)
        except Exception as exc:
            print(f"[podcast] safe_send failed pid={pid}: {exc}")

    async def update_podcast_meta(status: str, *, error: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        meta = await json_storage.get(f"podcast:{pid}") or {}
        if not isinstance(meta, dict):
            meta = {"id": pid}
        meta["status"] = status
        meta["updated_at"] = datetime.now().isoformat()
        if error:
            meta["error"] = error
        else:
            meta.pop("error", None)
        if extra:
            meta.update(extra)
        await json_storage.set(f"podcast:{pid}", meta)
        return meta

    # 发送 ready 消息
    await safe_send({"type": "ready", "pid": pid})

    try:
        data = await json_storage.get(f"podcast:{pid}:payload")
        if not data:
            try:
                data = await websocket.receive_json()
            except Exception:
                data = {}

        topic = data.get("topic", "")
        print(f"[podcast] ws payload pid={pid} topic_len={len(topic or '')} includeMaterials={bool(data.get('includeMaterials'))} materialIds={len(data.get('materialIds') or [])} length={data.get('length')}")

        await safe_send({"type": "phase", "value": "generating"})

        async def read_sidecar_text(file_path: str) -> str:
            txt_path = Path(file_path + ".txt")
            if not txt_path.exists():
                return ""
            try:
                async with aiofiles.open(txt_path, "r", encoding="utf-8") as f:
                    return await f.read()
            except Exception:
                return ""

        async def build_material_context(ids: List[str]) -> str:
            if not ids:
                return ""
            meta = await json_storage.get(f"podcast:{pid}") or {}
            owner_id = int(meta.get("owner_id") or 0)
            owner_username = str(meta.get("owner_username") or "")
            files = await list_files_for_user(owner_id, owner_username, "student")
            file_map = {f.get("id"): f for f in files if f.get("id")}
            max_chars = 40000
            parts: List[str] = []
            used = 0

            for fid in ids:
                meta = file_map.get(fid)
                if not meta:
                    continue
                filename = meta.get("filename")
                if not filename:
                    continue
                file_path = str(config.storage_dir / "uploads" / filename)
                text = ""
                if not text:
                    text = await read_sidecar_text(file_path)
                if not text:
                    try:
                        from utils.parser import extract_text_from_file
                        text = await extract_text_from_file(file_path, meta.get("mimeType"))
                    except Exception:
                        text = ""
                if not text:
                    continue
                remaining = max_chars - used
                if remaining <= 0:
                    break
                snippet = text[:remaining]
                header = f"\n\n[资料] {meta.get('originalName') or filename}\n"
                parts.append(header + snippet)
                used += len(snippet)

            return "".join(parts).strip()

        include_materials = bool(data.get("includeMaterials"))
        material_ids = data.get("materialIds") or []
        length = data.get("length") or "medium"

        materials_text = ""
        if include_materials and material_ids:
            materials_text = await build_material_context(material_ids)
            print(f"[podcast] materials pid={pid} chars={len(materials_text)}")

        # 创建 Agent 并执行（学习资料作为独立字段传入，不混入 topic）
        agent = PodcastAgent()
        input_data = PodcastInput(
            topic=topic,
            length=length,
            pid=pid,
            materials_text=materials_text if materials_text else None,
        )

        async def emit_callback(msg: Dict[str, Any]):
            try:
                msg_type = msg.get("type") if isinstance(msg, dict) else None
            except Exception:
                msg_type = None
            if msg_type:
                print(f"[podcast] emit pid={pid} type={msg_type}")
            if msg_type == "script" and isinstance(msg.get("data"), dict):
                await json_storage.set(f"podcast:{pid}:script", msg["data"])
                await update_podcast_meta("generating")
            await safe_send(msg)

        try:
            result = await agent.execute(input_data, emit_callback=emit_callback)
        except Exception as e:
            print(f"[podcast] generate failed: {e}")
            err_msg = str(e)
            await update_podcast_meta("error", error=err_msg)
            await safe_send({"type": "error", "error": err_msg})
            return

        print(f"[podcast] result pid={pid} success={result.success} audio_path={'yes' if result.audio_path else 'no'}")
        script_data = result.data.get("script") if isinstance(result.data, dict) else None
        if not isinstance(script_data, dict):
            saved_script = await json_storage.get(f"podcast:{pid}:script")
            script_data = saved_script if isinstance(saved_script, dict) else None
        if isinstance(script_data, dict):
            segs = script_data.get("segments") or []
            print(f"[podcast] script pid={pid} segments={len(segs)}")

        if result.success and result.audio_path:
            # 生成文件 URL
            file_name = Path(result.audio_path).name
            try:
                audio_size = Path(result.audio_path).stat().st_size
                print(f"[podcast] audio ready: {file_name} ({audio_size} bytes)")
            except Exception as e:
                print(f"[podcast] audio stat failed: {e}")
            urls = _build_podcast_urls(pid, file_name)

            await update_podcast_meta("ready", extra={"file": urls["file"], "static": urls["static"]})

            await safe_send({
                "type": "audio",
                "file": urls["file"],
                "filename": file_name,
                "staticUrl": urls["static"],
            })
            await safe_send({"type": "done"})
        elif script_data:
            err_msg = (result.error or "").strip() or "Audio synthesis failed"
            await update_podcast_meta("ready", error=err_msg)
            print(f"[podcast] warn pid={pid} message={err_msg}")
            await safe_send({"type": "warn", "message": f"{err_msg}，已保留播客脚本。"})
            await safe_send({"type": "done"})
        else:
            err_msg = (result.error or "").strip() or "Audio synthesis failed"
            await update_podcast_meta("error", error=err_msg)
            print(f"[podcast] error pid={pid} message={err_msg}")
            await safe_send({"type": "error", "error": err_msg})

    except WebSocketDisconnect:
        print(f"[podcast] ws disconnect pid={pid}")
        return
    except Exception as e:
        print(f"[podcast] ws error pid={pid}: {e}")
        await update_podcast_meta("error", error=str(e))
        try:
            await safe_send({"type": "error", "error": str(e)})
        except Exception:
            return


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

        return FileResponse(
            path=str(matching_file),
            media_type=_media_type_for_audio(matching_file),
            filename=matching_file.name,
        )

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
        await delete_podcast(pid)
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
