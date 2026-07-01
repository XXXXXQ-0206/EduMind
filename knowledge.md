# EduMind 技术文档

本文面向项目讲解、面试答辩和二次开发，说明 EduMind 当前微服务架构、核心模块、数据流和关键实现。当前版本已按服务边界拆分运行时、接入 Docker Compose 编排，并把共享状态、对象文件、事件和任务队列收敛到基础设施适配器。

## 一、项目定位

EduMind 是一个师生协同的 AI 教育平台，围绕“备课、授课、学习、练习、复盘”组织功能：

- 教师端：对话、文件库、Bilibili 视频备课、教案、教学幻灯片、教学视频、测验、试卷、教学记录汇。
- 学生端：对话、文件库、智能笔记、测验、播客、知识卡片、错题本、学习记录汇、英语口语、学习袋、B 站视频学习。
- 账户体系：统一登录注册，学生端和教师端共用身份体系，但业务历史按用户隔离。
- AI 能力：LLM、Embedding、TTS、图像生成、文生视频、语音评测、文档解析和 Bilibili MCP 检索。

## 二、当前架构

### 2.1 总体形态

当前默认运行形态是 Docker Compose 编排的微服务拓扑。API Gateway 对外暴露端口 `5000`，再按路径把请求分发到各服务：

```text
Browser
  -> frontend(Nginx)
  -> api-gateway(:5000)
      -> identity(:5101)
      -> learning-content(:5102)
      -> asset-library(:5103)
      -> media-generation(:5104)
      -> teaching-content(:5105)
      -> ai-core(:5106)

Long-running tasks
  -> Redis queue
  -> generation-worker

Media search
  -> media-generation
  -> bilibili-bridge(:5001)
  -> services/bilibili-mcp

Shared infrastructure
  -> PostgreSQL / Redis / MinIO
```

源码仍采用 monorepo 管理，`backend/` 内保留共享 Agent、工具函数和适配器；运行时已经按服务边界多容器启动。前端仍调用原有路径，例如 `/chat`、`/quiz`、`/lesson-plan`、`/api/bilibili/search`。API Gateway 负责保持路径兼容，并把请求代理到对应服务，避免前端随着服务拆分频繁改接口。

### 2.2 服务职责

| 服务 | 职责 |
|------|------|
| `api-gateway` | 对外入口；代理 HTTP / WebSocket；提供 `/health`、`/health/live`、`/health/ready`。 |
| `identity` | 用户注册、登录、会话、token 解析、修改密码、注销账户。 |
| `learning-content` | 学习侧和通用内容：对话、智能笔记、测验、知识卡片、错题本、辩论、规划、学习记录。 |
| `asset-library` | 文件上传、素材元数据、对象文件、解析和转写入口。 |
| `ai-core` | 统一模型调用入口，集中管理 LLM / Embedding provider 和内部鉴权。 |
| `media-generation` | 播客、TTS、英语口语评测、Bilibili 搜索代理和媒体能力。 |
| `teaching-content` | 教案、幻灯片、试卷、教学视频和教师内容生成。 |
| `generation-worker` | 消费 Redis 任务队列，执行长耗时生成任务，支持 ack、retry、dead-letter。 |
| `bilibili-bridge` | Node 服务，通过 MCP stdio 连接 `services/bilibili-mcp` 并提供 HTTP 检索接口。 |

### 2.3 运行模式

后端镜像统一通过 `scripts/start_backend_service.py` 启动，靠环境变量决定角色：

| `BACKEND_ROLE` | 入口 | 说明 |
|----------------|------|------|
| `gateway` | `backend/gateway_app.py` | API Gateway，对外端口 5000。 |
| `service` | `backend/service_app.py` | 按 `SERVICE_NAME` 启动一个服务边界。 |
| `worker` / `task-worker` | `backend/worker_app.py` | 消费异步任务队列。 |
| `monolith` 或未设置 | `backend/main.py` | 本地单进程兼容模式，便于排障，不是推荐部署形态。 |

微服务部署使用 `gateway`、`service` 和 `worker` 三类角色；`monolith` 只保留给本地排障和兼容旧数据迁移，不作为日常启动方式。

## 三、基础设施适配器

微服务化后，不能再让多个进程直接依赖同一份进程内状态。因此项目抽出了几类适配器：

