"""Helpers for upload objects shared across backend services."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import unquote, urlparse

from infrastructure.object_store import create_object_store, normalize_object_key


def upload_object_key_from_meta(meta: Mapping[str, Any]) -> str:
    object_key = normalize_object_key(str(meta.get("objectKey") or ""))
    if object_key:
        return object_key

    url = str(meta.get("url") or "").strip()
    if url:
        try:
            path = urlparse(url).path or url
        except Exception:
            path = url
        marker = "/storage/"
        if marker in path:
            return normalize_object_key(unquote(path.split(marker, 1)[1]))

    filename = Path(str(meta.get("filename") or "")).name
    return normalize_object_key(f"uploads/{filename}") if filename else ""


def upload_path_from_meta(meta: Mapping[str, Any]) -> Optional[Path]:
    object_key = upload_object_key_from_meta(meta)
    if not object_key:
        return None
    return create_object_store().path_for(object_key)


async def delete_upload_from_meta(meta: Mapping[str, Any]) -> None:
    object_key = upload_object_key_from_meta(meta)
    if object_key:
        await create_object_store().delete(object_key)
