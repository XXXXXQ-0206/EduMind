# Multi-File RAG Agent Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 agent 只能有效看到一个上传 PDF 的上下文构建缺陷，并在现有微服务化后端上建设可渐进落地的多文件 RAG 文件库。

**Architecture:** 先用公平预算的多文件上下文构建器恢复业务连续性，确保每个被选中文件至少有可见片段。随后在 `backend/rag/` 增加文档加载、分段、索引、检索和 agent 上下文编排层，复用当前 ObjectStore、JSONStorage、pgvector `VectorStore`、任务队列和 WebSocket/SSE 进度通道。所有 agent 入口统一调用 `prepare_agent_material_context()`，在向量检索不可用时降级到公平原文片段。

**Tech Stack:** Python 3.11, FastAPI, PostgreSQL + pgvector, Redis/Celery, existing ObjectStore/KV adapters, PyMuPDF, mammoth/python-docx, python-pptx, openpyxl, pytest, Vue 3 + TypeScript.

---

## Current Findings

- 上传链路不是单文件限制：`backend/api/routes/files.py` 的 `upload_files(file: List[UploadFile])` 已支持多文件，`frontend/src/lib/api.ts` 的 `uploadFiles(files: File[])` 也会追加多个 `file` 字段。
- 主要缺陷在 agent 材料上下文构建：`backend/utils/feature_support.py` 的 `build_files_context()` 采用全局 `max_chars` 和顺序截断，多个调用传入 `max_chars=8000, snippet_chars=8000`，第一个大 PDF 会吃完整个预算，后续文件被跳过。
- 这个问题被重复实现放大：`backend/api/routes/quiz.py`、`backend/api/routes/notes.py` 有自定义材料拼接逻辑，同样按顺序让第一个大文件占满上下文；`flashcards.py`、`podcast.py` 也会因为大 `snippet_chars` 出现首文件支配。
- `frontend/src/pages/Slides.vue` 目前即使勾选备课资料，也把 `materialIds` 固定传 `[]`，导致课件生成完全无法使用资料夹选择。
- 现有 `backend/utils/parser.py` 支持 PDF、DOCX、Markdown、TXT，但 `.doc` 实际会走 DOCX 解析并失败；PPTX、XLSX、CSV、JSON、HTML、多编码文本尚未作为一等文档输入处理。扫描版 PDF 没有 OCR 依赖，不能承诺可读。
- 项目已有 pgvector 基础：`backend/utils/storage.py` 的 `VectorStore` 可按 namespace 写入和检索，但它是通用“单 namespace 批量替换”能力，还没有文件级索引状态、跨文件检索、引用源信息和 agent 前置 RAG 编排。

## File Structure

### Existing files to modify

- `backend/utils/feature_support.py`: 增强公平多文件上下文构建，并保留当前公开函数名兼容既有 route。
- `backend/utils/parser.py`: 扩展文档解析类型和文本编码兜底。
- `backend/config.py`: 增加 RAG 配置项。
- `backend/api/routes/files.py`: 上传后创建 RAG 状态、删除时清理索引、暴露索引状态和触发索引接口。
- `backend/api/routes/chat.py`: 聊天 agent 前置 RAG 上下文。
- `backend/api/routes/quiz.py`: 删除自定义材料拼接，统一使用 RAG 上下文。
- `backend/api/routes/notes.py`: 删除全文拼接，统一使用 RAG 上下文。
- `backend/api/routes/flashcards.py`: 知识卡片生成统一使用 RAG 上下文。
- `backend/api/routes/lesson_plan.py`: 教案生成统一使用 RAG 上下文。
- `backend/api/routes/paper.py`: 试卷生成统一使用 RAG 上下文。
- `backend/api/routes/podcast.py`: 播客生成统一使用 RAG 上下文。
- `backend/api/routes/slides.py`: 课件生成统一使用 RAG 上下文。
- `backend/api/routes/teaching_video.py`: 教学视频脚本生成统一使用 RAG 上下文。
- `frontend/src/lib/api.ts`: 增加 RAG 状态类型和文件索引 API。
- `frontend/src/pages/FileLibrary.vue`: 展示索引状态，支持手动重建索引。
- `frontend/src/components/LearningFolderPanel.vue`: 显示已选文件数量、名称和可用状态。
- `frontend/src/pages/Slides.vue`: 修正 `materialIds` 传参。
- `README.md`, `knowledge.md`: 记录多文件 RAG 文件库能力与限制。

### New files to create

- `backend/rag/__init__.py`: RAG 包导出。
- `backend/rag/models.py`: RAG 索引、片段、检索结果和 agent 上下文数据模型。
- `backend/rag/document_loader.py`: 从文件 metadata 解析文本，统一支持 ObjectStore 路径、sidecar 和 parser。
- `backend/rag/chunking.py`: 稳定文本清洗和重叠分段。
- `backend/rag/indexer.py`: 文件级 hash、索引状态、pgvector 写入和删除。
- `backend/rag/retriever.py`: 对多个 file namespace 执行检索、合并、去重和公平覆盖。
- `backend/rag/context.py`: agent 前置 RAG 编排，提供成功上下文、引用源和降级诊断。
- `tests/backend/test_multi_file_context.py`: 多文件公平上下文测试。
- `tests/backend/test_document_loader.py`: 文档解析和编码兜底测试。
- `tests/backend/test_rag_chunking.py`: 分段测试。
- `tests/backend/test_rag_indexer.py`: 索引状态和 pgvector 调用测试。
- `tests/backend/test_rag_context.py`: RAG 检索、降级和 agent 上下文整合测试。
- `docs/architecture/file-library-rag.md`: 系统设计、API、数据模型和运维说明。

## Data Contracts

### RAG metadata in KV

Key: `rag:file:{file_id}`

```json
{
  "fileId": "uuid",
  "status": "pending",
  "owner_id": 1,
  "owner_username": "teacher",
  "role": "teacher",
  "objectKey": "uploads/...",
  "originalName": "chapter.pdf",
  "mimeType": "application/pdf",
  "size": 1024,
  "contentHash": "",
  "chunkCount": 0,
  "indexedAt": "",
  "error": ""
}
```

Valid status values: `pending`, `indexing`, `indexed`, `failed`, `unsupported`.

### pgvector namespace

- Namespace per file: `file:{file_id}`.
- Each chunk metadata:

```json
{
  "file_id": "uuid",
  "owner_id": 1,
  "role": "teacher",
  "original_name": "chapter.pdf",
  "object_key": "uploads/...",
  "chunk_index": 0,
  "char_start": 0,
  "char_end": 900,
  "content_hash": "sha256..."
}
```

### Agent material context

`prepare_agent_material_context()` returns a structured result:

```python
AgentMaterialContext(
    context="资料内容...",
    sources=[{"fileId": "...", "name": "...", "chunkIndex": 0, "score": 0.81}],
    diagnostics=[{"fileId": "...", "status": "indexed", "message": "2 chunks used"}],
    degraded=False,
)
```

Routes may still inject only `context` into existing prompts during the first integration pass, but they must preserve `sources` and `diagnostics` in storage or events where the feature already stores generation metadata.

## Task 1: Reproduce And Fix Fair Multi-File Context

**Files:**
- Modify: `backend/utils/feature_support.py`
- Create: `tests/backend/test_multi_file_context.py`

- [ ] **Step 1: Write failing tests for fair file coverage**

