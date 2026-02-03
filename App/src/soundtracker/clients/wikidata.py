"""Wikidata SPARQL client.

Provides access to Wikidata for structured data about composers,
their filmographies, and awards.
"""

import logging
import re
from typing import Optional

from soundtracker.clients.base import BaseClient
from soundtracker.models import Award, AwardStatus, Film

logger = logging.getLogger(__name__)


class WikidataClient(BaseClient):
    """Client for Wikidata API and SPARQL endpoint.

    Provides methods to get entity IDs, filmographies, and awards
    from the Wikidata knowledge base.

    Example:
        client = WikidataClient()
        qid = client.get_qid("John Williams")
        films = client.get_filmography(qid)
        awards = client.get_awards(qid)
    """

    API_URL = "https://www.wikidata.org/w/api.php"
    SPARQL_URL = "https://query.wikidata.org/sparql"

    def __init__(self, timeout: int = 15) -> None:
        """Initialize Wikidata client.

        Args:
            timeout: Request timeout in seconds.
        """
        super().__init__(
            base_url=self.API_URL,
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )

    def health_check(self) -> bool:
        """Check if Wikidata API is available.

        Returns:
            True if API responds successfully.
        """
        params = {
            "action": "wbsearchentities",
            "search": "test",
            "language": "en",
            "format": "json",
            "limit": "1",
        }
        result = self._get("", params)
        return result is not None

    def get_qid(self, name: str, language: str = "en") -> Optional[str]:
        """Get Wikidata QID for a person.

        Args:
            name: Person name to search.
            language: Search language.

        Returns:
            Wikidata QID (e.g., "Q180387") or None.
        """
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": language,
            "format": "json",
            "limit": "1",
        }

        data = self._get("", params)
        if not data:
            return None

        results = data.get("search", [])
        if not results:
            return None

        return results[0].get("id")

    def _sparql_query(self, query: str) -> Optional[dict]:
        """Execute a SPARQL query.

        Args:
            query: SPARQL query string.

        Returns:
            Query results or None on error.
        """
        try:
            response = self.session.get(
                self.SPARQL_URL,
                params={"format": "json", "query": query},
                headers=self.session.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("SPARQL query failed: %s", e)
            return None

    def get_filmography(self, qid: str, limit: int = 200) -> list[Film]:
        """Get filmography for a composer.

        Args:
            qid: Wikidata QID of the composer.
            limit: Maximum number of films.

        Returns:
            List of Film objects.
        """
        query = f"""
        SELECT ?film ?filmLabel ?labelEs ?labelEn ?originalTitle ?year WHERE {{
          ?film wdt:P86 wd:{qid} .
          OPTIONAL {{ ?film wdt:P1476 ?originalTitle . }}
          OPTIONAL {{ ?film rdfs:label ?labelEs FILTER(LANG(?labelEs) = "es") }}
          OPTIONAL {{ ?film rdfs:label ?labelEn FILTER(LANG(?labelEn) = "en") }}
          OPTIONAL {{ ?film wdt:P577 ?date . BIND(YEAR(?date) as ?year) }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {limit}
        """

        data = self._sparql_query(query)
        if not data:
            return []

        films: list[Film] = []
        for item in data.get("results", {}).get("bindings", []):
            label = item.get("filmLabel", {}).get("value")
            label_es = item.get("labelEs", {}).get("value")
            label_en = item.get("labelEn", {}).get("value")
            original_title = item.get("originalTitle", {}).get("value")
            year_str = item.get("year", {}).get("value")

            title = original_title or label_en or label or label_es
            if not title or re.fullmatch(r"Q\d+", title.strip()):
                continue

            year = None
            if year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    pass

            film = Film(
                title=title,
                original_title=original_title or label_en or title,
                title_es=label_es,
                year=year,
            )
            films.append(film)

        return films

    def get_awards(self, qid: str) -> list[Award]:
        """Get awards and nominations for a person.

        Args:
            qid: Wikidata QID of the person.

        Returns:
            List of Award objects.
        """
        query = f"""
        SELECT ?award ?awardLabel ?year ?workLabel ?status WHERE {{
          {{
            wd:{qid} p:P166 ?awardStatement .
            ?awardStatement ps:P166 ?award .
            BIND("Win" as ?status)
            OPTIONAL {{ ?awardStatement pq:P585 ?date . BIND(YEAR(?date) as ?year) }}
            OPTIONAL {{ ?awardStatement pq:P1686 ?work . }}
          }}
          UNION
          {{
            wd:{qid} p:P1411 ?awardStatement .
            ?awardStatement ps:P1411 ?award .
            BIND("Nomination" as ?status)
            OPTIONAL {{ ?awardStatement pq:P585 ?date . BIND(YEAR(?date) as ?year) }}
            OPTIONAL {{ ?awardStatement pq:P1686 ?work . }}
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """

        data = self._sparql_query(query)
        if not data:
            return []

        awards: list[Award] = []
        for item in data.get("results", {}).get("bindings", []):
            award_name = item.get("awardLabel", {}).get("value")
            year_str = item.get("year", {}).get("value")
            work = item.get("workLabel", {}).get("value")
            status_str = item.get("status", {}).get("value") or "Win"

            if not award_name:
                continue

            year = None
            if year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    pass

            status = AwardStatus.WIN if status_str == "Win" else AwardStatus.NOMINATION

            award = Award(
                award=award_name,
                year=year,
                film=work,
                status=status,
            )
            awards.append(award)

        return awards

    def get_birth_death_years(self, qid: str) -> tuple[Optional[int], Optional[int]]:
        """Get birth and death years for a person.

        Args:
            qid: Wikidata QID.

        Returns:
            Tuple of (birth_year, death_year). Either can be None.
        """
        query = f"""
        SELECT ?birthYear ?deathYear WHERE {{
          OPTIONAL {{ wd:{qid} wdt:P569 ?birthDate . BIND(YEAR(?birthDate) as ?birthYear) }}
          OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate . BIND(YEAR(?deathDate) as ?deathYear) }}
        }}
        LIMIT 1
        """

        data = self._sparql_query(query)
        if not data:
            return None, None

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None, None

        item = bindings[0]
        birth_year = None
        death_year = None

        birth_str = item.get("birthYear", {}).get("value")
        if birth_str:
            try:
                birth_year = int(birth_str)
            except ValueError:
                pass

        death_str = item.get("deathYear", {}).get("value")
        if death_str:
            try:
                death_year = int(death_str)
            except ValueError:
                pass

        return birth_year, death_year

    def get_country(self, qid: str) -> Optional[str]:
        """Get country of citizenship for a person.

        Args:
            qid: Wikidata QID.

        Returns:
            Country name or None.
        """
        query = f"""
        SELECT ?countryLabel WHERE {{
          wd:{qid} wdt:P27 ?country .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
        }}
        LIMIT 1
        """

        data = self._sparql_query(query)
        if not data:
            return None

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None

        return bindings[0].get("countryLabel", {}).get("value")
