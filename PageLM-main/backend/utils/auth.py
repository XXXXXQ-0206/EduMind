"""
Auth helpers for HTTP and WebSocket routes.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Request, WebSocket, status

from utils.auth_db import AuthUser, auth_db


def get_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    value = authorization.strip()
    if not value.lower().startswith("bearer "):
        return None
    token = value[7:].strip()
    return token or None


def resolve_user_from_token(token: Optional[str]) -> Optional[AuthUser]:
    if not token:
        return None
    return auth_db.get_user_by_token(token)


def require_auth(authorization: Optional[str] = Header(default=None)) -> AuthUser:
    user = resolve_user_from_token(get_bearer_token(authorization))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录后再访问",
        )
    return user


def get_request_user(request: Request) -> Optional[AuthUser]:
    return resolve_user_from_token(get_bearer_token(request.headers.get("authorization")))


async def require_websocket_auth(websocket: WebSocket) -> Optional[AuthUser]:
    token = websocket.query_params.get("token")
    user = resolve_user_from_token(token)
    if not user:
        await websocket.close(code=4401, reason="Unauthorized")
        return None
    return user
