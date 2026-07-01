"""Celery task definitions for EduMind generation jobs."""
from __future__ import annotations

import asyncio
import logging

from config import config
from core.celery_app import celery_app
from core.task_dispatcher import (
    UnknownTaskKindError,
    execute_registered_task,
    get_task_handlers,
)

# Import route modules so their registered generation handlers are available in
# Celery worker processes.
from api.routes import chat, exam, notes, paper, podcast, quiz, teaching_video  # noqa: F401


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="edumind.generation.run")
def run_generation_task(self, kind: str, task_id: str) -> dict[str, str]:
    """Execute a registered async generation handler inside a Celery worker."""

    normalized_kind = (kind or "").strip()
    normalized_id = (task_id or "").strip()
    if not normalized_kind or not normalized_id:
        raise ValueError("generation task requires kind and task_id")

    try:
        asyncio.run(execute_registered_task(normalized_kind, normalized_id))
    except UnknownTaskKindError:
        logger.exception(
            "unknown celery generation task kind=%s id=%s handlers=%s",
            normalized_kind,
            normalized_id,
            sorted(get_task_handlers()),
        )
        raise
    except Exception as exc:
        max_retries = max(0, int(config.celery_task_max_retries or 0))
        if self.request.retries >= max_retries:
            logger.exception(
                "celery generation task exhausted retries kind=%s id=%s",
                normalized_kind,
                normalized_id,
            )
            raise
        countdown = max(1, int(config.celery_task_retry_delay_seconds or 10))
        logger.exception(
            "celery generation task failed kind=%s id=%s retry=%s/%s",
            normalized_kind,
            normalized_id,
            self.request.retries + 1,
            max_retries,
        )
        raise self.retry(exc=exc, countdown=countdown, max_retries=max_retries)

    return {"kind": normalized_kind, "id": normalized_id, "status": "done"}
