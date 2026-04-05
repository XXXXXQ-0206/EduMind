"""
数据存储工具
支持 JSON 文件存储和向量存储
"""
import json
import asyncio
import shutil
from pathlib import Path
from typing import Any, Optional, List, Dict
from datetime import datetime
from urllib.parse import unquote, urlparse
import aiofiles

from config import config
from utils.auth_db import ADMIN_USERNAME


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
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取数据"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except Exception:
            return None

    async def set(self, key: str, value: Any) -> None:
        """设置数据"""
        file_path = self._get_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with self.lock:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(value, ensure_ascii=False, indent=2))

    async def delete(self, key: str) -> None:
        """删除数据"""
        file_path = self._get_file_path(key)

        if file_path.exists():
            file_path.unlink()

    def _get_file_path(self, key: str) -> Path:
        """获取文件路径"""
        # 将 key 转换为安全的文件名
        # Windows 不允许的字符: < > : " / \ | ? *
        safe_key = key
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            safe_key = safe_key.replace(char, '_')
        return self.base_dir / f"{safe_key}.json"


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


async def create_chat(title: str, scope: str = "student") -> Dict[str, Any]:
    """创建聊天会话，scope 为 student 或 teacher，用于教师端/学生端独立存储"""
    import uuid

    chat_id = str(uuid.uuid4())
    chat = {
        "id": chat_id,
        "title": title[:100],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "scope": scope,
    }

    await json_storage.set(f"chat:{chat_id}", chat)
    await json_storage.set(f"chat:{chat_id}:messages", [])

    return chat


async def add_message(
    chat_id: str,
    role: str,
    content: str,
) -> None:
    """添加消息到聊天会话"""
    messages = await json_storage.get(f"chat:{chat_id}:messages") or []

    message = {
        "role": role,
        "content": content,
        "at": datetime.now().timestamp() * 1000,
    }

    messages.append(message)

    await json_storage.set(f"chat:{chat_id}:messages", messages)

    chat = await json_storage.get(f"chat:{chat_id}") or {}
    if chat:
        chat["updated_at"] = datetime.now().isoformat()
        await json_storage.set(f"chat:{chat_id}", chat)


async def get_messages(chat_id: str) -> List[Dict[str, Any]]:
    """获取聊天消息"""
    return await json_storage.get(f"chat:{chat_id}:messages") or []


async def list_chats(query: Optional[str] = None, scope: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出聊天会话；scope 为 student/teacher 时仅返回该端会话，None 时返回全部（兼容旧数据）"""
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    chats: List[Dict[str, Any]] = []
    search = (query or "").strip().lower()

    for path in base.glob("chat_*.json"):
        name = path.name
        if name.endswith("_messages.json") or name.endswith("_length.json"):
            continue
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue

        if scope is not None:
            doc_scope = data.get("scope") or "student"
            if doc_scope != scope:
                continue

        title = str(data.get("title") or "")
        if search and search not in title.lower():
            messages = await json_storage.get(f"chat:{data.get('id')}:messages") or []
            snippet = " ".join([str(m.get("content") or "") for m in messages[-20:]]).lower()
            if search not in snippet:
                continue
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    quizzes: List[Dict[str, Any]] = []

    for path in base.glob("quiz_*.json"):
        name = path.name
        if (
            name.endswith("_topic.json")
            or name.endswith("_count.json")
            or name.endswith("_materials.json")
            or name.endswith("_difficulty.json")
            or name.endswith("_quiz.json")
        ):
            continue
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        if scope is not None:
            doc_scope = data.get("scope") or "student"
            if doc_scope != scope:
                continue
        quiz_id = data.get("id") or path.stem[5:]
        has_quiz = bool(await json_storage.get(f"quiz:{quiz_id}:quiz"))
        data["status"] = str(data.get("status") or ("ready" if has_quiz else "pending")).strip().lower()
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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
    await json_storage.set(f"quiz:{quiz_id}:attempts", attempts)


async def list_notes(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出笔记历史"""
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    notes: List[Dict[str, Any]] = []

    for path in base.glob("note_*.json"):
        name = path.name
        if (
            name.endswith("_payload.json")
            or name.endswith("_notes.json")
        ):
            continue
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        note_id = data.get("id") or path.stem[5:]
        note_payload = await json_storage.get(f"note:{note_id}:notes")
        data["id"] = note_id
        data["status"] = derive_note_status(data, note_payload)
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    podcasts: List[Dict[str, Any]] = []

    for path in base.glob("podcast_*.json"):
        name = path.name
        if name.endswith("_payload.json") or name.endswith("_script.json"):
            continue
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        pid = data.get("id") or path.stem[8:]
        data["id"] = pid
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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
    dir_path = config.storage_dir / "podcasts" / pid
    if dir_path.exists():
        try:
            shutil.rmtree(dir_path)
        except Exception:
            return


# ---------- 教案 (lesson_plan) ----------


async def list_lesson_plans(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出教案历史（教师端）"""
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    plans: List[Dict[str, Any]] = []
    prefix = "lesson_plan_"
    suffix_skip = ("_topic", "_materials", "_plan")

    for path in base.glob("lesson_plan_*.json"):
        stem = path.stem
        if any(stem.endswith(s) for s in suffix_skip):
            continue
        if not stem.startswith(prefix):
            continue
        lp_id = stem[len(prefix):]
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        data["id"] = lp_id
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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


# ---------- 试卷 (paper，教师端) ----------


async def list_papers(user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出试卷历史（教师端）"""
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    papers: List[Dict[str, Any]] = []
    suffix_skip = ("_topic", "_materials", "_difficulty", "_paper", "_counts")

    for path in base.glob("paper_*.json"):
        stem = path.stem
        if any(stem.endswith(s) for s in suffix_skip):
            continue
        if not stem.startswith("paper_"):
            continue
        paper_id = stem[6:]  # len("paper_")
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        if not await json_storage.get(f"paper:{paper_id}:paper"):
            continue
        data["id"] = paper_id
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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


# ---------- 教学视频 (teaching_video) ----------


async def list_teaching_videos(scope: Optional[str] = None, user_id: Optional[int] = None, username: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出教学视频历史；scope 为 student/teacher 时仅返回该端"""
    def to_ms(value: Optional[str]) -> int:
        if not value:
            return 0
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except Exception:
            return 0

    base = config.storage_dir
    videos: List[Dict[str, Any]] = []
    suffix_skip = ("_topic", "_script", "_materials", "_video_url", "_local_path", "_audio_path")

    for path in base.glob("video_*.json"):
        stem = path.stem
        if any(stem.endswith(s) for s in suffix_skip):
            continue
        if not stem.startswith("video_"):
            continue
        vid = stem[6:]  # len("video_")
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if user_id is not None and username is not None and not record_belongs_to_user(data, user_id, username):
            continue
        if scope is not None:
            doc_scope = data.get("scope") or "teacher"
            if doc_scope != scope:
                continue
        has_script = await json_storage.get(f"video:{vid}:script")
        has_video = await json_storage.get(f"video:{vid}:video_url")
        has_local = await json_storage.get(f"video:{vid}:local_path")
        has_audio = await json_storage.get(f"video:{vid}:audio_path")
        if not any((has_script, has_video, has_local, has_audio)):
            continue
        data["id"] = vid
        at = to_ms(data.get("updated_at") or data.get("created_at"))
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
    # 删除本地有声版目录
    local_dir = config.storage_dir / "teaching_videos" / video_id
    if local_dir.exists():
        try:
            shutil.rmtree(local_dir)
        except Exception:
            pass
