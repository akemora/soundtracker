"""SoundCloud searcher (some free content available)."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher


class SoundCloudSearcher(BaseSearcher):
    """Search SoundCloud for tracks (some free downloads available)."""

    name = "soundcloud"
    is_free = True  # Some tracks are free to download

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search SoundCloud via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="soundcloud.com",
        )
        for url in urls:
            if any(skip in url for skip in ["/sets/", "/likes", "/followers", "/following"]):
                continue
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=True,  # May have free download
                quality="MP3 128-320kbps",
                title=url,
            )
            results.append(result)

        return results