| 适配器 | 配置项 | Docker 默认 | 本地兼容 |
|--------|--------|-------------|----------|
| KV 状态 | `KV_STORE_PROVIDER` | `postgres` | `json` |
| 对象文件 | `OBJECT_STORE_PROVIDER` | `s3` / MinIO | `local` |
| 实时事件 | `EVENT_BUS_PROVIDER` | `redis` | `memory` |
| 任务队列 | `TASK_QUEUE_PROVIDER` | `redis` | `inline` |
| 任务租约 | `TASK_LEASE_PROVIDER` | `redis` | KV-backed lease |

关键代码：

- `backend/infrastructure/kv_store.py`：JSON 文件、PostgreSQL JSONB KV。
- `backend/infrastructure/object_store.py`：本地文件和 S3/MinIO 对象存储。
- `backend/infrastructure/event_bus.py`：内存事件和 Redis Pub/Sub。
- `backend/infrastructure/task_queue.py`：inline 队列和 Redis 队列。
- `backend/infrastructure/task_lease.py`：避免同一生成任务被重复执行。
- `backend/utils/storage.py`：保留原有业务存储 API，底层改走 KV adapter。
- `backend/utils/live_events.py`：统一发布 WebSocket 进度事件。

## 四、请求与数据流

### 4.1 普通 HTTP 请求

1. 浏览器调用 `http://localhost:5000/<legacy-path>`。
2. `api-gateway` 根据 `backend/core/gateway.py` 的路由表找到目标服务。
3. 目标服务通过 `identity` 解析 token，或在本地 identity 服务中直接查会话。
4. 业务服务读写 PostgreSQL KV、MinIO 对象或 Redis 事件。
5. 响应返回给 Gateway，再返回前端。

账户和会话由 `identity` 服务持有。当前 identity 仍兼容使用 `storage/edumind.sqlite3` 保存账户数据，其他服务在 Compose 中通过 `AUTH_VALIDATION_MODE=remote` 调 `/auth/internal/resolve`，不直接读取账户库。

### 4.2 长耗时生成任务

以试卷、播客、教学视频、智能笔记等为例：

1. 前端通过 HTTP 创建任务。
2. 业务服务持久化任务请求和初始状态。
3. `core.task_dispatcher` 将任务放入 Redis 队列，或在本地模式 inline 执行。
4. `generation-worker` 消费任务，拿任务租约，调用业务 runner。
5. runner 通过 `ai-core` 调 LLM，通过 ObjectStore 写文件，通过 EventBus 发进度。
6. 前端 WebSocket 订阅任务进度；断线重连时可读取已缓存状态。

### 4.3 AI 调用

业务服务和 worker 默认设置：

```env
LLM_EXECUTION_MODE=remote
AI_CORE_URL=http://ai-core:5106
```

它们不会直接持有模型 provider 调用逻辑，而是请求 `ai-core` 的内部接口。`ai-core` 使用 `backend/api/routes/ai_core.py` 和 `backend/utils/llm.py` 统一创建模型客户端。这样可以把模型密钥、provider 选择和调用日志集中到一个服务边界。

## 五、目录与关键文件

### 5.1 根目录

| 路径 | 作用 |
|------|------|
| `docker-compose.yml` | 当前微服务拓扑。 |
| `setup-edumind-environment.ps1` | 新机器环境配置：Git、Docker、`.env`、Compose 校验、镜像构建。 |
| `start-edumind.ps1` | 快速启动 Docker Compose 微服务。 |
| `.env.example` | 环境变量模板，`.env` 不提交 Git。 |
| `.githooks/` | 提交质量检查：pre-commit、commit-msg、pre-push。 |
| `.github/workflows/ci.yml` | GitHub Actions 后端/前端 CI。 |
| `docs/` | 架构、部署、协作文档。 |
| `tests/backend/` | 服务边界、网关、基础设施适配器测试。 |

### 5.2 后端

