# Final Microservice Gap Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the reviewed microservice migration gaps while keeping the existing frontend REST/WebSocket contract stable.

**Architecture:** Add an `ai-core` boundary with an internal LLM invocation endpoint and make business services able to route LLM calls through it. Add a PostgreSQL JSONB KV adapter as the first formal database-backed state model. Replace the in-process Bilibili bridge startup in Compose with an independently managed Node service. Upgrade Redis task queue semantics from destructive list pop to pending/processing/retry/dead-letter queues. Harden gateway upstream request cleanup.

**Tech Stack:** FastAPI, httpx, Redis, PostgreSQL via psycopg, Docker Compose, pytest.

---

### Task 1: Reliable Queue Adapter

**Files:**
- Modify: `backend/infrastructure/task_queue.py`
- Modify: `backend/core/task_dispatcher.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add task queue ack/fail protocol**

Add `ack(task)` and `fail(task, error)` to the queue protocol and include `attempts`, `max_attempts`, and `error` in `TaskEnvelope`.

- [x] **Step 2: Replace Redis BLPOP with BRPOPLPUSH**

Move tasks from pending to processing atomically, acknowledge with `LREM`, retry with `LPUSH`, and dead-letter after max attempts.

- [x] **Step 3: Worker acknowledges and fails tasks**

Call `ack` after handler success and `fail` after handler error or unknown task kind.

---

### Task 2: AI Core Service

**Files:**
- Create: `backend/api/routes/ai_core.py`
- Modify: `backend/utils/llm.py`
- Modify: `backend/config.py`
- Modify: `backend/core/service_registry.py`
- Modify: `docker-compose.yml`
- Test: `tests/backend/test_app_factory.py`

- [x] **Step 1: Add internal invoke endpoint**

Expose `POST /ai/internal/invoke` from the `ai-core` boundary.

- [x] **Step 2: Add remote LLM mode**

When `LLM_EXECUTION_MODE=remote`, route `utils.llm.invoke_llm` through `AI_CORE_URL`.

- [x] **Step 3: Add Compose ai-core service**

Run `SERVICE_NAME=ai-core` with `LLM_EXECUTION_MODE=local`; business services set `AI_CORE_URL=http://ai-core:5106`.

---

### Task 3: PostgreSQL KV Provider

**Files:**
- Modify: `backend/infrastructure/kv_store.py`
- Modify: `backend/config.py`
- Modify: `requirements.txt`
- Modify: `docker-compose.yml`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add Postgres config**

Add `POSTGRES_DSN` and support `KV_STORE_PROVIDER=postgres`.

- [x] **Step 2: Implement `PostgresKeyValueStore`**

Use a JSONB table `edumind_kv(key text primary key, value jsonb not null, updated_at timestamptz not null default now())`.

- [x] **Step 3: Add PostgreSQL service to Compose**

Include healthcheck and default business service `POSTGRES_DSN`.

---

### Task 4: Independent Bilibili Bridge Service

**Files:**
- Modify: `backend/core/app_factory.py`
- Modify: `backend/core/lifespan.py`
- Modify: `docker-compose.yml`
- Test: `tests/backend/test_app_factory.py`

- [x] **Step 1: Stop starting bridge inside service mode**

Only monolith starts the local child process by default; media-generation uses `BILIBILI_BRIDGE_URL`.

- [x] **Step 2: Add Compose `bilibili-bridge` service**

Run the Node bridge as its own service and point media-generation to it.

---

### Task 5: Gateway Cleanup And Verification

**Files:**
- Modify: `backend/core/gateway.py`
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Close upstream client on proxy errors**

Wrap upstream send in `try/except` and close the httpx client on error.

- [x] **Step 2: Verify**

Run backend pytest, compileall, and `docker compose config --quiet`.
