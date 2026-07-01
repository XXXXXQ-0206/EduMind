"""Entrypoint for the EduMind API Gateway."""
from __future__ import annotations

import os

import uvicorn

from config import config
from core.gateway import DEFAULT_GATEWAY_PORT, create_gateway_app


app = create_gateway_app()


if __name__ == "__main__":
    uvicorn.run(
        "gateway_app:app",
        host=config.host,
        port=int(os.environ.get("PORT", DEFAULT_GATEWAY_PORT)),
        reload=True,
        log_level="info",
    )
