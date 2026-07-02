"""Live event helpers for websocket progress streams."""
from __future__ import annotations

import asyncio
import json
from contextlib import suppress
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
    next_event_task: asyncio.Task[dict[str, Any]] | None = None
    try:
        while True:
            if next_event_task is None:
                next_event_task = asyncio.create_task(anext(events))
            done, _ = await asyncio.wait({next_event_task}, timeout=max(1.0, heartbeat_seconds))
            if not done:
                yield ": keep-alive\n\n"
                continue
            try:
                message = next_event_task.result()
            except StopAsyncIteration:
                return
            finally:
                next_event_task = None
            yield format_sse_message(message)
    finally:
        if next_event_task is not None and not next_event_task.done():
            next_event_task.cancel()
            with suppress(asyncio.CancelledError, StopAsyncIteration):
                await next_event_task
        await events.aclose()
