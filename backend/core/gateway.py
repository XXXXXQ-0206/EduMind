"""HTTP and WebSocket gateway for extracted service boundaries."""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx
import websockets
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from core.service_registry import SERVICE_BOUNDARIES


DEFAULT_GATEWAY_PORT = 5000
DEFAULT_UPSTREAM_HEALTH_TIMEOUT_SECONDS = 2.0
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


@dataclass(frozen=True)
class RouteTarget:
    prefix: str
    service: str


HTTP_ROUTE_TARGETS: tuple[RouteTarget, ...] = (
    RouteTarget("/auth", "identity"),
    RouteTarget("/chat", "learning-content"),
    RouteTarget("/chats", "learning-content"),
    RouteTarget("/smartnotes", "learning-content"),
    RouteTarget("/quiz", "learning-content"),
    RouteTarget("/quizzes", "learning-content"),
    RouteTarget("/wrongbook", "learning-content"),
    RouteTarget("/flashcards", "learning-content"),
    RouteTarget("/api/companion", "learning-content"),
    RouteTarget("/exam", "learning-content"),
    RouteTarget("/exams", "learning-content"),
    RouteTarget("/debate", "learning-content"),
    RouteTarget("/debates", "learning-content"),
    RouteTarget("/tasks", "learning-content"),
    RouteTarget("/planner", "learning-content"),
    RouteTarget("/files", "asset-library"),
    RouteTarget("/transcriber", "asset-library"),
    RouteTarget("/speaking", "media-generation"),
    RouteTarget("/podcast", "media-generation"),
    RouteTarget("/podcasts", "media-generation"),
    RouteTarget("/api/bilibili", "media-generation"),
    RouteTarget("/slides", "teaching-content"),
    RouteTarget("/lesson-plan", "teaching-content"),
    RouteTarget("/lesson-plans", "teaching-content"),
    RouteTarget("/paper", "teaching-content"),
    RouteTarget("/papers", "teaching-content"),
    RouteTarget("/teaching-video", "teaching-content"),
    RouteTarget("/teaching-videos", "teaching-content"),
    RouteTarget("/storage", "asset-library"),
)

WEBSOCKET_ROUTE_TARGETS: tuple[RouteTarget, ...] = (
    RouteTarget("/ws/chat", "learning-content"),
    RouteTarget("/ws/smartnotes", "learning-content"),
    RouteTarget("/ws/quiz", "learning-content"),
    RouteTarget("/ws/exams", "learning-content"),
    RouteTarget("/ws/debate/analyze", "learning-content"),
    RouteTarget("/ws/debate", "learning-content"),
    RouteTarget("/ws/planner", "learning-content"),
    RouteTarget("/ws/podcast", "media-generation"),
    RouteTarget("/ws/paper", "teaching-content"),
    RouteTarget("/ws/teaching-video", "teaching-content"),
)


def create_gateway_app() -> FastAPI:
    """Create a compatibility API gateway for the extracted services."""

    app = FastAPI(
        title="EduMind API Gateway",
        description="Compatibility gateway for EduMind microservices",
        version="1.0.0",
    )
    app.state.service_urls = build_service_url_map()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    register_gateway_routes(app)
    return app


def build_service_url_map() -> dict[str, str]:
    """Build service URL map from environment variables and default ports."""

    urls: dict[str, str] = {}
    for boundary in SERVICE_BOUNDARIES:
        env_key = f"{boundary.name.upper().replace('-', '_')}_URL"
        default = f"http://127.0.0.1:{boundary.default_port}"
        urls[boundary.name] = os.environ.get(env_key, default).rstrip("/")
    return urls


def upstream_health_timeout_seconds() -> float:
    try:
        return max(
            0.1,
            float(os.environ.get("GATEWAY_HEALTH_TIMEOUT_SECONDS", DEFAULT_UPSTREAM_HEALTH_TIMEOUT_SECONDS)),
        )
    except (TypeError, ValueError):
        return DEFAULT_UPSTREAM_HEALTH_TIMEOUT_SECONDS


def build_health_url(base_url: str) -> str:
    return build_upstream_url(base_url, "/health", "")


async def check_upstream_health(
    service: str,
    base_url: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, object]:
    health_url = build_health_url(base_url)
    close_client = client is None
    active_client = client or httpx.AsyncClient(timeout=upstream_health_timeout_seconds())
    try:
        response = await active_client.get(health_url)
        healthy = 200 <= response.status_code < 400
        return {
            "url": base_url,
            "healthUrl": health_url,
            "status": "healthy" if healthy else "unhealthy",
            "statusCode": response.status_code,
        }
    except Exception as exc:
        return {
            "url": base_url,
            "healthUrl": health_url,
            "status": "unreachable",
            "error": type(exc).__name__,
        }
    finally:
        if close_client:
            await active_client.aclose()


