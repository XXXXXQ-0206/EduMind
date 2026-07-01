import asyncio
import time

from agents.slides_agent import SlidesAgent, SlidesInput


async def main() -> None:
    agent = SlidesAgent()
    start = time.time()
    out = await agent.execute(
        SlidesInput(topic="细胞分裂", page_count=10, materials_text=None, slide_id="smoke-slide")
    )
    elapsed = time.time() - start
    print("success=", out.success)
    print("elapsed_sec=", round(elapsed, 2))
    print("page_count=", out.page_count)
    slides = out.slides or []
    with_image = sum(1 for s in slides if s.get("imageUrl"))
    print("slides=", len(slides))
    print("with_image=", with_image)
    print("error=", out.error)


if __name__ == "__main__":
    asyncio.run(main())
