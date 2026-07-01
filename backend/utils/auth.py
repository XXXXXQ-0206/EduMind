"""
Auth helpers for HTTP and WebSocket routes.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Request, WebSocket, status

from config import config
from utils.auth_contracts import AuthUser


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
    if (config.auth_validation_mode or "local").strip().lower() == "remote":
        return resolve_user_from_identity_service(token)
    return resolve_user_from_local_store(token)


def resolve_user_from_local_store(token: str) -> Optional[AuthUser]:
    from utils.auth_db import auth_db

    return auth_db.get_user_by_token(token)


def resolve_user_from_identity_service(token: str) -> Optional[AuthUser]:
    try:
        import httpx

        headers = {"Authorization": f"Bearer {token}"}
        if config.internal_service_token:
            headers["X-Internal-Service-Token"] = config.internal_service_token
        response = httpx.post(
            f"{config.identity_service_url.rstrip('/')}/auth/internal/resolve",
            headers=headers,
            timeout=5.0,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        if not payload.get("ok") or not isinstance(payload.get("user"), dict):
            return None
        user = payload["user"]
        return AuthUser(
            id=int(user["id"]),
            username=str(user["username"]),
            created_at=str(user.get("createdAt") or user.get("created_at") or ""),
        )
    except Exception:
        return None


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
