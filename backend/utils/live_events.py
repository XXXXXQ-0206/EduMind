"""Live event helpers for websocket progress streams."""
from __future__ import annotations

from typing import Any, Optional, Protocol

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
