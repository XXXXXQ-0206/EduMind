"""
Debate routes with websocket-based AI rebuttal and analysis.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.auth import get_request_user
from utils.feature_support import compact_text, ensure_string_list, safe_json_loads
from utils.llm import invoke_llm
from utils.storage import json_storage
from utils.websocket import manager


router = APIRouter()

_debate_generation_lock = asyncio.Lock()
_debate_generating: set[str] = set()
_analysis_generation_lock = asyncio.Lock()
_analysis_generating: set[str] = set()


class DebateStartRequest(BaseModel):
    topic: str
    position: str


class DebateArgumentRequest(BaseModel):
    argument: str


def _debate_key(debate_id: str) -> str:
    return f"debate:{debate_id}"


def _analysis_key(debate_id: str) -> str:
    return f"debate:{debate_id}:analysis"


async def _claim(set_name: set[str], guard: asyncio.Lock, key: str) -> bool:
    async with guard:
        if key in set_name:
            return False
        set_name.add(key)
        return True


async def _release(set_name: set[str], guard: asyncio.Lock, key: str) -> None:
    async with guard:
        set_name.discard(key)


async def _list_debates() -> List[Dict[str, Any]]:
    index = await json_storage.get("debates:index")
    return index if isinstance(index, list) else []


async def _save_index_entry(session: Dict[str, Any]) -> None:
    items = await _list_debates()
    filtered = [item for item in items if item.get("id") != session.get("id")]
    filtered.insert(
        0,
        {
            "id": session.get("id"),
            "topic": session.get("topic"),
            "position": session.get("position"),
            "createdAt": session.get("createdAt"),
            "status": session.get("status"),
            "winner": session.get("winner"),
            "updatedAt": session.get("updatedAt"),
        },
    )
    await json_storage.set("debates:index", filtered[:200])


async def _load_session(debate_id: str) -> Optional[Dict[str, Any]]:
    session = await json_storage.get(_debate_key(debate_id))
    return session if isinstance(session, dict) else None


async def _save_session(session: Dict[str, Any]) -> None:
    session["updatedAt"] = int(time.time() * 1000)
    await json_storage.set(_debate_key(str(session["id"])), session)
    await _save_index_entry(session)


def _ai_position(user_position: str) -> str:
    return "against" if user_position == "for" else "for"


def _history_for_prompt(messages: List[Dict[str, Any]]) -> str:
    trimmed = messages[-10:]
    lines: List[str] = []
    for item in trimmed:
        role = "User" if item.get("role") == "user" else "AI"
        lines.append(f"{role}: {compact_text(str(item.get('content') or ''), 1200)}")
    return "\n".join(lines)


async def _stream_text(session_id: str, text: str) -> None:
    remaining = text or ""
    while remaining:
        chunk = remaining[:28]
        remaining = remaining[28:]
        await manager.send_message({"type": "ai_token", "token": chunk}, session_id)
        await asyncio.sleep(0.015)


async def _generate_ai_reply(debate_id: str) -> None:
    claimed = await _claim(_debate_generating, _debate_generation_lock, debate_id)
    if not claimed:
        return

    try:
        session = await _load_session(debate_id)
        if not session:
            return
        if session.get("status") not in (None, "active"):
            return

        messages = list(session.get("messages") or [])
        if not messages or messages[-1].get("role") != "user":
            return

        await manager.send_message({"type": "ai_thinking"}, debate_id)

        system_prompt = """
You are an AI debate opponent.
Return only one JSON object:
{
  "reply": "string",
  "concede": false,
  "reason": "string"
}

Rules:
- Debate hard but fairly.
- Use the opposite stance from the user.
- Respond with evidence, logic, and direct rebuttal.
- Keep the reply under 260 Chinese characters unless the debate is in English.
- Set concede=true only if the user's latest argument clearly defeats your side.
- Output JSON only.
""".strip()
        user_prompt = f"""
Topic: {session.get("topic")}
User position: {session.get("position")}
AI position: {_ai_position(str(session.get("position") or "for"))}

Debate history:
{_history_for_prompt(messages)}