async def check_upstreams(
    service_urls: dict[str, str],
    client: httpx.AsyncClient | None = None,
) -> dict[str, dict[str, object]]:
    checks = await asyncio.gather(
        *[
            check_upstream_health(service, url, client=client)
            for service, url in service_urls.items()
        ]
    )
    return dict(zip(service_urls.keys(), checks))


def resolve_target(path: str, routes: Iterable[RouteTarget]) -> Optional[RouteTarget]:
    """Resolve a path to a service target using longest-prefix matching."""

    normalized = "/" + path.lstrip("/")
    matches = [
        target
        for target in routes
        if normalized == target.prefix or normalized.startswith(f"{target.prefix}/")
    ]
    if not matches:
        return None
    return max(matches, key=lambda target: len(target.prefix))


def register_gateway_routes(app: FastAPI) -> None:
    @app.get("/")
    async def root():
        return {
            "status": "ok",
            "message": "EduMind API Gateway is running",
            "version": "1.0.0",
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "api-gateway",
            "upstreams": app.state.service_urls,
        }

    @app.get("/health/live")
    async def live():
        return {
            "status": "healthy",
            "service": "api-gateway",
        }

    @app.get("/health/ready")
    async def ready():
        upstreams = await check_upstreams(app.state.service_urls)
        is_ready = all(item.get("status") == "healthy" for item in upstreams.values())
        return JSONResponse(
            status_code=200 if is_ready else 503,
            content={
                "status": "ready" if is_ready else "not_ready",
                "service": "api-gateway",
                "upstreams": upstreams,
            },
        )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_http(path: str, request: Request):
        target = resolve_target(f"/{path}", HTTP_ROUTE_TARGETS)
        if not target:
            return Response(
                content=b'{"detail":"No upstream service for path"}',
                media_type="application/json",
                status_code=404,
            )
        return await forward_http_request(request, app.state.service_urls[target.service])

    @app.websocket("/{path:path}")
    async def proxy_websocket(websocket: WebSocket, path: str):
        target = resolve_target(f"/{path}", WEBSOCKET_ROUTE_TARGETS)
        if not target:
            await websocket.close(code=4404, reason="No upstream service for path")
            return
        await forward_websocket(websocket, app.state.service_urls[target.service])


async def forward_http_request(request: Request, upstream_base_url: str) -> Response:
    url = build_upstream_url(upstream_base_url, request.url.path, request.url.query)
    headers = filter_headers(request.headers.items())
    body = await request.body()
    client = httpx.AsyncClient(timeout=None, follow_redirects=False)
    upstream_request = client.build_request(
        request.method,
        url,
        headers=headers,
        content=body,
    )
    try:
        upstream_response = await client.send(upstream_request, stream=True)
    except asyncio.CancelledError:
        await client.aclose()
        raise
    except Exception as exc:
        await client.aclose()
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Upstream request failed",
                "error": type(exc).__name__,
            },
        )
    response_headers = filter_headers(upstream_response.headers.items())
    return StreamingResponse(
        upstream_response.aiter_raw(),
        status_code=upstream_response.status_code,
        headers=response_headers,
        background=BackgroundTask(client.aclose),
    )


def build_upstream_url(base_url: str, path: str, query: str = "") -> str:
    parsed = urlsplit(base_url)
    base_path = parsed.path.rstrip("/")
    full_path = f"{base_path}/{path.lstrip('/')}"
    return urlunsplit((parsed.scheme, parsed.netloc, full_path, query, ""))


def filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }


async def forward_websocket(websocket: WebSocket, upstream_base_url: str) -> None:
    await websocket.accept()
    upstream_url = build_websocket_url(
        upstream_base_url,
        websocket.url.path,
        websocket.url.query,
    )
    headers = filter_headers(websocket.headers.items())

    try:
        async with websockets.connect(upstream_url, extra_headers=headers) as upstream:
            client_to_upstream = asyncio.create_task(pipe_client_to_upstream(websocket, upstream))
            upstream_to_client = asyncio.create_task(pipe_upstream_to_client(websocket, upstream))
            done, pending = await asyncio.wait(
                {client_to_upstream, upstream_to_client},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except Exception as exc:
        try:
            await websocket.close(code=1011, reason=str(exc)[:120])
        except Exception:
            pass


def build_websocket_url(base_url: str, path: str, query: str = "") -> str:
    http_url = build_upstream_url(base_url, path, query)
    parsed = urlsplit(http_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunsplit((scheme, parsed.netloc, parsed.path, parsed.query, ""))


async def pipe_client_to_upstream(websocket: WebSocket, upstream) -> None:
    while True:
        message = await websocket.receive()
        message_type = message.get("type")
        if message_type == "websocket.disconnect":
            await upstream.close()
            return
        if message.get("text") is not None:
            await upstream.send(message["text"])
        elif message.get("bytes") is not None:
            await upstream.send(message["bytes"])


async def pipe_upstream_to_client(websocket: WebSocket, upstream) -> None:
    async for message in upstream:
        if isinstance(message, bytes):
            await websocket.send_bytes(message)
        else:
            await websocket.send_text(message)
