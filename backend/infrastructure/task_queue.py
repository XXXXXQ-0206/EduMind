"""Task queue adapters for durable generation runners."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, Protocol

from config import config


@dataclass(frozen=True)
class TaskEnvelope:
    kind: str
    id: str
    attempts: int = 0
    max_attempts: int = 3
    error: Optional[str] = None
    raw: Optional[str] = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "id": self.id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
        }
        if self.error:
            payload["error"] = self.error
        return payload


class TaskQueue(Protocol):
    async def enqueue(self, task: TaskEnvelope) -> None:
        ...

    async def dequeue(self, timeout_seconds: int = 5) -> Optional[TaskEnvelope]:
        ...

    async def ack(self, task: TaskEnvelope) -> None:
        ...

    async def fail(self, task: TaskEnvelope, error: str) -> None:
        ...


class InlineTaskQueue:
    """No-op queue used when API processes run their runners inline."""

    async def enqueue(self, task: TaskEnvelope) -> None:
        return None

    async def dequeue(self, timeout_seconds: int = 5) -> Optional[TaskEnvelope]:
        return None

    async def ack(self, task: TaskEnvelope) -> None:
        return None

    async def fail(self, task: TaskEnvelope, error: str) -> None:
        return None


class RedisTaskQueue:
    """Redis list-backed task queue with processing and dead-letter lists."""

    def __init__(self, url: Optional[str] = None, queue_name: Optional[str] = None):
        try:
            from redis import asyncio as redis_async
        except ImportError as exc:
            raise RuntimeError("TASK_QUEUE_PROVIDER=redis requires the 'redis' package") from exc

        self.queue_name = queue_name or config.task_queue_name
        self.processing_name = f"{self.queue_name}:processing"
        self.dead_letter_name = f"{self.queue_name}:dead"
        self._redis = redis_async.from_url(url or config.redis_url, decode_responses=True)

    async def enqueue(self, task: TaskEnvelope) -> None:
        await self._redis.rpush(self.queue_name, json.dumps(task.as_dict(), ensure_ascii=False))

    async def dequeue(self, timeout_seconds: int = 5) -> Optional[TaskEnvelope]:
        raw = await self._redis.brpoplpush(
            self.queue_name,
            self.processing_name,
            timeout=max(1, int(timeout_seconds)),
        )
        if not raw:
            return None
        return self._decode(raw)

    async def ack(self, task: TaskEnvelope) -> None:
        if task.raw:
            await self._redis.lrem(self.processing_name, 1, task.raw)

    async def fail(self, task: TaskEnvelope, error: str) -> None:
        if task.raw:
            await self._redis.lrem(self.processing_name, 1, task.raw)
        failed = TaskEnvelope(
            kind=task.kind,
            id=task.id,
            attempts=task.attempts + 1,
            max_attempts=task.max_attempts,
            error=error,
        )
        payload = json.dumps(failed.as_dict(), ensure_ascii=False)
        if failed.attempts >= failed.max_attempts:
            await self._redis.rpush(self.dead_letter_name, payload)
        else:
            await self._redis.lpush(self.queue_name, payload)

    def _decode(self, raw: str) -> Optional[TaskEnvelope]:
        try:
            payload = json.loads(raw)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        kind = str(payload.get("kind") or "").strip()
        task_id = str(payload.get("id") or "").strip()
        if not kind or not task_id:
            return None
        try:
            attempts = int(payload.get("attempts") or 0)
        except Exception:
            attempts = 0
        try:
            max_attempts = int(payload.get("max_attempts") or 3)
        except Exception:
            max_attempts = 3
        return TaskEnvelope(
            kind=kind,
            id=task_id,
            attempts=max(0, attempts),
            max_attempts=max(1, max_attempts),
            error=str(payload.get("error") or "") or None,
            raw=raw,
        )


def create_task_queue() -> TaskQueue:
    provider = (config.task_queue_provider or "inline").strip().lower()
    if provider in {"inline", "memory", "none"}:
        return InlineTaskQueue()
    if provider == "redis":
        return RedisTaskQueue()
    raise ValueError(f"Unsupported TASK_QUEUE_PROVIDER: {provider}")
