# EduMind 后端服务边界

本文记录 EduMind 当前后端运行拓扑和服务边界。项目源码仍采用 monorepo 管理，但默认运行形态已经是 Docker Compose 微服务拓扑：API Gateway、6 个后端边界服务、异步生成 worker、独立 Bilibili Bridge、PostgreSQL、Redis、MinIO 和前端 Nginx 分容器运行。前端原有 HTTP / WebSocket 路径通过 Gateway 保持兼容。

## 当前装配

后端镜像统一从 `deploy/docker/Dockerfile.backend` 构建，入口由 `scripts/start_backend_service.py` 根据 `BACKEND_ROLE` 决定：

| `BACKEND_ROLE` | 入口 | 用途 |
| --- | --- | --- |
| `gateway` | `backend/gateway_app.py` | 对外 API Gateway，端口 `5000`。 |
| `service` | `backend/service_app.py` | 按 `SERVICE_NAME` 启动单个服务边界。 |
| `worker` / `task-worker` | `backend/worker_app.py` | 消费 Redis 队列中的长耗时生成任务。 |
| `monolith` 或未设置 | `backend/main.py` | 本地单进程兼容模式，仅用于排障和旧数据迁移。 |

`backend/core/app_factory.py` 负责创建服务 app，统一配置中间件、生命周期、健康检查和路由挂载。`backend/core/service_registry.py` 记录服务边界和路由归属；`backend/core/gateway.py` 记录旧路径到目标服务的映射。

Docker Compose 默认启动以下后端角色：

- `api-gateway`
- `identity`
- `learning-content`
- `asset-library`
- `ai-core`
- `media-generation`
- `teaching-content`
- `generation-worker`
- `bilibili-bridge`

## 服务边界

| 服务 | 当前路由 | 职责 |
| --- | --- | --- |
| `identity` | `/auth/*` | 用户、会话、登录 token、注册、登录、修改密码、注销账户和内部 token 解析。 |
| `learning-content` | `/chat`、`/smartnotes`、`/quiz`、`/wrongbook`、`/flashcards`、`/api/companion/*`、`/exam`、`/debate`、`/tasks`、`/planner` | 学生侧和通用学习工作流，包括对话、笔记、测验、错题、学习记录、辩论和规划。 |
| `asset-library` | `/files`、`/transcriber`、`/storage` | 文件上传、素材元数据、对象文件访问、文件解析和转写入口。 |
| `ai-core` | `/ai/internal/invoke` | 内部 LLM / Embedding 调用，集中管理模型 provider、密钥和调用参数。 |
| `media-generation` | `/speaking`、`/podcast`、`/api/bilibili/search` | TTS、播客、英语口语评测、Bilibili 搜索代理和媒体类供应商调用。 |
| `teaching-content` | `/slides`、`/lesson-plan`、`/paper`、`/teaching-video` | 教案、幻灯片、试卷、教学视频和教师侧内容生成。 |

## Gateway 合同

Gateway 对外提供：

- `/health`：返回 Gateway 进程状态和上游服务 URL。
- `/health/live`：Gateway 存活检查。
- `/health/ready`：聚合检查各后端服务 `/health`，任一服务不可用时返回 `503`。

HTTP 和 WebSocket 代理都使用最长前缀匹配。浏览器仍访问旧路径，例如 `/chat`、`/quiz`、`/lesson-plan`、`/api/bilibili/search`、`/ws/paper`；Gateway 负责把请求转发到对应服务。这样前端合同稳定，后端可以继续按边界演进。

## 身份与内部调用

`identity` 服务持有账户和会话。当前账户库兼容使用 `storage/edumind.sqlite3`，便于保留已有本地用户数据；其他边界服务在 Compose 中运行 `AUTH_VALIDATION_MODE=remote`，通过 `IDENTITY_URL/auth/internal/resolve` 解析 Bearer token，不直接读取账户库。

`ai-core` 是模型调用边界。业务服务和 worker 默认运行：

```env
LLM_EXECUTION_MODE=remote
AI_CORE_URL=http://ai-core:5106
```

`ai-core` 自身运行 `LLM_EXECUTION_MODE=local`，由它直接读取 provider 配置并创建模型客户端。如果配置了 `INTERNAL_SERVICE_TOKEN`，内部接口会校验 `X-Internal-Service-Token`。

## 基础设施适配器

