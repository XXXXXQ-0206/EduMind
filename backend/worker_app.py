"""Entrypoint for running queued EduMind generation workers."""
from __future__ import annotations

import asyncio
import logging

from core.task_dispatcher import get_task_handlers, run_task_worker

# Import route modules so their runner handlers register with the dispatcher.
from api.routes import chat, exam, notes, paper, podcast, quiz, teaching_video  # noqa: F401


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("registered generation task handlers: %s", ", ".join(sorted(get_task_handlers())))
    await run_task_worker()


if __name__ == "__main__":
    asyncio.run(main())
