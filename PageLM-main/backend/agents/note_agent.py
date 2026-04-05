"""
智能笔记生成 Agent
使用康奈尔笔记法生成结构化笔记
"""
import asyncio
import re
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class NoteInput(AgentInput):
    """笔记生成输入"""
    topic: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    length: Optional[str] = None


class NoteOutput(AgentOutput):
    """笔记生成输出"""
    file_path: Optional[str] = None


class NoteAgent(LLMAgent):
    """
    智能笔记生成 Agent
    将文本或主题转换为康奈尔风格的结构化笔记
    """

    def __init__(self):
        system_prompt = """
ROLE
You are a note generator producing Cornell-style notes.

OBJECTIVE
Generate study notes at the requested length (rough, medium, detailed) while staying concise.

OUTPUT
Return ONLY a valid JSON object, no markdown, no prose.

SCHEMA
{
  "title": string,
  "notes": string,
  "summary": string,
  "questions": string[],
  "answers": string[]
}

RULES
- Do not wrap with code fences.
- Do not add commentary.
- Use plain text only.
- If a field has no content, return "" or [].
- For each question, the corresponding answer must be in the same index in answers.

LENGTH GUIDE
- rough: 8-12 short lines for notes, 2-3 lines summary, 3 questions max.
- medium: 12-18 short lines for notes, 3-5 lines summary, 5 questions max.
- detailed: 18-26 short lines for notes, 5-7 lines summary, 7 questions max.
- Keep each line concise. Avoid long paragraphs.
""".strip()

        super().__init__("note_agent", system_prompt)
        self.description = "Generate Cornell-style structured notes from text or topics"

    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """执行笔记生成"""
        try:
            # 1. 获取输入文本
            input_text = await self._read_input(input_data)

            # 2. 调用 LLM 生成笔记
            notes_data = await self._generate_notes(input_text, input_data)

            # 3. 生成 PDF
            pdf_path = await self._create_pdf(notes_data)

            return NoteOutput(
                success=True,
                data={"file_path": pdf_path, "notes": notes_data},
                file_path=pdf_path,
            )

        except Exception as e:
            return NoteOutput(
                success=False, error=str(e), file_path=None
            )

    async def _read_input(self, input_data: NoteInput) -> str:
        """读取输入文本"""
        base_text = ""
        if input_data.notes:
            base_text = input_data.notes
        elif input_data.file_path:
            path = Path(input_data.file_path)
            if path.exists():
                base_text = path.read_text(encoding="utf-8")
        elif input_data.topic:
            base_text = input_data.topic
        else:
            raise ValueError("No valid input provided (topic, notes, or file_path required)")

        return base_text

    async def _generate_notes(self, text: str, input_data: NoteInput) -> Dict[str, Any]:
        """使用 LLM 生成笔记"""
        length = (input_data.length or "medium").lower()
        length_hint = {
            "rough": "rough",
            "short": "rough",
            "brief": "rough",
            "medium": "medium",
            "detailed": "detailed",
            "long": "detailed",
        }.get(length, "medium")
        language_hint = "Chinese" if self._has_cjk(text) else "English"
        user_prompt = (
            "CONTENT:\n"
            f"{text}\n\n"
            "TASK:\nGenerate Cornell-style notes as JSON only.\n"
            f"Language: {language_hint}.\n"
            f"Length: {length_hint}. Follow LENGTH GUIDE.\n\n"
            "Return ONLY the JSON object matching the schema."
        )

        # 第一次尝试
        response = await self.call_llm(user_prompt, expect_json=True)
        data = self._parse_notes_response(response)

        if self._is_valid_notes(data):
            return data

        # 第二次尝试：更严格的提示
        retry_prompt = (
            "Return only a JSON object matching the schema. "
            "No markdown. No extra text. Use plain text."
        )
        response2 = await self.call_llm(user_prompt, system_prompt=retry_prompt, expect_json=True)
        data2 = self._parse_notes_response(response2)

        if self._is_valid_notes(data2):
            return data2

        # 第三次尝试：纯文本笔记，再回填为 JSON
        text_prompt = (
            f"Topic: {text}\n"
            f"Language: {language_hint}.\n"
            f"Length: {length_hint}.\n"
            "Write Cornell-style notes with clear sections and bullet points."
        )
        response3 = await self.call_llm(text_prompt, expect_json=False)
        if response3 and response3.strip():
            parsed3 = self._parse_notes_response(response3)
            if self._is_valid_notes(parsed3):
                return parsed3
            return {
                "title": input_data.topic or "Notes",
                "notes": response3.strip(),
                "summary": "",
                "questions": [],
                "answers": [],
            }

        # 回退：使用原始文本
        return {
            "title": input_data.topic or "Notes",
            "notes": self._sanitize_text(text)[:4000],
            "summary": "",
            "questions": [],
            "answers": [],
        }

    def _has_cjk(self, text: str) -> bool:
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def _parse_notes_response(self, response: str) -> Dict[str, Any]:
        if not response:
            return {}
        data = self.safe_parse_json(response)
        if isinstance(data, str):
            inner = data.strip()
            if inner.startswith("{") and inner.endswith("}"):
                try:
                    inner_data = json.loads(inner)
                    if isinstance(inner_data, dict):
                        return inner_data
                except Exception:
                    return {}
        if isinstance(data, dict):
            return data

        extracted = self._extract_json_object(response)
        if extracted:
            try:
                parsed = json.loads(extracted)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {}
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

    def _is_valid_notes(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        notes_text = str(data.get("notes") or "").strip()
        summary_text = str(data.get("summary") or "").strip()
        questions = data.get("questions") or []
        if notes_text:
            return True
        if summary_text:
            return True
        if isinstance(questions, list) and questions:
            return True
        return False

    def _sanitize_text(self, text: str) -> str:
        """清理文本，移除特殊字符"""
        if not text:
            return ""
        return (
            text.replace("\u2192", "->")
            .replace("\u00b2", "^2")
            .replace("\u00b3", "^3")
        )

    async def _create_pdf(self, data: Dict[str, Any]) -> str:
        """创建 PDF 笔记"""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from config import config

        # 创建输出目录
        output_dir = config.storage_dir / "smartnotes"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        safe_title = self._sanitize_text(data.get("title", "notes"))
        safe_title = re.sub(r"[^a-z0-9]", "_", safe_title.lower())[:50]
        if not safe_title.strip("_"):
            safe_title = "notes"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.pdf"
        file_path = output_dir / filename

        # 注册中文字体
        font_name = "Helvetica"
        font_candidates = [
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
            config.base_dir / "assets" / "fonts" / "NotoSans.ttf",
        ]
        for font_path in font_candidates:
            if font_path.exists():
                try:
                    font_name = "SimHei" if font_path.name.lower().startswith("simhei") else "CjkFont"
                    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                    break
                except Exception:
                    continue

        # 创建 PDF
        doc = SimpleDocTemplate(str(file_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # 标题
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=20,
            fontName=font_name,
            textColor="#000000",
            spaceAfter=30,
        )
        story.append(Paragraph(self._sanitize_text(data.get("title", "Notes")), title_style))
        story.append(Spacer(1, 0.2 * inch))

        # 笔记内容
        notes_style = ParagraphStyle(
            "CustomNotes",
            parent=styles["BodyText"],
            fontSize=11,
            fontName=font_name,
            leading=14,
        )
        notes_text = self._sanitize_text(data.get("notes", ""))
        notes_text = notes_text.replace("\n", "<br/>")
        story.append(Paragraph(notes_text, notes_style))
        story.append(Spacer(1, 0.3 * inch))

        # 总结
        if data.get("summary"):
            summary_style = ParagraphStyle(
                "SummaryHeading",
                parent=styles["Heading2"],
                fontName=font_name,
            )
            story.append(Paragraph("<b>总结</b>", summary_style))
            story.append(Spacer(1, 0.1 * inch))
            summary_text = self._sanitize_text(data.get("summary", ""))
            summary_text = summary_text.replace("\n", "<br/>")
            story.append(Paragraph(summary_text, notes_style))
            story.append(Spacer(1, 0.3 * inch))

        # 问题和答案
        questions = data.get("questions", [])
        answers = data.get("answers", [])
        if questions:
            qa_style = ParagraphStyle(
                "QaHeading",
                parent=styles["Heading2"],
                fontName=font_name,
            )
            story.append(Paragraph("<b>问题与答案</b>", qa_style))
            story.append(Spacer(1, 0.1 * inch))

            for i, (q, a) in enumerate(zip(questions, answers)):
                qa_text = f"• {self._sanitize_text(q)}"
                if a:
                    qa_text += f"<br/>答案：{self._sanitize_text(a)}"
                story.append(Paragraph(qa_text, notes_style))
                story.append(Spacer(1, 0.1 * inch))

        # 构建 PDF
        doc.build(story)

        return str(file_path)
