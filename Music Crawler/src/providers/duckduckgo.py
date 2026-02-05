"""DuckDuckGo HTML scraping provider."""

from __future__ import annotations

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.providers.base import SearchProvider

logger = get_logger(__name__)

DDG_BASE_URL = "https://html.duckduckgo.com/html/"


def _extract_url(ddg_url: str) -> str | None:
    match = re.search(r"uddg=([^&]+)", ddg_url)
    if match:
        return urllib.parse.unquote(match.group(1))
    if ddg_url.startswith("http"):
        return ddg_url
    return None


def _ddg_search(query: str, num_results: int) -> list[str]:
    encoded_query = urllib.parse.quote(query)
    url = f"{DDG_BASE_URL}?q={encoded_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", class_="result__a", limit=num_results * 2)

    results: list[str] = []
    for link in links:
        href = link.get("href", "")
        actual_url = _extract_url(href)
        if actual_url and actual_url not in results:
            results.append(actual_url)
        if len(results) >= num_results:
            break
    return results


class DuckDuckGoProvider(SearchProvider):
    """Fallback search provider using DuckDuckGo HTML."""

    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        search_query = query if not site_filter else f"site:{site_filter} {query}"
        urls = _ddg_search(search_query, num_results)
        if site_filter:
            urls = [url for url in urls if site_filter in url]
        return urls[:num_results]

    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        return 2.0
