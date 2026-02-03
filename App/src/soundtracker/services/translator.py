"""Translation service for SOUNDTRACKER.

Provides text translation using Google Translate API.
"""

import logging
import re
from typing import Optional, Tuple

import requests

from soundtracker.config import settings

logger = logging.getLogger(__name__)


# Characters and hints for language detection
SPANISH_CHARS = set("áéíóúñü¿¡")
SPANISH_HINTS = [" el ", " la ", " de ", " y ", " que ", " en ", " los ", " las ", " un ", " una ", " del "]
ENGLISH_HINTS = [
    " the ",
    " and ",
    " was ",
    " were ",
    " born ",
    " composer ",
    " died ",
    " in ",
    " he ",
    " she ",
    " award ",
    " best ",
    " original ",
    " score ",
]


class TranslatorService:
    """Service for translating text between languages.

    Uses Google Translate API for translation.

    Example:
        translator = TranslatorService()
        spanish = translator.to_spanish("Hello world")
        english = translator.to_english("Hola mundo")
    """

    TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"

    def __init__(
        self,
        target_language: str = "es",
        timeout: int = 10,
    ) -> None:
        """Initialize translator.

        Args:
            target_language: Default target language code.
            timeout: Request timeout in seconds.
        """
        self.target_language = target_language or settings.translate_target
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Soundtracker/2.0"})

    def translate(
        self,
        text: str,
        target: Optional[str] = None,
        source: str = "auto",
    ) -> str:
        """Translate text to target language.

        Args:
            text: Text to translate.
            target: Target language code (default: instance default).
            source: Source language code ('auto' for detection).

        Returns:
            Translated text.
        """
        if not text:
            return text

        translated, _ = self.translate_detect(text, target or self.target_language, source)
        return translated

    def translate_detect(
        self,
        text: str,
        target: str,
        source: str = "auto",
    ) -> Tuple[str, str]:
        """Translate text and detect source language.

        Args:
            text: Text to translate.
            target: Target language code.
            source: Source language code.

        Returns:
            Tuple of (translated_text, detected_language).
        """
        if not text:
            return text, ""

        try:
            response = self._session.get(
                self.TRANSLATE_ENDPOINT,
                params={
                    "client": "gtx",
                    "sl": source,
                    "tl": target,
                    "dt": "t",
                    "q": text,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Translation failed: %s", e)
            return text, ""

        # Extract translated text
        translated = []
        for part in data[0]:
            if part and part[0]:
                translated.append(part[0])

        # Extract detected language
        detected = ""
        if len(data) > 2 and isinstance(data[2], str):
            detected = data[2]

        result = self._clean_text("".join(translated)) or text
        return result, detected

    def to_spanish(self, text: str) -> str:
        """Translate text to Spanish.

        Args:
            text: Text to translate.

        Returns:
            Spanish text.
        """
        if not text:
            return text

        translated, detected = self.translate_detect(text, "es")

        # If already Spanish, return original
        if detected.startswith("es"):
            return text

        return translated

    def to_english(self, text: str) -> str:
        """Translate text to English.

        Args:
            text: Text to translate.

        Returns:
            English text.
        """
        return self.translate(text, "en")

    def ensure_spanish(self, text: str) -> str:
        """Ensure text is in Spanish, translating if needed.

        Args:
            text: Text that may be in any language.

        Returns:
            Spanish text.
        """
        if not text:
            return text

        translated, detected = self.translate_detect(text, "es")

        if detected.startswith("es"):
            return text

        return translated

    def should_translate(self, text: str) -> bool:
        """Check if text should be translated to Spanish.

        Uses heuristics based on character presence and word patterns.

        Args:
            text: Text to check.

        Returns:
            True if translation is recommended.
        """
        lowered = f" {text.lower()} "

        # Check for Spanish characters
        spanish_char_count = sum(1 for ch in text if ch in SPANISH_CHARS)
        if spanish_char_count > 3:
            return False

        # Count language-specific hints
        spanish_hits = sum(1 for marker in SPANISH_HINTS if marker in lowered)
        english_hits = sum(1 for marker in ENGLISH_HINTS if marker in lowered)

        return english_hits > spanish_hits + 1

    def translate_paragraphs(self, paragraphs: list[str]) -> list[str]:
        """Translate a list of paragraphs to Spanish.

        Args:
            paragraphs: List of paragraph texts.

        Returns:
            List of translated paragraphs.
        """
        return [self.to_spanish(p) for p in paragraphs if p]

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
        return cleaned
