"""Document library and multi-file RAG helpers."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import aiofiles

from infrastructure.object_store import create_object_store
from utils.parser import extract_text_from_file_bytes
from utils.storage import VectorStore, json_storage
from utils.upload_objects import upload_object_key_from_meta, upload_path_from_meta


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 160
DEFAULT_MAX_CONTEXT_CHARS = 12000
DEFAULT_MAX_CONTEXT_CHUNKS = 10
DEFAULT_PER_FILE_K = 3
_INDEX_LOCKS: Dict[str, asyncio.Lock] = {}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    file_id: str
    file_name: str
    owner_id: int
    role: str
    object_key: str
    mime_type: str
    chunk_index: int
    total_chunks: int
    char_start: int
    char_end: int
    text: str
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def vector_metadata(self) -> Dict[str, Any]:
        data = self.to_dict()
        data.pop("text", None)
        data["source"] = "document_library"
        return data


@dataclass(frozen=True)
class DocumentIndexResult:
    file_id: str
    status: str
    chunk_count: int
    text_chars: int
    indexed_at: int
    vector_status: str
    error: str = ""

    def to_file_updates(self) -> Dict[str, Any]:
        updates = {
            "ragStatus": self.status,
            "ragIndexedAt": self.indexed_at,
            "ragChunkCount": self.chunk_count,
            "ragTextChars": self.text_chars,
            "ragVectorStatus": self.vector_status,
        }
        if self.error:
            updates["ragError"] = self.error
        else:
            updates.pop("ragError", None)
        return updates


@dataclass(frozen=True)
class RagContext:
    text: str
    chunks: List[Dict[str, Any]]
    files: List[Dict[str, Any]]
    failed_files: List[Dict[str, Any]]

    @property
    def has_context(self) -> bool:
        return bool(self.text.strip())


def _now_ms() -> int:
    return int(time.time() * 1000)


def _normalize_role(role: Optional[str]) -> str:
    value = (role or "student").strip().lower()
    return value if value in {"student", "teacher"} else "student"


def _file_id(meta: Dict[str, Any]) -> str:
    return str(meta.get("id") or "").strip()


def _file_name(meta: Dict[str, Any]) -> str:
    return str(meta.get("originalName") or meta.get("filename") or "document").strip() or "document"


def _file_owner_id(meta: Dict[str, Any], fallback: int = 0) -> int:
    try:
        return int(meta.get("owner_id") if meta.get("owner_id") is not None else fallback)
    except Exception:
        return int(fallback or 0)


def _namespace(owner_id: int, role: str, file_id: str) -> str:
    digest = hashlib.sha256(f"{owner_id}:{_normalize_role(role)}:{file_id}".encode("utf-8")).hexdigest()
    return f"rag_{digest}"


def _chunks_key(file_id: str) -> str:
    return f"rag:file:{file_id}:chunks"


def _status_key(file_id: str) -> str:
    return f"rag:file:{file_id}:status"


def _normalize_text(text: str) -> str:
    value = (text or "").replace("\x00", " ")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{4,}", "\n\n\n", value)
    return value.strip()


async def _read_sidecar_text(file_path: Path) -> str:
    sidecar = Path(str(file_path) + ".txt")
    if not sidecar.exists():
        return ""
    try:
        async with aiofiles.open(sidecar, "r", encoding="utf-8") as file:
            return await file.read()
    except Exception:
        return ""


async def _write_sidecar_text(file_path: Path, text: str) -> None:
    if not text.strip():
        return
    sidecar = Path(str(file_path) + ".txt")
    try:
        async with aiofiles.open(sidecar, "w", encoding="utf-8") as file:
            await file.write(text)
    except Exception:
        return


async def extract_text_for_file(meta: Dict[str, Any], *, use_cache: bool = True) -> str:
    """Extract text for an uploaded object, using the legacy sidecar cache when available."""
    file_path = upload_path_from_meta(meta)
    if not file_path or not file_path.exists():
        return ""

    if use_cache:
        cached = _normalize_text(await _read_sidecar_text(file_path))
        if cached:
            return cached

    object_key = upload_object_key_from_meta(meta)
    if not object_key:
        return ""
    content = await create_object_store().get_bytes(object_key)
    text = _normalize_text(
        await extract_text_from_file_bytes(
            content,
            filename=_file_name(meta),
            mime_type=meta.get("mimeType"),
        )
    )
    if use_cache and text:
        await _write_sidecar_text(file_path, text)
    return text


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    clean = _normalize_text(text)
    if not clean:
        return []

    chunk_size = max(200, int(chunk_size or DEFAULT_CHUNK_SIZE))
    overlap = max(0, min(int(overlap or 0), chunk_size // 2))
    chunks: List[Dict[str, Any]] = []
    start = 0
    length = len(clean)

    while start < length:
        end = min(length, start + chunk_size)
        if end < length:
            floor = min(length, start + max(120, chunk_size // 2))
            breakpoints = [
                clean.rfind("\n\n", floor, end),
                clean.rfind("。", floor, end),
                clean.rfind(".", floor, end),
                clean.rfind("；", floor, end),
                clean.rfind(";", floor, end),
                clean.rfind("\n", floor, end),
            ]
            best = max(breakpoints)
            if best > start:
                end = best + 1

        chunk = clean[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "char_start": start, "char_end": end})

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks


def build_document_chunks(
    meta: Dict[str, Any],
    text: str,
    *,
    owner_id: int,
    role: str,
) -> List[DocumentChunk]:
    file_id = _file_id(meta)
    file_name = _file_name(meta)
    object_key = upload_object_key_from_meta(meta)
    mime_type = str(meta.get("mimeType") or "application/octet-stream")
    raw_chunks = chunk_text(text)
    total = len(raw_chunks)
    chunks: List[DocumentChunk] = []
    for index, item in enumerate(raw_chunks):
        chunk_id = hashlib.sha256(f"{file_id}:{index}:{item['char_start']}:{item['char_end']}".encode("utf-8")).hexdigest()
        chunks.append(
            DocumentChunk(
                id=chunk_id,
                file_id=file_id,
                file_name=file_name,
                owner_id=owner_id,
                role=_normalize_role(role),
                object_key=object_key,
                mime_type=mime_type,
                chunk_index=index,
                total_chunks=total,
                char_start=int(item["char_start"]),
                char_end=int(item["char_end"]),
                text=str(item["text"]),
            )
        )
    return chunks


async def index_file_meta(
    meta: Dict[str, Any],
    *,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
    force: bool = False,
) -> DocumentIndexResult:
    file_id = _file_id(meta)
    if not file_id:
        return DocumentIndexResult("", "error", 0, 0, _now_ms(), "skipped", "file id missing")

    normalized_role = _normalize_role(role)
    resolved_owner_id = _file_owner_id(meta, fallback=int(owner_id or 0))

    async with _INDEX_LOCKS.setdefault(file_id, asyncio.Lock()):
        if not force:
            existing_status = await get_file_index_status(file_id)
            existing_chunks = await _load_indexed_chunks(file_id)
            if existing_status.get("status") in {"ready", "empty"} and (
                existing_chunks or existing_status.get("status") == "empty"
            ):
                return DocumentIndexResult(
                    file_id=file_id,
                    status=str(existing_status.get("status") or "ready"),
                    chunk_count=int(existing_status.get("chunk_count") or existing_status.get("chunkCount") or len(existing_chunks)),
                    text_chars=int(existing_status.get("text_chars") or existing_status.get("textChars") or 0),
                    indexed_at=int(existing_status.get("indexed_at") or existing_status.get("indexedAt") or _now_ms()),
                    vector_status=str(existing_status.get("vector_status") or existing_status.get("vectorStatus") or "unknown"),
                    error=str(existing_status.get("error") or ""),
                )
        return await _index_file_meta_unlocked(
            meta,
            file_id=file_id,
            owner_id=resolved_owner_id,
            role=normalized_role,
        )


async def _index_file_meta_unlocked(
    meta: Dict[str, Any],
    *,
    file_id: str,
    owner_id: int,
    role: str,
) -> DocumentIndexResult:
    try:
        text = await extract_text_for_file(meta)
        chunks = build_document_chunks(meta, text, owner_id=owner_id, role=role)
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        await json_storage.set(_chunks_key(file_id), chunk_dicts)

        vector_status = "skipped"
        if chunks:
            try:
                store = VectorStore(_namespace(owner_id, role, file_id))
                await store.add_documents(
                    [chunk.text for chunk in chunks],
                    [chunk.vector_metadata() for chunk in chunks],
                )
                vector_status = "indexed"
            except Exception as exc:
                vector_status = "keyword-fallback"
                logger.warning("RAG vector index fallback file_id=%s", file_id, exc_info=True)
        status = "ready" if chunks else "empty"
        result = DocumentIndexResult(
            file_id=file_id,
            status=status,
            chunk_count=len(chunks),
            text_chars=len(text),
            indexed_at=_now_ms(),
            vector_status=vector_status,
            error="",
        )
        await json_storage.set(_status_key(file_id), asdict(result))
        return result
    except Exception as exc:
        logger.exception("RAG document indexing failed")
        result = DocumentIndexResult(
            file_id=file_id,
            status="error",
            chunk_count=0,
            text_chars=0,
            indexed_at=_now_ms(),
            vector_status="failed",
            error="document indexing failed",
        )
        await json_storage.set(_status_key(file_id), asdict(result))
        return result


async def delete_file_index(
    file_id: str,
    *,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
) -> None:
    await json_storage.delete(_chunks_key(file_id))
    await json_storage.delete(_status_key(file_id))
    if owner_id is not None:
        try:
            await VectorStore(_namespace(int(owner_id), _normalize_role(role), file_id)).delete()
        except Exception:
            pass


async def get_file_index_status(file_id: str) -> Dict[str, Any]:
    status = await json_storage.get(_status_key(file_id))
    return dict(status) if isinstance(status, dict) else {}


async def _load_indexed_chunks(file_id: str) -> List[Dict[str, Any]]:
    chunks = await json_storage.get(_chunks_key(file_id)) or []
    if not isinstance(chunks, list):
        return []
    return [dict(item) for item in chunks if isinstance(item, dict) and str(item.get("text") or "").strip()]


async def ensure_file_index(
    meta: Dict[str, Any],
    *,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
) -> DocumentIndexResult:
    file_id = _file_id(meta)
    if not file_id:
        return DocumentIndexResult("", "error", 0, 0, _now_ms(), "skipped", "file id missing")

    status = await get_file_index_status(file_id)
    chunks = await _load_indexed_chunks(file_id)
    if status.get("status") in {"ready", "empty"} and (chunks or status.get("status") == "empty"):
        return DocumentIndexResult(
            file_id=file_id,
            status=str(status.get("status") or "ready"),
            chunk_count=int(status.get("chunk_count") or status.get("chunkCount") or len(chunks)),
            text_chars=int(status.get("text_chars") or status.get("textChars") or 0),
            indexed_at=int(status.get("indexed_at") or status.get("indexedAt") or _now_ms()),
            vector_status=str(status.get("vector_status") or status.get("vectorStatus") or "unknown"),
            error=str(status.get("error") or ""),
        )
    return await index_file_meta(meta, owner_id=owner_id, role=role)


def select_file_metas(files: Iterable[Dict[str, Any]], ids: Iterable[Any]) -> List[Dict[str, Any]]:
    file_list = [dict(item) for item in files if isinstance(item, dict)]
    selected_ids = [str(item) for item in ids if item]
    if not selected_ids:
        return file_list

    file_map = {str(item.get("id")): item for item in file_list if item.get("id")}
    selected: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for file_id in selected_ids:
        if file_id in seen:
            continue
        seen.add(file_id)
        if file_id in file_map:
            selected.append(file_map[file_id])
    return selected


def _tokenize_query(query: str) -> List[str]:
    text = (query or "").lower()
    tokens = re.findall(r"[a-z0-9_+-]{2,}|[\u4e00-\u9fff]{2,}", text)
    cjk_chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    tokens.extend(cjk_chars[:32])
    return list(dict.fromkeys(tokens))


def _keyword_score(text: str, query: str) -> float:
    if not query.strip():
        return 0.0
    body = (text or "").lower()
    if not body:
        return 0.0
    tokens = _tokenize_query(query)
    if not tokens:
        return 0.0
    score = 0.0
    for token in tokens:
        count = body.count(token)
        if count:
            score += 1.0 + math.log(count)
    return score / max(1.0, math.log(len(body) + 10))


def _coerce_chunk_from_vector_result(row: Dict[str, Any]) -> Dict[str, Any]:
    metadata = row.get("metadata") if isinstance(row, dict) else {}
    chunk = dict(metadata if isinstance(metadata, dict) else {})
    chunk["text"] = str(row.get("text") or chunk.get("text") or "")
    chunk["score"] = float(row.get("score") or 0.0)
    return chunk


async def retrieve_file_chunks(
    meta: Dict[str, Any],
    *,
    owner_id: int,
    role: str,
    query: str,
    k: int = DEFAULT_PER_FILE_K,
    ensure_index: bool = True,
) -> List[Dict[str, Any]]:
    file_id = _file_id(meta)
    if not file_id:
        return []

    if ensure_index:
        await ensure_file_index(meta, owner_id=owner_id, role=role)
    normalized_role = _normalize_role(role)
    limit = max(1, int(k or DEFAULT_PER_FILE_K))

    if query.strip():
        try:
            rows = await VectorStore(_namespace(owner_id, normalized_role, file_id)).similarity_search(query, k=limit)
            chunks = [_coerce_chunk_from_vector_result(dict(row)) for row in rows if isinstance(row, dict)]
            chunks = [chunk for chunk in chunks if str(chunk.get("text") or "").strip()]
            if chunks:
                return chunks[:limit]
        except Exception:
            pass

    chunks = await _load_indexed_chunks(file_id)
    if not chunks:
        return []

    for chunk in chunks:
        chunk["score"] = _keyword_score(str(chunk.get("text") or ""), query)
    if query.strip():
        chunks.sort(key=lambda item: (float(item.get("score") or 0.0), -int(item.get("chunk_index") or 0)), reverse=True)
    else:
        chunks.sort(key=lambda item: int(item.get("chunk_index") or 0))
    return chunks[:limit]


def _select_final_chunks(
    per_file_results: Sequence[List[Dict[str, Any]]],
    *,
    max_chunks: int,
) -> List[Dict[str, Any]]:
    max_chunks = max(1, int(max_chunks or DEFAULT_MAX_CONTEXT_CHUNKS))
    selected: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for file_chunks in per_file_results:
        if not file_chunks:
            continue
        chunk = dict(file_chunks[0])
        chunk_id = str(chunk.get("id") or f"{chunk.get('file_id')}:{chunk.get('chunk_index')}")
        if chunk_id in seen:
            continue
        selected.append(chunk)
        seen.add(chunk_id)

    remaining = [
        dict(chunk)
        for file_chunks in per_file_results
        for chunk in file_chunks[1:]
    ]
    remaining.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    for chunk in remaining:
        if len(selected) >= max_chunks:
            break
        chunk_id = str(chunk.get("id") or f"{chunk.get('file_id')}:{chunk.get('chunk_index')}")
        if chunk_id in seen:
            continue
        selected.append(chunk)
        seen.add(chunk_id)

    return selected[:max_chunks]


def format_rag_context(chunks: Sequence[Dict[str, Any]], *, max_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> str:
    if not chunks:
        return ""

    max_chars = max(1000, int(max_chars or DEFAULT_MAX_CONTEXT_CHARS))
    file_names = []
    for chunk in chunks:
        name = str(chunk.get("file_name") or "document")
        if name not in file_names:
            file_names.append(name)

    header = (
        f"以下为文件库 RAG 检索结果，共覆盖 {len(file_names)} 个文件、{len(chunks)} 个相关片段。"
        "请优先依据这些资料回答；若资料不足，请明确说明并再给出合理推断。\n"
        f"覆盖文件：{'；'.join(file_names)}"
    )
    parts = [header]
    remaining = max_chars - len(header)
    per_chunk_budget = max(280, remaining // max(1, len(chunks)))

    for idx, chunk in enumerate(chunks, start=1):
        if remaining <= 0:
            break
        text = re.sub(r"\s+", " ", str(chunk.get("text") or "")).strip()
        if not text:
            continue
        snippet = text[: min(per_chunk_budget, remaining)].rstrip()
        name = str(chunk.get("file_name") or "document")
        chunk_index = int(chunk.get("chunk_index") or 0) + 1
        total_chunks = int(chunk.get("total_chunks") or chunk_index)
        score = float(chunk.get("score") or 0.0)
        block = (
            f"\n\n[资料片段 {idx}] 文件：{name} | 分块：{chunk_index}/{total_chunks}"
            f" | 相关度：{score:.3f}\n{snippet}"
        )
        if len(block) > remaining:
            block = block[:remaining].rstrip()
        parts.append(block)
        remaining -= len(block)

    return "".join(parts).strip()


async def build_rag_context_for_user_files(
    files: Iterable[Dict[str, Any]],
    ids: Iterable[Any],
    *,
    owner_id: Optional[int] = None,
    role: Optional[str] = None,
    query: str = "",
    max_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    max_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS,
    per_file_k: int = DEFAULT_PER_FILE_K,
) -> RagContext:
    selected_files = select_file_metas(files, ids)
    if not selected_files:
        return RagContext(text="", chunks=[], files=[], failed_files=[])

    normalized_role = _normalize_role(role)
    resolved_owner_id = int(owner_id or _file_owner_id(selected_files[0]))
    per_file_results: List[List[Dict[str, Any]]] = []
    indexed_files: List[Dict[str, Any]] = []
    failed_files: List[Dict[str, Any]] = []

    for meta in selected_files:
        file_id = _file_id(meta)
        if not file_id:
            continue
        status = await ensure_file_index(meta, owner_id=resolved_owner_id, role=normalized_role)
        file_record = {
            "id": file_id,
            "name": _file_name(meta),
            "originalName": _file_name(meta),
            "filename": str(meta.get("filename") or ""),
            "status": status.status,
            "chunkCount": status.chunk_count,
            "vectorStatus": status.vector_status,
            "indexedAt": status.indexed_at,
        }
        if status.status == "error":
            file_record["error"] = status.error
            failed_files.append(file_record)
            per_file_results.append([])
            continue
        indexed_files.append(file_record)
        per_file_results.append(
            await retrieve_file_chunks(
                meta,
                owner_id=resolved_owner_id,
                role=normalized_role,
                query=query,
                k=per_file_k,
                ensure_index=False,
            )
        )

    chunks = _select_final_chunks(per_file_results, max_chunks=max_chunks)
    return RagContext(
        text=format_rag_context(chunks, max_chars=max_chars),
        chunks=chunks,
        files=indexed_files,
        failed_files=failed_files,
    )