Latest user argument:
{messages[-1].get("content")}
""".strip()

        raw = await invoke_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1200,
        )
        parsed = safe_json_loads(raw) if raw else None

        concede = bool(isinstance(parsed, dict) and parsed.get("concede"))
        reason = str(parsed.get("reason") or "").strip() if isinstance(parsed, dict) else ""
        reply = str(parsed.get("reply") or "").strip() if isinstance(parsed, dict) else ""
        if not reply and raw:
            reply = raw.strip()

        if concede:
            session["status"] = "ai_conceded"
            session["winner"] = "user"
            session.setdefault("messages", []).append(
                {
                    "role": "assistant",
                    "content": f"我必须承认在这场辩论中失败了。{reason or '你的论证更完整、更有说服力。'}",
                    "timestamp": int(time.time() * 1000),
                }
            )
            await _save_session(session)
            await manager.send_message({"type": "ai_concede", "reason": reason or "你的论证更完整、更有说服力。"}, debate_id)
            return

        if not reply:
            reply = "你的论点有一定力度，但仍存在证据不足与推理跳跃的问题。若不能进一步证明因果关系，你的立场依旧站不稳。"

        await _stream_text(debate_id, reply)
        session.setdefault("messages", []).append(
            {
                "role": "assistant",
                "content": reply,
                "timestamp": int(time.time() * 1000),
            }
        )
        await _save_session(session)
        await manager.send_message({"type": "ai_complete", "content": reply}, debate_id)
    except Exception as exc:
        await manager.send_message({"type": "error", "error": str(exc)}, debate_id)
    finally:
        await _release(_debate_generating, _debate_generation_lock, debate_id)


def _fallback_analysis(session: Dict[str, Any]) -> Dict[str, Any]:
    status = str(session.get("status") or "completed")
    winner = str(session.get("winner") or "")
    if winner not in ("user", "ai", "draw"):
        winner = "ai" if status == "user_surrendered" else "user" if status == "ai_conceded" else "draw"
    topic = str(session.get("topic") or "本场辩论")
    return {
        "winner": winner,
        "reason": "胜负根据让步状态、论点完整度与反驳力度综合判断。",
        "userStrengths": ["表达清晰", "能够围绕主题展开论证"],
        "aiStrengths": ["反驳结构完整", "会主动指出论证中的漏洞"],
        "userWeaknesses": ["可补充更具体的事实与案例"],
        "aiWeaknesses": ["部分表述偏概括，可进一步给出细节"],
        "keyMoments": [f"{topic} 中双方围绕核心论点进行了直接交锋。"],
        "overallAssessment": "这是一场有清晰对立立场的辩论；若继续优化，应进一步强化证据链与反驳的针对性。",
    }


async def _generate_analysis(debate_id: str) -> None:
    claimed = await _claim(_analysis_generating, _analysis_generation_lock, debate_id)
    if not claimed:
        return
    channel = f"debate-analysis:{debate_id}"

    try:
        session = await _load_session(debate_id)
        if not session:
            await manager.send_message({"type": "error", "error": "debate not found"}, channel)
            return

        cached = await json_storage.get(_analysis_key(debate_id))
        if isinstance(cached, dict):
            await manager.send_message({"type": "complete", "analysis": cached, "session": session}, channel)
            return

        await manager.send_message({"type": "phase", "value": "整理辩论记录"}, channel)
        await asyncio.sleep(0.05)
        await manager.send_message({"type": "phase", "value": "评估双方论证强度"}, channel)

        system_prompt = """
You are a debate judge.
Return only one JSON object with this schema:
{
  "winner": "user|ai|draw",
  "reason": "string",
  "userStrengths": ["string"],
  "aiStrengths": ["string"],
  "userWeaknesses": ["string"],
  "aiWeaknesses": ["string"],
  "keyMoments": ["string"],
  "overallAssessment": "string"
}

Rules:
- Use concise Chinese if the debate topic is Chinese; otherwise use English.
- Base the verdict on argument quality, evidence, responsiveness, and consistency.
- Provide 2-4 bullets per strengths/weaknesses list when possible.
- Output JSON only.
""".strip()
        user_prompt = f"""
Topic: {session.get("topic")}
User position: {session.get("position")}
AI position: {_ai_position(str(session.get("position") or "for"))}
Status: {session.get("status")}

