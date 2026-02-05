"""Musopen and IMSLP searchers - Public domain classical music."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class MusopenSearcher(BaseSearcher):
    """Search Musopen for public domain classical recordings."""

    name = "musopen"
    is_free = True  # Public domain / royalty-free

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Musopen via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            search_query = f"site:musopen.org {query}"
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
                musopen_url = self._extract_url(href)
                if musopen_url and "musopen.org" in musopen_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=musopen_url,
                        is_free=True,
                        quality="MP3/FLAC (Public Domain)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException as exc:
            logger.error("Musopen search failed for query '%s': %s", query, exc)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "musopen.org" in ddg_url:
            return ddg_url
        return None


class IMSLPSearcher(BaseSearcher):
    """Search IMSLP (International Music Score Library Project) for public domain recordings."""

    name = "imslp"
    is_free = True  # Public domain

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search IMSLP via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            search_query = f"site:imslp.org {query}"
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
                imslp_url = self._extract_url(href)
                if imslp_url and "imslp.org" in imslp_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=imslp_url,
                        is_free=True,
                        quality="MP3/FLAC (Public Domain)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException as exc:
            logger.error("IMSLP search failed for query '%s': %s", query, exc)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "imslp.org" in ddg_url:
            return ddg_url
        return None
