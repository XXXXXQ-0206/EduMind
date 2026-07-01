# Celery + Redis 长任务机制说明

本文说明本次长任务机制改造中 Celery、Redis、WebSocket/SSE 的职责变化，以及相对于原有实现的优势。

## 改造背景

EduMind 中的对话、智能笔记、测验、播客、试卷、考试、教学视频等功能都可能运行较久。它们通常包含 LLM 调用、文件上下文读取、TTS、视频生成、PDF/音频产物落盘等步骤。如果这些任务直接在 HTTP 请求或 WebSocket 连接中执行，会带来几个问题：

- 请求生命周期太长，容易被网关、浏览器或代理断开。
- API 服务既负责接收请求，又负责执行重任务，扩容和故障隔离困难。
- 多进程/多服务部署时，任务进度事件需要跨进程传递。
- 自写队列和 worker 需要维护重试、确认、可观测性等通用能力。

因此本次将长任务执行层改为 Celery + Redis，并保留 WebSocket，同时新增 SSE 作为进度订阅方式。

## 改造前

改造前的任务机制主要由项目内自写组件组成：

| 层级 | 实现 |
| --- | --- |
| 任务派发 | `core/task_dispatcher.py` 根据 `TASK_QUEUE_PROVIDER` 判断 inline 或 Redis list queue |
| 队列 | `infrastructure/task_queue.py` 中的 `RedisTaskQueue`，基于 Redis list、processing list、dead-letter list |
| worker | `worker_app.py` 循环 `dequeue()`，查找 `register_task_handler()` 注册的 handler 并执行 |
| 进度事件 | `infrastructure/event_bus.py`，支持 memory 或 Redis Pub/Sub |
| 前端订阅 | 各业务 WebSocket，如 `/ws/quiz`、`/ws/podcast`、`/ws/teaching-video` |

典型流程如下：

```text
HTTP 创建任务
  -> 写入任务元数据
  -> dispatch_generation_task(kind, id)
  -> inline 执行或写入自写 Redis 队列
  -> worker_app 轮询队列并执行 handler
  -> handler 通过 Redis Pub/Sub 发布进度
  -> WebSocket 转发进度给前端
```

这套方案已经能支持跨进程进度推送，但队列和 worker 仍然是项目自维护的，重试、确认、并发控制、worker 生命周期管理都比较基础。

## 改造后

改造后，任务执行层切换为 Celery，Redis 同时承担 broker、result backend、事件总线和任务租约的基础设施角色。

| 层级 | 实现 |
| --- | --- |
| 任务派发 | `core/task_dispatcher.py` 支持 `TASK_QUEUE_PROVIDER=celery` |
| Celery app | `core/celery_app.py` 配置 broker、backend、队列名、ack、prefetch、visibility timeout |
| Celery task | `core/celery_tasks.py` 定义统一任务 `edumind.generation.run(kind, task_id)` |
| worker 启动 | `scripts/start_backend_service.py` 在 `BACKEND_ROLE=worker` 且 `TASK_QUEUE_PROVIDER=celery` 时启动 Celery worker |
| 进度事件 | 继续使用 `RedisEventBus` / Redis Pub/Sub |
| 前端订阅 | WebSocket 保持兼容，新增通用 SSE：`/tasks/{kind}/{task_id}/events` |

新的典型流程如下：

```text
HTTP 创建任务
  -> 写入任务元数据
  -> dispatch_generation_task(kind, id)
  -> Celery send_task("edumind.generation.run", kind, id)
  -> Redis broker 持久化待执行任务
  -> Celery worker 获取任务并执行已注册 handler
  -> handler 通过 Redis Pub/Sub 发布进度
  -> WebSocket 或 SSE 转发进度给前端
```

## 核心变化

### 1. 任务执行从自写 worker 切换到 Celery

原来：

```text
API/service -> RedisTaskQueue -> worker_app.py -> handler
```

现在：

```text
API/service -> Celery broker Redis -> Celery worker -> handler
```