Create `tests/backend/test_multi_file_context.py`:

```python
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from utils.feature_support import build_selected_files_context  # noqa: E402


def _write_upload(tmp_path: Path, name: str, text: str) -> dict:
    upload_path = tmp_path / "uploads" / name
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    upload_path.write_text("binary-placeholder", encoding="utf-8")
    Path(str(upload_path) + ".txt").write_text(text, encoding="utf-8")
    return {
        "id": name,
        "originalName": name,
        "filename": name,
        "objectKey": f"uploads/{name}",
        "mimeType": "text/plain",
    }


def test_selected_files_context_keeps_each_selected_file_visible(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        files = [
            _write_upload(tmp_path, "first.txt", "FIRST-" + ("a" * 12000)),
            _write_upload(tmp_path, "second.txt", "SECOND-" + ("b" * 12000)),
            _write_upload(tmp_path, "third.txt", "THIRD-" + ("c" * 12000)),
        ]

        context = await build_selected_files_context(
            files,
            ["first.txt", "second.txt", "third.txt"],
            max_chars=2400,
            snippet_chars=2400,
        )

        assert "[资料 1/3] first.txt" in context
        assert "[资料 2/3] second.txt" in context
        assert "[资料 3/3] third.txt" in context
        assert "FIRST-" in context
        assert "SECOND-" in context
        assert "THIRD-" in context
        assert len(context) <= 2600

    asyncio.run(run())


def test_selected_files_context_respects_selection_order(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        files = [
            _write_upload(tmp_path, "a.txt", "AAA"),
            _write_upload(tmp_path, "b.txt", "BBB"),
            _write_upload(tmp_path, "c.txt", "CCC"),
        ]

        context = await build_selected_files_context(
            files,
            ["c.txt", "a.txt"],
            max_chars=1200,
            snippet_chars=1200,
        )

        assert context.index("c.txt") < context.index("a.txt")
        assert "b.txt" not in context

    asyncio.run(run())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
pytest tests/backend/test_multi_file_context.py -q
```

Expected before implementation: first test fails because only `first.txt` appears.

- [ ] **Step 3: Implement fair allocation in `feature_support.py`**

Replace the current `build_files_context()` body with a two-pass implementation that reads selected files first, allocates a base budget per readable file, then uses remaining budget for extra content:

```python
async def build_files_context(
    files: Iterable[Dict[str, Any]],
    *,
    max_chars: int = 12000,
    snippet_chars: int = 2500,
) -> str:
    file_items = [dict(item) for item in files if isinstance(item, dict)]
    readable: List[Dict[str, Any]] = []

    for index, meta in enumerate(file_items):
        text = (await extract_file_text_from_meta(meta)).strip()
        if not text:
            continue
        readable.append({"index": index, "meta": meta, "text": text})

    if not readable or max_chars <= 0:
        return ""

    per_file_budget = max(300, max_chars // len(readable))
    chunks: List[str] = []
    used = 0

    for visible_index, item in enumerate(readable, start=1):
        meta = item["meta"]
        text = item["text"]
        name = meta.get("originalName") or meta.get("filename") or "document"
        header = f"[资料 {visible_index}/{len(readable)}] {name}\n"
        body_budget = max(0, min(snippet_chars, per_file_budget) - len(header) - 2)
        if body_budget <= 0:
            continue
        body = compact_text(text, body_budget)
        chunk = f"{header}{body}"
        if used + len(chunk) > max_chars and chunks:
            break
        chunks.append(chunk)
        used += len(chunk) + 2

    if used < max_chars:
        expanded: List[str] = []
        extra_budget = max_chars
        for visible_index, item in enumerate(readable, start=1):
            meta = item["meta"]
            text = item["text"]
            name = meta.get("originalName") or meta.get("filename") or "document"
            header = f"[资料 {visible_index}/{len(readable)}] {name}\n"
            remaining_files = max(1, len(readable) - len(expanded))
            body_budget = max(0, min(snippet_chars, extra_budget // remaining_files) - len(header) - 2)
            if body_budget <= 0:
                continue
            body = compact_text(text, body_budget)
            chunk = f"{header}{body}"
            expanded.append(chunk)
            extra_budget -= len(chunk) + 2
        chunks = expanded or chunks

    return "\n\n".join(part for part in chunks if part).strip()
```

Keep `build_selected_files_context()` signature unchanged so existing route imports continue to work.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
pytest tests/backend/test_multi_file_context.py -q
```

Expected: 2 passed.

- [ ] **Step 5: Run existing adapter tests**

Run:

```powershell
pytest tests/backend/test_infrastructure_adapters.py -q
```

Expected: all existing tests pass, especially `test_selected_files_context_uses_object_keys`.

- [ ] **Step 6: Commit**

```powershell
git add backend/utils/feature_support.py tests/backend/test_multi_file_context.py
git commit -m "fix: keep multiple selected files visible in agent context"
```

## Task 2: Remove Duplicated Route Context Builders And Fix Slides Material IDs

**Files:**
- Modify: `backend/api/routes/quiz.py`
- Modify: `backend/api/routes/notes.py`
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/api/routes/flashcards.py`
- Modify: `backend/api/routes/lesson_plan.py`
- Modify: `backend/api/routes/paper.py`
- Modify: `backend/api/routes/podcast.py`
- Modify: `backend/api/routes/slides.py`
- Modify: `backend/api/routes/teaching_video.py`
- Modify: `frontend/src/pages/Slides.vue`
- Test: `tests/backend/test_multi_file_context.py`

- [ ] **Step 1: Replace custom quiz material builder**

In `backend/api/routes/quiz.py`, replace:

```python
from utils.feature_support import extract_file_text_from_meta
```

with:

```python
from utils.feature_support import build_selected_files_context
```

Replace `_build_material_context()` with:

```python
async def _build_material_context(owner_id: int, owner_username: str, quiz_scope: str, ids: List[str]) -> str:
    if not ids:
        return ""
    files = await list_files_for_user(owner_id, owner_username, quiz_scope)
    return await build_selected_files_context(files, ids, max_chars=8000, snippet_chars=8000)
```

- [ ] **Step 2: Replace custom smartnotes material builder**

In `backend/api/routes/notes.py`, replace:

```python
from utils.feature_support import extract_file_text_from_meta
```

with:

```python
from utils.feature_support import build_selected_files_context
```

Replace `_build_note_material_context()` with:

```python
async def _build_note_material_context(note_id: str, ids: List[str]) -> str:
    if not ids:
        return ""
    meta = await json_storage.get(f"note:{note_id}") or {}
    owner_id = int(meta.get("owner_id") or 0)
    owner_username = str(meta.get("owner_username") or "")
    files = await list_files_for_user(owner_id, owner_username, "student")
    return await build_selected_files_context(files, ids, max_chars=12000, snippet_chars=12000)
```

- [ ] **Step 3: Normalize high-risk `snippet_chars` calls**

Use the fair builder from Task 1, but keep feature-specific total budgets:

