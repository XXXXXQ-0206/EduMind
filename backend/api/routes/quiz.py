"""
测验 API 路由
与原 Node.js 版本完全兼容
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import re
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.quiz_agent import QuizAgent, QuizInput
from agents.wrongbook_report_agent import WrongBookReportAgent, WrongBookReportInput
from agents.knowledge_point_agent import KnowledgePointAgent, KnowledgePointInput
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.auth import require_auth, require_websocket_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import extract_file_text_from_meta
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import (
    get_quiz_attempts,
    json_storage,
    list_files_for_user,
    list_quizzes,
    owner_payload,
    record_belongs_to_user,
    set_quiz_attempts,
    upsert_quiz_attempt,
)
from config import config


router = APIRouter()
_quiz_run_locks: Dict[str, asyncio.Lock] = {}
_quiz_run_tasks: Dict[str, asyncio.Task] = {}


class QuizRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    count: Optional[int] = 5
    difficulty: Optional[str] = "medium"
    role: Optional[str] = None  # "student" | "teacher"，教师端/学生端独立存储


class QuizAttemptItem(BaseModel):
    questionId: int
    selectedAnswer: int
    correct: bool
    question: str
    selectedOption: str
    correctOption: str
    explanation: str
    at: Optional[int] = None


class QuizAttemptsRequest(BaseModel):
    answers: List[QuizAttemptItem]


class QuizAttemptAnswerRequest(BaseModel):
    questionId: int
    selectedAnswer: int
    correct: bool
    question: str
    selectedOption: str
    correctOption: str
    explanation: str
    at: Optional[int] = None


@router.post("/quiz")
async def create_quiz(request: QuizRequest, user: AuthUser = Depends(require_auth)):
    """创建测验"""
    try:
        topic = request.topic.strip()
        include_materials = bool(request.includeMaterials)
        material_ids = request.materialIds or []
        count = int(request.count or 5)
        difficulty = (request.difficulty or "medium").lower()

        if not topic:
            return JSONResponse(
                content={"ok": False, "error": "topic required"},
                status_code=400
            )

        quiz_id = str(uuid.uuid4())
        scope = (request.role or "student").strip().lower()
        if scope not in ("student", "teacher"):
            scope = "student"

        # 保存主题与配置到存储
        await json_storage.set(f"quiz:{quiz_id}:topic", topic)
        await json_storage.set(f"quiz:{quiz_id}:count", count)
        await json_storage.set(f"quiz:{quiz_id}:difficulty", difficulty)
        await json_storage.set(
            f"quiz:{quiz_id}:materials",
            {"include": include_materials, "ids": material_ids},
        )
        await json_storage.set(
            f"quiz:{quiz_id}",
            {
                "id": quiz_id,
                "title": topic[:100],
                "count": count,
                "difficulty": difficulty,
                "includeMaterials": include_materials,
                "scope": scope,
                "status": "pending",
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "updated_at": __import__("datetime").datetime.now().isoformat(),
                **owner_payload(user.id, user.username),
            },
        )

        await dispatch_generation_task("quiz", quiz_id, ensure_quiz_generation_task)

        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "quizId": quiz_id,
                "stream": f"/ws/quiz?quizId={quiz_id}",
            }
        )

    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500
        )


def _get_quiz_lock(quiz_id: str) -> asyncio.Lock:
    lock = _quiz_run_locks.get(quiz_id)
    if lock is None:
        lock = asyncio.Lock()
        _quiz_run_locks[quiz_id] = lock
    return lock


def _normalize_scope(scope: Optional[str]) -> str:
    value = (scope or "student").strip().lower()
    if value not in ("student", "teacher"):
        return "student"
    return value


def _quiz_channel(quiz_id: str) -> str:
    return f"quiz:{quiz_id}"


async def _safe_send_quiz(quiz_id: str, msg: Dict[str, Any]) -> None:
    try:
        await publish_live_event(_quiz_channel(quiz_id), msg)
    except Exception as e:
        print(f"[QUIZ_DEBUG] send failed quiz_id={quiz_id}: {e!r}", flush=True)


async def _update_quiz_status(quiz_id: str, status: str, *, error: Optional[str] = None) -> None:
    meta = await json_storage.get(f"quiz:{quiz_id}") or {}
    if not isinstance(meta, dict):
        return
    meta["status"] = status
    meta["updated_at"] = datetime.now().isoformat()
    if error:
        meta["error"] = error
    else:
        meta.pop("error", None)
    await json_storage.set(f"quiz:{quiz_id}", meta)


async def _quiz_still_exists(quiz_id: str) -> bool:
    return isinstance(await json_storage.get(f"quiz:{quiz_id}"), dict)


async def _build_material_context(owner_id: int, owner_username: str, quiz_scope: str, ids: List[str]) -> str:
    if not ids:
        return ""
    files = await list_files_for_user(owner_id, owner_username, quiz_scope)
    file_map = {f.get("id"): f for f in files if f.get("id")}
    max_chars = 8000
    parts: List[str] = []
    used = 0

    for fid in ids:
        meta = file_map.get(fid)
        if not meta:
            continue
        text = await extract_file_text_from_meta(meta)
        if not text:
            continue
        remaining = max_chars - used
        if remaining <= 0:
            break
        snippet = text[:remaining]
        header = f"\n\n[资料] {meta.get('originalName') or meta.get('filename') or 'document'}\n"
        parts.append(header + snippet)
        used += len(snippet)

    return "".join(parts).strip()


async def _generate_quiz(quiz_id: str) -> None:
    lock = _get_quiz_lock(quiz_id)
    async with lock:
        meta = await json_storage.get(f"quiz:{quiz_id}") or {}
        if not isinstance(meta, dict):
            return

        existing_quiz = await json_storage.get(f"quiz:{quiz_id}:quiz")
        status = str(meta.get("status") or "pending").strip().lower()
        if status == "ready" and isinstance(existing_quiz, list) and existing_quiz:
            return
        if status == "error" and isinstance(existing_quiz, list) and existing_quiz:
            return

        topic = await json_storage.get(f"quiz:{quiz_id}:topic")
        count = await json_storage.get(f"quiz:{quiz_id}:count") or 5
        materials_cfg = await json_storage.get(f"quiz:{quiz_id}:materials") or {}
        use_materials = bool(materials_cfg.get("include"))
        material_ids = list(materials_cfg.get("ids") or [])
        difficulty = await json_storage.get(f"quiz:{quiz_id}:difficulty") or "medium"

        quiz_scope = _normalize_scope(meta.get("scope"))
        owner_id = int(meta.get("owner_id") or 0)
        owner_username = str(meta.get("owner_username") or "")
        base_topic = (topic or "").strip()

        if not base_topic:
            await _update_quiz_status(quiz_id, "error", error="Quiz topic not found")
            await _safe_send_quiz(quiz_id, {"type": "error", "error": "Quiz topic not found"})
            return

        await _update_quiz_status(quiz_id, "generating")
        await _safe_send_quiz(quiz_id, {"type": "phase", "value": "generating"})

        agent = QuizAgent()
        prompt_topic = base_topic
        if use_materials and material_ids:
            print(f"[DEBUG] Quiz {quiz_id} scope={quiz_scope} owner_id={owner_id} material_ids={len(material_ids)}")
            materials_text = await _build_material_context(owner_id, owner_username, quiz_scope, material_ids)
            print(f"[DEBUG] Quiz {quiz_id} materials_text length={len(materials_text) if materials_text else 0}")
            if materials_text:
                prompt_topic = (
                    f"{base_topic}\n\n学习资料内容:\n{materials_text}\n\n"
                    "请优先基于资料生成测验，若资料不足再补充常识。"
                )

        difficulty_hint = {
            "easy": "难度：简单（概念题为主，计算简单）",
            "medium": "难度：中等（概念+应用，计算适中）",
            "hard": "难度：困难（综合应用，计算偏多）",
        }.get(str(difficulty).lower(), "难度：中等（概念+应用，计算适中）")

        stem_hint = "如果主题与数学、物理、化学或工程相关，请适当加入需要计算或推导的题目。"
        prompt_topic = f"{prompt_topic}\n{difficulty_hint}\n{stem_hint}"
        requested_count = max(1, min(20, int(count or 5)))
        input_data = QuizInput(topic=prompt_topic, count=requested_count)
        timeout_seconds = max(35, min(120, int(config.timeout / 1000)))

        result = None
        try:
            result = await asyncio.wait_for(agent.execute(input_data), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            print(f"[QUIZ_DEBUG] generation timeout quiz_id={quiz_id} timeout={timeout_seconds}s", flush=True)

        await _update_quiz_status(quiz_id, "packaging")
        await _safe_send_quiz(quiz_id, {"type": "phase", "value": "packaging"})

        quiz_data: List[Dict[str, Any]] = []
        if result and result.success and result.quiz:
            quiz_data = [q.dict() for q in result.quiz]
        else:
            fallback_items = agent._create_fallback_quiz(base_topic, requested_count)
            quiz_data = [q.dict() for q in fallback_items]
            if not quiz_data:
                err_msg = result.error if result else "quiz generation timeout"
                await _update_quiz_status(quiz_id, "error", error=err_msg)
                await _safe_send_quiz(quiz_id, {"type": "error", "error": err_msg})
                return

        if not await _quiz_still_exists(quiz_id):
            return

        await json_storage.set(f"quiz:{quiz_id}:quiz", quiz_data)
        meta = await json_storage.get(f"quiz:{quiz_id}") or {}
        if isinstance(meta, dict):
            meta["status"] = "ready"
            meta.pop("error", None)
            meta["updated_at"] = datetime.now().isoformat()
            await json_storage.set(f"quiz:{quiz_id}", meta)

        await _safe_send_quiz(quiz_id, {"type": "quiz", "quiz": quiz_data})
        await _safe_send_quiz(quiz_id, {"type": "done"})


async def ensure_quiz_generation_task(quiz_id: str) -> None:
    current = _quiz_run_tasks.get(quiz_id)
    if current and not current.done():
        return

    lease = await acquire_task_lease(f"quiz:{quiz_id}")
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _generate_quiz(quiz_id)
        except Exception as exc:
            await _update_quiz_status(quiz_id, "error", error=str(exc))
            await _safe_send_quiz(quiz_id, {"type": "error", "error": str(exc)})
            import traceback
            print(f"[ERROR] Quiz background task error: {type(exc).__name__}: {exc!r}")
            traceback.print_exc()
        finally:
            await release_task_lease(lease)
            if _quiz_run_tasks.get(quiz_id) is task:
                _quiz_run_tasks.pop(quiz_id, None)

    task = asyncio.create_task(_runner())
    _quiz_run_tasks[quiz_id] = task


async def run_quiz_generation_worker(quiz_id: str) -> None:
    lease = await acquire_task_lease(f"quiz:{quiz_id}")
    if not lease:
        return
    try:
        await _generate_quiz(quiz_id)
    except Exception as exc:
        await _update_quiz_status(quiz_id, "error", error=str(exc))
        await _safe_send_quiz(quiz_id, {"type": "error", "error": str(exc)})
        raise
    finally:
        await release_task_lease(lease)


@router.websocket("/ws/quiz")
async def quiz_websocket(websocket: WebSocket):
    """测验 WebSocket 端点"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return

    query_params = dict(websocket.query_params)
    quiz_id = query_params.get("quizId")

    if not quiz_id:
        await websocket.close(code=1008, reason="quizId required")
        return

    meta = await json_storage.get(f"quiz:{quiz_id}") or {}
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        await websocket.close(code=1008, reason="not found")
        return

    forwarder = asyncio.create_task(forward_live_events(websocket, _quiz_channel(quiz_id)))
    await asyncio.sleep(0)

    try:
        await websocket.send_json({"type": "ready", "quizId": quiz_id})
        await dispatch_generation_task("quiz", quiz_id, ensure_quiz_generation_task)

        meta = await json_storage.get(f"quiz:{quiz_id}") or meta
        status = str(meta.get("status") or "pending").strip().lower()
        questions = await json_storage.get(f"quiz:{quiz_id}:quiz") or []

        if isinstance(questions, list) and questions:
            await websocket.send_json({"type": "quiz", "quiz": questions})
            await websocket.send_json({"type": "done"})
        elif status in ("generating", "packaging"):
            await websocket.send_json({"type": "phase", "value": status})

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ERROR] Quiz websocket error: {type(e).__name__}: {e!r}")
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/quizzes")
async def list_quizzes_handler(role: Optional[str] = None, user: AuthUser = Depends(require_auth)):
    """列出测验历史；role=student|teacher 时仅返回该端"""
    try:
        scope = (role or "").strip().lower() or None
        if scope is not None and scope not in ("student", "teacher"):
            scope = None
        quizzes = await list_quizzes(scope=scope, user_id=user.id, username=user.username)
        return {"ok": True, "quizzes": quizzes}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.get("/quizzes/{quiz_id}")
