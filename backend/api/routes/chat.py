"""
聊天 API 路由
"""
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.task_lease import TaskLease, acquire_task_lease, release_task_lease
from utils.auth import require_auth, require_websocket_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import (
    add_message,
    create_chat,
    delete_chat,
    get_chat,
    get_messages,
    list_chats,
    list_files_for_user,
    record_belongs_to_user,
    update_chat_settings,
)
from utils.llm import invoke_llm


router = APIRouter()
CHAT_TASKS: Dict[str, asyncio.Task[Any]] = {}


class ChatRequest(BaseModel):
    q: str
    chatId: Optional[str] = None
    length: Optional[str] = "Short"  # Short, Medium, Long
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    role: Optional[str] = None  # "student" | "teacher"，用于教师端/学生端独立存储


async def claim_generation(chat_id: str) -> Optional[TaskLease]:
    return await acquire_task_lease(f"chat:{chat_id}")


async def release_generation(lease: Optional[TaskLease]) -> None:
    await release_task_lease(lease)


def _chat_channel(chat_id: str) -> str:
    return f"chat:{chat_id}"


async def _send_chat_event(chat_id: str, message: Dict[str, Any]) -> None:
    await publish_live_event(_chat_channel(chat_id), message)


async def wait_for_disconnect(websocket: WebSocket) -> None:
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass


def _is_chat_task_running(chat_id: str) -> bool:
    task = CHAT_TASKS.get(chat_id)
    return bool(task and not task.done())


async def _ensure_chat_generation(chat_id: str) -> None:
    if _is_chat_task_running(chat_id):
        return

    lease = await claim_generation(chat_id)
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _run_chat_generation(chat_id)
        finally:
            await release_generation(lease)
            CHAT_TASKS.pop(chat_id, None)

    CHAT_TASKS[chat_id] = asyncio.create_task(_runner())


async def _run_chat_generation_worker(chat_id: str) -> None:
    lease = await claim_generation(chat_id)
    if not lease:
        return
    try:
        await _run_chat_generation(chat_id)
    finally:
        await release_generation(lease)


async def _run_chat_generation(chat_id: str) -> None:
    try:
        chat_meta = await get_chat(chat_id) or {}
        if not isinstance(chat_meta, dict):
            return

        history = await get_messages(chat_id)
        if not history or history[-1].get("role") != "user":
            return

        await _send_chat_event(chat_id, {"type": "phase", "value": "generating"})

        length = chat_meta.get("length") or "Short"
        materials_cfg = {
            "include": bool(chat_meta.get("includeMaterials")),
            "ids": chat_meta.get("materialIds") or [],
        }
        use_materials = bool(materials_cfg.get("include"))
        material_ids = materials_cfg.get("ids") or []

        chat_scope = (chat_meta.get("scope") or "student").strip().lower()
        if chat_scope not in ("student", "teacher"):
            chat_scope = "student"
        owner_id = int(chat_meta.get("owner_id") or 0)
        owner_username = str(chat_meta.get("owner_username") or "")

        async def build_material_context(ids: List[str]) -> str:
            files = await list_files_for_user(owner_id, owner_username, chat_scope)
            if not files:
                return ""
            selected_ids = ids or [f.get("id") for f in files if f.get("id")]
            if not selected_ids:
                return ""
            return await build_selected_files_context(files, selected_ids, max_chars=8000, snippet_chars=8000)

        length_prompts = {
            "Short": "请用约200字回答问题，保持简洁明了。",
            "Medium": "请用约400字回答问题，提供适当的细节和解释。",
            "Long": "请用约600字回答问题，提供详细的解释和例子。"
        }
        system_prompt = length_prompts.get(length, length_prompts["Short"])
        if use_materials and material_ids:
            materials_text = await build_material_context(material_ids)
            if materials_text:
                assistant_role = "教学助手" if chat_scope == "teacher" else "学习助手"
                system_prompt += (
                    f"\n你是{assistant_role}，请优先基于以下资料回答问题。"
                    "如果资料中没有明确答案，请说明并给出合理推断。"
                    "\n资料内容:\n" + materials_text
                )
        elif use_materials:
            materials_text = await build_material_context([])
            if materials_text:
                assistant_role = "教学助手" if chat_scope == "teacher" else "学习助手"
                system_prompt += (
                    f"\n你是{assistant_role}，请优先基于以下资料回答问题。"
                    "如果资料中没有明确答案，请说明并给出合理推断。"
                    "\n资料内容:\n" + materials_text
                )

        relevant_history = history[-20:]
        messages = [{"role": "system", "content": system_prompt}]
        for msg in relevant_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        answer = await invoke_llm(messages)
        await add_message(chat_id, "assistant", answer)
        await _send_chat_event(chat_id, {"type": "answer", "answer": answer})
        await _send_chat_event(chat_id, {"type": "done"})
    except Exception as exc:
        await _send_chat_event(chat_id, {"type": "error", "error": str(exc)})
        await _send_chat_event(chat_id, {"type": "done"})


