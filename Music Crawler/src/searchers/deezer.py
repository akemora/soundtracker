"""Deezer searcher - has free API without authentication."""

import requests

from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher


class DeezerSearcher(BaseSearcher):
    """Search Deezer for tracks (log only, no download)."""

    name = "deezer"
    is_free = False  # Paid service for full tracks
    API_URL = "https://api.deezer.com/search"

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Deezer API (no authentication required for search)."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            params = {
                "q": query,
                "limit": self.max_results,
            }
            response = requests.get(
                self.API_URL,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("data", []):
                result = self._parse_result(track, item)
                if result:
                    results.append(result)

        except requests.RequestException:
            pass

        return results

    def _parse_result(self, track: Track, item: dict) -> SearchResult | None:
        """Parse a Deezer search result."""
        track_link = item.get("link")
        if not track_link:
            return None

        title = item.get("title", "Unknown")
        artist = item.get("artist", {}).get("name", "")
        album = item.get("album", {}).get("title", "")
        duration = item.get("duration", 0)

        full_title = f"{artist} - {title}"
        if album:
            full_title += f" ({album})"

        duration_str = None
        if duration:
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"

        return SearchResult(
            track=track,
            source=self.name,
            url=track_link,
            is_free=False,
            quality="FLAC (HiFi) / 320kbps MP3",
            title=full_title,
            duration=duration_str,
        )