async def get_quiz_handler(quiz_id: str, user: AuthUser = Depends(require_auth)):
    """获取测验详情"""
    try:
        if not quiz_id or quiz_id == "undefined" or quiz_id == "null":
            return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid quizId"})
        meta = await json_storage.get(f"quiz:{quiz_id}")
        quiz = await json_storage.get(f"quiz:{quiz_id}:quiz")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        status = str(meta.get("status") or ("ready" if quiz else "pending")).strip().lower()
        meta["status"] = status
        if status in ("pending", "generating", "packaging") and not quiz:
            await dispatch_generation_task("quiz", quiz_id, ensure_quiz_generation_task)
        return {"ok": True, "quiz": meta, "questions": quiz or []}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz_handler(quiz_id: str, user: AuthUser = Depends(require_auth)):
    """删除测验"""
    from utils.storage import delete_quiz

    try:
        if not quiz_id or quiz_id == "undefined" or quiz_id == "null":
            return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid quizId"})
        meta = await json_storage.get(f"quiz:{quiz_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        await delete_quiz(quiz_id)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.get("/quizzes/{quiz_id}/attempts")
async def get_quiz_attempts_handler(quiz_id: str, user: AuthUser = Depends(require_auth)):
    """获取测验作答记录"""
    try:
        if not quiz_id or quiz_id in {"undefined", "null"}:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid quizId"})
        meta = await json_storage.get(f"quiz:{quiz_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        attempts = await get_quiz_attempts(quiz_id)
        return {"ok": True, "attempts": attempts}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/quizzes/{quiz_id}/attempts")
async def save_quiz_attempts_handler(quiz_id: str, request: QuizAttemptsRequest, user: AuthUser = Depends(require_auth)):
    """保存测验作答记录"""
    try:
        if not quiz_id or quiz_id in {"undefined", "null"}:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid quizId"})
        meta = await json_storage.get(f"quiz:{quiz_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        answers = [a.dict() for a in request.answers]
        now_ms = int(datetime.now().timestamp() * 1000)
        for item in answers:
            if not item.get("at"):
                item["at"] = now_ms
        await set_quiz_attempts(quiz_id, answers)
        meta = await json_storage.get(f"quiz:{quiz_id}") or {}
        if meta:
            meta["updated_at"] = datetime.now().isoformat()
            await json_storage.set(f"quiz:{quiz_id}", meta)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.post("/quizzes/{quiz_id}/attempts/answer")
async def upsert_quiz_attempt_answer_handler(quiz_id: str, request: QuizAttemptAnswerRequest, user: AuthUser = Depends(require_auth)):
    """更新单题作答记录"""
    try:
        if not quiz_id or quiz_id in {"undefined", "null"}:
            return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid quizId"})
        meta = await json_storage.get(f"quiz:{quiz_id}")
        if not meta or not record_belongs_to_user(meta, user.id, user.username):
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})

        now_ms = int(datetime.now().timestamp() * 1000)
        payload = request.dict()
        payload["at"] = payload.get("at") or now_ms

        await upsert_quiz_attempt(quiz_id, payload)
        meta = await json_storage.get(f"quiz:{quiz_id}") or {}
        if meta:
            meta["updated_at"] = datetime.now().isoformat()
            await json_storage.set(f"quiz:{quiz_id}", meta)
        return {"ok": True, "attempt": payload}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


def _to_ms(value: Optional[str]) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value).timestamp() * 1000)
    except Exception:
        return 0