微服务化后，跨进程共享状态不再依赖单个 Python 进程内存或本地路径。项目抽出了以下适配器：

| 能力 | 配置项 | Docker 默认 | 本地兼容 |
| --- | --- | --- | --- |
| KV 状态 | `KV_STORE_PROVIDER` | `postgres`，使用 PostgreSQL JSONB | `json` |
| 对象文件 | `OBJECT_STORE_PROVIDER` | `s3`，由 MinIO 提供 S3 兼容存储 | `local` |
| 实时事件 | `EVENT_BUS_PROVIDER` | `redis` Pub/Sub | `memory` |
| 任务队列 | `TASK_QUEUE_PROVIDER` | `redis` list 队列 | `inline` |
| 任务租约 | `TASK_LEASE_PROVIDER` | `redis` | KV-backed lease |

关键实现：

- `backend/infrastructure/kv_store.py`：JSON、Redis、PostgreSQL KV provider。
- `backend/infrastructure/object_store.py`：本地文件与 S3/MinIO provider。
- `backend/infrastructure/event_bus.py`：内存事件与 Redis Pub/Sub。
- `backend/infrastructure/task_queue.py`：inline 与 Redis 队列。
- `backend/infrastructure/task_lease.py`：长任务租约，避免重复执行。
- `backend/utils/storage.py`：保留旧 JSONStorage API，底层改走 KV adapter。
- `backend/utils/live_events.py`：统一发布 WebSocket 进度事件。

## 长耗时任务

Chat、Smart Notes、Quiz、Exam、Paper、Podcast、Teaching Video 等生成流程已经改为 runner + queue 模式：

1. HTTP 创建任务并持久化初始状态。
2. `core.task_dispatcher` 写入 Redis 队列。
3. `generation-worker` 消费任务，获取租约，调用对应 runner。
4. runner 通过 `ai-core` 调模型，通过 ObjectStore 保存文件，通过 EventBus 发布进度。
5. WebSocket 只负责订阅和回放进度，不再承担任务执行本身。

Redis 队列使用 `{kind, id, attempts, max_attempts}` envelope。消费失败会按次数重试，超过上限后写入 dead-letter 队列。

## Bilibili Bridge

Bilibili MCP 是 Node/TypeScript 生态，当前独立为 `bilibili-bridge` 容器。`media-generation` 通过 `BILIBILI_BRIDGE_URL=http://bilibili-bridge:5001` 调用 Bridge；Bridge 再通过 stdio 连接 `/app/services/bilibili-mcp/dist/index.js`。

本地 `monolith` 调试模式仍可由 lifespan 启动本地 Bridge，但 Docker Compose 不使用这种路径。

## 数据迁移

旧本地 JSON / 文件数据可通过迁移脚本导入当前适配器：

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

默认 dry-run，只输出迁移报告；确认无误后再加 `--write`。目标 provider 由当前环境变量决定，例如 `KV_STORE_PROVIDER=postgres`、`OBJECT_STORE_PROVIDER=s3`。

## 当前边界状态

已完成：

- 服务化 app factory、service registry 和 Gateway 路由。
- Gateway readiness 聚合健康检查。
- 远程 token 解析和边界服务 remote auth。
- AI Core 内部调用边界。
- PostgreSQL KV、MinIO ObjectStore、Redis EventBus、Redis TaskQueue 和 Redis TaskLease。
- 长任务 worker、ack/retry/dead-letter 语义。
- 独立 Bilibili Bridge。
- dry-run-first 存储迁移工具。

仍需后续演进：

- `identity` 的账户/会话库仍兼容使用 SQLite；生产化可迁到独立 PostgreSQL schema。
- 代码仓库仍是 monorepo，部分 Agent、工具函数和适配器共享；如需团队级隔离，可继续拆 package 或独立仓库。
- 部分 PDF、PPTX、TTS、视频生成过程仍会使用本地临时文件；最终对象已通过 ObjectStore 暴露。
- 当前 Redis list 队列适合本项目规模；更大规模可替换为 Redis Streams、Celery、Dramatiq 或云队列。

## 验证

服务边界、Gateway 路由和基础设施合同由 `tests/backend/` 覆盖。常用检查：

```powershell
docker compose config --quiet
python -m compileall -q backend scripts tests
python -m pytest tests/backend -q
```

任何路由归属、Gateway 前缀或适配器合同变更，都应同步更新测试和本文档。
