"""URL handling utilities.

Provides functions for URL parsing, validation, and formatting.
"""

import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from soundtracker.config import settings

logger = logging.getLogger(__name__)

# Domains to block from web fetching
BLOCKED_DOMAINS = {
    "shutterstock.com",
    "letterboxd.com",
    "remix.berklee.edu",
    "movieposters.com",
    "etsy.com",
    "impawards.com",
}


def is_blocked_domain(url: str) -> bool:
    """Check if URL is from a blocked domain.

    Args:
        url: URL to check.

    Returns:
        True if domain is blocked.
    """
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc in BLOCKED_DOMAINS
    except Exception:
        return False


def is_image_url(url: str) -> bool:
    """Check if URL appears to be an image.

    Args:
        url: URL to check.

    Returns:
        True if URL looks like an image.
    """
    lower = url.lower()
    return any(ext in lower for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"])


def fetch_url_text(
    url: str,
    headers: Optional[dict[str, str]] = None,
    timeout: Optional[int] = None,
) -> str:
    """Fetch text content from a URL.

    Args:
        url: URL to fetch.
        headers: Optional request headers.
        timeout: Request timeout in seconds.

    Returns:
        Response text or empty string on failure.
    """
    if is_blocked_domain(url):
        return ""

    timeout = timeout or settings.request_timeout
    headers = headers or {"User-Agent": "Soundtracker/2.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.debug("Failed to fetch %s: %s", url, exc)
        return ""


def format_link(path: str, base: Path) -> str:
    """Format a path as a relative link.

    Args:
        path: File path or URL.
        base: Base path for relative links.

    Returns:
        Relative path or original URL.
    """
    if path.startswith("http://") or path.startswith("https://"):
        return path
    local = Path(path)
    if local.exists():
        try:
            return str(local.relative_to(base))
        except ValueError:
            return str(local)
    return path


def extract_domain(url: str) -> str:
    """Extract domain from URL.

    Args:
        url: URL to parse.

    Returns:
        Domain name or 'unknown'.
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() or "unknown"
    except Exception:
        return "unknown"


def is_wikipedia_url(url: str) -> bool:
    """Check if URL is a Wikipedia page.

    Args:
        url: URL to check.

    Returns:
        True if Wikipedia URL.
    """
    domain = extract_domain(url)
    return "wikipedia.org" in domain or "wikidata.org" in domain


def normalize_wikipedia_url(src: str) -> str:
    """Normalize a Wikipedia image URL.

    Args:
        src: Image src attribute.

    Returns:
        Full URL.
    """
    if src.startswith("//"):
        return f"https:{src}"
    if src.startswith("/"):
        return f"https://en.wikipedia.org{src}"
    return src


def build_wikipedia_url(title: str, lang: str = "en") -> str:
    """Build Wikipedia page URL from title.

    Args:
        title: Page title.
        lang: Wikipedia language code.

    Returns:
        Wikipedia URL.
    """
    return f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"


def clean_redirect_url(href: str) -> str:
    """Clean a search redirect URL.

    Args:
        href: Potentially redirected URL.

    Returns:
        Cleaned URL.
    """
    from urllib.parse import parse_qs, unquote

    parsed = urlparse(href)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        params = parse_qs(parsed.query)
        redirect = params.get("q") or params.get("url") or []
        if redirect:
            return unquote(redirect[0])
    return href


def extract_urls_from_text(text: str) -> list[str]:
    """Extract URLs from text.

    Args:
        text: Text containing URLs.

    Returns:
        List of URLs found.
    """
    pattern = r"https?://[^\s<>\"\')\]]+(?=[.,;:!?\s<>\"\')\]]|$)"
    urls = []
    for match in re.findall(pattern, text):
        cleaned = match.strip(").,;]\"'")
        if cleaned and cleaned not in urls:
            urls.append(cleaned)
    return urls
