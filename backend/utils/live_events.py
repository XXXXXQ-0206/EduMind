"""Live event helpers for websocket progress streams."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Optional, Protocol

from fastapi import WebSocket

from infrastructure.event_bus import EventBus, get_event_bus


class JsonWebSocket(Protocol):
    async def send_json(self, data: Any) -> None:
        ...


async def publish_live_event(
    channel: str,
    message: dict[str, Any],
    *,
    bus: Optional[EventBus] = None,
) -> None:
    await (bus or get_event_bus()).publish(channel, message)


async def forward_live_events(
    websocket: WebSocket | JsonWebSocket,
    channel: str,
    *,
    bus: Optional[EventBus] = None,
) -> None:
    events = (bus or get_event_bus()).subscribe(channel)
    try:
        async for message in events:
            await websocket.send_json(message)
    finally:
        await events.aclose()


def format_sse_message(message: dict[str, Any], *, event: str | None = None) -> str:
    lines: list[str] = []
    if event:
        lines.append(f"event: {event}")
    data = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    for line in data.splitlines() or [""]:
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


async def stream_live_events_sse(
    channel: str,
    *,
    heartbeat_seconds: float = 15.0,
    bus: Optional[EventBus] = None,
) -> AsyncIterator[str]:
    events = (bus or get_event_bus()).subscribe(channel)
    try:
        while True:
            try:
                message = await asyncio.wait_for(anext(events), timeout=max(1.0, heartbeat_seconds))
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield format_sse_message(message)
    finally:
        await events.aclose()
