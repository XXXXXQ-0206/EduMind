"""FastAPI application factory for EduMind."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import config
from core.lifespan import shutdown_services, startup_services
from core.service_registry import (
    SERVICE_BOUNDARIES,
    ServiceBoundary,
    get_service_boundary,
    iter_route_mounts,
)


def create_app() -> FastAPI:
    """Create the EduMind modular monolith application."""

    app = FastAPI(
        title="EduMind API",
        description="AI-powered learning platform backend",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.service_boundaries = SERVICE_BOUNDARIES
    app.state.service_name = "modular-monolith"
    app.state.starts_bilibili_bridge = should_start_bilibili_bridge(default=True)
    configure_middleware(app)
    mount_static_assets(app)
    register_routes(app)
    register_health_routes(app)
    return app


def create_service_app(service_name: str) -> FastAPI:
    """Create an independently runnable service boundary application."""

    boundary = get_service_boundary(service_name)
    app = FastAPI(
        title=f"EduMind {boundary.name} Service",
        description=boundary.description,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.service_boundaries = (boundary,)
    app.state.service_boundary = boundary
    app.state.service_name = boundary.name
    app.state.starts_bilibili_bridge = should_start_bilibili_bridge(default=False)
    configure_middleware(app)
    mount_static_assets(app)
    register_boundary_routes(app, boundary)
    register_service_health_routes(app, boundary)
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_services(app)
    try:
        yield
    finally:
        await shutdown_services(app)


def configure_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )


def should_start_bilibili_bridge(default: bool = False) -> bool:
    value = os.environ.get("START_BILIBILI_BRIDGE")
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def mount_static_assets(app: FastAPI) -> None:
    app.mount("/storage", StaticFiles(directory=str(config.storage_dir)), name="storage")


def register_routes(app: FastAPI) -> None:
    for mount in iter_route_mounts():
        app.include_router(mount.router, tags=[mount.tag])


def register_boundary_routes(app: FastAPI, boundary: ServiceBoundary) -> None:
    for mount in boundary.mounts:
        app.include_router(mount.router, tags=[mount.tag])


def register_health_routes(app: FastAPI) -> None:
    @app.get("/")
    async def root():
        """Root health check."""

        return {
            "status": "ok",
            "message": "EduMind Python Backend is running",
            "version": "1.0.0",
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""

        return {
            "status": "healthy",
            "llm_provider": config.llm_provider,
            "emb_provider": config.emb_provider,
            "service_boundaries": [boundary.name for boundary in SERVICE_BOUNDARIES],
        }


def register_service_health_routes(app: FastAPI, boundary: ServiceBoundary) -> None:
    @app.get("/")
    async def root():
        """Service root health check."""

        return {
            "status": "ok",
            "service": boundary.name,
            "message": f"EduMind {boundary.name} service is running",
            "version": "1.0.0",
        }

    @app.get("/health")
    async def health():
        """Service health check endpoint."""

        return {
            "status": "healthy",
            "service": boundary.name,
            "llm_provider": config.llm_provider,
            "emb_provider": config.emb_provider,
        }
