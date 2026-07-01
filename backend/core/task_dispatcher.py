"""Generation task dispatch and worker registry."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Dict

from config import config
from infrastructure.task_queue import TaskEnvelope, create_task_queue


TaskHandler = Callable[[str], Awaitable[None]]
logger = logging.getLogger(__name__)


_HANDLERS: Dict[str, TaskHandler] = {}


class UnknownTaskKindError(ValueError):
    """Raised when a queued task kind has no registered handler."""


def register_task_handler(kind: str, handler: TaskHandler) -> None:
    normalized = (kind or "").strip()
    if not normalized:
        raise ValueError("task kind is required")
    _HANDLERS[normalized] = handler


def get_task_handlers() -> Dict[str, TaskHandler]:
    return dict(_HANDLERS)


async def execute_registered_task(kind: str, task_id: str) -> None:
    normalized = (kind or "").strip()
    handler = _HANDLERS.get(normalized)
    if handler is None:
        raise UnknownTaskKindError(f"unknown task kind: {normalized}")
    await handler(task_id)


async def enqueue_celery_generation_task(kind: str, task_id: str) -> None:
    """Publish a generation task to Celery.

    Import lazily so local inline/test runs do not require Celery to be imported.
    """

    from core.celery_app import celery_app

    celery_app.send_task(
        "edumind.generation.run",
        args=(kind, task_id),
        queue=config.celery_task_queue_name,
        routing_key=config.celery_task_queue_name,
    )


async def dispatch_generation_task(kind: str, task_id: str, inline_starter: TaskHandler) -> None:
    """Dispatch a generation task using the configured execution mode."""

    provider = (config.task_queue_provider or "inline").strip().lower()
    if provider in {"inline", "memory", "none"}:
        await inline_starter(task_id)
        return
    if provider == "celery":
        await enqueue_celery_generation_task(kind, task_id)
        return
    await create_task_queue().enqueue(TaskEnvelope(kind=kind, id=task_id))


async def run_task_worker(stop_event: asyncio.Event | None = None) -> None:
    """Consume queued generation tasks forever."""

    queue = create_task_queue()
    logger.info("task worker started provider=%s queue=%s", config.task_queue_provider, config.task_queue_name)
    while stop_event is None or not stop_event.is_set():
        task = await queue.dequeue(timeout_seconds=max(1, int(config.task_worker_poll_seconds)))
        if task is None:
            continue
        try:
            await execute_registered_task(task.kind, task.id)
            await queue.ack(task)
        except UnknownTaskKindError as exc:
            logger.warning("discarding unknown generation task kind=%s id=%s", task.kind, task.id)
            await queue.fail(task, str(exc))
        except Exception:
            logger.exception("generation task failed kind=%s id=%s", task.kind, task.id)
            await queue.fail(task, "handler failed")
