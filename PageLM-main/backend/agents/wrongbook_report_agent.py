"""
Wrong Book Report Agent
深度分析每道错题的具体知识点薄弱环节，生成针对性的提升报告。
"""
import json
from typing import Any, Dict, List, Optional

from agents.base import LLMAgent, AgentInput, AgentOutput


class WrongBookReportInput(AgentInput):
    summary: Dict[str, Any]


class WrongBookReportOutput(AgentOutput):
    report: Optional[Dict[str, Any]] = None


class WrongBookReportAgent(LLMAgent):
    def __init__(self):
        system_prompt = """
你是一位资深教育诊断专家，擅长通过分析学生的错题来发现深层知识漏洞，并提出精准、可操作的提升方案。

## 任务
根据提供的错题数据（包含每道题的题目文本、正确答案、学生错选答案、解析等信息），生成一份深度分析提升报告。

## 分析要求
1. **逐题或逐类分析**：不要只看统计数字，要阅读每道错题的实际内容，找出学生错在哪个知识点、哪个思维环节。
2. **知识点要具体**：不要写"数学基础薄弱"这种笼统表述。要具体到如"二次函数顶点坐标公式记忆混淆""电路串并联中电阻计算规则混淆""英语虚拟语气中 if 从句时态搭配错误"等。
3. **错因归类**：将错误归为具体原因（概念混淆、公式记错、审题不清、计算失误、方法选择错误等），并给出每类的具体例证。
4. **提升措施要可操作**：不要说"多做题"，要说"重点练习XX类型的题，建议先回顾XX定理/概念，再完成3-5道同类变式题"。
5. **优先级排序**：按严重程度排列薄弱点，最需要优先解决的放前面。

## 输出格式
返回一个 JSON 对象：
{
  "overview": "总体诊断概述（2-3句，概括主要问题和总体方向）",
  "highlights": [
    {"title": "最关键的薄弱知识点名称", "desc": "具体说明这个知识点错在哪里，涉及哪些题目，错误模式是什么"},
    {"title": "第二关键薄弱点", "desc": "..."},
    {"title": "第三关键薄弱点", "desc": "..."}
  ],
  "strengths": ["基于正确题目分析出的优势领域（要具体）"],
  "weaknesses": ["细化到具体知识点的薄弱描述，每条要包含：知识点名称 + 错误表现 + 涉及题数"],
  "actions": [
    "针对每个薄弱知识点的具体改进步骤（包含：复习什么内容 + 练习什么题型 + 达到什么标准）"
  ],
  "weeklyPlan": [
    "按天安排的具体复习计划，每天要写清楚做什么、练什么、目标是什么"
  ],
  "metrics": {
    "currentAccuracy": 当前正确率数值,
    "targetAccuracy": 目标正确率数值,
    "reviewIntervalDays": 建议复习间隔天数
  }
}

## 严格约束
- 仅返回 JSON，不要包含 Markdown 标记或代码围栏。
- highlights 固定 3 条，按严重程度排序。
- weaknesses 至少 3 条，每条要具体到知识点。
- actions 至少 4 条，每条都要有可操作性。
- weeklyPlan 要覆盖完整一周（7 天）。
- 全部使用中文。
""".strip()

        super().__init__("wrongbook_report_agent", system_prompt)
        self.description = "Generate in-depth wrong-book analytics report with per-question analysis"

    def _build_question_detail(self, summary: Dict[str, Any]) -> str:
        """构造精简的逐题错误详情供 LLM 分析"""
        wrong_qs = summary.get("wrongQuestions") or []
        lines = []
        for idx, q in enumerate(wrong_qs[:40]):  # 限制 40 题避免 token 过多
            lines.append(
                f"[错题{idx+1}] 题目: {(q.get('title') or '')[:200]}\n"
                f"  学科/来源: {q.get('subject') or '未知'}\n"
                f"  正确答案解析: {(q.get('note') or q.get('explanation') or '')[:150]}\n"
                f"  难度: {q.get('level') or '未知'}\n"
                f"  提示: {(q.get('hint') or '')[:100]}"
            )
        return "\n".join(lines)

    async def execute(self, input_data: WrongBookReportInput) -> WrongBookReportOutput:
        try:
            summary = input_data.summary or {}
            stats = summary.get("stats") or {}

            # 构造包含逐题详情的 prompt
            question_detail = self._build_question_detail(summary)
            wrong_count = stats.get("wrongCount", 0)
            mastered_count = stats.get("masteredCount", 0)
            mastery_rate = stats.get("masteryRate", 0)

            user_message = (
                f"## 错题统计概览\n"
                f"- 错题总数: {wrong_count}\n"
                f"- 已掌握题数: {mastered_count}\n"
                f"- 当前正确率: {mastery_rate}%\n"
                f"- 复习间隔: {stats.get('reviewIntervalDays', 0)} 天\n\n"
                f"## 错题详情（共 {wrong_count} 道）\n"
                f"{question_detail}\n\n"
                f"请深入分析每道错题的具体知识点薄弱环节，找出错误模式和共性问题，"
                f"然后生成结构化的提升报告。返回 JSON。"
            )

            response = await self.call_llm(user_message, expect_json=True)
            data = self.safe_parse_json(response)
            if isinstance(data, dict) and data.get("highlights"):
                # 确保 metrics 完整
                metrics = data.get("metrics") or {}
                if not metrics.get("currentAccuracy"):
                    metrics["currentAccuracy"] = mastery_rate
                if not metrics.get("targetAccuracy"):
                    metrics["targetAccuracy"] = min(95, mastery_rate + 15)
                if not metrics.get("reviewIntervalDays"):
                    metrics["reviewIntervalDays"] = round(float(stats.get("reviewIntervalDays") or 2.0), 1)
                data["metrics"] = metrics
                return WrongBookReportOutput(success=True, data=data, report=data)

            fallback = self._fallback_report(summary)
            return WrongBookReportOutput(success=True, data=fallback, report=fallback)
        except Exception as e:
            fallback = self._fallback_report(input_data.summary or {})
            return WrongBookReportOutput(success=False, error=str(e), report=fallback)

    def _fallback_report(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        stats = summary.get("stats") or {}
        wrong_qs = summary.get("wrongQuestions") or []
        mastery_rate = int(stats.get("masteryRate") or 0)
        review_interval = float(stats.get("reviewIntervalDays") or 0)

        # 尝试从错题内容中提取代表性题目
        sample_titles = [q.get("title", "")[:50] for q in wrong_qs[:3]]
        sample_desc = "、".join([t for t in sample_titles if t]) or "当前课程相关题目"

        highlights = [
            {"title": "高频错误知识点", "desc": f"在以下题目中反复出错：{sample_desc}。建议逐题回顾解析，找出共性薄弱点。"},
            {"title": "错因分析", "desc": "常见错因包括概念混淆、公式记忆不准确或审题不够仔细，建议针对性地强化基础概念。"},
            {"title": "提升路径", "desc": "优先攻克出错频率最高的知识点模块，达到 80% 以上正确率后再扩展难度。"},
        ]

        weaknesses = []
        subjects = {}
        for q in wrong_qs:
            subj = q.get("subject") or "未分类"
            subjects[subj] = subjects.get(subj, 0) + 1
        for subj, cnt in sorted(subjects.items(), key=lambda x: -x[1]):
            weaknesses.append(f"{subj} 模块出现 {cnt} 道错题，需要重点复习该主题下的核心概念和典型题型。")
        if not weaknesses:
            weaknesses = ["暂无足够数据做细分分析，建议积累更多题目后重新生成。"]

        return {
            "overview": f"共有 {len(wrong_qs)} 道错题待攻克，当前正确率 {mastery_rate}%。建议优先集中复习高频错误知识点，结合变式练习巩固。",
            "highlights": highlights,
            "strengths": [f"已掌握 {stats.get('masteredCount', 0)} 道题目。" if mastery_rate >= 50 else "正在建立知识体系，继续保持。"],
            "weaknesses": weaknesses[:5],
            "actions": [
                "逐题回顾错题解析，标注每道题的具体错因（概念混淆/计算失误/审题不清）。",
                "针对出错最多的知识点，回顾教材对应章节的核心概念和公式。",
                "完成 3-5 道同类变式题，验证是否已掌握该知识点。",
                "将仍未掌握的题目加入下一轮复习队列，间隔 2-3 天再次练习。",
            ],
            "weeklyPlan": [
                "周一：回顾本周最高频的 3 个错误知识点，精读解析",
                "周二：针对周一的薄弱点完成变式练习（每个知识点 3 题）",
                "周三：复习其余错题，分类整理错因",
                "周四：对已整理的错题做二刷，检验掌握情况",
                "周五：综合练习，覆盖本周所有薄弱知识点",
                "周六：模拟测验，评估整体提升效果",
                "周日：总结本周复习情况，规划下周重点",
            ],
            "metrics": {
                "currentAccuracy": mastery_rate,
                "targetAccuracy": min(95, mastery_rate + 15),
                "reviewIntervalDays": round(review_interval or 2.0, 1),
            },
        }
