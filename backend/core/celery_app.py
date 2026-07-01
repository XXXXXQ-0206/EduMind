"""Celery application for durable EduMind generation tasks."""
from __future__ import annotations

from config import config


def _redis_url(value: str | None) -> str:
    return (value or config.redis_url).strip()


try:
    from celery import Celery
except ImportError as exc:  # pragma: no cover - exercised only in misconfigured runtimes.
    raise RuntimeError("TASK_QUEUE_PROVIDER=celery requires the 'celery[redis]' package") from exc


celery_app = Celery(
    "edumind",
    broker=_redis_url(config.celery_broker_url),
    backend=_redis_url(config.celery_result_backend),
    include=["core.celery_tasks"],
)

_visibility_timeout = max(60, int(config.celery_visibility_timeout_seconds or 3600))

celery_app.conf.update(
    task_default_queue=config.celery_task_queue_name,
    task_default_exchange=config.celery_task_queue_name,
    task_default_routing_key=config.celery_task_queue_name,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_soft_shutdown_timeout=10.0,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": _visibility_timeout},
    result_backend_transport_options={"visibility_timeout": _visibility_timeout},
    visibility_timeout=_visibility_timeout,
)
