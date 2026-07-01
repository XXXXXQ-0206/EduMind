"""
试卷 API 路由
创建试卷、WebSocket 流式生成、列表、详情、删除、PDF 导出
"""
import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from agents.paper_agent import PaperAgent, PaperInput
from core.task_dispatcher import dispatch_generation_task, register_task_handler
from infrastructure.object_store import create_object_store
from infrastructure.task_lease import acquire_task_lease, release_task_lease
from utils.auth import require_auth, require_websocket_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.live_events import forward_live_events, publish_live_event
from utils.storage import delete_paper, json_storage, list_files_for_user, list_papers, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()
PAPER_TASKS: Dict[str, asyncio.Task[Any]] = {}


def _paper_channel(paper_id: str) -> str:
    return f"paper:{paper_id}"


async def _send_paper_event(paper_id: str, msg: Dict[str, Any]) -> None:
    try:
        await publish_live_event(_paper_channel(paper_id), msg)
    except Exception as e:
        print("[PAPER_DEBUG] send failed paper_id=%s: %s" % (paper_id, e), flush=True)


def _is_paper_task_running(paper_id: str) -> bool:
    task = PAPER_TASKS.get(paper_id)
    return bool(task and not task.done())


async def _ensure_paper_generation(paper_id: str) -> None:
    if _is_paper_task_running(paper_id):
        return

    lease = await acquire_task_lease(f"paper:{paper_id}")
    if not lease:
        return

    async def _runner() -> None:
        try:
            await _run_paper_generation(paper_id)
        finally:
            await release_task_lease(lease)
            PAPER_TASKS.pop(paper_id, None)

    PAPER_TASKS[paper_id] = asyncio.create_task(_runner())


async def _run_paper_generation_worker(paper_id: str) -> None:
    lease = await acquire_task_lease(f"paper:{paper_id}")
    if not lease:
        return
    try:
        await _run_paper_generation(paper_id)
    finally:
        await release_task_lease(lease)


async def _send_paper_snapshot(paper_id: str) -> bool:
    cached = await json_storage.get(f"paper:{paper_id}:paper")
    if isinstance(cached, list) and cached:
        await _send_paper_event(paper_id, {"type": "paper", "paper": cached})
        await _send_paper_event(paper_id, {"type": "done"})
        return True
    run_state = str(await json_storage.get(f"paper:{paper_id}:run_state") or "").strip().lower()
    if run_state == "running":
        await _send_paper_event(paper_id, {"type": "phase", "value": "generating"})
    if run_state == "failed":
        await _send_paper_event(paper_id, {"type": "error", "error": "paper_generation_failed"})
        return True
    return False


async def _run_paper_generation(paper_id: str) -> None:
    topic = await json_storage.get(f"paper:{paper_id}:topic")
    materials_cfg = await json_storage.get(f"paper:{paper_id}:materials") or {}
    use_materials = bool(materials_cfg.get("include"))
    material_ids = list(materials_cfg.get("ids") or [])
    difficulty = await json_storage.get(f"paper:{paper_id}:difficulty") or "medium"
    counts = await json_storage.get(f"paper:{paper_id}:counts") or {}
    count_choice = int(counts.get("choice") or 10)
    count_fill = int(counts.get("fill") or 5)
    count_application = int(counts.get("application") or 2)
    cached = await json_storage.get(f"paper:{paper_id}:paper")

    if not topic:
        await _send_paper_event(paper_id, {"type": "error", "error": "Paper topic not found"})
        return

    if isinstance(cached, list) and cached:
        await _send_paper_event(paper_id, {"type": "paper", "paper": cached})
        await _send_paper_event(paper_id, {"type": "done"})
        return

    await json_storage.set(f"paper:{paper_id}:run_state", "running")
    await _send_paper_event(paper_id, {"type": "phase", "value": "generating"})

    if use_materials and material_ids:
        meta = await json_storage.get(f"paper:{paper_id}") or {}
        owner_id = int(meta.get("owner_id") or 0)
        owner_username = str(meta.get("owner_username") or "")
        files = await list_files_for_user(owner_id, owner_username, "teacher")
        materials_text = await build_selected_files_context(files, material_ids, max_chars=8000, snippet_chars=8000)
        if materials_text:
            topic = f"{topic}\n\n备课资料内容:\n{materials_text}\n\n请优先基于资料出题，不足处再补充常识。"

    agent = PaperAgent()
    input_data = PaperInput(
        topic=topic,
        count_choice=count_choice,
        count_fill=count_fill,
        count_application=count_application,
        difficulty=difficulty,
    )

    try:
        result = await agent.execute(input_data)
    except Exception as exc:
        await json_storage.set(f"paper:{paper_id}:run_state", "failed")
        await _send_paper_event(paper_id, {"type": "error", "error": str(exc)})
        return

    if result.success and result.paper:
        paper_data = [p.dict() for p in result.paper]
        print("[PAPER_DEBUG] Agent returned paper_id=%s, questions_count=%d" % (paper_id, len(paper_data)), flush=True)
        if not isinstance(await json_storage.get(f"paper:{paper_id}"), dict):
            return
        await json_storage.set(f"paper:{paper_id}:paper", paper_data)
        meta = await json_storage.get(f"paper:{paper_id}") or {}
        if isinstance(meta, dict):
            meta["updated_at"] = __import__("datetime").datetime.now().isoformat()
            await json_storage.set(f"paper:{paper_id}", meta)
        await json_storage.set(f"paper:{paper_id}:run_state", "done")
        await _send_paper_event(paper_id, {"type": "paper", "paper": paper_data})
        await _send_paper_event(paper_id, {"type": "done"})
        return

    await json_storage.set(f"paper:{paper_id}:run_state", "failed")
    await _send_paper_event(paper_id, {"type": "error", "error": result.error or "生成失败"})

