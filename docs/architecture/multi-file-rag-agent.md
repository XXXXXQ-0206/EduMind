# Multi-File RAG Agent Architecture

EduMind 的文件库与 agent 调用链路已经统一为“多文件文档库 + RAG 前置检索”模式。文件上传仍由 `asset-library` 服务负责，业务生成仍由各功能服务和 worker 执行；两者之间通过文档索引状态、向量命名空间和统一上下文构造器交互。

## 数据流

1. 用户在文件库上传一个或多个文件。
2. `/files` 保存对象文件到 ObjectStore，并把文件元数据写入 KV 存储。
3. `backend/services/document_library.py` 对每个文件执行文本提取、分段和索引。
4. 文档分块元数据写入 KV：`rag:file:{file_id}:chunks`、`rag:file:{file_id}:status`。
5. 向量写入 pgvector：namespace 为 `rag_{sha1(owner_id:role:file_id)}`。
6. chat、quiz、paper、lesson-plan、smartnotes、podcast、slides、teaching-video、flashcards 在调用 agent 前，使用用户问题或任务主题检索选中文件。
7. RAG 上下文按多个文件汇总为带来源文件名和分块编号的片段，再传给具体 agent。

## 存储模型

| 数据 | 位置 | 说明 |
| --- | --- | --- |
| 上传对象 | MinIO/S3 或本地 ObjectStore | `uploads/{stored_name}` |
| 文件元数据 | KV adapter | `files:user:{id}`、`files_teacher:user:{id}` |
| 分块元数据 | KV adapter | `rag:file:{file_id}:chunks` |
| 索引状态 | KV adapter | `rag:file:{file_id}:status` |
| 向量索引 | PostgreSQL pgvector | `PGVECTOR_TABLE`，按 namespace 隔离 |

## API

- `GET /files?role=student|teacher`：返回文件列表，并附带 `ragStatus`、`ragChunkCount`、`ragVectorStatus` 等索引状态。
- `POST /files`：支持一次上传多个文件，并逐个触发文档索引。
- `POST /files/{file_id}/rag/index`：手动重建指定文件索引。
- `GET /files/{file_id}/rag`：查看指定文件索引状态。
- `POST /files/rag/search`：在当前用户文件库内按 `query` 和 `materialIds` 检索片段。

## 回退策略

pgvector 或 embedding provider 暂不可用时，系统不会阻断业务生成。文档分块仍写入 KV，检索阶段自动回退到关键词相关度排序，并保持每个选中文件至少有一个片段进入候选集合，避免大文件把其他文件挤出上下文。

## Agent 接入点

统一入口为 `utils.feature_support.build_selected_files_context()`，内部优先调用 `services.document_library.build_rag_context_for_user_files()`。各业务路由传入：

- `files`：当前用户和角色下的文件库元数据；
- `materialIds`：前端学习/教学文件夹选中的多个文件 ID；
- `owner_id`、`role`：用于命名空间隔离；
- `query`：用户问题或生成主题。

该设计让 agent 不再直接关心 PDF/DOCX/TXT 等解析细节，也不会因为只读取第一个文件或顺序截断而丢失后续资料。
