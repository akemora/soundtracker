"""Tidal searcher (search only, no download) - Hi-res audio service."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher


class TidalSearcher(BaseSearcher):
    """Search Tidal for tracks (log only, no download)."""

    name = "tidal"
    is_free = False  # Premium service

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Tidal via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Search via DuckDuckGo
            search_query = f"site:tidal.com {query}"
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
                tidal_url = self._extract_url(href)
                if tidal_url and "tidal.com" in tidal_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=tidal_url,
                        is_free=False,
                        quality="MQA/FLAC (up to 24-bit/192kHz)",
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
        if "tidal.com" in ddg_url:
            return ddg_url
        return None


class QobuzSearcher(BaseSearcher):
    """Search Qobuz for tracks (log only) - Hi-res audio specialist."""

    name = "qobuz"
    is_free = False  # Premium service

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Qobuz via web search."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            search_query = f"site:qobuz.com {query}"
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
                qobuz_url = self._extract_url(href)
                if qobuz_url and "qobuz.com" in qobuz_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=qobuz_url,
                        is_free=False,
                        quality="Hi-Res FLAC (up to 24-bit/192kHz)",
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
        if "qobuz.com" in ddg_url:
            return ddg_url
        return None
