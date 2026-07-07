"""
Audio transcription API routes.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from utils.api_errors import safe_error_response
from utils.auth import require_auth
from utils.auth_contracts import AuthUser
from utils.transcription import build_study_materials, transcribe_audio_bytes


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/transcriber")
async def transcribe_audio_handler(
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_auth),
):
    try:
        filename = (file.filename or "audio.webm").strip() or "audio.webm"
        content = await file.read()
        if not content:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "上传文件为空"},
            )

        result = await transcribe_audio_bytes(
            file_bytes=content,
            filename=filename,
            content_type=file.content_type,
        )
        study_materials = await build_study_materials(result.get("text") or "")

        return {
            "ok": True,
            "transcription": result.get("text") or "",
            "provider": result.get("provider") or "",
            "confidence": result.get("confidence"),
            "studyMaterials": study_materials,
        }
    except Exception as exc:
        return safe_error_response(logger, exc, "audio transcription failed")
