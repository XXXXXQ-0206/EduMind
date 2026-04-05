"""
智能笔记 API 路由
与原 Node.js 版本完全兼容
"""
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiofiles

from agents.note_agent import NoteAgent, NoteInput
from utils.auth import require_auth, require_websocket_auth
from utils.auth_db import AuthUser
from utils.storage import derive_note_status, json_storage, list_files_for_user, list_notes, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()


class SmartNotesRequest(BaseModel):
    topic: Optional[str] = None
    notes: Optional[str] = None
    filePath: Optional[str] = None
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    length: Optional[str] = "medium"


NOTE_TASKS: Dict[str, asyncio.Task[Any]] = {}
NOTE_SUBSCRIBERS: Dict[str, Set[WebSocket]] = {}


async def _safe_send(websocket: WebSocket, message: Dict[str, Any], note_id: str) -> bool:
    try:
        await websocket.send_json(message)
        return True
    except Exception as exc:
        print(f"[smartnotes] safe_send failed noteId={note_id}: {exc}")
        return False


async def _broadcast_note_event(note_id: str, message: Dict[str, Any]) -> None:
    subscribers = list(NOTE_SUBSCRIBERS.get(note_id) or set())
    if not subscribers:
        return

    stale: List[WebSocket] = []
    for websocket in subscribers:
        ok = await _safe_send(websocket, message, note_id)
        if not ok:
            stale.append(websocket)

    if not stale:
        return

    current = NOTE_SUBSCRIBERS.get(note_id)
    if not current:
        return
    for websocket in stale:
        current.discard(websocket)
    if not current:
        NOTE_SUBSCRIBERS.pop(note_id, None)


