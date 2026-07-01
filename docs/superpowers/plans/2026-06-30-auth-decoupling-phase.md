# Auth Decoupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove startup-time coupling between non-identity boundary services and the local SQLite auth implementation.

**Architecture:** `utils.auth` keeps the public helper API used by route modules, but imports `utils.auth_db` only when `AUTH_VALIDATION_MODE` is local. Remote mode continues to resolve users through the identity service.

**Tech Stack:** FastAPI dependencies, existing identity `/auth/internal/resolve` endpoint, pytest.

---

## File Structure

- Modify `backend/utils/auth.py`: replace module-level `auth_db` import with a local-store helper that imports lazily.
- Modify `tests/backend/test_app_factory.py`: add a regression test that remote auth resolution does not call the local-store helper.
- Modify `docs/architecture/backend-service-boundaries.md`: update remaining auth coupling notes.
- Test with backend pytest, compileall, and Compose config validation.

---

### Task 1: Lazy Local Auth Store

**Files:**
- Modify: `backend/utils/auth.py`

- [x] **Step 1: Remove the top-level local database import**

```python
from utils.auth_db import auth_db
```

- [x] **Step 2: Add a lazy local resolver**

```python
def resolve_user_from_local_store(token: str) -> Optional[AuthUser]:
    from utils.auth_db import auth_db

    return auth_db.get_user_by_token(token)
```

- [x] **Step 3: Route local mode through the lazy resolver**

```python
return resolve_user_from_local_store(token)
```

---

### Task 2: Regression Test

**Files:**
- Modify: `tests/backend/test_app_factory.py`

- [x] **Step 1: Add remote-mode branch test**

```python
def test_remote_auth_resolution_skips_local_auth_store(monkeypatch):
    ...
```

The test monkeypatches remote identity resolution to return an `AuthUser` and monkeypatches the local resolver to raise if called.

---

### Task 3: Documentation And Verification

**Files:**
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Update auth coupling text**

Document that only the identity route and lifespan hook import `utils.auth_db` directly; route helpers lazy-load it only for local mode.

- [x] **Step 2: Run backend tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q
```

- [x] **Step 3: Run compile check**

```powershell
.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes backend\worker_app.py scripts tests\backend
```

- [x] **Step 4: Validate Compose**

```powershell
docker compose config --quiet
```
