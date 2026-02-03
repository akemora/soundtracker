"""Tests for soundtracker.services.top10."""

from unittest.mock import Mock

from soundtracker.models import Film
from soundtracker.services.top10 import Top10Service


class DummyStreamingClient:
    """Streaming client stub with no availability."""

    is_available = False

    def search_popularity(self, *_args, **_kwargs):
        return None

    def search_views(self, *_args, **_kwargs):
        return None


class DummySearchClient:
    """Search client stub with web search disabled."""

    is_enabled = False

    def search(self, *_args, **_kwargs):
        return []

    def fetch_url_text(self, *_args, **_kwargs):
        return ""


class TestTop10Service:
    """Tests for Top10Service."""

    def test_select_top_10_empty(self) -> None:
        """select_top_10 should return empty list when no films."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )

        assert service.select_top_10("Composer", [], []) == []

    def test_normalize_title_strips_numbering_and_year(self) -> None:
        """_normalize_title should strip numbering and year."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )

        assert service._normalize_title("1. Jaws (1975)") == "Jaws"

    def test_build_keys_unique(self) -> None:
        """_build_keys should generate unique normalized keys."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Star Wars", original_title="Star Wars", title_es="La guerra")

        keys = service._build_keys(film)

        assert "starwars" in keys
        assert "laguerra" in keys

    def test_score_film_penalizes_low_vote_count(self) -> None:
        """_score_film should penalize low vote counts."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            min_vote_count=50,
        )
        low_votes = Film(title="A", vote_count=10, vote_average=7.0)
        high_votes = Film(title="B", vote_count=100, vote_average=7.0)

        score_low = service._score_film(low_votes, {}, set(), 2024)
        score_high = service._score_film(high_votes, {}, set(), 2024)

        assert score_high > score_low
