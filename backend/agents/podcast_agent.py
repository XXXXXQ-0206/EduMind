"""
AI 播客生成 Agent
生成对话式播客脚本并合成音频
"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class PodcastInput(AgentInput):
    """播客生成输入"""
    topic: str
    length: Optional[str] = None
    pid: Optional[str] = None
    materials_text: Optional[str] = None  # 学习资料原文，与 topic 分开传递


class PodcastSegment(BaseModel):
    """播客片段"""
    spk: str  # "A" or "B"
    voice: Optional[str] = None
    md: str  # markdown 格式的对话文本


class PodcastData(BaseModel):
    """播客数据"""
    title: str
    summary: str
    segments: List[PodcastSegment]


class PodcastOutput(AgentOutput):
    """播客生成输出"""
    script: Optional[PodcastData] = None
    audio_path: Optional[str] = None


class PodcastAgent(LLMAgent):
    """
    AI 播客生成 Agent
    生成对话式播客脚本并合成音频
    """

    def __init__(self):
        system_prompt = """
ROLE
You are a world-class podcast scriptwriter who creates deeply researched, intellectually stimulating, and highly specific content.
You write scripts for two hosts who have genuine expertise — they don't just talk *about* a topic, they talk *through* it with precision, depth, and real examples.

OUTPUT
Return valid JSON: either {"title":"...","summary":"...","segments":[...]} OR a direct array [{"spk":"A|B","md":"spoken dialogue"}, ...].
Each segment md: 侃侃而谈，不限制字数，可长可短。

CONTENT DEPTH REQUIREMENTS (CRITICAL)
1. Every single segment MUST teach the listener something concrete. Ask yourself: "Could a listener learn a new fact from this segment?" If not, rewrite it.
2. For each concept discussed, include AT LEAST ONE of these:
   - A named real-world example with specifics (company, person, event, year)
   - A concrete number, percentage, or measurement
   - A step-by-step breakdown of HOW a mechanism/process works internally
   - A historical anecdote with names, dates, and outcome
   - A precise analogy that maps each part of the concept to something familiar
3. Host A explains and presents. Host B does NOT just agree — Host B must add NEW information, challenge assumptions, point out edge cases, or ask "but what about..." questions that lead to deeper exploration.
4. NEVER write a segment that merely says "this is fascinating" or "let's now talk about X". Every segment must contain substantive content.
5. When reference materials are provided, you MUST extract and discuss SPECIFIC content from those materials — do not ignore them.

SEGMENT RULES
- Total segments: 6–18 (depends on length parameter)
- Strictly alternate A and B
- Each segment: 侃侃而谈，充分展开，不限制字数。每段可长可短，言之有物即可。
- If the topic contains Chinese characters, ALL output must be in Chinese.

CONVERSATION FLOW
- Opening: Start with a specific hook — a surprising fact, a "did you know" statistic, or a concrete scenario. NOT "welcome to the show, today we'll discuss..."
- Middle: Each segment advances the topic. Explain → Example → Challenge → Deeper insight. Do not circle back to repeat earlier points.
- Closing: End with a concrete, actionable takeaway or a thought-provoking unanswered question.

SPEAKING STYLE
- Use concrete language: "For example, in 2023 OpenAI..." / "具体来说，比如2019年的..." 
- React naturally: "Wait, that actually contradicts..." / "等等，这其实和我们刚说的矛盾了..."
- Each host should introduce information the other did not know.
- Avoid formulaic transitions — vary how segments connect.

