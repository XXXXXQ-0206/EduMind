"""
Audio transcription helpers.

Transcription is feature-specific and should not depend on the main LLM provider
being compatible with speech APIs. This module keeps speech-to-text providers
separate from text-generation providers.
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, Optional

import httpx

from config import config


def _trim_error(text: str, limit: int = 300) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False
    quote = ""

    for idx in range(start, len(cleaned)):
        ch = cleaned[idx]
        if escape:
            escape = False
            continue
        if in_string:
            if ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    payload = json.loads(cleaned[start:idx + 1])
                except json.JSONDecodeError:
                    return None
                return payload if isinstance(payload, dict) else None
    return None


def _normalize_base_url(base_url: Optional[str], default: str) -> str:
    base = (base_url or default).strip().rstrip("/")
    if not base:
        base = default
    if base.endswith("/audio/transcriptions"):
        return base
    if "api.openai.com" in base and not base.endswith("/v1"):
        return base + "/v1"
    return base


def _openai_transcription_settings() -> tuple[str, str, str]:
    api_key = (config.transcription_openai_api_key or config.openai_api_key or "").strip()
    base_url = _normalize_base_url(
        config.transcription_openai_base_url or config.openai_base_url,
        "https://api.openai.com/v1",
    )
    model = (config.transcription_openai_model or "gpt-4o-mini-transcribe").strip()

    if "deepseek.com" in base_url.lower():
        raise ValueError(
            "当前 TRANSCRIPTION_PROVIDER=openai，但转写 base URL 指向 DeepSeek。"
            "DeepSeek 的 OpenAI 兼容接口不支持语音转写。"
            "请单独配置 TRANSCRIPTION_OPENAI_BASE_URL / TRANSCRIPTION_OPENAI_API_KEY，"
            "或改用 AssemblyAI。"
        )
    if not api_key:
        raise ValueError(
            "TRANSCRIPTION_PROVIDER=openai 但未配置转写 API Key。"
            "请设置 TRANSCRIPTION_OPENAI_API_KEY，或至少提供 OPENAI_API_KEY。"
        )
    if not model:
        raise ValueError("TRANSCRIPTION_OPENAI_MODEL not set")
    return api_key, base_url, model


async def _transcribe_with_openai(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str],
) -> Dict[str, Any]:
    api_key, base_url, model = _openai_transcription_settings()
    url = base_url if base_url.endswith("/audio/transcriptions") else f"{base_url}/audio/transcriptions"

    data = {"model": model}
    if config.transcription_language:
        data["language"] = config.transcription_language

    headers = {"Authorization": f"Bearer {api_key}"}
    files = {
        "file": (
            filename or "audio.webm",
            file_bytes,
            content_type or "application/octet-stream",
        )
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(url, headers=headers, data=data, files=files)

    if resp.status_code != 200:
        raise ValueError(
            f"OpenAI transcription failed ({resp.status_code}): {_trim_error(resp.text)}"
        )

    try:
        payload = resp.json()
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI transcription returned invalid JSON: {exc}") from exc

    text = str(payload.get("text") or payload.get("transcription") or "").strip()
    confidence = payload.get("confidence")
    if not text:
        raise ValueError("OpenAI transcription returned empty text")

    return {
        "text": text,
        "provider": "openai",
        "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
    }


async def _transcribe_with_assemblyai(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str],
) -> Dict[str, Any]:
    api_key = (config.assemblyai_api_key or "").strip()
    if not api_key:
        raise ValueError("TRANSCRIPTION_PROVIDER=assemblyai 但未配置 ASSEMBLYAI_API_KEY")

    headers = {"authorization": api_key}
    async with httpx.AsyncClient(timeout=180.0) as client:
        upload_resp = await client.post(
            "https://api.assemblyai.com/v2/upload",
            headers=headers,
            content=file_bytes,
        )
        if upload_resp.status_code != 200:
            raise ValueError(
                f"AssemblyAI upload failed ({upload_resp.status_code}): {_trim_error(upload_resp.text)}"
            )
        upload_payload = upload_resp.json()
        audio_url = str(upload_payload.get("upload_url") or "").strip()
        if not audio_url:
            raise ValueError("AssemblyAI upload succeeded but upload_url is missing")

        create_payload = {
            "audio_url": audio_url,
            "speech_model": "best",
        }
        if config.transcription_language:
            create_payload["language_code"] = config.transcription_language

        create_resp = await client.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={**headers, "content-type": "application/json"},
            json=create_payload,
        )
        if create_resp.status_code != 200:
            raise ValueError(
                f"AssemblyAI transcription creation failed ({create_resp.status_code}): "
                f"{_trim_error(create_resp.text)}"
            )
        create_data = create_resp.json()
        transcript_id = str(create_data.get("id") or "").strip()
        if not transcript_id:
            raise ValueError("AssemblyAI transcription id missing")

        for _ in range(120):
            poll_resp = await client.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=headers,
            )
            if poll_resp.status_code != 200:
                raise ValueError(
                    f"AssemblyAI polling failed ({poll_resp.status_code}): {_trim_error(poll_resp.text)}"
                )
            poll_data = poll_resp.json()
            status = str(poll_data.get("status") or "").lower()
            if status == "completed":
                text = str(poll_data.get("text") or "").strip()
                if not text:
                    raise ValueError("AssemblyAI returned empty text")
                confidence = poll_data.get("confidence")
                return {
                    "text": text,
                    "provider": "assemblyai",
                    "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
                }
            if status == "error":
                raise ValueError(
                    f"AssemblyAI transcription failed: {_trim_error(str(poll_data.get('error') or 'unknown error'))}"
                )
            await asyncio.sleep(2.0)

    raise TimeoutError("AssemblyAI transcription timed out")


async def transcribe_audio_bytes(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str],
) -> Dict[str, Any]:
    provider = (config.transcription_provider or "openai").strip().lower()

    if not file_bytes:
        raise ValueError("音频文件为空")

    if provider == "openai":
        return await _transcribe_with_openai(file_bytes, filename, content_type)
    if provider == "assemblyai":
        return await _transcribe_with_assemblyai(file_bytes, filename, content_type)
    if provider == "google":
        raise ValueError(
            "当前后端尚未启用 Google Speech-to-Text。"
            "请先改用 TRANSCRIPTION_PROVIDER=openai 或 assemblyai。"
        )
    if provider == "elevenlabs":
        raise ValueError(
            "当前后端尚未实现 ElevenLabs transcription。"
            "请先改用 TRANSCRIPTION_PROVIDER=openai 或 assemblyai。"
        )
    raise ValueError(f"Unsupported transcription provider: {provider}")


def _fallback_study_materials(text: str) -> Dict[str, Any]:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    sentences = [
        s.strip(" \n\r\t-")
        for s in re.split(r"[。！？!?;\n]+", text or "")
        if s and s.strip()
    ]
    key_points = sentences[:5]

    keywords = []
    seen = set()
    for match in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}|[\u4e00-\u9fff]{2,8}", normalized):
        token = match.strip()
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= 8:
            break

    return {
        "summary": (normalized[:220] + ("..." if len(normalized) > 220 else "")) if normalized else "",
        "keyPoints": key_points,
        "topics": keywords[:4],
        "categories": [],
        "searchableKeywords": keywords,
        "studyGuide": {
            "mainConcepts": key_points[:4],
            "importantTerms": [{"term": item, "definition": ""} for item in keywords[:4]],
            "questions": [],
            "takeaways": key_points[:3],
        },
        "timestamps": [],
    }


def _normalize_study_materials(payload: Dict[str, Any]) -> Dict[str, Any]:
    study_guide = payload.get("studyGuide") if isinstance(payload.get("studyGuide"), dict) else {}
    important_terms = study_guide.get("importantTerms")
    if not isinstance(important_terms, list):
        important_terms = []

    normalized_terms = []
    for item in important_terms[:8]:
        if not isinstance(item, dict):
            continue
        term = str(item.get("term") or "").strip()
        definition = str(item.get("definition") or "").strip()
        if term:
            normalized_terms.append({"term": term, "definition": definition})

    def _to_str_list(value: Any, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        items = []
        for raw in value[:limit]:
            text = str(raw or "").strip()
            if text:
                items.append(text)
        return items

    timestamps = []
    raw_timestamps = payload.get("timestamps")
    if isinstance(raw_timestamps, list):
        for item in raw_timestamps[:12]:
            if not isinstance(item, dict):
                continue
            try:
                time_value = float(item.get("time") or 0)
            except (TypeError, ValueError):
                time_value = 0.0
            timestamps.append({
                "time": time_value,
                "content": str(item.get("content") or "").strip(),
                "topic": str(item.get("topic") or "").strip(),
            })

    return {
        "summary": str(payload.get("summary") or "").strip(),
        "keyPoints": _to_str_list(payload.get("keyPoints"), 8),
        "topics": _to_str_list(payload.get("topics"), 8),
        "categories": _to_str_list(payload.get("categories"), 8),
        "searchableKeywords": _to_str_list(payload.get("searchableKeywords"), 12),
        "studyGuide": {
            "mainConcepts": _to_str_list(study_guide.get("mainConcepts"), 8),
            "importantTerms": normalized_terms,
            "questions": _to_str_list(study_guide.get("questions"), 8),
            "takeaways": _to_str_list(study_guide.get("takeaways"), 8),
        },
        "timestamps": timestamps,
    }


async def build_study_materials(transcription_text: str) -> Dict[str, Any]:
    text = (transcription_text or "").strip()
    if not text:
        return _fallback_study_materials(text)

    prompt = (
        "请把下面的语音转写内容整理成结构化学习材料。"
        "只返回 JSON 对象，不要 markdown，不要解释。\n\n"
        "字段结构必须是：\n"
        "{\n"
        '  "summary": "200字内摘要",\n'
        '  "keyPoints": ["要点1", "要点2"],\n'
        '  "topics": ["主题"],\n'
        '  "categories": ["分类"],\n'
        '  "searchableKeywords": ["关键词"],\n'
        '  "studyGuide": {\n'
        '    "mainConcepts": ["核心概念"],\n'
        '    "importantTerms": [{"term":"术语","definition":"定义"}],\n'
        '    "questions": ["复习问题"],\n'
        '    "takeaways": ["结论"]\n'
        "  },\n"
        '  "timestamps": []\n'
        "}\n\n"
        "要求：用中文输出；内容具体；如果转写文本里没有明显时间轴，timestamps 返回空数组。\n\n"
        "转写内容如下：\n"
        f"{text[:12000]}"
    )

    try:
        from utils.llm import invoke_llm

        raw = await invoke_llm(
            [{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        payload = _extract_json_object(raw)
        if isinstance(payload, dict):
            normalized = _normalize_study_materials(payload)
            if normalized["summary"] or normalized["keyPoints"]:
                return normalized
    except Exception:
        pass

    return _fallback_study_materials(text)
