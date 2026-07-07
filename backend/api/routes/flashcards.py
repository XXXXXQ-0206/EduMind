"""
闪卡 API 路由
与原 Node.js 版本完全兼容
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.flashcards_agent import KnowledgeCardsAgent, KnowledgeCardsInput
from utils.api_errors import safe_error_response
from utils.auth import require_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.storage import filter_records_for_user, json_storage, list_files_for_user, owner_payload, record_belongs_to_user


router = APIRouter()
logger = logging.getLogger(__name__)


class Flashcard(BaseModel):
    id: str
    question: str
    answer: str
    tag: str
    created: int


class CreateFlashcardRequest(BaseModel):
    question: str
    answer: str
    tag: str


class KnowledgeCardsRequest(BaseModel):
    topic: str
    count: Optional[int] = 5
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None


class KnowledgeCardPayload(BaseModel):
    id: str
    concept: str
    question: str
    fill_blank: Optional[str] = None
    hint: str
    answer: str
    mnemonic: str
    application: str


class KnowledgeDeckPayload(BaseModel):
    id: str
    title: str
    count: int
    created_at: str
    updated_at: str
    cards: List[KnowledgeCardPayload]


@router.post("/flashcards")
async def create_flashcard(request: CreateFlashcardRequest, user: AuthUser = Depends(require_auth)):
    """创建闪卡"""
    try:
        if not request.question or not request.answer or not request.tag:
            raise HTTPException(
                status_code=400,
                detail="question, answer, tag required"
            )

        card_id = str(uuid.uuid4())
        card = Flashcard(
            id=card_id,
            question=request.question,
            answer=request.answer,
            tag=request.tag,
            created=int(datetime.now().timestamp() * 1000),
        )
        card_dict = {**card.dict(), **owner_payload(user.id, user.username)}

        await json_storage.set(f"flashcard:{card_id}", card_dict)
        await json_storage.update(
            "flashcards",
            lambda cards: [*(cards if isinstance(cards, list) else []), card_dict],
            default=[],
        )

        return {"ok": True, "flashcard": card_dict}

    except HTTPException:
        raise
    except Exception as exc:
        return safe_error_response(logger, exc, "flashcard creation failed")


@router.get("/flashcards")
async def list_flashcards(user: AuthUser = Depends(require_auth)):
    """列出所有闪卡"""
    try:
        cards = await json_storage.get("flashcards") or []
        cards = filter_records_for_user(cards, user.id, user.username)
        return {"ok": True, "flashcards": cards}
    except Exception as exc:
        return safe_error_response(logger, exc, "flashcard list failed")


@router.delete("/flashcards/{card_id}")
async def delete_flashcard(card_id: str, user: AuthUser = Depends(require_auth)):
    """删除闪卡"""
    try:
        if not card_id:
            raise HTTPException(status_code=400, detail="id required")
        existing = await json_storage.get(f"flashcard:{card_id}")
        if not existing or not record_belongs_to_user(existing, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)

        # 删除单个闪卡
        await json_storage.delete(f"flashcard:{card_id}")

        await json_storage.update(
            "flashcards",
            lambda cards: [c for c in (cards if isinstance(cards, list) else []) if c.get("id") != card_id],
            default=[],
        )

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as exc:
        return safe_error_response(logger, exc, "flashcard deletion failed")


async def _build_material_context(ids: List[str], user: AuthUser, query: str) -> str:
    if not ids:
        return ""
    files = await list_files_for_user(user.id, user.username, "student")
    return await build_selected_files_context(
        files,
        ids,
        max_chars=20000,
        snippet_chars=20000,
        query=query,
        owner_id=user.id,
        role="student",
    )


@router.post("/flashcards/decks")
async def generate_knowledge_cards(request: KnowledgeCardsRequest, user: AuthUser = Depends(require_auth)):
    """生成知识卡片卡组"""
    try:
        topic = request.topic.strip() if request.topic else ""
        count = int(request.count or 5)
        include_materials = bool(request.includeMaterials)
        material_ids = request.materialIds or []

        if not topic:
            return JSONResponse(content={"ok": False, "error": "topic required"}, status_code=400)

        deck_id = str(uuid.uuid4())
        prompt_topic = topic

        if include_materials and material_ids:
            materials_text = await _build_material_context(material_ids, user, topic)
            if materials_text:
                prompt_topic = (
                    f"{topic}\n\n学习资料内容:\n{materials_text}\n\n"
                    "请优先基于资料生成知识卡片。"
                )

        agent = KnowledgeCardsAgent()
        result = await agent.execute(KnowledgeCardsInput(topic=prompt_topic, count=count, deck_id=deck_id))

        if not result.success or not result.cards:
            return JSONResponse(content={"ok": False, "error": result.error or "generation failed"}, status_code=500)

        now_iso = datetime.now().isoformat()
        deck = KnowledgeDeckPayload(
            id=deck_id,
            title=topic[:100],
            count=count,
            created_at=now_iso,
            updated_at=now_iso,
            cards=[KnowledgeCardPayload(**c.dict()) for c in result.cards],
        )

        deck_dict = {**deck.dict(), **owner_payload(user.id, user.username)}
        await json_storage.set(f"flashcard_deck:{deck_id}", deck_dict)

        summary = {
            "id": deck_id,
            "title": deck.title,
            "count": deck.count,
            "created_at": deck.created_at,
            "updated_at": deck.updated_at,
            **owner_payload(user.id, user.username),
        }
        await json_storage.update(
            "flashcard_decks",
            lambda decks: [
                *[d for d in (decks if isinstance(decks, list) else []) if d.get("id") != deck_id],
                summary,
            ],
            default=[],
        )

        return {"ok": True, "deck": deck_dict}
    except Exception as exc:
        return safe_error_response(logger, exc, "knowledge deck generation failed")


@router.get("/flashcards/decks")
async def list_knowledge_decks(user: AuthUser = Depends(require_auth)):
    """列出知识卡片卡组"""
    try:
        decks = await json_storage.get("flashcard_decks") or []
        decks = filter_records_for_user(decks, user.id, user.username)
        if isinstance(decks, list):
            decks.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        return {"ok": True, "decks": decks}
    except Exception as exc:
        return safe_error_response(logger, exc, "knowledge deck list failed")


@router.get("/flashcards/decks/{deck_id}")
async def get_knowledge_deck(deck_id: str, user: AuthUser = Depends(require_auth)):
    """获取知识卡片卡组详情"""
    try:
        if not deck_id:
            return JSONResponse(content={"ok": False, "error": "id required"}, status_code=400)
        deck = await json_storage.get(f"flashcard_deck:{deck_id}")
        if not deck or not record_belongs_to_user(deck, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        return {"ok": True, "deck": deck}
    except Exception as exc:
        return safe_error_response(logger, exc, "knowledge deck detail failed")


@router.delete("/flashcards/decks/{deck_id}")
async def delete_knowledge_deck(deck_id: str, user: AuthUser = Depends(require_auth)):
    """删除知识卡片卡组"""
    try:
        if not deck_id:
            return JSONResponse(content={"ok": False, "error": "id required"}, status_code=400)

        deck = await json_storage.get(f"flashcard_deck:{deck_id}")
        if not deck or not record_belongs_to_user(deck, user.id, user.username):
            return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
        await json_storage.delete(f"flashcard_deck:{deck_id}")
        await json_storage.update(
            "flashcard_decks",
            lambda decks: [d for d in (decks if isinstance(decks, list) else []) if d.get("id") != deck_id],
            default=[],
        )
        return {"ok": True}
    except Exception as exc:
        return safe_error_response(logger, exc, "knowledge deck deletion failed")