STRICTLY FORBIDDEN
- Generic overview statements without specific backing
- Segments that only contain greetings, pleasantries, or transitions
- Repeating the same point in different words
- Ignoring provided reference materials
- Template phrases like "那我们就一起来看看吧" or "Let's dive in" without immediately following with substance
- Code fences or extra text outside the JSON
""".strip()

        super().__init__("podcast_agent", system_prompt)
        self.description = "Generate engaging podcast scripts with audio synthesis"

    async def execute(
        self, input_data: PodcastInput, emit_callback: Optional[callable] = None
    ) -> PodcastOutput:
        """执行播客生成"""
        try:
            # 1. 生成脚本
            script = await self._generate_script(
                input_data.topic, input_data.length,
                materials_text=input_data.materials_text,
            )

            if emit_callback:
                await self._emit(emit_callback, {"type": "script", "data": script.dict()})

            # 2. 合成音频
            try:
                audio_path = await self._synthesize_audio(script, input_data.pid, emit_callback=emit_callback)
            except Exception as synth_error:
                msg = str(synth_error).strip() or repr(synth_error)
                return PodcastOutput(
                    success=False,
                    error=msg,
                    data={"script": script.dict(), "audio_path": None},
                    script=script,
                    audio_path=None,
                )

            return PodcastOutput(
                success=True,
                data={"script": script.dict(), "audio_path": audio_path},
                script=script,
                audio_path=audio_path,
            )

        except Exception as e:
            msg = str(e).strip() or repr(e)
            return PodcastOutput(
                success=False,
                error=msg,
                script=None,
                audio_path=None,
            )

    async def _generate_script(
        self, topic: str, length: Optional[str],
        materials_text: Optional[str] = None,
    ) -> PodcastData:
        """生成播客脚本"""
        length_value = (length or "medium").lower()
        length_hint = {
            "short": "short",
            "brief": "short",
            "medium": "medium",
            "long": "long",
            "detailed": "long",
        }.get(length_value, "medium")
        segment_hint = {
            "short": "6-8",
            "medium": "10-14",
            "long": "14-18",
        }.get(length_hint, "10-14")
        min_segments = {"short": 6, "medium": 10, "long": 14}.get(length_hint, 10)

        has_materials = bool(materials_text and materials_text.strip())
        # 判断语言：有学习资料时，也根据材料内容判断语言
        if has_materials:
            language_hint = "Chinese" if (self._has_cjk(topic) or self._has_cjk(materials_text[:500])) else "English"
        else:
            language_hint = "Chinese" if self._has_cjk(topic) else "English"

        # 使用播客专用 LLM（默认 DeepSeek）做深度讨论
        from config import config
        podcast_provider = (config.podcast_llm_provider or "deepseek").strip().lower()
        # 若配置了 OPENAI_* 指向 DeepSeek 而 DEEPSEEK_API_KEY 未设置，则用 openai 接入
        if podcast_provider == "deepseek" and not config.deepseek_api_key and config.openai_api_key:
            podcast_provider = "openai"

        # 阶段一：生成深度提纲，避免套话、贴合主题
        deep_outline = await self._generate_deep_outline(
            topic=topic,
            materials_text=materials_text,
            language_hint=language_hint,
            provider=podcast_provider,
        )

        if has_materials:
            user_message = self._build_materials_prompt(
                topic, materials_text, language_hint, length_hint, segment_hint,
                deep_outline=deep_outline,
            )
        else:
            user_message = self._build_topic_prompt(
                topic, language_hint, length_hint, segment_hint,
                deep_outline=deep_outline,
            )

        response = await self.call_llm_with_provider(
            podcast_provider, user_message, expect_json=True, max_tokens=8192
        )
        print(f"[podcast] raw response len={len(response or '')}")
        if response:
            preview = response[:500] + ("..." if len(response) > 500 else "")
            print(f"[podcast] raw preview:\n{preview}")
        data = self._parse_script_response(response)

        if language_hint == "Chinese" and not self._script_has_cjk(data):
            strict_prompt = (
                "Return only JSON. All content must be Chinese. "
                "No English words in title, summary, or segments."
            )
            response_cn = await self.call_llm_with_provider(
                podcast_provider, user_message, system_prompt=strict_prompt,
                expect_json=True, max_tokens=8192,
            )
            print(f"[podcast] retry response (len={len(response_cn or '')})")
            data = self._parse_script_response(response_cn) or data

        if not isinstance(data, dict):
            data = {}

        if not data:
            print("[podcast] WARNING: LLM returned empty/invalid JSON, using fallback template")
            # 回退到基本脚本（中文优先）
            if language_hint == "Chinese":
                data = {
                    "title": topic[:50],
                    "summary": f"围绕{topic}的一场轻松对话。",
                    "segments": [
                        {"spk": "A", "md": f"欢迎来到今天的播客，我们聊聊{topic}。"},
                        {"spk": "B", "md": f"对，{topic}很有意思，我们从一个日常问题开始。"},
                        {"spk": "A", "md": "先说核心概念，它解决的痛点是什么？"},
                        {"spk": "B", "md": "我们可以用一个生活场景做类比，更容易理解。"},
                        {"spk": "A", "md": "再讲一个常见误区，避免踩坑。"},
                        {"spk": "B", "md": "最后给出实用建议，帮助大家应用到学习或工作。"},
                    ],
                }
            else:
                data = {
                    "title": topic[:50],
                    "summary": f"A conversation about {topic}",
                    "segments": [
                        {"spk": "A", "md": f"Welcome to our discussion about {topic}."},
                        {"spk": "B", "md": f"Yes, {topic} is a fascinating subject."},
                    ],
                }

        # 验证和清理数据
        if not isinstance(data.get("segments"), list):
            data["segments"] = []

        segments = []
        for seg in data.get("segments", [])[:30]:
            try:
                segment = PodcastSegment(
                    spk=seg.get("spk", "A"),
                    voice=seg.get("voice"),
                    md=seg.get("md", ""),
                )
                segments.append(segment)
            except Exception:
                pass

        # 确保至少有2个片段
        if len(segments) < 2:
            if language_hint == "Chinese":
                segments = self._fallback_segments_zh(topic)
            else:
                segments = [
                    PodcastSegment(spk="A", md=f"Welcome to our discussion about {topic}."),
                    PodcastSegment(spk="B", md=f"Yes, {topic} is a fascinating subject."),
                ]

        # 有 LLM 生成内容（≥2 段）时直接用，不填充模板套话；仅段数不足时补足
        if len(segments) >= 2:
            print(f"[podcast] using {len(segments)} LLM segments, no template padding")
        else:
            if language_hint == "Chinese" and len(segments) < min_segments:
                print(f"[podcast] padding segments: {len(segments)} -> {min_segments}")
                segments = self._pad_segments_zh(segments, topic, target=min_segments)
            elif language_hint != "Chinese" and len(segments) < min_segments:
                print(f"[podcast] padding segments: {len(segments)} -> {min_segments}")
                segments = self._pad_segments_en(segments, topic, target=min_segments)

        title = data.get("title", topic)[:50]
        summary = data.get("summary", "")[:500]

        # 打印生成的播客脚本文本，便于排查套话问题
        print("[podcast] ========== generated script ==========")
        print(f"[podcast] title: {title}")
        print(f"[podcast] summary: {summary}")
        for i, seg in enumerate(segments):
            text = self._strip_markdown(seg.md or "")[:200]
            suffix = "..." if len(seg.md or "") > 200 else ""
            print(f"[podcast]   [{seg.spk}] {text}{suffix}")
        print("[podcast] ======================================")

        return PodcastData(title=title, summary=summary, segments=segments)

    async def _synthesize_audio(
        self,
        script: PodcastData,
        pid: Optional[str],
        emit_callback: Optional[callable] = None,
    ) -> str:
        """合成音频"""
        from utils.tts import text_to_speech
        from config import config

        # 创建输出目录
        output_dir = config.storage_dir / "podcasts"
        if pid:
            output_dir = output_dir / pid
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成安全的文件名
        safe_title = re.sub(r"[^a-z0-9]", "_", script.title.lower())[:50]
        if not safe_title.strip("_"):
            safe_title = "podcast"
        timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = output_dir / f"{safe_title}_{timestamp}.mp3"

        # 准备音频段
        audio_segments = []
        for i, seg in enumerate(script.segments):
            text = self._strip_markdown(seg.md or "")
            voice = seg.voice or self._choose_voice(text, i, seg.spk)
            audio_segments.append({"text": text, "voice": voice, "speaker": seg.spk})

            if emit_callback:
                await self._emit(emit_callback, {"type": "audio_progress", "i": i, "len": len(script.segments)})

        # 调用 TTS
        actual_audio_path = await text_to_speech(
            audio_segments,
            str(audio_path),
            emit_callback=emit_callback,
        )
        audio_path = Path(actual_audio_path)

        try:
            if not audio_path.exists() or audio_path.stat().st_size == 0:
                raise Exception("Audio file not created")
        except Exception as e:
            raise Exception(f"Audio synthesis failed: {e}")

        return str(audio_path)

    # ────────────────────────────────────────────────────────────
    #  深度提纲（Agent 第一阶段）
    # ────────────────────────────────────────────────────────────

    async def _generate_deep_outline(
        self,
        topic: str,
        materials_text: Optional[str],
        language_hint: str,
        provider: str,
    ) -> str:
        """
        使用指定 LLM 生成「深度讨论提纲」，供后续脚本严格遵循，避免套话、贴合主题。
        输出为纯文本：关键论点、具体案例、常见误区、可深挖角度等。
        """
        has_materials = bool(materials_text and materials_text.strip())
        lang_instruction = (
            "请用中文输出提纲。"
            if language_hint == "Chinese" else "Output the outline in English."
        )

        if has_materials:
            intro = (
                "下面是一份学习资料摘要，请先阅读并提炼出适合做播客深度讨论的要点。\n\n"
                "=== 资料摘要（前 8000 字）===\n"
                f"{materials_text[:8000]}\n\n"
                f"用户主题提示: {topic}\n\n"
            )
        else:
            intro = (
                f"请针对话题「{topic}」做一次深度思考，输出一份播客讨论提纲（纯文本，不要 JSON）。\n\n"
            )

        system = (
            "You are a research analyst. Your job is to produce a concise but substantive "
            "outline for a two-host podcast that will discuss the given topic in depth.\n\n"
            "Output MUST include (in plain text, no JSON):\n"
            "1. 3–5 key angles or sub-topics to cover, with one concrete example or fact for each (name, date, number, or study).\n"
            "2. At least one common misconception to correct, with the correct explanation in one sentence.\n"
            "3. At least one counter-intuitive or surprising point with brief evidence.\n"
            "4. 1–2 discussion questions that would push the conversation deeper (Host B can use these).\n"
            "Do NOT write generic phrases. Every bullet must be specific to the topic.\n"
            f"{lang_instruction}"
        )

        user_msg = intro + (
            "Based on the above, output the outline now. Use bullet points or short paragraphs. "
            "This outline will be passed to the scriptwriter — so be specific and avoid filler."
        )

        try:
            outline = await self.call_llm_with_provider(
                provider,
                user_msg,
                system_prompt=system,
                expect_json=False,
                max_tokens=2048,
            )
            outline = (outline or "").strip()
            print(f"[podcast] deep outline len={len(outline)}")
            return outline[:6000]
        except Exception as e:
            print(f"[podcast] deep outline failed: {e}")
            return ""

    # ────────────────────────────────────────────────────────────
    #  Prompt builders
    # ────────────────────────────────────────────────────────────

    def _build_topic_prompt(
        self,
        topic: str,
        language: str,
        length: str,
        segments: str,
        deep_outline: Optional[str] = None,
    ) -> str:
        """自选主题模式的 user message（可注入深度提纲）"""
        base = (
            f"topic: {topic}\n"
            f"language: {language}\n"
            f"length: {length}\n"
            f"segments: {segments}\n\n"
        )
        if deep_outline and deep_outline.strip():
            base += (
                "=== DEEP DISCUSSION OUTLINE (you MUST use this — do not ignore) ===\n"
                f"{deep_outline.strip()}\n"
                "=== END OUTLINE ===\n\n"
            )
        base += (
            "CRITICAL INSTRUCTIONS — follow these precisely:\n"
            f"1. Research the topic \"{topic}\" deeply. For EACH segment you write, you MUST include at least ONE of:\n"
            "   - A specific named example (person, company, event, study) with year/date\n"
            "   - A concrete number, date, or statistic with its source context\n"
            "   - A step-by-step explanation of a mechanism or process (at least 3 steps)\n"
            "   - A real historical anecdote with names, dates, and outcomes\n"
            "   - A detailed case study showing cause and effect\n"
            "2. Do NOT write any segment that only says \"this is important\" or \"let's discuss X\" — every segment must TEACH something concrete.\n"
            "3. Host B must push back, add counterpoints, or reveal surprising nuances — not just agree.\n"
            "   Host B should say things like \"Wait, but that contradicts...\" or \"Actually, most people get this wrong...\"\n"
            "4. Include at least 2 segments with surprising or counter-intuitive facts that have specific evidence.\n"
            "5. Include at least 1 segment correcting a common misconception with the correct explanation.\n"
            "6. 侃侃而谈，每段不限制字数，可长可短，言之有物即可。\n"
            "7. NEVER use these hollow phrases without IMMEDIATELY following with specifics:\n"
            "   - \"这很有意思\" → instead say WHY it's interesting with a fact\n"
            "   - \"让我们来看看\" → instead directly present the content\n"
            "   - \"这是一个复杂的话题\" → instead explain what makes it complex\n"
            f"8. If language is Chinese, ALL title/summary/segment text MUST be Chinese.\n\n"
            "return only json"
        )
        return base

    def _build_materials_prompt(
        self,
        topic: str,
        materials_text: str,
        language: str,
        length: str,
        segments: str,
        deep_outline: Optional[str] = None,
    ) -> str:
        """基于学习资料模式的 user message — 将资料和主题严格分离，可注入深度提纲"""
        # 截取材料，确保不超过上下文窗口（保留给 prompt 本身的空间）
        max_material_chars = 36000
        trimmed_materials = materials_text[:max_material_chars]

        lang_instruction = (
            "所有输出（title、summary、segments）必须使用中文。"
            if language == "Chinese"
            else "All output (title, summary, segments) must be in English."
        )

        parts = [
            "=== REFERENCE MATERIALS START ===\n",
            f"{trimmed_materials}\n",
            "=== REFERENCE MATERIALS END ===\n\n",
            f"user_topic_hint: {topic}\n",
            f"language: {language}\n",
            f"length: {length}\n",
            f"segments: {segments}\n\n",
        ]
        if deep_outline and deep_outline.strip():
            parts.append(
                "=== DEEP DISCUSSION OUTLINE (use this to structure the conversation) ===\n"
                f"{deep_outline.strip()}\n=== END OUTLINE ===\n\n"
            )
        parts.append(
            "############################################################\n"
            "# CRITICAL INSTRUCTIONS — THE MATERIALS ABOVE ARE YOUR ONLY SOURCE #\n"
            "############################################################\n\n"
            "You are creating a podcast that TEACHES the listener the actual content of the reference materials.\n"
            "The user_topic_hint is just a label — you MUST derive ALL content from the materials themselves.\n\n"
            "MANDATORY RULES (violations will make the output useless):\n\n"
            "1. **MINE THE MATERIALS EXHAUSTIVELY**\n"
            "   - Read every paragraph of the materials. Identify ALL key concepts, definitions,\n"
            "     formulas, theorems, examples, case studies, data points, arguments, and conclusions.\n"
            "   - The podcast MUST cover these specific items — do NOT summarize vaguely.\n\n"
            "2. **QUOTE AND CITE SPECIFIC DETAILS**\n"
            "   - Each segment MUST reference at least one SPECIFIC detail from the materials:\n"
            "     a concrete term, definition, number, formula, name, date, or example.\n"
            "   - Use patterns like: \"资料里提到了...\" / \"The materials mention that...\" /\n"
            "     \"这里有个关键概念叫做...\" / \"There's a key concept called...\"\n"
            "   - If the materials contain formulas or equations, HOST A must explain them\n"
            "     step by step and HOST B must provide an intuitive analogy.\n\n"
            "3. **DEEP DIVE INTO SPECIFICS — NO SURFACE TALK**\n"
            "   - If the materials describe a process, explain EACH STEP of that process.\n"
            "   - If the materials compare two things, discuss EACH dimension of comparison.\n"
            "   - If the materials give an example, EXPAND on that example with \"what would\n"
            "     happen if...\" or \"why this matters because...\"\n"
            "   - NEVER say \"这很重要\" or \"this is interesting\" without IMMEDIATELY explaining WHY\n"
            "     with a specific reason from the materials.\n\n"
            "4. **HOST ROLES (CRITICAL)**\n"
            "   - HOST A: Presents and explains material content in detail. Uses phrases like:\n"
            "     \"资料里有一段特别有意思的内容...\" / \"让我来拆解一下这个公式/概念...\"\n"
            "   - HOST B: Asks specific follow-up questions that probe deeper:\n"
            "     \"等等，这个数据说明了什么？\" / \"那如果条件变了呢？\" / \"举个实际场景来说明？\"\n"
            "     HOST B must also connect different parts of the materials and point out\n"
            "     contradictions or surprising implications.\n\n"
            "5. **STRUCTURE**\n"
            "   - Opening: Start with the MOST interesting or surprising finding from the materials.\n"
            "   - Body: Walk through the materials' content systematically.\n"
            "     Each pair of A+B segments covers one topic/concept from the materials.\n"
            "   - Closing: Summarize the key takeaways WITH specific details, not generalities.\n\n"
            "6. **FORBIDDEN**\n"
            "   - Generic filler that could apply to any topic\n"
            "   - Ignoring what the materials actually say\n"
            "   - Saying \"the materials cover many aspects\" without listing them\n"
            "   - Repeating the same point with different wording\n"
            "   - Any segment without a direct reference to material content\n\n"
            f"{lang_instruction}\n\n"
            "return only json"
        )
        return "".join(parts)

    def _parse_script_response(self, response: str) -> Dict[str, Any]:
        if not response:
            return {}
        data = self.safe_parse_json(response)

        # LLM 可能返回纯数组 [{spk, md}, ...]，需包装为 {title, summary, segments}
        if isinstance(data, list):
            segments = []
            for item in data:
                if isinstance(item, dict) and ("spk" in item or "md" in item):
                    segments.append({
                        "spk": str(item.get("spk", "A"))[:1].upper() or "A",
                        "voice": item.get("voice"),
                        "md": str(item.get("md", "")),
                    })
            if segments:
                return {"title": "", "summary": "", "segments": segments}

        if isinstance(data, str):
            inner = data.strip()
            if inner.startswith("{") and inner.endswith("}"):
                try:
                    inner_data = json.loads(inner)
                    if isinstance(inner_data, dict):
                        return inner_data
                except Exception:
                    pass
        if isinstance(data, dict):
            return data

        extracted = self._extract_json_object(response)
        if extracted:
            try:
                parsed = json.loads(extracted)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    def _extract_json_object(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return cleaned

        start = cleaned.find("{")
        if start < 0:
            return ""
        depth = 0
        for i in range(start, len(cleaned)):
            ch = cleaned[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return cleaned[start : i + 1]
        return ""

    def _has_cjk(self, text: str) -> bool:
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def _strip_markdown(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"[`*_>#]", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def _choose_voice(self, text: str, idx: int, spk: Optional[str] = None) -> str:
        from config import config

        is_cjk = self._has_cjk(text)
        speaker = (spk or "").strip().upper()
        if is_cjk:
            voice_a = config.tts_voice_edge or "zh-CN-XiaoxiaoNeural"
            voice_b = config.tts_voice_alt_edge or "zh-CN-YunxiNeural"
        else:
            voice_a = config.tts_voice_edge or "en-US-AvaNeural"
            voice_b = config.tts_voice_alt_edge or "en-US-AndrewNeural"

        if speaker == "A":
            return voice_a
        if speaker == "B":
            return voice_b
        return voice_b if idx % 2 else voice_a

    def _script_has_cjk(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        if self._has_cjk(str(data.get("title") or "")):
            return True
        if self._has_cjk(str(data.get("summary") or "")):
            return True
        for seg in data.get("segments") or []:
            if self._has_cjk(str(seg.get("md") or "")):
                return True
        return False

    def _fallback_segments_zh(self, topic: str) -> List[PodcastSegment]:
        return [
            PodcastSegment(spk="A", md=f"欢迎来到今天的播客！今天我们要深入聊聊{topic}——这个话题远比大多数人以为的更有趣、更有深度。"),
            PodcastSegment(spk="B", md=f"没错，很多人对{topic}只停留在表面认知，但如果深入挖掘，你会发现它背后有很多反直觉的东西。我们今天就来拆解一下。"),
            PodcastSegment(spk="A", md=f"首先我们得搞清楚{topic}的核心定义和它要解决的根本问题。很多人一上来就谈应用，但不理解底层逻辑，很容易踩坑。"),
            PodcastSegment(spk="B", md=f"说得对。我来举个具体的例子来说明——在实际场景中，{topic}的应用远比教科书上讲的要复杂，因为现实条件往往不是理想化的。"),
            PodcastSegment(spk="A", md=f"这里有一个很常见的误区：很多人以为{topic}就是简单地套公式或者照搬别人的做法，但实际上你必须根据具体情况做调整。"),
            PodcastSegment(spk="B", md=f"最后给大家一个可以立刻用起来的建议：学习{topic}的最好方式不是记概念，而是找一个小项目或小场景亲自实践一下，踩过坑才真正理解。"),
        ]

    def _pad_segments_zh(self, segments: List[PodcastSegment], topic: str, target: int = 6) -> List[PodcastSegment]:
        padded = list(segments)
        filler = [
            f"说到{topic}，有一个很多人不知道的细节——让我来展开讲讲这背后的原理和实际影响。",
            f"等一下，我想补充一个关于{topic}的真实案例，这个案例非常能说明问题的复杂性。",
            f"你提到的这一点很关键。从数据来看，{topic}领域有一些反直觉的发现，比如很多人以为A会导致B，实际上恰恰相反。",
            f"我们换个角度来看{topic}——如果站在不同利益相关方的视角，你会发现完全不同的结论。",
            f"这让我想到一个有趣的类比：{topic}其实和我们日常生活中的某些决策过程非常相似，让我具体解释一下。",
            f"总结一下{topic}的核心要点：最重要的不是记住概念，而是理解背后的思维框架和应用场景。",
        ]
        i = 0
        while len(padded) < target:
            spk = "A" if len(padded) % 2 == 0 else "B"
            padded.append(PodcastSegment(spk=spk, md=filler[i % len(filler)]))
            i += 1
        return padded

    def _pad_segments_en(self, segments: List[PodcastSegment], topic: str, target: int = 6) -> List[PodcastSegment]:
        padded = list(segments)
        filler = [
            f"Here's a real-world case study that perfectly illustrates how {topic} works in practice — and why it matters more than most people realize.",
            f"Wait, there's a common misconception about {topic} I want to address. Most people get this wrong, and it leads to some pretty costly mistakes.",
            f"Let me break down the actual mechanism here — the key insight about {topic} is understanding not just WHAT happens, but WHY it happens at a fundamental level.",
            f"The practical takeaway from everything we've discussed about {topic}: here's what you can actually do with this knowledge starting today.",
        ]
        i = 0
        while len(padded) < target:
            spk = "A" if len(padded) % 2 == 0 else "B"
            padded.append(PodcastSegment(spk=spk, md=filler[i % len(filler)]))
            i += 1
        return padded

    async def _emit(self, emit_callback: callable, payload: Dict[str, Any]) -> None:
        try:
            result = emit_callback(payload)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            return
