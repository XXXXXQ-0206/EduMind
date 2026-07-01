import asyncio
from pathlib import Path

from config import config
from utils.tts import text_to_speech


async def main() -> None:
    out = Path(config.storage_dir) / "debug_tts" / "podcast_probe.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    segments = [
        {"text": "大家好，欢迎来到今天的播客，我们先聊聊细胞分裂。", "voice": config.tts_voice_edge, "speaker": "A"},
        {"text": "好的，我们从有丝分裂和减数分裂的区别开始。", "voice": config.tts_voice_alt_edge, "speaker": "B"},
    ]
    result = await text_to_speech(segments, str(out))
    p = Path(result)
    print("output:", p)
    print("exists:", p.exists())
    print("size:", p.stat().st_size if p.exists() else 0)


if __name__ == "__main__":
    asyncio.run(main())