def _category_for_question(text: str) -> str:
    text = (text or "").lower()
    rules = [
        ("计算错误", ["计算", "求值", "数值", "公式", "代入"]),
        ("概念理解", ["定义", "概念", "性质", "原理", "含义"]),
        ("解题步骤", ["步骤", "过程", "推导", "证明", "推理"]),
        ("应用判断", ["应用", "场景", "实例", "案例", "判断"]),
    ]
    for name, keywords in rules:
        if any(k in text for k in keywords):
            return name
    return "其他"


def _extract_cjk_terms(text: str) -> List[str]:
    if not text:
        return []
    stopwords = {
        "根据", "以下", "下列", "关于", "哪个", "哪项", "说法", "正确", "错误", "不正确",
        "描述", "分别", "包括", "条件", "有关", "属于", "不是", "可能", "可以", "应当",
        "主要", "过程", "实验", "现象", "变化", "原因", "如何", "为什么", "哪些", "下述",
        "选择", "题目", "选项", "正确答案", "分析", "解析", "说明", "判断", "问题",
    }
    terms = re.findall(r"[\u4e00-\u9fff]{2,8}", str(text))
    cleaned = []
    for term in terms:
        if term in stopwords:
            continue
        if len(term) < 2:
            continue
        cleaned.append(term)
    return cleaned


