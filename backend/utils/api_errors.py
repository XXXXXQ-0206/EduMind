"""Shared helpers for returning safe API errors while preserving server logs."""
from __future__ import annotations

import logging
from typing import Any, Mapping

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def safe_error_response(
    logger: logging.Logger,
    exc: BaseException,
    message: str,
    *,
    status_code: int = 500,
    extra: Mapping[str, Any] | None = None,
) -> JSONResponse:
    logger.exception(message)
    payload: dict[str, Any] = {"ok": False, "error": message}
    if extra:
        payload.update(extra)
    return JSONResponse(content=payload, status_code=status_code)


def safe_error_payload(
    logger: logging.Logger,
    exc: BaseException,
    message: str,
) -> dict[str, Any]:
    logger.exception(message)
    return {"ok": False, "error": message}


def raise_safe_http_error(
    logger: logging.Logger,
    exc: BaseException,
    message: str,
    *,
    status_code: int = 500,
) -> None:
    logger.exception(message)
    raise HTTPException(status_code=status_code, detail=message) from exc
