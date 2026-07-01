"""
试卷生成 Agent
生成选择题、填空题、应用题（含简答与计算大题），使用项目配置的 DeepSeek LLM
"""
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class PaperInput(AgentInput):
    """试卷生成输入"""
    topic: str
    count_choice: int = 10
    count_fill: int = 5
    count_application: int = 2
    difficulty: str = "medium"


class PaperItem(BaseModel):
    """单道题目（多题型统一结构）"""
    id: int
    type: str  # "choice" | "fill" | "application"
    question: str
    options: Optional[List[str]] = None  # 仅选择题
    correct: Optional[int] = None  # 仅选择题，1-based
    answer: Optional[str] = None  # 填空题、应用题的参考答案
    explanation: Optional[str] = None


class PaperOutput(AgentOutput):
    """试卷生成输出"""
    paper: Optional[List[PaperItem]] = None


class PaperAgent(LLMAgent):
    """
    试卷生成 Agent
    根据主题与题型数量生成：选择题、填空题、应用题（简答+计算）
    """

    def __init__(self):
        self._base_system = """
你是一位专业的出题老师。请根据给定主题和难度，生成一份试卷。必须输出**具体、完整**的题目内容。

【重要】禁止使用任何占位符或模板文字：
- 禁止题目写「第X题」「关于xxx的选择题」等空洞表述，必须写出完整题干。
- 选择题的 options 必须是四个具体、互不相同的选项文字，禁止「选项A」「选项B」。
- 填空题、应用题的 answer 和 explanation 必须写出具体参考答案与解析。

OUTPUT：只输出一个 JSON 数组，不要 markdown 代码块、不要 ```、不要任何说明文字。

每个元素格式（严格按 type 区分）：
- type="choice"：id(数字), type("choice"), question(完整题干), options(4个选项字符串数组), correct(1-4), explanation(解析)
- type="fill"：id, type("fill"), question(完整题干), answer(参考答案), explanation
- type="application"：id, type("application"), question(完整题干，可含简答或计算大题), answer(参考答案，可含步骤), explanation

要求：与主题语言一致（中文主题全部用中文）；题目有区分度；难度体现在深度与计算量。
""".strip()
        super().__init__("paper_agent", self._base_system)
        self.description = "Generate exam papers with choice, fill-in-blank, and application questions"

    async def execute(self, input_data: PaperInput) -> PaperOutput:
        """执行试卷生成"""
        try:
            paper = await self._generate_paper(
                topic=input_data.topic,
                count_choice=input_data.count_choice,
                count_fill=input_data.count_fill,
                count_application=input_data.count_application,
                difficulty=input_data.difficulty or "medium",
            )
            return PaperOutput(success=True, data={"paper": [p.dict() for p in paper]}, paper=paper)
        except Exception as e:
            return PaperOutput(success=False, error=str(e), paper=None)

    async def _generate_paper(
        self,
        topic: str,
        count_choice: int,
        count_fill: int,
        count_application: int,
        difficulty: str,
    ) -> List[PaperItem]:
        n_choice = max(0, min(30, count_choice))
        n_fill = max(0, min(20, count_fill))
        n_app = max(0, min(20, count_application))
        total = n_choice + n_fill + n_app
        if total == 0:
            return []

        diff_hint = {
            "easy": "难度：简单，侧重概念与基础计算。",
            "medium": "难度：中等，概念与应用并重，计算适中。",
            "hard": "难度：困难，综合应用与较复杂计算。",
        }.get(str(difficulty).lower(), "难度：中等。")

        user_msg = f"""主题：{topic}
{diff_hint}

请严格按下列数量与顺序生成**具体题目**，输出一个 JSON 数组：
- 前 {n_choice} 题：选择题（type="choice"，question 完整题干，options 为 4 个具体选项，correct 为 1-4，explanation 可简短一两句）
- 第 {n_choice + 1} 到 {n_choice + n_fill} 题：填空题（type="fill"，question 完整，answer 参考答案，explanation 简短）
- 最后 {n_app} 题：应用题（type="application"，question 完整，answer 参考答案可含步骤，explanation 简短）

共 {total} 题。每道题须写出完整、具体的题目和答案，不要占位符。explanation 与 answer 尽量简洁以控制长度。只输出 JSON 数组，不要其它任何文字。"""

        response = await self.call_llm(
            user_msg,
            system_prompt=self._base_system,
            expect_json=True,
            max_tokens=16384,
        )
        # [DEBUG] 原始 LLM 响应（便于排查是否生成具体内容）
        def _debug(msg: str, *args: object) -> None:
            import sys
            text = msg % args if args else msg
            print("[PAPER_DEBUG] " + text, flush=True)
            import logging
            logging.getLogger("paper_agent").info("[PAPER_DEBUG] %s", text)

        _debug("LLM response length=%d, preview=%s", len(response), (response[:500] + "..." if len(response) > 500 else response))

        items = self._parse_paper_response(response, n_choice, n_fill, n_app)
        _debug("Parsed items count=%d, expected total=%d", len(items), total)
        if items:
            first = items[0]
            _debug("First item: type=%s, question_len=%d, question_preview=%s", first.type, len(first.question), (first.question[:80] + "..." if len(first.question) > 80 else first.question))
            if first.options:
                _debug("First item options count=%d, first_option=%s", len(first.options), (first.options[0][:60] + "..." if first.options and len(first.options[0]) > 60 else (first.options[0] if first.options else "")))

        # 只要有解析出的题目就优先使用，避免用模板覆盖
        if len(items) > 0:
            if len(items) < total:
                _debug("Padding from %d to %d", len(items), total)
                items = self._pad_paper(items, topic, total, n_choice, n_fill, n_app)
            return items
        # 仅当完全解析失败时才用模板生成
        _debug("No items parsed, using fallback template paper")
        return self._pad_paper([], topic, total, n_choice, n_fill, n_app)

    def _parse_paper_response(
        self, response: str, n_choice: int, n_fill: int, n_app: int
    ) -> List[PaperItem]:
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response)
        array_match = re.search(r"\[[\s\S]*", response)
        if not array_match:
            print("[PAPER_DEBUG] No JSON array found in response", flush=True)
            return []
        response = array_match.group(0)
        # 若响应被截断，可能缺少末尾的 ] 或最后一个对象未写完，先尝试直接解析
        if not response.rstrip().endswith("]"):
            response = response.rstrip()
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            print("[PAPER_DEBUG] JSON decode error:", e, flush=True)
            # 尝试从截断的 JSON 中恢复：找到最后一个完整的对象边界 "}, {"，只解析到该处
            data = self._recover_truncated_json(response)
            if not data:
                return []
        if not isinstance(data, list):
            print("[PAPER_DEBUG] Response is not a list, type=" + type(data).__name__, flush=True)
            return []
        return self._coerce_paper(data, n_choice, n_fill, n_app)

    def _recover_truncated_json(self, response: str) -> Optional[List[Dict[str, Any]]]:
        """从被截断的 JSON 数组中恢复已完整输出的题目对象（LLM 输出被截断时）。"""
        # 找到所有对象之间的分隔 "}, {"，从后往前尝试解析
        for match in reversed(list(re.finditer(r"\}\s*,\s*\{", response))):
            end = match.start() + 1
            prefix = response[:end] + "]"
            try:
                data = json.loads(prefix)
                if isinstance(data, list) and len(data) > 0:
                    print("[PAPER_DEBUG] Recovered %d items from truncated JSON" % len(data), flush=True)
                    return data
            except json.JSONDecodeError:
                continue
        # 可能只有一个对象，尝试补 "]"
        try:
            data = json.loads(response.rstrip() + "]")
            if isinstance(data, list) and len(data) > 0:
                print("[PAPER_DEBUG] Recovered %d item(s) (single object)" % len(data), flush=True)
                return data
        except json.JSONDecodeError:
            pass
        return None

    def _coerce_paper(
        self,
        data: List[Any],
        n_choice: int,
        n_fill: int,
        n_app: int,
    ) -> List[PaperItem]:
        items: List[PaperItem] = []
        idx = 0
        types_spec = (
            [("choice", n_choice), ("fill", n_fill), ("application", n_app)]
        )
        for qtype, count in types_spec:
            for _ in range(count):
                raw = data[idx] if idx < len(data) else {}
                idx += 1
                if not isinstance(raw, dict):
                    raw = {}
                t = str(raw.get("type") or qtype).strip().lower()
                if t not in ("choice", "fill", "application"):
                    t = qtype
                question = self._str(raw.get("question"), 500) or f"第 {len(items) + 1} 题"
                explanation = self._str(raw.get("explanation"), 300) or "略"
                if t == "choice":
                    options = raw.get("options")
                    if not isinstance(options, list):
                        options = []
                    options = [self._str(o, 200) for o in options[:4] if self._str(o, 1)]
                    while len(options) < 4:
                        options.append(f"选项 {len(options) + 1}")
                    correct = self._normalize_correct(raw.get("correct"))
                    items.append(
                        PaperItem(
                            id=len(items) + 1,
                            type="choice",
                            question=question,
                            options=options,
                            correct=correct,
                            answer=None,
                            explanation=explanation,
                        )
                    )
                else:
                    answer = self._str(raw.get("answer"), 500) or "略"
                    items.append(
                        PaperItem(
                            id=len(items) + 1,
                            type=t,
                            question=question,
                            options=None,
                            correct=None,
                            answer=answer,
                            explanation=explanation,
                        )
                    )
        return items

    def _str(self, value: Any, max_len: int) -> str:
        if value is None:
            return ""
        s = str(value).strip()
        s = re.sub(r"\s+", " ", s)
        return s[:max_len] if s else ""

    def _normalize_correct(self, value: Any) -> int:
        if isinstance(value, int) and 1 <= value <= 4:
            return value
        if isinstance(value, str):
            v = value.strip().upper()
            if v in ("A", "1"):
                return 1
            if v in ("B", "2"):
                return 2
            if v in ("C", "3"):
                return 3
            if v in ("D", "4"):
                return 4
        return 1

    def _pad_paper(
        self,
        items: List[PaperItem],
        topic: str,
        total: int,
        n_choice: int,
        n_fill: int,
        n_app: int,
    ) -> List[PaperItem]:
        type_queue: List[str] = []
        type_queue.extend(["choice"] * n_choice)
        type_queue.extend(["fill"] * n_fill)
        type_queue.extend(["application"] * n_app)
        while len(items) < total:
            i = len(items) + 1
            t = type_queue[len(items)] if len(items) < len(type_queue) else "choice"
            if t == "choice":
                items.append(
                    PaperItem(
                        id=i,
                        type="choice",
                        question=f"关于「{topic}」的选择题（第{i}题）",
                        options=["A", "B", "C", "D"],
                        correct=1,
                        answer=None,
                        explanation="略",
                    )
                )
            else:
                items.append(
                    PaperItem(
                        id=i,
                        type=t,
                        question=f"关于「{topic}」的{t}题（第{i}题）",
                        options=None,
                        correct=None,
                        answer="参考答案略",
                        explanation="略",
                    )
                )
        return items[:total]
