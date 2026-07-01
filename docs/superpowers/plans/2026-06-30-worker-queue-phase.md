# Worker Queue Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a production worker boundary for long-running generation tasks while keeping inline execution as the local development default.

**Architecture:** Add a task queue adapter with inline and Redis providers. API services dispatch `kind/id` envelopes through `dispatch_generation_task`; inline mode starts local runners, Redis mode enqueues work for `worker_app.py`. The worker imports route modules to register handlers and consumes the queue continuously.

**Tech Stack:** Python 3.11, Redis lists, existing TaskLease/EventBus adapters, Docker Compose.

---

### Task 1: Queue Adapter

**Files:**
- Create: `backend/infrastructure/task_queue.py`
- Modify: `backend/config.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add queue configuration**

`TASK_QUEUE_PROVIDER`, `TASK_QUEUE_NAME`, and `TASK_WORKER_POLL_SECONDS` are available in settings.

- [x] **Step 2: Add inline and Redis providers**

Inline is a no-op queue for local development. Redis uses `RPUSH`/`BLPOP` on JSON envelopes.

- [x] **Step 3: Test inline provider behavior**

The inline queue accepts enqueue calls and never dequeues work.

### Task 2: Dispatcher And Worker

**Files:**
- Create: `backend/core/task_dispatcher.py`
- Create: `backend/worker_app.py`
- Modify: `scripts/start_backend_service.py`
- Test: `tests/backend/test_app_factory.py`

- [x] **Step 1: Add task handler registry**

Route modules register existing runner functions by task kind.

- [x] **Step 2: Add dispatch function**

`dispatch_generation_task` starts inline runners or enqueues Redis tasks based on configuration.

- [x] **Step 3: Add worker entrypoint**

`worker_app.py` imports runner modules, logs registered handlers, and consumes queued work.

- [x] **Step 4: Add worker role**

`BACKEND_ROLE=worker` runs the worker instead of uvicorn.

### Task 3: Runner Integration

**Files:**
- Modify: `backend/api/routes/chat.py`
- Modify: `backend/api/routes/exam.py`
- Modify: `backend/api/routes/paper.py`
- Modify: `backend/api/routes/teaching_video.py`

- [x] **Step 1: Register runner handlers**

The four runner-backed workflows register `chat`, `exam`, `paper`, and `teaching_video`.

- [x] **Step 2: Dispatch from HTTP create endpoints**

Existing REST responses are preserved.

- [x] **Step 3: Dispatch from WebSocket fallback triggers**

WebSockets remain subscriber/replay endpoints and enqueue work when cached state is incomplete.

### Task 4: Compose And Verification

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Add `generation-worker` service**

The worker shares the backend image and consumes Redis queue tasks.

- [x] **Step 2: Configure business services for Redis queue**

Learning, media, and teaching services enqueue work in Compose; gateway, identity, and asset-library stay inline/no-op.

- [x] **Step 3: Run verification**

Backend tests, compileall, and `docker compose config --quiet` pass.
