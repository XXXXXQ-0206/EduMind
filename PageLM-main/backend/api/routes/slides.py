"""
幻灯片 API 路由
生成大纲 + 配图（即梦纯图无文字），仅展示不生成 pptx
"""
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from agents.slides_agent import SlidesAgent, SlidesInput
from config import config
from utils.auth import require_auth
from utils.auth_db import AuthUser
from utils.storage import json_storage, list_files_for_user, owner_payload, record_belongs_to_user


router = APIRouter()


class SlidesGenerateRequest(BaseModel):
    topic: str
    pageCount: Optional[int] = 10
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None


@router.post("/slides/generate")
async def generate_slides(request: SlidesGenerateRequest, user: AuthUser = Depends(require_auth)):
    """生成大纲与配图：返回 slideId、大纲与插图预览（不生成 pptx）。"""
    topic = (request.topic or "").strip()
    if not topic:
        return JSONResponse(
            content={"ok": False, "error": "请输入主题"},
            status_code=400,
        )
    page_count = max(5, min(25, request.pageCount or 10))
    include_materials = bool(request.includeMaterials)
    material_ids = request.materialIds or []

    # 可选：从备课资料中读取文本（与 quiz/podcast 类似）
    materials_text = ""
    if include_materials and material_ids:
        files = await list_files_for_user(user.id, user.username, "teacher")
        for fid in material_ids:
            for f in files:
                if f.get("id") == fid:
                    # 简单起见不解析 PDF/Word，仅占位；可后续接入文档解析
                    materials_text += f"[资料: {f.get('originalName', '')}]\n"
                    break

    slide_id = f"slide-{uuid.uuid4().hex[:12]}"
    agent = SlidesAgent()
    input_data = SlidesInput(
        topic=topic,
        page_count=page_count,
        materials_text=materials_text.strip() or None,
        slide_id=slide_id,
    )

    try:
        result = await agent.execute(input_data)
    except Exception as e:
        return JSONResponse(
            content={"ok": False, "error": str(e)},
            status_code=500,
        )

    if not result.success:
        return JSONResponse(
            content={"ok": False, "error": result.error or "生成失败"},
            status_code=500,
        )

    # 元数据写入 storage，供历史列表与详情使用
    meta = {
        "id": slide_id,
        "title": result.title or topic,
        "pageCount": result.page_count,
        "at": __import__("time").time() * 1000,
        **owner_payload(user.id, user.username),
    }
    await json_storage.set(f"slide:{slide_id}", meta)
    await json_storage.set(f"slide:{slide_id}:slides", result.slides or [])

    # 预览中图片需带后端 base URL，前端用 env.backend 拼接（不生成 pptx，无 downloadUrl）
    slides_with_urls = []
    for s in (result.slides or []):
        rec = dict(s)
        if rec.get("imageUrl") and not str(rec["imageUrl"]).startswith("http"):
            name = Path(rec["imageUrl"] or "").name or rec["imageUrl"]
            rec["imageUrl"] = f"{config.backend_url.rstrip('/')}/storage/slides/{slide_id}/{name}"
        slides_with_urls.append(rec)

    return {
        "ok": True,
        "slideId": slide_id,
        "title": result.title,
        "pageCount": result.page_count,
        "slides": slides_with_urls,
    }


@router.get("/slides/{slide_id}")
async def get_slide(slide_id: str, user: AuthUser = Depends(require_auth)):
    """获取单次幻灯片的元数据与预览数据。"""
    meta = await json_storage.get(f"slide:{slide_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        return JSONResponse(
            content={"ok": False, "error": "not found"},
            status_code=404,
        )
    slides = await json_storage.get(f"slide:{slide_id}:slides") or []
    base = config.backend_url.rstrip("/")
    for s in slides:
        if s.get("imageUrl") and not str(s["imageUrl"]).startswith("http"):
            name = Path(s.get("imageUrl") or "").name or s["imageUrl"]
            s["imageUrl"] = f"{base}/storage/slides/{slide_id}/{name}"
    return {
        "ok": True,
        "slide": meta,
        "slides": slides,
    }


@router.get("/slides/{slide_id}/download")
async def download_slide(slide_id: str, user: AuthUser = Depends(require_auth)):
    """下载生成的 .pptx 文件。"""
    meta = await json_storage.get(f"slide:{slide_id}")
    if not meta or not record_belongs_to_user(meta, user.id, user.username):
        return JSONResponse(
            content={"ok": False, "error": "not found"},
            status_code=404,
        )
    pptx_path = (config.storage_dir / "slides" / slide_id / f"{slide_id}.pptx").resolve()
    if not pptx_path.is_file():
        return JSONResponse(
            content={"ok": False, "error": "file not found"},
            status_code=404,
        )
    filename = f"{meta.get('title', slide_id)[:50]}.pptx"
    return FileResponse(
        path=str(pptx_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/slides")
async def list_slides(user: AuthUser = Depends(require_auth)):
    """列出历史幻灯片（教师端）。"""
    # 从 json_storage 中扫描 slide:* 的 meta
    # 简单实现：没有全局 list，只支持通过 generate 返回的 slideId 访问；可后续加 list 键
    return {"ok": True, "slides": []}
