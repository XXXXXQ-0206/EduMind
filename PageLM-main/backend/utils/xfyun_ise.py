"""
Xunfei ISE (speech evaluation) WebSocket client.
"""
import asyncio
import base64
import hashlib
import hmac
import json
import math
import ssl
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlencode, urlparse
import xml.etree.ElementTree as ET

import websockets

from config import config

try:
    import certifi
except Exception:  # pragma: no cover - fallback when certifi is unavailable
    certifi = None


def _rfc1123_now() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%a, %d %b %Y %H:%M:%S GMT")


def _lenient_score(raw: float) -> float:
    """Convert Xunfei ISE 0-5 score to 0-100 with a lenient boost curve.

    Mapping: raw 0-5 → normalised 0-100 using a power curve (exp < 1)
    that boosts mid/low range scores while keeping the top near 100.

    Examples (raw → result):
      5.0 → 100.0    4.5 → 93.8    4.0 → 87.9
      3.5 → 81.4     3.0 → 73.6    2.0 → 55.6
      1.0 → 35.6     0.0 → 0.0
    """
    if raw is None or raw < 0:
        return 0.0
    pct = min(raw / 5.0, 1.0)  # → 0..1
    boosted = pct ** 0.6        # power < 1 inflates lower scores
    return min(100.0, round(boosted * 100.0, 1))


def build_auth_url(host_url: str) -> str:
    url = urlparse(host_url)
    date = _rfc1123_now()

    api_key = config.xfyun_api_key
    api_secret = config.xfyun_api_secret
    if not api_key or not api_secret:
        raise ValueError("Xunfei API key/secret not set")

    signature_origin = f"host: {url.hostname}\n" + f"date: {date}\n" + f"GET {url.path} HTTP/1.1"
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f"api_key=\"{api_key}\", algorithm=\"hmac-sha256\", "
        f"headers=\"host date request-line\", signature=\"{signature}\""
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    query = urlencode({
        "authorization": authorization,
        "date": date,
        "host": url.hostname,
    })
    return f"{host_url}?{query}"


def parse_ise_xml(xml_text: str) -> dict:
    """Extract key scores and per-word detail from ISE XML response."""
    scores: Dict[str, Optional[float]] = {
        "total_score": None,
        "accuracy_score": None,
        "fluency_score": None,
        "standard_score": None,
        "integrity_score": None,
    }
    words: list = []

    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return {"scores": scores, "words": words}

    # extract top-level scores from the first element that has them
    # ISE returns 0-5 scale; normalise to 0-100 with lenient curve
    for elem in root.iter():
        for key in list(scores.keys()):
            if key in elem.attrib and scores[key] is None:
                try:
                    scores[key] = _lenient_score(float(elem.attrib[key]))
                except Exception:
                    scores[key] = None

    # extract per-word detail (content, total_score, dp_message)
    for word_elem in root.iter("word"):
        content = word_elem.attrib.get("content", "").strip()
        if not content:
            continue
        dp = int(word_elem.attrib.get("dp_message", "0"))
        w_score = None
        if "total_score" in word_elem.attrib:
            try:
                w_score = _lenient_score(float(word_elem.attrib["total_score"]))
            except Exception:
                pass
        # collect syllable-level errors too
        sylls = []
        for syll_elem in word_elem.iter("syll"):
            s_content = syll_elem.attrib.get("content", "").strip()
            if not s_content or s_content in ("sil", "silv", "fil"):
                continue
            s_serr = int(syll_elem.attrib.get("serr_msg", "0"))
            s_score = None
            if "syll_score" in syll_elem.attrib:
                try:
                    s_score = _lenient_score(float(syll_elem.attrib["syll_score"]))
                except Exception:
                    pass
            sylls.append({
                "content": s_content,
                "serr_msg": s_serr,
                "syll_score": s_score,
            })
        words.append({
            "content": content,
            "dp_message": dp,
            "total_score": w_score,
            "sylls": sylls,
        })

    return {"scores": scores, "words": words}


