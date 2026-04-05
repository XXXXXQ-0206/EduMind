"""
教案 API 路由
创建教案、列表、详情、删除、PDF 导出（学术权威主题色）
"""
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import aiofiles

from agents.lesson_plan_agent import LessonPlanAgent, LessonPlanInput
from utils.auth import get_request_user, resolve_user_from_token, require_auth
from utils.auth_db import AuthUser
from utils.storage import delete_lesson_plan, json_storage, list_files_for_user, list_lesson_plans, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()

# 学术权威主题色（用于 PDF）
PDF_THEME = {
    "primary": (0.12, 0.23, 0.37),      # #1e3a5f
    "secondary": (0.17, 0.32, 0.51),     # #2c5282
    "text": (0.10, 0.13, 0.17),          # #1a202c
    "muted": (0.45, 0.51, 0.58),         # #718096
    "page_bg": (0.97, 0.98, 0.99),       # #f7fafc
}


class LessonPlanRequest(BaseModel):
    topic: str
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None


async def _build_material_context_async(material_ids: List[str], user: AuthUser) -> str:
    if not material_ids:
        return ""
    files = await list_files_for_user(user.id, user.username, "teacher")
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

    return "".join(parts).strip()


@router.post("/lesson-plan")
async def create_lesson_plan(request: LessonPlanRequest, user: AuthUser = Depends(require_auth)):
    """创建教案（同步生成后返回）"""
    topic = (request.topic or "").strip()
    if not topic:
        return JSONResponse(content={"ok": False, "error": "topic required"}, status_code=400)

    include_materials = bool(request.includeMaterials)
    material_ids = list(request.materialIds or [])
    materials_text = ""
    if include_materials and material_ids:
        materials_text = await _build_material_context_async(material_ids, user)

    agent = LessonPlanAgent()
    result = await agent.execute(
        LessonPlanInput(topic=topic, materials_context=materials_text or None)
    )

    if not result.success or not result.plan:
        return JSONResponse(
            content={"ok": False, "error": result.error or "教案生成失败，请重试。"},
            status_code=500,
        )

    lesson_plan_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    meta = {
        "id": lesson_plan_id,
        "title": result.plan.title[:100],
        "created_at": now,
        "updated_at": now,
        **owner_payload(user.id, user.username),
    }
    plan_data = result.plan.model_dump()

    await json_storage.set(f"lesson_plan:{lesson_plan_id}", meta)
    await json_storage.set(f"lesson_plan:{lesson_plan_id}:topic", topic)
    await json_storage.set(
        f"lesson_plan:{lesson_plan_id}:materials",
        {"include": include_materials, "ids": material_ids},
    )
    await json_storage.set(f"lesson_plan:{lesson_plan_id}:plan", plan_data)

    return JSONResponse(
        content={
            "ok": True,
            "lessonPlanId": lesson_plan_id,
            "plan": plan_data,
            "meta": meta,
        },
    )


@router.get("/lesson-plans")
async def list_lesson_plans_handler(user: AuthUser = Depends(require_auth)):
    """列出教案历史"""
    plans = await list_lesson_plans(user.id, user.username)
    return {"ok": True, "lessonPlans": plans}


@router.get("/lesson-plans/{lesson_plan_id}")
async def get_lesson_plan_handler(lesson_plan_id: str, user: AuthUser = Depends(require_auth)):
    """获取教案详情"""
    if not lesson_plan_id or lesson_plan_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid lessonPlanId")
    meta = await json_storage.get(f"lesson_plan:{lesson_plan_id}")
    plan = await json_storage.get(f"lesson_plan:{lesson_plan_id}:plan")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return {"ok": True, "meta": meta, "plan": plan or {}}


