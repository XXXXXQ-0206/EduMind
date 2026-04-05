"""
Planner routes covering task CRUD, scheduling, materials generation, and websocket updates.
"""
from __future__ import annotations

import math
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import aiofiles
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.flashcards_agent import KnowledgeCardsAgent, KnowledgeCardsInput
from agents.quiz_agent import QuizAgent, QuizInput
from config import config
from utils.auth import require_auth, require_websocket_auth
from utils.auth_db import AuthUser
from utils.feature_support import (
    build_files_context,
    compact_text,
    ensure_flashcards,
    ensure_string_list,
    extract_file_text_from_meta,
    language_hint,
    safe_json_loads,
)
from utils.llm import invoke_llm
from utils.websocket import manager
from utils.storage import json_storage


router = APIRouter()


class IngestRequest(BaseModel):
    text: str


class WeeklyPlanRequest(BaseModel):
    cram: Optional[bool] = False


class PlanTaskRequest(BaseModel):
    cram: Optional[bool] = False


class MaterialsRequest(BaseModel):
    kind: str


def _tasks_key(user_id: int) -> str:
    return f"planner:tasks:user:{user_id}"


def _planner_channel(user_id: int) -> str:
    return f"planner:user:{user_id}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _normalize_status(value: Any) -> str:
    status = str(value or "todo").strip().lower()
    return status if status in {"todo", "doing", "done", "blocked"} else "todo"


def _normalize_priority(value: Any) -> int:
    try:
        num = int(value)
    except Exception:
        num = 3
    return max(1, min(5, num))


def _coerce_due_at(value: Any) -> int:
    if isinstance(value, (int, float)) and value > 0:
        return int(value)
    text = str(value or "").strip()
    if not text:
        return int((datetime.now() + timedelta(days=3)).timestamp() * 1000)
    try:
        if text.isdigit():
            return int(text)
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except Exception:
        return int((datetime.now() + timedelta(days=3)).timestamp() * 1000)


def _normalize_est_mins(value: Any) -> int:
    try:
        mins = int(value)
    except Exception:
        mins = 90
    return max(20, min(8 * 60, mins))


async def _load_tasks(user: AuthUser) -> List[Dict[str, Any]]:
    tasks = await json_storage.get(_tasks_key(user.id))
    return tasks if isinstance(tasks, list) else []


async def _save_tasks(user: AuthUser, tasks: List[Dict[str, Any]]) -> None:
    await json_storage.set(_tasks_key(user.id), tasks)


def _sort_tasks(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        [dict(task) for task in tasks],
        key=lambda item: (
            1 if item.get("status") == "done" else 0,
            int(item.get("dueAt") or 0),
            -int(item.get("priority") or 3),
            -int(item.get("updatedAt") or 0),
        ),
    )


async def _broadcast(user_id: int, message: Dict[str, Any]) -> None:
    await manager.send_message(message, _planner_channel(user_id))


def _task_index(tasks: List[Dict[str, Any]], task_id: str) -> int:
    for index, task in enumerate(tasks):
        if str(task.get("id")) == task_id:
            return index
    return -1


async def _save_uploads(user: AuthUser, files: List[UploadFile]) -> List[Dict[str, Any]]:
    upload_dir = config.storage_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved: List[Dict[str, Any]] = []

    for item in files:
        if not item.filename:
            continue
        now = _now_ms()
        unique = uuid.uuid4().hex[:10]
        stored_name = f"planner-{user.id}-{now}-{unique}-{item.filename}"
        destination = upload_dir / stored_name
        content = await item.read()
        async with aiofiles.open(destination, "wb") as handle:
            await handle.write(content)
        saved.append(
            {
                "id": str(uuid.uuid4()),
                "filename": stored_name,
                "originalName": item.filename,
                "mimeType": item.content_type or "application/octet-stream",
                "size": len(content),
                "uploadedAt": _now_ms(),
            }
        )
    return saved


