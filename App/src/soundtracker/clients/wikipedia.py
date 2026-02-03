"""Wikipedia API client.

Provides access to Wikipedia API for article content and images.
"""

import logging
from typing import Optional

from soundtracker.clients.base import BaseClient

logger = logging.getLogger(__name__)


class WikipediaClient(BaseClient):
    """Client for Wikipedia API.

    Provides methods to search for articles, get extracts,
    and retrieve images from Wikipedia in multiple languages.

    Example:
        client = WikipediaClient()
        title = client.search_title("John Williams composer")
        extract = client.get_extract("John Williams (composer)")
    """

    def __init__(
        self,
        lang: str = "en",
        timeout: int = 10,
    ) -> None:
        """Initialize Wikipedia client.

        Args:
            lang: Wikipedia language code (e.g., 'en', 'es').
            timeout: Request timeout in seconds.
        """
        base_url = f"https://{lang}.wikipedia.org/w/api.php"
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )
        self.lang = lang

    def health_check(self) -> bool:
        """Check if Wikipedia API is available.

        Returns:
            True if API responds successfully.
        """
        result = self._get("", {"action": "query", "meta": "siteinfo", "format": "json"})
        return result is not None

    def search_title(self, query: str, limit: int = 1) -> Optional[str]:
        """Search for a Wikipedia article title.

        Args:
            query: Search query.
            limit: Maximum number of results.

        Returns:
            Best matching article title or None.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "1",
            "srlimit": str(limit),
        }

        data = self._get("", params)
        if not data:
            return None

        results = data.get("query", {}).get("search", [])
        if not results:
            return None

        return results[0].get("title")

    def get_page_url(self, title: str) -> str:
        """Get Wikipedia page URL for a title.

        Args:
            title: Article title.

        Returns:
            Full Wikipedia URL.
        """
        return f"https://{self.lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"

    def fetch_html(self, query: str) -> Optional[str]:
        """Fetch HTML content for an article.

        Args:
            query: Search query or exact title.

        Returns:
            HTML content or None.
        """
        title = self.search_title(query)
        if not title:
            return None

        url = self.get_page_url(title)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning("Failed to fetch Wikipedia HTML: %s", e)
            return None

    def get_extract(self, query: str, intro_only: bool = True) -> str:
        """Get plain text extract from an article.

        Args:
            query: Search query or exact title.
            intro_only: If True, only return the intro section.

        Returns:
            Article extract text or empty string.
        """
        title = self.search_title(query)
        if not title:
            return ""

        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "format": "json",
            "titles": title,
        }
        if intro_only:
            params["exintro"] = "1"

        data = self._get("", params)
        if not data:
            return ""

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            extract = page.get("extract")
            if extract:
                return extract.strip()

        return ""

    def get_image_url(self, query: str) -> Optional[str]:
        """Get main image URL from an article.

        Args:
            query: Search query or exact title.

        Returns:
            Image URL or None.
        """
        title = self.search_title(query)
        if not title:
            return None

        params = {
            "action": "query",
            "prop": "pageimages",
            "format": "json",
            "titles": title,
            "piprop": "original",
        }

        data = self._get("", params)
        if not data:
            return None

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            original = page.get("original", {})
            source = original.get("source")
            if source:
                return source

        return None

    def get_infobox_image(self, query: str) -> Optional[str]:
        """Get infobox image URL (typically a portrait).

        Args:
            query: Search query or exact title.

        Returns:
            Image URL or None.
        """
        title = self.search_title(query)
        if not title:
            return None

        params = {
            "action": "query",
            "prop": "pageimages",
            "format": "json",
            "titles": title,
            "pithumbsize": "500",
        }

        data = self._get("", params)
        if not data:
            return None

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            thumbnail = page.get("thumbnail", {})
            source = thumbnail.get("source")
            if source:
                return source

        return None


class MultiLangWikipediaClient:
    """Wikipedia client with multi-language support.

    Tries multiple language versions to find content.

    Example:
        client = MultiLangWikipediaClient(["es", "en"])
        extract = client.get_extract("John Williams compositor")
    """

    def __init__(self, languages: Optional[list[str]] = None, timeout: int = 10) -> None:
        """Initialize multi-language client.

        Args:
            languages: List of language codes to try, in order.
            timeout: Request timeout in seconds.
        """
        self.languages = languages or ["es", "en"]
        self.clients = {lang: WikipediaClient(lang, timeout) for lang in self.languages}

    def search_title(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """Search for article title in multiple languages.

        Args:
            query: Search query.

        Returns:
            Tuple of (title, language) or (None, None).
        """
        for lang in self.languages:
            title = self.clients[lang].search_title(query)
            if title:
                return title, lang
        return None, None

    def get_extract(self, query: str, intro_only: bool = True) -> str:
        """Get extract from first language with results.

        Args:
            query: Search query.
            intro_only: If True, only return intro.

        Returns:
            Article extract or empty string.
        """
        for lang in self.languages:
            extract = self.clients[lang].get_extract(query, intro_only)
            if extract:
                return extract
        return ""

    def get_image_url(self, query: str) -> Optional[str]:
        """Get image from first language with results.

        Args:
            query: Search query.

        Returns:
            Image URL or None.
        """
        for lang in self.languages:
            url = self.clients[lang].get_image_url(query)
            if url:
                return url
        return None
