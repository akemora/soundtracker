"""Business logic services for the SOUNDTRACKER API.

This package exports all service functions for use in routers.
"""

from .composer_service import (
    get_awards,
    get_composer,
    get_composer_filter_options,
    get_filmography,
    list_composers,
)
from .search_service import search_composers, search_suggestions
from .playlist_service import get_playlist_by_composer, regenerate_playlist
from .music_service import get_tracks_by_composer

__all__ = [
    # Composer services
    "list_composers",
    "get_composer",
    "get_filmography",
    "get_awards",
    "get_composer_filter_options",
    # Search services
    "search_composers",
    "search_suggestions",
    # Music services
    "get_tracks_by_composer",
    # Playlist services
    "get_playlist_by_composer",
    "regenerate_playlist",
]
