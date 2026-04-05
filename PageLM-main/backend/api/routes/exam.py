"""
Exam Labs routes powered by the quiz agent.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.quiz_agent import QuizAgent, QuizInput
from utils.auth import require_auth, require_websocket_auth
from utils.auth_db import AuthUser
from utils.storage import json_storage, owner_payload, record_belongs_to_user
from utils.websocket import manager


router = APIRouter()


EXAM_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "gaokao-math-core",
        "name": "高考数学核心能力卷",
        "sections": [
            {"title": "函数与导数", "focus": "函数性质、导数应用", "count": 3},
            {"title": "解析几何与概率", "focus": "坐标系、概率统计、综合应用", "count": 3},
        ],
    },
    {
        "id": "gaokao-english-reading",
        "name": "高考英语阅读与词汇卷",
        "sections": [
            {"title": "阅读理解", "focus": "主旨推断、细节定位、作者态度", "count": 3},
            {"title": "词汇与语境", "focus": "词义辨析、上下文理解", "count": 3},
        ],
    },
    {
        "id": "civil-service-logic",
        "name": "行测逻辑推理模拟卷",
        "sections": [
            {"title": "类比与定义判断", "focus": "定义判断、类比推理", "count": 3},
            {"title": "逻辑推理", "focus": "削弱加强、真假推理、归纳论证", "count": 3},
        ],
    },
    {
        "id": "teacher-cert-pedagogy",
        "name": "教师资格证教育学基础卷",
        "sections": [
            {"title": "教育学原理", "focus": "教学原则、德育、课程理论", "count": 3},
            {"title": "心理与课堂实践", "focus": "学习理论、课堂管理、案例判断", "count": 3},
        ],
    },
]


class StartExamRequest(BaseModel):
    examId: str


def _exam_by_id(exam_id: str) -> Dict[str, Any] | None:
    for exam in EXAM_CATALOG:
        if exam["id"] == exam_id:
            return exam
    return None


def _exam_prompt(exam: Dict[str, Any]) -> tuple[str, int]:
    sections = exam.get("sections") or []
    total = sum(int(section.get("count") or 0) for section in sections) or 6
    lines = [f"Exam: {exam.get('name')}"]
    for section in sections:
        lines.append(
            f"- {section.get('title')}: {section.get('focus')} ({int(section.get('count') or 0)} questions)"
        )
    lines.append("题目需要覆盖所有部分，难度接近正式模拟卷，解释必须说明正确答案为何成立。")
    return "\n".join(lines), total


@router.get("/exams")
async def list_exams(user: AuthUser = Depends(require_auth)):
    return {"ok": True, "exams": EXAM_CATALOG}


@router.post("/exam")
async def start_exam(payload: StartExamRequest, user: AuthUser = Depends(require_auth)):
    exam = _exam_by_id((payload.examId or "").strip())
    if not exam:
        return JSONResponse(content={"ok": False, "error": "exam not found"}, status_code=404)

    run_id = str(uuid.uuid4())
    await json_storage.set(
        f"exam_run:{run_id}",
        {
            "id": run_id,
            "examId": exam["id"],
            "created_at": datetime.now().isoformat(),
            **owner_payload(user.id, user.username),
        },
    )
    return {
        "ok": True,
        "runId": run_id,
        "stream": f"/ws/exams?runId={run_id}",
    }


@router.websocket("/ws/exams")
async def exam_stream(websocket: WebSocket):
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    run_id = websocket.query_params.get("runId")
    if not run_id:
        await websocket.close(code=1008, reason="runId required")
        return

    run_meta = await json_storage.get(f"exam_run:{run_id}")
    if not run_meta or not record_belongs_to_user(run_meta, user.id, user.username):
        await websocket.close(code=1008, reason="invalid runId")
        return

    await manager.connect(websocket, run_id)
    await manager.send_message({"type": "ready", "runId": run_id}, run_id)

    try:
        cached = await json_storage.get(f"exam_run:{run_id}:questions")
        if isinstance(cached, list) and cached:
            await manager.send_message(
                {"type": "exam", "examId": run_meta.get("examId"), "payload": cached},
                run_id,
            )
            await manager.send_message({"type": "done"}, run_id)
            return

        exam = _exam_by_id(str(run_meta.get("examId") or ""))
        if not exam:
            await manager.send_message({"type": "error", "error": "exam not found"}, run_id)
            return

        await manager.send_message({"type": "phase", "value": "generating", "examId": exam["id"]}, run_id)
        prompt, count = _exam_prompt(exam)
        result = await QuizAgent().execute(QuizInput(topic=prompt, count=count))
        if not result.success or not result.quiz:
            await manager.send_message({"type": "error", "error": result.error or "exam generation failed"}, run_id)
            return

        payload = [item.model_dump() for item in result.quiz]
        await json_storage.set(f"exam_run:{run_id}:questions", payload)
        await manager.send_message({"type": "exam", "examId": exam["id"], "payload": payload}, run_id)
        await manager.send_message({"type": "done"}, run_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
    except Exception as exc:
        try:
            await manager.send_message({"type": "error", "error": str(exc)}, run_id)
        finally:
            manager.disconnect(websocket, run_id)
    finally:
        manager.disconnect(websocket, run_id)
