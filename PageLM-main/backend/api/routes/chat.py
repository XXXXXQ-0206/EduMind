"""
聊天 API 路由
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiofiles

from config import config
from utils.auth import require_auth, require_websocket_auth
from utils.auth_db import AuthUser, auth_db
from utils.storage import list_files_for_user
from utils.parser import extract_text_from_file
from utils.llm import invoke_llm
from utils.websocket import manager


router = APIRouter()
generation_guard = asyncio.Lock()
generating_chats: set[str] = set()


class ChatRequest(BaseModel):
    q: str
    chatId: Optional[str] = None
    length: Optional[str] = "Short"  # Short, Medium, Long
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    role: Optional[str] = None  # "student" | "teacher"，用于教师端/学生端独立存储


async def claim_generation(chat_id: str) -> bool:
    async with generation_guard:
        if chat_id in generating_chats:
            return False
        generating_chats.add(chat_id)
        return True


async def release_generation(chat_id: str) -> None:
    async with generation_guard:
        generating_chats.discard(chat_id)


async def wait_for_disconnect(websocket: WebSocket, chat_id: str) -> None:
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except RuntimeError:
        manager.disconnect(websocket, chat_id)


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
        chat = auth_db.get_chat(user.id, chat_id) if chat_id else None

        if not chat:
            chat = auth_db.create_chat(
                user_id=user.id,
                title=q,
                scope=scope,
                response_length=length,
                include_materials=include_materials,
                material_ids=material_ids,
            )
        else:
            auth_db.update_chat_settings(
                user_id=user.id,
                chat_id=chat["id"],
                response_length=length,
                include_materials=include_materials,
                material_ids=material_ids,
            )

        chat_id = chat["id"]

        # 保存用户消息和长度设置
        auth_db.add_message(user.id, chat_id, "user", q)

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
    claimed_generation = False

    # 获取 chatId
    query_params = dict(websocket.query_params)
    chat_id = query_params.get("chatId")

    print(f"[DEBUG] WebSocket connected with chatId: {chat_id}")

    # 验证 chatId
    if not chat_id or chat_id == "undefined" or chat_id == "null":
        print(f"[DEBUG] Invalid chatId, closing connection")
        manager.disconnect(websocket, chat_id or "")
        await websocket.close(code=1008, reason="Invalid chatId")
        return

    # 连接到管理器
    await manager.connect(websocket, chat_id)

    # 发送 ready 消息
    await manager.send_message({"type": "ready", "chatId": chat_id}, chat_id)

    try:
        # 获取历史消息
        history = auth_db.get_messages(user.id, chat_id)

        print(f"[DEBUG] Got {len(history) if history else 0} messages for chat {chat_id}")

        # 检查是否需要生成回答（最后一条是用户消息且没有助手回复）
        needs_answer = False
        if history:
            last_msg = history[-1]
            print(f"[DEBUG] Last message role: {last_msg.get('role')}")
            if last_msg.get("role") == "user":
                needs_answer = True

        if not needs_answer:
            # 没有待处理的消息，等待客户端发送或直接关闭
            # 这里我们选择直接返回，因为 POST /chat 已经创建了会话
            print(f"[DEBUG] No pending message, closing connection")
            manager.disconnect(websocket, chat_id)
            await websocket.close(code=1000, reason="No pending message")
            return

        claimed_generation = await claim_generation(chat_id)
        if not claimed_generation:
            print(f"[DEBUG] Chat {chat_id} already generating, keep socket open for broadcast")
            await wait_for_disconnect(websocket, chat_id)
            return

        # 发送生成阶段
        await manager.send_message({"type": "phase", "value": "generating"}, chat_id)

        # 获取长度设置
        chat_meta = auth_db.get_chat(user.id, chat_id) or {}
        length = chat_meta.get("length") or "Short"
        materials_cfg = {
            "include": bool(chat_meta.get("includeMaterials")),
            "ids": chat_meta.get("materialIds") or [],
        }
        use_materials = bool(materials_cfg.get("include"))
        material_ids = materials_cfg.get("ids") or []

        async def read_sidecar_text(file_path: str) -> str:
            txt_path = Path(file_path + ".txt")
            if not txt_path.exists():
                return ""
            try:
                async with aiofiles.open(txt_path, "r", encoding="utf-8") as f:
                    return await f.read()
            except Exception:
                return ""

        chat_scope = (chat_meta.get("scope") or "student").strip().lower()
        if chat_scope not in ("student", "teacher"):
            chat_scope = "student"

        async def build_material_context(ids: List[str]) -> str:
            files = await list_files_for_user(user.id, user.username, chat_scope)
            if not files:
                return ""
            file_map = {f.get("id"): f for f in files if f.get("id")}
            selected_ids = ids or [f.get("id") for f in files if f.get("id")]
            if not selected_ids:
                return ""
            max_chars = 8000
            parts: List[str] = []
            used = 0

            for fid in selected_ids:
                meta = file_map.get(fid)
                if not meta:
                    continue
                filename = meta.get("filename")
                if not filename:
                    continue
                file_path = str(config.storage_dir / "uploads" / filename)
                text = ""
                if not text:
                    text = await read_sidecar_text(file_path)
                if not text:
                    try:
                        text = await extract_text_from_file(file_path, meta.get("mimeType"))
                    except Exception:
                        text = ""
                if not text:
                    continue
                remaining = max_chars - used
                if remaining <= 0:
                    break
                snippet = text[:remaining]
                header = f"\n\n[资料] {meta.get('originalName') or filename}\n"
                parts.append(header + snippet)
                used += len(snippet)

            return "".join(parts).strip()

        # 根据长度设置生成系统提示
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

        # 获取历史消息（最近20条）
        relevant_history = history[-20:]

        # 调用 LLM - 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        for msg in relevant_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        print(f"[DEBUG] Calling LLM with {len(messages)} messages, length={length}")
        answer = await invoke_llm(messages)
        print(f"[DEBUG] Got answer from LLM, length: {len(answer)}")

        # 添加助手消息
        auth_db.add_message(user.id, chat_id, "assistant", answer)

        # 发送答案
        await manager.send_message({"type": "answer", "answer": answer}, chat_id)

        # 发送完成消息
        await manager.send_message({"type": "done"}, chat_id)
        await wait_for_disconnect(websocket, chat_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except Exception as e:
        await manager.send_message({"type": "error", "error": str(e)}, chat_id)
        manager.disconnect(websocket, chat_id)
    finally:
        if chat_id and claimed_generation:
            await release_generation(chat_id)


@router.get("/chats")
async def list_chats_handler(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    """列出聊天会话；role=student|teacher 时仅返回该端会话"""
    try:
        scope = (role or "").strip().lower() or None
        if scope is not None and scope not in ("student", "teacher"):
            scope = None
        chats = auth_db.list_chats(user.id, scope=scope)
        return {"ok": True, "chats": chats}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@router.get("/chats/{chat_id}")
async def get_chat_handler(chat_id: str, user: AuthUser = Depends(require_auth)):
    """获取聊天会话详情"""
    try:
        # 验证 chatId
        if not chat_id or chat_id == "undefined" or chat_id == "null":
            return {"error": "Invalid chatId"}, 400

        print(f"[DEBUG] Getting chat details for: {chat_id}")

        chat = auth_db.get_chat(user.id, chat_id)

        if not chat:
            return {"error": "not found"}, 404

        messages = auth_db.get_messages(user.id, chat_id)

        return {"ok": True, "chat": chat, "messages": messages}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@router.delete("/chats/{chat_id}")
async def delete_chat_handler(chat_id: str, user: AuthUser = Depends(require_auth)):
    """删除聊天会话"""
    try:
        if not chat_id or chat_id == "undefined" or chat_id == "null":
            return {"ok": False, "error": "Invalid chatId"}, 400
        auth_db.delete_chat(user.id, chat_id)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