```python
# chat.py
return await build_selected_files_context(files, selected_ids, max_chars=8000, snippet_chars=4000)

# flashcards.py
return await build_selected_files_context(files, ids, max_chars=16000, snippet_chars=6000)

# lesson_plan.py
return await build_selected_files_context(files, material_ids, max_chars=10000, snippet_chars=5000)

# paper.py
materials_text = await build_selected_files_context(files, material_ids, max_chars=10000, snippet_chars=5000)

# podcast.py
return await build_selected_files_context(files, ids, max_chars=24000, snippet_chars=8000)

# slides.py
materials_text = await build_selected_files_context(files, material_ids, max_chars=10000, snippet_chars=5000)

# teaching_video.py
return await build_selected_files_context(files, ids, max_chars=10000, snippet_chars=5000)
```

- [ ] **Step 4: Fix slides frontend material IDs**

In `frontend/src/pages/Slides.vue`, add the same localStorage reader used by the other teacher pages:

```ts
const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("edumind-learning-folder-teacher"));

function loadLearningFolderIds(): string[] {
  try {
    const raw = localStorage.getItem(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean) : [];
  } catch {
    return [];
  }
}
```

Then replace the payload:

```ts
const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
const useMaterials = includeMaterials.value && materialIds.length > 0;

const res = await generateSlides({
  topic: topicText,
  pageCount: pageCount.value,
  includeMaterials: useMaterials,
  materialIds: useMaterials ? materialIds : [],
});
```

- [ ] **Step 5: Run backend and frontend verification**

Run:

```powershell
pytest tests/backend/test_multi_file_context.py tests/backend/test_infrastructure_adapters.py -q
npm run build
```

Expected: pytest passes, Vite build completes without TypeScript errors.

- [ ] **Step 6: Commit**

```powershell
git add backend/api/routes/quiz.py backend/api/routes/notes.py backend/api/routes/chat.py backend/api/routes/flashcards.py backend/api/routes/lesson_plan.py backend/api/routes/paper.py backend/api/routes/podcast.py backend/api/routes/slides.py backend/api/routes/teaching_video.py frontend/src/pages/Slides.vue
git commit -m "fix: route all selected materials through fair context builder"
```

## Task 3: Add Document Loader And Parser Coverage

**Files:**
- Modify: `requirements.txt`
- Modify: `backend/utils/parser.py`
- Create: `backend/rag/__init__.py`
- Create: `backend/rag/document_loader.py`
- Create: `tests/backend/test_document_loader.py`

- [ ] **Step 1: Add XLSX dependency**

Append to the document parsing section in `requirements.txt`:

```text
openpyxl==3.1.5
```

- [ ] **Step 2: Extend parser type detection**

In `backend/utils/parser.py`, update `_guess_mime_type()`:

```python
mime_map = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}
```

Add parser branches:

```python
if "presentationml" in mime_type.lower() or path.suffix.lower() == ".pptx":
    return await _extract_pptx(file_path)

if "spreadsheetml" in mime_type.lower() or path.suffix.lower() == ".xlsx":
    return await _extract_xlsx(file_path)

if "csv" in mime_type.lower() or path.suffix.lower() == ".csv":
    return await _extract_text(file_path)

if "json" in mime_type.lower() or path.suffix.lower() == ".json":
    return await _extract_text(file_path)

if "html" in mime_type.lower() or path.suffix.lower() in [".html", ".htm"]:
    return await _extract_text(file_path)
```

Add legacy Office guard before DOCX parsing:

```python
if path.suffix.lower() in {".doc", ".ppt", ".xls"}:
    raise ValueError("Legacy binary Office files require conversion to DOCX/PPTX/XLSX before indexing")
```

- [ ] **Step 3: Add PPTX, XLSX, and encoding fallback helpers**

Add to `backend/utils/parser.py`:

```python
async def _extract_pptx(file_path: str) -> str:
    from pptx import Presentation

    presentation = Presentation(file_path)
    parts: list[str] = []
    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_parts: list[str] = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text = str(shape.text or "").strip()
                if text:
                    slide_parts.append(text)
        if slide_parts:
            parts.append(f"Slide {slide_number}\n" + "\n".join(slide_parts))
    return "\n\n".join(parts)


async def _extract_xlsx(file_path: str) -> str:
    from openpyxl import load_workbook

    workbook = load_workbook(file_path, read_only=True, data_only=True)
    parts: list[str] = []
    try:
        for sheet in workbook.worksheets:
            rows: list[str] = []
            for row in sheet.iter_rows(values_only=True):
                values = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if values:
                    rows.append("\t".join(values))
                if len(rows) >= 500:
                    rows.append("[sheet truncated at 500 non-empty rows]")
                    break
            if rows:
                parts.append(f"Sheet: {sheet.title}\n" + "\n".join(rows))
    finally:
        workbook.close()
    return "\n\n".join(parts)


async def _extract_text(file_path: str) -> str:
    encodings = ("utf-8", "utf-8-sig", "gb18030", "latin-1")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            async with aiofiles.open(file_path, "r", encoding=encoding) as f:
                return await f.read()
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return ""
```

- [ ] **Step 4: Create document loader wrapper**

Create `backend/rag/__init__.py`:

```python
"""RAG helpers for uploaded document indexing and agent context."""
```

Create `backend/rag/document_loader.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from utils.feature_support import extract_file_text_from_meta


@dataclass(frozen=True)
class LoadedDocument:
    file_id: str
    name: str
    mime_type: str
    text: str


async def load_document_from_meta(meta: Dict[str, Any]) -> LoadedDocument:
    file_id = str(meta.get("id") or "")
    name = str(meta.get("originalName") or meta.get("filename") or "document")
    mime_type = str(meta.get("mimeType") or "application/octet-stream")
    text = (await extract_file_text_from_meta(meta)).strip()
    if not file_id:
        raise ValueError("file id is required")
    if not text:
        raise ValueError(f"No extractable text found in {name}")
    return LoadedDocument(file_id=file_id, name=name, mime_type=mime_type, text=text)
```

- [ ] **Step 5: Add parser tests**

Create `tests/backend/test_document_loader.py`:

```python
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from rag.document_loader import load_document_from_meta  # noqa: E402
from utils.parser import extract_text_from_file  # noqa: E402


def test_text_parser_reads_gb18030(tmp_path):
    async def run():
        path = tmp_path / "note.txt"
        path.write_bytes("中文内容".encode("gb18030"))
        assert "中文内容" in await extract_text_from_file(str(path), "text/plain")

    asyncio.run(run())


def test_document_loader_uses_sidecar_text(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        upload = tmp_path / "uploads" / "chapter.pdf"
        upload.parent.mkdir(parents=True, exist_ok=True)
        upload.write_bytes(b"%PDF-placeholder")
        Path(str(upload) + ".txt").write_text("sidecar chapter text", encoding="utf-8")

        doc = await load_document_from_meta({
            "id": "file-1",
            "originalName": "chapter.pdf",
            "objectKey": "uploads/chapter.pdf",
            "mimeType": "application/pdf",
        })

        assert doc.file_id == "file-1"
        assert doc.name == "chapter.pdf"
        assert doc.text == "sidecar chapter text"

    asyncio.run(run())
```

- [ ] **Step 6: Run tests**

Run:

```powershell
pytest tests/backend/test_document_loader.py -q
```

Expected: tests pass.

- [ ] **Step 7: Commit**

```powershell
git add requirements.txt backend/utils/parser.py backend/rag/__init__.py backend/rag/document_loader.py tests/backend/test_document_loader.py
git commit -m "feat: load common document formats for rag indexing"
```

## Task 4: Add RAG Models And Chunking

**Files:**
- Create: `backend/rag/models.py`
- Create: `backend/rag/chunking.py`
- Create: `tests/backend/test_rag_chunking.py`

