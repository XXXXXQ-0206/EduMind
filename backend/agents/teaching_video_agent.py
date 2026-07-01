"""
教学视频文案生成 Agent
使用 LLM（如 DeepSeek）根据主题与可选备课资料生成视频脚本文案，供后续即梦文生视频使用
"""
from typing import Optional

from agents.base import LLMAgent, AgentInput, AgentOutput


class TeachingVideoInput(AgentInput):
    """教学视频文案生成输入"""
    topic: str
    materials_context: Optional[str] = None  # 备课资料摘要/正文，可选


class TeachingVideoOutput(AgentOutput):
    """教学视频文案生成输出"""
    script: Optional[str] = None  # 纯文本脚本，适合交给即梦文生视频


SYSTEM_PROMPT = """
你是一位教学视频脚本撰写专家。根据用户给出的主题（以及可选的备课资料内容），撰写一段适合「文生视频」使用的教学讲解脚本。

要求：
1. 语言与主题一致（中文主题用中文，英文主题用英文）。
2. 脚本为连贯的讲解词，适合配音或字幕，长度控制在 200–600 字（约 1–3 分钟口播）。
3. 结构清晰：开场点题 → 要点讲解 → 小结或引导。
4. 纯文本输出，不要 Markdown、不要标题层级、不要列表符号，仅一段可朗读的正文。
5. 若提供了备课资料，请基于资料内容撰写，保证准确、贴合教学场景；若未提供资料，则基于主题常识撰写。
6. 用词口语化、适合讲解，避免复杂公式或过长句子。
7. 直接输出脚本正文，不要输出「脚本如下」等前缀。
""".strip()


class TeachingVideoAgent(LLMAgent):
    """
    教学视频文案生成 Agent
    先用 LLM 生成讲解脚本，后续可将脚本传给即梦等文生视频模型
    """

    def __init__(self):
        super().__init__("teaching_video_agent", SYSTEM_PROMPT)
        self.description = "Generate teaching video script from topic (and optional materials) for text-to-video"

    async def execute(self, input_data: TeachingVideoInput) -> TeachingVideoOutput:
        """执行文案生成"""
        try:
            script = await self._generate_script(
                input_data.topic,
                input_data.materials_context,
            )
            return TeachingVideoOutput(success=True, data={"script": script}, script=script)
        except Exception as e:
            return TeachingVideoOutput(success=False, error=str(e), script=None)

    async def _generate_script(self, topic: str, materials_context: Optional[str] = None) -> str:
        topic = (topic or "").strip()
        if not topic:
            return "请提供教学主题。"

        user_content = f"教学主题：{topic}\n\n"
        if materials_context and materials_context.strip():
            user_content += "备课资料内容：\n" + materials_context.strip() + "\n\n请基于以上资料撰写教学视频脚本。"
        else:
            user_content += "请根据该主题撰写教学视频脚本（未提供备课资料，请基于常识撰写）。"

        response = await self.call_llm(
            user_content,
            system_prompt=SYSTEM_PROMPT,
            expect_json=False,
            max_tokens=2048,
        )

        script = (response or "").strip()
        # 去掉常见前缀
        for prefix in ("脚本如下：", "脚本：", "以下是脚本", "讲解脚本：", "【脚本】"):
            if script.startswith(prefix):
                script = script[len(prefix):].strip()
        if not script:
            script = "生成失败，请重试。"
        return script[:8000]  # 限制长度

    async def script_to_video_prompt(self, script: str) -> str:
        """
        将讲解脚本改写成适合文生视频的画面描述（教学微课风格），
        与讲解内容强相关，200–400 字，供即梦生成画面用。
        """
        script = (script or "").strip()[:2000]
        if not script:
            return "教学微课，知识讲解，清晰简洁的画面。"
        sys = """你是教学视频导演提示词专家。根据下面这段教学讲解脚本，写一段「文生视频」用的高质量画面描述。

要求：
1. 与讲解内容强相关：画面场景、动态演示、镜头节奏要贴合脚本主题与逻辑。
2. 教学微课风格：突出知识点可视化、实验演示、结构变化、角色或物体运动、镜头推进和转场。
3. 必须明确避免：整屏字幕、PPT 排版、海报封面、静止画面、logo、水印、重复镜头、机械的文字刷屏。
4. 只描述「画面与氛围」，不要写旁白或对白文字；可包含镜头语言（如：镜头缓缓推进、元素模型旋转、实验现象展开）。
5. 中文，200–400 字，一段连续描述，不要分点、不要标题。
5. 直接输出描述正文，不要加「画面描述如下」等前缀。"""
        user = f"教学讲解脚本：\n\n{script}\n\n请写出与之匹配的高质量教学视频画面提示词，重点是动态画面与知识可视化，不要字幕墙。"
        try:
            out = await self.call_llm(user, system_prompt=sys, expect_json=False, max_tokens=1024)
            out = (out or "").strip()
            for prefix in ("画面描述：", "画面描述如下：", "描述：", "【画面描述】"):
                if out.startswith(prefix):
                    out = out[len(prefix):].strip()
            return (out[:800] if out else self.fallback_video_prompt("教学主题", script)).strip()
        except Exception:
            return self.fallback_video_prompt("教学主题", script)

    def recommend_video_profile(self, topic: str, script: str) -> dict:
        text = f"{topic} {script}".lower()
        style = "vivid_fun"
        if any(token in text for token in ("实验", "reaction", "实验室", "化学", "physics", "物理", "生物")):
            style = "experiment_demo"
        elif any(token in text for token in ("表", "图", "坐标", "曲线", "统计", "趋势", "地图", "周期表")):
            style = "table_exploration"
        elif any(token in text for token in ("历史", "革命", "典故", "故事", "朝代")):
            style = "story_introduction"
        elif any(token in text for token in ("案例", "应用", "分析")):
            style = "case_analysis"
        return {
            "student_type": "mixed_age",
            "teaching_style": style,
            "voice_type": "zh_female_linjianvhai_moon_bigtts",
        }

    def build_gateway_video_prompt(self, topic: str, script: str) -> str:
        summary = "；".join(
            part.strip()
            for part in __import__("re").split(r"[。！？!?；;\n]+", script or "")
            if part.strip()
        )[:320]
        return (
            f"教学主题：{(topic or '课堂知识点').strip()}。"
            f"讲解重点：{summary or '围绕核心概念展开讲解。'}"
            " 请生成适合课堂播放的高质量微课视频：要有动态教学动画、结构变化、实验/示意演示、镜头推进与转场；"
            "禁止整屏字幕、禁止 PPT 式文字堆砌、禁止静态封面、禁止重复镜头，讲解语音要自然、有起伏、语速适中。"
        ).strip()

    def fallback_video_prompt(self, topic: str, script: str) -> str:
        return (
            f"高质量 K12 教学微课短视频，主题是{(topic or '课堂知识点').strip()}。"
            " 课堂或实验室环境中，镜头缓缓推进，出现动态知识点可视化、结构变化、关键概念演示和场景切换，"
            "画面清晰、节奏流畅、科普感强。禁止整屏字幕、禁止 PPT、禁止海报封面、禁止静止文字卡。"
        ).strip()
