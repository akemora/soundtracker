"""Deep research service using Perplexity for richer composer profiles."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

from soundtracker.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResearchSection:
    """Structured research section."""

    text: str
    citations: list[str]


@dataclass
class ResearchProfile:
    """Structured research profile."""

    biography: ResearchSection
    style: ResearchSection
    facts: ResearchSection


class ResearchService:
    """Deep research service that enriches composer profiles."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 20,
    ) -> None:
        self.api_key = api_key or settings.perplexity_key
        self.model = model or settings.pplx_model
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key) and settings.deep_research_enabled

    def get_profile(self, composer: str) -> Optional[ResearchProfile]:
        """Fetch deep research profile for a composer."""
        if not self.is_enabled:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un investigador musical. Responde SOLO con JSON válido. "
                        "Estructura: "
                        "{\"biography\": {\"text\": \"...\", \"citations\": [\"url\", ...]}, "
                        "\"style\": {\"text\": \"...\", \"citations\": [\"url\", ...]}, "
                        "\"facts\": {\"text\": \"...\", \"citations\": [\"url\", ...]}}. "
                        "Texto en español. "
                        "Biografía: 2-3 párrafos. "
                        "Estilo musical: 1-2 párrafos con técnicas de composición. "
                        "Datos curiosos: 2-4 frases/bullets sobre hábitos, métodos, excentricidades o rasgos humanos. "
                        "Incluye citas fiables por sección."
                    ),
                },
                {"role": "user", "content": f"Compositor: {composer}"},
            ],
            "max_tokens": 900,
            "temperature": 0.2,
        }

        try:
            response = self.session.post(
                f"{settings.pplx_api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.warning("Perplexity deep research failed: %s", exc)
            return None

        content = ""
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""

        parsed = self._parse_json(content)
        if not parsed:
            # Fallback: try to build something from citations only
            citations = data.get("citations") or []
            if not citations:
                return None
            return ResearchProfile(
                biography=ResearchSection(text="", citations=citations),
                style=ResearchSection(text="", citations=citations),
                facts=ResearchSection(text="", citations=citations),
            )

        return ResearchProfile(
            biography=ResearchSection(
                text=parsed["biography"]["text"].strip(),
                citations=self._dedupe(parsed["biography"].get("citations", [])),
            ),
            style=ResearchSection(
                text=parsed["style"]["text"].strip(),
                citations=self._dedupe(parsed["style"].get("citations", [])),
            ),
            facts=ResearchSection(
                text=parsed["facts"]["text"].strip(),
                citations=self._dedupe(parsed["facts"].get("citations", [])),
            ),
        )

    def _parse_json(self, content: str) -> Optional[dict]:
        """Parse JSON payload from content."""
        if not content:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON block
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON from Perplexity response")
            return None

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        seen = set()
        result = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result
