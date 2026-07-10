"""
教案 API 路由
创建教案、列表、详情、删除、PDF 导出（学术权威主题色）
"""
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from agents.lesson_plan_agent import LessonPlanAgent, LessonPlanInput
from infrastructure.object_store import create_object_store
from utils.api_errors import raise_safe_http_error
from utils.auth import get_request_user, resolve_user_from_token, require_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.lesson_plan_docx import (
    build_lesson_plan_docx,
    extract_template_placeholders,
    make_template_preview,
)
from utils.parser import extract_text_from_file_bytes
from utils.storage import delete_lesson_plan, json_storage, list_files_for_user, list_lesson_plans, owner_payload, record_belongs_to_user
from config import config


router = APIRouter()
logger = logging.getLogger(__name__)

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
    templateId: Optional[str] = None


async def _build_material_context_async(material_ids: List[str], user: AuthUser, query: str) -> str:
    if not material_ids:
        return ""
    files = await list_files_for_user(user.id, user.username, "teacher")
    return await build_selected_files_context(
        files,
        material_ids,
        max_chars=8000,
        snippet_chars=8000,
        query=query,
        owner_id=user.id,
        role="teacher",
    )


def _lesson_plan_template_key(user: AuthUser) -> str:
    return f"lesson_plan_template:user:{user.id}"


def _lesson_plan_template_history_key(user: AuthUser) -> str:
    return f"lesson_plan_template_history:user:{user.id}"


def _template_download_response(content: bytes, filename: str) -> Response:
    safe_filename = Path(filename).name or "lesson-plan.docx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}"},
    )


def _word_template_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(content={"ok": False, "error": message}, status_code=status_code)


async def _active_lesson_plan_template(user: AuthUser) -> Optional[Dict[str, Any]]:
    template = await json_storage.get(_lesson_plan_template_key(user))
    if not isinstance(template, dict):
        return None
    if not record_belongs_to_user(template, user.id, user.username):
        return None
    return template


async def _delete_template_objects(template: Optional[Dict[str, Any]]) -> None:
    if not isinstance(template, dict):
        return
    object_store = create_object_store()
    keys = {
        str(template.get("objectKey") or "").strip(),
        str(template.get("styleObjectKey") or "").strip(),
    }
    for key in {item for item in keys if item}:
        try:
            await object_store.delete(key)
        except Exception:
            pass


async def _try_convert_doc_template(content: bytes, out_path: Path) -> bool:
    """Best-effort conversion for legacy .doc templates into a DOCX style source."""
    import shutil
    import subprocess
    import tempfile

    tmp_root = (config.storage_dir / ".tmp" / "lesson_plan_templates").resolve()
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="template-doc-", dir=str(tmp_root)) as temp_name:
        temp_dir = Path(temp_name).resolve()
        source = temp_dir / "template.doc"
        source.write_bytes(content)

        try:
            import win32com.client  # type: ignore

            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(str(source), False, True)
            try:
                doc.SaveAs2(str(out_path), FileFormat=12)
            finally:
                doc.Close(False)
                word.Quit()
            if out_path.exists():
                return True
        except Exception:
            pass

        try:
            soffice = shutil.which("soffice") or shutil.which("libreoffice")
            if not soffice:
                return False
            subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    str(temp_dir),
                    "--",
                    str(source),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            converted = temp_dir / "template.docx"
            if converted.exists():
                out_path.write_bytes(converted.read_bytes())
                return True
        except Exception:
            pass
    return False


