"""Jamendo searcher - Creative Commons licensed music."""

import os
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class JamendoSearcher(BaseSearcher):
    """Search Jamendo for Creative Commons licensed tracks."""

    name = "jamendo"
    is_free = True  # Creative Commons licensed
    API_URL = "https://api.jamendo.com/v3.0/tracks"

    def __init__(self, max_results: int = 3):
        self.max_results = max_results
        # Try to get client ID from environment
        self.client_id = os.environ.get("JAMENDO_CLIENT_ID")

    def search(self, track: Track) -> list[SearchResult]:
        """Search Jamendo - tries API first, falls back to web search."""
        if self.client_id:
            results = self._search_api(track)
            if results:
                return results
        return self._search_web(track)

    def _search_api(self, track: Track) -> list[SearchResult]:
        """Search via Jamendo API (requires client_id)."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            params = {
                "client_id": self.client_id,
                "format": "json",
                "limit": self.max_results,
                "search": query,
                "include": "musicinfo",
            }
            response = requests.get(self.API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                result = self._parse_api_result(track, item)
                if result:
                    results.append(result)

        except requests.RequestException as exc:
            logger.error("Jamendo API search failed for query '%s': %s", query, exc)

        return results

    def _parse_api_result(self, track: Track, item: dict) -> SearchResult | None:
        """Parse a Jamendo API result."""
        track_id = item.get("id")
        if not track_id:
            return None

        title = item.get("name", "Unknown")
        artist = item.get("artist_name", "")
        duration = item.get("duration", 0)
        audio_url = item.get("audio")  # Direct download URL
        shareurl = item.get("shareurl", f"https://www.jamendo.com/track/{track_id}")

        full_title = f"{artist} - {title}" if artist else title

        duration_str = None
        if duration:
            mins, secs = divmod(int(duration), 60)
            duration_str = f"{mins}:{secs:02d}"

        return SearchResult(
            track=track,
            source=self.name,
            url=shareurl,
            is_free=True,
            quality="MP3 (Creative Commons)",
            title=full_title,
            duration=duration_str,
        )

    def _search_web(self, track: Track) -> list[SearchResult]:
        """Fallback: search via DuckDuckGo."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            search_query = f"site:jamendo.com {query}"
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
                jamendo_url = self._extract_url(href)
                if jamendo_url and "jamendo.com" in jamendo_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=jamendo_url,
                        is_free=True,
                        quality="MP3 (Creative Commons)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException as exc:
            logger.error("Jamendo web search failed for query '%s': %s", query, exc)

        return results

    def _extract_url(self, ddg_url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        if "jamendo.com" in ddg_url:
            return ddg_url
        return None