- [ ] **Step 1: Create RAG data models**

Create `backend/rag/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal


RagStatus = Literal["pending", "indexing", "indexed", "failed", "unsupported"]


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    chunk_index: int
    char_start: int
    char_end: int


@dataclass(frozen=True)
class RagSource:
    file_id: str
    name: str
    chunk_index: int
    score: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagDiagnostic:
    file_id: str
    status: str
    message: str


@dataclass(frozen=True)
class AgentMaterialContext:
    context: str
    sources: List[RagSource] = field(default_factory=list)
    diagnostics: List[RagDiagnostic] = field(default_factory=list)
    degraded: bool = False
```

- [ ] **Step 2: Create deterministic chunking**

Create `backend/rag/chunking.py`:

```python
from __future__ import annotations

import re
from typing import List

from rag.models import DocumentChunk


def normalize_document_text(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 120) -> List[DocumentChunk]:
    normalized = normalize_document_text(text)
    if not normalized:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    chunks: List[DocumentChunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            boundary = max(normalized.rfind("\n\n", start, end), normalized.rfind("。", start, end), normalized.rfind(".", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(DocumentChunk(text=piece, chunk_index=index, char_start=start, char_end=end))
            index += 1
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
```

- [ ] **Step 3: Add chunking tests**

Create `tests/backend/test_rag_chunking.py`:

```python
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from rag.chunking import chunk_text, normalize_document_text  # noqa: E402


def test_normalize_document_text_compacts_spaces_and_blank_lines():
    assert normalize_document_text("a   b\r\n\r\n\r\nc") == "a b\n\nc"


def test_chunk_text_uses_overlap_and_stable_indices():
    chunks = chunk_text("0123456789" * 50, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].char_start == chunks[0].char_end - 20
    assert all(chunk.text for chunk in chunks)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/backend/test_rag_chunking.py -q
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add backend/rag/models.py backend/rag/chunking.py tests/backend/test_rag_chunking.py
git commit -m "feat: add rag chunking models"
```

## Task 5: Add File Indexer, Status API, And Cleanup

**Files:**
- Modify: `backend/config.py`
- Create: `backend/rag/indexer.py`
- Modify: `backend/api/routes/files.py`
- Create: `tests/backend/test_rag_indexer.py`

- [ ] **Step 1: Add RAG config defaults**

In `backend/config.py`, add fields to `Settings`:

```python
rag_enabled: bool = Field(default=True, alias="RAG_ENABLED")
rag_chunk_size: int = Field(default=900, alias="RAG_CHUNK_SIZE")
rag_chunk_overlap: int = Field(default=120, alias="RAG_CHUNK_OVERLAP")
rag_top_k: int = Field(default=8, alias="RAG_TOP_K")
rag_per_file_k: int = Field(default=2, alias="RAG_PER_FILE_K")
rag_max_context_chars: int = Field(default=12000, alias="RAG_MAX_CONTEXT_CHARS")
```

Add matching values to `.env.example`:

```dotenv
RAG_ENABLED=true
RAG_CHUNK_SIZE=900
RAG_CHUNK_OVERLAP=120
RAG_TOP_K=8
RAG_PER_FILE_K=2
RAG_MAX_CONTEXT_CHARS=12000
```

- [ ] **Step 2: Create indexer**

Create `backend/rag/indexer.py`:

```python
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List

from config import config
from infrastructure.object_store import create_object_store
from rag.chunking import chunk_text
from rag.document_loader import load_document_from_meta
from utils.storage import VectorStore, json_storage
from utils.upload_objects import upload_object_key_from_meta


def rag_status_key(file_id: str) -> str:
    return f"rag:file:{file_id}"


def file_namespace(file_id: str) -> str:
    return f"file:{file_id}"


async def compute_file_hash(meta: Dict[str, Any]) -> str:
    object_key = upload_object_key_from_meta(meta)
    if not object_key:
        return ""
    content = await create_object_store().get_bytes(object_key)
    return hashlib.sha256(content).hexdigest()


async def initialize_rag_status(meta: Dict[str, Any], role: str | None) -> Dict[str, Any]:
    file_id = str(meta.get("id") or "")
    status = {
        "fileId": file_id,
        "status": "pending",
        "owner_id": meta.get("owner_id"),
        "owner_username": meta.get("owner_username"),
        "role": (role or "student").strip().lower() or "student",
        "objectKey": meta.get("objectKey"),
        "originalName": meta.get("originalName") or meta.get("filename"),
        "mimeType": meta.get("mimeType") or "application/octet-stream",
        "size": meta.get("size") or 0,
        "contentHash": "",
        "chunkCount": 0,
        "indexedAt": "",
        "error": "",
    }
    if file_id:
        await json_storage.set(rag_status_key(file_id), status)
    return status


async def delete_file_index(file_id: str) -> None:
    if not file_id:
        return
    await VectorStore(file_namespace(file_id)).delete()
    await json_storage.delete(rag_status_key(file_id))


async def ensure_file_indexed(meta: Dict[str, Any], role: str | None = None) -> Dict[str, Any]:
    file_id = str(meta.get("id") or "")
    if not file_id:
        raise ValueError("file id is required")

    existing = await json_storage.get(rag_status_key(file_id)) or await initialize_rag_status(meta, role)
    content_hash = await compute_file_hash(meta)
    if existing.get("status") == "indexed" and existing.get("contentHash") == content_hash:
        return existing

    status = dict(existing)
    status.update({"status": "indexing", "error": ""})
    await json_storage.set(rag_status_key(file_id), status)

    try:
        document = await load_document_from_meta(meta)
        chunks = chunk_text(document.text, chunk_size=config.rag_chunk_size, overlap=config.rag_chunk_overlap)
        if not chunks:
            raise ValueError("No extractable text chunks found")
        texts = [chunk.text for chunk in chunks]
        metadatas: List[Dict[str, Any]] = []
        for chunk in chunks:
            metadatas.append({
                "file_id": file_id,
                "owner_id": meta.get("owner_id"),
                "role": (role or status.get("role") or "student"),
                "original_name": document.name,
                "object_key": meta.get("objectKey"),
                "chunk_index": chunk.chunk_index,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "content_hash": content_hash,
            })
        await VectorStore(file_namespace(file_id)).add_documents(texts, metadatas)
        status.update({
            "status": "indexed",
            "contentHash": content_hash,
            "chunkCount": len(chunks),
            "indexedAt": datetime.now().isoformat(),
            "error": "",
        })
    except ValueError as exc:
        message = str(exc)
        next_status = "unsupported" if "Legacy binary Office" in message else "failed"
        status.update({"status": next_status, "error": message, "chunkCount": 0})
    except Exception as exc:
        status.update({"status": "failed", "error": str(exc), "chunkCount": 0})

    await json_storage.set(rag_status_key(file_id), status)
    return status
```

- [ ] **Step 3: Wire file upload status and delete cleanup**

In `backend/api/routes/files.py`, import:

```python
import asyncio

from config import config
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from rag.indexer import delete_file_index, ensure_file_indexed, initialize_rag_status, rag_status_key
```

After each `meta` is appended in upload, initialize status and store a lookup copy for background indexing:

```python
await initialize_rag_status(meta, role)
await json_storage.set(f"file_meta:{meta['id']}", {**meta, "role": (role or "student")})
```

