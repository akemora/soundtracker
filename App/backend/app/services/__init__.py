"""Business logic services for the SOUNDTRACKER API.

This package exports all service functions for use in routers.
"""

from .composer_service import get_awards, get_composer, get_filmography, list_composers
from .search_service import search_composers, search_suggestions

__all__ = [
    # Composer services
    "list_composers",
    "get_composer",
    "get_filmography",
    "get_awards",
    # Search services
    "search_composers",
    "search_suggestions",
]
