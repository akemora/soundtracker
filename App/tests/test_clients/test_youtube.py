"""Tests for soundtracker.clients.youtube."""

from unittest.mock import Mock

from soundtracker.clients.youtube import YouTubeClient
from soundtracker.config import settings


class DummyCache:
    """Simple in-memory cache for testing."""

    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: dict) -> None:
        self.data[key] = value


class TestYouTubeClient:
    """Tests for YouTubeClient."""

    def test_is_available_false_without_key(self, monkeypatch) -> None:
        """is_available should be False without API key."""
        monkeypatch.setattr(settings, "youtube_enabled", True)
        client = YouTubeClient(api_key=None)

        assert client.is_available is False

    def test_search_views_returns_cached_value(self, monkeypatch) -> None:
        """search_views should use cached value when present."""
        monkeypatch.setattr(settings, "youtube_enabled", True)
        cache = DummyCache()
        cache.set("youtube|John Williams|Star Wars", {"views": 123})
        client = YouTubeClient(api_key="key", cache=cache)
        client._get = Mock()

        views = client.search_views("John Williams", "Star Wars")

        assert views == 123
        client._get.assert_not_called()

    def test_search_views_returns_max_views(self, monkeypatch) -> None:
        """search_views should return max view count from videos."""
        monkeypatch.setattr(settings, "youtube_enabled", True)
        cache = DummyCache()
        client = YouTubeClient(api_key="key", cache=cache)
        client._get = Mock(
            side_effect=[
                {
                    "items": [
                        {"id": {"videoId": "id1"}},
                        {"id": {"videoId": "id2"}},
                    ]
                },
                {
                    "items": [
                        {"statistics": {"viewCount": "100"}},
                        {"statistics": {"viewCount": "250"}},
                    ]
                },
            ]
        )

        views = client.search_views("John Williams", "Star Wars")

        assert views == 250
        assert cache.get("youtube|John Williams|Star Wars") == {"views": 250}

    def test_get_video_views_returns_count(self, monkeypatch) -> None:
        """get_video_views should parse view count."""
        monkeypatch.setattr(settings, "youtube_enabled", True)
        client = YouTubeClient(api_key="key")
        client._get = Mock(
            return_value={"items": [{"statistics": {"viewCount": "42"}}]}
        )

        assert client.get_video_views("id1") == 42

    def test_get_video_views_returns_none_when_disabled(self, monkeypatch) -> None:
        """get_video_views should return None when API disabled."""
        monkeypatch.setattr(settings, "youtube_enabled", False)
        client = YouTubeClient(api_key="key")

        assert client.get_video_views("id1") is None
