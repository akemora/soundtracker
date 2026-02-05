"""Free Music Archive searcher - Creative Commons licensed music."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher


class FreeMusiceArchiveSearcher(BaseSearcher):
    """Search Free Music Archive for Creative Commons licensed tracks."""

    name = "fma"
    is_free = True  # Creative Commons licensed

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Free Music Archive via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="freemusicarchive.org",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=True,
                quality="MP3/FLAC (Creative Commons)",
                title=url,
            )
            results.append(result)

        return results
