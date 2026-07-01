# Durable Runners Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decouple the most important long-running generation workflows from WebSocket connection lifetimes so service instances can scale and reconnect safely while preserving existing frontend stream URLs.

**Architecture:** Keep HTTP create endpoints and WebSocket paths unchanged. Each create endpoint stores request state, triggers a lease-guarded runner, and returns the existing stream URL. Each WebSocket endpoint validates access, forwards EventBus messages, replays cached snapshots, and can re-trigger the same runner if needed.

**Tech Stack:** Python 3.11, FastAPI WebSockets, Redis/EventBus adapters, TaskLease, existing KV storage.

---

### Task 1: Chat Runner

**Files:**
- Modify: `backend/api/routes/chat.py`

- [x] **Step 1: Add task registry and `_ensure_chat_generation`**

The runner acquires the existing chat lease and publishes progress through `utils.live_events`.

- [x] **Step 2: Trigger runner from POST `/chat`**

POST keeps returning `202` with `chatId` and `stream`.

- [x] **Step 3: Simplify `/ws/chat`**

The websocket now subscribes, replays an existing assistant answer if available, and triggers the runner if the last message is still from the user.

### Task 2: Exam Runner

**Files:**
- Modify: `backend/api/routes/exam.py`

- [x] **Step 1: Add task registry and `_ensure_exam_generation`**

The runner owns quiz-agent execution and stores `exam_run:{id}:questions`.

- [x] **Step 2: Trigger runner from POST `/exam`**

The route still returns the existing `runId` and `/ws/exams` stream path.

- [x] **Step 3: Simplify `/ws/exams`**

The websocket now replays cached questions or subscribes while the runner publishes events.

### Task 3: Paper Runner

**Files:**
- Modify: `backend/api/routes/paper.py`

- [x] **Step 1: Add task registry and `_ensure_paper_generation`**

The runner owns paper-agent execution and stores `paper:{id}:paper`.

- [x] **Step 2: Trigger runner from POST `/paper`**

The route still returns `paperId` and `/ws/paper`.

- [x] **Step 3: Simplify `/ws/paper`**

The websocket now validates, replays cached papers, and subscribes to EventBus.

### Task 4: Teaching Video Runner

**Files:**
- Modify: `backend/api/routes/teaching_video.py`

- [x] **Step 1: Add task registry and `_ensure_teaching_video_generation`**

The runner owns script generation, TTS audio, remote video polling, local merge/fallback, and final ObjectStore commit.

- [x] **Step 2: Trigger runner from POST `/teaching-video`**

The route still returns `videoId` and `/ws/teaching-video`.

- [x] **Step 3: Simplify `/ws/teaching-video`**

The websocket now replays saved phase/script/media state and subscribes without running generation inline.

### Task 5: Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Run backend tests**

`.\.venv\Scripts\python.exe -m pytest tests\backend -q` passes.

- [x] **Step 2: Compile backend**

`.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes tests\backend` passes.

- [x] **Step 3: Validate Compose**

`docker compose config --quiet` passes from the repository root.

- [x] **Step 4: Update architecture docs**

Record that these workflows are now runner-backed and WebSocket endpoints are subscriber/replay boundaries.
