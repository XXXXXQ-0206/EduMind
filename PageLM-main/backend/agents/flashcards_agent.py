"""
Knowledge Cards Agent
Generates structured knowledge cards with hint, mnemonic, and application.
"""
import json
import re
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agents.base import LLMAgent, AgentInput, AgentOutput


class KnowledgeCardsInput(AgentInput):
    topic: str
    count: int = 5
    deck_id: Optional[str] = None


class KnowledgeCard(BaseModel):
    id: str
    concept: str
    question: str
    fill_blank: Optional[str] = None
    hint: str
    answer: str
    mnemonic: str
    application: str


class KnowledgeCardsOutput(AgentOutput):
    cards: Optional[List[KnowledgeCard]] = None


class KnowledgeCardsAgent(LLMAgent):
    def __init__(self):
        system_prompt = """
PRIMARY OBJECTIVE
Generate exactly N high-quality knowledge cards about the topic.

OUTPUT CONTRACT
Return only one valid JSON object:
{
    "cards": [
        {
            "concept": "string",
            "question": "string",
            "fill_blank": "string (optional)",
            "hint": "string",
            "answer": "string",
            "mnemonic": "string",
            "application": "string"
        }
    ]
}
No markdown, no code fences, no extra text.

CONTENT RULES
- Each card targets a DIFFERENT subtopic, definition, theorem, formula, case, or mechanism.
- The front is recall-focused: a clear question or a fill-in-the-blank.
- The back MUST directly answer that specific question with specific facts.
- Use diverse question styles (definition, components, process, comparison, boundary conditions, scenario judgment).
- Hint is helpful but does not reveal the answer.
- Mnemonic must be meaningfully linked to the concept and include at least one key term from the answer.
- Application is a concrete scenario or exam-style usage tied to the same concept and question.
- Hint/answer/mnemonic/application must be unique per card (no repeats).
- Use the same language as the topic (Chinese topic -> Chinese output).
- Avoid generic filler or template-like text such as placeholders.
""".strip()

        super().__init__("knowledge_cards_agent", system_prompt)
        self.description = "Generate knowledge cards with hints and mnemonics"

    async def execute(self, input_data: KnowledgeCardsInput) -> KnowledgeCardsOutput:
        try:
            cards = await self._generate_cards(input_data.topic, input_data.count)
            return KnowledgeCardsOutput(
                success=True,
                data={"cards": [c.dict() for c in cards]},
                cards=cards,
            )
        except Exception as e:
            return KnowledgeCardsOutput(success=False, error=str(e), cards=None)

    async def _generate_cards(self, topic: str, count: int) -> List[KnowledgeCard]:
        count = max(1, min(int(count or 5), 15))
        language_hint = "Chinese" if self._has_cjk(topic) else "English"
        user_message = (
            f"topic: {topic}\n"
            f"language: {language_hint}\n"
            f"count: {count}\n\n"
            "IMPORTANT:\n"
            "- Each card must cover a DIFFERENT knowledge point or subtopic.\n"
            "- Questions must be diverse in style and not just rephrases.\n"
            "- No duplicates, no paraphrases, no repeated concepts.\n"
            "- Hint/answer/mnemonic/application must be specific to each card and not repeated.\n"
            "- The answer must be a correct, direct response to the question.\n"
            "- Mnemonic and application must be clearly related to the same concept.\n"
            "- Keep all cards strictly on-topic.\n\n"
            "return only json"
        )

        response = await self.call_llm(user_message, expect_json=True)
        data = self._parse_cards_response(response)

        if language_hint == "Chinese" and not self._cards_have_cjk(data):
            strict_prompt = "Return only JSON. All content must be Chinese."
            response_cn = await self.call_llm(user_message, system_prompt=strict_prompt, expect_json=True)
            data = self._parse_cards_response(response_cn) or data

        cards_raw = data.get("cards") if isinstance(data, dict) else []
        if not isinstance(cards_raw, list) or not cards_raw:
            strict_format_prompt = """
RETURN ONLY JSON
Output one JSON object with key 'cards' only.
Each card must include: concept, question, hint, answer, mnemonic, application.
No markdown, no extra text.
""".strip()
            response_format = await self.call_llm(
                user_message,
                system_prompt=strict_format_prompt,
                expect_json=True,
            )
            data_format = self._parse_cards_response(response_format)
            cards_raw = data_format.get("cards") if isinstance(data_format, dict) else []
            if not isinstance(cards_raw, list) or not cards_raw:
                return self._fallback_cards(topic, count)

        cards: List[KnowledgeCard] = []
        for item in cards_raw[:count]:
            if not isinstance(item, dict):
                continue
            card = KnowledgeCard(
                id=str(uuid.uuid4()),
                concept=str(item.get("concept") or topic)[:80],
                question=str(item.get("question") or "")[:300],
                fill_blank=str(item.get("fill_blank") or "")[:300] or None,
                hint=str(item.get("hint") or "")[:200],
                answer=str(item.get("answer") or "")[:800],
                mnemonic=str(item.get("mnemonic") or "")[:200],
                application=str(item.get("application") or "")[:300],
            )
            cards.append(card)

        if self._cards_quality_ok(cards, count):
            return self._dedupe_cards(cards)

        strict_prompt = """
RETRY: STRICT QUALITY
Output only the JSON object with key 'cards'.
    Each card must have a specific question, a complete answer, a linked mnemonic, and a concrete application example.
    Avoid placeholders like "要点包括..." or "考试常考点". Do NOT use template phrases such as "参考答案" or "记忆法".
    Answers should be 1-3 concise sentences with specific facts.
    Mnemonic must include a key term from the answer.
""".strip()
        response2 = await self.call_llm(user_message, system_prompt=strict_prompt, expect_json=True)
        data2 = self._parse_cards_response(response2)
        cards_raw2 = data2.get("cards") if isinstance(data2, dict) else []
        cards2: List[KnowledgeCard] = []
        for item in cards_raw2[:count]:
            if not isinstance(item, dict):
                continue
            cards2.append(
                KnowledgeCard(
                    id=str(uuid.uuid4()),
                    concept=str(item.get("concept") or topic)[:80],
                    question=str(item.get("question") or "")[:300],
                    fill_blank=str(item.get("fill_blank") or "")[:300] or None,
                    hint=str(item.get("hint") or "")[:200],
                    answer=str(item.get("answer") or "")[:800],
                    mnemonic=str(item.get("mnemonic") or "")[:200],
                    application=str(item.get("application") or "")[:300],
                )
            )
        if self._cards_quality_ok(cards2, count):
            return self._dedupe_cards(cards2)

        cards = self._dedupe_cards(cards)
        if len(cards) < count:
            cards = self._pad_cards(cards, topic, count)
        return cards

    def _parse_cards_response(self, response: str) -> Dict[str, Any]:
        if not response:
            return {}
        data = self.safe_parse_json(response)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"cards": data}
        extracted = self._extract_json_object(response)
        if extracted:
            try:
                parsed = json.loads(extracted)
                if isinstance(parsed, dict):
                    return parsed
                if isinstance(parsed, list):
                    return {"cards": parsed}
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

    def _has_cjk(self, text: str) -> bool:
        for ch in text:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def _cards_have_cjk(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        cards = data.get("cards") or []
        for item in cards:
            if self._has_cjk(str(item)):
                return True
        return False

    def _cards_quality_ok(self, cards: List[KnowledgeCard], count: int) -> bool:
        if not isinstance(cards, list) or len(cards) < count:
            return False
        return all(self._card_quality(card) for card in cards[:count])

    def _card_quality(self, card: KnowledgeCard) -> bool:
        if not (card.question or card.fill_blank):
            return False
        if not card.answer or len(card.answer.strip()) < 8:
            return False
        if self._looks_generic(card.answer):
            return False
        if self._looks_generic(card.mnemonic):
            return False
        if self._looks_generic(card.application):
            return False
        if self._answer_too_close_to_question(card.question or "", card.answer or ""):
            return False
        return True

    def _looks_generic(self, text: str) -> bool:
        plain = (text or "").strip()
        if not plain:
            return True
        generic_phrases = [
            "要点包括",
            "要点如下",
            "参考答案",
            "答案要点",
            "可结合",
            "考试常考点",
            "常见题型",
            "记忆法",
            "应用案例",
            "...",
        ]
        return any(phrase in plain for phrase in generic_phrases)

    def _answer_too_close_to_question(self, question: str, answer: str) -> bool:
        q = re.sub(r"\s+", " ", question or "").strip()
        a = re.sub(r"\s+", " ", answer or "").strip()
        if not q or not a:
            return True
        if a in q and len(a) <= len(q) + 10:
            return True
        if q in a and len(a) <= len(q) + 10:
            return True
        return False

    def _fallback_cards(self, topic: str, count: int) -> List[KnowledgeCard]:
        cards: List[KnowledgeCard] = []
        templates = [
            "请说明 {topic} 的核心概念。",
            "{topic} 的关键要素有哪些？",
            "{topic} 常见的错误理解是什么？",
            "{topic} 在实际问题中如何应用？",
            "{topic} 与相近概念的区别是什么？",
        ]
        hint_templates = [
            "回忆定义中的关键词与核心目标。",
            "想一想组成结构、条件或步骤。",
            "关注常见陷阱与容易混淆的点。",
            "联想到典型题型或生活场景。",
            "对比相似概念的边界与差异。",
        ]
        mnemonic_templates = [
            "联想：用关键词构建小场景帮助记忆。",
            "联想：把概念拆成步骤并串成故事。",
            "联想：用对比词强化概念边界。",
            "联想：给关键项编排节奏或押韵。",
            "联想：用自问自答巩固关键点。",
        ]
        application_templates = [
            "应用：判断给定案例是否满足定义条件。",
            "应用：依据题干要素进行推断或选择。",
            "应用：结合场景解释适用范围或限制。",
            "应用：与相近概念进行对比并下结论。",
            "应用：识别常见误区并给出纠正理由。",
        ]
        for i in range(count):
            cards.append(
                KnowledgeCard(
                    id=str(uuid.uuid4()),
                    concept=topic[:50],
                    question=templates[i % len(templates)].format(topic=topic),
                    fill_blank=None,
                    hint=hint_templates[i % len(hint_templates)],
                    answer=f"答案：围绕{topic}的定义、组成与边界进行概括说明。",
                    mnemonic=mnemonic_templates[i % len(mnemonic_templates)],
                    application=application_templates[i % len(application_templates)],
                )
            )
        return cards

    def _pad_cards(self, cards: List[KnowledgeCard], topic: str, target: int) -> List[KnowledgeCard]:
        padded = list(cards)
        seed = len(padded)
        while len(padded) < target:
            padded.extend(self._fallback_cards(f"{topic} · 补充 {seed + 1}", 1))
            seed += 1
        return self._dedupe_cards(padded)

    def _dedupe_cards(self, cards: List[KnowledgeCard]) -> List[KnowledgeCard]:
        seen = set()
        unique: List[KnowledgeCard] = []
        for card in cards:
            key = (card.concept.strip().lower(), (card.question or "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(card)
        return unique
