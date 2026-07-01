# Remaining Worker Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the remaining user-facing long-running generators, SmartNotes, Quiz, and Podcast, behind the shared task dispatcher and worker queue boundary.

**Architecture:** HTTP routes persist request state and enqueue work through `core.task_dispatcher`. WebSocket routes validate ownership, send `ready`, replay durable snapshots from KV, and subscribe to `utils.live_events`. Worker registration happens by importing route modules in `backend/worker_app.py`.

**Tech Stack:** FastAPI, asyncio, Redis-backed queue/event/lease adapters, existing KV/ObjectStore adapters.

---

## File Structure

- Modify `backend/api/routes/notes.py`: dispatch SmartNotes generation through the shared task dispatcher and register its runner.
- Modify `backend/api/routes/quiz.py`: dispatch Quiz generation through the shared task dispatcher and register its runner.
- Modify `backend/api/routes/podcast.py`: extract WebSocket-bound generation into a lease-guarded runner that publishes live events, then dispatch it through the shared task dispatcher.
- Modify `backend/worker_app.py`: import SmartNotes, Quiz, and Podcast route modules so handlers register in worker mode.
- Modify `docs/architecture/backend-service-boundaries.md`: update queue coverage status and remaining work.
- Test with `pytest`, `compileall`, and `docker compose config --quiet`.

---

### Task 1: SmartNotes Dispatcher Integration

**Files:**
- Modify: `backend/api/routes/notes.py`

- [x] **Step 1: Import dispatcher functions**

```python
from core.task_dispatcher import dispatch_generation_task, register_task_handler
```

- [x] **Step 2: Replace direct runner starts**

Use this pattern anywhere create, WebSocket fallback, or detail polling starts generation:

```python
await dispatch_generation_task("smartnotes", note_id, _ensure_note_generation)
```

- [x] **Step 3: Register the runner**

```python
register_task_handler("smartnotes", _ensure_note_generation)
```

---

### Task 2: Quiz Dispatcher Integration

**Files:**
- Modify: `backend/api/routes/quiz.py`

- [x] **Step 1: Import dispatcher functions**

```python
from core.task_dispatcher import dispatch_generation_task, register_task_handler
```

- [x] **Step 2: Replace direct runner starts**

Use this pattern anywhere create, WebSocket fallback, or detail polling starts generation:

```python
await dispatch_generation_task("quiz", quiz_id, ensure_quiz_generation_task)
```

- [x] **Step 3: Register the runner**

```python
register_task_handler("quiz", ensure_quiz_generation_task)
```

---

### Task 3: Podcast Runner Extraction

**Files:**
- Modify: `backend/api/routes/podcast.py`

- [x] **Step 1: Add imports and task registry**

```python
import asyncio

from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.live_events import forward_live_events, publish_live_event
```

- [x] **Step 2: Add helper functions**

Create `_podcast_channel`, `_send_podcast_event`, `_update_podcast_meta`, `_send_podcast_snapshot`, `_ensure_podcast_generation`, `_run_podcast_generation`, and `_build_material_context`.

- [x] **Step 3: Keep REST and WS contracts stable**

Create returns:

```python
{"ok": True, "pid": pid, "stream": f"/ws/podcast?pid={pid}"}
```

WebSocket sends:

```python
{"type": "ready", "pid": pid}
```

Snapshot replay sends `script`, `audio`, `warn`, `phase`, `done`, or `error` messages using existing field names.

- [x] **Step 4: Register the runner**

```python
register_task_handler("podcast", _ensure_podcast_generation)
```

---

### Task 4: Worker Registration

**Files:**
- Modify: `backend/worker_app.py`

- [x] **Step 1: Import all queue-backed route modules**

```python
from api.routes import chat, exam, notes, paper, podcast, quiz, teaching_video  # noqa: F401
```

---

### Task 5: Documentation And Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Update architecture text**

Document that Chat, Smart Notes, Quiz, Exam, Paper, Podcast, and Teaching Video now use the queue-backed worker boundary.

- [x] **Step 2: Run backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q
```

Expected: all tests pass.

- [x] **Step 3: Run compile check**

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes backend\worker_app.py scripts tests\backend
```

Expected: command exits successfully.

- [x] **Step 4: Validate Compose**

Run from `C:\Users\熊骞\Desktop\EduMind`:

```powershell
docker compose config --quiet
```

Expected: command exits successfully.
