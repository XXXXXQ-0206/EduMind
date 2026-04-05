"""
教案生成 Agent
使用 DeepSeek（或配置的 LLM）按标准教案模板生成：教学目标（三维）、教学重难点、教学准备、教学过程、作业设计
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class LessonPlanInput(AgentInput):
    """教案生成输入"""
    topic: str
    materials_context: Optional[str] = None  # 可选备课资料文本


class TeachingGoal(BaseModel):
    """三维目标单项"""
    knowledge: str = ""   # 知识与技能
    process: str = ""     # 过程与方法
    emotion: str = ""     # 情感态度与价值观


class TeachingProcessStep(BaseModel):
    """教学过程单步"""
    title: str = ""      # 如 导入、新授、练习、总结
    content: str = ""


class LessonPlanData(BaseModel):
    """教案结构化数据"""
    title: str = ""
    teaching_goals: TeachingGoal = TeachingGoal()
    key_points: List[str] = []
    difficult_points: List[str] = []
    preparation: List[str] = []           # 教学准备
    process: List[TeachingProcessStep] = []  # 教学过程
    homework: str = ""                   # 作业设计


class LessonPlanOutput(AgentOutput):
    """教案生成输出"""
    plan: Optional[LessonPlanData] = None


class LessonPlanAgent(LLMAgent):
    """
    教案生成 Agent
    按标准教案模板拆解：三维目标、重难点、教学准备、教学过程（导入/新授/练习/总结）、作业设计
    """

    SYSTEM_PROMPT = """
你是一位经验丰富的教研专家，请根据给定的课题（及可选备课资料）生成一份规范、可直接使用的教案。

输出要求：
1. 仅输出一个 JSON 对象，不要输出 markdown 代码块或其它说明文字。
2. 使用以下结构（字段名必须一致，且为中文内容）：

{
  "title": "课题名称",
  "teaching_goals": {
    "knowledge": "知识与技能目标（1-2 条，具体可测）",
    "process": "过程与方法目标（1 条）",
    "emotion": "情感态度与价值观目标（1 条）"
  },
  "key_points": ["教学重点1", "教学重点2"],
  "difficult_points": ["教学难点1", "教学难点2"],
  "preparation": ["教学准备项1（如：PPT、教具）", "教学准备项2"],
  "process": [
    { "title": "一、导入", "content": "导入环节的详细设计（情境、问题、时间安排等）" },
    { "title": "二、新授", "content": "新授环节的详细设计（分步骤、师生活动、重难点突破）" },
    { "title": "三、练习", "content": "练习环节的详细设计（巩固与反馈）" },
    { "title": "四、总结", "content": "课堂小结与板书要点" }
  ],
  "homework": "作业设计（分层或拓展，具体可操作）"
}

