"""Tests for soundtracker.models module."""

import pytest
from datetime import datetime

from soundtracker.models import (
    Award,
    AwardStatus,
    ComposerInfo,
    ExternalSource,
    Film,
)


class TestFilm:
    """Tests for Film dataclass."""

    def test_basic_creation(self):
        """Test creating a Film with minimal data."""
        film = Film(title="Star Wars")
        assert film.title == "Star Wars"
        assert film.original_title == "Star Wars"
        assert film.title_es == "Star Wars"

    def test_full_creation(self):
        """Test creating a Film with all fields."""
        film = Film(
            title="Star Wars",
            original_title="Star Wars",
            title_es="La Guerra de las Galaxias",
            year=1977,
            poster_url="https://example.com/poster.jpg",
            popularity=100.0,
            vote_count=5000,
            vote_average=8.5,
        )
        assert film.year == 1977
        assert film.popularity == 100.0
        assert film.vote_count == 5000

    def test_display_title(self):
        """Test display_title property."""
        film = Film(
            title="Star Wars",
            title_es="La Guerra de las Galaxias",
        )
        assert film.display_title == "La Guerra de las Galaxias"

    def test_has_poster(self):
        """Test has_poster property."""
        film = Film(title="Test")
        assert not film.has_poster

        film.poster_url = "https://example.com/poster.jpg"
        assert film.has_poster

        film.poster_url = None
        film.poster_local = "/path/to/poster.jpg"
        assert film.has_poster

    def test_to_dict(self):
        """Test conversion to dictionary."""
        film = Film(title="Test", year=2000)
        d = film.to_dict()
        assert d["title"] == "Test"
        assert d["year"] == 2000

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"title": "Test", "year": 2000, "popularity": 50.0}
        film = Film.from_dict(data)
        assert film.title == "Test"
        assert film.year == 2000
        assert film.popularity == 50.0


class TestAward:
    """Tests for Award dataclass."""

    def test_basic_creation(self):
        """Test creating an Award."""
        award = Award(award="Oscar")
        assert award.award == "Oscar"
        assert award.status == AwardStatus.WIN

    def test_full_creation(self):
        """Test creating an Award with all fields."""
        award = Award(
            award="Oscar",
            year=1978,
            film="Star Wars",
            status=AwardStatus.WIN,
            category="Best Original Score",
        )
        assert award.year == 1978
        assert award.film == "Star Wars"
        assert award.is_win

    def test_nomination(self):
        """Test nomination status."""
        award = Award(award="Oscar", status=AwardStatus.NOMINATION)
        assert not award.is_win
        assert award.status == AwardStatus.NOMINATION

    def test_display_text(self):
        """Test display_text property."""
        award = Award(award="Oscar", year=1978, film="Star Wars")
        text = award.display_text
        assert "Oscar" in text
        assert "Star Wars" in text

    def test_to_dict(self):
        """Test conversion to dictionary."""
        award = Award(award="Oscar", year=1978)
        d = award.to_dict()
        assert d["award"] == "Oscar"
        assert d["year"] == 1978
        assert d["status"] == "Win"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"award": "Oscar", "year": 1978, "status": "Nomination"}
        award = Award.from_dict(data)
        assert award.award == "Oscar"
        assert award.status == AwardStatus.NOMINATION


class TestExternalSource:
    """Tests for ExternalSource dataclass."""

    def test_basic_creation(self):
        """Test creating an ExternalSource."""
        source = ExternalSource(name="IMDb", url="https://imdb.com")
        assert source.name == "IMDb"
        assert source.url == "https://imdb.com"

    def test_with_snippet(self):
        """Test source with snippet."""
        source = ExternalSource(
            name="MundoBSO",
            url="https://mundobso.com",
            snippet="Great resource for soundtracks",
            text="Extended text content",
        )
        assert source.snippet == "Great resource for soundtracks"
        assert source.text == "Extended text content"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        source = ExternalSource(name="Test", url="https://test.com")
        d = source.to_dict()
        assert d["name"] == "Test"
        assert d["url"] == "https://test.com"


class TestComposerInfo:
    """Tests for ComposerInfo dataclass."""

    def test_basic_creation(self):
        """Test creating a ComposerInfo."""
        info = ComposerInfo(name="John Williams")
        assert info.name == "John Williams"
        assert info.filmography == []
        assert info.awards == []
        assert info.created_at is not None

    def test_full_creation(self):
        """Test creating ComposerInfo with all fields."""
        info = ComposerInfo(
            name="John Williams",
            index=1,
            birth_year=1932,
            country="USA",
            biography="A legendary composer...",
            filmography=[Film(title="Star Wars")],
            awards=[Award(award="Oscar")],
        )
        assert info.index == 1
        assert info.birth_year == 1932
        assert len(info.filmography) == 1
        assert len(info.awards) == 1

    def test_is_alive(self):
        """Test is_alive property."""
        info = ComposerInfo(name="Test", birth_year=1932)
        assert info.is_alive

        info.death_year = 2020
        assert not info.is_alive

    def test_life_span(self):
        """Test life_span property."""
        info = ComposerInfo(name="Test", birth_year=1932)
        assert info.life_span == "(1932-)"

        info.death_year = 2020
        assert info.life_span == "(1932-2020)"

    def test_slug(self):
        """Test slug generation."""
        info = ComposerInfo(name="John Williams")
        assert info.slug == "john_williams"

        info = ComposerInfo(name="Hans Zimmer")
        assert info.slug == "hans_zimmer"

    def test_filename(self):
        """Test filename generation."""
        info = ComposerInfo(name="John Williams", index=1)
        assert info.filename == "001_john_williams.md"

        info = ComposerInfo(name="John Williams")
        assert info.filename == "john_williams.md"

    def test_folder_name(self):
        """Test folder_name generation."""
        info = ComposerInfo(name="John Williams", index=1)
        assert info.folder_name == "001_john_williams"

    def test_photo_property(self):
        """Test photo property returns local or URL."""
        info = ComposerInfo(name="Test")
        assert info.photo is None

        info.image_url = "https://example.com/photo.jpg"
        assert info.photo == "https://example.com/photo.jpg"

        info.image_local = "/local/photo.jpg"
        assert info.photo == "/local/photo.jpg"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = ComposerInfo(
            name="John Williams",
            index=1,
            filmography=[Film(title="Star Wars")],
        )
        d = info.to_dict()
        assert d["name"] == "John Williams"
        assert d["index"] == 1
        assert len(d["filmography"]) == 1

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "John Williams",
            "index": 1,
            "birth_year": 1932,
            "filmography": [{"title": "Star Wars", "year": 1977}],
            "awards": [{"award": "Oscar", "year": 1978}],
        }
        info = ComposerInfo.from_dict(data)
        assert info.name == "John Williams"
        assert info.birth_year == 1932
        assert len(info.filmography) == 1
        assert info.filmography[0].title == "Star Wars"


class TestAwardStatus:
    """Tests for AwardStatus enum."""

    def test_values(self):
        """Test enum values."""
        assert AwardStatus.WIN.value == "Win"
        assert AwardStatus.NOMINATION.value == "Nomination"

    def test_comparison(self):
        """Test enum comparison."""
        assert AwardStatus.WIN != AwardStatus.NOMINATION
