"""Task lease adapters for cross-process generation de-duplication."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from config import config
from infrastructure.kv_store import KeyValueStore, create_kv_store


@dataclass(frozen=True)
class TaskLease:
    name: str
    key: str
    owner: str


class TaskLeaseProvider(Protocol):
    async def acquire(self, name: str, ttl_seconds: Optional[int] = None) -> Optional[TaskLease]:
        ...

    async def release(self, lease: TaskLease) -> None:
        ...


class KeyValueTaskLeaseProvider:
    """KV-backed lease provider used for local development.

    The JSON-file provider is best-effort and not a substitute for Redis in a
    horizontally scaled deployment, but it gives every route one lease contract.
    """

    def __init__(self, base_dir: Optional[Path] = None, store: Optional[KeyValueStore] = None):
        self.store = store or create_kv_store(base_dir=base_dir)

    async def acquire(self, name: str, ttl_seconds: Optional[int] = None) -> Optional[TaskLease]:
        ttl = int(ttl_seconds or config.task_lease_ttl_seconds)
        now = time.time()
        key = _lease_key(name)
        existing = await self.store.get(key)
        if isinstance(existing, dict) and float(existing.get("expires_at") or 0) > now:
            return None

        owner = uuid.uuid4().hex
        await self.store.set(key, {"owner": owner, "expires_at": now + ttl})
        confirmed = await self.store.get(key)
        if isinstance(confirmed, dict) and confirmed.get("owner") == owner:
            return TaskLease(name=name, key=key, owner=owner)
        return None

    async def release(self, lease: TaskLease) -> None:
        existing = await self.store.get(lease.key)
        if isinstance(existing, dict) and existing.get("owner") == lease.owner:
            await self.store.delete(lease.key)


class RedisTaskLeaseProvider:
    """Redis-backed atomic lease provider."""

    def __init__(self, url: Optional[str] = None):
        try:
            from redis import asyncio as redis_async
        except ImportError as exc:
            raise RuntimeError("TASK_LEASE_PROVIDER=redis requires the 'redis' package") from exc

        self._redis_async = redis_async
        self._url = url or config.redis_url

    async def acquire(self, name: str, ttl_seconds: Optional[int] = None) -> Optional[TaskLease]:
        ttl = int(ttl_seconds or config.task_lease_ttl_seconds)
        key = _lease_key(name)
        owner = uuid.uuid4().hex
        redis = self._redis_async.from_url(self._url, decode_responses=True)
        try:
            ok = await redis.set(key, owner, nx=True, ex=ttl)
            if ok:
                return TaskLease(name=name, key=key, owner=owner)
            return None
        finally:
            await redis.aclose()

    async def release(self, lease: TaskLease) -> None:
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        end
        return 0
        """
        redis = self._redis_async.from_url(self._url, decode_responses=True)
        try:
            await redis.eval(script, 1, lease.key, lease.owner)
        finally:
            await redis.aclose()


_provider: TaskLeaseProvider | None = None


def get_task_lease_provider() -> TaskLeaseProvider:
    global _provider
    if _provider is not None:
        return _provider

    provider = (config.task_lease_provider or "kv").strip().lower()
    if provider == "kv":
        _provider = KeyValueTaskLeaseProvider()
    elif provider == "redis":
        _provider = RedisTaskLeaseProvider()
    else:
        raise ValueError(f"Unsupported TASK_LEASE_PROVIDER: {provider}")
    return _provider


async def acquire_task_lease(name: str, ttl_seconds: Optional[int] = None) -> Optional[TaskLease]:
    return await get_task_lease_provider().acquire(name, ttl_seconds=ttl_seconds)


async def release_task_lease(lease: Optional[TaskLease]) -> None:
    if lease is not None:
        await get_task_lease_provider().release(lease)


def _lease_key(name: str) -> str:
    return f"task_lease:{name}"
