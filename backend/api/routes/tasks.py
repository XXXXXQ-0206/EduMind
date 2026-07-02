"""Generic task event routes shared by long-running generators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from utils.auth import get_bearer_token, resolve_user_from_token
from utils.live_events import format_sse_message, stream_live_events_sse
from utils.storage import get_messages, json_storage, record_belongs_to_user


router = APIRouter()


@dataclass(frozen=True)
class TaskEventTarget:
    canonical_kind: str
    channel_for: Callable[[str], str]
    record_key_for: Callable[[str], str]


_TASK_EVENT_TARGETS: dict[str, TaskEventTarget] = {
    "chat": TaskEventTarget(
        "chat",
        lambda task_id: f"chat:{task_id}",
        lambda task_id: f"chat:{task_id}",
    ),
    "quiz": TaskEventTarget(
        "quiz",
        lambda task_id: f"quiz:{task_id}",
        lambda task_id: f"quiz:{task_id}",
    ),
    "smartnotes": TaskEventTarget(
        "smartnotes",
        lambda task_id: f"note:{task_id}",
        lambda task_id: f"note:{task_id}",
    ),
    "note": TaskEventTarget(
        "smartnotes",
        lambda task_id: f"note:{task_id}",
        lambda task_id: f"note:{task_id}",
    ),
    "podcast": TaskEventTarget(
        "podcast",
        lambda task_id: f"podcast:{task_id}",
        lambda task_id: f"podcast:{task_id}",
    ),
    "paper": TaskEventTarget(
        "paper",
        lambda task_id: f"paper:{task_id}",
        lambda task_id: f"paper:{task_id}",
    ),
    "exam": TaskEventTarget(
        "exam",
        lambda task_id: f"exam:{task_id}",
        lambda task_id: f"exam_run:{task_id}",
    ),
    "teaching_video": TaskEventTarget(
        "teaching_video",
        lambda task_id: f"video:{task_id}",
        lambda task_id: f"video:{task_id}",
    ),
    "teaching-video": TaskEventTarget(
        "teaching_video",
        lambda task_id: f"video:{task_id}",
        lambda task_id: f"video:{task_id}",
    ),
    "video": TaskEventTarget(
        "teaching_video",
        lambda task_id: f"video:{task_id}",
        lambda task_id: f"video:{task_id}",
    ),
}


def _normalize_kind(kind: str) -> str:
    return (kind or "").strip().lower().replace(" ", "_")


def _resolve_token(request: Request, authorization: Optional[str]) -> Optional[str]:
    return request.query_params.get("token") or get_bearer_token(authorization)


@router.get("/tasks/{kind}/{task_id}/events")
async def task_events_sse(
    kind: str,
    task_id: str,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    """Subscribe to a generation task over Server-Sent Events."""

    target = _TASK_EVENT_TARGETS.get(_normalize_kind(kind))
    normalized_id = (task_id or "").strip()
    if target is None or not normalized_id:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"ok": False, "error": "task event stream not found"},
        )

    user = resolve_user_from_token(_resolve_token(request, authorization))
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"ok": False, "error": "unauthorized"},
        )

    record = await json_storage.get(target.record_key_for(normalized_id))
    if not isinstance(record, dict) or not record_belongs_to_user(record, user.id, user.username):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"ok": False, "error": "not found"},
        )

    channel = target.channel_for(normalized_id)

    async def event_stream():
        yield format_sse_message(
            {
                "type": "ready",
                "kind": target.canonical_kind,
                "taskId": normalized_id,
            }
        )
        if target.canonical_kind == "chat":
            messages = await get_messages(normalized_id)
            if messages and messages[-1].get("role") == "assistant":
                yield format_sse_message(
                    {
                        "type": "answer",
                        "answer": messages[-1].get("content", ""),
                        "replayed": True,
                    }
                )
                yield format_sse_message({"type": "done", "replayed": True})
                return

        async for chunk in stream_live_events_sse(channel):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
