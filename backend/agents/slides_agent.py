"""
幻灯片生成 Agent
流水线：逻辑大纲(DeepSeek) -> 配图(即梦，纯图无文字) -> 仅展示大纲+插图，不生成 pptx 避免文字乱码
"""
import asyncio
import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from agents.base import LLMAgent, AgentInput, AgentOutput
from config import config
from infrastructure.object_store import create_object_store

# 配图生成时的系统化要求：尽可能生动、高质量，且不含任何文字
ILLUSTRATION_PROMPT_PREFIX = """高质量教学插图，要求：画面生动、富有感染力、色彩鲜明、构图清晰、细节丰富，适合课堂展示；纯图像内容，不要出现任何文字、字幕、标签或字母。主题："""
ILLUSTRATION_PROMPT_SUFFIX = (
    "；画面风格：动态教学动画质感、卡通与 3D 元素融合、知识点可视化演示。"
)

logger = logging.getLogger(__name__)


IMAGE_CONCURRENCY = 2
IMAGE_TIMEOUT_SEC = 18


class SlidesInput(AgentInput):
    """幻灯片生成输入"""
    topic: str
    page_count: int = 10
    materials_text: Optional[str] = None
    slide_id: Optional[str] = None  # 用于保存路径


class SlideItem:
    """单页幻灯片数据"""
    def __init__(
        self,
        title: str,
        bullets: List[str],
        image_path: Optional[str] = None,
        image_object_key: Optional[str] = None,
    ):
        self.title = title
        self.bullets = bullets or []
        self.image_path = image_path
        self.image_object_key = image_object_key

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "bullets": self.bullets,
            "imageUrl": self.image_path,  # 前端用 URL，后端存相对路径
            "imageObjectKey": self.image_object_key,
        }


class SlidesOutput(AgentOutput):
    """幻灯片生成输出（大纲 + 配图，无 pptx）"""
    slide_id: Optional[str] = None
    title: Optional[str] = None
    page_count: int = 0
    slides: Optional[List[dict]] = None  # 每页 {title, bullets, imageUrl}


