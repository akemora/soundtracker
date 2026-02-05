"""Musopen and IMSLP searchers - Public domain classical music."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.duckduckgo import DuckDuckGoProvider
from src.searchers.base import BaseSearcher


class MusopenSearcher(BaseSearcher):
    """Search Musopen for public domain classical recordings."""

    name = "musopen"
    is_free = True  # Public domain / royalty-free

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or DuckDuckGoProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Musopen via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="musopen.org",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=True,
                quality="MP3/FLAC (Public Domain)",
                title=url,
            )
            results.append(result)

        return results


class IMSLPSearcher(BaseSearcher):
    """Search IMSLP (International Music Score Library Project) for public domain recordings."""

    name = "imslp"
    is_free = True  # Public domain

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or DuckDuckGoProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search IMSLP via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="imslp.org",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=True,
                quality="MP3/FLAC (Public Domain)",
                title=url,
            )
            results.append(result)

        return results
