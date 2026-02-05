"""Spotify searcher (search only, no download)."""

import requests

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class SpotifySearcher(BaseSearcher):
    """Search Spotify for tracks (log only, no download)."""

    name = "spotify"
    is_free = False  # Paid service

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Spotify via web search (no API key needed)."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="open.spotify.com",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=False,
                quality="320kbps (Premium)",
                title=url,
            )
            results.append(result)

        return results


class ITunesSearcher(BaseSearcher):
    """Search iTunes/Apple Music for tracks (log only)."""

    name = "itunes"
    is_free = False
    SEARCH_URL = "https://itunes.apple.com/search"

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search iTunes Store API."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            params = {
                "term": query,
                "media": "music",
                "limit": self.max_results,
            }
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                result = self._parse_result(track, item)
                if result:
                    results.append(result)

        except requests.RequestException as exc:
            logger.error("iTunes search failed for query '%s': %s", query, exc, exc_info=True)

        return results

    def _parse_result(self, track: Track, item: dict) -> SearchResult | None:
        """Parse an iTunes search result."""
        track_url = item.get("trackViewUrl")
        if not track_url:
            return None

        title = item.get("trackName", "Unknown")
        artist = item.get("artistName", "")
        album = item.get("collectionName", "")

        full_title = f"{artist} - {title}"
        if album:
            full_title += f" ({album})"

        return SearchResult(
            track=track,
            source=self.name,
            url=track_url,
            is_free=False,
            quality="AAC 256kbps",
            title=full_title,
        )
