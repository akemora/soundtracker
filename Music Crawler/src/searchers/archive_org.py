"""Internet Archive searcher."""

import requests

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class ArchiveOrgSearcher(BaseSearcher):
    """Search Internet Archive for tracks."""

    name = "archive"
    is_free = True
    BASE_URL = "https://archive.org/advancedsearch.php"

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Internet Archive for the track."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Search for audio items
            params = {
                "q": f"{query} AND mediatype:audio",
                "fl[]": ["identifier", "title", "creator", "format"],
                "rows": self.max_results,
                "output": "json",
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            docs = data.get("response", {}).get("docs", [])
            for doc in docs:
                result = self._parse_result(track, doc)
                if result:
                    results.append(result)

        except requests.RequestException as exc:
            logger.error("Archive search failed for query '%s': %s", query, exc)

        return results

    def _parse_result(self, track: Track, doc: dict) -> SearchResult | None:
        """Parse an Internet Archive search result."""
        identifier = doc.get("identifier")
        if not identifier:
            return None

        title = doc.get("title", "Unknown")
        formats = doc.get("format", [])

        # Determine quality from available formats
        quality = "unknown"
        if isinstance(formats, list):
            if "FLAC" in formats:
                quality = "FLAC"
            elif "VBR MP3" in formats or "MP3" in formats:
                quality = "MP3"

        return SearchResult(
            track=track,
            source=self.name,
            url=f"https://archive.org/details/{identifier}",
            is_free=True,
            quality=quality,
            title=title if isinstance(title, str) else title[0] if title else "Unknown",
        )
