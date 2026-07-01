import asyncio
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from services import document_library as rag  # noqa: E402
from utils import feature_support  # noqa: E402
from utils.storage import JSONStorage  # noqa: E402


class FakeVectorStore:
    data = {}

    def __init__(self, namespace):
        self.namespace = namespace

    async def add_documents(self, texts, metadatas=None):
        self.data[self.namespace] = list(zip(texts, metadatas or [{} for _ in texts]))

    async def similarity_search(self, query, k=4):
        # Force the production keyword fallback path so tests do not need an embedding service.
        return []

    async def delete(self):
        self.data.pop(self.namespace, None)


def _meta(file_id: str, name: str, *, owner_id: int = 7):
    return {
        "id": file_id,
        "filename": name,
        "originalName": name,
        "objectKey": f"uploads/{name}",
        "mimeType": "text/plain",
        "owner_id": owner_id,
    }


def _write_upload(tmp_path: Path, name: str, text: str):
    path = tmp_path / "uploads" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _install_test_storage(tmp_path, monkeypatch):
    storage = JSONStorage(base_dir=tmp_path / "kv")
    monkeypatch.setattr(config, "storage_dir", tmp_path)
    monkeypatch.setattr(config, "object_store_provider", "local")
    monkeypatch.setattr(rag, "json_storage", storage)
    monkeypatch.setattr(rag, "VectorStore", FakeVectorStore)
    FakeVectorStore.data = {}
    return storage


def test_chunk_text_keeps_ranges_and_overlap():
    text = "第一段。" * 200

    chunks = rag.chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert chunks[0]["char_start"] == 0
    assert chunks[0]["char_end"] > chunks[0]["char_start"]
    assert chunks[1]["char_start"] < chunks[0]["char_end"]
    assert all(item["text"].strip() for item in chunks)


def test_multi_file_rag_context_includes_each_selected_file(tmp_path, monkeypatch):
    async def run():
        _install_test_storage(tmp_path, monkeypatch)
        _write_upload(tmp_path, "alpha.txt", "函数导数用于分析单调性和极值。" * 20)
        _write_upload(tmp_path, "beta.txt", "概率统计关注样本、均值、方差和分布。" * 20)
        files = [_meta("a", "alpha.txt"), _meta("b", "beta.txt")]

        context = await rag.build_rag_context_for_user_files(
            files,
            ["a", "b"],
            owner_id=7,
            role="teacher",
            query="函数 概率",
            max_chunks=4,
            max_chars=5000,
        )

        assert context.has_context
        assert "alpha.txt" in context.text
        assert "beta.txt" in context.text
        assert "函数导数" in context.text
        assert "概率统计" in context.text
        assert {item["name"] for item in context.files} == {"alpha.txt", "beta.txt"}
        assert len(context.chunks) >= 2

    asyncio.run(run())


def test_feature_support_selected_files_context_uses_rag(tmp_path, monkeypatch):
    async def run():
        _install_test_storage(tmp_path, monkeypatch)
        _write_upload(tmp_path, "one.txt", "牛顿第一定律说明惯性。" * 30)
        _write_upload(tmp_path, "two.txt", "牛顿第二定律说明力和加速度。" * 30)
        files = [_meta("one", "one.txt"), _meta("two", "two.txt")]

        context = await feature_support.build_selected_files_context(
            files,
            ["one", "two"],
            owner_id=7,
            role="teacher",
            query="牛顿定律",
            max_chars=4000,
        )

        assert "文件库 RAG 检索结果" in context
        assert "one.txt" in context
        assert "two.txt" in context

    asyncio.run(run())


def test_delete_file_index_removes_chunks_and_vector_namespace(tmp_path, monkeypatch):
    async def run():
        storage = _install_test_storage(tmp_path, monkeypatch)
        _write_upload(tmp_path, "remove.txt", "要删除的材料内容。" * 10)
        meta = _meta("remove", "remove.txt")

        result = await rag.index_file_meta(meta, owner_id=7, role="student")
        assert result.status == "ready"
        assert await storage.get("rag:file:remove:chunks")
        assert FakeVectorStore.data

        await rag.delete_file_index("remove", owner_id=7, role="student")

        assert await storage.get("rag:file:remove:chunks") is None
        assert await storage.get("rag:file:remove:status") is None

    asyncio.run(run())