async def evaluate_ise(
    pcm_data: bytes,
    text: str,
    category: str,
) -> Dict[str, Optional[float]]:
    """
    Call Xunfei ISE WebSocket API following the official SDK protocol:
      Frame 1 (ssb) : common + business(cmd=ssb) + data(status=0)   — NO audio
      Frame 2 (auw) : business(cmd=auw, aus=1) + data(status=1, audio)
      Frame 3…N-1   : business(cmd=auw, aus=2) + data(status=1, audio)
      Frame N       : business(cmd=auw, aus=4) + data(status=2, audio)
    """
    import logging
    log = logging.getLogger("xfyun_ise")

    host_url = "wss://ise-api.xfyun.cn/v2/open-ise"
    auth_url = build_auth_url(host_url)

    if not config.xfyun_appid:
        raise ValueError("Xunfei APPID not set")

    # ---- validate / normalise PCM ----
    if not pcm_data or len(pcm_data) < 2:
        raise ValueError("empty or invalid audio data")

    # 16-bit samples → must be even number of bytes
    if len(pcm_data) % 2 != 0:
        pcm_data += b"\x00"

    frame_size = 1280  # 40 ms @ 16 kHz 16-bit mono

    # split into frames
    frames: list[bytes] = []
    offset = 0
    while offset < len(pcm_data):
        frames.append(pcm_data[offset: offset + frame_size])
        offset += frame_size

    if not frames:
        raise ValueError("no audio frames to evaluate")

    log.info("ISE evaluate: text=%r  category=%s  pcm_bytes=%d  frames=%d",
             text, category, len(pcm_data), len(frames))

    # ---- format text with required ISE markers ----
    # English requires: [word]\ntext for read_word, [content]\ntext for read_sentence
    if category == "read_word":
        formatted_text = "[word]\n" + text
    elif category in ("read_sentence", "read_chapter"):
        formatted_text = "[content]\n" + text
    else:
        formatted_text = text

    text_bom = "\uFEFF" + formatted_text
    log.info("ISE formatted text: %r", text_bom[:200])

    ssb_business = {
        "sub": "ise",
        "ent": "en_vip",
        "category": category,
        "text": text_bom,
        "tte": "utf-8",
        "ttp_skip": True,
        "cmd": "ssb",
        "aue": "raw",
        "auf": "audio/L16;rate=16000",
    }

    ssl_context = ssl.create_default_context(
        cafile=certifi.where() if certifi else None,
    )

    async with websockets.connect(auth_url, ping_interval=None, ssl=ssl_context) as ws:
        # ---- Frame 1: ssb (parameters only, no audio) ----
        ssb_msg = {
            "common": {"app_id": config.xfyun_appid},
            "business": ssb_business,
            "data": {"status": 0},
        }
        await ws.send(json.dumps(ssb_msg))
        log.info("ISE sent ssb frame")

        # ---- Audio frames (auw) ----
        n = len(frames)
        for i, chunk in enumerate(frames):
            if n == 1:
                aus = 4  # single frame = first + last
                data_status = 2
            elif i == 0:
                aus = 1  # first audio chunk
                data_status = 1
            elif i == n - 1:
                aus = 4  # last audio chunk
                data_status = 2
            else:
                aus = 2  # middle audio chunk
                data_status = 1

            auw_msg = {
                "business": {"cmd": "auw", "aus": aus},
                "data": {
                    "status": data_status,
                    "data": base64.b64encode(chunk).decode(),
                },
            }
            await ws.send(json.dumps(auw_msg))

            if i < n - 1:
                await asyncio.sleep(0.04)

        log.info("ISE sent %d auw frames", n)

        # ---- read results ----
        final_xml = None
        while True:
            resp_raw = await ws.recv()
            resp = json.loads(resp_raw)
            code = resp.get("code", 0)
            if code != 0:
                msg_text = resp.get("message") or f"xfyun error {code}"
                log.error("ISE error: code=%d  msg=%s", code, msg_text)
                raise Exception(msg_text)
            data = resp.get("data") or {}
            if data.get("status") == 2:
                data_field = data.get("data")
                if data_field:
                    final_xml = base64.b64decode(data_field).decode("utf-8", errors="ignore")
                break

        log.info("ISE result XML length: %d", len(final_xml or ""))
        return parse_ise_xml(final_xml or "")
