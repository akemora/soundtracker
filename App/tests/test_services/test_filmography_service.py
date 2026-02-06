"""Tests for soundtracker.services.filmography."""

from unittest.mock import Mock

from soundtracker.models import Film
from soundtracker.services.filmography import FilmographyService


class TestFilmographyService:
    """Tests for FilmographyService."""

    def test_extract_films_from_text(self) -> None:
        """_extract_films_from_text should parse titles and years."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        films = service._extract_films_from_text("Jaws (1975) and Star Wars (1977)")

        assert len(films) == 2
        assert films[0].title == "Jaws"
        assert films[0].year == 1975

    def test_dedupe_films_filters_bad_titles(self) -> None:
        """_dedupe_films should remove duplicates and bad titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        films = [
            Film(title="Jaws", year=1975),
            Film(title="Jaws", year=1975),
            Film(title="Main Page", year=2000),
        ]

        result = service._dedupe_films(films)

        assert len(result) == 1
        assert result[0].title == "Jaws"

    def test_poster_filename(self) -> None:
        """_poster_filename should include year when provided."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        assert service._poster_filename("Star Wars", 1977) == "poster_star_wars_1977.jpg"

    def test_merge_films_dedupes(self) -> None:
        """_merge_films should avoid duplicates."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        base = [Film(title="Jaws", original_title="Jaws")]
        extra = [Film(title="Jaws", original_title="Jaws"), Film(title="Star Wars")]

        result = service._merge_films(base, extra)

        assert len(result) == 2

    def test_extract_films_from_html(self) -> None:
        """_extract_films_from_html should parse list items."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        html = "<ul><li>Jaws (1975)</li><li>Star Wars (1977)</li></ul>"

        films = service._extract_films_from_html(html)

        assert len(films) == 2

    def test_extract_films_from_html_dedupes_and_limits(self) -> None:
        """_extract_films_from_html should dedupe and respect limit."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        def fake_extract(_text: str):
            return [Film(title="Jaws", year=1975)]

        service._extract_films_from_text = Mock(side_effect=fake_extract)
        html = "<ul>" + "".join(["<li>Jaws (1975)</li>" for _ in range(210)]) + "</ul>"

        films = service._extract_films_from_html(html)

        assert len(films) == 1

    def test_extract_films_from_html_returns_on_limit(self) -> None:
        """_extract_films_from_html should return when reaching limit."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        service._extract_films_from_text = Mock(
            return_value=[Film(title=f"Film {i}") for i in range(200)]
        )
        html = "<ul><li>Film 1 (2000)</li></ul>"

        films = service._extract_films_from_html(html)

        assert len(films) == 200

    def test_search_filmography_no_results(self) -> None:
        """_search_filmography should return empty when none found."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="")
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
        )

        assert service._search_filmography("Composer") == []

    def test_normalize_title_key(self) -> None:
        """_normalize_title_key should strip non-alphanumerics."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        assert service._normalize_title_key("Star Wars: A New Hope") == "starwarsanewhope"

    def test_is_bad_title_flags(self) -> None:
        """_is_bad_title should flag bad titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        assert service._is_bad_title("Main Page") is True
        assert service._is_bad_title("Edit this page") is True
        assert service._is_bad_title("Q123") is True

    def test_set_poster_path(self, tmp_path) -> None:
        """_set_poster_path should set poster_url and poster_file."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", year=1975, poster_path="/a.jpg")

        service._set_poster_path(film, tmp_path)

        assert film.poster_url.endswith("/a.jpg")
        assert str(tmp_path / "posters") in film.poster_file

    def test_set_poster_path_without_poster_path(self, tmp_path) -> None:
        """_set_poster_path should set poster_file even without poster_path."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", year=1975)

        service._set_poster_path(film, tmp_path)

        assert film.poster_url is None
        assert film.poster_file is not None

    def test_enrich_film_no_tmdb(self) -> None:
        """_enrich_film should no-op when tmdb unavailable."""
        tmdb = Mock()
        tmdb.is_available = False
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws")

        service._enrich_film(film)

        assert film.title_es == "Jaws"

    def test_enrich_film_updates_fields(self) -> None:
        """_enrich_film should update missing fields."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_movie_details = Mock(
            return_value={
                "original_title": "Jaws",
                "title_es": "Tiburón",
                "poster_path": "/a.jpg",
                "popularity": 1.0,
                "vote_count": 10,
                "vote_average": 7.0,
            }
        )
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws")
        film.title_es = None
        film.title_es_distribution = None
        film.original_title = None

        service._enrich_film(film)

        assert film.title_es == "Tiburón"

    def test_enrich_film_handles_no_details(self) -> None:
        """_enrich_film should return when no details found."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_movie_details = Mock(return_value=None)
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws")
        film.title_es = None
        film.title_es_distribution = None
        film.original_title = None

        service._enrich_film(film)

        assert film.title_es is None

    def test_get_complete_filmography_tmdb_only(self) -> None:
        """get_complete_filmography should return TMDB films."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_person = Mock(return_value=(1, []))
        tmdb.get_person_movie_credits = Mock(return_value=[Film(title="Jaws", year=1975)])
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("John Williams")

        assert len(films) == 1

    def test_get_complete_filmography_tmdb_search_person_none(self) -> None:
        """get_complete_filmography should skip tmdb when no person_id."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_person = Mock(return_value=(None, []))
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("Composer")

        assert films == []

    def test_get_complete_filmography_skips_fallbacks_when_enough_films(self) -> None:
        """get_complete_filmography should skip fallbacks when enough films."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_person = Mock(return_value=(1, []))
        tmdb.get_person_movie_credits = Mock(
            return_value=[Film(title=f"Film {i}", year=2000) for i in range(8)]
        )
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value="Q1")
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value="<li>Extra (1975)</li>")
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("Composer")

        assert len(films) == 8

    def test_get_complete_filmography_imdb_only(self) -> None:
        """get_complete_filmography should use IMDb when available."""
        tmdb = Mock()
        tmdb.is_available = False
        imdb = Mock()
        imdb.is_available = True
        imdb.get_composer_filmography = Mock(return_value=[Film(title="Jaws", year=1975)])
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("John Williams")

        assert len(films) == 1

    def test_get_complete_filmography_wikidata_fallback(self) -> None:
        """get_complete_filmography should use Wikidata fallback."""
        tmdb = Mock()
        tmdb.is_available = False
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value="Q1")
        wikidata.get_filmography = Mock(return_value=[Film(title="Jaws", year=1975)])
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("John Williams")

        assert len(films) == 1

    def test_get_complete_filmography_wikipedia_fallback(self) -> None:
        """get_complete_filmography should use Wikipedia fallback."""
        tmdb = Mock()
        tmdb.is_available = False
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value="<li>Jaws (1975)</li>")
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("John Williams")

        assert len(films) == 1

    def test_get_complete_filmography_web_fallback(self) -> None:
        """get_complete_filmography should use web search fallback."""
        tmdb = Mock()
        tmdb.is_available = False
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="Jaws (1975)")
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("John Williams")

        assert len(films) == 1

    def test_apply_title_translations_sets_distribution(self) -> None:
        """_apply_title_translations should set literal/distribution."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        service.translator.ensure_spanish = Mock(return_value="Titulo ES")
        film = Film(title="Jaws", title_es="Tiburon", original_title="Jaws")
        film.title_es_distribution = None

        service._apply_title_translations([film])

        assert film.title_es_literal == "Titulo ES"
        assert film.title_es_distribution == "Tiburon"

    def test_apply_title_translations_skips_same_title(self) -> None:
        """_apply_title_translations should skip distribution when same title."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", title_es="Jaws")
        film.title_es_distribution = None

        service._apply_title_translations([film])

        assert film.title_es_distribution is None

    def test_get_tv_credits_returns_empty_when_imdb_missing(self) -> None:
        """get_tv_credits should return empty when imdb unavailable."""
        imdb = Mock()
        imdb.is_available = False
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            imdb_client=imdb,
        )

        assert service.get_tv_credits("Composer") == []

    def test_get_video_game_credits_returns_empty_when_imdb_missing(self) -> None:
        """get_video_game_credits should return empty when imdb unavailable."""
        imdb = Mock()
        imdb.is_available = False
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            imdb_client=imdb,
        )

        assert service.get_video_game_credits("Composer") == []

    def test_get_tv_credits_with_imdb(self) -> None:
        """get_tv_credits should return imdb films."""
        imdb = Mock()
        imdb.is_available = True
        imdb.get_composer_filmography = Mock(return_value=[Film(title="TV Show")])
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            imdb_client=imdb,
        )

        films = service.get_tv_credits("Composer")

        assert len(films) == 1

    def test_get_video_game_credits_with_imdb(self) -> None:
        """get_video_game_credits should return imdb films."""
        imdb = Mock()
        imdb.is_available = True
        imdb.get_composer_filmography = Mock(return_value=[Film(title="Game")])
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            imdb_client=imdb,
        )

        films = service.get_video_game_credits("Composer")

        assert len(films) == 1

    def test_extract_films_from_text_dedupes(self) -> None:
        """_extract_films_from_text should dedupe titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        films = service._extract_films_from_text("Jaws (1975) Jaws (1975)")

        assert len(films) == 1

    def test_extract_films_from_text_skips_empty_title(self) -> None:
        """_extract_films_from_text should skip empty titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        assert service._extract_films_from_text("   (1975)") == []

    def test_extract_films_from_text_breaks_on_limit(self, monkeypatch) -> None:
        """_extract_films_from_text should break at limit."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        class DummyMatch:
            def __init__(self, title: str, year: str) -> None:
                self._title = title
                self._year = year

            def group(self, idx: int):
                return self._title if idx == 1 else self._year

        class DummyPattern:
            def finditer(self, _text: str):
                return [DummyMatch(f"Film {i}", "1975") for i in range(205)]

        monkeypatch.setattr("soundtracker.services.filmography.re.compile", lambda *_args, **_kwargs: DummyPattern())

        films = service._extract_films_from_text("anything")

        assert len(films) == 200

    def test_extract_films_from_text_skips_blank_match(self, monkeypatch) -> None:
        """_extract_films_from_text should skip blank match titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        class DummyMatch:
            def group(self, idx: int):
                return "   " if idx == 1 else "1975"

        class DummyPattern:
            def finditer(self, _text: str):
                return [DummyMatch()]

        monkeypatch.setattr("soundtracker.services.filmography.re.compile", lambda *_args, **_kwargs: DummyPattern())

        films = service._extract_films_from_text("anything")

        assert films == []

    def test_poster_filename_no_year(self) -> None:
        """_poster_filename should omit year when not provided."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )

        assert service._poster_filename("Star Wars") == "poster_star_wars.jpg"

    def test_merge_films_skips_empty_key(self) -> None:
        """_merge_films should skip films with empty key."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        base = []
        extra = [Film(title="", original_title="")]

        result = service._merge_films(base, extra)

        assert result == []

    def test_merge_films_skips_empty_base_key(self) -> None:
        """_merge_films should skip empty base keys."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        base = [Film(title="", original_title="")]
        extra = [Film(title="Jaws", original_title="Jaws")]

        result = service._merge_films(base, extra)

        assert len(result) == 2

    def test_dedupe_films_filters_wikipedia_edit(self) -> None:
        """_dedupe_films should filter wikipedia/edit titles."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        films = [
            Film(title="Wikipedia", year=2000),
            Film(title="Edit this page", year=2001),
        ]

        assert service._dedupe_films(films) == []

    def test_search_filmography_returns_empty_when_no_films(self) -> None:
        """_search_filmography should return empty when no films parsed."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="No film data")
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
        )

        assert service._search_filmography("Composer") == []

    def test_search_filmography_returns_films(self) -> None:
        """_search_filmography should return films when parsed."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="Jaws (1975)")
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
        )

        films = service._search_filmography("Composer")

        assert len(films) == 1

    def test_apply_title_translations_skips_empty_original(self) -> None:
        """_apply_title_translations should skip empty original title."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="")

        service._apply_title_translations([film])

        assert film.title_es_literal is None

    def test_apply_title_translations_keeps_distribution(self) -> None:
        """_apply_title_translations should keep existing distribution."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", title_es="Tiburon")
        film.title_es_distribution = "Distrib"

        service._apply_title_translations([film])

        assert film.title_es_distribution == "Distrib"

    def test_apply_title_translations_keeps_literal(self) -> None:
        """_apply_title_translations should keep existing literal title."""
        service = FilmographyService(
            tmdb_client=Mock(),
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", title_es="Tiburon")
        film.title_es_literal = "Literal"

        service._apply_title_translations([film])

        assert film.title_es_literal == "Literal"

    def test_get_complete_filmography_uses_tmdb_id(self) -> None:
        """get_complete_filmography should use provided tmdb_id."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.get_person_movie_credits = Mock(return_value=[Film(title="Jaws", year=1975)])
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("Composer", tmdb_id=1)

        assert len(films) == 1

    def test_get_complete_filmography_with_composer_folder(self, tmp_path) -> None:
        """get_complete_filmography should set poster paths when folder provided."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_person = Mock(return_value=(1, []))
        tmdb.get_person_movie_credits = Mock(return_value=[Film(title="Jaws", year=1975)])
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_qid = Mock(return_value=None)
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("Composer", composer_folder=tmp_path)

        assert films[0].poster_file is not None

    def test_enrich_film_skips_when_has_title_and_poster(self) -> None:
        """_enrich_film should skip when title_es and poster_path exist."""
        tmdb = Mock()
        tmdb.is_available = True
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(title="Jaws", poster_path="/a.jpg")

        service._enrich_film(film)

        tmdb.search_movie_details.assert_not_called()

    def test_enrich_film_skips_existing_fields(self) -> None:
        """_enrich_film should not overwrite existing fields."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_movie_details = Mock(
            return_value={
                "original_title": "New",
                "title_es": "Nuevo",
                "poster_path": "/new.jpg",
                "popularity": 5.0,
                "vote_count": 50,
                "vote_average": 8.0,
            }
        )
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(
            title="Jaws",
            original_title="Jaws",
            title_es="",
            poster_path="/old.jpg",
            popularity=1.0,
            vote_count=10,
            vote_average=7.0,
        )
        film.title_es_distribution = None

        service._enrich_film(film)

        assert film.poster_path == "/old.jpg"
        assert film.popularity == 1.0

    def test_enrich_film_skips_existing_title_es(self) -> None:
        """_enrich_film should keep existing title_es."""
        tmdb = Mock()
        tmdb.is_available = True
        tmdb.search_movie_details = Mock(
            return_value={
                "original_title": "New",
                "title_es": "Nuevo",
                "poster_path": "/new.jpg",
                "popularity": 5.0,
                "vote_count": 50,
                "vote_average": 8.0,
            }
        )
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
        )
        film = Film(
            title="Jaws",
            original_title="Jaws",
            title_es="Tiburon",
            poster_path=None,
            popularity=None,
            vote_count=None,
            vote_average=None,
        )

        service._enrich_film(film)

        assert film.title_es == "Tiburon"
        assert film.poster_path == "/new.jpg"

    def test_get_complete_filmography_uses_wikidata_qid(self) -> None:
        """get_complete_filmography should use provided wikidata_qid."""
        tmdb = Mock()
        tmdb.is_available = False
        imdb = Mock()
        imdb.is_available = False
        wikidata = Mock()
        wikidata.get_filmography = Mock(return_value=[Film(title="Jaws", year=1975)])
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=[])
        service = FilmographyService(
            tmdb_client=tmdb,
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            imdb_client=imdb,
        )

        films = service.get_complete_filmography("Composer", wikidata_qid="Q1")

        assert len(films) == 1
