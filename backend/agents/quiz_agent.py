"""
测验生成 Agent
生成包含提示和解释的多项选择题
"""
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class QuizInput(AgentInput):
    """测验生成输入"""
    topic: str
    count: int = 5


class QuizItem(BaseModel):
    """单个测验题"""
    id: int
    question: str
    options: List[str]
    correct: int
    hint: str
    explanation: str


class QuizOutput(AgentOutput):
    """测验生成输出"""
    quiz: Optional[List[QuizItem]] = None


class QuizAgent(LLMAgent):
    """
    测验生成 Agent
    根据主题生成包含多道多项选择题的测验
    """

    def __init__(self):
        self.system_prompt_template = """
PRIMARY OBJECTIVE
    Generate exactly {count} multiple-choice questions about the given topic.

OUTPUT CONTRACT
Return only a JSON array with {count} objects.
No markdown, no code fences, no prose outside the JSON.

SCHEMA
"id": 1..{count}
"question": clear and unambiguous question text in the same language as the topic
"options": array of exactly 4 distinct strings; each prefixed with A) , B) , C) , D)
"correct": 1|2|3|4 (1-based index into options, where 1=A, 2=B, 3=C, 4=D)
"hint": helpful hint text
"explanation": detailed explanation

STYLE
- Use the same language as the topic (Chinese for Chinese topics, English for English topics)
- Plain text only. No LaTeX. No markdown in the options.
- All options must be realistic and relevant to the question
- Questions should test understanding, not just recall

VALIDATION
Exactly {count} items
Each item has all 6 keys
options length is exactly 4
correct in [1,2,3,4]
All strings trimmed and non-empty

FAIL-SAFE
If uncertain, pick the standard interpretation of the topic.
Output only the JSON array.
""".strip()

        super().__init__("quiz_agent", self.system_prompt_template.format(count=5))
        self.description = "Generate multiple-choice quizzes with hints and explanations"

    async def execute(self, input_data: QuizInput) -> QuizOutput:
        """执行测验生成"""
        try:
            # 生成测验
            quiz = await self._generate_quiz(input_data.topic, input_data.count)

            return QuizOutput(success=True, data={"quiz": quiz}, quiz=quiz)

        except Exception as e:
            return QuizOutput(success=False, error=str(e), quiz=None)

    async def _generate_quiz(self, topic: str, count: int) -> List[QuizItem]:
        """生成测验题目"""

        count = self._normalize_count(count)
        system_prompt = self._system_prompt_for_count(count)

        # 第一次尝试
        response = await self.call_llm(
            f"Topic:\n{topic}\nQuestions: {count}\nReturn only the JSON array.",
            system_prompt=system_prompt,
            expect_json=True,
        )

        quiz_data = self._parse_quiz_response(response, count)

        # 检查数据质量 - 如果所有问题都是默认值，则重新生成
        if quiz_data and len(quiz_data) == count:
            has_real_content = any(
                q.question != f"问题 {i + 1}"
                and "选项 A" not in q.options[0]
                for i, q in enumerate(quiz_data)
            )

            if has_real_content:
                return quiz_data

        # 第二次尝试：更严格的提示
        strict_prompt = f"""
RETRY: STRICT FORMAT ONLY

OUTPUT
    Only a JSON array with {count} objects. No markdown. No extra text.

FIELDS
id 1..{count}
question clear question text
options array of 4 strings
correct 1|2|3|4
hint helpful hint
explanation detailed explanation

IMPORTANT:
- Use plain Chinese text for questions and options
- Do NOT use placeholders like "问题 1" or "选项 A"
- Each option must be meaningful and relevant
"""
        response2 = await self.call_llm(
            f"Topic:\n{topic}\nQuestions: {count}\nReturn only the JSON array.",
            system_prompt=strict_prompt,
            expect_json=True,
        )
        quiz_data2 = self._parse_quiz_response(response2, count)

        # 检查第二次尝试的质量
        if quiz_data2 and len(quiz_data2) == count:
            has_real_content = any(
                q.question != f"问题 {i + 1}"
                and "选项 A" not in q.options[0]
                for i, q in enumerate(quiz_data2)
            )

            if has_real_content:
                return quiz_data2

        # 如果两次都失败，使用备选方案：手动构建简单测验
        return self._create_fallback_quiz(topic, count)

    def _parse_quiz_response(self, response: str, count: int) -> List[QuizItem]:
        """解析测验响应"""
        # 移除代码围栏（先做这个，因为围栏可能影响正则匹配）
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*|\s*```$", "", response)

        # 提取 JSON 数组
        array_match = re.search(r"\[[\s\S]*\]", response)
        if array_match:
            response = array_match.group(0)

        # 解析 JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            data = []

        # 强制转换和清理
        return self._coerce_quiz(data, count)

    def _coerce_quiz(self, data: Any, count: int) -> List[QuizItem]:
        """强制转换和清理测验数据"""
        if not isinstance(data, list):
            data = []

        items = []

        count = self._normalize_count(count)
        for i, item in enumerate(data[:count]):
            try:
                # 获取原始字段值
                raw_question = item.get("question", "")
                raw_hint = item.get("hint", "")
                raw_explanation = item.get("explanation", "")
                raw_options = item.get("options", [])

                # 清理选项
                options = self._clean_options(raw_options)

                # 确保有4个选项
                while len(options) < 4:
                    options.append(f"选项 {len(options) + 1}")

                # 规范化正确答案索引
                correct = self._normalize_correct_index(item.get("correct", 1))

                # 获取问题文本
                question_text = self._normalize_string(raw_question, min_len=0, max_len=160)
                hint_text = self._normalize_string(raw_hint, min_len=0, max_len=120)
                explanation_text = self._normalize_string(raw_explanation, min_len=0, max_len=200)

                # 创建题目
                quiz_item = QuizItem(
                    id=i + 1,
                    question=question_text if question_text else f"问题 {i + 1}",
                    options=options[:4],
                    correct=correct,
                    hint=hint_text if hint_text else "请使用核心概念来回答。",
                    explanation=explanation_text if explanation_text else "正确选项符合主要思想，其他选项不符合。",
                )
                items.append(quiz_item)
            except Exception:
                pass

        # 确保有足够题目
        while len(items) < count:
            i = len(items)
            if items:
                # 复制最后一题并旋转选项
                src = items[-1]
                rotated_options = src.options[1:] + [src.options[0]]
                correct = ((src.correct - 1) % 4) + 1
                quiz_item = QuizItem(
                    id=i + 1,
                    question=src.question,
                    options=rotated_options,
                    correct=correct,
                    hint=src.hint,
                    explanation=src.explanation,
                )
            else:
                # 创建默认题目
                quiz_item = QuizItem(
                    id=i + 1,
                    question=f"问题 {i + 1}",
                    options=["选项 A", "选项 B", "选项 C", "选项 D"],
                    correct=1,
                    hint="使用核心概念。",
                    explanation="正确选项符合主要思想。",
                )
            items.append(quiz_item)

        return items

    def _normalize_count(self, count: int) -> int:
        if isinstance(count, int) and count > 0:
            return min(max(count, 1), 20)
        return 5

    def _system_prompt_for_count(self, count: int) -> str:
        return self.system_prompt_template.format(count=count)

    def _clean_options(self, options: Any) -> List[str]:
        """清理和规范选项"""
        if isinstance(options, str):
            options = re.split(r"[,;|]\s*", options)
        if not isinstance(options, list):
            options = []

        cleaned = []
        seen = set()

        for opt in options:
            if not isinstance(opt, str):
                continue

            # 移除前缀 (A), B), C), D) 或 1), 2), 3), 4)
            opt_clean = re.sub(r"^\s*(?:[A-D]\)|[1-4]\)|\d+[\.\)]\s*)", "", str(opt)).strip()

            # 转为小写去重，但保留原始大小写
            opt_lower = opt_clean.lower()
            if opt_clean and opt_lower not in seen:
                seen.add(opt_lower)
                cleaned.append(opt_clean)
                if len(cleaned) >= 4:
                    break

        # 不添加前缀，返回纯文本（前端会自动添加 A) B) C) D)）
        # 如果不足4个，添加占位符
        while len(cleaned) < 4:
            cleaned.append(f"选项 {len(cleaned) + 1}")

        return cleaned[:4]

    def _normalize_correct_index(self, value: Any) -> int:
        """规范化正确答案索引"""
        if isinstance(value, int):
            return max(1, min(4, value))

        if isinstance(value, str):
            value_upper = value.strip().upper()

            # 检查数字 1-4
            if re.match(r"^[1-4]$", value_upper):
                return int(value_upper)

            # 检查字母 A-D
            if value_upper.startswith("A"):
                return 1
            elif value_upper.startswith("B"):
                return 2
            elif value_upper.startswith("C"):
                return 3
            elif value_upper.startswith("D"):
                return 4

            # 尝试提取数字
            match = re.search(r"\d", value_upper)
            if match:
                num = int(match.group())
                if 1 <= num <= 4:
                    return num

        return 1

    def _normalize_string(self, value: Any, min_len: int = 1, max_len: int = 500) -> str:
        """规范化字符串"""
        text = str(value or "") if value else ""
        text = re.sub(r"\s+", " ", text).strip()

        # 不检查最小长度，只要有内容就返回
        # 中文字符可能较少但含义完整
        if not text:
            return ""

        return text[:max_len]

    def _validate_quiz(self, quiz: List[QuizItem], count: int = 5) -> bool:
        """验证测验数据"""
        if not isinstance(quiz, list) or len(quiz) != self._normalize_count(count):
            return False

        for item in quiz:
            if not isinstance(item, QuizItem):
                return False
            if len(item.options) != 4:
                return False
            if item.correct < 1 or item.correct > 4:
                return False

        return True

    def _create_fallback_quiz(self, topic: str, count: int) -> List[QuizItem]:
        """创建备选测验"""
        count = self._normalize_count(count)
        base = [
            {
                "question": f"关于{topic}，以下哪个描述是正确的？",
                "options": ["描述 A", "描述 B", "描述 C", "描述 D"],
                "hint": f"思考{topic}的核心概念",
                "explanation": f"这是关于{topic}的基础问题",
            },
            {
                "question": f"在{topic}中，最重要的概念是什么？",
                "options": ["概念 A", "概念 B", "概念 C", "概念 D"],
                "hint": f"回顾{topic}的主要内容",
                "explanation": f"核心概念是{topic}的关键",
            },
            {
                "question": f"{topic}的主要特点包括哪些？",
                "options": ["特点 A", "特点 B", "特点 C", "特点 D"],
                "hint": f"考虑{topic}的实际应用",
                "explanation": f"这些特点定义了{topic}",
            },
            {
                "question": f"如何在实际场景中应用{topic}？",
                "options": ["应用 A", "应用 B", "应用 C", "应用 D"],
                "hint": f"思考{topic}的实践方法",
                "explanation": f"实际应用需要考虑{topic}的原理",
            },
            {
                "question": f"{topic}与其他相关概念有何不同？",
                "options": ["区别 A", "区别 B", "区别 C", "区别 D"],
                "hint": f"比较{topic}与类似概念",
                "explanation": f"理解这个区别有助于掌握{topic}",
            },
        ]
        items: List[QuizItem] = []
        for i in range(count):
            src = base[i % len(base)]
            items.append(
                QuizItem(
                    id=i + 1,
                    question=src["question"],
                    options=src["options"],
                    correct=1,
                    hint=src["hint"],
                    explanation=src["explanation"],
                )
            )
        return items
