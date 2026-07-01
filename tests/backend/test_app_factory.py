import sys
from pathlib import Path

from fastapi.routing import APIWebSocketRoute


BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from core.app_factory import create_app, create_service_app  # noqa: E402
from core.gateway import (  # noqa: E402
    HTTP_ROUTE_TARGETS,
    WEBSOCKET_ROUTE_TARGETS,
    build_upstream_url,
    build_websocket_url,
    build_health_url,
    check_upstreams,
    resolve_target,
)
from core.lifespan import should_initialize_auth_db  # noqa: E402
from scripts.start_backend_service import is_worker_role  # noqa: E402


def test_service_boundaries_are_registered():
    app = create_app()

    assert [boundary.name for boundary in app.state.service_boundaries] == [
        "identity",
        "learning-content",
        "asset-library",
        "ai-core",
        "media-generation",
        "teaching-content",
    ]


def test_public_route_contract_is_preserved():
    app = create_app()
    http_paths = {route.path for route in app.routes if hasattr(route, "path")}
    websocket_paths = {
        route.path
        for route in app.routes
        if isinstance(route, APIWebSocketRoute)
    }

    assert "/" in http_paths
    assert "/health" in http_paths
    assert "/auth/login" in http_paths
    assert "/auth/internal/resolve" in http_paths
    assert "/chat" in http_paths
    assert "/files" in http_paths
    assert "/smartnotes" in http_paths
    assert "/quiz" in http_paths
    assert "/podcast" in http_paths
    assert "/lesson-plan" in http_paths
    assert "/slides/generate" in http_paths
    assert "/teaching-video" in http_paths
    assert "/api/bilibili/search" in http_paths
    assert "/ai/internal/invoke" in http_paths

    assert "/ws/chat" in websocket_paths
    assert "/ws/smartnotes" in websocket_paths
    assert "/ws/quiz" in websocket_paths
    assert "/ws/podcast" in websocket_paths
    assert "/ws/teaching-video" in websocket_paths


def test_service_app_mounts_only_boundary_routes():
    app = create_service_app("identity")
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert app.state.service_name == "identity"
    assert "/auth/login" in paths
    assert "/auth/internal/resolve" in paths
    assert "/chat" not in paths
    assert "/files" not in paths


def test_ai_core_service_mounts_only_internal_ai_routes():
    app = create_service_app("ai-core")
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert app.state.service_name == "ai-core"
    assert "/ai/internal/invoke" in paths
    assert "/chat" not in paths
    assert "/files" not in paths


def test_bilibili_bridge_starts_only_when_process_owns_it(monkeypatch):
    monkeypatch.delenv("START_BILIBILI_BRIDGE", raising=False)

    assert create_app().state.starts_bilibili_bridge is True
    assert create_service_app("media-generation").state.starts_bilibili_bridge is False

    monkeypatch.setenv("START_BILIBILI_BRIDGE", "true")

    assert create_service_app("media-generation").state.starts_bilibili_bridge is True


def test_gateway_resolves_legacy_http_paths_to_services():
    assert resolve_target("/auth/login", HTTP_ROUTE_TARGETS).service == "identity"
    assert resolve_target("/files", HTTP_ROUTE_TARGETS).service == "asset-library"
    assert resolve_target("/storage/uploads/example.pdf", HTTP_ROUTE_TARGETS).service == "asset-library"
    assert resolve_target("/podcast/download/id/audio.mp3", HTTP_ROUTE_TARGETS).service == "media-generation"
    assert resolve_target("/teaching-videos/abc/video", HTTP_ROUTE_TARGETS).service == "teaching-content"
    assert resolve_target("/unknown", HTTP_ROUTE_TARGETS) is None


def test_gateway_resolves_legacy_websocket_paths_to_services():
    assert resolve_target("/ws/chat", WEBSOCKET_ROUTE_TARGETS).service == "learning-content"
    assert resolve_target("/ws/debate/analyze", WEBSOCKET_ROUTE_TARGETS).service == "learning-content"
    assert resolve_target("/ws/podcast", WEBSOCKET_ROUTE_TARGETS).service == "media-generation"
    assert resolve_target("/ws/teaching-video", WEBSOCKET_ROUTE_TARGETS).service == "teaching-content"
    assert resolve_target("/ws/missing", WEBSOCKET_ROUTE_TARGETS) is None


