# Multi-File RAG Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 agent 只处理单个 PDF 的材料链路，并实现可复用的多文件文档库与 RAG 前置检索流程。

**Architecture:** 文件上传仍由 `asset-library` 负责，上传元数据保留在现有 KV 存储中，对象内容保留在 ObjectStore。新增 `backend/services/document_library.py` 封装解析、分段、索引、检索和 agent 上下文格式化，业务路由只传用户、角色、材料 ID 和查询文本。

**Tech Stack:** FastAPI、现有 JSONStorage/KV adapter、ObjectStore、现有 pgvector `VectorStore`、PyMuPDF/python-docx/mammoth、pytest。

---

### Task 1: RAG Core Service

**Files:**
- Create: `backend/services/document_library.py`
- Modify: `backend/utils/feature_support.py`
- Test: `tests/backend/test_document_library.py`

- [x] 定义 `DocumentChunk`、`DocumentIndexResult`、`RagContext` 数据模型。
- [x] 实现文件文本提取、通用分段、每文件 sidecar 缓存和选中文件去重。
- [x] 实现按用户/角色/文件 ID 的 namespace，支持 pgvector 写入和检索。
- [x] 在向量服务不可用时提供确定性关键词回退检索，保证本地测试与无外部 embedding 环境可用。

### Task 2: Asset Library API Integration

**Files:**
- Modify: `backend/api/routes/files.py`
- Test: `tests/backend/test_document_library.py`

- [x] 上传多个文件后逐个触发文档索引，元数据记录 `ragStatus`、`ragIndexedAt`、`ragChunkCount`、`ragError`。
- [x] 删除文件时同步清理该文件的文档分块元数据和向量 namespace。
- [x] 新增文档库状态与检索端点，支持前端/调试查看多文件是否已进入 RAG。

### Task 3: Agent Pre-RAG Integration

**Files:**
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/api/routes/quiz.py`
- Modify: `backend/api/routes/paper.py`
- Modify: `backend/api/routes/lesson_plan.py`
- Modify: `backend/api/routes/notes.py`
- Modify: `backend/api/routes/slides.py`
- Modify: `backend/api/routes/podcast.py`
- Modify: `backend/api/routes/teaching_video.py`

- [x] 将重复的材料全文拼接替换成统一 `build_rag_context_for_user_files()`。
- [x] query 使用用户主题、问题或生成任务主题，RAG 在 agent 调用前执行。
- [x] 生成上下文包含多个来源文件名、chunk 序号和相关片段，避免只显示第一个文件。

### Task 4: Tests And Documentation

**Files:**
- Create: `docs/architecture/multi-file-rag-agent.md`
- Modify: `README.md`
- Modify: `knowledge.md`
- Test: `tests/backend/test_document_library.py`

- [x] 覆盖多文件分段、检索、上下文格式化、索引状态和兼容入口。
- [x] 记录数据库/向量命名空间、数据交互、API 和回退策略。
- [x] 运行目标后端测试并修复发现的问题。
