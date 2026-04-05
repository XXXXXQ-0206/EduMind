"""
教学视频生成 Provider

支持两条官方链路：
1. 知识点视频生成智能体（推荐，带自然语音）
   Endpoint: https://ai-gateway.vei.volces.com/v1/contents/generations/tasks
2. 即梦 Visual 文生视频 3.0 1080P（AK/SK 签名，静音视频 + 本地配音）
   Endpoint: https://visual.volcengineapi.com/?Action=CVSync2AsyncSubmitTask&Version=2022-08-31
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import httpx

from config import config
from utils.jimeng_client import _sign_volc_request

logger = logging.getLogger(__name__)


JIMENG_VIDEO_REQ_KEY = "jimeng_t2v_v30_1080p"
VOLC_ACTION_SUBMIT = "CVSync2AsyncSubmitTask"
VOLC_ACTION_GET_RESULT = "CVSync2AsyncGetResult"
VOLC_VERSION = "2022-08-31"
VOLC_HOST = "visual.volcengineapi.com"

GATEWAY_MODEL = "AG-video-generate-agent"
GATEWAY_STATUSES_PENDING = {"pending", "processing", "in_queue", "queued"}
GATEWAY_STATUSES_DONE = {"completed", "done", "success"}
GATEWAY_STATUSES_FAILED = {"failed", "error", "cancelled", "canceled"}

VISUAL_PENDING = {"in_queue", "generating", "processing", "pending"}
VISUAL_DONE = {"done", "success", "completed"}
VISUAL_FAILED = {"failed", "error", "not_found", "expired"}


@dataclass
class VideoGenerationProfile:
    student_type: str = "mixed_age"
    teaching_style: str = "vivid_fun"
    voice_type: str = "zh_female_linjianvhai_moon_bigtts"


@dataclass
class VideoTask:
    provider: str
    task_id: str
    request_id: Optional[str] = None


class VideoGenerationError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        retryable: bool = False,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.retryable = retryable
        self.response_body = response_body

    def to_user_message(self) -> str:
        parts = [str(self)]
        if self.code:
            parts.append(f"code={self.code}")
        if self.status_code:
            parts.append(f"http={self.status_code}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " | ".join(parts)


def _clean_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _gateway_api_key() -> str:
    return _clean_text(config.jimeng_video_gateway_api_key) or _clean_text(config.jimeng_video_ark_api_key)


def _gateway_configured() -> bool:
    return bool(_gateway_api_key())


def _visual_configured() -> bool:
    return bool(_clean_text(config.jimeng_access_key_id) and _clean_text(config.jimeng_secret_access_key))


def get_configured_provider() -> Optional[str]:
    forced = _clean_text(config.jimeng_video_provider).lower()
    if forced and forced != "auto":
        if forced == "gateway" and _gateway_configured():
            return "gateway"
        if forced == "visual" and _visual_configured():
            return "visual"
        return None
    if _gateway_configured():
        return "gateway"
    if _visual_configured():
        return "visual"
    return None


def is_configured() -> bool:
    return get_configured_provider() is not None


def is_gateway_configured() -> bool:
    return _gateway_configured()


def is_visual_configured() -> bool:
    return _visual_configured()


def _submit_url() -> str:
    return f"https://{VOLC_HOST}/?Action={VOLC_ACTION_SUBMIT}&Version={VOLC_VERSION}"


def _get_result_url() -> str:
    return f"https://{VOLC_HOST}/?Action={VOLC_ACTION_GET_RESULT}&Version={VOLC_VERSION}"


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _extract_request_id(payload: dict[str, Any], response: Optional[httpx.Response] = None) -> Optional[str]:
    request_id = payload.get("request_id")
    if isinstance(request_id, str) and request_id.strip():
        return request_id.strip()
    meta = payload.get("ResponseMetadata")
    if isinstance(meta, dict):
        rid = meta.get("RequestId")
        if isinstance(rid, str) and rid.strip():
            return rid.strip()
    if response is not None:
        for key in ("x-request-id", "request-id", "x-tt-logid"):
            header = response.headers.get(key)
            if header:
                return header.strip()
    return None


def _extract_error(payload: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    code = payload.get("code")
    message = payload.get("message")
    if isinstance(code, int):
        code = str(code)
    if isinstance(code, str) and isinstance(message, str):
        return code.strip() or None, message.strip() or None
    meta = payload.get("ResponseMetadata")
    if isinstance(meta, dict):
        err = meta.get("Error")
        if isinstance(err, dict):
            err_code = err.get("Code")
            err_message = err.get("Message")
            return (
                str(err_code).strip() if err_code is not None else None,
                str(err_message).strip() if err_message is not None else None,
            )
    return None, None


def _visual_status(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in VISUAL_DONE:
        return "done"
    if value in VISUAL_FAILED:
        return "failed"
    if value in VISUAL_PENDING:
        return value or "in_queue"
    return value or "in_queue"


def _gateway_status(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in GATEWAY_STATUSES_DONE:
        return "done"
    if value in GATEWAY_STATUSES_FAILED:
        return "failed"
    if value in GATEWAY_STATUSES_PENDING:
        return value or "processing"
    return value or "processing"


def _extract_visual_video_url(result: dict[str, Any]) -> Optional[str]:
    for key in ("video_url", "url"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    video_urls = result.get("video_urls")
    if isinstance(video_urls, list):
        for value in video_urls:
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                url = value.get("url") or value.get("video_url")
                if isinstance(url, str) and url.strip():
                    return url.strip()
    video_info = result.get("video_info")
    if isinstance(video_info, dict):
        for key in ("url", "video_url"):
            value = video_info.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _extract_gateway_task_id(payload: dict[str, Any]) -> Optional[str]:
    for key in ("id", "task_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("id", "task_id"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _extract_gateway_item(payload: dict[str, Any], task_id: str) -> Optional[dict[str, Any]]:
    items = payload.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and str(item.get("id") or "").strip() == task_id:
                return item
        for item in items:
            if isinstance(item, dict):
                return item
    data = payload.get("data")
    if isinstance(data, dict):
        item = data.get("item") or data.get("task")
        if isinstance(item, dict):
            return item
    return None


def _build_gateway_prompt(prompt: str, profile: VideoGenerationProfile) -> str:
    cleaned = " ".join(_clean_text(prompt).split())
    return (
        f"{cleaned} "
        "要求：画面必须是动态教学视频，不要整页字幕、不要 PPT 排版、不要海报封面、不要静止文字卡、不要重复镜头，"
        "要有知识点可视化、镜头运动、场景切换和自然讲解节奏。"
        f" --student_type {profile.student_type}"
        f" --teaching_style {profile.teaching_style}"
        f" --voice_type {profile.voice_type}"
    ).strip()


def _build_visual_prompt(prompt: str) -> str:
    cleaned = " ".join(_clean_text(prompt).split())
    guardrails = (
        " 高质量 K12 教学微课短视频，画面连续动态，知识点以动画、实验演示、结构变化、场景切换来展示。"
        " 禁止整屏字幕、禁止大段文字、禁止 PPT、禁止海报构图、禁止 logo 水印、禁止重复镜头、禁止静止不动的封面画面。"
        " 需要自然镜头运动、节奏流畅、信息可视化清晰。"
    )
    return (cleaned + guardrails)[:900].strip()


async def _visual_submit_task(prompt: str, duration_sec: int, aspect_ratio: str) -> VideoTask:
    ak = _clean_text(config.jimeng_access_key_id)
    sk = _clean_text(config.jimeng_secret_access_key)
    frames = 241 if duration_sec >= 10 else 121
    body = {
        "req_key": JIMENG_VIDEO_REQ_KEY,
        "prompt": _build_visual_prompt(prompt),
        "seed": -1,
        "frames": frames,
        "aspect_ratio": aspect_ratio or "16:9",
    }
    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
    query = f"Action={VOLC_ACTION_SUBMIT}&Version={VOLC_VERSION}"
    headers = _sign_volc_request("POST", "/", query, body_bytes, ak, sk, host=VOLC_HOST)
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(_submit_url(), content=body_bytes, headers=headers)
    payload = _safe_json(response)
    request_id = _extract_request_id(payload, response)
    if response.status_code != 200:
        code, message = _extract_error(payload)
        raise VideoGenerationError(
            message or "即梦 Visual 视频提交失败",
            provider="visual",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            retryable=response.status_code >= 500,
            response_body=response.text[:1000],
        )
    code, message = _extract_error(payload)
    if code and code != "10000":
        raise VideoGenerationError(
            message or "即梦 Visual 视频提交失败",
            provider="visual",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            response_body=response.text[:1000],
        )
    result = payload.get("data")
    if not isinstance(result, dict):
        raise VideoGenerationError(
            "即梦 Visual 返回数据缺少 task_id",
            provider="visual",
            status_code=response.status_code,
            request_id=request_id,
            response_body=response.text[:1000],
        )
    task_id = _clean_text(result.get("task_id"))
    if not task_id:
        raise VideoGenerationError(
            "即梦 Visual 返回数据缺少 task_id",
            provider="visual",
            status_code=response.status_code,
            request_id=request_id,
            response_body=response.text[:1000],
        )
    logger.info("teaching_video visual submit ok task_id=%s request_id=%s", task_id, request_id)
    return VideoTask(provider="visual", task_id=task_id, request_id=request_id)


async def _gateway_submit_task(prompt: str, profile: VideoGenerationProfile) -> VideoTask:
    api_key = _gateway_api_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": GATEWAY_MODEL,
        "content": [
            {
                "type": "text",
                "text": _build_gateway_prompt(prompt, profile),
            }
        ],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            config.jimeng_video_gateway_base_url,
            headers=headers,
            json=body,
        )
    payload = _safe_json(response)
    request_id = _extract_request_id(payload, response)
    if response.status_code != 200:
        code, message = _extract_error(payload)
        raise VideoGenerationError(
            message or "知识点视频生成智能体提交失败",
            provider="gateway",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            retryable=response.status_code >= 500,
            response_body=response.text[:1000],
        )
    task_id = _extract_gateway_task_id(payload)
    if not task_id:
        raise VideoGenerationError(
            "知识点视频生成智能体返回数据缺少 task_id",
            provider="gateway",
            status_code=response.status_code,
            request_id=request_id,
            response_body=response.text[:1000],
        )
    logger.info("teaching_video gateway submit ok task_id=%s request_id=%s", task_id, request_id)
    return VideoTask(provider="gateway", task_id=task_id, request_id=request_id)


async def submit_text_to_video(
    prompt: str,
    *,
    duration_sec: int = 5,
    aspect_ratio: str = "16:9",
    profile: Optional[VideoGenerationProfile] = None,
    provider: Optional[str] = None,
) -> VideoTask:
    selected = (provider or "").strip().lower() or get_configured_provider()
    if not selected:
        raise VideoGenerationError("未配置教学视频生成凭证", provider="none")
    if selected == "gateway":
        if not _gateway_configured():
            raise VideoGenerationError("未配置教学视频 Gateway 凭证", provider="gateway")
        return await _gateway_submit_task(prompt, profile or VideoGenerationProfile())
    if selected == "visual":
        if not _visual_configured():
            raise VideoGenerationError("未配置即梦 Visual 凭证", provider="visual")
        return await _visual_submit_task(prompt, duration_sec, aspect_ratio)
    raise VideoGenerationError(f"未知视频 provider: {selected}", provider=selected)


async def _visual_get_task_result(task_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    ak = _clean_text(config.jimeng_access_key_id)
    sk = _clean_text(config.jimeng_secret_access_key)
    body = {
        "req_key": JIMENG_VIDEO_REQ_KEY,
        "task_id": task_id,
    }
    body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
    query = f"Action={VOLC_ACTION_GET_RESULT}&Version={VOLC_VERSION}"
    headers = _sign_volc_request("POST", "/", query, body_bytes, ak, sk, host=VOLC_HOST)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(_get_result_url(), content=body_bytes, headers=headers)
    payload = _safe_json(response)
    request_id = _extract_request_id(payload, response)
    if response.status_code != 200:
        code, message = _extract_error(payload)
        raise VideoGenerationError(
            message or "即梦 Visual 视频查询失败",
            provider="visual",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            retryable=response.status_code >= 500,
            response_body=response.text[:1000],
        )
    code, message = _extract_error(payload)
    if code and code != "10000":
        raise VideoGenerationError(
            message or "即梦 Visual 视频查询失败",
            provider="visual",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            response_body=response.text[:1000],
        )
    result = payload.get("data")
    if not isinstance(result, dict):
        return "in_queue", None, request_id
    status = _visual_status(result.get("status"))
    video_url = _extract_visual_video_url(result) if status == "done" else None
    return status, video_url, request_id


async def _gateway_get_task_result(task_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_gateway_api_key()}",
    }
    params = {
        "page_index": 1,
        "page_size": 1,
        "filter.task_ids": task_id,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            config.jimeng_video_gateway_base_url,
            headers=headers,
            params=params,
        )
    payload = _safe_json(response)
    request_id = _extract_request_id(payload, response)
    if response.status_code != 200:
        code, message = _extract_error(payload)
        raise VideoGenerationError(
            message or "知识点视频生成智能体查询失败",
            provider="gateway",
            status_code=response.status_code,
            code=code,
            request_id=request_id,
            retryable=response.status_code >= 500,
            response_body=response.text[:1000],
        )
    item = _extract_gateway_item(payload, task_id)
    if not item:
        return "processing", None, request_id
    status = _gateway_status(item.get("status"))
    content = item.get("content")
    video_url = None
    if isinstance(content, dict):
        value = content.get("video_url")
        if isinstance(value, str) and value.strip():
            video_url = value.strip()
    return status, video_url, request_id


async def get_task_result(task: VideoTask | str, provider: Optional[str] = None) -> Tuple[str, Optional[str], Optional[str]]:
    if isinstance(task, VideoTask):
        provider = task.provider
        task_id = task.task_id
    else:
        task_id = task
    if not task_id:
        return "failed", None, None
    selected = provider or get_configured_provider()
    if selected == "gateway":
        return await _gateway_get_task_result(task_id)
    if selected == "visual":
        return await _visual_get_task_result(task_id)
    raise VideoGenerationError("未配置教学视频生成凭证", provider=selected or "none")


async def wait_for_video(
    task: VideoTask | str,
    *,
    provider: Optional[str] = None,
    poll_interval: float = 6.0,
    max_wait_sec: float = 600.0,
) -> Tuple[str, Optional[str], Optional[str]]:
    if isinstance(task, VideoTask):
        task_id = task.task_id
        provider = provider or task.provider
    else:
        task_id = task
    if not task_id:
        return "failed", None, None
    elapsed = 0.0
    while elapsed < max_wait_sec:
        status, video_url, request_id = await get_task_result(task_id, provider=provider)
        if status in ("done", "failed", "not_found", "expired"):
            return status, video_url, request_id
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return "failed", None, None
