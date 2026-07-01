import asyncio
import copy
import json
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from infrastructure import kv_store as kv_module  # noqa: E402
from infrastructure.event_bus import InMemoryEventBus  # noqa: E402
from infrastructure.kv_store import JsonFileKeyValueStore, PostgresKeyValueStore, sanitize_key  # noqa: E402
from infrastructure.object_store import LocalObjectStore, normalize_object_key  # noqa: E402
from infrastructure.task_queue import InlineTaskQueue, RedisTaskQueue, TaskEnvelope  # noqa: E402
from infrastructure.task_lease import KeyValueTaskLeaseProvider  # noqa: E402
from scripts.migrate_storage_to_adapters import (  # noqa: E402
    iter_legacy_kv_files,
    iter_legacy_object_files,
    iter_legacy_vector_files,
    restore_legacy_kv_key,
    run_migration,
)
from utils import storage as storage_module  # noqa: E402
from utils.feature_support import build_selected_files_context, extract_file_text_from_meta  # noqa: E402
from utils.live_events import (  # noqa: E402
    format_sse_message,
    forward_live_events,
    publish_live_event,
    stream_live_events_sse,
)
from utils.storage import JSONStorage  # noqa: E402
from utils.storage import VectorStore  # noqa: E402
from utils.auth_db import AuthDatabase  # noqa: E402
from utils.upload_objects import upload_object_key_from_meta  # noqa: E402


def test_kv_store_sanitizes_legacy_json_keys():
    assert sanitize_key("quiz:abc/attempts") == "quiz_abc_attempts"


def test_json_file_kv_store_round_trips_values(tmp_path):
    async def run():
        store = JsonFileKeyValueStore(base_dir=tmp_path)
        await store.set("quiz:abc", {"ok": True, "items": [1]})
        await store.set("quiz:abc:attempts", [{"score": 1}])

        assert await store.get("quiz:abc") == {"ok": True, "items": [1]}
        assert store.path_for_key("quiz:abc") == tmp_path / "quiz_abc.json"
        items = await store.list_prefix("quiz:")
        assert {item.key for item in items} == {"quiz_abc", "quiz_abc_attempts"}

        await store.delete("quiz:abc")
        assert await store.get("quiz:abc") is None

    asyncio.run(run())


def test_json_file_kv_store_update_merges_concurrent_writes(tmp_path):
    async def run():
        store = JsonFileKeyValueStore(base_dir=tmp_path)

        async def append_value(value):
            async def updater(current):
                items = list(current or [])
                await asyncio.sleep(0)
                items.append(value)
                return items

            return await store.update("shared:list", updater, default=[])

        await asyncio.gather(*(append_value(index) for index in range(20)))

        assert sorted(await store.get("shared:list")) == list(range(20))

    asyncio.run(run())


class FakePostgresCursor:
    def __init__(self, rows=None):
        self.rows = rows or []

    async def fetchone(self):
        return self.rows[0] if self.rows else None

    async def fetchall(self):
        return self.rows


class FakePostgresTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakePostgresConnection:
    def __init__(self, data, executed):
        self.data = data
        self.executed = executed
        self.commits = 0

    async def execute(self, sql, params=()):
        normalized = " ".join(sql.lower().split())
        self.executed.append((sql, params))
        if normalized.startswith("create table"):
            return FakePostgresCursor()
        if "pg_advisory_xact_lock" in normalized:
            return FakePostgresCursor()
        if normalized.startswith("select value from"):
            key = params[0]
            if key not in self.data:
                return FakePostgresCursor()
            return FakePostgresCursor([{"value": copy.deepcopy(self.data[key])}])
        if normalized.startswith("insert into"):
            key, value = params
            self.data[key] = copy.deepcopy(unwrap_json_param(value))
            return FakePostgresCursor()
        if normalized.startswith("delete from"):
            self.data.pop(params[0], None)
            return FakePostgresCursor()
        if normalized.startswith("select key, value"):
            prefix = params[0]
            rows = [
                {"key": key, "value": copy.deepcopy(value)}
                for key, value in sorted(self.data.items())
                if key.startswith(prefix)
            ]
            return FakePostgresCursor(rows)
        raise AssertionError(f"unexpected SQL: {sql}")

    async def commit(self):
        self.commits += 1

    def transaction(self):
        return FakePostgresTransaction()


class FakePostgresConnectionContext:
    def __init__(self, data, executed):
        self.connection = FakePostgresConnection(data, executed)

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def unwrap_json_param(value):
    return getattr(value, "obj", getattr(value, "_obj", value))


