"""
智能笔记 API 路由
与原 Node.js 版本完全兼容
"""
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.note_agent import NoteAgent, NoteInput
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.object_store import create_object_store
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.api_errors import safe_error_response
from utils.auth import require_auth, require_websocket_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import derive_note_status, json_storage, list_files_for_user, list_notes, owner_payload, record_belongs_to_user


router = APIRouter()
logger = logging.getLogger(__name__)


class SmartNotesRequest(BaseModel):
    topic: Optional[str] = None
    notes: Optional[str] = None
    filePath: Optional[str] = None
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    length: Optional[str] = "medium"


NOTE_TASKS: Dict[str, asyncio.Task[Any]] = {}


async def _safe_send(websocket: WebSocket, message: Dict[str, Any], note_id: str) -> bool:
    try:
        await websocket.send_json(message)
        return True
    except Exception as exc:
        print(f"[smartnotes] safe_send failed noteId={note_id}: {exc}")
        return False


def _note_channel(note_id: str) -> str:
    return f"note:{note_id}"


async def _broadcast_note_event(note_id: str, message: Dict[str, Any]) -> None:
    await publish_live_event(_note_channel(note_id), message)


async def _update_note_meta(
    note_id: str,
    status: str,
    *,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    meta = await json_storage.get(f"note:{note_id}") or {}
    if not isinstance(meta, dict):
        return {}
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


async def _note_still_exists(note_id: str) -> bool:
    return isinstance(await json_storage.get(f"note:{note_id}"), dict)


async def _build_note_material_context(note_id: str, ids: List[str], query: str) -> str:
    if not ids:
        return ""

    meta = await json_storage.get(f"note:{note_id}") or {}
    owner_id = int(meta.get("owner_id") or 0)
    owner_username = str(meta.get("owner_username") or "")
    files = await list_files_for_user(owner_id, owner_username, "student")
    return await build_selected_files_context(
        files,
        ids,
        max_chars=12000,
        snippet_chars=4000,
        query=query,
        owner_id=owner_id,
        role="student",
    )


def _is_note_task_running(note_id: str) -> bool:
    task = NOTE_TASKS.get(note_id)
    return bool(task and not task.done())


async def _ensure_note_generation(note_id: str) -> None:
    if _is_note_task_running(note_id):
        return

    lease = await acquire_task_lease(f"smartnotes:{note_id}")
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _run_note_generation(note_id)
        finally:
            await release_task_lease(lease)
            NOTE_TASKS.pop(note_id, None)

    NOTE_TASKS[note_id] = asyncio.create_task(_runner())


async def _run_note_generation_worker(note_id: str) -> None:
    lease = await acquire_task_lease(f"smartnotes:{note_id}")
    if not lease:
        return
    try:
        await _run_note_generation(note_id)
    finally:
        await release_task_lease(lease)


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
        materials_query = str(topic or data.get("notes") or "智能笔记")
        materials_text = await _build_note_material_context(note_id, material_ids, materials_query)
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
        logger.exception("Smart notes background generation failed")
        err_msg = "smart notes generation failed"
        await _update_note_meta(note_id, "error", error=err_msg)
        await _broadcast_note_event(note_id, {"type": "error", "error": err_msg})
        return

    if not isinstance(note_payload, dict) or not agent._is_valid_notes(note_payload):
        err_msg = "generation failed"
        await _update_note_meta(note_id, "error", error=err_msg)
        await _broadcast_note_event(note_id, {"type": "error", "error": err_msg})
        return

    if not await _note_still_exists(note_id):
        return

    await json_storage.set(f"note:{note_id}:notes", note_payload)
    await _update_note_meta(note_id, "generating")
    await _broadcast_note_event(note_id, {"type": "phase", "value": "notes"})
    await _broadcast_note_event(note_id, {"type": "notes", "notes": note_payload})

    try:
        await _broadcast_note_event(note_id, {"type": "phase", "value": "file"})
        pdf_path = await agent._create_pdf(note_payload)
        if not await _note_still_exists(note_id):
            return
        if pdf_path:
            file_name = Path(pdf_path).name
            object_key = f"smartnotes/{file_name}"
            file_url = await create_object_store().put_file(object_key, Path(pdf_path))
            await _update_note_meta(note_id, "ready", extra={"file": file_url, "objectKey": object_key})
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
        await dispatch_generation_task("smartnotes", note_id, _ensure_note_generation)

        return JSONResponse(
            content={
                "ok": True,
                "noteId": note_id,
                "stream": f"/ws/smartnotes?noteId={note_id}",
                "events": f"/tasks/smartnotes/{note_id}/events",
            },
            status_code=202,
        )

    except Exception as exc:
        return safe_error_response(logger, exc, "smart notes generation failed")


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

    forwarder = asyncio.create_task(forward_live_events(websocket, _note_channel(note_id)))
    await asyncio.sleep(0)

    try:
        await _safe_send(websocket, {"type": "ready", "noteId": note_id}, note_id)
        await _send_note_snapshot(websocket, note_id)
        await dispatch_generation_task("smartnotes", note_id, _ensure_note_generation)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/smartnotes")
async def list_smartnotes(user: AuthUser = Depends(require_auth)):
    """列出笔记历史"""
    try:
        notes = await list_notes(user.id, user.username)
        return {"ok": True, "notes": notes}
    except Exception as exc:
        return safe_error_response(logger, exc, "smart notes list failed")


@router.get("/smartnotes/{note_id}")
async def get_smartnote(note_id: str, user: AuthUser = Depends(require_auth)):
    """获取笔记详情"""
    try:
        if not note_id or note_id in {"undefined", "null"}:
            return JSONResponse(content={"ok": False, "error": "Invalid noteId"}, status_code=400)
        meta = await json_storage.get(f"note:{note_id}")
        notes = await json_storage.get(f"note:{note_id}:notes")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        status = derive_note_status(meta, notes)
        if status in {"pending", "generating"}:
            await dispatch_generation_task("smartnotes", note_id, _ensure_note_generation)
        meta["id"] = note_id
        meta["status"] = status
        return {"ok": True, "note": meta, "notes": notes}
    except Exception as exc:
        return safe_error_response(logger, exc, "smart note detail failed")


register_task_handler("smartnotes", _run_note_generation_worker)


@router.delete("/smartnotes/{note_id}")
async def delete_smartnote(note_id: str, user: AuthUser = Depends(require_auth)):
    """删除笔记"""
    from utils.storage import delete_note

    try:
        if not note_id or note_id in {"undefined", "null"}:
            return JSONResponse(content={"ok": False, "error": "Invalid noteId"}, status_code=400)
        meta = await json_storage.get(f"note:{note_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        task = NOTE_TASKS.pop(note_id, None)
        if task and not task.done():
            task.cancel()
        object_key = str(meta.get("objectKey") or "")
        if object_key:
            await create_object_store().delete(object_key)
        await delete_note(note_id)
        return {"ok": True}
    except Exception as exc:
        return safe_error_response(logger, exc, "smart note deletion failed")