Add a non-blocking index dispatcher:

```python
async def _dispatch_file_index(file_id: str) -> None:
    provider = (config.task_queue_provider or "inline").strip().lower()
    if provider in {"inline", "memory", "none"}:
        asyncio.create_task(_ensure_file_index_task(file_id))
        return
    await dispatch_generation_task("file-index", file_id, _ensure_file_index_task)
```

After upload storage update, enqueue indexing:

```python
for meta in saved:
    await _dispatch_file_index(meta["id"])
```

In delete route, after object delete:

```python
await delete_file_index(file_id)
await json_storage.delete(f"file_meta:{file_id}")
```

Add the task handler:

```python
async def _ensure_file_index_task(file_id: str) -> None:
    meta = await json_storage.get(f"file_meta:{file_id}")
    if isinstance(meta, dict):
        await ensure_file_indexed(meta, str(meta.get("role") or "student"))


register_task_handler("file-index", _ensure_file_index_task)
```

Add status endpoints:

```python
@router.get("/files/{file_id}/rag-status")
async def get_file_rag_status(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    files = await list_files_for_user(user.id, user.username, role)
    if not any(str(item.get("id")) == file_id for item in files):
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    status = await json_storage.get(rag_status_key(file_id))
    return {"ok": True, "status": status or {"fileId": file_id, "status": "pending"}}


@router.post("/files/{file_id}/index")
async def rebuild_file_index(file_id: str, role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    files = await list_files_for_user(user.id, user.username, role)
    meta = next((item for item in files if str(item.get("id")) == file_id), None)
    if not meta:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    status = await ensure_file_indexed(meta, role)
    return {"ok": True, "status": status}
```

- [ ] **Step 4: Add indexer unit tests with monkeypatched vector store**

Create `tests/backend/test_rag_indexer.py`:

```python
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from rag import indexer as indexer_module  # noqa: E402
from utils.storage import JSONStorage  # noqa: E402


class FakeVectorStore:
    calls = []

    def __init__(self, namespace):
        self.namespace = namespace

    async def add_documents(self, texts, metadatas=None):
        FakeVectorStore.calls.append((self.namespace, texts, metadatas))

    async def delete(self):
        FakeVectorStore.calls.append((self.namespace, "delete", None))


def test_ensure_file_indexed_writes_status_and_vectors(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        monkeypatch.setattr(config, "rag_chunk_size", 40)
        monkeypatch.setattr(config, "rag_chunk_overlap", 5)
        monkeypatch.setattr(indexer_module, "json_storage", JSONStorage(base_dir=tmp_path / "kv"))
        monkeypatch.setattr(indexer_module, "VectorStore", FakeVectorStore)
        FakeVectorStore.calls.clear()

        upload = tmp_path / "uploads" / "lesson.txt"
        upload.parent.mkdir(parents=True, exist_ok=True)
        upload.write_text("lesson " * 50, encoding="utf-8")
        meta = {
            "id": "file-1",
            "originalName": "lesson.txt",
            "objectKey": "uploads/lesson.txt",
            "mimeType": "text/plain",
            "owner_id": 7,
        }

        status = await indexer_module.ensure_file_indexed(meta, "student")

        assert status["status"] == "indexed"
        assert status["chunkCount"] > 1
        assert FakeVectorStore.calls[0][0] == "file:file-1"
        assert FakeVectorStore.calls[0][2][0]["file_id"] == "file-1"

    asyncio.run(run())
```

- [ ] **Step 5: Run tests**

Run:

```powershell
pytest tests/backend/test_rag_indexer.py -q
```

Expected: tests pass.

- [ ] **Step 6: Commit**

```powershell
git add backend/config.py .env.example backend/rag/indexer.py backend/api/routes/files.py tests/backend/test_rag_indexer.py
git commit -m "feat: index uploaded files into rag vector store"
```

## Task 6: Add Multi-File Retriever And Agent Context Assembly

**Files:**
- Create: `backend/rag/retriever.py`
- Create: `backend/rag/context.py`
- Create: `tests/backend/test_rag_context.py`

- [ ] **Step 1: Create retriever using one namespace per selected file**

Create `backend/rag/retriever.py`:

```python
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from config import config
from rag.indexer import file_namespace
from utils.storage import VectorStore


async def retrieve_from_files(query: str, file_ids: Iterable[str], *, per_file_k: int | None = None, top_k: int | None = None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    per_file = max(1, int(per_file_k or config.rag_per_file_k))
    for file_id in [str(item) for item in file_ids if item]:
        store = VectorStore(file_namespace(file_id))
        for item in await store.similarity_search(query, k=per_file):
            metadata = dict(item.get("metadata") or {})
            metadata.setdefault("file_id", file_id)
            results.append({
                "text": item.get("text") or "",
                "metadata": metadata,
                "score": float(item.get("score") or 0.0),
            })
    results.sort(key=lambda item: item["score"], reverse=True)
    limit = max(1, int(top_k or config.rag_top_k))
    return results[:limit]
```

- [ ] **Step 2: Create context assembler with fallback**

Create `backend/rag/context.py`:

```python
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from config import config
from rag.indexer import ensure_file_indexed
from rag.models import AgentMaterialContext, RagDiagnostic, RagSource
from rag.retriever import retrieve_from_files
from utils.feature_support import build_selected_files_context, compact_text


def _selected_file_list(files: Iterable[Dict[str, Any]], ids: Iterable[Any]) -> List[Dict[str, Any]]:
    file_list = [dict(item) for item in files if isinstance(item, dict)]
    file_map = {str(item.get("id")): item for item in file_list if item.get("id")}
    selected_ids = [str(item) for item in ids if item]
    return [file_map[item] for item in selected_ids if item in file_map] if selected_ids else file_list


def _format_rag_context(results: List[Dict[str, Any]], max_chars: int) -> tuple[str, List[RagSource]]:
    parts: List[str] = []
    sources: List[RagSource] = []
    used = 0
    for item in results:
        metadata = dict(item.get("metadata") or {})
        file_id = str(metadata.get("file_id") or "")
        name = str(metadata.get("original_name") or metadata.get("originalName") or metadata.get("file_name") or "document")
        chunk_index = int(metadata.get("chunk_index") or 0)
        score = float(item.get("score") or 0.0)
        header = f"[资料片段] {name} #chunk-{chunk_index} score={score:.3f}\n"
        remaining = max_chars - used - len(header) - 2
        if remaining <= 0:
            break
        text = compact_text(str(item.get("text") or ""), remaining)
        block = f"{header}{text}"
        parts.append(block)
        used += len(block) + 2
        sources.append(RagSource(file_id=file_id, name=name, chunk_index=chunk_index, score=score, metadata=metadata))
    return "\n\n".join(parts).strip(), sources


async def prepare_agent_material_context(
    *,
    files: Iterable[Dict[str, Any]],
    material_ids: Iterable[Any],
    query: str,
    role: str,
    max_chars: int | None = None,
) -> AgentMaterialContext:
    selected = _selected_file_list(files, material_ids)
    selected_ids = [str(item.get("id")) for item in selected if item.get("id")]
    if not selected_ids:
        return AgentMaterialContext(context="")

    budget = int(max_chars or config.rag_max_context_chars)
    diagnostics: List[RagDiagnostic] = []

    if not config.rag_enabled:
        raw = await build_selected_files_context(selected, selected_ids, max_chars=budget, snippet_chars=max(1000, budget // max(1, len(selected))))
        return AgentMaterialContext(context=raw, degraded=True, diagnostics=[RagDiagnostic(file_id="all", status="fallback", message="RAG disabled")])

    try:
        for meta in selected:
            status = await ensure_file_indexed(meta, role)
            diagnostics.append(RagDiagnostic(
                file_id=str(meta.get("id") or ""),
                status=str(status.get("status") or ""),
                message=str(status.get("error") or f"{status.get('chunkCount', 0)} chunks"),
            ))

        indexed_ids = [
            str(meta.get("id"))
            for meta in selected
            if any(diag.file_id == str(meta.get("id")) and diag.status == "indexed" for diag in diagnostics)
        ]
        if not indexed_ids:
            raise RuntimeError("No selected files indexed")

        results = await retrieve_from_files(query or "学习资料", indexed_ids, per_file_k=config.rag_per_file_k, top_k=config.rag_top_k)
        context, sources = _format_rag_context(results, budget)
        if context:
            return AgentMaterialContext(context=context, sources=sources, diagnostics=diagnostics, degraded=False)
        raise RuntimeError("RAG retrieval returned no text")
    except Exception as exc:
        raw = await build_selected_files_context(selected, selected_ids, max_chars=budget, snippet_chars=max(1000, budget // max(1, len(selected))))
        diagnostics.append(RagDiagnostic(file_id="all", status="fallback", message=str(exc)))
        return AgentMaterialContext(context=raw, diagnostics=diagnostics, degraded=True)
```