@router.delete("/lesson-plans/{lesson_plan_id}")
async def delete_lesson_plan_handler(lesson_plan_id: str, user: AuthUser = Depends(require_auth)):
    """删除教案"""
    if not lesson_plan_id or lesson_plan_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid lessonPlanId")
    meta = await json_storage.get(f"lesson_plan:{lesson_plan_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    await delete_lesson_plan(lesson_plan_id)
    return {"ok": True}


def _build_lesson_plan_pdf(plan_data: Dict[str, Any], meta: Dict[str, Any], out_path: Path) -> None:
    """使用 reportlab 生成学术权威主题色 PDF。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    # 注册中文字体（优先 Windows 宋体）
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
    line_height = 6 * mm
    primary = PDF_THEME["primary"]
    secondary = PDF_THEME["secondary"]
    text_color = PDF_THEME["text"]
    muted = PDF_THEME["muted"]

    def draw_heading(text: str, size: int = 16, color: tuple = primary):
        nonlocal y
        c.setFont(font_name, size)
        c.setFillColorRGB(*color)
        c.drawString(x, y, text[:200])
        y -= line_height * 1.5

    def draw_subheading(text: str):
        nonlocal y
        y -= line_height * 0.5
        c.setFont(font_name, 12)
        c.setFillColorRGB(*secondary)
        c.drawString(x, y, text[:300])
        y -= line_height

    def draw_paragraph(label: str, content: str, indent: bool = True):
        nonlocal y
        if y < margin + 30:
            c.showPage()
            y = height - margin
        c.setFont(font_name, 10)
        c.setFillColorRGB(*text_color)
        c.drawString(x, y, (label + " " + content)[:500])
        y -= line_height
        if indent and len(content) > 60:
            y -= line_height * 0.5

    title = (plan_data.get("title") or meta.get("title") or "教案").strip()
    c.setFont(font_name, 18)
    c.setFillColorRGB(*primary)
    c.drawString(x, y, title[:100])
    y -= line_height * 2

    # 教学目标（三维）
    tg = plan_data.get("teaching_goals") or {}
    if isinstance(tg, dict):
        draw_heading("一、教学目标（三维目标）")
        for key, label in [("knowledge", "知识与技能："), ("process", "过程与方法："), ("emotion", "情感态度与价值观：")]:
            val = (tg.get(key) or "").strip()
            if val:
                draw_paragraph(label, val)
    y -= line_height

    # 教学重难点
    key_pts = plan_data.get("key_points") or []
    diff_pts = plan_data.get("difficult_points") or []
    draw_heading("二、教学重难点")
    if key_pts:
        c.setFont(font_name, 10)
        c.setFillColorRGB(*text_color)
        c.drawString(x, y, "教学重点：" + "；".join(key_pts)[:400])
        y -= line_height
    if diff_pts:
        c.drawString(x, y, "教学难点：" + "；".join(diff_pts)[:400])
        y -= line_height
    y -= line_height

    # 教学准备
    prep = plan_data.get("preparation") or []
    draw_heading("三、教学准备")
    if prep:
        c.setFont(font_name, 10)
        c.setFillColorRGB(*text_color)
        c.drawString(x, y, "；".join(prep)[:500])
        y -= line_height
    y -= line_height

    # 教学过程
    draw_heading("四、教学过程")
    process = plan_data.get("process") or []
    for step in process:
        if y < margin + 40:
            c.showPage()
            y = height - margin
        t = (step.get("title") or "").strip()
        cont = (step.get("content") or "").strip()
        c.setFont(font_name, 11)
        c.setFillColorRGB(*secondary)
        c.drawString(x, y, t[:100])
        y -= line_height
        c.setFont(font_name, 10)
        c.setFillColorRGB(*text_color)
        for chunk in [cont[i : i + 80] for i in range(0, len(cont), 80)]:
            if y < margin + 20:
                c.showPage()
                y = height - margin
            c.drawString(x + 5 * mm, y, chunk)
            y -= line_height
        y -= line_height * 0.5

    # 作业设计
    homework = (plan_data.get("homework") or "").strip()
    if homework:
        if y < margin + 30:
            c.showPage()
            y = height - margin
        draw_heading("五、作业设计")
        c.setFont(font_name, 10)
        c.setFillColorRGB(*text_color)
        for chunk in [homework[i : i + 80] for i in range(0, len(homework), 80)]:
            if y < margin + 20:
                c.showPage()
                y = height - margin
            c.drawString(x, y, chunk)
            y -= line_height

    c.save()


@router.get("/lesson-plans/{lesson_plan_id}/pdf")
async def export_lesson_plan_pdf(
    lesson_plan_id: str,
    token: Optional[str] = Query(default=None),
    user: Optional[AuthUser] = Depends(get_request_user),
):
    """导出教案为 PDF（学术权威主题色）"""
    if not lesson_plan_id or lesson_plan_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid lessonPlanId")

    auth_user = user or resolve_user_from_token(token)
    if not auth_user:
        raise HTTPException(status_code=401, detail="请先登录后再访问")

    meta = await json_storage.get(f"lesson_plan:{lesson_plan_id}")
    plan = await json_storage.get(f"lesson_plan:{lesson_plan_id}:plan")
    if not meta or not plan or not record_belongs_to_user(meta, auth_user.id, auth_user.username):
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    pdf_dir = config.storage_dir / "lesson_plans"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    out_path = pdf_dir / f"{lesson_plan_id}.pdf"

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _build_lesson_plan_pdf, plan, meta, out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"{(meta.get('title') or '教案')[:50]}.pdf"
    return FileResponse(
        path=str(out_path),
        media_type="application/pdf",
        filename=filename,
    )