@router.post("/chat")
async def create_chat_handler(request: ChatRequest, user: AuthUser = Depends(require_auth)):
    """创建或继续聊天会话"""
    try:
        q = request.q
        chat_id = request.chatId
        length = request.length or "Short"
        include_materials = bool(request.includeMaterials)
        material_ids = request.materialIds or []

        if not q:
            return JSONResponse(
                content={"ok": False, "error": "q required"},
                status_code=400
            )

        scope = (request.role or "student").strip().lower()
        if scope not in ("student", "teacher"):
            scope = "student"

        # 获取或创建聊天会话
        chat = await get_chat(chat_id) if chat_id else None
        if chat and not record_belongs_to_user(chat, user.id, user.username):
            chat = None

        if not chat:
            chat = await create_chat(
                title=q,
                scope=scope,
                owner_id=user.id,
                owner_username=user.username,
                response_length=length,
                include_materials=include_materials,
                material_ids=material_ids,
            )
        else:
            await update_chat_settings(
                chat_id=chat["id"],
                response_length=length,
                include_materials=include_materials,
                material_ids=material_ids,
            )

        chat_id = chat["id"]

        # 保存用户消息和长度设置
        await add_message(chat_id, "user", q)
        await dispatch_generation_task("chat", chat_id, _ensure_chat_generation)

        # 返回 202 和 WebSocket URL
        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "chatId": chat_id,
                "stream": f"/ws/chat?chatId={chat_id}",
            }
        )

    except Exception as e:
        print(f"[ERROR] Failed to create chat: {e}")
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500
        )


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """聊天 WebSocket 端点"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    query_params = dict(websocket.query_params)
    chat_id = query_params.get("chatId")
    print(f"[DEBUG] WebSocket connected with chatId: {chat_id}")

    if not chat_id or chat_id == "undefined" or chat_id == "null":
        print(f"[DEBUG] Invalid chatId, closing connection")
        await websocket.close(code=1008, reason="Invalid chatId")
        return

    forwarder = asyncio.create_task(forward_live_events(websocket, _chat_channel(chat_id)))
    await asyncio.sleep(0)
    await websocket.send_json({"type": "ready", "chatId": chat_id})

    try:
        chat_meta = await get_chat(chat_id) or {}
        if not chat_meta or not record_belongs_to_user(chat_meta, user.id, user.username):
            await websocket.close(code=1008, reason="not found")
            return

        history = await get_messages(chat_id)
        print(f"[DEBUG] Got {len(history) if history else 0} messages for chat {chat_id}")

        needs_answer = False
        if history:
            last_msg = history[-1]
            print(f"[DEBUG] Last message role: {last_msg.get('role')}")
            if last_msg.get("role") == "user":
                needs_answer = True

        if not needs_answer:
            if history and history[-1].get("role") == "assistant":
                await websocket.send_json({"type": "answer", "answer": history[-1].get("content", "")})
                await websocket.send_json({"type": "done"})
            print(f"[DEBUG] No pending message, closing connection")
            await websocket.close(code=1000, reason="No pending message")
            return

        await dispatch_generation_task("chat", chat_id, _ensure_chat_generation)
        await wait_for_disconnect(websocket)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ERROR] chat websocket failed chatId={chat_id}: {e}")
        await _send_chat_event(chat_id, {"type": "error", "error": str(e)})
        await _send_chat_event(chat_id, {"type": "done"})
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/chats")
async def list_chats_handler(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    """列出聊天会话；role=student|teacher 时仅返回该端会话"""
    try:
        scope = (role or "").strip().lower() or None
        if scope is not None and scope not in ("student", "teacher"):
            scope = None
        chats = await list_chats(scope=scope, user_id=user.id, username=user.username)
        return {"ok": True, "chats": chats}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.get("/chats/{chat_id}")
async def get_chat_handler(chat_id: str, user: AuthUser = Depends(require_auth)):
    """获取聊天会话详情"""
    try:
        # 验证 chatId
        if not chat_id or chat_id == "undefined" or chat_id == "null":
            return JSONResponse(content={"error": "Invalid chatId"}, status_code=400)

        print(f"[DEBUG] Getting chat details for: {chat_id}")

        chat = await get_chat(chat_id)

        if not chat or not record_belongs_to_user(chat, user.id, user.username):
            return JSONResponse(content={"error": "not found"}, status_code=404)

        messages = await get_messages(chat_id)

        return {"ok": True, "chat": chat, "messages": messages}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.delete("/chats/{chat_id}")
async def delete_chat_handler(chat_id: str, user: AuthUser = Depends(require_auth)):
    """删除聊天会话"""
    try:
        if not chat_id or chat_id == "undefined" or chat_id == "null":
            return JSONResponse(content={"ok": False, "error": "Invalid chatId"}, status_code=400)
        chat = await get_chat(chat_id)
        if not chat or not record_belongs_to_user(chat, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        await delete_chat(chat_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


register_task_handler("chat", _run_chat_generation_worker)
