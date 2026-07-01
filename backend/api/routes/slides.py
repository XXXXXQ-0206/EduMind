"""
幻灯片 API 路由
生成大纲 + 配图（即梦纯图无文字），仅展示不生成 pptx
"""
import uuid
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from agents.slides_agent import SlidesAgent, SlidesInput
from config import config
from infrastructure.object_store import create_object_store
from utils.auth import require_auth
from utils.auth_contracts import AuthUser
from utils.feature_support import build_selected_files_context
from utils.storage import json_storage, list_files_for_user, owner_payload, record_belongs_to_user


router = APIRouter()


class SlidesGenerateRequest(BaseModel):
    topic: str
    pageCount: Optional[int] = 10
    includeMaterials: Optional[bool] = False
    materialIds: Optional[List[str]] = None


def _absolute_asset_url(value: Optional[str], *, object_key: Optional[str] = None) -> str:
    candidate = (object_key or value or "").strip()
    if not candidate:
        return ""
    if candidate.startswith(("http://", "https://")):
        return candidate
    if candidate.startswith("/"):
        return f"{config.backend_url.rstrip('/')}{candidate}"
    url = create_object_store().url_for(candidate)
    return f"{config.backend_url.rstrip('/')}{url}" if url.startswith("/") else url


def _normalize_slide_assets(slides: List[dict]) -> List[dict]:
    normalized = []
    for slide in slides:
        rec = dict(slide)
        image_key = str(rec.get("imageObjectKey") or "").strip() or None
        image_url = str(rec.get("imageUrl") or "").strip() or None
        if image_key or image_url:
            rec["imageUrl"] = _absolute_asset_url(image_url, object_key=image_key)
        normalized.append(rec)
    return normalized


def _download_response(content: bytes, filename: str) -> Response:
    safe_filename = Path(filename).name or "slides.pptx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(safe_filename)}"},
    )


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

    materials_text = ""
    if include_materials and material_ids:
        files = await list_files_for_user(user.id, user.username, "teacher")
        materials_text = await build_selected_files_context(
            files,
            material_ids,
            max_chars=10000,
            snippet_chars=4000,
            query=topic,
            owner_id=user.id,
            role="teacher",
        )

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

    return {
        "ok": True,
        "slideId": slide_id,
        "title": result.title,
        "pageCount": result.page_count,
        "slides": _normalize_slide_assets(result.slides or []),
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
    return {
        "ok": True,
        "slide": meta,
        "slides": _normalize_slide_assets(slides),
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
    object_store = create_object_store()
    object_key = str(meta.get("pptxObjectKey") or f"slides/{slide_id}/{slide_id}.pptx")
    try:
        content = await object_store.get_bytes(object_key)
    except Exception:
        pptx_path = (config.storage_dir / "slides" / slide_id / f"{slide_id}.pptx").resolve()
        if not pptx_path.is_file():
            return JSONResponse(
                content={"ok": False, "error": "file not found"},
                status_code=404,
            )
        file_url = await object_store.put_file(object_key, pptx_path)

        def remember_pptx(current):
            next_meta = dict(current if isinstance(current, dict) else meta)
            next_meta["pptxObjectKey"] = object_key
            next_meta["downloadUrl"] = file_url
            return next_meta

        await json_storage.update(f"slide:{slide_id}", remember_pptx, default=meta)
        content = await object_store.get_bytes(object_key)

    if not content:
        return JSONResponse(
            content={"ok": False, "error": "file not found"},
            status_code=404,
        )
    filename = f"{meta.get('title', slide_id)[:50]}.pptx"
    return _download_response(content, filename)


@router.get("/slides")
async def list_slides(user: AuthUser = Depends(require_auth)):
    """列出历史幻灯片（教师端）。"""
    slides = []
    for item in await json_storage.list_prefix("slide:"):
        if not isinstance(item.value, dict):
            continue
        meta = dict(item.value)
        if not record_belongs_to_user(meta, user.id, user.username):
            continue
        meta["id"] = meta.get("id") or str(item.key).split(":")[-1]
        slides.append(meta)
    slides.sort(key=lambda slide: slide.get("at") or slide.get("updated_at") or "", reverse=True)
    return {"ok": True, "slides": slides}
