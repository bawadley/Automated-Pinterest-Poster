import hashlib
import json
import re
from difflib import SequenceMatcher

import requests


class AIContentGenerator:
    def __init__(self, config: dict):
        self.api_key = str(config.get("api_key", "")).strip()
        self.model = str(config.get("model", "gpt-6-luna")).strip()
        self.base_url = str(
            config.get("base_url", "https://api.openai.com/v1")
        ).rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _item_text(item: dict) -> str:
        if not item:
            return ""

        content = item.get("content")
        if isinstance(content, dict):
            source = content
        else:
            source = item

        parts = []
        for key in (
            "title",
            "headline",
            "body",
            "quote",
            "prompt",
            "subtext",
            "description",
        ):
            value = source.get(key)
            if value:
                parts.append(str(value))

        for key in ("bullets", "options"):
            values = source.get(key, [])
            if isinstance(values, list):
                parts.extend(str(value) for value in values if value)

        return " ".join(parts)

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.casefold()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return " ".join(text.split())

    def _too_similar(self, tip: dict, previous_items: list[dict]) -> bool:
        candidate = self._normalize(self._item_text(tip))
        if not candidate:
            return True

        candidate_words = set(candidate.split())

        for previous in previous_items:
            old = self._normalize(self._item_text(previous))
            if not old:
                continue

            ratio = SequenceMatcher(None, candidate, old).ratio()
            old_words = set(old.split())
            union = candidate_words | old_words
            overlap = (
                len(candidate_words & old_words) / len(union)
                if union
                else 0.0
            )

            if ratio >= 0.72 or overlap >= 0.62:
                return True

        return False

    @staticmethod
    def _schema():
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "headline": {"type": "string"},
                "body": {"type": "string"},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "quote": {"type": "string"},
                "prompt": {"type": "string"},
                "subtext": {"type": "string"},
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "answer": {"type": "string"},
                "cta": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": [
                "title",
                "headline",
                "body",
                "bullets",
                "quote",
                "prompt",
                "subtext",
                "options",
                "answer",
                "cta",
                "description",
            ],
        }

    def _history_prompt(self, previous_items: list[dict]) -> str:
        lines = []
        for item in previous_items[:100]:
            category = item.get("category", "")
            text = self._item_text(item)
            if not text:
                continue
            lines.append(f"- [{category}] {text[:650]}")

        if not lines:
            return "No previous posted content is available yet."

        return "\n".join(lines)

    def _instructions(self, category: dict) -> str:
        content_type = category.get("content_type", "tip")
        vertical = category.get("vertical", "")
        category_name = category.get("name", "")

        return f"""
You create one original Pinterest non-affiliate content card.

Vertical: {vertical}
Category: {category_name}
Content type: {content_type}

The card must be useful, natural, concise, and genuinely distinct from the
previously posted content supplied by the user.

Rules:
1. Do not reuse the same central idea, punchline, question, fact, framing, or
   wording as previous content.
2. Do not make close paraphrases of previous content.
3. Keep language conversational, not spammy or clickbait-heavy.
4. Do not mention AI, automation, affiliate links, or this prompt.
5. Avoid unsafe repair instructions. Keep motorcycle and 3D-printing advice
   conservative and appropriate for a general-interest Pinterest post.
6. For factual tips/quizzes, use broadly accepted facts. Avoid obscure exact
   specifications, model-year claims, or technical claims unless highly
   confident.
7. Keep the image text short enough for a 1000x1500 Pinterest graphic.
8. Return all schema fields. Fields not used by this content type must be empty
   strings or empty arrays.

Content-type requirements:
- tip: title, headline, body, exactly 3 short bullets, description.
- quote: title, quote, description. Make it light/humorous/relatable.
- question: title, prompt, subtext, CTA, description. Invite a genuine answer.
- quiz: title, prompt, exactly 3 options labeled A., B., C., answer, CTA,
  description. Exactly one option must be clearly correct. Do not reveal the
  answer in the description.

Maximum guidance:
- title <= 85 characters
- headline/prompt <= 115 characters
- quote <= 180 characters
- body <= 260 characters
- each bullet <= 80 characters
- subtext <= 140 characters
- CTA <= 35 characters
- description <= 500 characters
""".strip()

    @staticmethod
    def _extract_text(response_json: dict) -> str:
        for output in response_json.get("output", []):
            if output.get("type") != "message":
                continue
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        raise RuntimeError("OpenAI response did not contain output text.")

    @staticmethod
    def _clean_generated(data: dict, content_type: str) -> dict:
        result = {
            "title": str(data.get("title", "")).strip()[:100],
            "headline": str(data.get("headline", "")).strip(),
            "body": str(data.get("body", "")).strip(),
            "bullets": [
                str(value).strip()
                for value in data.get("bullets", [])
                if str(value).strip()
            ][:3],
            "quote": str(data.get("quote", "")).strip(),
            "prompt": str(data.get("prompt", "")).strip(),
            "subtext": str(data.get("subtext", "")).strip(),
            "options": [
                str(value).strip()
                for value in data.get("options", [])
                if str(value).strip()
            ][:3],
            "answer": str(data.get("answer", "")).strip(),
            "cta": str(data.get("cta", "")).strip(),
            "description": str(data.get("description", "")).strip()[:800],
        }

        required = {
            "tip": ["title", "headline", "body", "description"],
            "quote": ["title", "quote", "description"],
            "question": [
                "title",
                "prompt",
                "subtext",
                "cta",
                "description",
            ],
            "quiz": [
                "title",
                "prompt",
                "answer",
                "cta",
                "description",
            ],
        }.get(content_type, ["title", "headline", "body", "description"])

        missing = [key for key in required if not result.get(key)]
        if missing:
            raise RuntimeError(
                "AI response was missing required fields: "
                + ", ".join(missing)
            )

        if content_type == "tip" and len(result["bullets"]) != 3:
            raise RuntimeError("AI tip must contain exactly 3 bullets.")

        if content_type == "quiz" and len(result["options"]) != 3:
            raise RuntimeError("AI quiz must contain exactly 3 options.")

        return result

    def generate(
        self,
        category: dict,
        previous_items: list[dict],
        max_attempts: int = 3,
    ) -> dict:
        if not self.available:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        content_type = category.get("content_type", "tip")
        history_text = self._history_prompt(previous_items)

        for attempt in range(1, max_attempts + 1):
            prompt = f"""
Previously posted Pinterest content:
{history_text}

Generate one NEW {content_type} for:
- vertical: {category.get("vertical", "")}
- category: {category.get("name", "")}

This is generation attempt {attempt}. It must be meaningfully different from
every item above.
""".strip()

            response = requests.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "instructions": self._instructions(category),
                    "input": prompt,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "pinterest_content",
                            "strict": True,
                            "schema": self._schema(),
                        }
                    },
                },
                timeout=90,
            )

            if not response.ok:
                raise RuntimeError(
                    f"OpenAI API error {response.status_code}: "
                    f"{response.text[:500]}"
                )

            response_json = response.json()
            text = self._extract_text(response_json)

            try:
                generated = json.loads(text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "OpenAI returned invalid structured JSON."
                ) from exc

            tip = self._clean_generated(generated, content_type)
            fingerprint = self._normalize(self._item_text(tip))
            tip["id"] = (
                f"ai-{content_type}-"
                + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:14]
            )

            if not self._too_similar(tip, previous_items):
                return tip

        raise RuntimeError(
            "AI generated content that was too similar to previous posts "
            f"after {max_attempts} attempts."
        )
