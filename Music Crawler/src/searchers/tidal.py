"""Tidal searcher (search only, no download) - Hi-res audio service."""

from src.models.track import SearchResult, Track
from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider
from src.searchers.base import BaseSearcher


class TidalSearcher(BaseSearcher):
    """Search Tidal for tracks (log only, no download)."""

    name = "tidal"
    is_free = False  # Premium service

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Tidal via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="tidal.com",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=False,
                quality="MQA/FLAC (up to 24-bit/192kHz)",
                title=url,
            )
            results.append(result)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "tidal.com" in ddg_url:
            return ddg_url
        return None


class QobuzSearcher(BaseSearcher):
    """Search Qobuz for tracks (log only) - Hi-res audio specialist."""

    name = "qobuz"
    is_free = False  # Premium service

    def __init__(self, provider: SearchProvider | None = None, max_results: int = 3):
        self.provider = provider or ChromeProvider()
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Qobuz via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        urls = self.provider.search_urls(
            query,
            num_results=self.max_results,
            site_filter="qobuz.com",
        )
        for url in urls:
            result = SearchResult(
                track=track,
                source=self.name,
                url=url,
                is_free=False,
                quality="Hi-Res FLAC (up to 24-bit/192kHz)",
                title=url,
            )
            results.append(result)

        return results
