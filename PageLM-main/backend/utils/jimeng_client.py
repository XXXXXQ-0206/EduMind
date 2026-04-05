"""
即梦 AI（火山引擎）图像生成客户端
支持：1) 火山引擎 Visual SDK（推荐）；2) 直连 OpenAPI 签名请求。
Action=CVSync2AsyncSubmitTask / CVAsyncSubmitTaskGetResult, Version=2022-08-31
"""
import asyncio
import base64
import hashlib
import hmac
import json as _json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx

from config import config

logger = logging.getLogger(__name__)

# Seedream 通用3.0 文生图：文档 https://www.volcengine.com/docs/86081
VOLC_ACTION_SUBMIT = "CVSync2AsyncSubmitTask"
VOLC_ACTION_GET_RESULT = "CVSync2AsyncGetResult"  # 查询任务接口名
VOLC_VERSION = "2022-08-31"
# 固定值，文档要求
JIMENG_REQ_KEY = "high_aes_general_v30l_zt2i"
VOLC_HOST = "visual.volcengineapi.com"


def _norm_query(query_str: str) -> str:
    """Query 按参数名排序并编码，与火山引擎规范一致。"""
    if not query_str:
        return ""
    params = {}
    for part in query_str.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    parts = [quote(k, safe="-_.~") + "=" + quote(params[k], safe="-_.~") for k in sorted(params)]
    return "&".join(parts).replace("+", "%20")


def _sign_volc_request(
    method: str,
    path: str,
    query: str,
    body: bytes,
    ak: str,
    sk: str,
    host: str = VOLC_HOST,
    service: str = "cv",
    region: str = "cn-north-1",
) -> dict:
    """火山引擎 OpenAPI 签名（对齐官方 sign.py：含 Host、X-Content-Sha256，Query 排序）。"""
    now = datetime.now(timezone.utc)
    date_stamp = now.strftime("%Y%m%d")
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    payload_hash = hashlib.sha256(body).hexdigest()
    canonical_query = _norm_query(query)
    content_type = "application/json"
    signed_headers_list = ["content-type", "host", "x-content-sha256", "x-date"]
    canonical_headers_str = (
        "content-type:" + content_type + "\n"
        "host:" + host + "\n"
        "x-content-sha256:" + payload_hash + "\n"
        "x-date:" + amz_date + "\n"
    )
    signed_headers = ";".join(signed_headers_list)
    canonical_request = "\n".join([
        method.upper(),
        path,
        canonical_query,
        canonical_headers_str,
        signed_headers,
        payload_hash,
    ])
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    cred_scope = f"{date_stamp}/{region}/{service}/request"
    string_to_sign = "\n".join(["HMAC-SHA256", amz_date, cred_scope, hashed_canonical])
    sk_bytes = sk.encode("utf-8")
    k_date = hmac.new(sk_bytes, date_stamp.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = f"HMAC-SHA256 Credential={ak}/{cred_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return {
        "Content-Type": content_type,
        "Host": host,
        "X-Content-Sha256": payload_hash,
        "X-Date": amz_date,
        "Authorization": auth,
    }


def _save_image_from_response(result: dict, prompt: str, save_dir: Optional[Path]) -> Optional[Path]:
    """从 API 返回的 data 中解析 image_urls / binary_data_base64 并保存到 save_dir。"""
    if not save_dir:
        return None
    save_dir.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha1(prompt.encode()).hexdigest()[:12] + ".png"
    # 文档：image_urls (array of string) 或 binary_data_base64 (array of string)
    urls = result.get("image_urls")
    if isinstance(urls, list) and urls and isinstance(urls[0], str):
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(urls[0])
            if r.status_code == 200:
                path = save_dir / name
                path.write_bytes(r.content)
                return path
        except Exception:
            pass
    b64_arr = result.get("binary_data_base64")
    if isinstance(b64_arr, list) and b64_arr and isinstance(b64_arr[0], str):
        try:
            raw = base64.b64decode(b64_arr[0])
            path = save_dir / name
            path.write_bytes(raw)
            return path
        except Exception:
            pass
    # 兼容旧结构
    image_url = result.get("image_url")
    image_base64 = result.get("image_base64") or result.get("b64_image")
    if isinstance(image_base64, str):
        try:
            raw = base64.b64decode(image_base64)
            path = save_dir / name
            path.write_bytes(raw)
            return path
        except Exception:
            pass
    if image_url:
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(image_url)
            if r.status_code == 200:
                path = save_dir / name
                path.write_bytes(r.content)
                return path
        except Exception:
            pass
    return None


