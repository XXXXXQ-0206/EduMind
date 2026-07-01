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


def register_task_handler(kind: str, handler: TaskHandler) -> None:
    normalized = (kind or "").strip()
    if not normalized:
        raise ValueError("task kind is required")
    _HANDLERS[normalized] = handler


def get_task_handlers() -> Dict[str, TaskHandler]:
    return dict(_HANDLERS)


async def dispatch_generation_task(kind: str, task_id: str, inline_starter: TaskHandler) -> None:
    """Dispatch a generation task using the configured execution mode."""

    provider = (config.task_queue_provider or "inline").strip().lower()
    if provider in {"inline", "memory", "none"}:
        await inline_starter(task_id)
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
        handler = _HANDLERS.get(task.kind)
        if handler is None:
            logger.warning("discarding unknown generation task kind=%s id=%s", task.kind, task.id)
            await queue.fail(task, f"unknown task kind: {task.kind}")
            continue
        try:
            await handler(task.id)
            await queue.ack(task)
        except Exception:
            logger.exception("generation task failed kind=%s id=%s", task.kind, task.id)
            await queue.fail(task, "handler failed")