async def _build_and_store_lesson_plan_docx(
    lesson_plan_id: str,
    plan_data: Dict[str, Any],
    meta: Dict[str, Any],
    template: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    object_store = create_object_store()
    docx_dir = config.storage_dir / ".tmp" / "lesson_plans"
    docx_dir.mkdir(parents=True, exist_ok=True)
    out_path = docx_dir / f"{lesson_plan_id}-{uuid.uuid4().hex}.docx"
    object_key = f"lesson_plans/{lesson_plan_id}.docx"

    template_path: Optional[Path] = None
    template_text = ""
    template_mode = "default"
    if isinstance(template, dict):
        template_text = str(template.get("text") or "")
        style_key = str(template.get("styleObjectKey") or template.get("objectKey") or "")
        if style_key:
            try:
                candidate = object_store.path_for(style_key)
                if candidate.suffix.lower() == ".docx" and candidate.exists():
                    template_path = candidate
                    template_mode = "docx"
            except Exception:
                template_path = None
        if template_path is None and template_text:
            template_mode = "text"

    try:
        await asyncio.to_thread(
            build_lesson_plan_docx,
            plan_data,
            meta,
            out_path,
            template_path=template_path,
            template_text=template_text,
        )
        file_url = await object_store.put_file(object_key, out_path)
        return {
            "docxObjectKey": object_key,
            "docxUrl": file_url,
            "templateId": template.get("id") if isinstance(template, dict) else None,
            "templateName": template.get("originalName") if isinstance(template, dict) else None,
            "templateMode": template_mode,
            "templateApplied": template_mode == "docx",
            "templateStyleSourceAvailable": template_mode == "docx",
        }
    finally:
        try:
            out_path.unlink()
        except Exception:
            pass


@router.get("/lesson-plan/template")
async def get_lesson_plan_template(user: AuthUser = Depends(require_auth)):
    """获取当前账号正在使用的教案 Word 模板。"""
    template = await _active_lesson_plan_template(user)
    if isinstance(template, dict):
        template = {key: value for key, value in template.items() if key != "text"}
    return {"ok": True, "template": template}


@router.post("/lesson-plan/template")
async def upload_lesson_plan_template(file: UploadFile = File(...), user: AuthUser = Depends(require_auth)):
    """上传 DOC/DOCX 教案模板，作为后续教案生成的当前模板。"""
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".doc", ".docx"}:
        return _word_template_error("仅支持上传 .doc 或 .docx 模板文件")

    content = await file.read()
    if not content:
        return _word_template_error("模板文件为空")
    if len(content) > 20 * 1024 * 1024:
        return _word_template_error("模板文件不能超过 20MB")

    try:
        text = await extract_text_from_file_bytes(content, filename=filename, mime_type=file.content_type)
    except Exception as exc:
        raise_safe_http_error(logger, exc, "模板解析失败，请确认文件可以正常打开", status_code=400)
    text = (text or "")[:50000]

    template_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    object_store = create_object_store()
    converted_path: Optional[Path] = None
    if suffix == ".doc":
        converted_path = config.storage_dir / ".tmp" / "lesson_plan_templates" / f"{template_id}.docx"
        converted = await _try_convert_doc_template(content, converted_path)
        if not converted:
            return _word_template_error(
                "当前运行环境无法将 .doc 模板转换为 .docx，不能保留原模板格式。请在 Word/WPS 中另存为 .docx 后重新上传。",
                status_code=400,
            )

    object_key = f"lesson_plan_templates/{user.id}/{template_id}{suffix}"
    file_url = await object_store.put_bytes(object_key, content)
    style_object_key = object_key if suffix == ".docx" else ""
    style_url = file_url if suffix == ".docx" else ""

    if converted_path is not None:
        style_object_key = f"lesson_plan_templates/{user.id}/{template_id}.docx"
        style_url = await object_store.put_file(style_object_key, converted_path)
        try:
            converted_path.unlink()
        except Exception:
            pass

    template = {
        "id": template_id,
        "originalName": filename or f"template{suffix}",
        "mimeType": file.content_type or (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if suffix == ".docx"
            else "application/msword"
        ),
        "size": len(content),
        "uploadedAt": int(datetime.now().timestamp() * 1000),
        "created_at": now,
        "updated_at": now,
        "objectKey": object_key,
        "url": file_url,
        "styleObjectKey": style_object_key,
        "styleUrl": style_url,
        "styleSourceAvailable": bool(style_object_key),
        "text": text,
        "textPreview": make_template_preview(text),
        "textChars": len(text or ""),
        "placeholders": extract_template_placeholders(text),
        **owner_payload(user.id, user.username),
    }

    previous = await _active_lesson_plan_template(user)
    await _delete_template_objects(previous)
    await json_storage.set(_lesson_plan_template_key(user), template)

    def prepend_history(current):
        items = current if isinstance(current, list) else []
        brief = {key: value for key, value in template.items() if key != "text"}
        return [brief, *items[:9]]

    await json_storage.update(_lesson_plan_template_history_key(user), prepend_history, default=[])
    return {"ok": True, "template": {key: value for key, value in template.items() if key != "text"}}