| 路径 | 作用 |
|------|------|
| `backend/core/app_factory.py` | 创建单进程或服务模式 FastAPI app。 |
| `backend/core/service_registry.py` | 记录服务边界和路由归属。 |
| `backend/core/gateway.py` | Gateway 路由解析、代理、健康检查。 |
| `backend/core/task_dispatcher.py` | 任务 handler 注册、入队和 worker 分发。 |
| `backend/gateway_app.py` | Gateway 入口。 |
| `backend/service_app.py` | 单服务入口，读取 `SERVICE_NAME`。 |
| `backend/worker_app.py` | worker 入口，导入 route modules 注册任务 handler。 |
| `backend/api/routes/auth.py` | identity 边界，负责账户和会话。 |
| `backend/api/routes/ai_core.py` | AI Core 内部模型调用接口。 |
| `backend/api/routes/chat.py`、`notes.py`、`quiz.py` | learning-content 主要学习工作流。 |
| `backend/api/routes/files.py`、`transcriber.py` | asset-library 文件和转写能力。 |
| `backend/api/routes/podcast.py`、`speaking.py`、`bilibili.py` | media-generation 能力。 |
| `backend/api/routes/lesson_plan.py`、`slides.py`、`paper.py`、`teaching_video.py` | teaching-content 能力。 |
| `backend/agents/` | LLM Agent，负责 prompt、结构化输出和业务生成。 |
| `backend/utils/` | auth、storage、llm、tts、parser、对象文件、实时事件等公共能力。 |

### 5.3 前端

| 路径 | 作用 |
|------|------|
| `frontend/src/router/index.ts` | 学生/教师路由、登录拦截、角色入口。 |
| `frontend/src/lib/api.ts` | 前端 API 封装和 TypeScript 类型。 |
| `frontend/src/stores/auth.ts` | 登录态、当前用户、token 持久化。 |
| `frontend/src/stores/role.ts` | 教师/学生角色状态。 |
| `frontend/src/pages/EduMindHome.vue` | 首页和 GitHub 展示入口。 |
| `frontend/src/pages/Chat.vue` | 教师/学生对话共用页面。 |
| `frontend/src/pages/FileLibrary.vue` | 文件库共用页面。 |
| `frontend/src/pages/Quiz.vue` | 教师出题和学生作答共用页面。 |
| `frontend/src/pages/Paper.vue` | 教师试卷生成页面。 |
| `frontend/src/views/BiliLearning.vue`、`BiliLessonPrep.vue` | 学生 B 站学习和教师视频备课。 |

## 六、核心功能实现

### 6.1 账户与数据隔离

- 入口：`frontend/src/pages/AuthPortal.vue`。
- 后端：`backend/api/routes/auth.py`、`backend/utils/auth.py`、`backend/utils/auth_db.py`。
- identity 服务在本地模式使用 SQLite 兼容旧账户数据；边界服务通过 `AUTH_VALIDATION_MODE=remote` 调 `/auth/internal/resolve`。
- 业务数据按用户、scope、role 或 owner 字段隔离。新注册账户不会继承默认演示数据。

### 6.2 文件库与资料上下文

- 文件上传进入 `asset-library`。
- 元数据走 KV Store，文件字节走 ObjectStore。
- 业务模块不再拼接 `storage/uploads` 本地路径，而是通过 object key 和 helper 取文本、取缓存路径或生成 URL。
- 对话、教案、测验、笔记、试卷等都可以复用选中文件作为上下文。

### 6.3 对话、笔记、测验和错题本

- 学习内容归 `learning-content`。
- Chat、Smart Notes、Quiz 等长流程使用 HTTP 创建任务 + WebSocket 订阅进度。
- Quiz attempts 记录答题结果，错题本从 attempts 中汇总错误、薄弱点和报告。
- WebSocket 进度通过 EventBus 发布，避免依赖某一个业务进程内的连接表。

### 6.4 教案、幻灯片、试卷和教学视频

- 教师内容归 `teaching-content`。
- 教案和试卷使用结构化 Agent 输出，再由 reportlab 导出 PDF。
- 幻灯片使用 LLM 生成大纲，可调用即梦生成无字配图。
- 教学视频链路：主题/资料 -> LLM 脚本 -> 即梦文生视频 -> TTS 配音 -> FFmpeg 合成 -> ObjectStore 保存 -> WebSocket 推进度。

### 6.5 播客、口语和 Bilibili

- 媒体工作流归 `media-generation`。
- 播客使用 PodcastAgent 生成对话脚本，TTS 分段合成音频。
- 英语口语可调用讯飞 ISE 评测。
- Bilibili 搜索由 `media-generation` 代理到独立 `bilibili-bridge`，后者通过 MCP stdio 调 `services/bilibili-mcp/dist/index.js`。