PDF_THEME = {
    "primary": (0.12, 0.23, 0.37),
    "secondary": (0.17, 0.32, 0.51),
    "text": (0.10, 0.13, 0.17),
    "muted": (0.45, 0.51, 0.58),
}


class PaperRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None
    difficulty: Optional[str] = "medium"
    count_choice: Optional[int] = 10
    count_fill: Optional[int] = 5
    count_application: Optional[int] = 2


@router.post("/paper")
async def create_paper(request: PaperRequest, user: AuthUser = Depends(require_auth)):
    """创建试卷（返回 paperId 与 stream URL）"""
    try:
        topic = (request.topic or "").strip()
        if not topic:
            return JSONResponse(content={"ok": False, "error": "topic required"}, status_code=400)

        paper_id = str(uuid.uuid4())
        include_materials = bool(request.includeMaterials)
        material_ids = list(request.materialIds or [])
        difficulty = (request.difficulty or "medium").strip().lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        count_choice = max(0, min(30, int(request.count_choice or 10)))
        count_fill = max(0, min(20, int(request.count_fill or 5)))
        count_application = max(0, min(20, int(request.count_application or 2)))

        await json_storage.set(f"paper:{paper_id}:topic", topic)
        await json_storage.set(f"paper:{paper_id}:materials", {"include": include_materials, "ids": material_ids})
        await json_storage.set(f"paper:{paper_id}:difficulty", difficulty)
        await json_storage.set(
            f"paper:{paper_id}:counts",
            {"choice": count_choice, "fill": count_fill, "application": count_application},
        )
        await json_storage.set(
            f"paper:{paper_id}",
            {
                "id": paper_id,
                "title": topic[:100],
                "count_choice": count_choice,
                "count_fill": count_fill,
                "count_application": count_application,
                "difficulty": difficulty,
                "scope": "teacher",
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "updated_at": __import__("datetime").datetime.now().isoformat(),
                **owner_payload(user.id, user.username),
            },
        )
        await dispatch_generation_task("paper", paper_id, _ensure_paper_generation)

        return JSONResponse(
            status_code=202,
            content={
                "ok": True,
                "paperId": paper_id,
                "stream": f"/ws/paper?paperId={paper_id}",
            },
        )
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.websocket("/ws/paper")
async def paper_websocket(websocket: WebSocket):
    """试卷生成 WebSocket"""
    await websocket.accept()
    user = await require_websocket_auth(websocket)
    if not user:
        return
    query_params = dict(websocket.query_params)
    paper_id = query_params.get("paperId")
    if not paper_id:
        await websocket.close(code=1008, reason="paperId required")
        return

    meta = await json_storage.get(f"paper:{paper_id}") or {}
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        await websocket.close(code=1008, reason="not found")
        return

    forwarder = asyncio.create_task(forward_live_events(websocket, _paper_channel(paper_id)))
    await asyncio.sleep(0)
    try:
        await websocket.send_json({"type": "ready", "paperId": paper_id})
        done = await _send_paper_snapshot(paper_id)
        if not done:
            await dispatch_generation_task("paper", paper_id, _ensure_paper_generation)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await json_storage.set(f"paper:{paper_id}:run_state", "failed")
        except Exception:
            pass
        try:
            await _send_paper_event(paper_id, {"type": "error", "error": str(e)})
        except Exception:
            pass
    finally:
        forwarder.cancel()
        try:
            await forwarder
        except asyncio.CancelledError:
            pass


@router.get("/papers")
async def list_papers_handler(user: AuthUser = Depends(require_auth)):
    """列出试卷历史（教师端）"""
    try:
        papers = await list_papers(user.id, user.username)
        return {"ok": True, "papers": papers}
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)


