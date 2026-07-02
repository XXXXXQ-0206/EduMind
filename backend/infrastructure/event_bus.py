"""Task event bus adapters.

The in-memory adapter is intentionally small and local. It gives long-running
generation routes a shared contract that can be replaced with Redis Pub/Sub or
another broker once the deployment is ready for cross-process progress streams.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any, AsyncIterator, DefaultDict, Protocol

from config import config


class EventBus(Protocol):
    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        ...

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        ...


class InMemoryEventBus:
    """Process-local event bus used by default."""

    def __init__(self):
        self._subscribers: DefaultDict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        for queue in list(self._subscribers[channel]):
            await queue.put(payload)

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[channel].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers[channel].remove(queue)


class RedisEventBus:
    """Redis Pub/Sub-backed event bus for cross-process websocket streams."""

    def __init__(self, url: str | None = None):
        try:
            from redis import asyncio as redis_async
        except ImportError as exc:
            raise RuntimeError("EVENT_BUS_PROVIDER=redis requires the 'redis' package") from exc

        self._redis_async = redis_async
        self._url = url or config.redis_url

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        redis = self._redis_async.from_url(self._url, decode_responses=True)
        try:
            await redis.publish(channel, json.dumps(payload, ensure_ascii=False))
        finally:
            await redis.aclose()

    async def subscribe(self, channel: str) -> AsyncIterator[dict[str, Any]]:
        redis = self._redis_async.from_url(self._url, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                raw = message.get("data")
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    yield payload
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis.aclose()


_local_event_bus = InMemoryEventBus()
_redis_event_bus: RedisEventBus | None = None


def get_event_bus() -> EventBus:
    global _redis_event_bus
    provider = (config.event_bus_provider or "memory").strip().lower()
    if provider == "memory":
        return _local_event_bus
    if provider == "redis":
        if _redis_event_bus is None:
            _redis_event_bus = RedisEventBus()
        return _redis_event_bus
    raise ValueError(f"Unsupported EVENT_BUS_PROVIDER: {provider}")