async def _task_context(task: Dict[str, Any], *, max_chars: int = 12000) -> str:
    files = list(task.get("files") or [])
    file_context = await build_files_context(files, max_chars=max_chars // 2, snippet_chars=2200) if files else ""
    lines = [
        f"任务标题: {task.get('title')}",
        f"课程: {task.get('course') or '未指定'}",
        f"类型: {task.get('type') or '未指定'}",
        f"备注: {task.get('notes') or '无'}",
        f"预计耗时: {task.get('estMins')} 分钟",
        f"优先级: {task.get('priority')}",
        f"截止时间: {datetime.fromtimestamp(int(task.get('dueAt') or _now_ms()) / 1000).isoformat()}",
    ]
    if task.get("steps"):
        lines.append("当前步骤: " + " | ".join(str(step) for step in task.get("steps") or []))
    if file_context:
        lines.append("附件内容:\n" + file_context)
    return "\n".join(lines)[:max_chars]


async def _infer_task_from_text(text: str, file_context: str = "") -> Dict[str, Any]:
    prompt = f"""
现在时间: {datetime.now().isoformat()}
用户输入:
{text}

附件内容:
{file_context or '(无)'}
""".strip()
    system_prompt = """
You are a task-planning assistant.
Return only one JSON object:
{
  "title": "string",
  "course": "string",
  "type": "string",
  "notes": "string",
  "dueAt": 0,
  "estMins": 90,
  "priority": 3,
  "tags": ["string"],
  "steps": ["string"]
}

Rules:
- Use Chinese if the input is Chinese, otherwise English.
- dueAt must be a unix timestamp in milliseconds.
- If the user did not specify a deadline, infer a reasonable one within the next 2-5 days.
- estMins should be realistic.
- steps should contain 3-6 actionable items.
- Output JSON only.
""".strip()
    raw = await invoke_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
    )
    parsed = safe_json_loads(raw)
    if isinstance(parsed, dict):
        return parsed
    return {}


def _fallback_task_from_text(text: str) -> Dict[str, Any]:
    clean = compact_text(text or "新任务", 120)
    return {
        "title": clean or "新任务",
        "course": "",
        "type": "assignment",
        "notes": text.strip(),
        "dueAt": int((datetime.now() + timedelta(days=3)).timestamp() * 1000),
        "estMins": 90,
        "priority": 3,
        "tags": [],
        "steps": ["梳理要求", "完成主体内容", "检查并提交"],
    }


def _build_task(parsed: Dict[str, Any], *, text: str, files: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    fallback = _fallback_task_from_text(text)
    now = _now_ms()
    title = str(parsed.get("title") or fallback["title"]).strip() or fallback["title"]
    notes = str(parsed.get("notes") or fallback["notes"]).strip()
    task = {
        "id": str(uuid.uuid4()),
        "course": str(parsed.get("course") or fallback["course"]).strip(),
        "title": title[:200],
        "type": str(parsed.get("type") or fallback["type"]).strip() or "assignment",
        "notes": notes[:2000],
        "dueAt": _coerce_due_at(parsed.get("dueAt") or fallback["dueAt"]),
        "estMins": _normalize_est_mins(parsed.get("estMins") or fallback["estMins"]),
        "priority": _normalize_priority(parsed.get("priority") or fallback["priority"]),
        "status": "todo",
        "createdAt": now,
        "updatedAt": now,
        "tags": ensure_string_list(parsed.get("tags"), limit=6, item_limit=40),
        "files": files or [],
        "steps": ensure_string_list(parsed.get("steps"), limit=6, item_limit=80)
        or ensure_string_list(fallback["steps"], limit=6, item_limit=80),
    }
    return task


def _round_start(base: datetime) -> datetime:
    candidate = base.replace(second=0, microsecond=0)
    minute = candidate.minute
    if minute == 0:
        return candidate
    if minute <= 30:
        return candidate.replace(minute=30)
    return (candidate + timedelta(hours=1)).replace(minute=0)


def _generate_slots(task: Dict[str, Any], cram: bool = False) -> List[Dict[str, Any]]:
    now = datetime.now()
    due_dt = datetime.fromtimestamp(int(task.get("dueAt") or _now_ms()) / 1000)
    if due_dt <= now:
        due_dt = now + timedelta(days=1)
    est_mins = int(task.get("estMins") or 90)
    focus_blocks = max(1, math.ceil(est_mins / 50))
    review_blocks = 1 if est_mins >= 60 else 0
    buffer_blocks = 1 if est_mins >= 120 else 0
    total_blocks = focus_blocks + review_blocks + buffer_blocks

    days_left = max(1, (due_dt.date() - now.date()).days + 1)
    spread_days = 1 if cram else min(max(1, total_blocks), days_left)
    start_seed = _round_start(now + timedelta(minutes=20))
    slots: List[Dict[str, Any]] = []

    def add_slot(day_offset: int, hour: int, minute: int, duration: int, kind: str) -> None:
        slot_start = (start_seed + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if slot_start < start_seed:
            slot_start = start_seed
        slot_end = slot_start + timedelta(minutes=duration)
        if slot_end > due_dt:
            return
        slots.append(
            {
                "id": str(uuid.uuid4()),
                "taskId": task["id"],
                "start": int(slot_start.timestamp() * 1000),
                "end": int(slot_end.timestamp() * 1000),
                "kind": kind,
                "done": False,
            }
        )

    for index in range(focus_blocks):
        day_offset = min(index, spread_days - 1)
        hour = 19 if day_offset > 0 else max(start_seed.hour, 9)
        minute = 0 if index % 2 == 0 else 10
        add_slot(day_offset, min(hour, 21), minute if minute in (0, 10, 30) else 0, 50, "focus")

    if review_blocks:
        review_day = max(0, spread_days - 1)
        add_slot(review_day, 21, 0, 30, "review")
    if buffer_blocks:
        buffer_day = max(0, spread_days - 1)
        add_slot(buffer_day, 16, 30, 20, "buffer")

    slots.sort(key=lambda item: item["start"])
    return slots


async def _plan_task_with_ai(task: Dict[str, Any], cram: bool = False) -> Dict[str, Any]:
    context = await _task_context(task, max_chars=9000)
    system_prompt = """
You help break learning tasks into steps.
Return only one JSON object:
{
  "steps": ["string"],
  "notes": "string"
}

Rules:
- 3 to 6 steps.
- Each step must be a concrete action.
- Keep the notes practical and short.
- Output JSON only.
""".strip()
    raw = await invoke_llm(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Task context:\n{context}\n\n"
                    f"Planning mode: {'cram' if cram else 'normal'}\n"
                    "Generate actionable steps and a short planning note."
                ),
            },
        ],
        max_tokens=800,
    )
    parsed = safe_json_loads(raw)
    if isinstance(parsed, dict):
        steps = ensure_string_list(parsed.get("steps"), limit=6, item_limit=80)
        if steps:
            task["steps"] = steps
        note = str(parsed.get("notes") or "").strip()
        if note:
            existing = str(task.get("notes") or "").strip()
            task["notes"] = (existing + ("\n\n" if existing else "") + "AI计划建议：" + note)[:2000]
    task["plan"] = {"slots": _generate_slots(task, cram=cram)}
    task["updatedAt"] = _now_ms()
    return task


