# Shared State And Artifacts Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the highest-risk remaining single-process assumptions by making shared JSON mutations adapter-owned and moving generated binary artifacts behind ObjectStore while preserving the current REST and WebSocket contracts.

**Architecture:** Add an atomic `update` operation to the KV adapter and expose it through the existing `JSONStorage` facade. Migrate list-like shared state in files, planner, flashcards, and speaking history to this operation. Then store exported PDFs and slide download artifacts through ObjectStore while keeping legacy download endpoints and response shapes intact.

**Tech Stack:** Python 3.11, FastAPI, aiofiles, Redis/JSON KV adapters, S3/MinIO/local ObjectStore, pytest.

---

### Task 1: Atomic KV Updates

**Files:**
- Modify: `backend/infrastructure/kv_store.py`
- Modify: `backend/utils/storage.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Add an adapter-level updater contract**

Define a `JsonUpdater` callable type and `KeyValueStore.update(key, updater, default)` method. The method must return the stored value after mutation.

- [x] **Step 2: Implement JSON-file update**

Read the current value under a per-key lock, call the updater, write a temp JSON file, then replace the target file. This keeps local behavior while avoiding in-process lost updates.

- [x] **Step 3: Implement Redis CAS update**

Use Redis `WATCH`, `MULTI`, and `EXEC`; retry on `WatchError` so concurrent writers merge through the same updater logic.

- [x] **Step 4: Expose `JSONStorage.update`**

Keep route code importing `json_storage`, but let high-write routes call `await json_storage.update(...)`.

- [x] **Step 5: Test update merging**

Add a test that performs concurrent appends against one key and verifies no append is lost.

### Task 2: Migrate Shared Lists

**Files:**
- Modify: `backend/api/routes/files.py`
- Modify: `backend/api/routes/planner.py`
- Modify: `backend/api/routes/flashcards.py`
- Modify: `backend/api/routes/speaking.py`
- Test: `tests/backend/test_infrastructure_adapters.py`

- [x] **Step 1: Update file library append/delete**

Use `json_storage.update` for upload list prepends and delete filtering. Keep returned `files`, `ok`, `error`, `objectKey`, and `url` fields unchanged.

- [x] **Step 2: Update planner task mutations**

Add small helpers that mutate the task list in a single `json_storage.update` call for create, patch, delete, plan, and attachment changes. Broadcast the same event payloads after the update.

- [x] **Step 3: Update flashcard indexes**

Keep per-card and per-deck records as separate keys, but mutate `flashcards` and `flashcard_decks` indexes through `update`.

- [x] **Step 4: Update speaking history upsert/delete**

Mutate the `speaking:history` list through `update`, preserving the newest-first max-50 behavior.

### Task 3: ObjectStore Binary Artifact Completion

**Files:**
- Modify: `backend/api/routes/lesson_plan.py`
- Modify: `backend/api/routes/paper.py`
- Modify: `backend/api/routes/slides.py`
- Modify: `backend/agents/slides_agent.py`
- Modify: `backend/utils/storage.py`

- [x] **Step 1: Export PDFs through ObjectStore**

Generate PDFs in a local temp/cache path, commit them to keys `lesson_plans/{id}.pdf` and `papers/{id}.pdf`, then serve the bytes from ObjectStore through the existing download endpoints.

- [x] **Step 2: Delete binary artifacts with metadata**

Extend lesson plan and paper deletion to remove their ObjectStore prefixes or known PDF keys.

- [x] **Step 3: Commit slide images/PPTX artifacts to ObjectStore**

Ensure slide images returned by the agent have stable object keys and list/download routes use metadata plus `list_prefix` rather than returning an empty history.

### Task 4: Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Run backend tests**

Run `.\.venv\Scripts\python.exe -m pytest tests\backend -q` and keep all tests green.

- [x] **Step 2: Compile backend**

Run `.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes tests\backend`.

- [x] **Step 3: Validate compose**

Run `docker compose config --quiet` from the repository root.

- [x] **Step 4: Update architecture docs**

Record the new atomic KV mutation rule and ObjectStore artifact boundary.
