"""Amazon Music searcher (search only, no download)."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class AmazonMusicSearcher(BaseSearcher):
    """Search Amazon Music for tracks (log only, no download)."""

    name = "amazon"
    is_free = False  # Paid service

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Amazon Music via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Search via DuckDuckGo to find Amazon Music links
            search_query = f"site:music.amazon.com OR site:amazon.com/music {query}"
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
                amazon_url = self._extract_url(href)
                if amazon_url and ("music.amazon" in amazon_url or "amazon.com/music" in amazon_url):
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=amazon_url,
                        is_free=False,
                        quality="HD/Ultra HD (up to 24-bit/192kHz)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException as exc:
            logger.error("Amazon Music search failed for query '%s': %s", query, exc)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "amazon" in ddg_url:
            return ddg_url
        return None