def _weekly_plan_from_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    days_map: Dict[str, List[Dict[str, Any]]] = {}
    for offset in range(7):
        date_key = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
        days_map[date_key] = []

    for task in tasks:
        for slot in ((task.get("plan") or {}).get("slots") or []):
            date_key = datetime.fromtimestamp(int(slot["start"]) / 1000).strftime("%Y-%m-%d")
            days_map.setdefault(date_key, []).append(slot)

    return {
        "days": [
            {"date": date_key, "slots": sorted(slots, key=lambda item: item["start"])}
            for date_key, slots in sorted(days_map.items())
        ]
    }


async def _materials_payload(task: Dict[str, Any], kind: str) -> Any:
    context = await _task_context(task, max_chars=12000)

    if kind == "flashcards":
        result = await KnowledgeCardsAgent().execute(KnowledgeCardsInput(topic=context, count=5))
        cards = []
        if result.success and result.cards:
            for card in result.cards[:5]:
                cards.append({"q": card.question or card.concept, "a": card.answer, "tag": card.concept})
        return {"flashcards": cards}

    if kind == "quiz":
        result = await QuizAgent().execute(QuizInput(topic=context, count=5))
        return {"questions": [item.model_dump() for item in (result.quiz or [])]}

    system_prompt = """
    You are an academic assistant. Output JSON only.
    For kind=summary return {"answer":"..."}.
    For kind=studyGuide return {
      "mainConcepts": ["..."],
      "importantTerms": [{"term":"...","definition":"..."}],
      "questions": ["..."],
      "checklist": ["..."],
      "nextAction": "..."
    }.
    """.strip()
    raw = await invoke_llm(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"kind={kind}\n\nTask context:\n{context}",
            },
        ],
        max_tokens=1200,
    )
    parsed = safe_json_loads(raw)
    if isinstance(parsed, dict):
        if kind == "summary":
            return {"answer": str(parsed.get("answer") or "").strip() or raw.strip()}
        important_terms: List[Dict[str, str]] = []
        if isinstance(parsed.get("importantTerms"), list):
            for item in parsed.get("importantTerms") or []:
                if not isinstance(item, dict):
                    continue
                term = str(item.get("term") or "").strip()
                definition = str(item.get("definition") or "").strip()
                if term and definition:
                    important_terms.append({"term": term[:80], "definition": definition[:200]})
                if len(important_terms) >= 6:
                    break
        return {
            "mainConcepts": ensure_string_list(parsed.get("mainConcepts"), limit=6),
            "importantTerms": important_terms,
            "questions": ensure_string_list(parsed.get("questions"), limit=6),
            "checklist": ensure_string_list(parsed.get("checklist"), limit=6),
            "nextAction": str(parsed.get("nextAction") or "").strip(),
        }
    if kind == "summary":
        return {"answer": raw.strip()}
    return {
        "mainConcepts": ensure_string_list(task.get("steps"), limit=6),
        "importantTerms": [],
        "questions": [
            f"{task.get('title')} 的核心要求是什么？",
            f"完成 {task.get('title')} 前需要先准备什么？",
        ],
        "checklist": ensure_string_list(task.get("steps"), limit=6),
        "nextAction": "先完成第一步，再补充资料与细节。",
    }


