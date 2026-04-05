"""
Speaking practice API routes.
Generates words/phrases/sentences and synthesizes audio via Edge TTS.
"""
import uuid
import subprocess
import shutil
import logging
import json as json_lib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aiofiles

from agents.speaking_agent import SpeakingAgent, SpeakingInput
from config import config
from utils.auth import require_auth
from utils.auth_db import AuthUser
from utils.tts import text_to_speech
from utils.xfyun_ise import evaluate_ise

log = logging.getLogger("speaking")


router = APIRouter()


class SpeakingGenerateRequest(BaseModel):
    count: Optional[int] = 5
    difficulty: Optional[str] = "easy"
    itemType: Optional[str] = "word"
    topic: Optional[str] = None
    voice: Optional[str] = "american"  # american | british


class SpeakingEvaluateRequest(BaseModel):
    sessionId: str
    filename: str
    text: str
    itemType: Optional[str] = "word"  # word | phrase | sentence


@router.post("/speaking/generate")
async def generate_speaking_items(request: SpeakingGenerateRequest, user: AuthUser = Depends(require_auth)):
    """Generate speaking items and TTS audio files."""
    try:
        count = int(request.count or 5)
        difficulty = (request.difficulty or "easy").lower()
        item_type = (request.itemType or "word").lower()
        topic = (request.topic or "").strip()
        voice = (request.voice or "american").lower()

        agent = SpeakingAgent()
        input_data = SpeakingInput(
            count=count,
            difficulty=difficulty,
            item_type=item_type,
            topic=topic or None,
        )
        result = await agent.execute(input_data)
        if not result.success or not result.items:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": result.error or "generation failed"},
            )

        session_id = str(uuid.uuid4())
        output_dir = config.storage_dir / "speaking" / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        voice_map = {
            "british": config.tts_voice_edge_en_gb or "en-GB-LibbyNeural",
            "american": config.tts_voice_edge_en_us or "en-US-AvaNeural",
        }
        selected_voice = voice_map.get(voice, config.tts_voice_edge_en_us or "en-US-AvaNeural")

        items_payload: List[dict] = []
        for item in result.items:
            requested_path = output_dir / f"item_{item.id}.mp3"

            actual_path = await text_to_speech(
                segments=[{"text": item.text, "voice": selected_voice}],
                output_path=str(requested_path),
            )
            filename = Path(actual_path).name

            audio_url = f"{config.backend_url}/storage/speaking/{session_id}/{filename}"
            items_payload.append(
                {
                    "id": item.id,
                    "text": item.text,
                    "translation": item.translation,
                    "phonetic": item.phonetic,
                    "level": item.level,
                    "tag": item.tag,
                    "audioUrl": audio_url,
                }
            )

        return JSONResponse(
            content={
                "ok": True,
                "sessionId": session_id,
                "items": items_payload,
                "voice": voice,
            }
        )

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(exc)},
        )


@router.post("/speaking/upload")
async def upload_speaking_audio(
    file: UploadFile = File(...),
    sessionId: Optional[str] = Form(None),
    itemId: Optional[int] = Form(None),
    user: AuthUser = Depends(require_auth),
):
    """Upload a speaking recording file."""
    try:
        session = sessionId or str(uuid.uuid4())
        safe_item = str(itemId) if itemId is not None else "x"

        content_type = (file.content_type or "").lower()
        ext = ".webm"
        if "." in (file.filename or ""):
            ext = "." + file.filename.rsplit(".", 1)[-1]
        elif "wav" in content_type:
            ext = ".wav"
        elif "mpeg" in content_type or "mp3" in content_type:
            ext = ".mp3"
        elif "mp4" in content_type or "m4a" in content_type:
            ext = ".m4a"

        output_dir = config.storage_dir / "speaking" / "recordings" / session
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"recording_{safe_item}_{uuid.uuid4().hex}{ext}"
        output_path = output_dir / filename

        async with aiofiles.open(output_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await f.write(chunk)

        static_url = f"{config.backend_url}/storage/speaking/recordings/{session}/{filename}"
        return JSONResponse(
            content={
                "ok": True,
                "sessionId": session,
                "filename": filename,
                "staticUrl": static_url,
            }
        )

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(exc)},
        )


