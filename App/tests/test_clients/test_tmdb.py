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

    def test_is_available_reflects_api_key(self) -> None:
        """is_available should reflect API key presence."""
        assert TMDBClient(api_key="key").is_available is True
        assert TMDBClient(api_key=None).is_available is False

    def test_health_check_no_api_key(self) -> None:
        """health_check should return False without API key."""
        settings.tmdb_api_key = None
        client = TMDBClient(api_key=None)

        assert client.health_check() is False

    def test_health_check_true_with_api_key(self) -> None:
        """health_check should return True when configuration responds."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value={"images": {}})

        assert client.health_check() is True

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

    def test_search_movie_details_no_results_without_cache(self) -> None:
        """search_movie_details should return None when no cache and no results."""
        client = TMDBClient(api_key="key", cache=None, rate_limit_delay=0)
        client._get_with_key = Mock(return_value={"results": []})

        assert client.search_movie_details("Missing", None) is None

    def test_get_with_key_returns_none_without_api_key(self) -> None:
        """_get_with_key should return None without api key."""
        client = TMDBClient(api_key=None)
        assert client._get_with_key("/test") is None

    def test_get_with_key_merges_params(self) -> None:
        """_get_with_key should merge api key with params."""
        client = TMDBClient(api_key="key")
        client._get = Mock(return_value={"ok": True})

        client._get_with_key("/test", {"language": "es"})

        client._get.assert_called_once()
        endpoint, params = client._get.call_args.args
        assert endpoint == "/test"
        assert params["api_key"] == "key"
        assert params["language"] == "es"

    def test_get_with_key_uses_only_api_key(self) -> None:
        """_get_with_key should use only api key when params missing."""
        client = TMDBClient(api_key="key")
        client._get = Mock(return_value={"ok": True})

        client._get_with_key("/test", None)

        client._get.assert_called_once()
        _endpoint, params = client._get.call_args.args
        assert params == {"api_key": "key"}

    def test_search_movie_details_returns_none_without_api_key(self) -> None:
        """search_movie_details should return None without api key."""
        client = TMDBClient(api_key=None)
        assert client.search_movie_details("Jaws", 1975) is None

    def test_search_movie_details_handles_no_data(self) -> None:
        """search_movie_details should handle missing data."""
        cache = DummyCache()
        client = TMDBClient(api_key="key", cache=cache, rate_limit_delay=0)
        client._get_with_key = Mock(return_value=None)

        assert client.search_movie_details("Jaws", 1975) is None
        assert cache.get("Jaws|1975") == {}

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

    def test_search_movie_details_no_year_uses_first(self) -> None:
        """search_movie_details should use first result when no year given."""
        client = TMDBClient(api_key="key", rate_limit_delay=0)

        client._get_with_key = Mock(
            side_effect=[
                {"results": [{"id": 1, "title": "First"}]},
                {"title": "First ES"},
            ]
        )

        result = client.search_movie_details("First", None)

        assert result is not None
        assert result["id"] == 1

    def test_search_movie_details_skips_falsy_chosen(self) -> None:
        """search_movie_details should continue when chosen is falsy."""
        client = TMDBClient(api_key="key", rate_limit_delay=0)

        def fake_get(endpoint: str, params=None):
            if endpoint == "/search/movie":
                if params and params.get("language") == "es-ES":
                    return {"results": [{}]}
                return {"results": [{"id": 2, "title": "Second"}]}
            if endpoint == "/movie/2":
                return {"title": "Second ES"}
            return None

        client._get_with_key = Mock(side_effect=fake_get)

        result = client.search_movie_details("Second", 1999)

        assert result is not None
        assert result["id"] == 2

    def test_search_movie_details_year_no_match_uses_first(self) -> None:
        """search_movie_details should fall back to first result when no year match."""
        client = TMDBClient(api_key="key", rate_limit_delay=0)

        def fake_get(endpoint: str, params=None):
            if endpoint == "/search/movie":
                return {
                    "results": [
                        {
                            "id": 1,
                            "title": "First",
                            "release_date": "1975-01-01",
                        }
                    ]
                }
            if endpoint == "/movie/1":
                return {"title": "First ES"}
            return None

        client._get_with_key = Mock(side_effect=fake_get)

        result = client.search_movie_details("First", 1980)

        assert result is not None
        assert result["id"] == 1

    def test_search_movie_details_handles_missing_movie_id(self) -> None:
        """search_movie_details should handle missing movie id."""
        client = TMDBClient(api_key="key", rate_limit_delay=0)
        client._get_with_key = Mock(return_value={"results": [{"title": "No ID"}]})

        result = client.search_movie_details("No ID", None)

        assert result is not None
        assert result["id"] is None

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

    def test_search_person_handles_missing(self) -> None:
        """search_person should handle missing data."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value=None)

        assert client.search_person("John Williams") == (None, [])

    def test_search_person_returns_none_without_key(self) -> None:
        """search_person should return None when API key missing."""
        client = TMDBClient(api_key=None)

        assert client.search_person("John Williams") == (None, [])

    def test_search_person_handles_empty_results(self) -> None:
        """search_person should return None when results empty."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value={"results": []})

        assert client.search_person("John Williams") == (None, [])

    def test_get_person_movie_credits_filters_music(self) -> None:
        """get_person_movie_credits should filter music credits."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [
                    {"job": "Composer", "department": "Music", "title": "A", "release_date": "2000-01-01"},
                    {"job": "Director", "department": "Directing", "title": "B", "release_date": "2001-01-01"},
                ],
                "cast": [{"title": "C", "release_date": "2002-01-01"}],
            }
        )

        films = client.get_person_movie_credits(1, limit=10)
        titles = [film.title for film in films]
        assert "A" in titles
        assert "C" in titles

    def test_get_person_movie_credits_handles_no_data(self) -> None:
        """get_person_movie_credits should return empty when data missing."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value=None)

        assert client.get_person_movie_credits(1) == []

    def test_get_person_movie_credits_returns_empty_without_key(self) -> None:
        """get_person_movie_credits should return empty without API key."""
        client = TMDBClient(api_key=None)
        assert client.get_person_movie_credits(1) == []

    def test_get_person_movie_credits_uses_all_crew_when_few_music(self) -> None:
        """get_person_movie_credits should include crew when few music credits."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [
                    {"job": "Producer", "department": "Production", "title": "A"},
                ],
                "cast": [],
            }
        )

        films = client.get_person_movie_credits(1, limit=10)
        assert films and films[0].title == "A"

    def test_get_person_movie_credits_keeps_music_credits_when_many(self) -> None:
        """get_person_movie_credits should keep music credits when enough."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [
                    {"job": "Composer", "department": "Music", "title": f"A{i}"}
                    for i in range(5)
                ],
                "cast": [],
            }
        )

        films = client.get_person_movie_credits(1, limit=10)
        assert len(films) == 5

    def test_get_person_movie_credits_handles_invalid_date(self) -> None:
        """get_person_movie_credits should ignore invalid dates."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [{"job": "Composer", "department": "Music", "title": "A", "release_date": "bad-date"}],
                "cast": [],
            }
        )

        films = client.get_person_movie_credits(1, limit=10)
        assert films[0].year is None

    def test_get_person_movie_credits_skips_missing_title(self) -> None:
        """get_person_movie_credits should skip items without title."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(
            return_value={
                "crew": [{"job": "Composer", "department": "Music"}],
                "cast": [],
            }
        )

        assert client.get_person_movie_credits(1) == []

    def test_get_person_profile_url_handles_missing(self) -> None:
        """get_person_profile_url should return None when missing."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value={"profile_path": None})

        assert client.get_person_profile_url(1) is None

    def test_get_person_profile_url_returns_none_without_key(self) -> None:
        """get_person_profile_url should return None when API key missing."""
        client = TMDBClient(api_key=None)

        assert client.get_person_profile_url(1) is None

    def test_get_person_profile_url_returns_none_when_no_data(self) -> None:
        """get_person_profile_url should return None when data missing."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value=None)

        assert client.get_person_profile_url(1) is None

    def test_get_person_profile_url_returns_url(self) -> None:
        """get_person_profile_url should build full URL."""
        client = TMDBClient(api_key="key")
        client._get_with_key = Mock(return_value={"profile_path": "/a.jpg"})

        assert client.get_person_profile_url(1).endswith("/a.jpg")

    def test_get_poster_url(self) -> None:
        """get_poster_url should append path."""
        client = TMDBClient(api_key="key", image_base_url="https://img")
        assert client.get_poster_url("/a.jpg") == "https://img/a.jpg"

    def test_search_movie_poster_handles_missing(self) -> None:
        """search_movie_poster should return None when no details."""
        client = TMDBClient(api_key="key")
        client.search_movie_details = Mock(return_value=None)
        assert client.search_movie_poster("Jaws", 1975) is None

    def test_search_movie_poster_handles_missing_poster(self) -> None:
        """search_movie_poster should return None when poster missing."""
        client = TMDBClient(api_key="key")
        client.search_movie_details = Mock(return_value={"poster_path": None})
        assert client.search_movie_poster("Jaws", 1975) is None

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
