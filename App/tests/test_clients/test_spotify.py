"""Tests for soundtracker.clients.spotify."""

from unittest.mock import Mock

from soundtracker.clients.spotify import SpotifyClient
from soundtracker.config import settings


class DummyCache:
    """Simple in-memory cache for testing."""

    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: dict) -> None:
        self.data[key] = value


class TestSpotifyClient:
    """Tests for SpotifyClient."""

    def test_is_available_false_without_credentials(self, monkeypatch) -> None:
        """is_available should be False when credentials missing."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        monkeypatch.setattr(settings, "spotify_client_id", None)
        monkeypatch.setattr(settings, "spotify_client_secret", None)
        client = SpotifyClient(client_id=None, client_secret=None)

        assert client.is_available is False

    def test_get_token_returns_token(self, monkeypatch) -> None:
        """_get_token should return access token and cache it."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        client = SpotifyClient(client_id="id", client_secret="secret")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"access_token": "token", "expires_in": 3600})
        client.session.post = Mock(return_value=response)

        token = client._get_token()

        assert token == "token"
        assert client._token == "token"

    def test_search_popularity_returns_cached_value(self, monkeypatch) -> None:
        """search_popularity should use cached popularity when present."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        cache = DummyCache()
        cache.set("spotify|John Williams|Star Wars", {"popularity": 77})
        client = SpotifyClient(client_id="id", client_secret="secret", cache=cache)
        client._get_token = Mock(return_value="token")

        result = client.search_popularity("John Williams", "Star Wars")

        assert result == 77

    def test_search_popularity_returns_best_score(self, monkeypatch) -> None:
        """search_popularity should return highest popularity from results."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        cache = DummyCache()
        client = SpotifyClient(client_id="id", client_secret="secret", cache=cache)
        client._get_token = Mock(return_value="token")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={
                "tracks": {"items": [{"popularity": 20}, {"popularity": 55}]}
            }
        )
        client.session.get = Mock(return_value=response)

        result = client.search_popularity("John Williams", "Star Wars")

        assert result == 55.0
        assert cache.get("spotify|John Williams|Star Wars") == {"popularity": 55.0}

    def test_search_artist_returns_item(self, monkeypatch) -> None:
        """search_artist should return the first artist item."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        client = SpotifyClient(client_id="id", client_secret="secret")
        client._get_token = Mock(return_value="token")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"artists": {"items": [{"id": "a1"}]}})
        client.session.get = Mock(return_value=response)

        artist = client.search_artist("John Williams")

        assert artist == {"id": "a1"}

    def test_get_artist_top_tracks_returns_list(self, monkeypatch) -> None:
        """get_artist_top_tracks should return tracks list."""
        monkeypatch.setattr(settings, "spotify_enabled", True)
        client = SpotifyClient(client_id="id", client_secret="secret")
        client._get_token = Mock(return_value="token")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"tracks": [{"id": "t1"}]})
        client.session.get = Mock(return_value=response)

        tracks = client.get_artist_top_tracks("a1", market="ES")

        assert tracks == [{"id": "t1"}]
