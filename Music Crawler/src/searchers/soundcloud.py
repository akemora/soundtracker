"""SoundCloud searcher (some free content available)."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class SoundCloudSearcher(BaseSearcher):
    """Search SoundCloud for tracks (some free downloads available)."""

    name = "soundcloud"
    is_free = True  # Some tracks are free to download

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search SoundCloud via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Search via DuckDuckGo
            search_query = f"site:soundcloud.com {query}"
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", class_="result__a", limit=self.max_results * 2)

            for link in links:
                href = link.get("href", "")
                sc_url = self._extract_url(href)
                if sc_url and "soundcloud.com" in sc_url:
                    # Skip non-track URLs
                    if any(skip in sc_url for skip in ["/sets/", "/likes", "/followers", "/following"]):
                        continue
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=sc_url,
                        is_free=True,  # May have free download
                        quality="MP3 128-320kbps",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException as exc:
            logger.error("SoundCloud search failed for query '%s': %s", query, exc, exc_info=True)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "soundcloud.com" in ddg_url:
            return ddg_url
        return None