- [ ] **Step 3: Add RAG context tests with fakes**

Create `tests/backend/test_rag_context.py`:

```python
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from rag import context as context_module  # noqa: E402


def test_prepare_agent_material_context_falls_back_when_rag_errors(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        monkeypatch.setattr(config, "rag_enabled", True)

        async def fail_index(meta, role):
            raise RuntimeError("embedding provider unavailable")

        monkeypatch.setattr(context_module, "ensure_file_indexed", fail_index)

        upload = tmp_path / "uploads" / "a.txt"
        upload.parent.mkdir(parents=True, exist_ok=True)
        upload.write_text("raw", encoding="utf-8")
        Path(str(upload) + ".txt").write_text("fallback text", encoding="utf-8")

        result = await context_module.prepare_agent_material_context(
            files=[{"id": "a", "originalName": "a.txt", "objectKey": "uploads/a.txt"}],
            material_ids=["a"],
            query="question",
            role="student",
            max_chars=2000,
        )

        assert result.degraded is True
        assert "fallback text" in result.context
        assert any(diag.status == "fallback" for diag in result.diagnostics)

    asyncio.run(run())


def test_prepare_agent_material_context_returns_retrieved_chunks(monkeypatch):
    async def run():
        monkeypatch.setattr(config, "rag_enabled", True)

        async def ok_index(meta, role):
            return {"status": "indexed", "chunkCount": 1}

        async def fake_retrieve(query, file_ids, per_file_k=None, top_k=None):
            return [{
                "text": "retrieved from second file",
                "metadata": {"file_id": "b", "original_name": "b.txt", "chunk_index": 0},
                "score": 0.9,
            }]

        monkeypatch.setattr(context_module, "ensure_file_indexed", ok_index)
        monkeypatch.setattr(context_module, "retrieve_from_files", fake_retrieve)

        result = await context_module.prepare_agent_material_context(
            files=[{"id": "a", "originalName": "a.txt"}, {"id": "b", "originalName": "b.txt"}],
            material_ids=["a", "b"],
            query="question",
            role="student",
            max_chars=2000,
        )

        assert result.degraded is False
        assert "retrieved from second file" in result.context
        assert result.sources[0].file_id == "b"

    asyncio.run(run())
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/backend/test_rag_context.py -q
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/rag/retriever.py backend/rag/context.py tests/backend/test_rag_context.py
git commit -m "feat: assemble rag context before agent calls"
```

## Task 7: Integrate RAG Context Into Agent Routes

**Files:**
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/api/routes/quiz.py`
- Modify: `backend/api/routes/notes.py`
- Modify: `backend/api/routes/flashcards.py`
- Modify: `backend/api/routes/lesson_plan.py`
- Modify: `backend/api/routes/paper.py`
- Modify: `backend/api/routes/podcast.py`
- Modify: `backend/api/routes/slides.py`
- Modify: `backend/api/routes/teaching_video.py`
- Test: `tests/backend/test_rag_context.py`

- [ ] **Step 1: Import RAG context helper in all agent routes**

Add this import to each listed route:

```python
from rag.context import prepare_agent_material_context
```

- [ ] **Step 2: Replace selected-file builders with RAG calls**

Use this pattern wherever a route currently loads files and calls `build_selected_files_context()`:

```python
rag_context = await prepare_agent_material_context(
    files=files,
    material_ids=material_ids,
    query=topic_or_question,
    role=scope_or_role,
    max_chars=12000,
)
materials_text = rag_context.context
```

Apply exact query variables:

```python
# chat.py
query=history[-1].get("content", "")
role=chat_scope

# quiz.py
query=base_topic
role=quiz_scope

# notes.py
query=topic or data.get("notes") or "智能笔记"
role="student"

# flashcards.py
query=topic
role="student"

# lesson_plan.py
query=topic
role="teacher"

# paper.py
query=topic
role="teacher"

# podcast.py
query=topic or "基于学习资料的深度解读"
role="student"

# slides.py
query=topic
role="teacher"

# teaching_video.py
query=topic
role=scope
```

- [ ] **Step 3: Preserve existing prompt behavior**

Keep existing Chinese prompt wording, only replace `materials_text` source. Example for quiz remains:

```python
if materials_text:
    prompt_topic = (
        f"{base_topic}\n\n学习资料内容:\n{materials_text}\n\n"
        "请优先基于资料生成测验，若资料不足再补充常识。"
    )
```

- [ ] **Step 4: Store diagnostics where routes already persist material metadata**

For task records that already store `:materials`, add diagnostics without changing response contracts:

```python
await json_storage.set(
    f"quiz:{quiz_id}:materials",
    {
        "include": include_materials,
        "ids": material_ids,
        "ragDiagnostics": [diag.__dict__ for diag in rag_context.diagnostics],
        "ragSources": [source.__dict__ for source in rag_context.sources],
        "ragDegraded": rag_context.degraded,
    },
)
```

For routes where the metadata is written before generation starts, update inside the generation function after `prepare_agent_material_context()` returns.

- [ ] **Step 5: Run backend tests**

Run:

```powershell
pytest tests/backend/test_multi_file_context.py tests/backend/test_rag_context.py tests/backend/test_infrastructure_adapters.py -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

```powershell
git add backend/api/routes/chat.py backend/api/routes/quiz.py backend/api/routes/notes.py backend/api/routes/flashcards.py backend/api/routes/lesson_plan.py backend/api/routes/paper.py backend/api/routes/podcast.py backend/api/routes/slides.py backend/api/routes/teaching_video.py
git commit -m "feat: run rag retrieval before agent generation"
```

