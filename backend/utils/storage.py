"""
数据存储工具
支持 JSON 文件存储和向量存储
"""
import asyncio
from pathlib import Path
from collections.abc import Awaitable, Callable
from typing import Any, Optional, List, Dict
from datetime import datetime
from urllib.parse import unquote, urlparse

from config import config
from infrastructure.kv_store import KeyValueItem, KeyValueStore, create_kv_store, sanitize_key
from infrastructure.object_store import create_object_store
from utils.auth_contracts import ADMIN_USERNAME


JsonUpdater = Callable[[Any], Any | Awaitable[Any]]


def _pick_first_audio_file(directory: Path) -> Optional[Path]:
    for pattern in ("*.mp3", "*.m4a", "*.mp4", "*.wav"):
        files = [f for f in directory.glob(pattern) if not f.name.startswith("segment_")]
        if files:
            return files[0]
    return None


def _build_podcast_urls(pid: str, filename: str) -> Dict[str, str]:
    safe_name = Path(filename).name
    return {
        "static": f"/storage/podcasts/{pid}/{safe_name}",
        "file": f"/podcast/download/{pid}/{safe_name}",
    }


def _audio_filename_from_meta(meta: Dict[str, Any]) -> Optional[str]:
    for key in ("static", "file"):
        raw = str(meta.get(key) or "").strip()
        if not raw:
            continue
        try:
            parsed = urlparse(raw)
            candidate = parsed.path or raw
        except Exception:
            candidate = raw
        name = Path(unquote(candidate)).name
        if name:
            return name
    return None


VALID_GENERATION_STATUSES = {"pending", "generating", "ready", "error"}


def _to_epoch_ms(value: Optional[str]) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value).timestamp() * 1000)
    except Exception:
        return 0


def _safe_item_key(item: KeyValueItem) -> str:
    return sanitize_key(item.key)


def _item_entity_id(item: KeyValueItem, prefix: str, fallback_offset: int = 0) -> str:
    safe_key = _safe_item_key(item)
    safe_prefix = sanitize_key(prefix)
    if safe_key.startswith(safe_prefix):
        return safe_key[len(safe_prefix):]
    return safe_key[fallback_offset:]


def _is_auxiliary_item(item: KeyValueItem, auxiliary_suffixes: tuple[str, ...]) -> bool:
    safe_key = _safe_item_key(item)
    return any(safe_key.endswith(suffix) for suffix in auxiliary_suffixes)


def normalize_generation_status(value: Any, fallback: str = "pending") -> str:
    candidate = str(value or "").strip().lower()
    if candidate in VALID_GENERATION_STATUSES:
        return candidate
    return fallback if fallback in VALID_GENERATION_STATUSES else "pending"


def note_has_readable_result(meta: Optional[Dict[str, Any]], notes: Optional[Any]) -> bool:
    data = meta or {}
    return bool(data.get("file") or notes)


def podcast_has_audio(meta: Optional[Dict[str, Any]]) -> bool:
    data = meta or {}
    return bool(data.get("file") or data.get("static"))


def derive_note_status(meta: Optional[Dict[str, Any]], notes: Optional[Any]) -> str:
    normalized = normalize_generation_status((meta or {}).get("status"), "")
    if note_has_readable_result(meta, notes):
        return "ready"
    if normalized in VALID_GENERATION_STATUSES:
        return normalized
    return "pending"


def derive_podcast_status(meta: Optional[Dict[str, Any]], script: Optional[Any]) -> str:
    normalized = normalize_generation_status((meta or {}).get("status"), "")
    has_script = bool(script)
    if podcast_has_audio(meta):
        return "ready"
    if normalized == "ready" and has_script:
        return "ready"
    if has_script:
        return "error" if normalized == "error" else "generating"
    if normalized in {"pending", "generating", "error"}:
        return normalized
    return "pending"