def _find_ffmpeg() -> Optional[str]:
    custom = config.ffmpeg_path
    if custom and custom != "ffmpeg":
        if Path(custom).exists():
            return custom
    common_paths = [
        Path("/opt/homebrew/bin/ffmpeg"),
        Path("/opt/homebrew/opt/ffmpeg/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
    ]
    for candidate in common_paths:
        if candidate.exists():
            return str(candidate)
    cellar_root = Path("/opt/homebrew/Cellar/ffmpeg")
    if cellar_root.exists():
        versions = sorted(cellar_root.iterdir(), reverse=True)
        for version_dir in versions:
            candidate = version_dir / "bin" / "ffmpeg"
            if candidate.exists():
                return str(candidate)
    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and Path(bundled).exists():
            return bundled
    except Exception:
        pass
    return shutil.which("ffmpeg")


def _convert_to_pcm(input_path: Path, output_path: Path) -> None:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise Exception("ffmpeg not found for audio conversion")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "s16le",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace") if result.stderr else "ffmpeg failed"
        raise Exception(err.strip())


@router.post("/speaking/evaluate")
async def evaluate_speaking(request: SpeakingEvaluateRequest, user: AuthUser = Depends(require_auth)):
    """Evaluate a speaking recording with Xunfei ISE."""
    try:
        session = request.sessionId.strip()
        filename = request.filename.strip()
        text = request.text.strip()
        if not session or not filename or not text:
            return JSONResponse(status_code=400, content={"ok": False, "error": "missing params"})

        file_path = config.storage_dir / "speaking" / "recordings" / session / filename
        if not file_path.exists():
            return JSONResponse(status_code=404, content={"ok": False, "error": "audio file not found"})

        tmp_dir = config.storage_dir / "speaking" / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        pcm_path = tmp_dir / f"{uuid.uuid4().hex}.pcm"

        _convert_to_pcm(file_path, pcm_path)
        pcm_data = pcm_path.read_bytes()
        log.info("PCM conversion done: src=%s  pcm_size=%d bytes  duration≈%.2fs",
                 file_path.name, len(pcm_data),
                 len(pcm_data) / (16000 * 2))

        item_type = (request.itemType or "word").lower()
        category = "read_word" if item_type == "word" else "read_sentence"
        log.info("ISE evaluate: text=%r  category=%s", text, category)

        scores = await evaluate_ise(pcm_data=pcm_data, text=text, category=category)

        try:
            pcm_path.unlink()
        except Exception:
            pass

        # scores is now {"scores": {...}, "words": [...]}
        return JSONResponse(content={"ok": True, **scores})

    except Exception as exc:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


# ── History endpoints ──

HISTORY_FILE = config.storage_dir / "speaking" / "history.json"


def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json_lib.loads(HISTORY_FILE.read_text("utf-8"))
        except Exception:
            pass
    return []


def _save_history(records: list):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json_lib.dumps(records, ensure_ascii=False, indent=2), "utf-8")


class SpeakingHistorySaveRequest(BaseModel):
    sessionId: Optional[str] = None
    count: int = 0
    difficulty: str = "easy"
    itemType: str = "word"
    voice: str = "american"
    avgScore: float = 0
    avgAccuracy: float = 0
    avgFluency: float = 0
    avgStandard: float = 0
    items: list = []


@router.get("/speaking/history")
async def list_speaking_history(user: AuthUser = Depends(require_auth)):
    """Return all history records (newest first)."""
    records = _load_history()
    records = [r for r in records if (r.get("owner_id") == user.id) or (r.get("owner_id") is None and user.username == "admin1")]
    return JSONResponse(content={"ok": True, "records": records})


@router.post("/speaking/history")
async def save_speaking_history(request: SpeakingHistorySaveRequest, user: AuthUser = Depends(require_auth)):
    """Save or update a speaking practice session to history."""
    records = _load_history()

    record_id = request.sessionId or str(uuid.uuid4())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_record = {
        "id": record_id,
        "date": now_str,
        "count": request.count,
        "difficulty": request.difficulty,
        "itemType": request.itemType,
        "voice": request.voice,
        "avgScore": round(request.avgScore, 1),
        "avgAccuracy": round(request.avgAccuracy, 1),
        "avgFluency": round(request.avgFluency, 1),
        "avgStandard": round(request.avgStandard, 1),
        "items": request.items[:20],  # cap at 20 items
        "owner_id": user.id,
        "owner_username": user.username,
    }

    # Upsert by id
    existing_idx = next((i for i, r in enumerate(records) if r.get("id") == record_id), None)
    if existing_idx is not None:
        records[existing_idx] = new_record
    else:
        records.insert(0, new_record)

    # Keep max 50 records
    records = records[:50]
    _save_history(records)

    return JSONResponse(content={"ok": True, "id": record_id})


@router.get("/speaking/history/{record_id}")
async def get_speaking_history_detail(record_id: str, user: AuthUser = Depends(require_auth)):
    """Return a single history record by id."""
    records = _load_history()
    record = next((r for r in records if r.get("id") == record_id and ((r.get("owner_id") == user.id) or (r.get("owner_id") is None and user.username == "admin1"))), None)
    if not record:
        return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
    return JSONResponse(content={"ok": True, "record": record})


@router.delete("/speaking/history/{record_id}")
async def delete_speaking_history(record_id: str, user: AuthUser = Depends(require_auth)):
    """Delete a single history record by id."""
    records = _load_history()
    next_records = [
        r for r in records
        if not (
            r.get("id") == record_id
            and ((r.get("owner_id") == user.id) or (r.get("owner_id") is None and user.username == "admin1"))
        )
    ]
    if len(next_records) == len(records):
        return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
    _save_history(next_records)
    return JSONResponse(content={"ok": True})
