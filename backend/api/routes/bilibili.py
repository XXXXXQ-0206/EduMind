"""
B站视频搜索路由
通过 Node MCP Bridge 转发查询请求
"""
import logging
import os
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
import httpx
from utils.api_errors import safe_error_response
from utils.auth import require_auth
from utils.auth_contracts import AuthUser


router = APIRouter()
logger = logging.getLogger(__name__)


def _bridge_base_url() -> str:
    return os.getenv("BILIBILI_BRIDGE_URL", "http://127.0.0.1:5001")


@router.get("/api/bilibili/search")
async def bilibili_search(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    user: AuthUser = Depends(require_auth),
):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{_bridge_base_url()}/api/bilibili/search",
                params={"keyword": keyword},
            )

        if resp.status_code >= 400:
            detail = resp.text
            return JSONResponse(
                status_code=resp.status_code,
                content={"ok": False, "error": detail or "bilibili bridge request failed"},
            )

        data = resp.json()
        items = data.get("items") if isinstance(data, dict) else []
        return {"ok": True, "keyword": keyword, "items": items or []}

    except httpx.RequestError as exc:
        return safe_error_response(logger, exc, "bilibili bridge unavailable", status_code=503)
    except Exception as exc:
        return safe_error_response(logger, exc, "bilibili search failed")