@router.get("/papers/{paper_id}")
async def get_paper_handler(paper_id: str, user: AuthUser = Depends(require_auth)):
    """获取试卷详情"""
    if not paper_id or paper_id in ("undefined", "null"):
        return JSONResponse(content={"ok": False, "error": "Invalid paperId"}, status_code=400)
    meta = await json_storage.get(f"paper:{paper_id}")
    questions = await json_storage.get(f"paper:{paper_id}:paper")
    if not meta or not questions or not record_belongs_to_user(meta, user.id, user.username):
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    return {"ok": True, "paper": meta, "questions": questions}


@router.delete("/papers/{paper_id}")
async def delete_paper_handler(paper_id: str, user: AuthUser = Depends(require_auth)):
    """删除试卷"""
    if not paper_id or paper_id in ("undefined", "null"):
        return JSONResponse(content={"ok": False, "error": "Invalid paperId"}, status_code=400)
    meta = await json_storage.get(f"paper:{paper_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        return JSONResponse(content={"ok": False, "error": "not found"}, status_code=404)
    await delete_paper(paper_id)
    return {"ok": True}


def _build_paper_pdf(questions: List[Dict[str, Any]], meta: Dict[str, Any], out_path: Path) -> None:
    """使用 reportlab 生成试卷 PDF（含题目与答案）。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_registered = False
    for font_name, font_path in [
        ("SimSun", os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simsun.ttc")),
        ("SimSun", os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simsun.ttf")),
        ("SimHei", os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simhei.ttf")),
    ]:
        if os.path.isfile(font_path):
            try:
                pdfmetrics.registerFont(TTFont("CJK", font_path))
                font_registered = True
                break
            except Exception:
                pass
    if not font_registered:
        try:
            pdfmetrics.registerFont(TTFont("CJK", "SimHei.ttf"))
            font_registered = True
        except Exception:
            pass
    font_name = "CJK" if font_registered else "Helvetica"

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    margin = 20 * mm
    x = margin
    y = height - margin
    line_height = 5 * mm
    primary = PDF_THEME["primary"]
    secondary = PDF_THEME["secondary"]
    text_color = PDF_THEME["text"]
    muted = PDF_THEME["muted"]

    def draw_line(text: str, font_size: int = 10, color: tuple = text_color):
        nonlocal y
        if y < margin + 25:
            c.showPage()
            y = height - margin
        c.setFont(font_name, font_size)
        c.setFillColorRGB(*color)
        for i in range(0, len(text), 60):
            chunk = text[i : i + 60]
            c.drawString(x, y, chunk)
            y -= line_height
        y -= line_height * 0.3

    title = (meta.get("title") or "试卷").strip()
    c.setFont(font_name, 16)
    c.setFillColorRGB(*primary)
    c.drawString(x, y, title[:80])
    y -= line_height * 2

    for i, q in enumerate(questions):
        qtype = (q.get("type") or "choice").strip()
        question = (q.get("question") or "").strip()
        draw_line(f"{i + 1}. {question}", 10, text_color)
        if qtype == "choice":
            opts = q.get("options") or []
            correct_idx = (q.get("correct") or 1) - 1
            for j, opt in enumerate(opts[:4]):
                mark = " ✓" if j == correct_idx else ""
                draw_line(f"   {chr(65 + j)}. {opt}{mark}", 9, secondary)
            ans = (opts[correct_idx] if 0 <= correct_idx < len(opts) else "") or "见上"
        else:
            ans = (q.get("answer") or "").strip() or "略"
            draw_line(f"   参考答案：{ans}", 9, muted)
        y -= line_height * 0.5

    c.save()


def _pdf_download_response(content: bytes, filename: str) -> Response:
    safe_filename = Path(filename).name or "paper.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}"},
    )


@router.get("/papers/{paper_id}/pdf")
async def export_paper_pdf(paper_id: str, user: AuthUser = Depends(require_auth)):
    """导出试卷为 PDF（题目+答案）"""
    if not paper_id or paper_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid paperId")
    meta = await json_storage.get(f"paper:{paper_id}")
    questions = await json_storage.get(f"paper:{paper_id}:paper")
    if not meta or not questions or not record_belongs_to_user(meta, user.id, user.username):
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_dir = config.storage_dir / ".tmp" / "papers"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    out_path = pdf_dir / f"{paper_id}-{uuid.uuid4().hex}.pdf"
    object_key = f"papers/{paper_id}.pdf"
    object_store = create_object_store()
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _build_paper_pdf, questions, meta, out_path)
        file_url = await object_store.put_file(object_key, out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    finally:
        try:
            out_path.unlink()
        except Exception:
            pass

    def remember_pdf(current):
        next_meta = dict(current if isinstance(current, dict) else meta)
        next_meta["pdfObjectKey"] = object_key
        next_meta["pdfUrl"] = file_url
        return next_meta

    await json_storage.update(f"paper:{paper_id}", remember_pdf, default=meta)
    filename = f"{(meta.get('title') or '试卷')[:50]}.pdf"
    return _pdf_download_response(await object_store.get_bytes(object_key), filename)


register_task_handler("paper", _run_paper_generation_worker)
