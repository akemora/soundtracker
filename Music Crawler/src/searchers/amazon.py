"""Amazon Music searcher (search only, no download)."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher


class AmazonMusicSearcher(BaseSearcher):
    """Search Amazon Music for tracks (log only, no download)."""

    name = "amazon"
    is_free = False  # Paid service

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Amazon Music via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="amazon.com",
        )
        for url in urls:
            if "music.amazon" not in url and "amazon.com/music" not in url:
                continue
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=False,
                quality="HD/Ultra HD (up to 24-bit/192kHz)",
                title=url,
            )
            results.append(result)

        return results
