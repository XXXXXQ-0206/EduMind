"""Key-value storage adapters.

PostgreSQL JSONB is the default runtime adapter. JSON-file storage remains as a
legacy/local adapter and as an explicit test fixture when a base directory is
provided.
"""
from __future__ import annotations

import asyncio
import copy
import inspect
import json
import os
import uuid
from collections.abc import Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Optional, Protocol

import aiofiles

from config import config


@dataclass(frozen=True)
class KeyValueItem:
    key: str
    value: Any


JsonUpdater = Callable[[Any], Any | Awaitable[Any]]


async def _apply_update(updater: JsonUpdater, current: Any) -> Any:
    result = updater(current)
    if inspect.isawaitable(result):
        return await result
    return result


def _default_value(default: Any) -> Any:
    return copy.deepcopy(default)


class KeyValueStore(Protocol):
    async def get(self, key: str) -> Optional[Any]:
        ...

    async def set(self, key: str, value: Any) -> None:
        ...

    async def update(self, key: str, updater: JsonUpdater, default: Any = None) -> Any:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def list_prefix(self, prefix: str) -> list[KeyValueItem]:
        ...

    def path_for_key(self, key: str) -> Path:
        ...

    def iter_prefix(self, prefix: str) -> Iterable[Path]:
        ...


class JsonFileKeyValueStore:
    """JSON file-backed key-value store."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or config.storage_dir
        self._update_locks: dict[str, asyncio.Lock] = {}

    async def get(self, key: str) -> Optional[Any]:
        file_path = self.path_for_key(key)
        if not file_path.exists():
            return None
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
                content = await file.read()
            return json.loads(content)
        except Exception:
            return None

    async def set(self, key: str, value: Any) -> None:
        file_path = self.path_for_key(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = file_path.with_name(f".{file_path.name}.{uuid.uuid4().hex}.tmp")
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as file:
            await file.write(json.dumps(value, ensure_ascii=False, indent=2))
        await asyncio.to_thread(os.replace, tmp_path, file_path)

    async def update(self, key: str, updater: JsonUpdater, default: Any = None) -> Any:
        async with self._lock_for_key(key):
            current = await self.get(key)
            if current is None:
                current = _default_value(default)
            next_value = await _apply_update(updater, current)
            await self.set(key, next_value)
            return next_value

    async def delete(self, key: str) -> None:
        file_path = self.path_for_key(key)
        if file_path.exists():
            file_path.unlink()

    async def list_prefix(self, prefix: str) -> list[KeyValueItem]:
        items: list[KeyValueItem] = []
        for file_path in self.iter_prefix(prefix):
            if not file_path.is_file():
                continue
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
                    content = await file.read()
                items.append(KeyValueItem(key=file_path.stem, value=json.loads(content)))
            except Exception:
                continue
        return items

    def path_for_key(self, key: str) -> Path:
        return self.base_dir / f"{sanitize_key(key)}.json"

    def iter_prefix(self, prefix: str) -> Iterable[Path]:
        safe_prefix = sanitize_key(prefix)
        return self.base_dir.glob(f"{safe_prefix}*.json")

    def _lock_for_key(self, key: str) -> asyncio.Lock:
        safe_key = sanitize_key(key)
        lock = self._update_locks.get(safe_key)
        if lock is None:
            lock = asyncio.Lock()
            self._update_locks[safe_key] = lock
        return lock


class RedisKeyValueStore:
    """Redis-backed JSON key-value store."""

    def __init__(self, url: Optional[str] = None, namespace: str = "edumind:kv"):
        try:
            from redis import asyncio as redis_async
        except ImportError as exc:
            raise RuntimeError("KV_STORE_PROVIDER=redis requires the 'redis' package") from exc

        self.namespace = namespace.strip(":")
        self._redis = redis_async.from_url(url or config.redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._redis.get(self._redis_key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    async def set(self, key: str, value: Any) -> None:
        await self._redis.set(self._redis_key(key), json.dumps(value, ensure_ascii=False))

    async def update(self, key: str, updater: JsonUpdater, default: Any = None) -> Any:
        from redis.exceptions import WatchError

        redis_key = self._redis_key(key)
        for attempt in range(25):
            async with self._redis.pipeline() as pipe:
                try:
                    await pipe.watch(redis_key)
                    raw = await pipe.get(redis_key)
                    if raw is None:
                        current = _default_value(default)
                    else:
                        try:
                            current = json.loads(raw)
                        except Exception:
                            current = _default_value(default)
                    next_value = await _apply_update(updater, current)
                    pipe.multi()
                    pipe.set(redis_key, json.dumps(next_value, ensure_ascii=False))
                    await pipe.execute()
                    return next_value
                except WatchError:
                    await asyncio.sleep(min(0.02 * (attempt + 1), 0.25))
                    continue
                finally:
                    await pipe.reset()
        raise RuntimeError(f"Failed to update KV key after concurrent retries: {key}")

    async def delete(self, key: str) -> None:
        await self._redis.delete(self._redis_key(key))

    async def list_prefix(self, prefix: str) -> list[KeyValueItem]:
        items: list[KeyValueItem] = []
        match = f"{self._redis_key(prefix)}*"
        async for redis_key in self._redis.scan_iter(match=match):
            raw = await self._redis.get(redis_key)
            if raw is None:
                continue
            try:
                value = json.loads(raw)
            except Exception:
                continue
            items.append(KeyValueItem(key=self._strip_namespace(redis_key), value=value))
        return items

    def path_for_key(self, key: str) -> Path:
        raise NotImplementedError("RedisKeyValueStore does not expose filesystem paths")

    def iter_prefix(self, prefix: str) -> Iterable[Path]:
        raise NotImplementedError("RedisKeyValueStore does not expose filesystem paths")

    def _redis_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def _strip_namespace(self, key: str) -> str:
        prefix = f"{self.namespace}:"
        return key[len(prefix):] if key.startswith(prefix) else key


class PostgresKeyValueStore:
    """PostgreSQL JSONB key-value store.

    This adapter is intentionally small: it gives the extracted services a
    formal, shared relational backing table while preserving the legacy
    key-value contract used by JSONStorage.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        table_name: str = "edumind_kv",
        connection_factory: Optional[Callable[[], Any]] = None,
    ):
        self.dsn = dsn or config.postgres_dsn
        self.table_name = validate_sql_identifier(table_name)
        self._connection_factory = connection_factory
        self._schema_lock = asyncio.Lock()
        self._schema_ready = False

    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_schema()
        async with self._connection() as conn:
            cursor = await conn.execute(
                f"SELECT value FROM {self.table_name} WHERE key = %s",
                (key,),
            )
            row = await cursor.fetchone()
            return self._row_value(row)

    async def set(self, key: str, value: Any) -> None:
        await self._ensure_schema()
        async with self._connection() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (key, value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = now()
                """,
                (key, self._json_param(value)),
            )
            await self._commit(conn)

    async def update(self, key: str, updater: JsonUpdater, default: Any = None) -> Any:
        await self._ensure_schema()
        async with self._connection() as conn:
            async with conn.transaction():
                await conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))
                cursor = await conn.execute(
                    f"SELECT value FROM {self.table_name} WHERE key = %s FOR UPDATE",
                    (key,),
                )
                row = await cursor.fetchone()
                current = self._row_value(row)
                if current is None:
                    current = _default_value(default)
                next_value = await _apply_update(updater, current)
                await conn.execute(
                    f"""
                    INSERT INTO {self.table_name} (key, value, updated_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT (key)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = now()
                    """,
                    (key, self._json_param(next_value)),
                )
                return next_value

    async def delete(self, key: str) -> None:
        await self._ensure_schema()
        async with self._connection() as conn:
            await conn.execute(f"DELETE FROM {self.table_name} WHERE key = %s", (key,))
            await self._commit(conn)

    async def list_prefix(self, prefix: str) -> list[KeyValueItem]:
        await self._ensure_schema()
        async with self._connection() as conn:
            cursor = await conn.execute(
                f"""
                SELECT key, value
                FROM {self.table_name}
                WHERE left(key, length(%s)) = %s
                ORDER BY key
                """,
                (prefix, prefix),
            )
            rows = await cursor.fetchall()
            return [
                KeyValueItem(key=str(self._row_field(row, "key", 0)), value=self._row_field(row, "value", 1))
                for row in rows
            ]

    def path_for_key(self, key: str) -> Path:
        raise NotImplementedError("PostgresKeyValueStore does not expose filesystem paths")

    def iter_prefix(self, prefix: str) -> Iterable[Path]:
        raise NotImplementedError("PostgresKeyValueStore does not expose filesystem paths")

    async def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        async with self._schema_lock:
            if self._schema_ready:
                return
            async with self._connection() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        key text PRIMARY KEY,
                        value jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                await self._commit(conn)
            self._schema_ready = True

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[Any]:
        if self._connection_factory is not None:
            async with self._connection_factory() as conn:
                yield conn
            return

        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("KV_STORE_PROVIDER=postgres requires the 'psycopg' package") from exc

        conn = await psycopg.AsyncConnection.connect(self.dsn, row_factory=dict_row)
        try:
            yield conn
        finally:
            await conn.close()

    async def _commit(self, conn: Any) -> None:
        commit = getattr(conn, "commit", None)
        if commit is not None:
            result = commit()
            if inspect.isawaitable(result):
                await result

    def _json_param(self, value: Any) -> Any:
        if self._connection_factory is not None:
            return value
        try:
            from psycopg.types.json import Jsonb

            return Jsonb(value)
        except ImportError:
            return value

    def _row_value(self, row: Any) -> Optional[Any]:
        if row is None:
            return None
        return self._row_field(row, "value", 0)

    def _row_field(self, row: Any, name: str, index: int) -> Any:
        if isinstance(row, dict):
            return row.get(name)
        return row[index]


def sanitize_key(key: str) -> str:
    safe_key = key
    for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        safe_key = safe_key.replace(char, "_")
    return safe_key


def validate_sql_identifier(identifier: str) -> str:
    if not identifier or not identifier.replace("_", "").isalnum() or identifier[0].isdigit():
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier


def create_kv_store(base_dir: Optional[Path] = None) -> KeyValueStore:
    if base_dir is not None:
        return JsonFileKeyValueStore(base_dir=base_dir)

    provider = (config.kv_store_provider or "postgres").strip().lower()
    if provider == "json":
        return JsonFileKeyValueStore(base_dir=base_dir)
    if provider == "redis":
        return RedisKeyValueStore()
    if provider in {"postgres", "postgresql", "pg"}:
        return PostgresKeyValueStore()
    raise ValueError(f"Unsupported KV_STORE_PROVIDER: {provider}")
