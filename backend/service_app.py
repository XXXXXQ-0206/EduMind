"""Entrypoint for running a single EduMind service boundary."""
from __future__ import annotations

import os

import uvicorn

from config import config
from core.app_factory import create_service_app
from core.service_registry import get_service_boundary


SERVICE_NAME = os.environ.get("SERVICE_NAME", "identity")
SERVICE_BOUNDARY = get_service_boundary(SERVICE_NAME)

app = create_service_app(SERVICE_BOUNDARY.name)


if __name__ == "__main__":
    uvicorn.run(
        "service_app:app",
        host=config.host,
        port=int(os.environ.get("PORT", SERVICE_BOUNDARY.default_port)),
        reload=True,
        log_level="info",
    )
