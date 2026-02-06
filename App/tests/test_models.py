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
        film = Film(title="Test", year=2000, imdb_id="tt1234567")
        d = film.to_dict()
        assert d["title"] == "Test"
        assert d["year"] == 2000
        assert d["imdb_id"] == "tt1234567"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"title": "Test", "year": 2000, "popularity": 50.0, "imdb_id": "tt7654321"}
        film = Film.from_dict(data)
        assert film.title == "Test"
        assert film.year == 2000
        assert film.popularity == 50.0
        assert film.imdb_id == "tt7654321"


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
        assert "🏆" in text

        nomination = Award(
            award="Golden Globe",
            year=2001,
            film="Test Film",
            status=AwardStatus.NOMINATION,
            category="Best Score",
        )
        text_nom = nomination.display_text
        assert "🎯" in text_nom
        assert "Best Score" in text_nom

    def test_display_text_without_optional_fields(self):
        """Test display_text without optional fields."""
        award = Award(award="Oscar", status=AwardStatus.NOMINATION, year=None, film=None, category=None)
        text = award.display_text
        assert "Oscar" in text
        assert "🎯" in text
        assert "por *" not in text

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

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"name": "Src", "url": "https://src.com", "snippet": "s", "text": "t"}
        source = ExternalSource.from_dict(data)
        assert source.name == "Src"
        assert source.url == "https://src.com"
        assert source.snippet == "s"
        assert source.text == "t"


class TestComposerInfo:
    """Tests for ComposerInfo dataclass."""

    def test_basic_creation(self):
        """Test creating a ComposerInfo."""
        info = ComposerInfo(name="John Williams")
        assert info.name == "John Williams"
        assert info.filmography == []
        assert info.tv_credits == []
        assert info.video_games == []
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

        info.birth_year = None
        assert info.life_span == ""

    def test_slug(self):
        """Test slug generation."""
        info = ComposerInfo(name="John Williams")
        assert info.slug == "john_williams"

        info = ComposerInfo(name="Hans Zimmer")
        assert info.slug == "hans_zimmer"

        info = ComposerInfo(name="!!!")
        assert info.slug == "composer"

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

        info = ComposerInfo(name="John Williams")
        assert info.folder_name == "john_williams"

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
            tv_credits=[Film(title="Series A")],
            video_games=[Film(title="Game A")],
        )
        d = info.to_dict()
        assert d["name"] == "John Williams"
        assert d["index"] == 1
        assert len(d["filmography"]) == 1
        assert len(d["tv_credits"]) == 1
        assert len(d["video_games"]) == 1

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "John Williams",
            "index": 1,
            "birth_year": 1932,
            "filmography": [{"title": "Star Wars", "year": 1977}],
            "tv_credits": [{"title": "Series A", "year": 1990}],
            "video_games": [{"title": "Game A", "year": 2000}],
            "awards": [{"award": "Oscar", "year": 1978}],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        info = ComposerInfo.from_dict(data)
        assert info.name == "John Williams"
        assert info.birth_year == 1932
        assert len(info.filmography) == 1
        assert info.filmography[0].title == "Star Wars"
        assert len(info.tv_credits) == 1
        assert len(info.video_games) == 1

    def test_from_dict_without_timestamps(self):
        """Test creation when timestamps are missing."""
        data = {
            "name": "Composer",
            "filmography": [],
            "awards": [],
        }
        info = ComposerInfo.from_dict(data)
        assert info.name == "Composer"
        assert info.created_at is not None
        assert info.updated_at is not None


class TestAwardStatus:
    """Tests for AwardStatus enum."""

    def test_values(self):
        """Test enum values."""
        assert AwardStatus.WIN.value == "Win"
        assert AwardStatus.NOMINATION.value == "Nomination"

    def test_comparison(self):
        """Test enum comparison."""
        assert AwardStatus.WIN != AwardStatus.NOMINATION
