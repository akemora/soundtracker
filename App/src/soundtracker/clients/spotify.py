"""Spotify Web API client.

Provides access to Spotify API for searching soundtrack popularity.
"""

import base64
import logging
import time
from typing import Optional

from soundtracker.cache import FileCache
from soundtracker.clients.base import BaseClient
from soundtracker.config import settings

logger = logging.getLogger(__name__)


class SpotifyClient(BaseClient):
    """Client for Spotify Web API.

    Handles OAuth2 client credentials flow and provides methods
    to search for soundtracks and get popularity metrics.

    Example:
        client = SpotifyClient(client_id="id", client_secret="secret")
        popularity = client.search_popularity("John Williams", "Star Wars")
    """

    AUTH_URL = "https://accounts.spotify.com/api/token"
    API_URL = "https://api.spotify.com/v1"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cache: Optional[FileCache] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize Spotify client.

        Args:
            client_id: Spotify API client ID.
            client_secret: Spotify API client secret.
            cache: Optional cache for responses.
            timeout: Request timeout in seconds.
        """
        super().__init__(
            base_url=self.API_URL,
            timeout=timeout,
            headers={"User-Agent": "Soundtracker/2.0"},
        )
        self.client_id = client_id or settings.spotify_client_id
        self.client_secret = client_secret or settings.spotify_client_secret
        self.cache = cache
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    @property
    def is_available(self) -> bool:
        """Check if credentials are configured and enabled."""
        return (
            settings.spotify_enabled
            and bool(self.client_id)
            and bool(self.client_secret)
        )

    def _get_token(self) -> Optional[str]:
        """Get OAuth2 access token, refreshing if needed.

        Returns:
            Access token or None on error.
        """
        if not self.is_available:
            return None

        now = time.time()
        if self._token and self._token_expires_at > now + 60:
            return self._token

        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        basic = base64.b64encode(credentials).decode("utf-8")

        try:
            response = self.session.post(
                self.AUTH_URL,
                data={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {basic}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning("Failed to get Spotify token: %s", e)
            return None

        token = data.get("access_token")
        expires_in = data.get("expires_in", 0)

        if token:
            self._token = token
            self._token_expires_at = now + int(expires_in)
            logger.debug("Obtained Spotify token, expires in %d seconds", expires_in)

        return token

    def health_check(self) -> bool:
        """Check if Spotify API is available.

        Returns:
            True if API responds successfully.
        """
        token = self._get_token()
        if not token:
            return False

        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self.session.get(
                f"{self.API_URL}/browse/categories",
                headers=headers,
                params={"limit": "1"},
                timeout=self.timeout,
            )
            return response.status_code == 200
        except Exception:
            return False

    def search_popularity(
        self,
        composer: str,
        title: str,
    ) -> Optional[float]:
        """Search for soundtrack and get popularity score.

        Args:
            composer: Composer name.
            title: Film/soundtrack title.

        Returns:
            Popularity score (0-100) or None.
        """
        if not self.is_available or not title:
            return None

        token = self._get_token()
        if not token:
            return None

        # Check cache
        if self.cache:
            cache_key = f"spotify|{composer}|{title}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached.get("popularity")

        queries = [
            f'track:"{title}" soundtrack {composer}',
            f'album:"{title}" soundtrack {composer}',
            f'"{title}" "{composer}" soundtrack',
            f'"{title}" soundtrack',
        ]

        headers = {"Authorization": f"Bearer {token}"}
        best: Optional[float] = None

        for query in queries:
            try:
                response = self.session.get(
                    f"{self.API_URL}/search",
                    headers=headers,
                    params={"q": query, "type": "track", "limit": "5"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.debug("Spotify search failed: %s", e)
                continue

            for item in data.get("tracks", {}).get("items", []):
                pop = item.get("popularity")
                if pop is None:
                    continue
                if best is None or pop > best:
                    best = float(pop)

            if best is not None:
                break

        # Cache result
        if self.cache and best is not None:
            self.cache.set(f"spotify|{composer}|{title}", {"popularity": best})

        return best

    def search_artist(self, name: str) -> Optional[dict]:
        """Search for an artist.

        Args:
            name: Artist name.

        Returns:
            Artist data or None.
        """
        if not self.is_available:
            return None

        token = self._get_token()
        if not token:
            return None

        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self.session.get(
                f"{self.API_URL}/search",
                headers=headers,
                params={"q": name, "type": "artist", "limit": "1"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning("Spotify artist search failed: %s", e)
            return None

        items = data.get("artists", {}).get("items", [])
        return items[0] if items else None

    def get_artist_top_tracks(
        self,
        artist_id: str,
        market: str = "ES",
    ) -> list[dict]:
        """Get top tracks for an artist.

        Args:
            artist_id: Spotify artist ID.
            market: Country code for market.

        Returns:
            List of track data.
        """
        if not self.is_available:
            return []

        token = self._get_token()
        if not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = self.session.get(
                f"{self.API_URL}/artists/{artist_id}/top-tracks",
                headers=headers,
                params={"market": market},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning("Spotify top tracks failed: %s", e)
            return []

        return data.get("tracks", [])
