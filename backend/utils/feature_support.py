"""
Shared helpers for AI-backed feature routes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import aiofiles

from utils.upload_objects import upload_path_from_meta


def strip_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)


def extract_json_array(text: str) -> str:
    cleaned = strip_code_fences(text)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    return match.group(0) if match else ""


def extract_json_object(text: str) -> str:
    cleaned = strip_code_fences(text)
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    start = cleaned.find("{")
    if start < 0:
        return ""
    depth = 0
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : index + 1]
    return ""


def safe_json_loads(
    text: str,
    *,
    prefer_array: bool = False,
) -> Optional[Any]:
    cleaned = strip_code_fences(text)
    candidates = [cleaned]
    if prefer_array:
        array_candidate = extract_json_array(cleaned)
        object_candidate = extract_json_object(cleaned)
        candidates.extend([array_candidate, object_candidate])
    else:
        object_candidate = extract_json_object(cleaned)
        array_candidate = extract_json_array(cleaned)
        candidates.extend([object_candidate, array_candidate])

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None


def compact_text(text: str, limit: int) -> str:
    raw = re.sub(r"\s+", " ", (text or "")).strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 1)].rstrip() + "…"


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in (text or ""))


def language_hint(text: str) -> str:
    return "Chinese" if has_cjk(text) else "English"


async def read_sidecar_text(file_path: Path) -> str:
    txt_path = Path(str(file_path) + ".txt")
    if not txt_path.exists():
        return ""
    try:
        async with aiofiles.open(txt_path, "r", encoding="utf-8") as file:
            return await file.read()
    except Exception:
        return ""


async def extract_file_text_from_meta(meta: Dict[str, Any]) -> str:
    file_path = upload_path_from_meta(meta)
    if not file_path:
        return ""
    if not file_path.exists():
        return ""

    text = await read_sidecar_text(file_path)
    if text:
        return text

    try:
        from utils.parser import extract_text_from_file

        return await extract_text_from_file(str(file_path), meta.get("mimeType"))
    except Exception:
        return ""


async def build_files_context(
    files: Iterable[Dict[str, Any]],
    *,
    max_chars: int = 12000,
    snippet_chars: int = 2500,
) -> str:
    parts: List[str] = []
    used = 0
    for meta in files:
        remaining = max_chars - used
        if remaining <= 0:
            break
        text = await extract_file_text_from_meta(meta)
        if not text:
            continue
        name = meta.get("originalName") or meta.get("filename") or "document"
        snippet = text[: min(snippet_chars, remaining)]
        chunk = f"[资料] {name}\n{snippet.strip()}"
        parts.append(chunk)
        used += len(chunk)
    return "\n\n".join(part for part in parts if part).strip()


async def build_selected_files_context(
    files: Iterable[Dict[str, Any]],
    ids: Iterable[Any],
    *,
    max_chars: int = 12000,
    snippet_chars: int = 2500,
) -> str:
    file_list = [dict(item) for item in files if isinstance(item, dict)]
    file_map = {str(item.get("id")): item for item in file_list if item.get("id")}
    selected_ids = [str(item) for item in ids if item]
    selected = [file_map[item] for item in selected_ids if item in file_map] if selected_ids else file_list
    return await build_files_context(selected, max_chars=max_chars, snippet_chars=snippet_chars)


def ensure_string_list(value: Any, *, limit: int = 8, item_limit: int = 200) -> List[str]:
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        result.append(text[:item_limit])
        if len(result) >= limit:
            break
    return result


def ensure_flashcards(value: Any, *, limit: int = 8) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    cards: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        question = str(item.get("q") or item.get("question") or "").strip()
        answer = str(item.get("a") or item.get("answer") or "").strip()
        if not question or not answer:
            continue
        card: Dict[str, str] = {"q": question[:200], "a": answer[:500]}
        tag = str(item.get("tag") or item.get("concept") or "").strip()
        if tag:
            card["tag"] = tag[:80]
        cards.append(card)
        if len(cards) >= limit:
            break
    return cards
