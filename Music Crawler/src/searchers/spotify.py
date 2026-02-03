"""Spotify searcher (search only, no download)."""

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher


class SpotifySearcher(BaseSearcher):
    """Search Spotify for tracks (log only, no download)."""

    name = "spotify"
    is_free = False  # Paid service

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search Spotify via web search (no API key needed)."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Search via DuckDuckGo to find Spotify links
            search_query = f"site:open.spotify.com {query}"
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
                # Extract actual URL from DuckDuckGo redirect
                spotify_url = self._extract_spotify_url(href)
                if spotify_url and "open.spotify.com" in spotify_url:
                    title = link.get_text(strip=True)
                    result = SearchResult(
                        track=track,
                        source=self.name,
                        url=spotify_url,
                        is_free=False,
                        quality="320kbps (Premium)",
                        title=title,
                    )
                    results.append(result)
                    if len(results) >= self.max_results:
                        break

        except requests.RequestException:
            pass

        return results

    def _extract_spotify_url(self, ddg_url: str) -> str | None:
        """Extract actual Spotify URL from DuckDuckGo redirect."""
        # DuckDuckGo uses uddg parameter for actual URL
        match = re.search(r"uddg=([^&]+)", ddg_url)
        if match:
            return urllib.parse.unquote(match.group(1))
        # Fallback: try to find spotify.com directly
        if "open.spotify.com" in ddg_url:
            return ddg_url
        return None


class ITunesSearcher(BaseSearcher):
    """Search iTunes/Apple Music for tracks (log only)."""

    name = "itunes"
    is_free = False
    SEARCH_URL = "https://itunes.apple.com/search"

    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search iTunes Store API."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            params = {
                "term": query,
                "media": "music",
                "limit": self.max_results,
            }
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                result = self._parse_result(track, item)
                if result:
                    results.append(result)

        except requests.RequestException:
            pass

        return results

    def _parse_result(self, track: Track, item: dict) -> SearchResult | None:
        """Parse an iTunes search result."""
        track_url = item.get("trackViewUrl")
        if not track_url:
            return None

        title = item.get("trackName", "Unknown")
        artist = item.get("artistName", "")
        album = item.get("collectionName", "")

        full_title = f"{artist} - {title}"
        if album:
            full_title += f" ({album})"

        return SearchResult(
            track=track,
            source=self.name,
            url=track_url,
            is_free=False,
            quality="AAC 256kbps",
            title=full_title,
        )
