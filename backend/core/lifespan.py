"""Startup and shutdown hooks for process-local infrastructure."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI

from utils.auth_db import auth_db


async def startup_services(app: FastAPI) -> None:
    """Initialize local dependencies used by the modular monolith."""

    if should_initialize_auth_db(app):
        auth_db.initialize()
    if getattr(app.state, "starts_bilibili_bridge", False):
        await startup_bilibili_bridge(app)


async def shutdown_services(app: FastAPI) -> None:
    """Stop local dependencies owned by this process."""

    await shutdown_bilibili_bridge(app)


def should_initialize_auth_db(app: FastAPI) -> bool:
    """Return whether this process owns direct auth database initialization."""

    service_name = str(getattr(app.state, "service_name", "") or "")
    auth_mode = str(os.environ.get("AUTH_VALIDATION_MODE", "local") or "local").strip().lower()
    return service_name in {"modular-monolith", "identity"} or auth_mode != "remote"


async def startup_bilibili_bridge(app: FastAPI) -> None:
    """Start the local Node.js Bilibili MCP bridge when Node is available."""

    node_path = shutil.which("node")
    if not node_path:
        print("[WARN] Node.js not found, skip starting bilibili MCP bridge")
        return

    backend_dir = Path(__file__).resolve().parent.parent
    bridge_entry = backend_dir / "services" / "bilibiliBridgeServer.js"

    if not bridge_entry.exists():
        print("[WARN] bilibili bridge server file not found, skip startup")
        return

    env = os.environ.copy()
    bridge_port = env.get("BILIBILI_BRIDGE_PORT", "5001")
    env.setdefault("BILIBILI_BRIDGE_URL", f"http://127.0.0.1:{bridge_port}")

    try:
        app.state.bilibili_bridge_proc = subprocess.Popen(
            [node_path, str(bridge_entry)],
            cwd=str(backend_dir),
            env=env,
        )
        print(f"[INFO] bilibili MCP bridge started on port {bridge_port}")
    except Exception as exc:
        print(f"[WARN] failed to start bilibili MCP bridge: {exc}")


async def shutdown_bilibili_bridge(app: FastAPI) -> None:
    """Terminate the local Bilibili bridge if this process started it."""

    proc = getattr(app.state, "bilibili_bridge_proc", None)
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
        print("[INFO] bilibili MCP bridge stopped")
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
