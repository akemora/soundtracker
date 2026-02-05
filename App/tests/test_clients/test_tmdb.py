"""Tests for soundtracker.clients.tmdb."""

from unittest.mock import Mock

from soundtracker.clients.tmdb import TMDBClient
from soundtracker.config import settings


class DummyCache:
    """Simple in-memory cache for testing."""

    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: dict) -> None:
        self.data[key] = value


class TestTMDBClient:
    """Tests for TMDBClient."""

    def test_health_check_no_api_key(self) -> None:
        """health_check should return False without API key."""
        settings.tmdb_api_key = None
        client = TMDBClient(api_key=None)

        assert client.health_check() is False

    def test_search_movie_details_cache_hit(self) -> None:
        """search_movie_details should return cached value when present."""
        cache = DummyCache()
        cache.set("Jaws|1975", {"id": 1, "title_es": "Tiburón"})
        client = TMDBClient(api_key="key", cache=cache, rate_limit_delay=0)
        client._get_with_key = Mock()

        result = client.search_movie_details("Jaws", 1975)

        assert result == {"id": 1, "title_es": "Tiburón"}
        client._get_with_key.assert_not_called()

    def test_search_movie_details_no_results_sets_cache(self) -> None:
        """search_movie_details should cache empty result when not found."""
        cache = DummyCache()
        client = TMDBClient(api_key="key", cache=cache, rate_limit_delay=0)
        client._get_with_key = Mock(return_value={"results": []})

        result = client.search_movie_details("Missing", None)

        assert result is None
        assert cache.get("Missing|") == {}

    def test_search_movie_details_year_match(self) -> None:
        """search_movie_details should pick matching year result."""
        cache = DummyCache()
        client = TMDBClient(api_key="key", cache=cache, rate_limit_delay=0)

        def fake_get(endpoint: str, params=None):
            if endpoint == "/search/movie":
                return {
                    "results": [
                        {
                            "id": 1,
                            "title": "Older",
                            "release_date": "1975-06-01",
                            "poster_path": "/a.jpg",
                            "popularity": 1.0,
                            "vote_count": 10,
                            "vote_average": 7.0,
                        },
                        {
                            "id": 2,
                            "title": "Target",
                            "release_date": "1977-01-01",
                            "poster_path": "/b.jpg",
                            "popularity": 5.0,
                            "vote_count": 99,
                            "vote_average": 8.5,
                        },
                    ]
                }
            if endpoint == "/movie/2":
                return {
                    "title": "Target ES",
                    "original_title": "Target",
                    "poster_path": "/b.jpg",
                }
            return None

        client._get_with_key = Mock(side_effect=fake_get)

        result = client.search_movie_details("Target", 1977)

        assert result is not None
        assert result["id"] == 2
        assert result["title_es"] == "Target ES"
        assert result["poster_path"] == "/b.jpg"
        assert cache.get("Target|1977") is not None

    def test_search_person_returns_known_for(self) -> None:
        """search_person should return id and unique known_for titles."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "results": [
                    {
                        "id": 42,
                        "known_for": [
                            {"title": "Jaws"},
                            {"original_title": "Star Wars"},
                            {"title": "Jaws"},
                        ],
                    }
                ]
            }
        )

        person_id, known_for = client.search_person("John Williams")

        assert person_id == 42
        assert known_for == ["Jaws", "Star Wars"]

    def test_get_person_movie_credits_limit_and_language(self) -> None:
        """get_person_movie_credits should respect limit and set title_es."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [
                    {
                        "title": "Film A",
                        "original_title": "Film A",
                        "job": "Composer",
                        "department": "Music",
                        "release_date": "1977-01-01",
                    },
                    {
                        "title": "Film B",
                        "original_title": "Film B",
                        "job": "Producer",
                        "department": "Production",
                        "release_date": "1980-01-01",
                    },
                ],
                "cast": [
                    {
                        "title": "Film C",
                        "original_title": "Film C",
                        "release_date": "1981-01-01",
                    }
                ],
            }
        )

        films = client.get_person_movie_credits(1, language="es-ES", limit=2)

        assert len(films) == 2
        assert films[0].title_es is not None

    def test_get_person_profile_url(self) -> None:
        """get_person_profile_url should return full image URL."""
        client = TMDBClient(api_key="key", image_base_url="http://img/")
        client._get_with_key = Mock(return_value={"profile_path": "/p.jpg"})

        assert client.get_person_profile_url(1) == "http://img//p.jpg"

    def test_get_poster_url(self) -> None:
        """get_poster_url should build full URL."""
        client = TMDBClient(api_key="key", image_base_url="http://img/")

        assert client.get_poster_url("/poster.jpg") == "http://img//poster.jpg"

    def test_search_movie_poster(self) -> None:
        """search_movie_poster should return poster URL when present."""
        client = TMDBClient(api_key="key", image_base_url="http://img/")
        client.search_movie_details = Mock(return_value={"poster_path": "/p.jpg"})

        assert client.search_movie_poster("Jaws", 1975) == "http://img//p.jpg"