class JSONStorage:
    """JSON 文件存储"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or config.storage_dir
        self.store: KeyValueStore = create_kv_store(self.base_dir)
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取数据"""
        return await self.store.get(key)

    async def set(self, key: str, value: Any) -> None:
        """设置数据"""
        async with self.lock:
            await self.store.set(key, value)

    async def update(self, key: str, updater: JsonUpdater, default: Any = None) -> Any:
        """原子更新数据并返回更新后的值。"""
        return await self.store.update(key, updater, default)

    async def delete(self, key: str) -> None:
        """删除数据"""
        await self.store.delete(key)

    async def list_prefix(self, prefix: str) -> List[KeyValueItem]:
        """按键前缀列出数据。"""
        return await self.store.list_prefix(prefix)

    async def list_values(self, prefix: str) -> List[Any]:
        """按键前缀列出值。"""
        return [item.value for item in await self.list_prefix(prefix)]

    def _get_file_path(self, key: str) -> Path:
        """获取文件路径"""
        return self.store.path_for_key(key)


class VectorStore:
    """向量存储（基于 FAISS 或 ChromaDB）"""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self.storage = JSONStorage()

    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """添加文档到向量存储"""
        from utils.llm import get_embeddings

        embeddings = get_embeddings()

        # 生成嵌入向量
        vectors = await embeddings.aembed_documents(texts)

        # 准备数据
        data = {
            "texts": texts,
            "vectors": vectors,
            "metadatas": metadatas or [{}] * len(texts),
            "created_at": datetime.now().isoformat(),
        }

        # 保存到 JSON 存储
        await self.storage.set(f"vectors:{self.namespace}", data)

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
    ) -> List[Dict[str, Any]]:
        """相似度搜索"""
        from utils.llm import get_embeddings
        import numpy as np

        embeddings = get_embeddings()

        # 加载数据
        data = await self.storage.get(f"vectors:{self.namespace}")

        if not data or not data.get("vectors"):
            return []

        # 生成查询向量
        query_vector = await embeddings.aembed_query(query)

        # 计算相似度
        vectors = np.array(data["vectors"])
        query_vec = np.array(query_vector)

        # 使用余弦相似度
        similarities = np.dot(vectors, query_vec) / (
            np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vec)
        )

        # 获取 top-k
        top_k_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for idx in top_k_indices:
            results.append({
                "text": data["texts"][idx],
                "metadata": data.get("metadatas", [{}] * len(data["texts"]))[idx],
                "score": float(similarities[idx]),
            })

        return results

    async def delete(self) -> None:
        """删除命名空间的所有数据"""
        await self.storage.delete(f"vectors:{self.namespace}")


# 全局存储实例
json_storage = JSONStorage()


def owner_payload(user_id: int, username: str) -> Dict[str, Any]:
    return {
        "owner_id": user_id,
        "owner_username": username,
    }


def record_belongs_to_user(record: Optional[Dict[str, Any]], user_id: int, username: str) -> bool:
    if not isinstance(record, dict):
        return False
    owner_id = record.get("owner_id")
    if owner_id is None:
        return username == ADMIN_USERNAME
    try:
        return int(owner_id) == int(user_id)
    except Exception:
        return False


def filter_records_for_user(records: List[Dict[str, Any]], user_id: int, username: str) -> List[Dict[str, Any]]:
    return [item for item in records if record_belongs_to_user(item, user_id, username)]


def user_files_key(role: Optional[str], user_id: int) -> str:
    normalized = (role or "").strip().lower()
    base = "files_teacher" if normalized == "teacher" else "files"
    return f"{base}:user:{user_id}"


def legacy_files_key(role: Optional[str]) -> str:
    normalized = (role or "").strip().lower()
    return "files_teacher" if normalized == "teacher" else "files"


async def list_files_for_user(user_id: int, username: str, role: Optional[str]) -> List[Dict[str, Any]]:
    key = user_files_key(role, user_id)
    files = await json_storage.get(key) or []
    if username == ADMIN_USERNAME:
        legacy = await json_storage.get(legacy_files_key(role)) or []
        merged: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in [*files, *legacy]:
            item_id = str(item.get("id") or "")
            if item_id and item_id in seen:
                continue
            if item_id:
                seen.add(item_id)
            merged.append(item)
        return merged
    return files


async def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    """获取聊天会话"""
    return await json_storage.get(f"chat:{chat_id}")


