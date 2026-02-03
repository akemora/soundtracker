"""Awards service for composer accolades.

Provides functionality to fetch and process awards and nominations
for film composers from various sources.
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from soundtracker.clients import SearchClient, WikidataClient, WikipediaClient
from soundtracker.models import Award, AwardStatus
from soundtracker.services.translator import TranslatorService

logger = logging.getLogger(__name__)


AWARD_KEYWORDS = [
    "Academy Award",
    "Oscar",
    "Golden Globe",
    "Globo de Oro",
    "BAFTA",
    "Grammy",
    "Emmy",
    "Premio de la Academia",
]


class AwardsService:
    """Service for fetching composer awards and nominations.

    Combines data from Wikidata, Wikipedia, and web search
    to compile a complete awards history.

    Example:
        service = AwardsService()
        awards = service.get_awards("John Williams")
    """

    def __init__(
        self,
        wikidata_client: Optional[WikidataClient] = None,
        wikipedia_client: Optional[WikipediaClient] = None,
        search_client: Optional[SearchClient] = None,
        translator: Optional[TranslatorService] = None,
    ) -> None:
        """Initialize awards service.

        Args:
            wikidata_client: Wikidata client.
            wikipedia_client: Wikipedia client.
            search_client: Web search client.
            translator: Translation service.
        """
        self.wikidata = wikidata_client or WikidataClient()
        self.wikipedia_es = wikipedia_client or WikipediaClient(lang="es")
        self.wikipedia_en = WikipediaClient(lang="en")
        self.search = search_client or SearchClient()
        self.translator = translator or TranslatorService()

    def get_awards(self, composer: str) -> list[Award]:
        """Get all awards and nominations for a composer.

        Args:
            composer: Composer name.

        Returns:
            List of Award objects.
        """
        # Try Wikidata first (most structured)
        qid = self.wikidata.get_qid(composer)
        if qid:
            awards = self.wikidata.get_awards(qid)
            if awards:
                return self._dedupe_and_translate(awards)

        # Try Wikipedia
        awards = self._get_from_wikipedia(composer)
        if awards:
            return self._dedupe_and_translate(awards)

        # Fall back to web search
        return self._search_awards(composer)

    def _get_from_wikipedia(self, composer: str) -> list[Award]:
        """Extract awards from Wikipedia.

        Args:
            composer: Composer name.

        Returns:
            List of awards.
        """
        awards: list[Award] = []

        # Try Spanish Wikipedia first
        html = self.wikipedia_es.fetch_html(f"{composer} compositor")
        if not html:
            html = self.wikipedia_en.fetch_html(f"{composer} composer")

        if not html:
            return awards

        awards_html = self._extract_section(html)
        if not awards_html:
            return awards

        soup = BeautifulSoup(awards_html, "html.parser")
        lines = [li.get_text(" ", strip=True) for li in soup.find_all("li")]

        for line in lines:
            award = self._parse_award_line(line)
            if award:
                awards.append(award)

        return awards

    def _extract_section(self, html: str) -> str:
        """Extract awards section from HTML.

        Args:
            html: Full HTML content.

        Returns:
            Awards section HTML.
        """
        keywords = [
            "award",
            "awards",
            "honor",
            "honours",
            "recognition",
            "premios",
            "reconocimientos",
        ]

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

    def _parse_award_line(self, line: str) -> Optional[Award]:
        """Parse an award line into Award object.

        Args:
            line: Text line describing an award.

        Returns:
            Award object or None.
        """
        if not any(kw.lower() in line.lower() for kw in AWARD_KEYWORDS):
            return None

        # Extract year
        year_match = re.search(r"(19|20)\d{2}", line)
        year = int(year_match.group()) if year_match else None

        # Validate year range
        if year and (year < 1900 or year > 2030):
            return None

        # Extract film
        film_match = re.search(r"for\s+['\"]?([^'\"\n,]+)", line, re.IGNORECASE)
        film = film_match.group(1).strip() if film_match else None

        # Determine status
        status = (
            AwardStatus.WIN
            if "win" in line.lower() or "winner" in line.lower()
            else AwardStatus.NOMINATION
        )

        # Determine award name
        award_name = next(
            (kw for kw in AWARD_KEYWORDS if kw.lower() in line.lower()),
            "Award",
        )

        return Award(
            award=award_name,
            year=year,
            film=film,
            status=status,
        )

    def _search_awards(self, composer: str) -> list[Award]:
        """Search web for awards information.

        Args:
            composer: Composer name.

        Returns:
            List of awards.
        """
        awards: list[Award] = []
        urls = self.search.search(f"{composer} awards and nominations", num=5)

        for url in urls:
            html = self.search.fetch_url_text(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n")

            for line in text.splitlines():
                award = self._parse_award_line(line)
                if award:
                    awards.append(award)

            if awards:
                break

        return self._dedupe_and_translate(awards)

    def _dedupe_and_translate(self, awards: list[Award]) -> list[Award]:
        """Deduplicate awards and translate to Spanish.

        Args:
            awards: Raw list of awards.

        Returns:
            Cleaned and translated list.
        """
        seen = set()
        unique: list[Award] = []

        for award in awards:
            key = (
                (award.award or "").strip().lower(),
                award.year,
                (award.film or "").strip().lower(),
                award.status.value.lower(),
            )

            if key in seen:
                continue
            seen.add(key)

            # Translate award name
            if award.award:
                award.award = self.translator.to_spanish(award.award)

            unique.append(award)

        # Sort by year, award, film
        unique.sort(
            key=lambda a: (
                a.year or 9999,
                a.award or "",
                a.film or "",
            )
        )

        return unique
