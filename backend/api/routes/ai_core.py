"""Internal AI Core service routes."""
from __future__ import annotations

from typing import Dict, List, Optional

import json

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from config import config
from utils.llm import invoke_llm_local, stream_llm_local


router = APIRouter(prefix="/ai")


class InvokeRequest(BaseModel):
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = None
    provider: Optional[str] = None


@router.post("/internal/invoke")
async def invoke_llm_handler(
    payload: InvokeRequest,
    x_internal_service_token: str | None = Header(default=None),
):
    if config.internal_service_token and x_internal_service_token != config.internal_service_token:
        raise HTTPException(status_code=403, detail="invalid internal service token")
    try:
        text = await invoke_llm_local(
            payload.messages,
            max_tokens=payload.max_tokens,
            provider=payload.provider,
        )
        return {"ok": True, "text": text}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/internal/invoke/stream")
async def stream_llm_handler(
    payload: InvokeRequest,
    x_internal_service_token: str | None = Header(default=None),
):
    if config.internal_service_token and x_internal_service_token != config.internal_service_token:
        raise HTTPException(status_code=403, detail="invalid internal service token")

    async def stream():
        try:
            async for chunk in stream_llm_local(
                payload.messages,
                max_tokens=payload.max_tokens,
                provider=payload.provider,
            ):
                yield json.dumps({"type": "delta", "delta": chunk}, ensure_ascii=False) + "\n"
            yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"type": "error", "error": str(exc)}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
