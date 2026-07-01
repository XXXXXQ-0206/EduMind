"""
文件库 API 路由
教师端与学生端文件库独立存储：role=student 使用 key "files"，role=teacher 使用 "files_teacher"。
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from infrastructure.object_store import ObjectStore, create_object_store
from utils.auth import require_auth
from utils.auth_contracts import ADMIN_USERNAME, AuthUser
from utils.storage import json_storage, legacy_files_key, list_files_for_user, user_files_key


router = APIRouter()


def _object_store() -> ObjectStore:
    return create_object_store()


def _file_url(filename: str) -> str:
    return _object_store().url_for(f"uploads/{filename}")


@router.get("/files")
async def list_files(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    files = await list_files_for_user(user.id, user.username, role)
    files = sorted(files, key=lambda f: f.get("uploadedAt", 0), reverse=True)
    return {"ok": True, "files": files}


@router.post("/files")
async def upload_files(file: List[UploadFile] = File(...), role: Optional[str] = Form(None), user: AuthUser = Depends(require_auth)):
    key = user_files_key(role, user.id)
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
        }
        saved.append(meta)

    if not saved:
        return JSONResponse(content={"ok": False, "error": "no files"}, status_code=400)

    def prepend_saved(existing):
        return [*saved, *(existing if isinstance(existing, list) else [])]

    await json_storage.update(key, prepend_saved, default=[])

    return {"ok": True, "files": saved}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    keys = [user_files_key(role, user.id)]
    if user.username == ADMIN_USERNAME:
        keys.append(legacy_files_key(role))

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

    if matched_key is None:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True}
