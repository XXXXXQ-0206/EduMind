"""
English speaking content generator agent.
Generates words, phrases, or sentences for speaking practice.
"""
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class SpeakingInput(AgentInput):
    """Speaking content generation input."""
    count: int = 5
    difficulty: str = "easy"
    item_type: str = "word"  # word | phrase | sentence
    topic: Optional[str] = None


class SpeakingItem(BaseModel):
    """Single speaking practice item."""
    id: int
    text: str
    translation: str
    phonetic: str
    level: str
    tag: str


class SpeakingOutput(AgentOutput):
    """Speaking content generation output."""
    items: Optional[List[SpeakingItem]] = None


class SpeakingAgent(LLMAgent):
    """Generate English speaking practice items."""

    def __init__(self):
        system_prompt = """
ROLE
You are an English speaking practice content generator.

OBJECTIVE
Generate exactly {count} items for the requested type and difficulty.

OUTPUT
Return ONLY a JSON array. No markdown, no code fences, no extra text.

SCHEMA (array items)
{{
    "id": 1..{count},
    "text": string,
    "translation": Chinese translation,
    "phonetic": ASCII-only pronunciation guide (no IPA symbols),
    "level": "easy" | "medium" | "hard",
    "tag": short label in Chinese (e.g. "高频词", "场景短语", "课堂表达")
}}

RULES
- item_type=word: single word, no spaces or punctuation.
- item_type=phrase: 2-4 words.
- item_type=sentence: 6-14 words, full sentence with punctuation.
- Use plain ASCII letters for phonetic; no IPA characters.
- Keep items distinct and non-overlapping.
- Use the provided difficulty level.
""".strip()

        super().__init__("speaking_agent", system_prompt)
        self.description = "Generate English speaking practice items with translations"

    async def execute(self, input_data: SpeakingInput) -> SpeakingOutput:
        try:
            items = await self._generate_items(input_data)
            return SpeakingOutput(success=True, data={"items": items}, items=items)
        except Exception as exc:
            return SpeakingOutput(success=False, error=str(exc), items=None)

    async def _generate_items(self, input_data: SpeakingInput) -> List[SpeakingItem]:
        count = self._normalize_count(input_data.count)
        difficulty = self._normalize_level(input_data.difficulty)
        item_type = self._normalize_type(input_data.item_type)
        topic = (input_data.topic or "").strip()

        system_prompt = self.system_prompt.format(count=count)
        user_prompt = (
            f"type: {item_type}\n"
            f"difficulty: {difficulty}\n"
            f"topic: {topic or 'general English'}\n"
            f"count: {count}\n"
            "Return only the JSON array."
        )

        response = await self.call_llm(user_prompt, system_prompt=system_prompt, expect_json=True)
        items = self._parse_items(response, count, difficulty, item_type)

        if len(items) == count:
            return items

        retry_prompt = (
            "Return only a JSON array with the exact schema. "
            "No markdown. No placeholders. ASCII phonetic only."
        )
        response2 = await self.call_llm(user_prompt, system_prompt=retry_prompt, expect_json=True)
        items2 = self._parse_items(response2, count, difficulty, item_type)

        if len(items2) == count:
            return items2

        return self._fallback_items(count, difficulty, item_type)

    def _normalize_count(self, count: int) -> int:
        if isinstance(count, int) and count > 0:
            return min(max(count, 1), 20)
        return 5

    def _normalize_level(self, level: str) -> str:
        key = (level or "easy").lower()
        if key in {"easy", "medium", "hard"}:
            return key
        return "easy"

    def _normalize_type(self, item_type: str) -> str:
        key = (item_type or "word").lower()
        if key in {"word", "phrase", "sentence"}:
            return key
        return "word"

    def _parse_items(
        self, response: str, count: int, level: str, item_type: str
    ) -> List[SpeakingItem]:
        if not response:
            return []

        cleaned = response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
        match = re.search(r"\[[\s\S]*\]", cleaned)
        if match:
            cleaned = match.group(0)

        try:
            raw = json.loads(cleaned)
        except json.JSONDecodeError:
            raw = []

        if not isinstance(raw, list):
            return []

        items: List[SpeakingItem] = []
        for idx, item in enumerate(raw[:count]):
            if not isinstance(item, dict):
                continue
            text = self._clean_text(item.get("text"))
            translation = self._clean_text(item.get("translation"))
            phonetic = self._clean_text(item.get("phonetic"))
            tag = self._clean_text(item.get("tag"))
            level_value = self._clean_text(item.get("level")) or level

            if not text:
                continue

            item_id = idx + 1
            items.append(
                SpeakingItem(
                    id=item_id,
                    text=text,
                    translation=translation or "",
                    phonetic=phonetic or self._fallback_phonetic(text),
                    level=level_value or level,
                    tag=tag or self._default_tag(item_type),
                )
            )

        while len(items) < count:
            next_id = len(items) + 1
            fallback = self._fallback_items(1, level, item_type)[0]
            items.append(
                SpeakingItem(
                    id=next_id,
                    text=fallback.text,
                    translation=fallback.translation,
                    phonetic=fallback.phonetic,
                    level=fallback.level,
                    tag=fallback.tag,
                )
            )

        return items[:count]

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return re.sub(r"\s+", " ", text)

    def _fallback_phonetic(self, text: str) -> str:
        return f"/{text.lower()}".strip() + "/"

    def _default_tag(self, item_type: str) -> str:
        if item_type == "phrase":
            return "场景短语"
        if item_type == "sentence":
            return "课堂表达"
        return "高频词"

    def _fallback_items(self, count: int, level: str, item_type: str) -> List[SpeakingItem]:
        words = ["adapt", "focus", "confirm", "predict", "summarize"]
        phrases = ["on time", "take notes", "look forward", "in advance", "keep calm"]
        sentences = [
            "I would like to ask a question.",
            "Could you please repeat that?",
            "We need to review the key points today.",
            "She explained the topic with clear examples.",
            "The data suggests a significant trend.",
        ]

        source = words if item_type == "word" else phrases if item_type == "phrase" else sentences
        items: List[SpeakingItem] = []
        for i in range(count):
            text = source[i % len(source)]
            items.append(
                SpeakingItem(
                    id=i + 1,
                    text=text,
                    translation="",
                    phonetic=self._fallback_phonetic(text),
                    level=level,
                    tag=self._default_tag(item_type),
                )
            )
        return items