@router.delete("/lesson-plan/template")
async def delete_lesson_plan_template(user: AuthUser = Depends(require_auth)):
    """删除当前教案 Word 模板。"""
    template = await _active_lesson_plan_template(user)
    await _delete_template_objects(template)
    await json_storage.delete(_lesson_plan_template_key(user))
    return {"ok": True}


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
        materials_text = await _build_material_context_async(material_ids, user, topic)

    template = await _active_lesson_plan_template(user)
    if request.templateId and (not template or str(template.get("id")) != str(request.templateId)):
        return JSONResponse(content={"ok": False, "error": "模板不存在或已失效"}, status_code=404)

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

    try:
        docx_info = await _build_and_store_lesson_plan_docx(lesson_plan_id, plan_data, meta, template)
        meta.update({key: value for key, value in docx_info.items() if value not in (None, "")})
    except Exception as exc:
        raise_safe_http_error(logger, exc, "Word 教案生成失败")

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
            "docxUrl": meta.get("docxUrl"),
            "templateApplied": meta.get("templateApplied"),
            "templateMode": meta.get("templateMode"),
            "templateName": meta.get("templateName"),
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


def _pdf_download_response(content: bytes, filename: str) -> Response:
    safe_filename = Path(filename).name or "lesson-plan.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}"},
    )


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

    pdf_dir = config.storage_dir / ".tmp" / "lesson_plans"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    out_path = pdf_dir / f"{lesson_plan_id}-{uuid.uuid4().hex}.pdf"
    object_key = f"lesson_plans/{lesson_plan_id}.pdf"
    object_store = create_object_store()

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _build_lesson_plan_pdf, plan, meta, out_path)
        file_url = await object_store.put_file(object_key, out_path)
    except Exception as exc:
        raise_safe_http_error(logger, exc, "PDF generation failed")
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

    await json_storage.update(f"lesson_plan:{lesson_plan_id}", remember_pdf, default=meta)

    filename = f"{(meta.get('title') or '教案')[:50]}.pdf"
    return _pdf_download_response(await object_store.get_bytes(object_key), filename)


@router.get("/lesson-plans/{lesson_plan_id}/docx")
async def export_lesson_plan_docx(
    lesson_plan_id: str,
    token: Optional[str] = Query(default=None),
    user: Optional[AuthUser] = Depends(get_request_user),
):
    """导出教案为 Word 文档。"""
    if not lesson_plan_id or lesson_plan_id in ("undefined", "null"):
        raise HTTPException(status_code=400, detail="Invalid lessonPlanId")

    auth_user = user or resolve_user_from_token(token)
    if not auth_user:
        raise HTTPException(status_code=401, detail="请先登录后再访问")

    meta = await json_storage.get(f"lesson_plan:{lesson_plan_id}")
    plan = await json_storage.get(f"lesson_plan:{lesson_plan_id}:plan")
    if not meta or not plan or not record_belongs_to_user(meta, auth_user.id, auth_user.username):
        raise HTTPException(status_code=404, detail="Lesson plan not found")

    object_store = create_object_store()
    object_key = str(meta.get("docxObjectKey") or f"lesson_plans/{lesson_plan_id}.docx")
    template = await _active_lesson_plan_template(auth_user)
    active_template_id = str(template.get("id") or "") if isinstance(template, dict) else ""
    stored_template_id = str(meta.get("templateId") or "")
    should_refresh_for_template = bool(active_template_id and active_template_id != stored_template_id)
    content: Optional[bytes] = None

    if not should_refresh_for_template:
        try:
            content = await object_store.get_bytes(object_key)
        except Exception:
            content = None

    if content is None:
        try:
            docx_info = await _build_and_store_lesson_plan_docx(lesson_plan_id, plan, meta, template)
            object_key = str(docx_info.get("docxObjectKey") or object_key)

            def remember_docx(current):
                next_meta = dict(current if isinstance(current, dict) else meta)
                next_meta.update({key: value for key, value in docx_info.items() if value not in (None, "")})
                return next_meta

            await json_storage.update(f"lesson_plan:{lesson_plan_id}", remember_docx, default=meta)
            content = await object_store.get_bytes(object_key)
        except Exception as exc:
            raise_safe_http_error(logger, exc, "Word 教案生成失败")

    filename = f"{(meta.get('title') or '教案')[:50]}.docx"
    return _template_download_response(content, filename)