def _extract_question_terms(question: Dict[str, Any]) -> List[str]:
    text = " ".join(
        [
            str(question.get("title") or ""),
            str(question.get("hint") or ""),
            str(question.get("explanation") or ""),
        ]
    )
    terms = _extract_cjk_terms(text)
    if not terms:
        return []
    return list(dict.fromkeys(terms))


def _trend_series(attempts: List[Dict[str, Any]], days: int = 14) -> List[int]:
    today = datetime.now().date()
    buckets: Dict[str, List[bool]] = defaultdict(list)
    for item in attempts:
        at_ms = item.get("at") or 0
        if not at_ms:
            continue
        d = datetime.fromtimestamp(at_ms / 1000).date()
        key = d.isoformat()
        buckets[key].append(bool(item.get("correct")))

    series: List[int] = []
    last_value = 0
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        key = day.isoformat()
        values = buckets.get(key) or []
        if not values:
            series.append(last_value)
            continue
        rate = int(round(sum(1 for v in values if v) / len(values) * 100))
        series.append(rate)
        last_value = rate
    return series


def _level_from_rate(rate: int) -> Tuple[str, str, str]:
    if rate >= 60:
        return ("高", "bg-rose-500/15 text-rose-200", "bg-rose-400")
    if rate >= 40:
        return ("中", "bg-amber-500/15 text-amber-200", "bg-amber-400")
    return ("低", "bg-emerald-500/15 text-emerald-200", "bg-emerald-400")