def test_gateway_builds_upstream_urls():
    assert (
        build_upstream_url("http://learning:5102", "/quiz", "topic=math")
        == "http://learning:5102/quiz?topic=math"
    )
    assert (
        build_upstream_url("http://example.internal/base", "/files/123", "")
        == "http://example.internal/base/files/123"
    )
    assert (
        build_websocket_url("http://learning:5102", "/ws/chat", "chatId=abc")
        == "ws://learning:5102/ws/chat?chatId=abc"
    )
    assert build_health_url("http://identity:5101") == "http://identity:5101/health"


def test_gateway_checks_upstream_health_with_mock_transport():
    import asyncio

    import httpx

    async def run():
        async def handler(request):
            if str(request.url) == "http://identity:5101/health":
                return httpx.Response(200, json={"status": "healthy"})
            return httpx.Response(503, json={"status": "down"})

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await check_upstreams(
                {
                    "identity": "http://identity:5101",
                    "media-generation": "http://media-generation:5104",
                },
                client=client,
            )

        assert result["identity"]["status"] == "healthy"
        assert result["identity"]["statusCode"] == 200
        assert result["media-generation"]["status"] == "unhealthy"
        assert result["media-generation"]["statusCode"] == 503

    asyncio.run(run())


def test_gateway_closes_upstream_client_on_proxy_error(monkeypatch):
    import httpx
    from fastapi.testclient import TestClient
    from core import gateway as gateway_module

    closed = []

    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        def build_request(self, method, url, headers=None, content=None):
            return httpx.Request(method, url, headers=headers, content=content)

        async def send(self, request, stream=False):
            raise httpx.ConnectError("boom", request=request)

        async def aclose(self):
            closed.append(True)

    monkeypatch.setattr(gateway_module.httpx, "AsyncClient", FailingClient)

    app = gateway_module.create_gateway_app()
    response = TestClient(app).get("/auth/login")

    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream request failed"
    assert closed == [True]


def test_remote_auth_boundary_does_not_initialize_auth_db(monkeypatch):
    app = create_service_app("learning-content")
    monkeypatch.setenv("AUTH_VALIDATION_MODE", "remote")

    assert should_initialize_auth_db(app) is False


def test_identity_still_initializes_auth_db_when_remote_mode_is_set(monkeypatch):
    app = create_service_app("identity")
    monkeypatch.setenv("AUTH_VALIDATION_MODE", "remote")

    assert should_initialize_auth_db(app) is True


def test_worker_role_is_reserved_for_worker_entrypoint(monkeypatch):
    assert is_worker_role("worker") is True
    assert is_worker_role("task-worker") is True
    assert is_worker_role("service") is False


def test_worker_app_registers_generation_handlers():
    import worker_app  # noqa: F401
    from core.task_dispatcher import get_task_handlers

    assert {
        "chat",
        "smartnotes",
        "quiz",
        "exam",
        "paper",
        "podcast",
        "teaching_video",
    }.issubset(set(get_task_handlers()))


def test_remote_auth_resolution_skips_local_auth_store(monkeypatch):
    from config import config
    from utils import auth as auth_module
    from utils.auth_contracts import AuthUser

    monkeypatch.setattr(config, "auth_validation_mode", "remote")
    monkeypatch.setattr(
        auth_module,
        "resolve_user_from_identity_service",
        lambda token: AuthUser(id=7, username="remote-user", created_at="2026-06-30T00:00:00"),
    )

    def fail_local_store(token):
        raise AssertionError("local auth store should not be used in remote mode")

    monkeypatch.setattr(auth_module, "resolve_user_from_local_store", fail_local_store)

    user = auth_module.resolve_user_from_token("token")

    assert user is not None
    assert user.username == "remote-user"
