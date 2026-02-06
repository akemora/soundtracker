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

    def test_select_top_10_returns_unique(self) -> None:
        """select_top_10 should return unique films."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        films = [
            Film(title="Jaws", year=1975),
            Film(title="Jaws", year=1975),
            Film(title="Star Wars", year=1977),
        ]

        result = service.select_top_10("Composer", films, [])

        assert len(result) == 2

    def test_select_top_10_force_awards(self) -> None:
        """select_top_10 should prioritize award winners."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            force_awards=True,
        )
        films = [
            Film(title="Jaws", year=1975),
            Film(title="Star Wars", year=1977),
        ]
        awards = [Mock(film="Star Wars")]

        result = service.select_top_10("Composer", films, awards)

        assert result[0].title == "Star Wars"

    def test_get_web_rankings_disabled(self) -> None:
        """get_web_rankings should return empty when search disabled."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )

        assert service.get_web_rankings("Composer") == {}

    def test_get_web_rankings_counts_titles(self) -> None:
        """get_web_rankings should count extracted titles."""
        search = DummySearchClient()
        search.is_enabled = True
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(
            return_value="<article><li>1. Jaws (1975)</li><li>Star Wars (1977)</li></article>"
        )
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=search,
        )

        counts = service.get_web_rankings("Composer")

        assert counts["jaws"] == 4

    def test_extract_titles_from_html_limits(self) -> None:
        """_extract_titles_from_html should limit titles."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        html = "<ul>" + "".join([f"<li>Film {i} (2000)</li>" for i in range(20)]) + "</ul>"

        titles = service._extract_titles_from_html(html, max_titles=5)

        assert len(titles) == 5

    def test_normalize_title_invalid_returns_none(self) -> None:
        """_normalize_title should return None for invalid titles."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )

        assert service._normalize_title("A") is None

    def test_add_streaming_signals_updates(self) -> None:
        """_add_streaming_signals should update popularity/views."""
        spotify = Mock()
        spotify.is_available = True
        spotify.search_popularity = Mock(return_value=80)
        youtube = Mock()
        youtube.is_available = True
        youtube.search_views = Mock(return_value=1000)
        service = Top10Service(
            spotify_client=spotify,
            youtube_client=youtube,
            search_client=DummySearchClient(),
            streaming_candidate_limit=1,
        )
        films = [Film(title="Jaws", year=1975)]

        service._add_streaming_signals("Composer", films, {}, set())

        assert films[0].spotify_popularity == 80
        assert films[0].youtube_views == 1000

    def test_add_streaming_signals_skips_existing_youtube(self) -> None:
        """_add_streaming_signals should skip existing youtube views."""
        spotify = Mock()
        spotify.is_available = False
        youtube = Mock()
        youtube.is_available = True
        youtube.search_views = Mock(return_value=123)
        service = Top10Service(
            spotify_client=spotify,
            youtube_client=youtube,
            search_client=DummySearchClient(),
            streaming_candidate_limit=1,
        )
        film = Film(title="Jaws", year=1975, youtube_views=999)

        service._add_streaming_signals("Composer", [film], {}, set())

        youtube.search_views.assert_not_called()

    def test_has_signal_with_boost(self) -> None:
        """_has_signal should return True with boost score."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Jaws")

        assert service._has_signal(film, {"jaws": 1}, set()) is True

    def test_has_signal_false(self) -> None:
        """_has_signal should return False with no signals."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Jaws")

        assert service._has_signal(film, {}, set()) is False

    def test_score_film_award_boost(self) -> None:
        """_score_film should include award boost."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Jaws", year=1975)

        score_no_award = service._score_film(film, {}, set(), 2024)
        score_award = service._score_film(film, {}, {"jaws"}, 2024)

        assert score_award > score_no_award

    def test_score_film_future_year_penalty(self) -> None:
        """_score_film should penalize future years."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Future", year=3000)

        assert service._score_film(film, {}, set(), 2024) < 0

    def test_score_film_boost_scores(self) -> None:
        """_score_film should include boost scores."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Jaws")

        score = service._score_film(film, {"jaws": 2}, set(), 2024)

        assert score >= 40

    def test_add_streaming_signals_skips_missing_title(self) -> None:
        """_add_streaming_signals should skip films with no title."""
        spotify = Mock()
        spotify.is_available = True
        youtube = Mock()
        youtube.is_available = True
        service = Top10Service(
            spotify_client=spotify,
            youtube_client=youtube,
            search_client=DummySearchClient(),
            streaming_candidate_limit=1,
        )
        film = Film(title="")

        service._add_streaming_signals("Composer", [film], {}, set())

        assert film.spotify_popularity is None

    def test_add_streaming_signals_returns_when_unavailable(self) -> None:
        """_add_streaming_signals should return when no clients."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Jaws")

        service._add_streaming_signals("Composer", [film], {}, set())

        assert film.spotify_popularity is None

    def test_select_top_10_filters_future_and_low_votes(self) -> None:
        """select_top_10 should filter future and low vote films."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            min_vote_count=50,
        )
        current_year = 2024
        films = [
            Film(title="Future", year=current_year + 1, vote_count=100),
            Film(title="Low", year=2000, vote_count=10),
            Film(title="Ok", year=2000, vote_count=100),
        ]

        result = service.select_top_10("Composer", films, [])

        assert any(f.title == "Ok" for f in result)

    def test_select_top_10_signaled_filter(self) -> None:
        """select_top_10 should use signaled films when enough."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        films = [Film(title=f"Film {i}") for i in range(6)]
        boost = {service._normalize_key(f.title): 1 for f in films}

        result = service.select_top_10("Composer", films, [], boost_scores=boost)

        assert len(result) == 6

    def test_get_web_rankings_skips_empty_html(self) -> None:
        """get_web_rankings should skip empty html."""
        search = DummySearchClient()
        search.is_enabled = True
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="")
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=search,
        )

        assert service.get_web_rankings("Composer") == {}

    def test_extract_titles_from_html_skips_invalid(self) -> None:
        """_extract_titles_from_html should skip invalid titles."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        html = "<ul><li>A</li><li>Jaws (1975)</li></ul>"

        titles = service._extract_titles_from_html(html, max_titles=10)

        assert "Jaws" in titles

    def test_build_keys_dedupes(self) -> None:
        """_build_keys should dedupe keys."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        film = Film(title="Star Wars", original_title="Star Wars")

        keys = service._build_keys(film)

        assert keys.count("starwars") == 1

    def test_select_top_10_awards_with_missing_film(self) -> None:
        """select_top_10 should ignore awards without film."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        films = [Film(title="Jaws", year=1975)]
        awards = [Mock(film=None)]

        result = service.select_top_10("Composer", films, awards)

        assert result

    def test_select_top_10_eligible_over_ten(self) -> None:
        """select_top_10 should keep eligible list when >=10."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        films = [Film(title=f"Film {i}", year=2000, vote_count=100) for i in range(10)]

        result = service.select_top_10("Composer", films, [])

        assert len(result) == 10

    def test_get_web_rankings_skips_empty_titles(self) -> None:
        """get_web_rankings should skip empty keys."""
        search = DummySearchClient()
        search.is_enabled = True
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<article><li></li></article>")
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=search,
        )
        service._extract_titles_from_html = Mock(return_value=[""])

        assert service.get_web_rankings("Composer") == {}

    def test_add_streaming_signals_skips_existing(self) -> None:
        """_add_streaming_signals should skip existing values."""
        spotify = Mock()
        spotify.is_available = True
        spotify.search_popularity = Mock(return_value=80)
        youtube = Mock()
        youtube.is_available = True
        youtube.search_views = Mock(return_value=1000)
        service = Top10Service(
            spotify_client=spotify,
            youtube_client=youtube,
            search_client=DummySearchClient(),
            streaming_candidate_limit=1,
        )
        film = Film(title="Jaws", spotify_popularity=10, youtube_views=None)

        service._add_streaming_signals("Composer", [film], {}, set())

        assert film.spotify_popularity == 10

    def test_extract_titles_from_html_dedupes(self) -> None:
        """_extract_titles_from_html should dedupe titles."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        html = "<ul><li>Jaws (1975)</li><li>Jaws (1975)</li></ul>"

        titles = service._extract_titles_from_html(html, max_titles=10)

        assert titles.count("Jaws") == 1

    def test_select_top_10_skips_future_year(self) -> None:
        """select_top_10 should skip films with future years."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            min_vote_count=0,
        )
        films = [Film(title=f"Film {i}", year=2000, vote_count=100) for i in range(10)]
        films.append(Film(title="Future", year=3000, vote_count=100))

        result = service.select_top_10("Composer", films, [])

        assert all(f.title != "Future" for f in result)

    def test_force_awards_skips_duplicate_award_entries(self) -> None:
        """select_top_10 should skip duplicate award entries."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            force_awards=True,
        )
        films = [
            Film(title="Jaws", year=1975),
            Film(title="Jaws", year=1975),
            Film(title="Star Wars", year=1977),
        ]
        awards = [Mock(film="Jaws")]

        result = service.select_top_10("Composer", films, awards)

        assert sum(1 for film in result if film.title == "Jaws") == 1

    def test_force_awards_returns_early_when_full(self) -> None:
        """select_top_10 should return when award list fills top 10."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
            force_awards=True,
        )
        award_films = [Film(title=f"Award {i}", year=2000) for i in range(10)]
        extra = [Film(title=f"Extra {i}", year=2001) for i in range(2)]
        awards = [Mock(film=f"Award {i}") for i in range(10)]

        result = service.select_top_10("Composer", award_films + extra, awards)

        assert len(result) == 10
        assert all(f.title.startswith("Award ") for f in result)

    def test_score_film_includes_popularity(self) -> None:
        """_score_film should include popularity signal."""
        service = Top10Service(
            spotify_client=DummyStreamingClient(),
            youtube_client=DummyStreamingClient(),
            search_client=DummySearchClient(),
        )
        with_popularity = Film(title="Popular", popularity=50)
        without_popularity = Film(title="Unpopular", popularity=None)

        score_with = service._score_film(with_popularity, {}, set(), 2024)
        score_without = service._score_film(without_popularity, {}, set(), 2024)

        assert score_with > score_without
