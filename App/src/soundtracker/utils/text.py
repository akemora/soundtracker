"""Text manipulation utilities.

Provides functions for text cleaning, normalization, and validation.
"""

import re
from typing import Optional


# Characters and hints for language detection
SPANISH_CHARS = set("áéíóúñü¿¡")
NOISE_HINTS = [
    "cookie",
    "privacy",
    "subscribe",
    "newsletter",
    "sign up",
    "terms of use",
    "otras secciones",
    "bso news",
    "news",
    "entrevistas",
    "reviews",
    "miniaturas",
    "soundtracks",
    "festivales",
    "conciertos",
    "participaciones",
    "menu",
]


def slugify(name: str) -> str:
    """Convert a name to a URL-safe slug.

    Args:
        name: Name to convert.

    Returns:
        Lowercase slug with underscores.
    """
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return slug.strip("_") or "composer"


def clean_text(text: str) -> str:
    """Clean and normalize text.

    Collapses whitespace and fixes punctuation spacing.

    Args:
        text: Text to clean.

    Returns:
        Cleaned text.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return cleaned


def truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to maximum characters at word boundary.

    Args:
        text: Text to truncate.
        max_chars: Maximum length.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit(" ", 1)[0]
    return trimmed.rstrip() + "..."


def is_noise_text(text: str) -> bool:
    """Check if text appears to be noise/boilerplate.

    Args:
        text: Text to check.

    Returns:
        True if text appears to be noise.
    """
    letters = [ch for ch in text if ch.isalpha()]
    if letters:
        upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
        if upper_ratio > 0.6 and len(text.split()) > 6:
            return True
    if text == text.upper() and len(text.split()) > 8:
        return True
    if len(text.split()) > 20 and text.count(".") == 0 and text.count(",") == 0:
        return True
    lowered = text.lower()
    if any(hint in lowered for hint in NOISE_HINTS):
        return True
    return False


def normalize_title(text: str) -> Optional[str]:
    """Normalize a film title from extracted text.

    Args:
        text: Raw title text.

    Returns:
        Normalized title or None if invalid.
    """
    cleaned = re.sub(r"^\d+\.?\s*", "", text.strip())
    cleaned = re.sub(r"\s*\(\d{4}\)\s*", "", cleaned).strip(" .-–:;")
    if not cleaned or len(cleaned) < 2 or len(cleaned) > 90:
        return None
    return cleaned


def normalize_key(title: str) -> str:
    """Normalize title to a comparison key.

    Args:
        title: Title to normalize.

    Returns:
        Lowercase alphanumeric key.
    """
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def poster_filename(title: str, year: Optional[int] = None) -> str:
    """Generate a poster filename from title.

    Args:
        title: Film title.
        year: Optional release year.

    Returns:
        Filename for the poster.
    """
    base = slugify(title or "poster")
    if base == "composer":
        base = "poster"
    if year:
        return f"poster_{base}_{year}.jpg"
    return f"poster_{base}.jpg"


def format_film_title(
    original_title: Optional[str],
    title_es: Optional[str] = None,
) -> str:
    """Format a film title with Spanish title if different.

    Args:
        original_title: Original title.
        title_es: Spanish title.

    Returns:
        Formatted title string.
    """
    original = (original_title or "").strip()
    spanish = (title_es or "").strip()

    if not original and spanish:
        original = spanish
    if original and not spanish:
        spanish = original

    if original and spanish and original.lower() != spanish.lower():
        return f"{original} (Título en España: {spanish})"
    return original or spanish


def extract_year(text: str) -> Optional[int]:
    """Extract a year from text.

    Args:
        text: Text containing a year.

    Returns:
        Year as integer or None.
    """
    match = re.search(r"(19|20)\d{2}", text)
    if match:
        year = int(match.group())
        if 1900 <= year <= 2030:
            return year
    return None


def has_spanish_chars(text: str) -> bool:
    """Check if text contains Spanish-specific characters.

    Args:
        text: Text to check.

    Returns:
        True if Spanish characters found.
    """
    return any(ch in SPANISH_CHARS for ch in text)


def count_spanish_chars(text: str) -> int:
    """Count Spanish-specific characters in text.

    Args:
        text: Text to check.

    Returns:
        Count of Spanish characters.
    """
    return sum(1 for ch in text if ch in SPANISH_CHARS)
