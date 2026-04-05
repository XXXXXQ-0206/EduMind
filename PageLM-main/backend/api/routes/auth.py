from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from utils.auth import get_bearer_token, require_auth, resolve_user_from_token
from utils.auth_db import AuthUser, auth_db


router = APIRouter(prefix="/auth")


class AuthPayload(BaseModel):
    username: str
    password: str


class ChangePasswordPayload(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class DeleteAccountPayload(BaseModel):
    password: str


def _session_payload(token: str, user_id: int):
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    return {
        "ok": True,
        "token": token,
        "user": user.as_dict(),
    }


@router.post("/register")
async def register(payload: AuthPayload):
    try:
        user = auth_db.create_user(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    token = auth_db.create_session(user.id)
    return _session_payload(token, user.id)


@router.post("/login")
async def login(payload: AuthPayload):
    user = auth_db.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth_db.create_session(user.id)
    return _session_payload(token, user.id)


@router.post("/logout")
async def logout(authorization: str | None = Header(default=None)):
    token = get_bearer_token(authorization)
    if token:
        auth_db.delete_session(token)
    return {"ok": True}


@router.get("/me")
async def me(authorization: str | None = Header(default=None)):
    user = resolve_user_from_token(get_bearer_token(authorization))
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    return {"ok": True, "user": user.as_dict()}


@router.post("/change-password")
async def change_password(payload: ChangePasswordPayload, user: AuthUser = Depends(require_auth)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    try:
        auth_db.change_password(user.id, payload.old_password, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/delete-account")
async def delete_account(payload: DeleteAccountPayload, user: AuthUser = Depends(require_auth)):
    try:
        auth_db.delete_user(user.id, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}