def test_postgres_kv_store_round_trips_values_with_formal_jsonb_model():
    async def run():
        data = {}
        executed = []
        store = PostgresKeyValueStore(
            dsn="postgresql://unit-test",
            connection_factory=lambda: FakePostgresConnectionContext(data, executed),
        )

        await store.set("quiz:one", {"score": 1})
        assert await store.get("quiz:one") == {"score": 1}

        updated = await store.update(
            "quiz:one",
            lambda current: {"score": int(current["score"]) + 1},
            default={"score": 0},
        )
        assert updated == {"score": 2}
        assert await store.get("quiz:one") == {"score": 2}

        await store.set("quiz:two", {"score": 3})
        items = await store.list_prefix("quiz:")
        assert [(item.key, item.value) for item in items] == [
            ("quiz:one", {"score": 2}),
            ("quiz:two", {"score": 3}),
        ]

        await store.delete("quiz:one")
        assert await store.get("quiz:one") is None

        sql_statements = "\n".join(statement for statement, _params in executed)
        assert "CREATE TABLE IF NOT EXISTS edumind_kv" in sql_statements
        assert "value jsonb NOT NULL" in sql_statements
        assert "FOR UPDATE" in sql_statements
        assert "pg_advisory_xact_lock" in sql_statements

    asyncio.run(run())


def test_create_kv_store_supports_postgres_provider(monkeypatch):
    class FakePostgresStore:
        pass

    monkeypatch.setattr(config, "kv_store_provider", "postgres")
    monkeypatch.setattr(kv_module, "PostgresKeyValueStore", FakePostgresStore)

    assert isinstance(kv_module.create_kv_store(), FakePostgresStore)


class FakeSyncConnectionContext:
    def __init__(self, executed):
        self.executed = executed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        return self


def test_auth_database_uses_postgres_tables_and_jsonb():
    executed = []
    database = AuthDatabase(
        dsn="postgresql://unit-test",
        table_prefix="unit_auth",
        connection_factory=lambda: FakeSyncConnectionContext(executed),
    )

    database._ensure_schema()

    sql_statements = "\n".join(statement for statement, _params in executed)
    assert "CREATE TABLE IF NOT EXISTS unit_auth_users" in sql_statements
    assert "CREATE TABLE IF NOT EXISTS unit_auth_chats" in sql_statements
    assert "material_ids jsonb NOT NULL" in sql_statements
    assert "REFERENCES unit_auth_users(id) ON DELETE CASCADE" in sql_statements


class FakeVectorTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeVectorConnection:
    def __init__(self, executed):
        self.executed = executed
        self.commits = 0

    async def execute(self, sql, params=()):
        self.executed.append((sql, params))
        return FakePostgresCursor()

    async def commit(self):
        self.commits += 1

    def transaction(self):
        return FakeVectorTransaction()


class FakeVectorConnectionContext:
    def __init__(self, executed):
        self.connection = FakeVectorConnection(executed)

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def test_vector_store_initializes_pgvector_schema():
    async def run():
        executed = []
        store = VectorStore(
            "unit",
            dsn="postgresql://unit-test",
            table_name="unit_vectors",
            connection_factory=lambda: FakeVectorConnectionContext(executed),
        )

        await store._ensure_schema()

        sql_statements = "\n".join(statement for statement, _params in executed)
        assert "CREATE EXTENSION IF NOT EXISTS vector" in sql_statements
        assert "CREATE TABLE IF NOT EXISTS unit_vectors" in sql_statements
        assert "embedding vector NOT NULL" in sql_statements
        assert store._vector_literal([0.1, 2, -3.5]) == "[0.1,2,-3.5]"

    asyncio.run(run())


def test_json_storage_update_returns_updated_value(tmp_path):
    async def run():
        storage = JSONStorage(base_dir=tmp_path)

        updated = await storage.update(
            "counter",
            lambda current: {"count": int((current or {}).get("count") or 0) + 1},
            default={"count": 0},
        )

        assert updated == {"count": 1}
        assert await storage.get("counter") == {"count": 1}

    asyncio.run(run())


def test_json_storage_preserves_existing_adapter_contract(tmp_path):
    async def run():
        storage = JSONStorage(base_dir=tmp_path)
        await storage.set("note:one:notes", {"title": "demo"})

        assert await storage.get("note:one:notes") == {"title": "demo"}
        assert await storage.list_values("note:") == [{"title": "demo"}]
        assert storage._get_file_path("note:one:notes") == tmp_path / "note_one_notes.json"

    asyncio.run(run())


