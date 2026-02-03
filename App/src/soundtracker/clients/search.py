"""Web search client with fallback chain.

Provides unified web search interface with multiple providers:
Perplexity API, Google Search, and DuckDuckGo.
"""

import logging
import re
import time
from typing import Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from bs4 import BeautifulSoup

from soundtracker.clients.base import BaseClient
from soundtracker.config import settings

logger = logging.getLogger(__name__)


class SearchClient(BaseClient):
    """Unified web search client with fallback chain.

    Tries multiple search providers in order:
    1. Perplexity API (if API key available)
    2. Google Search (via googlesearch-python)
    3. DuckDuckGo HTML scraping

    Example:
        client = SearchClient()
        urls = client.search("John Williams best soundtracks", num=5)
    """

    DUCKDUCKGO_ENDPOINTS = [
        "https://duckduckgo.com/html/?q=",
        "https://html.duckduckgo.com/html/?q=",
        "https://lite.duckduckgo.com/lite/?q=",
    ]

    def __init__(
        self,
        perplexity_api_key: Optional[str] = None,
        perplexity_model: Optional[str] = None,
        timeout: int = 10,
        search_pause: float = 1.2,
    ) -> None:
        """Initialize search client.

        Args:
            perplexity_api_key: Perplexity API key (optional).
            perplexity_model: Perplexity model to use.
            timeout: Request timeout in seconds.
            search_pause: Pause between Google searches.
        """
        super().__init__(
            base_url="https://api.perplexity.ai/v2",
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )
        self.perplexity_api_key = perplexity_api_key or settings.perplexity_key
        self.perplexity_model = perplexity_model or settings.pplx_model
        self._search_pause = search_pause

    @property
    def is_enabled(self) -> bool:
        """Check if web search is enabled."""
        return settings.search_web_enabled

    def health_check(self) -> bool:
        """Check if search is available.

        Returns:
            True if any search provider is available.
        """
        return self.is_enabled

    def search(self, query: str, num: int = 5) -> list[str]:
        """Search the web using fallback chain.

        Args:
            query: Search query.
            num: Maximum number of results.

        Returns:
            List of URLs.
        """
        if not self.is_enabled:
            return []

        # Try Perplexity first
        if self.perplexity_api_key:
            urls = self._search_perplexity(query, num)
            if urls:
                return urls

        # Try Google
        urls = self._search_google(query, num)
        if urls:
            return urls

        # Fall back to DuckDuckGo
        return self._search_duckduckgo(query, num)

    def _search_perplexity(self, query: str, num: int = 5) -> list[str]:
        """Search using Perplexity API.

        Args:
            query: Search query.
            num: Maximum results.

        Returns:
            List of URLs.
        """
        if not self.perplexity_api_key:
            return []

        payload = {
            "model": self.perplexity_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Devuelve resultados de busqueda con URLs fiables.",
                },
                {"role": "user", "content": query},
            ],
            "max_tokens": 128,
            "temperature": 0.2,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.debug("Perplexity search failed: %s", e)
            return []

        urls: list[str] = []

        # Try search_results field
        for item in data.get("search_results") or []:
            url = item.get("url")
            if url and url not in urls:
                urls.append(url)

        # Try citations field
        if not urls:
            for url in data.get("citations") or []:
                if url and url not in urls:
                    urls.append(url)

        # Try extracting from content
        if not urls:
            content = ""
            choices = data.get("choices") or []
            if choices:
                content = (choices[0].get("message") or {}).get("content") or ""
            for match in re.findall(r"https?://\S+", content):
                cleaned = match.strip(').,;]"\'')
                if cleaned not in urls:
                    urls.append(cleaned)

        return urls[:num]

    def _search_google(self, query: str, num: int = 5) -> list[str]:
        """Search using Google.

        Args:
            query: Search query.
            num: Maximum results.

        Returns:
            List of URLs.
        """
        try:
            from googlesearch import search

            time.sleep(self._search_pause)
            results = list(search(query, num=num, stop=num, pause=self._search_pause))

            # Deduplicate
            deduped = []
            for url in results:
                if url not in deduped:
                    deduped.append(url)

            return deduped
        except Exception as e:
            logger.debug("Google search failed: %s", e)
            return []

    def _search_duckduckgo(self, query: str, num: int = 5) -> list[str]:
        """Search using DuckDuckGo HTML scraping.

        Args:
            query: Search query.
            num: Maximum results.

        Returns:
            List of URLs.
        """
        for base_url in self.DUCKDUCKGO_ENDPOINTS:
            url = f"{base_url}{quote_plus(query)}"

            try:
                response = self.session.get(url, timeout=self.timeout)
                if not response.ok:
                    continue
                html = response.text
            except Exception:
                continue

            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            results: list[str] = []

            anchors = soup.select("a.result__a") or soup.find_all("a")
            for a in anchors:
                href = a.get("href")
                if not href or not href.startswith("http"):
                    continue

                # Handle DuckDuckGo redirects
                parsed = urlparse(href)
                if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
                    params = parse_qs(parsed.query)
                    redirect = params.get("uddg", [])
                    if redirect:
                        href = unquote(redirect[0])

                if href not in results:
                    results.append(href)

                if len(results) >= num:
                    break

            if results:
                return results

        return []

    def fetch_url_text(
        self,
        url: str,
        blocked_domains: Optional[set[str]] = None,
    ) -> str:
        """Fetch and return text content from a URL.

        Args:
            url: URL to fetch.
            blocked_domains: Set of domains to skip.

        Returns:
            HTML text content or empty string.
        """
        blocked = blocked_domains or set()
        netloc = urlparse(url).netloc.lower()

        if netloc in blocked:
            return ""

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.debug("Failed to fetch %s: %s", url, e)
            return ""

    def extract_paragraphs(
        self,
        html: str,
        max_paragraphs: int = 4,
        min_length: int = 50,
        noise_hints: Optional[list[str]] = None,
    ) -> list[str]:
        """Extract clean paragraphs from HTML.

        Args:
            html: HTML content.
            max_paragraphs: Maximum paragraphs to extract.
            min_length: Minimum paragraph length.
            noise_hints: Words indicating noise content.

        Returns:
            List of paragraph texts.
        """
        noise = noise_hints or [
            "cookie",
            "privacy",
            "subscribe",
            "newsletter",
            "sign up",
            "terms of use",
        ]

        soup = BeautifulSoup(html, "html.parser")
        paragraphs: list[str] = []

        for tag in soup.find_all(["p", "li"]):
            text = self._clean_text(tag.get_text(" ", strip=True))

            if len(text) < min_length:
                continue

            lowered = text.lower()
            if any(hint in lowered for hint in noise):
                continue

            if self._is_noise_text(text):
                continue

            paragraphs.append(text)

            if len(paragraphs) >= max_paragraphs:
                break

        return paragraphs

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
        return cleaned

    def _is_noise_text(self, text: str) -> bool:
        """Check if text appears to be noise/navigation."""
        letters = [ch for ch in text if ch.isalpha()]
        if letters:
            upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
            if upper_ratio > 0.6 and len(text.split()) > 6:
                return True

        if text == text.upper() and len(text.split()) > 8:
            return True

        if len(text.split()) > 20 and text.count(".") == 0 and text.count(",") == 0:
            return True

        return False