def _try_volc_sdk(prompt: str, save_dir: Optional[Path]) -> Optional[Path]:
    """使用 volcengine-python-sdk 的 VisualService 调用即梦（若 SDK 可用）。"""
    try:
        from volcengine.visual.VisualService import VisualService
    except ImportError:
        return None
    ak = config.jimeng_access_key_id
    sk = config.jimeng_secret_access_key
    if not ak or not sk:
        return None
    try:
        svc = VisualService()
        svc.set_ak(ak)
        svc.set_sk(sk)
        form = {"req_key": JIMENG_REQ_KEY, "prompt": prompt[:500], "width": 1024, "height": 1024}
        resp = svc.cv_sync2async_submit_task(form)
        if not isinstance(resp, dict):
            return None
        task_id = (resp.get("data") or {}).get("task_id") or resp.get("task_id")
        if not task_id:
            return None
        import time
        for _ in range(30):
            time.sleep(2)
            get_resp = svc.cv_async_submit_task_get_result({"req_key": JIMENG_REQ_KEY, "task_id": task_id})
            if not isinstance(get_resp, dict):
                continue
            data = (get_resp.get("data") or get_resp) or {}
            status = data.get("status") or data.get("task_status")
            if status == 1 or str(status).lower() == "success":
                return _save_image_from_response(data, prompt, save_dir)
            if status == 2 or str(status).lower() in ("failed", "error"):
                break
        return None
    except Exception as e:
        logger.warning("jimeng sdk: %s", e)
        return None


async def _try_openapi_http(prompt: str, save_dir: Optional[Path]) -> Optional[Path]:
    """直连火山引擎 Seedream 通用3.0 文生图：提交任务后轮询 CVSync2AsyncGetResult 取结果。"""
    ak = config.jimeng_access_key_id
    sk = config.jimeng_secret_access_key
    if not ak or not sk:
        return None
    base_url = "https://visual.volcengineapi.com"
    uri = "/"
    # 1) 提交任务。Body 仅含文档要求的 req_key、prompt，可选 width/height
    query_submit = f"Action={VOLC_ACTION_SUBMIT}&Version={VOLC_VERSION}"
    body_json = {
        "req_key": JIMENG_REQ_KEY,
        "prompt": prompt[:500],
        "seed": -1,
        "width": 1024,
        "height": 1024,
    }
    body_bytes = _json.dumps(body_json, ensure_ascii=False).encode("utf-8")
    try:
        signed = _sign_volc_request("POST", uri, query_submit, body_bytes, ak, sk)
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{base_url}{uri}?{query_submit}",
                content=body_bytes,
                headers=signed,
            )
        if r.status_code != 200:
            logger.warning("jimeng openapi submit status %s body %s", r.status_code, r.text[:500])
            return None
        data = r.json()
        # 文档：code=10000 为成功，再取 data.task_id
        if data.get("code") != 10000:
            logger.warning("jimeng openapi submit code %s message %s", data.get("code"), data.get("message"))
            return None
        result = data.get("data")
        if not isinstance(result, dict):
            return None
        task_id = result.get("task_id")
        if not task_id:
            return None
        # 2) 轮询查询结果。Action=CVSync2AsyncGetResult，req_json 可要求 return_url
        query_get = f"Action={VOLC_ACTION_GET_RESULT}&Version={VOLC_VERSION}"
        get_body = {
            "req_key": JIMENG_REQ_KEY,
            "task_id": task_id,
            "req_json": _json.dumps({"return_url": True}, ensure_ascii=False),
        }
        get_body_bytes = _json.dumps(get_body, ensure_ascii=False).encode("utf-8")
        for _ in range(35):
            await asyncio.sleep(2)
            signed_get = _sign_volc_request("POST", uri, query_get, get_body_bytes, ak, sk)
            async with httpx.AsyncClient(timeout=30.0) as client:
                r2 = await client.post(
                    f"{base_url}{uri}?{query_get}",
                    content=get_body_bytes,
                    headers=signed_get,
                )
            if r2.status_code != 200:
                continue
            data2 = r2.json()
            if data2.get("code") != 10000:
                continue
            res2 = data2.get("data")
            if not isinstance(res2, dict):
                continue
            status = (res2.get("status") or "").lower()
            if status == "done":
                return _save_image_from_response(res2, prompt, save_dir)
            if status in ("not_found", "expired"):
                logger.warning("jimeng task %s: %s", status, task_id)
                break
        return None
    except Exception as e:
        logger.warning("jimeng openapi error: %s", e)
    return None


async def generate_image(prompt: str, save_dir: Optional[Path] = None) -> Optional[Path]:
    """
    根据文本提示调用即梦 AI 生成一张图片。
    优先尝试 Visual SDK，再尝试 OpenAPI 签名请求；失败返回 None。
    """
    if not config.jimeng_access_key_id or not config.jimeng_secret_access_key:
        logger.debug("jimeng: no ak/sk configured")
        return None
    # 1) SDK 为同步接口，在线程池中执行避免阻塞
    import asyncio
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _try_volc_sdk, prompt, save_dir)
    if path:
        return path
    # 2) OpenAPI 直连
    return await _try_openapi_http(prompt, save_dir)