## Task 8: Surface File Index State And Selected Material Count In UI

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/FileLibrary.vue`
- Modify: `frontend/src/components/LearningFolderPanel.vue`
- Modify: `frontend/src/components/Chat/Composer.vue`
- Modify: `frontend/src/components/Quiz/TopicBar.vue`
- Modify: `frontend/src/components/Paper/PaperTopicBar.vue`
- Modify: `frontend/src/components/Slides/SlidesTopicBar.vue`
- Modify: `frontend/src/components/TeachingVideo/VideoTopicBar.vue`
- Modify: `frontend/src/components/Podcast/PodcastTopicBar.vue`
- Modify: `frontend/src/components/SmartNotes/NoteTopicBar.vue`
- Modify: `frontend/src/components/KnowledgeCards/KnowledgeCardsTopicBar.vue`
- Modify: `frontend/src/pages/Chat.vue`
- Modify: `frontend/src/pages/Quiz.vue`
- Modify: `frontend/src/pages/Paper.vue`
- Modify: `frontend/src/pages/Slides.vue`
- Modify: `frontend/src/pages/TeachingVideo.vue`
- Modify: `frontend/src/pages/Podcast.vue`
- Modify: `frontend/src/pages/SmartNotes.vue`
- Modify: `frontend/src/pages/KnowledgeCards.vue`
- Modify: `frontend/src/pages/LessonPlan.vue`

- [ ] **Step 1: Add API types**

In `frontend/src/lib/api.ts`, extend `LibraryFile`:

```ts
export type RagFileStatus = "pending" | "indexing" | "indexed" | "failed" | "unsupported";

export type RagStatusPayload = {
  fileId: string;
  status: RagFileStatus;
  chunkCount?: number;
  indexedAt?: string;
  error?: string;
};

export type LibraryFile = {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  uploadedAt: number;
  url: string;
  ragStatus?: RagStatusPayload;
};
```

Add calls:

```ts
export function getFileRagStatus(fileId: string, role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<{ ok: true; status: RagStatusPayload }>(`${env.backend}/files/${encodeURIComponent(fileId)}/rag-status${qs}`, { method: "GET" });
}

export function rebuildFileIndex(fileId: string, role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<{ ok: true; status: RagStatusPayload }>(`${env.backend}/files/${encodeURIComponent(fileId)}/index${qs}`, { method: "POST", timeout: Math.max(env.timeout, 300000) });
}
```

- [ ] **Step 2: Show indexing state in file library**

In `frontend/src/pages/FileLibrary.vue`, after list load, request statuses for visible files:

```ts
await Promise.all(files.value.map(async (file) => {
  try {
    const res = await getFileRagStatus(file.id, isTeacherPage.value ? "teacher" : "student");
    file.ragStatus = res.status;
  } catch {
    file.ragStatus = { fileId: file.id, status: "pending" };
  }
}));
```

Add a compact status label near file metadata:

```vue
<span class="text-[11px] text-[color:var(--nav-text-muted)]">
  {{ file.ragStatus?.status === "indexed" ? `已索引 ${file.ragStatus?.chunkCount || 0} 段` : file.ragStatus?.status === "indexing" ? "索引中" : file.ragStatus?.status === "failed" ? "索引失败" : file.ragStatus?.status === "unsupported" ? "暂不支持索引" : "待索引" }}
</span>
```

Add a rebuild button:

```vue
<button type="button" class="p-2 rounded-lg border border-[color:var(--nav-border)]" @click="rebuildIndex(file)">
  重建索引
</button>
```

with:

```ts
async function rebuildIndex(file: LibraryFile) {
  const res = await rebuildFileIndex(file.id, isTeacherPage.value ? "teacher" : "student");
  file.ragStatus = res.status;
}
```

- [ ] **Step 3: Show selected material count**

In `LearningFolderPanel.vue`, compute:

```ts
const selectedCount = computed(() => learningFolderFiles.value.length);
const selectedNames = computed(() => learningFolderFiles.value.map((file) => file.originalName || file.filename).slice(0, 3).join("、"));
```

Display in the panel header:

```vue
<div class="text-xs text-[color:var(--nav-text-muted)]">
  {{ selectedCount ? `已选择 ${selectedCount} 个资料${selectedNames ? `：${selectedNames}` : ""}` : folderEmptyHint }}
</div>
```

- [ ] **Step 4: Update topic bar labels without adding instructional text blocks**

For each topic bar listed above, replace binary labels such as `学习资料：是` with count-aware labels by accepting an optional `selectedMaterialCount` prop:

```ts
const props = withDefaults(defineProps<{ selectedMaterialCount?: number; includeMaterials?: boolean }>(), {
  selectedMaterialCount: 0,
  includeMaterials: false,
});

const materialStateLabel = computed(() => props.includeMaterials ? `资料 ${props.selectedMaterialCount}` : "资料 0");
```

Use it in the existing button text:

```vue
<span>{{ materialStateLabel }}</span>
```

- [ ] **Step 5: Pass selected counts from pages**

In each page that already defines `loadLearningFolderIds()`, add:

```ts
const selectedMaterialCount = computed(() => loadLearningFolderIds().length);
```

Pass it to the existing composer or topic bar:

```vue
<TopicBar
  :includeMaterials="includeMaterials"
  :selectedMaterialCount="selectedMaterialCount"
/>
```

For `LessonPlan.vue`, where the material toggle is inline instead of a dedicated topic bar, replace the status text with:

```vue
{{ includeMaterials ? `已关联 ${selectedMaterialCount} 个备课资料` : "未关联备课资料" }}
```

- [ ] **Step 6: Build frontend**

Run:

```powershell
npm run build
```

Expected: build succeeds.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/lib/api.ts frontend/src/pages/FileLibrary.vue frontend/src/components/LearningFolderPanel.vue frontend/src/components/Chat/Composer.vue frontend/src/components/Quiz/TopicBar.vue frontend/src/components/Paper/PaperTopicBar.vue frontend/src/components/Slides/SlidesTopicBar.vue frontend/src/components/TeachingVideo/VideoTopicBar.vue frontend/src/components/Podcast/PodcastTopicBar.vue frontend/src/components/SmartNotes/NoteTopicBar.vue frontend/src/components/KnowledgeCards/KnowledgeCardsTopicBar.vue frontend/src/pages/Chat.vue frontend/src/pages/Quiz.vue frontend/src/pages/Paper.vue frontend/src/pages/Slides.vue frontend/src/pages/TeachingVideo.vue frontend/src/pages/Podcast.vue frontend/src/pages/SmartNotes.vue frontend/src/pages/KnowledgeCards.vue frontend/src/pages/LessonPlan.vue
git commit -m "feat: show rag indexing and selected material state"
```

## Task 9: End-To-End And Performance Verification

**Files:**
- Create: `tests/backend/test_agent_material_integration.py`
- Modify: `README.md`
- Modify: `knowledge.md`

- [ ] **Step 1: Add route-level integration test for multi-file visibility**

Create `tests/backend/test_agent_material_integration.py`:

```python
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from rag.context import prepare_agent_material_context  # noqa: E402


def _file(tmp_path: Path, file_id: str, text: str) -> dict:
    path = tmp_path / "uploads" / f"{file_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "id": file_id,
        "originalName": f"{file_id}.txt",
        "objectKey": f"uploads/{file_id}.txt",
        "mimeType": "text/plain",
        "owner_id": 1,
    }


def test_prepare_agent_material_context_degrades_to_all_selected_files(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        monkeypatch.setattr(config, "object_store_provider", "local")
        monkeypatch.setattr(config, "rag_enabled", False)

        files = [
            _file(tmp_path, "alpha", "ALPHA content " * 100),
            _file(tmp_path, "beta", "BETA content " * 100),
        ]

        result = await prepare_agent_material_context(
            files=files,
            material_ids=["alpha", "beta"],
            query="生成测验",
            role="student",
            max_chars=2000,
        )

        assert result.degraded is True
        assert "ALPHA content" in result.context
        assert "BETA content" in result.context

    asyncio.run(run())
```