业务 handler 没有被重写。现有 `register_task_handler("quiz", run_quiz_generation_worker)` 这类注册方式仍然保留，Celery worker 只负责根据 `kind` 和 `task_id` 调用已经注册的 handler。

### 2. 任务派发接口保持兼容

业务路由仍然调用：

```python
await dispatch_generation_task("quiz", quiz_id, ensure_quiz_generation_task)
```

区别在于：

- `TASK_QUEUE_PROVIDER=inline`：本地直接启动，用于开发或简单运行。
- `TASK_QUEUE_PROVIDER=redis`：保留旧 Redis list 队列能力，方便回滚。
- `TASK_QUEUE_PROVIDER=celery`：发布 Celery 任务，推荐部署模式。

### 3. 进度事件继续走 Redis Pub/Sub

Celery 只负责“任务什么时候、由哪个 worker 执行”。任务过程中的阶段事件、结果事件、错误事件仍由业务代码通过 `publish_live_event()` 发布。

这样可以保持现有 WebSocket 行为不变：

```text
/ws/chat
/ws/quiz
/ws/smartnotes
/ws/podcast
/ws/paper
/ws/exams
/ws/teaching-video
```

### 4. 新增 SSE 进度接口

新增通用接口：

```text
GET /tasks/{kind}/{task_id}/events
```

支持的 kind 包括：

```text
chat
quiz
smartnotes
podcast
paper
exam
teaching-video
```

SSE 接口会：

- 通过 `Authorization: Bearer <token>` 或 `?token=<token>` 鉴权。
- 校验任务元数据是否属于当前用户。
- 订阅对应 Redis Pub/Sub channel。
- 输出 `text/event-stream` 格式事件。

前端也新增了通用 helper：

```ts
connectTaskEvents(kind, taskId, onEvent)
```

这意味着前端可以继续用 WebSocket，也可以在只需要服务端单向推送时使用 SSE。

## 优势

### 1. 更成熟的任务调度模型

Celery 天然提供任务确认、worker 并发、失败重试、prefetch 控制、broker 断线重连等能力。相比自写 Redis list worker，后续维护成本更低。

### 2. API 服务和任务执行解耦

API 服务只负责创建任务和返回任务 ID，不再承担重任务执行压力。Celery worker 可以独立扩容，例如视频生成较慢时，只扩容 worker，不需要扩容所有 API 服务。

### 3. 更适合微服务部署

当前 Docker Compose 中 `learning-content`、`media-generation`、`teaching-content` 都会把长任务发到同一个 Celery 队列，由独立 `generation-worker` 执行。服务边界更清晰：

```text
业务服务：接收请求、写元数据、发布 Celery 任务
worker：执行耗时生成逻辑
Redis：任务 broker、结果 backend、事件 pub/sub、任务租约
```

### 4. WebSocket 兼容，SSE 更轻量

WebSocket 保留，旧前端不需要立刻迁移。SSE 新增后，有些只需要单向进度推送的场景可以使用更简单的浏览器原生 `EventSource`。

对比：

| 方式 | 适合场景 |
| --- | --- |
| WebSocket | 双向通信、已有页面、需要客户端持续发送消息 |
| SSE | 服务端单向推送进度、浏览器原生自动重连、实现更轻 |

### 5. 回滚路径清晰

`TASK_QUEUE_PROVIDER` 仍然支持：

- `inline`
- `redis`
- `celery`

如果 Celery 部署出现问题，可以临时改回 `redis` 或 `inline` 验证业务逻辑，降低上线风险。

## 关键配置

`.env.example` 新增或强调以下配置：

```env
REDIS_URL=redis://redis:6379/0
EVENT_BUS_PROVIDER=redis
TASK_LEASE_PROVIDER=redis
TASK_QUEUE_PROVIDER=celery

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TASK_QUEUE_NAME=edumind:generation
CELERY_VISIBILITY_TIMEOUT_SECONDS=3600
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_RETRY_DELAY_SECONDS=10
CELERY_WORKER_CONCURRENCY=2
CELERY_WORKER_POOL=prefork
```

