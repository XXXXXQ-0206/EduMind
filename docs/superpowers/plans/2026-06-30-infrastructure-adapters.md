# Infrastructure Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move shared backend state behind replaceable infrastructure adapters so EduMind services can later switch from local JSON/files/WebSocket-only state to database, object storage, and pub/sub without changing route code again.

**Architecture:** Keep current local behavior as the default adapter. Introduce explicit interfaces and factory functions for key-value JSON state, object files, and task events. Migrate the file library route to the object store adapter first because it is the cleanest boundary and feeds many other services.

**Tech Stack:** Python 3.11, FastAPI, aiofiles, pytest, existing EduMind backend.

---

### Task 1: Key-Value Store Adapter

**Files:**
- Create: `backend/infrastructure/__init__.py`
- Create: `backend/infrastructure/kv_store.py`
- Modify: `backend/config.py`
- Modify: `backend/utils/storage.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add KV store configuration**

Add `KV_STORE_PROVIDER` with default `json`.

- [x] **Step 2: Create `KeyValueStore` protocol and JSON adapter**

Define `get`, `set`, `delete`, `path_for_key`, and `iter_prefix`.

- [x] **Step 3: Wire `utils.storage.JSONStorage` through the adapter**

Keep the public `JSONStorage` class but delegate file path and get/set/delete behavior to the adapter.

- [x] **Step 4: Test key sanitization and read/write/delete**

Verify keys with `:` and `/` still map to safe JSON files and preserve existing behavior.

### Task 2: Object Store Adapter

**Files:**
- Create: `backend/infrastructure/object_store.py`
- Modify: `backend/config.py`
- Modify: `backend/api/routes/files.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add object store configuration**

Add `OBJECT_STORE_PROVIDER`, `OBJECT_STORE_BASE_URL`, and keep local filesystem default.

- [x] **Step 2: Create local filesystem object store**

Implement `put_bytes`, `delete`, `url_for`, and `path_for`.

- [x] **Step 3: Migrate file uploads/deletes**

Update `/files` route to write and delete through object store while keeping response shape unchanged.

- [x] **Step 4: Test local object store URLs and paths**

Verify uploaded object keys produce `/storage/...` compatible URLs by default.

### Task 3: Task Event Bus Foundation

**Files:**
- Create: `backend/infrastructure/event_bus.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Define event bus interface**

Add `publish`, `subscribe`, and local in-memory implementation.

- [x] **Step 2: Document Redis replacement boundary**

Keep implementation local for now, but make provider selection explicit.

- [x] **Step 3: Test local publish/subscribe**

Verify subscribers receive published event payloads.

### Task 4: Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Run focused tests**

Run `.\.venv\Scripts\python.exe -m pytest tests\backend -q`.

- [x] **Step 2: Run compile check**

Run `.\.venv\Scripts\python.exe -m compileall backend tests\backend`.

- [x] **Step 3: Update architecture documentation**

Record the adapter boundaries and next provider swaps.
