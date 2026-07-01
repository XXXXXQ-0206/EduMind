"""
文件库 API 路由
教师端与学生端文件库独立存储：role=student 使用 key "files"，role=teacher 使用 "files_teacher"。
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from infrastructure.object_store import ObjectStore, create_object_store
from services.document_library import (
    build_rag_context_for_user_files,
    delete_file_index,
    get_file_index_status,
    index_file_meta,
)
from utils.auth import require_auth
from utils.auth_contracts import ADMIN_USERNAME, AuthUser
from utils.storage import json_storage, legacy_files_key, list_files_for_user, user_files_key


router = APIRouter()


class RagSearchRequest(BaseModel):
    query: str = ""
    role: Optional[str] = None
    materialIds: Optional[List[str]] = None
    maxChunks: Optional[int] = 10
    maxChars: Optional[int] = 12000


def _object_store() -> ObjectStore:
    return create_object_store()


def _file_url(filename: str) -> str:
    return _object_store().url_for(f"uploads/{filename}")


def _normalize_role(role: Optional[str]) -> str:
    value = (role or "student").strip().lower()
    return value if value in {"student", "teacher"} else "student"


def _rag_updates_from_status(status: dict) -> dict:
    if not isinstance(status, dict) or not status:
        return {}
    updates = {
        "ragStatus": status.get("status"),
        "ragIndexedAt": status.get("indexed_at") or status.get("indexedAt"),
        "ragChunkCount": status.get("chunk_count") or status.get("chunkCount"),
        "ragTextChars": status.get("text_chars") or status.get("textChars"),
        "ragVectorStatus": status.get("vector_status") or status.get("vectorStatus"),
    }
    error = status.get("error")
    if error:
        updates["ragError"] = error
    return {key: value for key, value in updates.items() if value not in (None, "")}


async def _update_file_meta(key: str, file_id: str, updates: dict) -> None:
    if not updates:
        return

    def apply_updates(files):
        result = []
        for item in files if isinstance(files, list) else []:
            if isinstance(item, dict) and str(item.get("id")) == str(file_id):
                next_item = dict(item)
                next_item.update(updates)
                if not updates.get("ragError"):
                    next_item.pop("ragError", None)
                result.append(next_item)
            else:
                result.append(item)
        return result

    await json_storage.update(key, apply_updates, default=[])


async def _index_saved_files(key: str, saved: List[dict], role: str, user: AuthUser) -> None:
    for meta in saved:
        result = await index_file_meta(meta, owner_id=user.id, role=role)
        await _update_file_meta(key, result.file_id, result.to_file_updates())


@router.get("/files")
async def list_files(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    files = await list_files_for_user(user.id, user.username, role)
    files = sorted(files, key=lambda f: f.get("uploadedAt", 0), reverse=True)
    enriched = []
    for item in files:
        meta = dict(item)
        status = await get_file_index_status(str(meta.get("id") or ""))
        if status:
            meta.update(_rag_updates_from_status(status))
        enriched.append(meta)
    return {"ok": True, "files": enriched}


@router.post("/files")
async def upload_files(
    background_tasks: BackgroundTasks,
    file: List[UploadFile] = File(...),
    role: Optional[str] = Form(None),
    user: AuthUser = Depends(require_auth),
):
    normalized_role = _normalize_role(role)
    key = user_files_key(normalized_role, user.id)
    saved = []
    now = int(time.time() * 1000)
    object_store = _object_store()

    for item in file:
        if not item.filename:
            continue
        unique = uuid.uuid4().hex[:8]
        stored_name = f"{now}-{unique}-{item.filename}"
        object_key = f"uploads/{stored_name}"

        content = await item.read()
        url = await object_store.put_bytes(object_key, content)

        meta = {
            "id": str(uuid.uuid4()),
            "filename": stored_name,
            "objectKey": object_key,
            "originalName": item.filename,
            "mimeType": item.content_type or "application/octet-stream",
            "size": len(content),
            "uploadedAt": int(time.time() * 1000),
            "url": url,
            "owner_id": user.id,
            "owner_username": user.username,
            "ragStatus": "pending",
            "ragChunkCount": 0,
            "ragVectorStatus": "pending",
        }
        saved.append(meta)

    if not saved:
        return JSONResponse(content={"ok": False, "error": "no files"}, status_code=400)

    def prepend_saved(existing):
        return [*saved, *(existing if isinstance(existing, list) else [])]

    await json_storage.update(key, prepend_saved, default=[])
    background_tasks.add_task(_index_saved_files, key, saved, normalized_role, user)

    return {"ok": True, "files": saved}


@router.post("/files/rag/search")
async def search_file_library(request: RagSearchRequest, user: AuthUser = Depends(require_auth)):
    role = _normalize_role(request.role)
    files = await list_files_for_user(user.id, user.username, role)
    context = await build_rag_context_for_user_files(
        files,
        request.materialIds or [],
        owner_id=user.id,
        role=role,
        query=request.query or "",
        max_chunks=max(1, min(30, int(request.maxChunks or 10))),
        max_chars=max(1000, min(50000, int(request.maxChars or 12000))),
    )
    if context.files or context.failed_files:
        status_by_id = {
            str(item.get("id")): {
                "ragStatus": item.get("status"),
                "ragChunkCount": item.get("chunkCount"),
                "ragVectorStatus": item.get("vectorStatus"),
                "ragError": item.get("error"),
                "ragIndexedAt": item.get("indexedAt") or int(time.time() * 1000),
            }
            for item in [*context.files, *context.failed_files]
            if item.get("id")
        }
        if status_by_id:
            key = user_files_key(role, user.id)

            def sync_rag_status(existing):
                result = []
                for item in existing if isinstance(existing, list) else []:
                    file_id = str(item.get("id") or "") if isinstance(item, dict) else ""
                    if file_id in status_by_id:
                        next_item = dict(item)
                        updates = {key: value for key, value in status_by_id[file_id].items() if value not in (None, "")}
                        next_item.update(updates)
                        if not updates.get("ragError"):
                            next_item.pop("ragError", None)
                        result.append(next_item)
                    else:
                        result.append(item)
                return result

            await json_storage.update(key, sync_rag_status, default=[])
    return {
        "ok": True,
        "context": context.text,
        "chunks": context.chunks,
        "files": context.files,
        "failedFiles": context.failed_files,
    }


@router.get("/files/{file_id}/rag")
async def get_file_rag_status(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    normalized_role = _normalize_role(role)
    files = await list_files_for_user(user.id, user.username, normalized_role)
    target = next((item for item in files if str(item.get("id")) == str(file_id)), None)
    if not target:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    status = await get_file_index_status(file_id)
    return {"ok": True, "file": target, "rag": _rag_updates_from_status(status)}


@router.post("/files/{file_id}/rag/index")
async def rebuild_file_rag_index(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    normalized_role = _normalize_role(role)
    key = user_files_key(normalized_role, user.id)
    files = await list_files_for_user(user.id, user.username, normalized_role)
    target = next((item for item in files if str(item.get("id")) == str(file_id)), None)
    if not target:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    result = await index_file_meta(target, owner_id=user.id, role=normalized_role, force=True)
    updates = result.to_file_updates()
    await _update_file_meta(key, file_id, updates)
    return {"ok": True, "rag": updates}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    normalized_role = _normalize_role(role)
    keys = [user_files_key(normalized_role, user.id)]
    if user.username == ADMIN_USERNAME:
        keys.append(legacy_files_key(normalized_role))

    target = None
    matched_key = None

    for key in keys:
        def remove_file(files):
            nonlocal target, matched_key
            remain = []
            for f in (files if isinstance(files, list) else []):
                if f.get("id") == file_id:
                    target = f
                    matched_key = key
                else:
                    remain.append(f)
            return remain

        await json_storage.update(key, remove_file, default=[])
        if target:
            break

    if not target:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)

    filename = target.get("filename")
    object_key = target.get("objectKey") or (f"uploads/{filename}" if filename else "")
    if object_key:
        await _object_store().delete(object_key)
    await delete_file_index(file_id, owner_id=user.id, role=normalized_role)

    if matched_key is None:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True}