@router.get("/wrongbook/summary")
async def wrongbook_summary_handler(user: AuthUser = Depends(require_auth)):
    """错题本汇总数据（仅学生端测验）"""
    try:
        quizzes = await list_quizzes(scope="student", user_id=user.id, username=user.username)
        wrong_questions: List[Dict[str, Any]] = []
        mastered_questions: List[Dict[str, Any]] = []
        all_attempts: List[Dict[str, Any]] = []
        wrong_categories: Dict[str, int] = defaultdict(int)
        term_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"wrong": 0, "total": 0})

        for quiz in quizzes:
            quiz_id = quiz.get("id")
            if not quiz_id:
                continue
            questions = await json_storage.get(f"quiz:{quiz_id}:quiz") or []
            attempts = await get_quiz_attempts(quiz_id)
            if not questions or not attempts:
                continue

            attempt_map: Dict[int, Dict[str, Any]] = {}
            review_counts: Dict[int, int] = defaultdict(int)
            for item in attempts:
                qid = item.get("questionId")
                if qid is None:
                    continue
                review_counts[qid] += 1
                prev = attempt_map.get(qid)
                if not prev or (item.get("at") or 0) >= (prev.get("at") or 0):
                    attempt_map[qid] = item

            topic_name = quiz.get("title") or "测验"
            topic_difficulty = quiz.get("difficulty") or "medium"
            level_map = {"easy": "简单", "medium": "中等", "hard": "困难"}
            level_label = level_map.get(str(topic_difficulty).lower(), "中等")
            quiz_time = _to_ms(quiz.get("updated_at") or quiz.get("created_at"))

            for q in questions:
                qid = q.get("id")
                if qid is None or qid not in attempt_map:
                    continue
                attempt = attempt_map[qid]
                correct = bool(attempt.get("correct"))
                at_ms = attempt.get("at") or quiz_time
                correct_idx = q.get("correct")
                if isinstance(correct_idx, int):
                    correct_idx = max(0, correct_idx - 1)
                else:
                    correct_idx = 0

                item = {
                    "id": qid,
                    "quizId": quiz_id,
                    "title": q.get("question") or "未命名题目",
                    "subject": topic_name,
                    "time": int(at_ms or 0),
                    "topic": topic_name,
                    "level": level_label,
                    "accuracy": 100 if correct else 0,
                    "reviewCount": review_counts.get(qid, 1),
                    "tag": "已掌握" if correct else "错题",
                    "tone": "bg-emerald-500/15 text-emerald-200" if correct else "bg-rose-500/15 text-rose-200",
                    "note": attempt.get("explanation") or attempt.get("correctOption") or "",
                    "options": q.get("options") or [],
                    "correct": correct_idx,
                    "explanation": q.get("explanation") or attempt.get("explanation") or "",
                    "hint": q.get("hint") or "",
                }

                if correct:
                    mastered_questions.append(item)
                else:
                    wrong_questions.append(item)
                    wrong_categories[_category_for_question(item["title"])]+= 1

                terms = _extract_question_terms(item)
                for term in terms:
                    term_stats[term]["total"] += 1
                    if not correct:
                        term_stats[term]["wrong"] += 1
                all_attempts.append({"correct": correct, "at": at_ms})

        total = len(wrong_questions) + len(mastered_questions)
        mastery_rate = int(round((len(mastered_questions) / total) * 100)) if total else 0

        recent_window = datetime.now() - timedelta(days=7)
        recent_wrong = sum(1 for item in wrong_questions if (item.get("time") or 0) >= int(recent_window.timestamp() * 1000))

        intervals = []
        attempt_times = sorted([a.get("at") for a in all_attempts if a.get("at")])
        for i in range(1, len(attempt_times)):
            delta = (attempt_times[i] - attempt_times[i - 1]) / (1000 * 60 * 60 * 24)
            if delta >= 0:
                intervals.append(delta)
        review_interval = round(sum(intervals) / len(intervals), 1) if intervals else 0

        breakdown = []
        if wrong_categories:
            total_wrong = sum(wrong_categories.values())
            for name, count in wrong_categories.items():
                value = int(round(count / total_wrong * 100)) if total_wrong else 0
                breakdown.append({"name": name, "value": value})
        breakdown.sort(key=lambda x: x["value"], reverse=True)

        weak_topics = []
        for name, stats in term_stats.items():
            total_count = stats.get("total") or 0
            wrong_count = stats.get("wrong") or 0
            if total_count == 0 or wrong_count == 0:
                continue
            rate = int(round(wrong_count / total_count * 100))
            level, badge_tone, bar_tone = _level_from_rate(rate)
            suggestion = "建议补充同类练习" if rate >= 60 else "建议巩固核心概念" if rate >= 40 else "保持节奏，适当提升难度"
            weak_topics.append({
                "name": name,
                "wrong": wrong_count,
                "total": total_count,
                "rate": rate,
                "level": level,
                "badgeTone": badge_tone,
                "barTone": bar_tone,
                "suggestion": suggestion,
            })
        weak_topics.sort(key=lambda x: (x["wrong"], x["rate"]), reverse=True)

        trend = _trend_series(all_attempts, 14)

        return {
            "ok": True,
            "stats": {
                "wrongCount": len(wrong_questions),
                "masteredCount": len(mastered_questions),
                "totalCount": total,
                "masteryRate": mastery_rate,
                "reviewIntervalDays": review_interval,
                "newWrongCount": recent_wrong,
            },
            "breakdown": breakdown[:4],
            "weakTopics": weak_topics[:6],
            "masteryTrend": trend,
            "wrongQuestions": wrong_questions,
            "masteredQuestions": mastered_questions,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


register_task_handler("quiz", run_quiz_generation_worker)


@router.post("/wrongbook/report")
async def wrongbook_report_handler(user: AuthUser = Depends(require_auth)):
    """生成错题统计报告"""
    try:
        summary = await wrongbook_summary_handler(user)
        if isinstance(summary, tuple) or not summary.get("ok"):
            return {"ok": False, "error": "summary_failed"}, 500

        agent = WrongBookReportAgent()
        input_data = WrongBookReportInput(summary=summary)
        result = await agent.execute(input_data)
        if not result.success or not result.report:
            return {"ok": False, "error": result.error or "report_failed"}, 500
        return {"ok": True, "report": result.report}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


@router.post("/wrongbook/weak-points")
async def wrongbook_weak_points_handler(user: AuthUser = Depends(require_auth)):
    """使用 LLM 从错题中提取精确薄弱知识点"""
    try:
        summary = await wrongbook_summary_handler(user)
        if isinstance(summary, tuple) or not summary.get("ok"):
            return {"ok": False, "error": "summary_failed"}, 500

        wrong_questions = summary.get("wrongQuestions") or []
        if not wrong_questions:
            return {"ok": True, "points": []}

        agent = KnowledgePointAgent()
        input_data = KnowledgePointInput(wrong_questions=wrong_questions)
        result = await agent.execute(input_data)

        points = result.points if result.points else []
        return {"ok": True, "points": points}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500
