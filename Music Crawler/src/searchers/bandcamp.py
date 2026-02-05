"""Bandcamp searcher (search only, no download)."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher


class BandcampSearcher(BaseSearcher):
    """Search Bandcamp for tracks (log only - mix of free and paid)."""

    name = "bandcamp"
    is_free = False  # Most content is paid, some free

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Bandcamp via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="bandcamp.com",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=False,  # Could be free, check manually
                quality="FLAC/WAV/MP3 (varies)",
                title=url,
            )
            results.append(result)

        return results
