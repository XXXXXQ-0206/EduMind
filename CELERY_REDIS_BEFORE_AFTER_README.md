# Celery + Redis 改造前后对比

这份文档聚焦本次 Celery、Redis 长任务机制调整的前后变化和收益。完整机制说明可继续参考 `CELERY_REDIS_TASKS_README.md`。

## 改造目标

EduMind 的测验、智能笔记、播客、试卷、考试、教学视频等功能都可能涉及 LLM 调用、文件解析、TTS、视频生成和产物保存。它们不适合长期占用 HTTP 请求或 WebSocket 连接。

本次改造的目标是把“任务排队、任务执行、失败重试、worker 扩容”交给 Celery + Redis，让业务服务只负责创建任务、保存元数据和发布进度。

## 改造前

改造前的长任务主要依赖项目内自写队列和 worker：

```text
HTTP / WebSocket 请求
  -> 业务路由创建任务
  -> dispatch_generation_task()
  -> inline 执行或 Redis list 队列
  -> worker_app.py 轮询任务
  -> 调用注册的业务 handler
  -> Redis Pub/Sub 推送进度
  -> WebSocket 返回前端
```

| 能力 | 改造前 |
| --- | --- |
| 任务队列 | 自写 `RedisTaskQueue`，基于 Redis list |
| worker | `worker_app.py` 手写轮询循环 |
| 失败处理 | 基础 ack / fail / dead-letter |
| 并发控制 | 主要依赖进程和自写循环 |
| 进度推送 | Redis Pub/Sub 或内存事件 |
| 前端订阅 | 主要是 WebSocket |
| 回滚模式 | `inline`、旧 Redis list |

这套方案已经能工作，但队列语义、重试策略、worker 生命周期和并发模型都要由项目自己维护。

## 改造后

改造后，任务执行层切换为 Celery，Redis 作为 Celery broker、result backend、事件总线和租约基础设施：

```text
HTTP 请求
  -> 业务路由创建任务并快速返回 task_id
  -> dispatch_generation_task()
  -> Celery send_task("edumind.generation.run")
  -> Redis broker 保存待执行任务
  -> generation-worker / Celery worker 执行业务 handler
  -> Redis Pub/Sub 推送进度
  -> WebSocket 或 SSE 返回前端
```

| 能力 | 改造后 |
| --- | --- |
| 任务队列 | Celery task queue |
| broker | Redis |
| result backend | Redis |
| worker | Celery worker，由 `generation-worker` 容器运行 |
| 失败处理 | Celery retry、ack late、worker lost reject |
| 并发控制 | `CELERY_WORKER_CONCURRENCY`、prefetch 控制 |
| 进度推送 | 继续使用 Redis Pub/Sub |
| 前端订阅 | WebSocket 保持兼容，新增 SSE 进度接口 |
| 回滚模式 | 仍保留 `inline` 和旧 `redis` provider |

## 核心变化

### 1. 业务服务不再直接执行长任务

改造前，API/service 进程可能直接执行耗时生成逻辑。改造后，业务服务只负责：

- 校验请求和用户权限。
- 写入任务元数据。
- 投递 Celery 任务。
- 返回任务 ID、WebSocket 地址或 SSE 地址。

真正耗时的生成逻辑交给 `generation-worker` 执行。

### 2. 自写 Redis list 队列升级为 Celery

原来项目需要维护 Redis list、processing list、dead-letter list 和 worker 循环。现在 Celery 提供更成熟的队列抽象：

- `task_acks_late=True`：任务完成后再确认。
- `task_reject_on_worker_lost=True`：worker 异常退出时任务可重新投递。
- `worker_prefetch_multiplier=1`：减少单个 worker 预取过多长任务。
- `visibility_timeout`：避免 Redis broker 中任务不可见时间过短。
- `self.retry(...)`：统一失败重试策略。

### 3. Redis 的职责更清晰

Redis 现在承担四类基础设施职责：

| Redis 用途 | 说明 |
| --- | --- |
| Celery broker | 保存待执行任务 |
| Celery result backend | 保存任务执行状态/结果 |
| EventBus | 通过 Pub/Sub 分发进度事件 |
| TaskLease | 避免同一个生成任务被重复执行 |

这让不同服务和 worker 可以跨进程共享任务状态、进度事件和执行租约。

### 4. WebSocket 兼容，SSE 补充

原有 WebSocket 路径继续保留，旧前端可以不改。新增 SSE 后，单向进度订阅可以更轻：

| 订阅方式 | 适合场景 |
| --- | --- |
| WebSocket | 双向对话、已有实时页面、需要客户端继续发送消息 |
| SSE | 只需要服务端推送任务阶段、结果、错误 |

SSE 的优势是浏览器原生支持、协议简单、自动重连更直接。

## 主要优势

### 更稳定

长任务从请求链路中拆出去后，浏览器刷新、网关超时或 API 服务短暂波动，不会直接打断 worker 中的生成任务。

### 更容易扩容

如果教学视频或播客生成变慢，可以只扩容 `generation-worker`，不用横向扩容所有业务 API 服务。

### 更容易排障

Celery worker 日志集中记录任务开始、重试、失败和完成状态。Redis 队列名、任务 kind、task id 都更容易定位。

### 更少自维护基础设施

项目不需要继续扩大自写 worker 的复杂度。Celery 已经覆盖任务确认、重试、并发、预取、broker 重连等通用能力。

### 保留兼容和回滚

`TASK_QUEUE_PROVIDER` 仍支持：

```text
inline
redis
celery
```

这意味着本地调试可以继续用 `inline`，必要时也能临时回到旧 Redis list provider。

## 关键配置

推荐的 Docker Compose / 微服务配置：

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

## 服务职责变化

| 服务 | 改造前 | 改造后 |
| --- | --- | --- |
| `learning-content` | 可能直接执行或投递旧队列 | 创建任务并投递 Celery |
| `media-generation` | 可能直接执行或投递旧队列 | 创建任务并投递 Celery |
| `teaching-content` | 可能直接执行或投递旧队列 | 创建任务并投递 Celery |
| `generation-worker` | 自写队列消费者 | Celery worker |
| `redis` | 队列、事件、租约 | Celery broker/backend、事件、租约 |

## 总结

改造前，EduMind 已经有可用的 Redis 队列和 worker，但核心任务调度能力仍由项目自己维护。改造后，Celery 接管长任务调度，Redis 统一提供队列、结果、事件和租约能力。

最大的收益是：API 服务更轻、worker 更独立、任务更可靠、扩容更直接，同时保留旧模式作为调试和回滚路径。
