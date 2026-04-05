"""
Study companion route backed by the configured LLM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import config
from utils.auth import require_auth
from utils.auth_db import AuthUser
from utils.feature_support import (
    compact_text,
    ensure_flashcards,
    extract_file_text_from_meta,
    language_hint,
    safe_json_loads,
)
from utils.llm import invoke_llm
from utils.parser import extract_text_from_file


router = APIRouter()


class CompanionHistoryItem(BaseModel):
    role: str
    content: str


class CompanionAskRequest(BaseModel):
    question: str
    filePath: Optional[str] = None
    documentText: Optional[str] = None
    documentTitle: Optional[str] = None
    topic: Optional[str] = None
    history: Optional[List[CompanionHistoryItem]] = None


def _resolve_storage_path(file_path: str) -> Optional[Path]:
    raw = (file_path or "").strip()
    if not raw:
        return None
    direct = Path(raw)
    if direct.exists():
        return direct

    marker = "/storage/uploads/"
    if marker in raw:
        name = raw.split(marker, 1)[1].strip().split("?", 1)[0]
        candidate = config.storage_dir / "uploads" / name
        if candidate.exists():
            return candidate

    uploads_dir = config.storage_dir / "uploads"
    fallback = uploads_dir / Path(raw).name
    if fallback.exists():
        return fallback
    return None


async def _load_document_text(payload: CompanionAskRequest) -> str:
    provided = (payload.documentText or "").strip()
    if provided:
        return provided

    resolved = _resolve_storage_path(payload.filePath or "")
    if not resolved:
        return ""
    try:
        return await extract_text_from_file(str(resolved))
    except Exception:
        return ""


def _history_excerpt(history: List[CompanionHistoryItem]) -> str:
    if not history:
        return ""
    recent = history[-6:]
    parts: List[str] = []
    for item in recent:
        role = "User" if item.role == "user" else "Assistant"
        parts.append(f"{role}: {compact_text(item.content, 500)}")
    return "\n".join(parts)


@router.post("/api/companion/ask")
async def companion_ask(
    payload: CompanionAskRequest,
    user: AuthUser = Depends(require_auth),
):
    question = (payload.question or "").strip()
    if not question:
        return JSONResponse(content={"ok": False, "error": "question required"}, status_code=400)

    document_text = await _load_document_text(payload)
    if not document_text:
        return JSONResponse(content={"ok": False, "error": "document context required"}, status_code=400)

    topic = (payload.topic or payload.documentTitle or "当前文档").strip() or "当前文档"
    language = language_hint(f"{topic}\n{question}\n{document_text[:500]}")
    history_text = _history_excerpt(payload.history or [])
    context_text = document_text[:12000]

    system_prompt = f"""
You are a study companion grounded strictly in the provided document.
Return only one JSON object:
{{
  "topic": "string",
  "answer": "string",
  "flashcards": [{{"q": "string", "a": "string"}}]
}}

Rules:
- Use {language}.
- Answer the user's question using the document context first.
- If the document is incomplete, say what is missing instead of inventing facts.
- Keep the answer practical and easy to study from.
- Generate 0 to 4 concise flashcards only when useful.
- No markdown code fences. Output JSON only.
""".strip()

    user_prompt = f"""
Topic: {topic}
Question: {question}

Conversation so far:
{history_text or "(none)"}

Document context:
{context_text}
""".strip()

    try:
        raw = await invoke_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1800,
        )
    except Exception as exc:
        return JSONResponse(content={"ok": False, "error": str(exc)}, status_code=500)

    parsed = safe_json_loads(raw)
    if isinstance(parsed, dict):
        answer = str(parsed.get("answer") or "").strip()
        flashcards = ensure_flashcards(parsed.get("flashcards"))
        response_topic = str(parsed.get("topic") or topic).strip() or topic
        if answer:
            return {
                "ok": True,
                "companion": {
                    "topic": response_topic[:120],
                    "answer": answer,
                    "flashcards": flashcards,
                },
            }

    fallback_answer = raw.strip() or "I couldn't generate a response from the provided context."
    return {
        "ok": True,
        "companion": {
            "topic": topic[:120],
            "answer": fallback_answer,
            "flashcards": [],
        },
    }