def test_list_chats_uses_kv_prefix_listing(tmp_path):
    async def run():
        original_storage = storage_module.json_storage
        storage_module.json_storage = JSONStorage(base_dir=tmp_path)
        try:
            await storage_module.json_storage.set(
                "chat:alpha",
                {
                    "id": "alpha",
                    "title": "Algebra help",
                    "scope": "student",
                    "created_at": "2026-06-30T10:00:00",
                    "updated_at": "2026-06-30T10:01:00",
                },
            )
            await storage_module.json_storage.set(
                "chat:alpha:messages",
                [{"role": "assistant", "content": "quadratic formula"}],
            )
            await storage_module.json_storage.set("chat:alpha:length", "Short")

            results = await storage_module.list_chats(query="quadratic", scope="student")

            assert [item["id"] for item in results] == ["alpha"]
            assert results[0]["at"] > 0
        finally:
            storage_module.json_storage = original_storage

    asyncio.run(run())


def test_local_object_store_writes_urls_and_deletes(tmp_path):
    async def run():
        store = LocalObjectStore(base_dir=tmp_path, public_base_url="/storage")
        url = await store.put_bytes("uploads/example.txt", b"hello")
        source = tmp_path / "source.bin"
        source.write_bytes(b"from-file")
        file_url = await store.put_file("uploads/source.bin", source)
        await store.put_bytes("uploads/nested/one.txt", b"one")
        await store.put_bytes("uploads/nested/two.txt", b"two")
        await store.put_bytes("uploads/keep.txt", b"keep")

        assert normalize_object_key("\\uploads\\example.txt") == "uploads/example.txt"
        assert url == "/storage/uploads/example.txt"
        assert file_url == "/storage/uploads/source.bin"
        assert store.path_for("uploads/example.txt").read_bytes() == b"hello"
        assert await store.get_bytes("uploads/source.bin") == b"from-file"

        await store.delete("uploads/example.txt")
        assert not store.path_for("uploads/example.txt").exists()
        await store.delete_prefix("uploads/nested")
        assert not store.path_for("uploads/nested").exists()
        assert store.path_for("uploads/keep.txt").exists()

    asyncio.run(run())


