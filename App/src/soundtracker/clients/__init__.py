"""API clients for external services.

This module provides clients for various external APIs used by SOUNDTRACKER:
- TMDB (The Movie Database)
- Wikipedia
- Wikidata
- YouTube
- Spotify
- Web Search (Perplexity, Google, DuckDuckGo)
"""

from soundtracker.clients.base import BaseClient
from soundtracker.clients.search import SearchClient
from soundtracker.clients.spotify import SpotifyClient
from soundtracker.clients.tmdb import TMDBClient
from soundtracker.clients.wikidata import WikidataClient
from soundtracker.clients.wikipedia import MultiLangWikipediaClient, WikipediaClient
from soundtracker.clients.youtube import YouTubeClient

__all__ = [
    "BaseClient",
    "MultiLangWikipediaClient",
    "SearchClient",
    "SpotifyClient",
    "TMDBClient",
    "WikidataClient",
    "WikipediaClient",
    "YouTubeClient",
]