规范说明：
- 课题与资料若为中文，全文使用中文；若为英文，可中英结合，以中文为主。
- 目标表述要具体、可观测，避免空泛。
- 教学过程各环节内容要充实，体现师生活动与时间安排思路。
- 作业设计要明确、可检查。
""".strip()

    def __init__(self):
        super().__init__("lesson_plan_agent", self.SYSTEM_PROMPT)
        self.description = "Generate standard lesson plans with 3D goals, key/difficult points, preparation, process, and homework"

    async def execute(self, input_data: LessonPlanInput) -> LessonPlanOutput:
        """执行教案生成"""
        try:
            plan = await self._generate_plan(
                input_data.topic,
                input_data.materials_context,
            )
            return LessonPlanOutput(success=True, data={"plan": plan.model_dump()}, plan=plan)
        except Exception as e:
            return LessonPlanOutput(success=False, error=str(e), plan=None)

    async def _generate_plan(self, topic: str, materials_context: Optional[str] = None) -> LessonPlanData:
        """调用 LLM 生成并解析教案"""
        user_content = f"课题：\n{topic}\n\n"
        if materials_context and materials_context.strip():
            user_content += f"备课资料（请优先依据以下资料设计教案）：\n{materials_context}\n\n"
        user_content += "请直接输出上述 JSON 对象，不要包含其它文字、不要用 markdown 代码块包裹。"

        # 使用原始输出；提高 max_tokens 避免教案 JSON 被截断
        response = await self.call_llm(
            user_content,
            system_prompt=self.SYSTEM_PROMPT,
            expect_json=False,
            max_tokens=16384,
        )
        if not (response and response.strip()):
            raise ValueError("LLM 返回为空，请检查 API 配置与网络。")

        data = self._parse_response(response)
        if not data:
            logger.warning("教案 JSON 解析失败，原始响应片段: %s", (response[:500] if response else ""))
            raise ValueError("无法从模型输出中解析出教案 JSON，请重试或检查模型是否按约定输出。")
        return self._coerce_plan(data, topic)

    def _strip_thinking(self, text: str) -> str:
        """去掉 DeepSeek R1 等模型的 think 块，只保留后续正文。"""
        if not text:
            return text
        # 去掉 think 标签整块（含换行）
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
        return text.strip()

    def _extract_json_object(self, text: str) -> str:
        """从文本中按括号匹配提取第一个完整 JSON 对象，避免被字符串内的 } 截断"""
        start = text.find("{")
        if start < 0:
            return ""
        depth = 0
        in_string = False
        escape = False
        quote = None
        i = start
        while i < len(text):
            c = text[i]
            if escape:
                escape = False
                i += 1
                continue
            if c == "\\" and in_string:
                escape = True
                i += 1
                continue
            if not in_string:
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
                elif c in ('"', "'"):
                    in_string = True
                    quote = c
            else:
                if c == quote:
                    in_string = False
            i += 1
        return ""

    def _repair_truncated_json(self, raw: str) -> str:
        """若 LLM 输出被截断，补全缺失的键和闭合括号以便解析"""
        raw = raw.rstrip()
        if not raw or not raw.startswith("{"):
            return raw
        if raw.endswith("}"):
            return raw
        s = raw.rstrip()
        # 截断在 process 数组内（如 "title": "一、导入", "c ）：补全 content、闭合对象与数组、补 homework
        if '"process"' in s and ("process" in s and "[" in s):
            while s and s[-1] in (",", " ", '"', "c", "o", "n", "t", "e"):
                s = s[:-1].rstrip()
            if s.endswith('"'):
                s = s[:-1].rstrip()
            if s.endswith(","):
                s = s[:-1]
            has_homework = '"homework"' in s
            tail = '"content": ""}]}' + (',"homework":""}' if not has_homework else "}")
            return s + "," + tail
        # 其他截断：补 preparation / process / homework
        tail = '"preparation":[],"process":[],"homework":""}'
        while s and s[-1] in (",", " ", '"'):
            s = s[:-1].rstrip()
        if s.endswith("]"):
            return s + "," + tail[1:]
        if s.endswith("}"):
            return s
        return s + "," + tail[1:]

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """从 LLM 响应中解析 JSON 对象（兼容 <think> 块、markdown 代码块、截断输出）"""
        text = response.strip()
        text = self._strip_thinking(text)
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
        text = text.strip()
        # 优先用括号匹配提取
        json_str = self._extract_json_object(text)
        if not json_str:
            obj_match = re.search(r"\{[\s\S]*\}", text)
            if obj_match:
                json_str = obj_match.group(0)
        if not json_str and "{" in text:
            json_str = text[text.index("{"):]
        if not json_str:
            json_str = text
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        repaired = self._repair_truncated_json(json_str)
        if repaired != json_str:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        logger.debug("JSON 解析失败，片段: %s", json_str[:500])
        return {}

    def _coerce_plan(self, data: Dict[str, Any], fallback_title: str) -> LessonPlanData:
        """将字典转为 LessonPlanData，缺项补全"""
        title = (data.get("title") or fallback_title or "教案").strip()[:200]

        tg = data.get("teaching_goals") or {}
        if isinstance(tg, dict):
            teaching_goals = TeachingGoal(
                knowledge=(tg.get("knowledge") or "").strip() or "掌握本课核心知识与技能。",
                process=(tg.get("process") or "").strip() or "经历探究与归纳的过程，提升思维方法。",
                emotion=(tg.get("emotion") or "").strip() or "形成积极的学习态度与价值观。",
            )
        else:
            teaching_goals = TeachingGoal()

        key_points = data.get("key_points")
        if not isinstance(key_points, list):
            key_points = []
        key_points = [str(x).strip() for x in key_points if x][:5]

        difficult_points = data.get("difficult_points")
        if not isinstance(difficult_points, list):
            difficult_points = []
        difficult_points = [str(x).strip() for x in difficult_points if x][:5]

        preparation = data.get("preparation")
        if not isinstance(preparation, list):
            preparation = []
        preparation = [str(x).strip() for x in preparation if x][:10]

        process_raw = data.get("process")
        process: List[TeachingProcessStep] = []
        if isinstance(process_raw, list):
            for item in process_raw:
                if isinstance(item, dict):
                    process.append(TeachingProcessStep(
                        title=(item.get("title") or "").strip() or "环节",
                        content=(item.get("content") or "").strip() or "",
                    ))
                elif isinstance(item, str):
                    process.append(TeachingProcessStep(title="环节", content=str(item).strip()))
        if not process:
            process = [
                TeachingProcessStep(title="一、导入", content="创设情境，引出课题。"),
                TeachingProcessStep(title="二、新授", content="展开新知，突破重难点。"),
                TeachingProcessStep(title="三、练习", content="巩固练习，及时反馈。"),
                TeachingProcessStep(title="四、总结", content="课堂小结，布置作业。"),
            ]

        homework = (data.get("homework") or "").strip()
        if not homework:
            homework = "完成课后练习；学有余力者可拓展阅读。"

        return LessonPlanData(
            title=title,
            teaching_goals=teaching_goals,
            key_points=key_points,
            difficult_points=difficult_points,
            preparation=preparation,
            process=process,
            homework=homework,
        )