## 七、部署与启动

推荐流程：

```powershell
.\setup-edumind-environment.ps1
.\start-edumind.ps1
```

访问：

- 前端：`http://localhost`
- API Gateway：`http://localhost:5000`
- Readiness：`http://localhost:5000/health/ready`
- MinIO：`http://localhost:9001`

常用验证：

```powershell
docker compose config --quiet
docker compose ps
Invoke-WebRequest -UseBasicParsing http://localhost:5000/health/ready
python -m compileall -q backend scripts tests
python -m pytest tests/backend -q
```

## 八、迁移与兼容

当前版本保留了三层兼容：

1. 前端 API 路径兼容：Gateway 继续暴露旧路径。
2. 本地单进程兼容：`BACKEND_ROLE=monolith` 可用于排障和旧数据迁移，不是推荐启动方式。
3. 旧数据兼容：`scripts/migrate_storage_to_adapters.py` 支持把 `storage/` 里的 JSON 和对象文件迁入 PostgreSQL / MinIO。

迁移数据时先 dry-run：

```powershell
python scripts/migrate_storage_to_adapters.py --source-dir storage
python scripts/migrate_storage_to_adapters.py --source-dir storage --write
```

## 九、面试常见追问

1. **为什么要加 API Gateway？**
   前端已有大量稳定路径。Gateway 把旧路径映射到新服务，既能拆服务，又不破坏前端合同，还能统一健康检查和跨服务代理。

2. **微服务拆分后如何处理登录态？**
   identity 服务持有账户和会话。其他服务运行在 `AUTH_VALIDATION_MODE=remote`，通过 `/auth/internal/resolve` 解析 token，避免每个服务直接读账户库。

3. **长耗时任务为什么不用 WebSocket 直接跑到底？**
   教学视频、播客、试卷等任务耗时长，进程重启或连接断开会丢状态。现在 HTTP 创建任务，worker 执行，WebSocket 只订阅进度，状态可持久化、可重放。

4. **为什么要抽 KV/ObjectStore/EventBus/TaskQueue 适配器？**
   微服务不能依赖进程内变量和本地文件路径。适配器让本地开发保留 JSON/文件系统，又能在 Docker 中切到 PostgreSQL、Redis、MinIO。

5. **AI Core 的价值是什么？**
   模型 provider、密钥、调用参数和内部鉴权集中在一个边界。业务服务只表达“要生成什么”，不直接耦合具体模型 SDK。

6. **Bilibili MCP 为什么单独成 Node 服务？**
   MCP 服务是 Node/TypeScript 生态，Python 后端通过独立 Bridge 调它，比在每个服务里拉子进程更清晰，也便于健康检查和独立重启。

7. **如何保证服务拆分没有破坏旧功能？**
   `tests/backend/test_app_factory.py` 检查服务边界、公共路由和 Gateway 路由；`test_infrastructure_adapters.py` 检查 KV、ObjectStore、EventBus、Queue、迁移脚本等基础设施合同。

8. **现在还算完全独立微服务吗？**
   运行上已经是多容器、多服务边界；代码仓库仍是 monorepo，部分工具函数和 Agent 仍共享。下一步可以按服务边界继续拆包、独立数据库 schema 和独立 CI/CD。

9. **如何迁移到另一台机器？**
   克隆仓库，运行 `setup-edumind-environment.ps1`，补 `.env` 密钥，再运行 `start-edumind.ps1`。Docker 镜像里包含 Python/Node 依赖，PostgreSQL/Redis/MinIO 由 Compose 拉起。

10. **`.env`、`storage/` 为什么不提交？**
    `.env` 有密钥，`storage/` 是运行数据和用户生成内容。协作只提交源码、配置模板和迁移脚本；运行数据靠数据库、对象存储或备份迁移。

## 十、后续演进方向

- 为各服务拆独立 Python package 或独立仓库。
- 为 identity、learning、teaching、media 建更明确的数据库 schema。
- 用 Redis Streams、Celery、Dramatiq 或云队列替换当前 Redis list 队列。
- 给 Gateway 增加更完整的鉴权、限流、请求追踪和结构化日志。
- 将 GitHub Actions 拆成后端、前端、Docker 镜像构建和部署流水线。