async def _connect_digest(user: AuthUser) -> None:
    tasks = _sort_tasks(await _load_tasks(user))
    today = _now_ms() + 24 * 60 * 60 * 1000
    due = [
        {"id": task["id"], "title": task["title"], "dueAt": task["dueAt"]}
        for task in tasks
        if task.get("status") != "done" and int(task.get("dueAt") or 0) <= today
    ][:5]
    sessions = sum(len((task.get("plan") or {}).get("slots") or []) for task in tasks)
    message = (
        f"今天待处理任务 {len(due)} 项，已安排学习时段 {sessions} 个。"
        if tasks
        else "目前还没有任务，添加一个作业后我会帮你拆解和排期。"
    )
    await _broadcast(
        user.id,
        {
            "type": "daily.digest",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due": due,
            "sessions": sessions,
            "message": message,
        },
    )
    if due:
        next_due = due[0]
        await _broadcast(
            user.id,
            {
                "type": "reminder",
                "text": f"优先处理：{next_due['title']}",
                "at": _now_ms(),
                "taskId": next_due["id"],
                "scheduledFor": datetime.fromtimestamp(next_due["dueAt"] / 1000).isoformat(),
            },
        )


@router.post("/tasks/ingest")
async def planner_ingest(payload: IngestRequest, user: AuthUser = Depends(require_auth)):
    text = (payload.text or "").strip()
    if not text:
        return JSONResponse(content={"ok": False, "error": "text required"}, status_code=400)

    parsed = await _infer_task_from_text(text)
    task = _build_task(parsed, text=text)
    tasks = await _load_tasks(user)
    tasks.insert(0, task)
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.created", "task": task})
    return {"ok": True, "task": task}


@router.get("/tasks")
async def planner_list(
    status: Optional[str] = Query(default=None),
    dueBefore: Optional[int] = Query(default=None),
    course: Optional[str] = Query(default=None),
    user: AuthUser = Depends(require_auth),
):
    tasks = _sort_tasks(await _load_tasks(user))
    filtered: List[Dict[str, Any]] = []
    for task in tasks:
        if status and task.get("status") != status:
            continue
        if dueBefore and int(task.get("dueAt") or 0) > int(dueBefore):
            continue
        if course and str(task.get("course") or "").strip() != course:
            continue
        filtered.append(task)
    return {"ok": True, "tasks": filtered}


@router.get("/tasks/{task_id}")
async def planner_get_task(task_id: str, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True, "task": tasks[index]}


@router.post("/tasks")
async def planner_create_with_files(
    q: Optional[str] = Form(default=None),
    title: Optional[str] = Form(default=None),
    course: Optional[str] = Form(default=None),
    type: Optional[str] = Form(default=None),
    file: List[UploadFile] = File(default=[]),
    user: AuthUser = Depends(require_auth),
):
    saved_files = await _save_uploads(user, file)
    file_context = await build_files_context(saved_files, max_chars=6000, snippet_chars=1800) if saved_files else ""
    source_text = (q or title or "").strip() or (saved_files[0]["originalName"] if saved_files else "新任务")
    parsed = await _infer_task_from_text(source_text, file_context=file_context)
    if course:
        parsed["course"] = course
    if type:
        parsed["type"] = type
    if title:
        parsed["title"] = title
    task = _build_task(parsed, text=source_text, files=saved_files)
    tasks = await _load_tasks(user)
    tasks.insert(0, task)
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.created", "task": task})
    if saved_files:
        await _broadcast(user.id, {"type": "task.files.added", "taskId": task["id"], "files": saved_files})
    return {"ok": True, "task": task}


