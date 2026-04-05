"""
试卷 API 路由
创建试卷、WebSocket 流式生成、列表、详情、删除、PDF 导出
"""
import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import aiofiles

from agents.paper_agent import PaperAgent, PaperInput
from utils.auth import require_auth, require_websocket_auth
from utils.auth_db import AuthUser
from utils.websocket import manager
from utils.storage import delete_paper, json_storage, list_files_for_user, list_papers, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()

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

    await manager.connect(websocket, paper_id)

    async def safe_send(msg: dict) -> None:
        try:
            await manager.send_message(msg, paper_id)
        except Exception as e:
            print("[PAPER_DEBUG] safe_send failed (client may have disconnected): %s" % e, flush=True)

    try:
        await safe_send({"type": "ready", "paperId": paper_id})

        topic = await json_storage.get(f"paper:{paper_id}:topic")
        materials_cfg = await json_storage.get(f"paper:{paper_id}:materials") or {}
        use_materials = bool(materials_cfg.get("include"))
        material_ids = list(materials_cfg.get("ids") or [])
        difficulty = await json_storage.get(f"paper:{paper_id}:difficulty") or "medium"
        counts = await json_storage.get(f"paper:{paper_id}:counts") or {}
        count_choice = int(counts.get("choice") or 10)
        count_fill = int(counts.get("fill") or 5)
        count_application = int(counts.get("application") or 2)

        if not topic:
            await safe_send({"type": "error", "error": "Paper topic not found"})
            try:
                await websocket.close(code=1000, reason="Topic not found")
            except Exception:
                pass
            return

        await safe_send({"type": "phase", "value": "generating"})

        if use_materials and material_ids:
            meta = await json_storage.get(f"paper:{paper_id}") or {}
            owner_id = int(meta.get("owner_id") or 0)
            owner_username = str(meta.get("owner_username") or "")
            files = await list_files_for_user(owner_id, owner_username, "teacher")
            file_map = {f.get("id"): f for f in files if f.get("id")}
            max_chars = 8000
            parts: List[str] = []
            used = 0

            async def read_sidecar_text(file_path: str) -> str:
                txt_path = Path(file_path + ".txt")
                if not txt_path.exists():
                    return ""
                try:
                    async with aiofiles.open(txt_path, "r", encoding="utf-8") as f:
                        return await f.read()
                except Exception:
                    return ""

            for fid in material_ids:
                meta = file_map.get(fid)
                if not meta:
                    continue
                filename = meta.get("filename")
                if not filename:
                    continue
                file_path = str(config.storage_dir / "uploads" / filename)
                text = await read_sidecar_text(file_path)
                if not text:
                    try:
                        from utils.parser import extract_text_from_file
                        text = await extract_text_from_file(file_path, meta.get("mimeType"))
                    except Exception:
                        text = ""
                if not text:
                    continue
                remaining = max_chars - used
                if remaining <= 0:
                    break
                snippet = text[:remaining]
                header = f"\n\n[资料] {meta.get('originalName') or filename}\n"
                parts.append(header + snippet)
                used += len(snippet)

            materials_text = "".join(parts).strip()
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
        result = await agent.execute(input_data)

        if result.success and result.paper:
            paper_data = [p.dict() for p in result.paper]
            print("[PAPER_DEBUG] Agent returned paper_id=%s, questions_count=%d" % (paper_id, len(paper_data)), flush=True)
            if paper_data:
                first = paper_data[0]
                q = str(first.get("question", ""))
                print("[PAPER_DEBUG] First question: type=%s, question_len=%d, preview=%s" % (first.get("type"), len(q), (q[:80] + "..." if len(q) > 80 else q)), flush=True)
            await json_storage.set(f"paper:{paper_id}:paper", paper_data)
            meta = await json_storage.get(f"paper:{paper_id}") or {}
            meta["updated_at"] = __import__("datetime").datetime.now().isoformat()
            await json_storage.set(f"paper:{paper_id}", meta)
            print("[PAPER_DEBUG] Sending paper to client, paper_id=%s, payload_questions_count=%d" % (paper_id, len(paper_data)), flush=True)
            await safe_send({"type": "paper", "paper": paper_data})
            await safe_send({"type": "done"})
        else:
            print("[PAPER_DEBUG] Agent failed: success=%s, error=%s" % (result.success, getattr(result, "error", None)), flush=True)
            await safe_send({"type": "error", "error": result.error or "生成失败"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, paper_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            await manager.send_message({"type": "error", "error": str(e)}, paper_id)
        except Exception:
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


@router.get("/papers/{paper_id}/pdf")
async def export_paper_pdf(paper_id: str, user: AuthUser = Depends(require_auth)):
    """导出试卷为 PDF（题目+答案）"""
    if not paper_id or paper_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid paperId")
    meta = await json_storage.get(f"paper:{paper_id}")
    questions = await json_storage.get(f"paper:{paper_id}:paper")
    if not meta or not questions or not record_belongs_to_user(meta, user.id, user.username):
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_dir = config.storage_dir / "papers"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    out_path = pdf_dir / f"{paper_id}.pdf"
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _build_paper_pdf, questions, meta, out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    filename = f"{(meta.get('title') or '试卷')[:50]}.pdf"
    return FileResponse(path=str(out_path), media_type="application/pdf", filename=filename)
