"""Start an EduMind backend process role inside one reusable image."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn

from config import config
from core.gateway import DEFAULT_GATEWAY_PORT
from core.service_registry import get_service_boundary


def is_worker_role(role: str) -> bool:
    return (role or "").strip().lower() in {"worker", "task-worker"}


def resolve_app_target() -> tuple[str, int]:
    role = os.environ.get("BACKEND_ROLE", "monolith").strip().lower()
    if role in {"gateway", "api-gateway"}:
        return "gateway_app:app", int(os.environ.get("PORT", DEFAULT_GATEWAY_PORT))
    if role in {"service", "boundary"}:
        service_name = os.environ.get("SERVICE_NAME", "identity")
        boundary = get_service_boundary(service_name)
        return "service_app:app", int(os.environ.get("PORT", boundary.default_port))
    return "main:app", int(os.environ.get("PORT", config.port))


if __name__ == "__main__":
    role = os.environ.get("BACKEND_ROLE", "monolith").strip().lower()
    if is_worker_role(role):
        from worker_app import main as worker_main

        import asyncio

        asyncio.run(worker_main())
        raise SystemExit(0)

    app_target, port = resolve_app_target()
    uvicorn.run(
        app_target,
        host=config.host,
        port=port,
        reload=False,
        log_level="info",
    )