def test_upload_metadata_prefers_object_key_for_text_extraction(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        upload_path = tmp_path / "uploads" / "planner-note.txt"
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        upload_path.write_text("source", encoding="utf-8")
        Path(str(upload_path) + ".txt").write_text("sidecar text", encoding="utf-8")

        meta = {
            "filename": "legacy-name.txt",
            "objectKey": "uploads/planner-note.txt",
            "url": "/storage/uploads/planner-note.txt",
        }

        assert upload_object_key_from_meta(meta) == "uploads/planner-note.txt"
        assert await extract_file_text_from_meta(meta) == "sidecar text"

    asyncio.run(run())


def test_selected_files_context_uses_object_keys(tmp_path, monkeypatch):
    async def run():
        monkeypatch.setattr(config, "storage_dir", tmp_path)
        upload_path = tmp_path / "uploads" / "lesson.txt"
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        upload_path.write_text("source", encoding="utf-8")
        Path(str(upload_path) + ".txt").write_text("selected context", encoding="utf-8")

        context = await build_selected_files_context(
            [
                {
                    "id": "one",
                    "originalName": "lesson.txt",
                    "objectKey": "uploads/lesson.txt",
                    "filename": "legacy.txt",
                }
            ],
            ["one"],
        )

        assert "lesson.txt" in context
        assert "selected context" in context

    asyncio.run(run())


def test_in_memory_event_bus_delivers_events():
    async def run():
        bus = InMemoryEventBus()
        events = bus.subscribe("task:one")
        first = asyncio.create_task(anext(events))
        await asyncio.sleep(0)

        await bus.publish("task:one", {"phase": "ready"})

        assert await asyncio.wait_for(first, timeout=1) == {"phase": "ready"}
        await events.aclose()

    asyncio.run(run())


def test_kv_task_lease_serializes_generation(tmp_path):
    async def run():
        provider = KeyValueTaskLeaseProvider(base_dir=tmp_path)
        first = await provider.acquire("quiz:one", ttl_seconds=60)
        assert first is not None

        assert await provider.acquire("quiz:one", ttl_seconds=60) is None

        await provider.release(first)
        second = await provider.acquire("quiz:one", ttl_seconds=60)
        assert second is not None
        await provider.release(second)

    asyncio.run(run())


def test_inline_task_queue_is_noop():
    async def run():
        queue = InlineTaskQueue()
        await queue.enqueue(TaskEnvelope(kind="chat", id="one"))
        assert await queue.dequeue(timeout_seconds=1) is None

    asyncio.run(run())


def test_task_envelope_serializes_retry_metadata():
    task = TaskEnvelope(kind="quiz", id="one", attempts=2, max_attempts=5, error="boom")

    assert task.as_dict() == {
        "kind": "quiz",
        "id": "one",
        "attempts": 2,
        "max_attempts": 5,
        "error": "boom",
    }


def test_redis_task_queue_decode_preserves_retry_metadata():
    queue = RedisTaskQueue.__new__(RedisTaskQueue)
    raw = json.dumps(
        {
            "kind": "quiz",
            "id": "one",
            "attempts": 2,
            "max_attempts": 5,
            "error": "boom",
        }
    )

    task = queue._decode(raw)

    assert task == TaskEnvelope(
        kind="quiz",
        id="one",
        attempts=2,
        max_attempts=5,
        error="boom",
        raw=raw,
    )


def test_redis_task_queue_fail_retries_then_dead_letters():
    class FakeRedis:
        def __init__(self):
            self.removed = []
            self.retried = []
            self.dead = []

        async def lrem(self, name, count, raw):
            self.removed.append((name, count, raw))

        async def lpush(self, name, raw):
            self.retried.append((name, raw))

        async def rpush(self, name, raw):
            self.dead.append((name, raw))

    async def run():
        redis = FakeRedis()
        queue = RedisTaskQueue.__new__(RedisTaskQueue)
        queue.queue_name = "edumind:tasks"
        queue.processing_name = "edumind:tasks:processing"
        queue.dead_letter_name = "edumind:tasks:dead"
        queue._redis = redis

        await queue.fail(
            TaskEnvelope(kind="quiz", id="one", attempts=1, max_attempts=3, raw="raw-one"),
            "temporary",
        )
        await queue.fail(
            TaskEnvelope(kind="quiz", id="two", attempts=2, max_attempts=3, raw="raw-two"),
            "fatal",
        )

        assert redis.removed == [
            ("edumind:tasks:processing", 1, "raw-one"),
            ("edumind:tasks:processing", 1, "raw-two"),
        ]
        retried = json.loads(redis.retried[0][1])
        dead = json.loads(redis.dead[0][1])
        assert redis.retried[0][0] == "edumind:tasks"
        assert retried["attempts"] == 2
        assert retried["error"] == "temporary"
        assert redis.dead[0][0] == "edumind:tasks:dead"
        assert dead["attempts"] == 3
        assert dead["error"] == "fatal"

    asyncio.run(run())


def test_task_worker_acknowledges_success_and_fails_unknown_tasks(monkeypatch):
    from core import task_dispatcher

    class FakeQueue:
        def __init__(self, stop_event):
            self.stop_event = stop_event
            self.tasks = [
                TaskEnvelope(kind="unit-success", id="one"),
                TaskEnvelope(kind="unit-missing", id="two"),
            ]
            self.acked = []
            self.failed = []

        async def dequeue(self, timeout_seconds=5):
            if self.tasks:
                return self.tasks.pop(0)
            self.stop_event.set()
            return None

        async def enqueue(self, task):
            raise AssertionError("worker should not enqueue")

        async def ack(self, task):
            self.acked.append(task)

        async def fail(self, task, error):
            self.failed.append((task, error))

    async def run():
        stop_event = asyncio.Event()
        queue = FakeQueue(stop_event)
        handled = []

        async def handler(task_id):
            handled.append(task_id)

        task_dispatcher.register_task_handler("unit-success", handler)
        monkeypatch.setattr(task_dispatcher, "create_task_queue", lambda: queue)

        await task_dispatcher.run_task_worker(stop_event=stop_event)

        assert handled == ["one"]
        assert [task.id for task in queue.acked] == ["one"]
        assert [(task.id, error) for task, error in queue.failed] == [
            ("two", "unknown task kind: unit-missing")
        ]

    asyncio.run(run())


def test_dispatch_generation_task_uses_celery_provider(monkeypatch):
    from core import task_dispatcher

    async def run():
        calls = []

        async def fake_enqueue(kind, task_id):
            calls.append((kind, task_id))

        async def inline_starter(task_id):
            raise AssertionError("celery provider should not start inline")

        monkeypatch.setattr(config, "task_queue_provider", "celery")
        monkeypatch.setattr(task_dispatcher, "enqueue_celery_generation_task", fake_enqueue)

        await task_dispatcher.dispatch_generation_task("quiz", "one", inline_starter)

        assert calls == [("quiz", "one")]

    asyncio.run(run())


def test_live_event_forwarder_sends_websocket_json():
    class FakeWebSocket:
        def __init__(self):
            self.messages = asyncio.Queue()

        async def send_json(self, data):
            await self.messages.put(data)

    async def run():
        bus = InMemoryEventBus()
        websocket = FakeWebSocket()
        forwarder = asyncio.create_task(forward_live_events(websocket, "planner:user:1", bus=bus))
        await asyncio.sleep(0)

        await publish_live_event("planner:user:1", {"type": "ready"}, bus=bus)

        assert await asyncio.wait_for(websocket.messages.get(), timeout=1) == {"type": "ready"}
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass

    asyncio.run(run())


def test_sse_message_format_is_parseable_json():
    message = format_sse_message({"type": "ready", "text": "你好"})

    assert message.endswith("\n\n")
    first_line = message.splitlines()[0]
    assert first_line.startswith("data: ")
    assert json.loads(first_line.removeprefix("data: ")) == {"type": "ready", "text": "你好"}


def test_sse_stream_yields_published_events():
    async def run():
        bus = InMemoryEventBus()
        stream = stream_live_events_sse("task:one", heartbeat_seconds=10, bus=bus)
        first = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)

        await bus.publish("task:one", {"type": "phase", "value": "generating"})

        chunk = await asyncio.wait_for(first, timeout=1)
        assert json.loads(chunk.splitlines()[0].removeprefix("data: ")) == {
            "type": "phase",
            "value": "generating",
        }
        await stream.aclose()

    asyncio.run(run())


