"""Filmography service for composer film credits.

Provides functionality to fetch, merge, and deduplicate filmographies
from multiple sources (TMDB, Wikidata, Wikipedia, web search).
"""

import logging
import re
from pathlib import Path
from typing import Optional

from soundtracker.clients import (
    ImdbDataset,
    SearchClient,
    TMDBClient,
    WikidataClient,
    WikipediaClient,
)
from soundtracker.config import settings
from soundtracker.models import Film

logger = logging.getLogger(__name__)


# Bad titles to filter out
BAD_TITLES = {
    "main page",
    "contents",
    "current events",
    "random article",
    "about wikipedia",
    "contact us",
    "help",
    "learn to edit",
    "community portal",
    "recent changes",
    "donate",
    "contribute",
    "privacy policy",
    "terms of use",
    "disclaimers",
}


class FilmographyService:
    """Service for fetching and managing composer filmographies.

    Combines data from TMDB, Wikidata, Wikipedia, and web search
    to create comprehensive filmography lists.

    Example:
        service = FilmographyService()
        films = service.get_complete_filmography("John Williams")
    """

    def __init__(
        self,
        tmdb_client: Optional[TMDBClient] = None,
        wikidata_client: Optional[WikidataClient] = None,
        wikipedia_client: Optional[WikipediaClient] = None,
        search_client: Optional[SearchClient] = None,
        imdb_client: Optional[ImdbDataset] = None,
        film_limit: int = 200,
    ) -> None:
        """Initialize filmography service.

        Args:
            tmdb_client: TMDB API client.
            wikidata_client: Wikidata client.
            wikipedia_client: Wikipedia client.
            search_client: Web search client.
            film_limit: Maximum films to return.
        """
        self.tmdb = tmdb_client or TMDBClient()
        self.wikidata = wikidata_client or WikidataClient()
        self.wikipedia = wikipedia_client or WikipediaClient(lang="en")
        self.search = search_client or SearchClient()
        self.imdb = imdb_client or ImdbDataset()
        self.film_limit = film_limit or settings.film_limit

    def get_complete_filmography(
        self,
        composer: str,
        composer_folder: Optional[Path] = None,
        tmdb_id: Optional[int] = None,
        wikidata_qid: Optional[str] = None,
    ) -> list[Film]:
        """Get complete filmography for a composer.

        Fetches from multiple sources and merges results.

        Args:
            composer: Composer name.
            composer_folder: Optional folder for poster paths.
            tmdb_id: Optional TMDB person ID to skip search.
            wikidata_qid: Optional Wikidata QID to skip lookup.

        Returns:
            List of Film objects sorted by year.
        """
        films: list[Film] = []

        # Primary source: IMDb dataset (offline)
        if self.imdb.is_available:
            imdb_films = self.imdb.get_composer_filmography(
                composer,
                max_titles=self.film_limit,
            )
            films = self._merge_films(films, imdb_films)

        # Secondary source: TMDB
        if not films and self.tmdb.is_available:
            person_id = tmdb_id
            if person_id is None:
                person_id, _ = self.tmdb.search_person(composer)
            if person_id:
                tmdb_films = self.tmdb.get_person_movie_credits(person_id)
                films = tmdb_films

        # Supplement with Wikidata
        if len(films) < 8:
            qid = wikidata_qid or self.wikidata.get_qid(composer)
            if qid:
                wd_films = self.wikidata.get_filmography(qid)
                films = self._merge_films(films, wd_films)

        # Supplement with Wikipedia
        if len(films) < 8:
            html = self.wikipedia.fetch_html(f"{composer} composer")
            if html:
                wiki_films = self._extract_films_from_html(html)
                films = self._merge_films(films, wiki_films)

        # Fall back to web search
        if len(films) < 8:
            web_films = self._search_filmography(composer)
            films = self._merge_films(films, web_films)

        # Deduplicate and sort
        films = self._dedupe_films(films)
        films.sort(key=lambda f: (f.year or 9999, f.title or ""))

        # Enrich with TMDB details
        if self.tmdb.is_available:
            for film in films:
                self._enrich_film(film)

        # Set poster paths
        if composer_folder:
            for film in films:
                self._set_poster_path(film, composer_folder)

        return films[: self.film_limit]

    def _merge_films(self, base: list[Film], extra: list[Film]) -> list[Film]:
        """Merge film lists, avoiding duplicates.

        Args:
            base: Base film list.
            extra: Additional films to merge.

        Returns:
            Merged list.
        """
        existing = set()
        for film in base:
            key = self._normalize_title_key(film.original_title or film.title)
            if key:
                existing.add(key)

        for film in extra:
            key = self._normalize_title_key(film.original_title or film.title)
            if key and key not in existing:
                base.append(film)
                existing.add(key)

        return base

    def _dedupe_films(self, films: list[Film]) -> list[Film]:
        """Deduplicate film list.

        Args:
            films: List of films.

        Returns:
            Deduplicated list.
        """
        seen = set()
        unique: list[Film] = []

        for film in films:
            title = (film.original_title or film.title or "").strip()
            if not title or self._is_bad_title(title):
                continue

            key = (title.lower(), film.year)
            if key in seen:
                continue

            seen.add(key)
            unique.append(film)

        return unique

    def _enrich_film(self, film: Film) -> None:
        """Enrich film with TMDB details.

        Args:
            film: Film to enrich (modified in place).
        """
        if not self.tmdb.is_available:
            return

        if film.title_es and film.poster_path:
            return

        details = self.tmdb.search_movie_details(
            film.original_title or film.title,
            film.year,
        )

        if not details:
            return

        if not film.original_title:
            film.original_title = details.get("original_title")
        if not film.title_es:
            film.title_es = details.get("title_es")
        if not film.poster_path:
            film.poster_path = details.get("poster_path")
        if film.popularity is None:
            film.popularity = details.get("popularity")
        if film.vote_count is None:
            film.vote_count = details.get("vote_count")
        if film.vote_average is None:
            film.vote_average = details.get("vote_average")

    def _set_poster_path(self, film: Film, composer_folder: Path) -> None:
        """Set local poster path for a film.

        Args:
            film: Film to update.
            composer_folder: Composer assets folder.
        """
        if film.poster_path:
            film.poster_url = f"https://image.tmdb.org/t/p/w500{film.poster_path}"

        poster_name = self._poster_filename(
            film.original_title or film.title,
            film.year,
        )
        film.poster_file = str(composer_folder / "posters" / poster_name)

    def _extract_films_from_html(self, html: str) -> list[Film]:
        """Extract film list from HTML.

        Args:
            html: HTML content.

        Returns:
            List of films.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        films: list[Film] = []

        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            extracted = self._extract_films_from_text(text)
            for film in extracted:
                if film not in films:
                    films.append(film)
                if len(films) >= 200:
                    return films

        return films

    def _extract_films_from_text(self, text: str) -> list[Film]:
        """Extract films from text using regex.

        Args:
            text: Text containing film references.

        Returns:
            List of films.
        """
        pattern = re.compile(r"([A-Z][A-Za-z0-9\-'\".,\s]{3,80})\s*\(?((19|20)\d{2})\)?")
        seen = set()
        films: list[Film] = []

        for match in pattern.finditer(text):
            title = match.group(1).strip(" .-–")
            year_str = match.group(2)

            if not title:
                continue

            key = (title.lower(), year_str)
            if key in seen:
                continue
            seen.add(key)

            year = int(year_str) if year_str else None
            films.append(Film(title=title, year=year))

            if len(films) >= 200:
                break

        return films

    def _search_filmography(self, composer: str) -> list[Film]:
        """Search web for filmography.

        Args:
            composer: Composer name.

        Returns:
            List of films.
        """
        urls = self.search.search(f"{composer} filmography list", num=5)

        for url in urls:
            html = self.search.fetch_url_text(url)
            if not html:
                continue

            films = self._extract_films_from_text(html)
            if films:
                return films

        return []

    def _normalize_title_key(self, title: str) -> str:
        """Normalize title for deduplication.

        Args:
            title: Film title.

        Returns:
            Normalized key.
        """
        return re.sub(r"[^a-z0-9]+", "", title.lower())

    def _is_bad_title(self, title: str) -> bool:
        """Check if title should be filtered out.

        Args:
            title: Title to check.

        Returns:
            True if bad title.
        """
        lowered = title.strip().lower()
        if lowered in BAD_TITLES:
            return True
        if "wikipedia" in lowered or "edit" in lowered:
            return True
        if re.fullmatch(r"q\d+", lowered):
            return True
        return False

    def _poster_filename(self, title: str, year: Optional[int] = None) -> str:
        """Generate poster filename.

        Args:
            title: Film title.
            year: Release year.

        Returns:
            Filename for poster.
        """
        slug = re.sub(r"[^a-z0-9]+", "_", (title or "poster").lower()).strip("_") or "poster"
        if year:
            return f"poster_{slug}_{year}.jpg"
        return f"poster_{slug}.jpg"
