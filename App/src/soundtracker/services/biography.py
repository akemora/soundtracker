"""Biography service for composer information.

Provides functionality to fetch and assemble composer biographies,
musical style descriptions, and anecdotes from various sources.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from soundtracker.clients import SearchClient, WikipediaClient
from soundtracker.services.translator import TranslatorService

logger = logging.getLogger(__name__)


STYLE_SECTION_KEYWORDS = [
    "musical style",
    "style and influence",
    "style",
    "influence",
    "influences",
    "compositions",
    "estilo",
    "estilo musical",
    "influencia",
    "influencias",
]

ANECDOTE_SECTION_KEYWORDS = [
    "personal life",
    "legacy",
    "later life",
    "death",
    "trivia",
    "anecdote",
    "vida personal",
    "legado",
    "muerte",
    "curiosidades",
]

STYLE_HINTS = [
    "style",
    "influence",
    "sound",
    "orchestration",
    "melody",
    "theme",
    "estilo",
    "música",
    "musical",
    "bandas sonoras",
    "orquesta",
]

ANECDOTE_HINTS = [
    "born",
    "died",
    "career",
    "personal",
    "known for",
    "worked",
    "collaborated",
    "nacio",
    "murio",
    "nació",
    "murió",
]

FUN_FACT_HINTS = [
    "premio",
    "nomin",
    "gan",
    "oscar",
    "academia",
    "compuso",
    "compositor",
    "orquesta",
    "orquestal",
    "tema",
    "melod",
    "colabor",
    "trabaj",
    "director",
    "dirig",
    "innov",
    "pioner",
    "destac",
]


class BiographyService:
    """Service for fetching and assembling composer biographies.

    Combines information from Wikipedia, web search, and other sources
    to create comprehensive biographies in Spanish.

    Example:
        service = BiographyService()
        bio = service.get_biography("John Williams")
        style = service.get_musical_style("John Williams")
    """

    def __init__(
        self,
        wikipedia_client: Optional[WikipediaClient] = None,
        search_client: Optional[SearchClient] = None,
        translator: Optional[TranslatorService] = None,
        max_paragraphs: int = 6,
        min_paragraph_len: int = 50,
    ) -> None:
        """Initialize biography service.

        Args:
            wikipedia_client: Wikipedia API client.
            search_client: Web search client.
            translator: Translation service.
            max_paragraphs: Maximum biography paragraphs.
            min_paragraph_len: Minimum paragraph length.
        """
        self.wikipedia = wikipedia_client or WikipediaClient(lang="es")
        self.wikipedia_en = WikipediaClient(lang="en")
        self.search = search_client or SearchClient()
        self.translator = translator or TranslatorService()
        self.max_paragraphs = max_paragraphs
        self.min_paragraph_len = min_paragraph_len

    def get_biography(self, composer: str) -> str:
        """Get composer biography in Spanish.

        Args:
            composer: Composer name.

        Returns:
            Biography text in Spanish.
        """
        # Try Spanish Wikipedia first
        bio = self.wikipedia.get_extract(f"{composer} compositor")
        if bio:
            return self._format_biography(bio)

        # Try English Wikipedia
        bio = self.wikipedia_en.get_extract(f"{composer} composer")
        if bio:
            translated = self.translator.to_spanish(bio)
            return self._format_biography(translated)

        # Fall back to web search
        return self._search_biography(composer)

    def _format_biography(self, text: str) -> str:
        """Format biography text into paragraphs.

        Args:
            text: Raw biography text.

        Returns:
            Formatted biography.
        """
        paragraphs = text.split("\n\n")
        result = []

        for para in paragraphs:
            cleaned = self._clean_text(para)
            if len(cleaned) >= self.min_paragraph_len:
                result.append(cleaned)
            if len(result) >= self.max_paragraphs:
                break

        return "\n\n".join(result)

    def _search_biography(self, composer: str) -> str:
        """Search web for biography information.

        Args:
            composer: Composer name.

        Returns:
            Biography text or empty string.
        """
        queries = [
            f"{composer} compositor biografía",
            f"{composer} composer biography",
        ]

        for query in queries:
            urls = self.search.search(query, num=3)
            for url in urls:
                html = self.search.fetch_url_text(url)
                if not html:
                    continue

                paragraphs = self.search.extract_paragraphs(
                    html,
                    max_paragraphs=self.max_paragraphs,
                    min_length=self.min_paragraph_len,
                )

                if paragraphs:
                    text = "\n\n".join(paragraphs)
                    return self.translator.ensure_spanish(text)

        return ""

    def get_musical_style(self, composer: str) -> str:
        """Get description of composer's musical style.

        Args:
            composer: Composer name.

        Returns:
            Style description in Spanish.
        """
        # Try extracting from Wikipedia sections
        for lang, client in [("es", self.wikipedia), ("en", self.wikipedia_en)]:
            html = client.fetch_html(f"{composer} compositor" if lang == "es" else f"{composer} composer")
            if not html:
                continue

            section = self._extract_section(html, STYLE_SECTION_KEYWORDS)
            if section:
                text = self._section_to_text(section)
                if lang == "en":
                    text = self.translator.to_spanish(text)
                return text

        # Fall back to search
        return self._search_for_text(
            f"{composer} estilo musical compositor",
            STYLE_HINTS,
        )

    def get_anecdotes(self, composer: str) -> str:
        """Get personal anecdotes about a composer.

        Args:
            composer: Composer name.

        Returns:
            Anecdotes text in Spanish.
        """
        # Try extracting from Wikipedia sections
        for lang, client in [("es", self.wikipedia), ("en", self.wikipedia_en)]:
            html = client.fetch_html(f"{composer} compositor" if lang == "es" else f"{composer} composer")
            if not html:
                continue

            section = self._extract_section(html, ANECDOTE_SECTION_KEYWORDS)
            if section:
                text = self._section_to_text(section)
                if lang == "en":
                    text = self.translator.to_spanish(text)
                return text

        # Fall back to search
        return self._search_for_text(
            f"{composer} compositor curiosidades vida personal",
            ANECDOTE_HINTS,
        )

    def derive_fun_facts(self, biography: str, style: str) -> str:
        """Derive fun facts from available biography/style text.

        Args:
            biography: Biography text.
            style: Musical style text.

        Returns:
            Short facts text or empty string.
        """
        for text in [style, biography]:
            selected = self._select_sentences(text, FUN_FACT_HINTS, max_sentences=2)
            if selected:
                return "\n\n".join(selected)
        return ""

    def _select_sentences(
        self,
        text: str,
        keywords: list[str],
        max_sentences: int = 2,
    ) -> list[str]:
        """Select sentences containing any keyword.

        Args:
            text: Source text.
            keywords: Keywords to match.
            max_sentences: Maximum number of sentences to return.

        Returns:
            List of selected sentences.
        """
        if not text:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        selected: list[str] = []

        for sentence in sentences:
            lowered = sentence.lower()
            if any(keyword in lowered for keyword in keywords):
                cleaned = self._clean_text(sentence)
                if len(cleaned) >= self.min_paragraph_len:
                    selected.append(cleaned)
            if len(selected) >= max_sentences:
                break

        return selected

    def _extract_section(self, html: str, keywords: list[str]) -> str:
        """Extract a section from HTML based on heading keywords.

        Args:
            html: HTML content.
            keywords: Keywords to match in headings.

        Returns:
            Section HTML or empty string.
        """
        soup = BeautifulSoup(html, "html.parser")

        for heading in soup.find_all(["h2", "h3"]):
            title = heading.get_text(" ", strip=True).lower()
            if any(keyword in title for keyword in keywords):
                content = []
                for sibling in heading.next_siblings:
                    if getattr(sibling, "name", None) in ["h2", "h3"]:
                        break
                    content.append(str(sibling))
                return "".join(content)

        return ""

    def _section_to_text(self, html: str, max_paragraphs: int = 2) -> str:
        """Convert section HTML to plain text.

        Args:
            html: Section HTML.
            max_paragraphs: Maximum paragraphs.

        Returns:
            Plain text.
        """
        if not html:
            return ""

        paragraphs = self.search.extract_paragraphs(
            html,
            max_paragraphs=max_paragraphs,
            min_length=self.min_paragraph_len,
        )
        return "\n\n".join(paragraphs)

    def _search_for_text(self, query: str, required_keywords: list[str]) -> str:
        """Search for text containing required keywords.

        Args:
            query: Search query.
            required_keywords: Keywords that must appear.

        Returns:
            Found text in Spanish or empty string.
        """
        urls = self.search.search(query, num=4)

        for url in urls:
            html = self.search.fetch_url_text(url)
            if not html:
                continue

            paragraphs = self.search.extract_paragraphs(html, max_paragraphs=4)

            for paragraph in paragraphs:
                lowered = paragraph.lower()
                if any(keyword in lowered for keyword in required_keywords):
                    return self.translator.ensure_spanish(paragraph)

        return ""

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
        return cleaned