async def _update_note_meta(
    note_id: str,
    status: str,
    *,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = await json_storage.get(f"note:{note_id}") or {}
    if not isinstance(meta, dict):
        meta = {"id": note_id}
    meta["status"] = status
    meta["updated_at"] = datetime.now().isoformat()
    if error:
        meta["error"] = error
    else:
        meta.pop("error", None)
    if extra:
        meta.update(extra)
    await json_storage.set(f"note:{note_id}", meta)
    return meta


async def _read_sidecar_text(file_path: str) -> str:
    txt_path = Path(file_path + ".txt")
    if not txt_path.exists():
        return ""
    try:
        async with aiofiles.open(txt_path, "r", encoding="utf-8") as f:
            return await f.read()
    except Exception:
        return ""


async def _build_note_material_context(note_id: str, ids: List[str]) -> str:
    if not ids:
        return ""

    meta = await json_storage.get(f"note:{note_id}") or {}
    owner_id = int(meta.get("owner_id") or 0)
    owner_username = str(meta.get("owner_username") or "")
    files = await list_files_for_user(owner_id, owner_username, "student")
    file_map = {f.get("id"): f for f in files if f.get("id")}
    parts: List[str] = []

    for fid in ids:
        file_meta = file_map.get(fid)
        if not file_meta:
            continue
        filename = file_meta.get("filename")
        if not filename:
            continue

        file_path = str(config.storage_dir / "uploads" / filename)
        text = await _read_sidecar_text(file_path)
        if not text:
            try:
                from utils.parser import extract_text_from_file
                text = await extract_text_from_file(file_path, file_meta.get("mimeType"))
            except Exception:
                text = ""
        if not text:
            continue

        header = f"\n\n[资料] {file_meta.get('originalName') or filename}\n"
        parts.append(header + text)

    return "".join(parts).strip()


def _is_note_task_running(note_id: str) -> bool:
    task = NOTE_TASKS.get(note_id)
    return bool(task and not task.done())


def _ensure_note_generation(note_id: str) -> None:
    if _is_note_task_running(note_id):
        return

    task = asyncio.create_task(_run_note_generation(note_id))
    NOTE_TASKS[note_id] = task

    def _cleanup(_: asyncio.Task[Any]) -> None:
        NOTE_TASKS.pop(note_id, None)

    task.add_done_callback(_cleanup)


async def _run_note_generation(note_id: str) -> None:
    data = await json_storage.get(f"note:{note_id}:payload")
    if not isinstance(data, dict):
        err_msg = "generation failed"
        await _update_note_meta(note_id, "error", error=err_msg)
        await _broadcast_note_event(note_id, {"type": "error", "error": err_msg})
        return

    existing_meta = await json_storage.get(f"note:{note_id}") or {}
    existing_notes = await json_storage.get(f"note:{note_id}:notes")
    if existing_notes and isinstance(existing_meta, dict) and existing_meta.get("file"):
        await _broadcast_note_event(note_id, {"type": "phase", "value": "notes"})
        await _broadcast_note_event(note_id, {"type": "notes", "notes": existing_notes})
        await _broadcast_note_event(note_id, {"type": "phase", "value": "file"})
        await _broadcast_note_event(note_id, {"type": "file", "file": existing_meta["file"]})
        await _broadcast_note_event(note_id, {"type": "done"})
        return

    await _update_note_meta(note_id, "generating")
    await _broadcast_note_event(note_id, {"type": "phase", "value": "generating"})

    agent = NoteAgent()
    include_materials = bool(data.get("includeMaterials"))
    material_ids = data.get("materialIds") or []
    length = data.get("length") or "medium"
    topic = data.get("topic")

    if include_materials and material_ids:
        materials_text = await _build_note_material_context(note_id, material_ids)
        if materials_text:
            topic = (
                f"{topic or ''}\n\n学习资料内容:\n{materials_text}\n\n"
                "请优先基于资料生成笔记，若资料不足再补充常识。"
            ).strip()

    input_data = NoteInput(
        topic=topic,
        notes=data.get("notes"),
        file_path=data.get("filePath"),
        length=length,
    )

    try:
        input_text = await agent._read_input(input_data)
        note_payload = await agent._generate_notes(input_text, input_data)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        err_msg = str(exc).strip() or "generation failed"
        await _update_note_meta(note_id, "error", error=err_msg)
        await _broadcast_note_event(note_id, {"type": "error", "error": err_msg})
        return

    if not isinstance(note_payload, dict) or not agent._is_valid_notes(note_payload):
        err_msg = "generation failed"
        await _update_note_meta(note_id, "error", error=err_msg)
        await _broadcast_note_event(note_id, {"type": "error", "error": err_msg})
        return

    await json_storage.set(f"note:{note_id}:notes", note_payload)
    await _update_note_meta(note_id, "generating")
    await _broadcast_note_event(note_id, {"type": "phase", "value": "notes"})
    await _broadcast_note_event(note_id, {"type": "notes", "notes": note_payload})

    try:
        await _broadcast_note_event(note_id, {"type": "phase", "value": "file"})
        pdf_path = await agent._create_pdf(note_payload)
        if pdf_path:
            file_name = Path(pdf_path).name
            file_url = f"/storage/smartnotes/{file_name}"
            await _update_note_meta(note_id, "ready", extra={"file": file_url})
            await _broadcast_note_event(note_id, {"type": "file", "file": file_url})
        else:
            await _update_note_meta(note_id, "ready")
    except asyncio.CancelledError:
        raise
    except Exception as pdf_exc:
        print(f"[smartnotes] pdf generation failed noteId={note_id}: {pdf_exc}")
        await _update_note_meta(note_id, "ready")

    await _broadcast_note_event(note_id, {"type": "done"})


async def _send_note_snapshot(websocket: WebSocket, note_id: str) -> None:
    meta = await json_storage.get(f"note:{note_id}") or {}
    notes = await json_storage.get(f"note:{note_id}:notes")
    if not isinstance(meta, dict):
        return

    status = derive_note_status(meta, notes)
    if notes:
        await _safe_send(websocket, {"type": "phase", "value": "notes"}, note_id)
        await _safe_send(websocket, {"type": "notes", "notes": notes}, note_id)
    elif status in {"pending", "generating"}:
        await _safe_send(websocket, {"type": "phase", "value": "generating"}, note_id)

    if meta.get("file"):
        await _safe_send(websocket, {"type": "phase", "value": "file"}, note_id)
        await _safe_send(websocket, {"type": "file", "file": meta["file"]}, note_id)

    if status == "error" and meta.get("error"):
        await _safe_send(websocket, {"type": "error", "error": meta["error"]}, note_id)
        return

    if status == "ready" and meta.get("file") and not _is_note_task_running(note_id):
        await _safe_send(websocket, {"type": "done"}, note_id)


@router.post("/smartnotes")
async def create_smartnotes(request: SmartNotesRequest, user: AuthUser = Depends(require_auth)):
    """创建智能笔记"""
    try:
        if not request.topic and not request.notes and not request.filePath:
            return JSONResponse(
                content={"ok": False, "error": "Provide topic, notes, or filePath"},
                status_code=400,
            )

        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        payload = {
            "topic": request.topic,
            "notes": request.notes,
            "filePath": request.filePath,
            "includeMaterials": bool(request.includeMaterials),
            "materialIds": request.materialIds or [],
            "length": request.length or "medium",
        }

        await json_storage.set(f"note:{note_id}", {
            "id": note_id,
            "title": (request.topic or "智能笔记")[:100],
            "length": request.length or "medium",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            **owner_payload(user.id, user.username),
        })
        await json_storage.set(f"note:{note_id}:payload", payload)
        _ensure_note_generation(note_id)

        return JSONResponse(
            content={
                "ok": True,
                "noteId": note_id,
                "stream": f"/ws/smartnotes?noteId={note_id}",
            },
            status_code=202,
        )

    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.websocket("/ws/smartnotes")
async def smartnotes_websocket(websocket: WebSocket):
    """智能笔记 WebSocket 端点"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    query_params = dict(websocket.query_params)
    note_id = query_params.get("noteId")
    if not note_id:
        await websocket.close(code=1008, reason="noteId required")
        return

    meta = await json_storage.get(f"note:{note_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        await websocket.close(code=1008, reason="not found")
        return

    subscribers = NOTE_SUBSCRIBERS.setdefault(note_id, set())
    subscribers.add(websocket)

    try:
        await _safe_send(websocket, {"type": "ready", "noteId": note_id}, note_id)
        await _send_note_snapshot(websocket, note_id)
        _ensure_note_generation(note_id)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    finally:
        current = NOTE_SUBSCRIBERS.get(note_id)
        if current:
            current.discard(websocket)
            if not current:
                NOTE_SUBSCRIBERS.pop(note_id, None)


@router.get("/smartnotes")
async def list_smartnotes(user: AuthUser = Depends(require_auth)):
    """列出笔记历史"""
    try:
        notes = await list_notes(user.id, user.username)
        return {"ok": True, "notes": notes}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@router.get("/smartnotes/{note_id}")
async def get_smartnote(note_id: str, user: AuthUser = Depends(require_auth)):
    """获取笔记详情"""
    try:
        if not note_id or note_id in {"undefined", "null"}:
            return {"ok": False, "error": "Invalid noteId"}, 400
        meta = await json_storage.get(f"note:{note_id}")
        notes = await json_storage.get(f"note:{note_id}:notes")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return {"ok": False, "error": "not found"}, 404
        status = derive_note_status(meta, notes)
        if status in {"pending", "generating"}:
            _ensure_note_generation(note_id)
        meta["id"] = note_id
        meta["status"] = status
        return {"ok": True, "note": meta, "notes": notes}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@router.delete("/smartnotes/{note_id}")
async def delete_smartnote(note_id: str, user: AuthUser = Depends(require_auth)):
    """删除笔记"""
    from utils.storage import delete_note

    try:
        if not note_id or note_id in {"undefined", "null"}:
            return {"ok": False, "error": "Invalid noteId"}, 400
        meta = await json_storage.get(f"note:{note_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return {"ok": False, "error": "not found"}, 404
        task = NOTE_TASKS.pop(note_id, None)
        if task and not task.done():
            task.cancel()
        NOTE_SUBSCRIBERS.pop(note_id, None)
        await delete_note(note_id)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
