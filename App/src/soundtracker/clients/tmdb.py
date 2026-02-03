"""TMDB (The Movie Database) API client.

Provides access to TMDB API for film and person information.
"""

import logging
import time
from typing import Any, Optional

from soundtracker.cache import FileCache
from soundtracker.clients.base import BaseClient
from soundtracker.config import settings
from soundtracker.models import Film

logger = logging.getLogger(__name__)


class TMDBClient(BaseClient):
    """Client for The Movie Database API.

    Provides methods to search for movies, get person credits,
    and retrieve poster images. Includes caching to reduce API calls.

    Attributes:
        api_key: TMDB API key.
        image_base_url: Base URL for poster images.
        cache: Optional cache for API responses.

    Example:
        client = TMDBClient(api_key="your_key")
        details = client.search_movie_details("Jaws", 1975)
        person_id, known_for = client.search_person("John Williams")
    """

    DEFAULT_BASE_URL = "https://api.themoviedb.org/3"
    DEFAULT_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        image_base_url: Optional[str] = None,
        cache: Optional[FileCache] = None,
        timeout: int = 10,
        rate_limit_delay: float = 0.25,
    ) -> None:
        """Initialize TMDB client.

        Args:
            api_key: TMDB API key. Falls back to settings if not provided.
            base_url: API base URL. Defaults to TMDB API v3.
            image_base_url: Image base URL. Defaults to w500 size.
            cache: Optional FileCache for caching responses.
            timeout: Request timeout in seconds.
            rate_limit_delay: Delay between requests in seconds.
        """
        super().__init__(
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )
        self.api_key = api_key or settings.tmdb_api_key
        self.image_base_url = image_base_url or self.DEFAULT_IMAGE_URL
        self.cache = cache
        self._rate_limit_delay = rate_limit_delay

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_with_key(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Make a GET request with API key.

        Args:
            endpoint: API endpoint.
            params: Additional query parameters.

        Returns:
            JSON response or None on error.
        """
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None

        base_params = {"api_key": self.api_key}
        if params:
            base_params.update(params)
        return self._get(endpoint, base_params)

    def health_check(self) -> bool:
        """Check if TMDB API is available.

        Returns:
            True if API responds successfully.
        """
        if not self.api_key:
            return False
        result = self._get_with_key("/configuration")
        return result is not None

    def search_movie_details(
        self,
        title: str,
        year: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        """Search for a movie and get its details.

        Args:
            title: Movie title to search.
            year: Optional release year for filtering.

        Returns:
            Dictionary with movie details or None if not found.
        """
        if not self.api_key:
            return None

        # Check cache first
        cache_key = f"{title}|{year or ''}"
        if self.cache and cache_key in self.cache:
            cached = self.cache.get(cache_key)
            return cached if cached else None

        chosen = None
        for lang in ["es-ES", "en-US"]:
            params = {"query": title, "language": lang, "include_adult": "false"}
            if year:
                params["year"] = str(year)

            data = self._get_with_key("/search/movie", params)
            if not data:
                continue

            results = data.get("results", [])
            if not results:
                continue

            chosen = results[0]
            if year:
                for result in results:
                    release = result.get("release_date") or ""
                    if release.startswith(str(year)):
                        chosen = result
                        break
            if chosen:
                break

        if not chosen:
            if self.cache:
                self.cache.set(cache_key, {})
            return None

        # Get Spanish details
        movie_id = chosen.get("id")
        es_data = None
        if movie_id:
            es_data = self._get_with_key(f"/movie/{movie_id}", {"language": "es-ES"})

        details = {
            "original_title": (es_data or {}).get("original_title")
            or chosen.get("original_title")
            or chosen.get("title"),
            "title_es": (es_data or {}).get("title")
            or chosen.get("title")
            or chosen.get("original_title"),
            "poster_path": (es_data or {}).get("poster_path")
            or chosen.get("poster_path"),
            "popularity": chosen.get("popularity"),
            "vote_count": chosen.get("vote_count"),
            "vote_average": chosen.get("vote_average"),
            "id": movie_id,
        }

        if self.cache:
            self.cache.set(cache_key, details)

        time.sleep(self._rate_limit_delay)
        return details

    def search_person(self, name: str) -> tuple[Optional[int], list[str]]:
        """Search for a person and get their known works.

        Args:
            name: Person name to search.

        Returns:
            Tuple of (person_id, list of known_for titles).
        """
        if not self.api_key:
            return None, []

        data = self._get_with_key("/search/person", {"query": name})
        if not data:
            return None, []

        results = data.get("results", [])
        if not results:
            return None, []

        person = results[0]
        known_for_titles: list[str] = []
        for item in person.get("known_for", []) or []:
            title = item.get("title") or item.get("original_title")
            if title and title not in known_for_titles:
                known_for_titles.append(title)

        return person.get("id"), known_for_titles

    def get_person_movie_credits(
        self,
        person_id: int,
        language: str = "es-ES",
        limit: int = 200,
    ) -> list[Film]:
        """Get movie credits for a person.

        Args:
            person_id: TMDB person ID.
            language: Language for titles.
            limit: Maximum number of films to return.

        Returns:
            List of Film objects.
        """
        if not self.api_key:
            return []

        data = self._get_with_key(
            f"/person/{person_id}/movie_credits",
            {"language": language},
        )
        if not data:
            return []

        crew = data.get("crew", [])
        cast = data.get("cast", [])

        # Filter for music/composer credits
        music_credits = []
        for item in crew:
            job = (item.get("job") or "").lower()
            dept = (item.get("department") or "").lower()
            if "music" in dept or "composer" in job or "score" in job:
                music_credits.append(item)

        # If few music credits, include all crew
        if len(music_credits) < 5:
            music_credits = crew

        all_credits = music_credits + cast

        films: list[Film] = []
        for item in all_credits:
            title = item.get("title") or item.get("original_title")
            if not title:
                continue

            year = None
            release = item.get("release_date")
            if release:
                try:
                    year = int(release.split("-")[0])
                except (ValueError, IndexError):
                    pass

            film = Film(
                title=title,
                original_title=item.get("original_title") or title,
                title_es=title if language.startswith("es") else None,
                year=year,
                poster_path=item.get("poster_path"),
                popularity=item.get("popularity"),
                vote_count=item.get("vote_count"),
                vote_average=item.get("vote_average"),
            )
            films.append(film)

            if len(films) >= limit:
                break

        return films

    def get_person_profile_url(self, person_id: int) -> Optional[str]:
        """Get profile image URL for a person.

        Args:
            person_id: TMDB person ID.

        Returns:
            Full URL to profile image or None.
        """
        if not self.api_key:
            return None

        data = self._get_with_key(f"/person/{person_id}", {})
        if not data:
            return None

        profile = data.get("profile_path")
        if not profile:
            return None

        return f"{self.image_base_url}{profile}"

    def get_poster_url(self, poster_path: str) -> str:
        """Build full poster URL from path.

        Args:
            poster_path: TMDB poster path (e.g., /abc123.jpg).

        Returns:
            Full URL to poster image.
        """
        return f"{self.image_base_url}{poster_path}"

    def search_movie_poster(
        self,
        title: str,
        year: Optional[int] = None,
    ) -> Optional[str]:
        """Search for a movie and get its poster URL.

        Args:
            title: Movie title.
            year: Optional release year.

        Returns:
            Full poster URL or None.
        """
        details = self.search_movie_details(title, year)
        if not details:
            return None

        poster_path = details.get("poster_path")
        if not poster_path:
            return None

        return self.get_poster_url(poster_path)
