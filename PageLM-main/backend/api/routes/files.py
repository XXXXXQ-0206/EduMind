"""
文件库 API 路由
教师端与学生端文件库独立存储：role=student 使用 key "files"，role=teacher 使用 "files_teacher"。
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from config import config
from utils.auth import require_auth
from utils.auth_db import ADMIN_USERNAME, AuthUser
from utils.storage import json_storage, legacy_files_key, list_files_for_user, user_files_key


router = APIRouter()


def _uploads_dir() -> Path:
    base = config.storage_dir / "uploads"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _file_url(filename: str) -> str:
    return f"{config.backend_url}/storage/uploads/{filename}"


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
    upload_dir = _uploads_dir()

    for item in file:
        if not item.filename:
            continue
        unique = uuid.uuid4().hex[:8]
        stored_name = f"{now}-{unique}-{item.filename}"
        dest = upload_dir / stored_name

        content = await item.read()
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        meta = {
            "id": str(uuid.uuid4()),
            "filename": stored_name,
            "originalName": item.filename,
            "mimeType": item.content_type or "application/octet-stream",
            "size": len(content),
            "uploadedAt": int(time.time() * 1000),
            "url": _file_url(stored_name),
            "owner_id": user.id,
            "owner_username": user.username,
        }
        saved.append(meta)

    if not saved:
        return JSONResponse(content={"ok": False, "error": "no files"}, status_code=400)

    existing = await json_storage.get(key) or []
    await json_storage.set(key, saved + existing)

    return {"ok": True, "files": saved}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    keys = [user_files_key(role, user.id)]
    if user.username == ADMIN_USERNAME:
        keys.append(legacy_files_key(role))

    target = None
    matched_key = None

    for key in keys:
        files = await json_storage.get(key) or []
        remain = []
        for f in files:
            if f.get("id") == file_id:
                target = f
                matched_key = key
            else:
                remain.append(f)
        if target:
            await json_storage.set(key, remain)
            break

    if not target:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)

    filename = target.get("filename")
    if filename:
        path = _uploads_dir() / filename
        if path.exists():
            path.unlink()

    if matched_key is None:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True}
