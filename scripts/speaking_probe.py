import asyncio
from pathlib import Path

from agents.speaking_agent import SpeakingAgent, SpeakingInput
from config import config
from utils.tts import text_to_speech


async def main() -> None:
    agent = SpeakingAgent()
    result = await agent.execute(
        SpeakingInput(count=5, difficulty="easy", item_type="word", topic="daily")
    )
    print("agent_success:", result.success)
    if not result.success or not result.items:
        print("agent_error:", result.error)
        return

    session = "probe-speaking"
    output_dir = config.storage_dir / "speaking" / session
    output_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for item in result.items:
        out = output_dir / f"item_{item.id}.mp3"
        path = await text_to_speech(
            [{"text": item.text, "voice": config.tts_voice_edge_en_us or "en-US-AvaNeural"}],
            str(out),
        )
        p = Path(path)
        if p.exists() and p.stat().st_size > 0:
            ok += 1

    print("items:", len(result.items))
    print("audio_ok:", ok)


if __name__ == "__main__":
    asyncio.run(main())