其中：

| 配置 | 作用 |
| --- | --- |
| `TASK_QUEUE_PROVIDER` | 控制任务派发模式，生产推荐 `celery` |
| `CELERY_BROKER_URL` | Celery broker，当前使用 Redis |
| `CELERY_RESULT_BACKEND` | Celery 结果后端，当前使用 Redis |
| `CELERY_TASK_QUEUE_NAME` | Celery 队列名 |
| `CELERY_VISIBILITY_TIMEOUT_SECONDS` | Redis broker 中任务可见性超时时间 |
| `CELERY_TASK_MAX_RETRIES` | Celery 任务失败最大重试次数 |
| `CELERY_WORKER_CONCURRENCY` | worker 并发数 |
| `EVENT_BUS_PROVIDER` | 进度事件总线，跨进程部署应使用 `redis` |
| `TASK_LEASE_PROVIDER` | 防重复执行租约，跨进程部署应使用 `redis` |

## Docker Compose 变化

生产式 compose 中，以下服务默认使用 Celery：

```text
learning-content
media-generation
teaching-content
generation-worker
```

其中业务服务负责发任务：

```env
TASK_QUEUE_PROVIDER=celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_TASK_QUEUE_NAME=edumind:generation
```

`generation-worker` 在启动时会检测：

```text
BACKEND_ROLE=worker
TASK_QUEUE_PROVIDER=celery
```

然后启动 Celery worker，而不是旧的 `worker_app.py` 轮询循环。

## 新返回字段

创建长任务的接口仍然返回原有 WebSocket 地址：

```json
{
  "ok": true,
  "quizId": "...",
  "stream": "/ws/quiz?quizId=..."
}
```

现在额外返回 SSE 地址：

```json
{
  "ok": true,
  "quizId": "...",
  "stream": "/ws/quiz?quizId=...",
  "events": "/tasks/quiz/.../events"
}
```

这个字段是向后兼容新增字段，旧前端可以忽略，新前端可以按需选择 SSE。

## 运行与检查

常规 Docker Compose 启动：

```powershell
docker compose up --build
```

检查 worker 是否启动为 Celery：

```powershell
docker compose logs generation-worker
```

正常情况下可以看到 Celery worker 日志，并监听 `edumind:generation` 队列。

检查 Redis：

```powershell
docker compose exec redis redis-cli ping
```

检查 API 创建任务后，业务服务应快速返回 `202`，实际生成由 `generation-worker` 异步完成。

## 排障建议

| 现象 | 可能原因 | 检查点 |
| --- | --- | --- |
| 任务一直 pending | worker 未启动或未连上 Redis | `docker compose logs generation-worker` |
| 前端收不到进度 | `EVENT_BUS_PROVIDER` 不是 `redis` 或 Redis Pub/Sub 不通 | 业务服务和 worker 的 `REDIS_URL` 是否一致 |
| 重复执行任务 | Redis lease 未生效 | `TASK_LEASE_PROVIDER=redis` |
| SSE 返回 401 | 未携带 token | `Authorization` header 或 `?token=` |
| SSE 返回 404 | 任务不存在或不属于当前用户 | 任务元数据 owner 字段 |
| Celery 重试后仍失败 | 业务 handler 内部异常 | worker 日志中的任务异常栈 |

## 总结

这次改造的重点不是重写业务生成逻辑，而是把“长任务怎么排队、怎么执行、怎么扩容、怎么失败重试”交给 Celery 和 Redis。业务层仍然通过统一的 `dispatch_generation_task(kind, task_id, inline_starter)` 发任务，通过 `publish_live_event()` 发进度。前端 WebSocket 不破坏，SSE 新增为更轻量的进度订阅通道。

最终收益是：

- 长任务执行与 API 请求解耦。
- worker 可以独立扩容和重启。
- 任务调度能力更成熟。
- 进度推送同时支持 WebSocket 和 SSE。
- 保留 inline/legacy redis 回滚路径。
