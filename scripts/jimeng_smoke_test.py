import asyncio
from pathlib import Path

from config import config
from utils.jimeng_client import generate_image
from utils.jiemeng_video import submit_text_to_video, wait_for_video


async def main() -> None:
    print("[smoke] start")
    print("[smoke] provider:", config.jimeng_video_provider)
    print("[smoke] has_ak:", bool(config.jimeng_access_key_id))
    print("[smoke] has_sk:", bool(config.jimeng_secret_access_key))

    image_path = await generate_image(
        "教学插图：细胞分裂过程，科普风格，无文字",
        save_dir=Path(config.storage_dir) / "debug_jimeng",
    )
    print("[smoke] image_path:", image_path)

    task = await submit_text_to_video(
        "中学化学微课，动态演示酸碱中和实验过程，镜头推进，禁止字幕墙",
        duration_sec=5,
        aspect_ratio="16:9",
    )
    print("[smoke] video_task:", task)

    status, url, request_id = await wait_for_video(task, poll_interval=6.0, max_wait_sec=150.0)
    print("[smoke] video_status:", status)
    print("[smoke] video_url:", url)
    print("[smoke] request_id:", request_id)


if __name__ == "__main__":
    asyncio.run(main())
