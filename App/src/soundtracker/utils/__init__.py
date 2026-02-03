"""Utility functions for SOUNDTRACKER.

Provides text manipulation and URL handling utilities.
"""

from soundtracker.utils.text import (
    clean_text,
    count_spanish_chars,
    extract_year,
    format_film_title,
    has_spanish_chars,
    is_noise_text,
    normalize_key,
    normalize_title,
    poster_filename,
    slugify,
    truncate_text,
)
from soundtracker.utils.urls import (
    BLOCKED_DOMAINS,
    build_wikipedia_url,
    clean_redirect_url,
    extract_domain,
    extract_urls_from_text,
    fetch_url_text,
    format_link,
    is_blocked_domain,
    is_image_url,
    is_wikipedia_url,
    normalize_wikipedia_url,
)

__all__ = [
    # Text utilities
    "clean_text",
    "count_spanish_chars",
    "extract_year",
    "format_film_title",
    "has_spanish_chars",
    "is_noise_text",
    "normalize_key",
    "normalize_title",
    "poster_filename",
    "slugify",
    "truncate_text",
    # URL utilities
    "BLOCKED_DOMAINS",
    "build_wikipedia_url",
    "clean_redirect_url",
    "extract_domain",
    "extract_urls_from_text",
    "fetch_url_text",
    "format_link",
    "is_blocked_domain",
    "is_image_url",
    "is_wikipedia_url",
    "normalize_wikipedia_url",
]
