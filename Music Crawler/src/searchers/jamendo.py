"""Jamendo searcher - Creative Commons licensed music."""

import requests

from src.core.config import settings
from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.duckduckgo import DuckDuckGoProvider
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class JamendoSearcher(BaseSearcher):
    """Search Jamendo for Creative Commons licensed tracks."""

    name = "jamendo"
    is_free = True  # Creative Commons licensed
    API_URL = "https://api.jamendo.com/v3.0/tracks"

    def __init__(self, max_results: int = 3, provider: SearchProvider | None = None):
        self.max_results = max_results
        # Try to get client ID from environment
        self.client_id = settings.jamendo_client_id
        self.provider: SearchProvider = provider or DuckDuckGoProvider()

    def search(self, track: Track) -> list[SearchResult]:
        """Search Jamendo - tries API first, falls back to web search."""
        if self.client_id:
            results = self._search_api(track)
            if results:
                return results
        return self._search_web(track)

    def _search_api(self, track: Track) -> list[SearchResult]:
        """Search via Jamendo API (requires client_id)."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            params = {
                "client_id": self.client_id,
                "format": "json",
                "limit": self.max_results,
                "search": query,
                "include": "musicinfo",
            }
            response = requests.get(self.API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                result = self._parse_api_result(track, item)
                if result:
                    results.append(result)

        except requests.RequestException as exc:
            logger.error("Jamendo API search failed for query '%s': %s", query, exc, exc_info=True)

        return results

    def _parse_api_result(self, track: Track, item: dict) -> SearchResult | None:
        """Parse a Jamendo API result."""
        track_id = item.get("id")
        if not track_id:
            return None

        title = item.get("name", "Unknown")
        artist = item.get("artist_name", "")
        duration = item.get("duration", 0)
        audio_url = item.get("audio")  # Direct download URL
        shareurl = item.get("shareurl", f"https://www.jamendo.com/track/{track_id}")

        full_title = f"{artist} - {title}" if artist else title

        duration_str = None
        if duration:
            mins, secs = divmod(int(duration), 60)
            duration_str = f"{mins}:{secs:02d}"

        return SearchResult(
            track=track,
            source=self.name,
            url=shareurl,
            is_free=True,
            quality="MP3 (Creative Commons)",
            title=full_title,
            duration=duration_str,
        )

    def _search_web(self, track: Track) -> list[SearchResult]:
        """Fallback: search via DuckDuckGo."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="jamendo.com",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=True,
                quality="MP3 (Creative Commons)",
                title=url,
            )
            results.append(result)

        return results