async def create_chat(
    title: str,
    scope: str = "student",
    *,
    owner_id: Optional[int] = None,
    owner_username: Optional[str] = None,
    response_length: str = "Short",
    include_materials: bool = False,
    material_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """创建聊天会话，scope 为 student 或 teacher，用于教师端/学生端独立存储"""
    import uuid

    chat_id = str(uuid.uuid4())
    chat = {
        "id": chat_id,
        "title": title[:100],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "scope": scope,
        "length": response_length,
        "includeMaterials": include_materials,
        "materialIds": material_ids or [],
    }
    if owner_id is not None and owner_username is not None:
        chat.update(owner_payload(owner_id, owner_username))

    await json_storage.set(f"chat:{chat_id}", chat)
    await json_storage.set(f"chat:{chat_id}:messages", [])

    return chat


async def update_chat_settings(
    chat_id: str,
    *,
    response_length: str,
    include_materials: bool,
    material_ids: Optional[List[str]],
) -> None:
    if not isinstance(await json_storage.get(f"chat:{chat_id}"), dict):
        return

    def update_settings(chat: Any) -> Any:
        if not isinstance(chat, dict):
            return chat
        next_chat = dict(chat)
        next_chat["length"] = response_length
        next_chat["includeMaterials"] = include_materials
        next_chat["materialIds"] = material_ids or []
        next_chat["updated_at"] = datetime.now().isoformat()
        return next_chat

    await json_storage.update(f"chat:{chat_id}", update_settings, default={})


async def add_message(
    chat_id: str,
    role: str,
    content: str,
) -> None:
    """添加消息到聊天会话"""
    message = {
        "role": role,
        "content": content,
        "at": datetime.now().timestamp() * 1000,
    }

    await json_storage.update(
        f"chat:{chat_id}:messages",
        lambda messages: [*(messages if isinstance(messages, list) else []), message],
        default=[],
    )

    def touch_chat(chat: Any) -> Any:
        if not isinstance(chat, dict):
            return chat
        next_chat = dict(chat)
        next_chat["updated_at"] = datetime.now().isoformat()
        return next_chat

    if isinstance(await json_storage.get(f"chat:{chat_id}"), dict):
        await json_storage.update(f"chat:{chat_id}", touch_chat, default={})


async def get_messages(chat_id: str) -> List[Dict[str, Any]]:
    """获取聊天消息"""
    return await json_storage.get(f"chat:{chat_id}:messages") or []


async def list_chats(
    query: Optional[str] = None,
    scope: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """列出聊天会话；scope 为 student/teacher 时仅返回该端会话，None 时返回全部（兼容旧数据）"""
    chats: List[Dict[str, Any]] = []
    search = (query or "").strip().lower()

    for item in await json_storage.list_prefix("chat:"):
        if _is_auxiliary_item(item, ("_messages", "_length", "_materials")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue

        if scope is not None:
            doc_scope = data.get("scope") or "student"
            if doc_scope != scope:
                continue

        title = str(data.get("title") or "")
        if search and search not in title.lower():
            chat_id = data.get("id") or _item_entity_id(item, "chat:", 5)
            messages = await json_storage.get(f"chat:{chat_id}:messages") or []
            snippet = " ".join([str(m.get("content") or "") for m in messages[-20:]]).lower()
            if search not in snippet:
                continue
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        chats.append(data)

    chats.sort(key=lambda item: item.get("at", 0), reverse=True)
    return chats


async def delete_chat(chat_id: str) -> None:
    """删除聊天会话及其关联数据"""
    await json_storage.delete(f"chat:{chat_id}")
    await json_storage.delete(f"chat:{chat_id}:messages")
    await json_storage.delete(f"chat:{chat_id}:length")
    await json_storage.delete(f"chat:{chat_id}:materials")


async def list_quizzes(scope: Optional[str] = None, user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出测验历史；scope 为 student/teacher 时仅返回该端，None 时返回全部"""
    quizzes: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("quiz:"):
        if _is_auxiliary_item(
            item,
            ("_topic", "_count", "_materials", "_difficulty", "_quiz", "_attempts"),
        ):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        if scope is not None:
            doc_scope = data.get("scope") or "student"
            if doc_scope != scope:
                continue
        quiz_id = data.get("id") or _item_entity_id(item, "quiz:", 5)
        has_quiz = bool(await json_storage.get(f"quiz:{quiz_id}:quiz"))
        data["status"] = str(data.get("status") or ("ready" if has_quiz else "pending")).strip().lower()
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        quizzes.append(data)

    quizzes.sort(key=lambda item: item.get("at", 0), reverse=True)
    return quizzes


async def delete_quiz(quiz_id: str) -> None:
    """删除测验及其关联数据"""
    await json_storage.delete(f"quiz:{quiz_id}")
    await json_storage.delete(f"quiz:{quiz_id}:topic")
    await json_storage.delete(f"quiz:{quiz_id}:count")
    await json_storage.delete(f"quiz:{quiz_id}:difficulty")
    await json_storage.delete(f"quiz:{quiz_id}:materials")
    await json_storage.delete(f"quiz:{quiz_id}:quiz")
    await json_storage.delete(f"quiz:{quiz_id}:attempts")


async def get_quiz_attempts(quiz_id: str) -> List[Dict[str, Any]]:
    """获取测验作答记录"""
    return await json_storage.get(f"quiz:{quiz_id}:attempts") or []


async def set_quiz_attempts(quiz_id: str, attempts: List[Dict[str, Any]]) -> None:
    """设置测验作答记录"""
    await json_storage.update(f"quiz:{quiz_id}:attempts", lambda _current: list(attempts), default=[])


async def upsert_quiz_attempt(quiz_id: str, attempt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按 questionId 原子更新单题作答记录。"""
    question_id = attempt.get("questionId")

    def upsert(attempts: Any) -> List[Dict[str, Any]]:
        items = [dict(item) for item in attempts] if isinstance(attempts, list) else []
        for index, item in enumerate(items):
            if item.get("questionId") == question_id:
                items[index] = dict(attempt)
                return items
        items.append(dict(attempt))
        return items

    updated = await json_storage.update(f"quiz:{quiz_id}:attempts", upsert, default=[])
    return updated if isinstance(updated, list) else []


async def list_notes(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出笔记历史"""
    notes: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("note:"):
        if _is_auxiliary_item(item, ("_payload", "_notes")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        note_id = data.get("id") or _item_entity_id(item, "note:", 5)
        note_payload = await json_storage.get(f"note:{note_id}:notes")
        data["id"] = note_id
        data["status"] = derive_note_status(data, note_payload)
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        notes.append(data)

    notes.sort(key=lambda item: item.get("at", 0), reverse=True)
    return notes


async def delete_note(note_id: str) -> None:
    """删除笔记及其关联数据"""
    await json_storage.delete(f"note:{note_id}")
    await json_storage.delete(f"note:{note_id}:payload")
    await json_storage.delete(f"note:{note_id}:notes")


async def list_podcasts(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出播客历史"""
    base = config.storage_dir
    podcasts: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("podcast:"):
        if _is_auxiliary_item(item, ("_payload", "_script")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        pid = data.get("id") or _item_entity_id(item, "podcast:", 8)
        data["id"] = pid
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        script = await json_storage.get(f"podcast:{pid}:script")

        audio_file_name = _audio_filename_from_meta(data)
        if audio_file_name:
            data.update(_build_podcast_urls(pid, audio_file_name))

        # 如果 meta 中没有 file/static URL，尝试从文件系统查找
        if not data.get("file") and not data.get("static"):
            if pid:
                podcast_dir = base / "podcasts" / pid
                if podcast_dir.exists():
                    audio_file = _pick_first_audio_file(podcast_dir)
                    if audio_file:
                        data.update(_build_podcast_urls(pid, audio_file.name))
        data["status"] = derive_podcast_status(data, script)
        podcasts.append(data)

    podcasts.sort(key=lambda item: item.get("at", 0), reverse=True)
    return podcasts


async def delete_podcast(pid: str) -> None:
    """删除播客及其关联数据"""
    await json_storage.delete(f"podcast:{pid}")
    await json_storage.delete(f"podcast:{pid}:payload")
    await json_storage.delete(f"podcast:{pid}:script")
    await create_object_store().delete_prefix(f"podcasts/{pid}")


# ---------- 教案 (lesson_plan) ----------


async def list_lesson_plans(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出教案历史（教师端）"""
    plans: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("lesson_plan:"):
        if _is_auxiliary_item(item, ("_topic", "_materials", "_plan")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        lp_id = data.get("id") or _item_entity_id(item, "lesson_plan:", 12)
        data["id"] = lp_id
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        plans.append(data)

    plans.sort(key=lambda item: item.get("at", 0), reverse=True)
    return plans


async def delete_lesson_plan(lesson_plan_id: str) -> None:
    """删除教案及其关联数据"""
    await json_storage.delete(f"lesson_plan:{lesson_plan_id}")
    await json_storage.delete(f"lesson_plan:{lesson_plan_id}:topic")
    await json_storage.delete(f"lesson_plan:{lesson_plan_id}:materials")
    await json_storage.delete(f"lesson_plan:{lesson_plan_id}:plan")
    object_store = create_object_store()
    await object_store.delete(f"lesson_plans/{lesson_plan_id}.pdf")
    await object_store.delete_prefix(f"lesson_plans/{lesson_plan_id}")


# ---------- 试卷 (paper，教师端) ----------


async def list_papers(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出试卷历史（教师端）"""
    papers: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("paper:"):
        if _is_auxiliary_item(item, ("_topic", "_materials", "_difficulty", "_paper", "_counts")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        paper_id = data.get("id") or _item_entity_id(item, "paper:", 6)
        if not await json_storage.get(f"paper:{paper_id}:paper"):
            continue
        data["id"] = paper_id
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        papers.append(data)

    papers.sort(key=lambda item: item.get("at", 0), reverse=True)
    return papers


async def delete_paper(paper_id: str) -> None:
    """删除试卷及其关联数据"""
    await json_storage.delete(f"paper:{paper_id}")
    await json_storage.delete(f"paper:{paper_id}:topic")
    await json_storage.delete(f"paper:{paper_id}:materials")
    await json_storage.delete(f"paper:{paper_id}:difficulty")
    await json_storage.delete(f"paper:{paper_id}:counts")
    await json_storage.delete(f"paper:{paper_id}:paper")
    object_store = create_object_store()
    await object_store.delete(f"papers/{paper_id}.pdf")
    await object_store.delete_prefix(f"papers/{paper_id}")


# ---------- 教学视频 (teaching_video) ----------


async def list_teaching_videos(scope: Optional[str] = None, user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出教学视频历史；scope 为 student/teacher 时仅返回该端"""
    videos: List[Dict[str, Any]] = []

    for item in await json_storage.list_prefix("video:"):
        if _is_auxiliary_item(item, ("_topic", "_script", "_materials", "_video_url", "_local_path", "_audio_path")):
            continue
        if not isinstance(item.value, dict):
            continue
        data = dict(item.value)
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        if scope is not None:
            doc_scope = data.get("scope") or "teacher"
            if doc_scope != scope:
                continue
        vid = data.get("id") or _item_entity_id(item, "video:", 6)
        has_script = await json_storage.get(f"video:{vid}:script")
        has_video = await json_storage.get(f"video:{vid}:video_url")
        has_local = await json_storage.get(f"video:{vid}:local_path")
        has_audio = await json_storage.get(f"video:{vid}:audio_path")
        if not any((has_script, has_video, has_local, has_audio)):
            continue
        data["id"] = vid
        at = _to_epoch_ms(data.get("updated_at") or data.get("created_at"))
        data["at"] = at
        videos.append(data)

    videos.sort(key=lambda item: item.get("at", 0), reverse=True)
    return videos


async def delete_teaching_video(video_id: str) -> None:
    """删除教学视频及其关联数据（含本地 storage/teaching_videos/{id}/ 目录）"""
    await json_storage.delete(f"video:{video_id}")
    await json_storage.delete(f"video:{video_id}:topic")
    await json_storage.delete(f"video:{video_id}:script")
    await json_storage.delete(f"video:{video_id}:materials")
    await json_storage.delete(f"video:{video_id}:video_url")
    await json_storage.delete(f"video:{video_id}:local_path")
    await json_storage.delete(f"video:{video_id}:audio_path")
    await create_object_store().delete_prefix(f"teaching_videos/{video_id}")