- [ ] **Step 2: Run unit and integration suite**

Run:

```powershell
pytest tests/backend/test_multi_file_context.py tests/backend/test_document_loader.py tests/backend/test_rag_chunking.py tests/backend/test_rag_indexer.py tests/backend/test_rag_context.py tests/backend/test_agent_material_integration.py tests/backend/test_infrastructure_adapters.py -q
```

Expected: all pass.

- [ ] **Step 3: Run Docker-backed smoke test**

Run infrastructure:

```powershell
docker compose up -d postgres redis minio
```

Run a pgvector smoke from the backend environment:

```powershell
@'
import asyncio
import sys

sys.path.insert(0, "backend")

from utils.storage import VectorStore


async def main():
    store = VectorStore("smoke-rag")
    await store._ensure_schema()
    print("pgvector schema ok")


asyncio.run(main())
'@ | python -
```

Expected: `pgvector schema ok`. This checks PostgreSQL connectivity and pgvector schema creation without requiring embedding credentials.

- [ ] **Step 4: Manual browser verification**

Use the local app:

1. Upload two large PDFs or `.txt` files into the student file library.
2. Add both to the learning folder.
3. Open chat, enable materials, ask a question requiring content from both files.
4. Confirm the backend generation prompt includes both file names in logs or diagnostics.
5. Repeat for quiz, smartnotes, paper and slides.

Expected: both selected file names appear in diagnostics; generated output references both when query requires both.

- [ ] **Step 5: Performance sanity check**

Prepare documents:

- 2 files, each about 5 pages.
- 5 files, each about 20 pages.
- 1 file with no extractable text, such as a scanned PDF.

Check:

- Upload returns quickly because indexing is queued.
- Agent call completes with RAG context or clear degraded fallback.
- Unsupported/scanned documents show `failed` or `unsupported` status instead of making the whole agent request fail.

- [ ] **Step 6: Commit**

```powershell
git add tests/backend/test_agent_material_integration.py
git commit -m "test: cover multi-file rag material integration"
```

## Task 10: Documentation

**Files:**
- Create: `docs/architecture/file-library-rag.md`
- Modify: `README.md`
- Modify: `knowledge.md`

- [ ] **Step 1: Create architecture document**

Create `docs/architecture/file-library-rag.md` with:

```markdown
# File Library RAG Architecture

EduMind 的文件库 RAG 分为上传元数据、对象文件、文档解析、分段索引、向量检索和 agent 上下文编排六层。

## Runtime Flow

1. `/files` 上传文件，ObjectStore 保存原始对象，KV 保存文件 metadata。
2. 上传成功后写入 `rag:file:{fileId}` 状态，并派发 `file-index` 任务。
3. indexer 读取 ObjectStore 文件，解析文本，按 `RAG_CHUNK_SIZE` 和 `RAG_CHUNK_OVERLAP` 分段。
4. 每个文件写入独立 pgvector namespace: `file:{fileId}`。
5. agent 执行前调用 `prepare_agent_material_context()`，确保所选文件已索引并按 query 检索相关片段。
6. 如果 pgvector、embedding provider 或解析失败，则降级到公平多文件原文片段。

## Supported Documents

- First-class: PDF with extractable text, DOCX, PPTX, XLSX, TXT, Markdown, CSV, JSON, HTML and common text encodings.
- Degraded or unsupported: scanned PDF without OCR, legacy `.doc/.ppt/.xls` unless converted before upload, image/audio/video files without OCR or transcription.

## API

- `GET /files?role=student|teacher`
- `POST /files`
- `DELETE /files/{file_id}`
- `GET /files/{file_id}/rag-status`
- `POST /files/{file_id}/index`

## Failure Policy

RAG failure must not block core generation. Agent routes fall back to fair multi-file snippets and record diagnostics.
```

- [ ] **Step 2: Update README**

Add a short section under storage/vector docs:

```markdown
### File Library RAG

Uploaded documents are stored through ObjectStore and indexed into pgvector per file namespace. Agent features call the RAG context builder before generation so multiple selected files can contribute context. If indexing or embeddings are unavailable, EduMind falls back to fair snippets from every selected file to preserve generation continuity.
```

- [ ] **Step 3: Update knowledge base**

Add to `knowledge.md`:

```markdown
## 文件库 RAG

- 上传支持多文件，metadata 存在用户维度的 files key 中，原始对象通过 ObjectStore 保存。
- RAG 状态 key 为 `rag:file:{fileId}`，向量 namespace 为 `file:{fileId}`。
- 所有 agent 材料入口应使用 `prepare_agent_material_context()`，不要在 route 内自行拼接全文。
- 当前不做 OCR；扫描 PDF 需要后续接入 OCR 后才能检索。
```

- [ ] **Step 4: Run docs-adjacent verification**

Run:

```powershell
rg -n "prepare_agent_material_context|build_selected_files_context|extract_file_text_from_meta" backend/api/routes backend/rag backend/utils
```

Expected:

- agent routes import `prepare_agent_material_context`.
- `extract_file_text_from_meta` remains only in parser/loading utilities or non-RAG direct upload flows.
- no route has a custom loop that appends selected file full text.

- [ ] **Step 5: Commit**

```powershell
git add docs/architecture/file-library-rag.md README.md knowledge.md
git commit -m "docs: document file library rag architecture"
```

## Acceptance Criteria

- 多文件上传后，agent 入口可以同时看到所有被选中的文件；在 RAG 关闭或失败时也不会回到“只看到第一个大文件”的行为。
- `quiz.py`、`notes.py` 等 route 不再维护自定义全文拼接逻辑。
- `Slides.vue` 勾选资料时会传递学习资料夹中的 `materialIds`。
- PDF、DOCX、PPTX、XLSX、TXT、Markdown、CSV、JSON、HTML 能解析可抽取文本；扫描 PDF 与旧二进制 Office 文件有明确失败状态。
- 每个上传文件有 RAG 状态，删除文件时删除对应向量 namespace 和 RAG 状态。
- agent 调用前执行 RAG 检索，并将片段整合到原有 prompt；检索失败时保留业务连续性。
- 单元测试、集成测试、前端构建通过。
- README、knowledge 和架构文档反映当前真实能力与限制。

## Self-Review

- Spec coverage: 多文件查看、文件库、向量数据库、预处理、嵌入、检索、整合、agent 前置调用、测试、文档都有对应任务。
- Realism check: 当前 pgvector 能力被复用但没有被描述成已经存在的完整 RAG；扫描 PDF、旧 Office 二进制和无 embedding 凭据的环境都有明确降级或失败策略。
- Type consistency: `AgentMaterialContext`、`RagSource`、`RagDiagnostic`、`prepare_agent_material_context()`、`ensure_file_indexed()` 在任务中先定义后使用。
- Continuity: Task 1 和 Task 2 可独立修复用户可见 bug；Task 3 到 Task 10 完成完整 RAG 文件库与 UI/文档闭环。
