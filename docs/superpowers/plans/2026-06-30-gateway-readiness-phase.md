# Gateway Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-style liveness and readiness checks to the API gateway so deployments can distinguish "gateway process is alive" from "all upstream services are reachable".

**Architecture:** Keep `/health` as the existing lightweight status endpoint. Add `/health/live` for process liveness and `/health/ready` for upstream service readiness. Docker Compose should use `/health/ready` for the gateway service.

**Tech Stack:** FastAPI, httpx, Docker Compose healthchecks, pytest.

---

## File Structure

- Modify `backend/core/gateway.py`: add upstream health probe helpers and two health endpoints.
- Modify `../docker-compose.yml`: switch the `api-gateway` healthcheck to `/health/ready` and expose a probe timeout environment variable.
- Modify `tests/backend/test_app_factory.py`: test upstream health aggregation without real network calls.
- Modify `docs/architecture/backend-service-boundaries.md`: document liveness/readiness behavior.
- Test with backend pytest, compileall, and Compose config validation.

---

### Task 1: Gateway Health Helpers

**Files:**
- Modify: `backend/core/gateway.py`

- [x] **Step 1: Add helper functions**

```python
def build_health_url(base_url: str) -> str:
    return build_upstream_url(base_url, "/health", "")
```

```python
async def check_upstream_health(service: str, base_url: str, client: httpx.AsyncClient | None = None) -> dict:
    ...
```

```python
async def check_upstreams(service_urls: dict[str, str], client: httpx.AsyncClient | None = None) -> dict[str, dict]:
    ...
```

- [x] **Step 2: Add endpoints**

```python
@app.get("/health/live")
async def live():
    return {"status": "healthy", "service": "api-gateway"}
```

```python
@app.get("/health/ready")
async def ready():
    upstreams = await check_upstreams(app.state.service_urls)
    is_ready = all(item["status"] == "healthy" for item in upstreams.values())
    return JSONResponse(..., status_code=200 if is_ready else 503)
```

---

### Task 2: Compose Healthcheck

**Files:**
- Modify: `../docker-compose.yml`

- [x] **Step 1: Add timeout env var**

```yaml
GATEWAY_HEALTH_TIMEOUT_SECONDS: ${GATEWAY_HEALTH_TIMEOUT_SECONDS:-2}
```

- [x] **Step 2: Use readiness endpoint**

```yaml
test: ["CMD", "curl", "-fsS", "http://127.0.0.1:5000/health/ready"]
```

---

### Task 3: Tests And Docs

**Files:**
- Modify: `tests/backend/test_app_factory.py`
- Modify: `docs/architecture/backend-service-boundaries.md`

- [x] **Step 1: Test upstream health aggregation**

Use `httpx.MockTransport` so the test does not require live services.

- [x] **Step 2: Document health semantics**

Explain `/health`, `/health/live`, and `/health/ready`.

- [x] **Step 3: Verify**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\backend -q
.\.venv\Scripts\python.exe -m compileall backend\core backend\infrastructure backend\utils backend\api\routes backend\worker_app.py scripts tests\backend
```

From `C:\Users\熊骞\Desktop\EduMind`, run:

```powershell
docker compose config --quiet
```
