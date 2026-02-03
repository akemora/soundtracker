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
