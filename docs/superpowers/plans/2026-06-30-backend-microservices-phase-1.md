# Backend Microservices Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the EduMind backend from an implicit modular monolith into an explicit, test-guarded modular monolith that can be split into microservices without changing the current frontend API.

**Architecture:** Introduce a FastAPI application factory and service boundary registry. Keep all existing route handlers in place, but register them through named boundaries so future work can move one boundary behind a gateway at a time.

**Tech Stack:** Python 3.11, FastAPI, pytest, existing EduMind backend modules.

---

### Task 1: Application Assembly Boundary

**Files:**
- Create: `backend/core/__init__.py`
- Create: `backend/core/app_factory.py`
- Create: `backend/core/lifespan.py`
- Create: `backend/core/service_registry.py`
- Modify: `backend/main.py`

- [x] **Step 1: Create the service boundary registry**

Add `ServiceBoundary` and `RouteMount` dataclasses, then group existing routers into `identity`, `learning-content`, `asset-library`, `media-generation`, and `teaching-content`.

- [x] **Step 2: Move process lifecycle logic**

Move auth database initialization and Bilibili bridge startup/shutdown into `backend/core/lifespan.py`.

- [x] **Step 3: Create the FastAPI application factory**

Create `create_app()` in `backend/core/app_factory.py`, configure middleware, mount `/storage`, register routes through the registry, and expose `/` plus `/health`.

- [x] **Step 4: Keep `main.py` as the compatibility entrypoint**

Update `backend/main.py` to instantiate `app = create_app()` and preserve the existing `uvicorn main:app` launch path.

### Task 2: Route Contract Verification

**Files:**
- Create: `tests/backend/test_app_factory.py`

- [x] **Step 1: Test service boundary names**

Verify the application exposes the five expected boundary names on `app.state.service_boundaries`.

- [x] **Step 2: Test legacy public routes**

Verify representative HTTP and WebSocket paths remain mounted, including `/auth/login`, `/chat`, `/files`, `/smartnotes`, `/quiz`, `/podcast`, `/lesson-plan`, `/slides/generate`, `/teaching-video`, `/api/bilibili/search`, `/ws/chat`, `/ws/quiz`, and `/ws/teaching-video`.

- [x] **Step 3: Run the test**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend\test_app_factory.py -q
```

Expected result: `2 passed`.

### Task 3: Architecture Documentation

**Files:**
- Create: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Document current assembly**

Explain that the backend is still deployed as one FastAPI process, but route ownership is now explicit.

- [x] **Step 2: Document extraction order**

Record the recommended order: identity, asset-library, media-generation, then learning-content and teaching-content.

- [x] **Step 3: Document migration rules**

Document compatibility, repository extraction, object storage, and WebSocket progress rules.

