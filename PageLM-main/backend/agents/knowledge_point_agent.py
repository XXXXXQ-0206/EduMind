"""
Knowledge Point Agent
从错题中提取细化的薄弱知识点，使用 LLM 分析实际题目内容。
"""
import json
from typing import Any, Dict, List, Optional

from agents.base import LLMAgent, AgentInput, AgentOutput


class KnowledgePointInput(AgentInput):
    wrong_questions: List[Dict[str, Any]]


class KnowledgePointOutput(AgentOutput):
    points: Optional[List[Dict[str, Any]]] = None


class KnowledgePointAgent(LLMAgent):
    def __init__(self):
        system_prompt = """
你是一位资深教育诊断专家，擅长从学生的错题中提炼出精确、具体、可操作的薄弱知识点。

## 任务
根据提供的错题列表（包含题目文本、正确答案、学生答案和解析），分析并输出结构化的薄弱知识点列表。

## 分析要求
1. 知识点粒度要细：不要写"数学基础"这种笼统表述，要细化到如"一元二次方程的判别式应用""牛顿第二定律中合力方向的判断""DNA双螺旋结构中碱基互补配对规则"这样的具体知识点。
2. 每个知识点都必须能对应到至少一道错题。
3. 相似的错题应归纳到同一个知识点下。
4. 针对每个知识点给出具体的、有指导意义的复习建议（不要泛泛而谈）。
5. 最多输出 8 个知识点，按严重程度从高到低排序。

## 输出格式
返回一个 JSON 数组，每个元素的结构如下：
[
  {
    "name": "具体知识点名称（如：一元二次方程求根公式的应用）",
    "category": "学科 · 章节（如：数学 · 二次方程）",
    "severity": "high | medium | low",
    "wrongCount": 出错题数,
    "description": "对这个知识点薄弱表现的简要描述（1-2句）",
    "suggestion": "针对性的具体复习建议（2-3句，要有可操作性）",
    "questionIndices": [对应的题目序号, 从0开始]
  }
]

## 严格约束
- 仅返回 JSON 数组，不要包含任何其他文字、Markdown 标记或代码围栏。
- 使用中文输出。
- severity 判定：同一知识点出错 ≥3 题为 high，2 题为 medium，1 题为 low。
- 如果错题量很少（≤3 题），仍然要尽可能细化知识点。
""".strip()

        super().__init__("knowledge_point_agent", system_prompt)
        self.description = "Extract specific weak knowledge points from wrong questions"

    async def execute(self, input_data: KnowledgePointInput) -> KnowledgePointOutput:
        try:
            questions = input_data.wrong_questions or []
            if not questions:
                return KnowledgePointOutput(success=True, points=[])

            # 构造精简的题目信息，避免 token 过多
            compact = []
            for idx, q in enumerate(questions[:50]):  # 限制最多 50 题
                entry = {
                    "idx": idx,
                    "question": (q.get("title") or q.get("question") or "")[:300],
                    "options": q.get("options", []),
                    "correctAnswer": q.get("correctOption") or q.get("note") or "",
                    "studentAnswer": q.get("selectedOption") or "",
                    "explanation": (q.get("explanation") or "")[:200],
                    "hint": (q.get("hint") or "")[:100],
                    "subject": q.get("subject") or q.get("topic") or "",
                }
                compact.append(entry)

            user_message = (
                f"以下是学生的 {len(compact)} 道错题，请分析并提取具体薄弱知识点：\n\n"
                + json.dumps(compact, ensure_ascii=False, indent=None)
                + "\n\n请返回 JSON 数组。"
            )

            response = await self.call_llm(user_message, expect_json=True)
            data = self.safe_parse_json(response)

            if isinstance(data, list) and len(data) > 0:
                # 验证结构
                validated = []
                for item in data[:8]:
                    if not isinstance(item, dict) or not item.get("name"):
                        continue
                    validated.append({
                        "name": str(item.get("name", "")),
                        "category": str(item.get("category", "")),
                        "severity": str(item.get("severity", "medium")),
                        "wrongCount": int(item.get("wrongCount", 1)),
                        "description": str(item.get("description", "")),
                        "suggestion": str(item.get("suggestion", "")),
                        "questionIndices": item.get("questionIndices", []),
                    })
                return KnowledgePointOutput(success=True, data={"points": validated}, points=validated)

            # LLM 返回格式不符，使用退化逻辑
            fallback = self._fallback_extract(questions)
            return KnowledgePointOutput(success=True, data={"points": fallback}, points=fallback)

        except Exception as e:
            fallback = self._fallback_extract(input_data.wrong_questions or [])
            return KnowledgePointOutput(success=False, error=str(e), points=fallback)

    def _fallback_extract(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """LLM 不可用时的退化逻辑：按 subject 分组"""
        from collections import defaultdict
        groups: Dict[str, List[int]] = defaultdict(list)
        for idx, q in enumerate(questions):
            subject = q.get("subject") or q.get("topic") or "未分类"
            groups[subject].append(idx)

        points = []
        for name, indices in sorted(groups.items(), key=lambda x: -len(x[1])):
            count = len(indices)
            severity = "high" if count >= 3 else "medium" if count >= 2 else "low"
            points.append({
                "name": f"{name} 相关知识",
                "category": name,
                "severity": severity,
                "wrongCount": count,
                "description": f"在 {name} 相关题目中出现 {count} 次错误。",
                "suggestion": "建议回顾该主题的核心概念并完成同类练习。",
                "questionIndices": indices[:10],
            })

        return points[:8]