class SlidesAgent(LLMAgent):
    """幻灯片生成 Agent：大纲 -> 配图（纯图无文字），仅展示大纲+插图"""

    def __init__(self):
        system_prompt = """你是一位专业的教学课件设计专家。根据用户给出的主题和页数，生成适合课堂使用的 PPT 大纲。
输出要求：
1. 只输出一个合法的 JSON 数组，不要包含 markdown 代码块或其它说明文字。
2. 数组长度必须等于用户要求的页数（第一页为封面/标题页，其余为内容页）。
3. 每一项格式：{"title": "本页标题", "bullets": ["要点1", "要点2", ...]}
4. 封面页的 title 为课程/主题标题，bullets 可为空数组或简短副标题。
5. 内容页的 bullets 每页 3～6 条，表述清晰、适合教学。
6. 若用户提供备课资料，请结合资料内容生成更贴合的要点。
7. 若主题或资料为中文，全部使用中文；否则可用英文。"""
        super().__init__("slides_agent", system_prompt)

    async def execute(
        self, input_data: SlidesInput, emit_callback: Optional[callable] = None
    ) -> SlidesOutput:
        try:
            topic = (input_data.topic or "").strip()
            page_count = max(5, min(25, int(input_data.page_count or 10)))
            materials_text = input_data.materials_text or ""
            slide_id = input_data.slide_id or f"slide-{uuid.uuid4().hex[:12]}"

            # 1. LLM 生成大纲与详细内容
            outline = await self._generate_outline(topic, page_count, materials_text)
            if not outline or len(outline) < 2:
                return SlidesOutput(
                    success=False,
                    error="生成大纲失败或页数不足",
                )

            # 2. 组装每页数据（标题 + 要点）
            slides_data: List[SlideItem] = []
            for i, item in enumerate(outline):
                title = item.get("title") or (f"第{i+1}页" if i > 0 else topic)
                bullets = item.get("bullets")
                if isinstance(bullets, list):
                    bullets = [str(b).strip() for b in bullets if str(b).strip()]
                else:
                    bullets = []
                slides_data.append(SlideItem(title=title, bullets=bullets))

            # 3. 即梦生成配图（纯图、无文字，使用生动高质量提示词）
            save_dir = config.storage_dir / "slides" / slide_id
            save_dir.mkdir(parents=True, exist_ok=True)
            try:
                from utils.jimeng_client import generate_image
                object_store = create_object_store()
                generated_count = 0
                skipped_count = 0
                lock = asyncio.Lock()
                semaphore = asyncio.Semaphore(IMAGE_CONCURRENCY)

                async def generate_for_page(i: int, slide: SlideItem) -> None:
                    nonlocal generated_count, skipped_count
                    prompt = self._build_illustration_prompt(slide.title, slide.bullets)
                    img_path = None
                    # 即梦接口会偶发并发限流，做短重试避免整页缺图。
                    for attempt in range(3):
                        try:
                            async with semaphore:
                                img_path = await asyncio.wait_for(
                                    generate_image(prompt, save_dir=save_dir), timeout=IMAGE_TIMEOUT_SEC
                                )
                        except asyncio.TimeoutError:
                            logger.warning(
                                "即梦配图超时 slide_id=%s page=%s attempt=%s",
                                slide_id,
                                i + 1,
                                attempt + 1,
                            )
                            img_path = None
                        except Exception as page_exc:
                            logger.warning(
                                "即梦配图失败 slide_id=%s page=%s attempt=%s error=%s",
                                slide_id,
                                i + 1,
                                attempt + 1,
                                page_exc,
                            )
                            img_path = None

                        if img_path:
                            break

                        if attempt < 2:
                            await asyncio.sleep(1.2 * (attempt + 1))

                    if img_path:
                        object_key = f"slides/{slide_id}/{img_path.name}"
                        slide.image_path = await object_store.put_file(object_key, img_path)
                        slide.image_object_key = object_key
                        async with lock:
                            generated_count += 1
                        return

                    async with lock:
                        skipped_count += 1

                await asyncio.gather(
                    *(generate_for_page(i, slide) for i, slide in enumerate(slides_data)),
                    return_exceptions=True,
                )

                if skipped_count:
                    logger.warning(
                        "slide %s 即梦配图缺失: total=%s, success=%s, skipped=%s",
                        slide_id,
                        len(slides_data),
                        generated_count,
                        skipped_count,
                    )
            except Exception as e:
                logger.warning("即梦配图失败（大纲仍会展示）: %s", e)

            # 仅返回大纲 + 配图，不生成 pptx，避免文字乱码
            slides_for_api: List[dict] = [s.to_dict() for s in slides_data]

            return SlidesOutput(
                success=True,
                slide_id=slide_id,
                title=topic,
                page_count=len(slides_data),
                slides=slides_for_api,
            )
        except Exception as e:
            return SlidesOutput(success=False, error=str(e))

    def _repair_json_array(self, raw: str) -> str:
        """尝试修复 LLM 常出的 JSON 格式问题，便于解析。"""
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            return raw
        s = match.group(0)
        # 去掉末尾多余逗号：, ] -> ]  ，, } -> }
        s = re.sub(r",\s*\]", "]", s)
        s = re.sub(r",\s*}", "}", s)
        # 数组元素之间缺少逗号："]\s*[" 或 "}\s*{" 中间补逗号（仅限外层，避免误伤字符串内）
        # 简单做法： "}\s*{" 替换为 "}, {"（对象之间漏逗号很常见）
        s = re.sub(r"\}\s*\{", "}, {", s)
        return s

    def _safe_parse_outline(self, raw: str, topic: str, page_count: int) -> List[Dict[str, Any]]:
        """解析大纲 JSON，失败时返回默认大纲，避免 500。"""
        arr: List[Dict[str, Any]] = []
        for text in (raw, self._repair_json_array(raw)):
            try:
                arr = json.loads(text)
                if isinstance(arr, list) and len(arr) >= 2:
                    return arr[:page_count]
            except (json.JSONDecodeError, TypeError):
                continue
        # 提取 [...] 后再试一次修复并解析
        extracted = self._repair_json_array(raw)
        try:
            arr = json.loads(extracted)
            if isinstance(arr, list) and len(arr) >= 2:
                return arr[:page_count]
        except (json.JSONDecodeError, TypeError):
            pass
        # 回退：生成默认大纲，保证能出结果
        arr = [{"title": topic, "bullets": []}]
        for i in range(1, page_count):
            arr.append({
                "title": f"{topic} - 第{i}部分",
                "bullets": [f"要点 {j+1}" for j in range(3)],
            })
        return arr[:page_count]

    async def _generate_outline(
        self, topic: str, page_count: int, materials_text: str
    ) -> List[Dict[str, Any]]:
        """调用 LLM 生成幻灯片大纲（JSON 数组）。"""
        lang = "中文" if self._has_cjk(topic or materials_text[:200]) else "英文"
        user = f"""主题：{topic}
页数：{page_count}（含封面）
语言：{lang}
"""
        if materials_text.strip():
            user += f"\n备课资料（请结合以下内容生成要点）：\n{materials_text[:8000]}\n"
        user += "\n请直接输出 JSON 数组，不要其它内容。确保每项为 {\"title\": \"...\", \"bullets\": [...]}，且无多余逗号、无未转义换行。"

        response = await self.call_llm(user, expect_json=True)
        raw = self._extract_json(response) or "[]"
        return self._safe_parse_outline(raw, topic, page_count)

    def _has_cjk(self, text: str) -> bool:
        if not text:
            return False
        for c in text:
            if "\u4e00" <= c <= "\u9fff":
                return True
        return False

    def _build_illustration_prompt(self, title: str, bullets: List[str]) -> str:
        key_points = "、".join([b for b in (bullets or []) if b][:3])
        if key_points:
            return f"{ILLUSTRATION_PROMPT_PREFIX}{title}；核心知识点：{key_points}{ILLUSTRATION_PROMPT_SUFFIX}"
        return f"{ILLUSTRATION_PROMPT_PREFIX}{title}{ILLUSTRATION_PROMPT_SUFFIX}"
