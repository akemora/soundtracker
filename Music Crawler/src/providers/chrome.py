"""Chrome-based search provider."""

from __future__ import annotations

import re
import shutil
import subprocess
import urllib.parse

from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.providers.base import SearchProvider

logger = get_logger(__name__)

GOOGLE_SEARCH_URL = "https://www.google.com/search"
CHROME_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)


def _find_chrome_binary() -> str | None:
    for candidate in CHROME_CANDIDATES:
        path = shutil.which(candidate)
        if path:
            return path
    return None


def _build_search_url(query: str, site_filter: str | None = None) -> str:
    final_query = query if not site_filter else f"site:{site_filter} {query}"
    return f"{GOOGLE_SEARCH_URL}?q={urllib.parse.quote(final_query)}"


def _extract_google_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/url?"):
            match = re.search(r"[?&]q=([^&]+)", href)
            if match:
                target = urllib.parse.unquote(match.group(1))
                if target.startswith("http") and target not in urls:
                    urls.append(target)
        elif href.startswith("http") and "google.com" not in href:
            if href not in urls:
                urls.append(href)
    return urls


class ChromeProvider(SearchProvider):
    """Search provider using headless Chrome to fetch results."""

    def __init__(self) -> None:
        super().__init__()
        self.chrome_path = _find_chrome_binary()

    def search_urls(
        self, query: str, num_results: int = 5, site_filter: str | None = None
    ) -> list[str]:
        self.wait_rate_limit()
        if not self.chrome_path:
            logger.warning("Chrome not found; skipping ChromeProvider search")
            return []

        search_url = _build_search_url(query, site_filter=site_filter)
        cmd = [
            self.chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--dump-dom",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            search_url,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if result.returncode != 0:
                logger.error("Chrome search failed: %s", result.stderr, exc_info=True)
                return []
            urls = _extract_google_urls(result.stdout)
            if site_filter:
                urls = [url for url in urls if site_filter in url]
            return urls[:num_results]
        except subprocess.TimeoutExpired:
            logger.error("Chrome search timed out", exc_info=True)
        except Exception:
            logger.error("Chrome search error", exc_info=True)
        return []

    def get_rate_limit(self) -> float:
        """Return seconds to wait between requests."""
        return 2.0
