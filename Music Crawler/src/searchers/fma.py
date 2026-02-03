"""Free Music Archive searcher - Creative Commons licensed music."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher


class FreeMusiceArchiveSearcher(BaseSearcher):
    """Search Free Music Archive for Creative Commons licensed tracks."""

    name = "fma"
    is_free = True  # Creative Commons licensed

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Free Music Archive via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            search_query = f"site:freemusicarchive.org {query}"
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
                fma_url = self._extract_url(href)
                if fma_url and "freemusicarchive.org" in fma_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=fma_url,
                        is_free=True,
                        quality="MP3/FLAC (Creative Commons)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException:
            pass

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "freemusicarchive.org" in ddg_url:
            return ddg_url
        return None