def test_storage_migration_restores_legacy_kv_keys():
    assert restore_legacy_kv_key("note_abc_payload") == "note:abc:payload"
    assert restore_legacy_kv_key("podcast_pid_script") == "podcast:pid:script"
    assert restore_legacy_kv_key("files_teacher_user_2") == "files_teacher:user:2"
    assert restore_legacy_kv_key("planner_tasks_user_7") == "planner:tasks:user:7"
    assert restore_legacy_kv_key("debate_debate-id_analysis") == "debate:debate-id:analysis"
    assert restore_legacy_kv_key("flashcard_deck_deck-id") == "flashcard_deck:deck-id"
    assert restore_legacy_kv_key("speaking_history") == "speaking:history"


def test_storage_migration_scans_kv_and_object_files(tmp_path):
    (tmp_path / "note_abc_payload.json").write_text('{"topic":"math"}', encoding="utf-8")
    (tmp_path / "vectors_lesson.json").write_text(
        '{"texts":["algebra"],"vectors":[[0.1,0.2]],"metadatas":[{"source":"unit"}]}',
        encoding="utf-8",
    )
    (tmp_path / "edumind.sqlite3").write_bytes(b"sqlite")
    upload = tmp_path / "uploads" / "lesson.txt"
    upload.parent.mkdir(parents=True)
    upload.write_text("lesson", encoding="utf-8")
    cache_file = tmp_path / "cache" / "ignore.bin"
    cache_file.parent.mkdir()
    cache_file.write_bytes(b"cache")

    kv_items = list(iter_legacy_kv_files(tmp_path))
    vector_items = list(iter_legacy_vector_files(tmp_path))
    object_items = list(iter_legacy_object_files(tmp_path))

    assert kv_items == [("note:abc:payload", tmp_path / "note_abc_payload.json")]
    assert vector_items == [("lesson", tmp_path / "vectors_lesson.json")]
    assert object_items == [("uploads/lesson.txt", upload)]


def test_storage_migration_dry_run_does_not_write(tmp_path):
    async def run():
        (tmp_path / "quiz_q1_topic.json").write_text('"algebra"', encoding="utf-8")
        (tmp_path / "vectors_lesson.json").write_text(
            '{"texts":["algebra"],"vectors":[[0.1,0.2]],"metadatas":[{"source":"unit"}]}',
            encoding="utf-8",
        )
        upload = tmp_path / "uploads" / "source.txt"
        upload.parent.mkdir(parents=True)
        upload.write_text("source", encoding="utf-8")

        report = await run_migration(tmp_path, write=False, include_kv=True, include_objects=True)

        assert report.dry_run is True
        assert report.kv_scanned == 1
        assert report.kv_written == 0
        assert report.kv_skipped == 1
        assert report.vectors_scanned == 1
        assert report.vectors_written == 0
        assert report.vectors_skipped == 1
        assert report.objects_scanned == 1
        assert report.objects_written == 0
        assert report.objects_skipped == 1

    asyncio.run(run())