Transcript:
{_history_for_prompt(list(session.get("messages") or []))}
""".strip()

        raw = await invoke_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1600,
        )
        parsed = safe_json_loads(raw)
        analysis = parsed if isinstance(parsed, dict) else _fallback_analysis(session)

        winner = str(analysis.get("winner") or "")
        if winner not in ("user", "ai", "draw"):
            winner = _fallback_analysis(session)["winner"]
        analysis = {
            "winner": winner,
            "reason": str(analysis.get("reason") or _fallback_analysis(session)["reason"]).strip(),
            "userStrengths": ensure_string_list(analysis.get("userStrengths"), limit=4),
            "aiStrengths": ensure_string_list(analysis.get("aiStrengths"), limit=4),
            "userWeaknesses": ensure_string_list(analysis.get("userWeaknesses"), limit=4),
            "aiWeaknesses": ensure_string_list(analysis.get("aiWeaknesses"), limit=4),
            "keyMoments": ensure_string_list(analysis.get("keyMoments"), limit=5),
            "overallAssessment": str(
                analysis.get("overallAssessment") or _fallback_analysis(session)["overallAssessment"]
            ).strip(),
        }

        if not analysis["userStrengths"]:
            analysis["userStrengths"] = _fallback_analysis(session)["userStrengths"]
        if not analysis["aiStrengths"]:
            analysis["aiStrengths"] = _fallback_analysis(session)["aiStrengths"]
        if not analysis["keyMoments"]:
            analysis["keyMoments"] = _fallback_analysis(session)["keyMoments"]

        session["winner"] = analysis["winner"]
        if session.get("status") in (None, "active"):
            session["status"] = "completed"
        await _save_session(session)
        await json_storage.set(_analysis_key(debate_id), analysis)
        await manager.send_message({"type": "phase", "value": "生成最终结论"}, channel)
        await manager.send_message({"type": "complete", "analysis": analysis, "session": session}, channel)
    except Exception as exc:
        await manager.send_message({"type": "error", "error": str(exc)}, channel)
    finally:
        await _release(_analysis_generating, _analysis_generation_lock, debate_id)


@router.post("/debate/start")
async def start_debate(payload: DebateStartRequest, request: Request):
    topic = (payload.topic or "").strip()
    position = (payload.position or "for").strip().lower()
    if position not in ("for", "against"):
        position = "for"
    if not topic:
        return JSONResponse(content={"ok": False, "error": "topic required"}, status_code=400)

    debate_id = str(uuid.uuid4())
    user = get_request_user(request)
    session = {
        "id": debate_id,
        "topic": topic,
        "position": position,
        "messages": [],
        "createdAt": int(time.time() * 1000),
        "updatedAt": int(time.time() * 1000),
        "status": "active",
        "winner": None,
    }
    if user:
        session["owner_id"] = user.id
        session["owner_username"] = user.username
    await _save_session(session)

    return {
        "ok": True,
        "debateId": debate_id,
        "session": {
            "id": debate_id,
            "topic": topic,
            "position": position,
            "createdAt": session["createdAt"],
        },
        "stream": f"/ws/debate?debateId={debate_id}",
    }


@router.get("/debate/{debate_id}")
async def get_debate(debate_id: str):
    session = await _load_session(debate_id)
    if not session:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True, "session": session}


@router.get("/debates")
async def list_debates():
    debates = await _list_debates()
    return {"ok": True, "debates": debates}


@router.delete("/debate/{debate_id}")
async def delete_debate(debate_id: str):
    session = await _load_session(debate_id)
    if not session:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    await json_storage.delete(_debate_key(debate_id))
    await json_storage.delete(_analysis_key(debate_id))
    items = await _list_debates()
    await json_storage.set("debates:index", [item for item in items if item.get("id") != debate_id])
    return {"ok": True, "message": "debate deleted"}


@router.post("/debate/{debate_id}/argue")
async def argue(debate_id: str, payload: DebateArgumentRequest):
    session = await _load_session(debate_id)
    if not session:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    if session.get("status") not in (None, "active"):
        return JSONResponse(content={"ok": False, "error": "debate ended"}, status_code=400)

    argument = (payload.argument or "").strip()
    if not argument:
        return JSONResponse(content={"ok": False, "error": "argument required"}, status_code=400)

    entry = {"role": "user", "content": argument, "timestamp": int(time.time() * 1000)}
    session.setdefault("messages", []).append(entry)
    await _save_session(session)
    await manager.send_message({"type": "user_argument", "content": argument}, debate_id)
    asyncio.create_task(_generate_ai_reply(debate_id))
    return {"ok": True, "message": "argument accepted"}


@router.post("/debate/{debate_id}/surrender")
async def surrender(debate_id: str):
    session = await _load_session(debate_id)
    if not session:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    session["status"] = "user_surrendered"
    session["winner"] = "ai"
    await _save_session(session)
    return {"ok": True, "message": "surrendered"}


@router.post("/debate/{debate_id}/analyze")
async def analyze(debate_id: str):
    session = await _load_session(debate_id)
    if not session:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    asyncio.create_task(_generate_analysis(debate_id))
    return {"ok": True, "message": "analysis started"}


@router.websocket("/ws/debate")
async def debate_ws(websocket: WebSocket):
    await websocket.accept()
    debate_id = websocket.query_params.get("debateId")
    if not debate_id:
        await websocket.close(code=1008, reason="debateId required")
        return

    await manager.connect(websocket, debate_id)
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        manager.disconnect(websocket, debate_id)
    except RuntimeError:
        manager.disconnect(websocket, debate_id)


@router.websocket("/ws/debate/analyze")
async def debate_analysis_ws(websocket: WebSocket):
    await websocket.accept()
    debate_id = websocket.query_params.get("debateId")
    if not debate_id:
        await websocket.close(code=1008, reason="debateId required")
        return

    channel = f"debate-analysis:{debate_id}"
    await manager.connect(websocket, channel)

    cached = await json_storage.get(_analysis_key(debate_id))
    session = await _load_session(debate_id)
    if isinstance(cached, dict) and session:
        await manager.send_message({"type": "complete", "analysis": cached, "session": session}, channel)

    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except RuntimeError:
        manager.disconnect(websocket, channel)