@router.patch("/tasks/{task_id}")
async def planner_update(task_id: str, patch: Dict[str, Any], user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)

    task = dict(tasks[index])
    before_status = task.get("status")
    allowed = {"course", "title", "type", "notes", "dueAt", "estMins", "priority", "status", "tags", "steps"}
    for key, value in patch.items():
        if key not in allowed:
            continue
        if key == "dueAt":
            task[key] = _coerce_due_at(value)
        elif key == "estMins":
            task[key] = _normalize_est_mins(value)
        elif key == "priority":
            task[key] = _normalize_priority(value)
        elif key == "status":
            task[key] = _normalize_status(value)
        elif key in {"tags", "steps"}:
            task[key] = ensure_string_list(value, limit=8, item_limit=80)
        else:
            task[key] = str(value or "").strip()
    task["updatedAt"] = _now_ms()
    tasks[index] = task
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.updated", "task": task})

    if before_status != task.get("status") and task.get("status") == "doing":
        await _broadcast(
            user.id,
            {
                "type": "session.started",
                "session": {
                    "id": str(uuid.uuid4()),
                    "taskId": task["id"],
                    "startedAt": datetime.now().isoformat(),
                    "status": "running",
                },
            },
        )
    if before_status != task.get("status") and task.get("status") == "done":
        await _broadcast(
            user.id,
            {
                "type": "session.ended",
                "session": {
                    "id": str(uuid.uuid4()),
                    "endedAt": datetime.now().isoformat(),
                    "minutesWorked": int(task.get("estMins") or 0),
                    "completed": True,
                    "status": "completed",
                },
            },
        )

    return {"ok": True, "task": task}


@router.delete("/tasks/{task_id}")
async def planner_delete(task_id: str, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    task = tasks.pop(index)
    for meta in task.get("files") or []:
        filename = str(meta.get("filename") or "")
        if not filename:
            continue
        path = config.storage_dir / "uploads" / filename
        if path.exists():
            path.unlink()
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.deleted", "taskId": task_id})
    return {"ok": True}


@router.post("/tasks/{task_id}/plan")
async def planner_plan(task_id: str, payload: PlanTaskRequest, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    task = await _plan_task_with_ai(dict(tasks[index]), cram=bool(payload.cram))
    tasks[index] = task
    await _save_tasks(user, tasks)
    slots = list((task.get("plan") or {}).get("slots") or [])
    await _broadcast(user.id, {"type": "plan.update", "taskId": task_id, "slots": slots})
    await _broadcast(user.id, {"type": "task.updated", "task": task})
    return {"ok": True, "task": task}


@router.post("/planner/weekly")
async def planner_weekly(payload: WeeklyPlanRequest, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    return {"ok": True, "plan": _weekly_plan_from_tasks(tasks)}


@router.post("/tasks/{task_id}/materials")
async def planner_materials(task_id: str, payload: MaterialsRequest, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    kind = str(payload.kind or "summary").strip()
    data = await _materials_payload(tasks[index], kind)
    return {"ok": True, "data": data}


@router.post("/tasks/{task_id}/files")
async def planner_upload_files(task_id: str, file: List[UploadFile] = File(...), user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    saved_files = await _save_uploads(user, file)
    task = dict(tasks[index])
    task["files"] = [*(task.get("files") or []), *saved_files]
    task["updatedAt"] = _now_ms()
    tasks[index] = task
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.files.added", "taskId": task_id, "files": saved_files})
    await _broadcast(user.id, {"type": "task.updated", "task": task})
    return {"ok": True, "files": saved_files}


@router.delete("/tasks/{task_id}/files/{file_id}")
async def planner_delete_file(task_id: str, file_id: str, user: AuthUser = Depends(require_auth)):
    tasks = await _load_tasks(user)
    index = _task_index(tasks, task_id)
    if index < 0:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    task = dict(tasks[index])
    remaining: List[Dict[str, Any]] = []
    target: Optional[Dict[str, Any]] = None
    for meta in task.get("files") or []:
        if str(meta.get("id")) == file_id:
            target = meta
        else:
            remaining.append(meta)
    if not target:
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)

    filename = str(target.get("filename") or "")
    if filename:
        path = config.storage_dir / "uploads" / filename
        if path.exists():
            path.unlink()

    task["files"] = remaining
    task["updatedAt"] = _now_ms()
    tasks[index] = task
    await _save_tasks(user, tasks)
    await _broadcast(user.id, {"type": "task.file.removed", "taskId": task_id, "fileId": file_id})
    await _broadcast(user.id, {"type": "task.updated", "task": task})
    return {"ok": True}


@router.websocket("/ws/planner")
async def planner_ws(websocket: WebSocket):
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    sid = websocket.query_params.get("sid") or str(uuid.uuid4())
    channel = _planner_channel(user.id)
    await manager.connect(websocket, channel)
    await manager.send_message({"type": "ready", "sid": sid}, channel)
    await _connect_digest(user)

    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except RuntimeError:
        manager.disconnect(websocket, channel)
