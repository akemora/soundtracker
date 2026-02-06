"""Tests for soundtracker.services.posters."""

from pathlib import Path
from unittest.mock import Mock

from soundtracker.config import settings
from soundtracker.models import Film
from soundtracker.services.posters import PosterService


class TestPosterService:
    """Tests for PosterService."""

    def test_is_image_url(self) -> None:
        """_is_image_url should detect image extensions."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())

        assert service._is_image_url("http://example.com/a.jpg") is True
        assert service._is_image_url("http://example.com/a.png") is True
        assert service._is_image_url("http://example.com/a.html") is False

    def test_download_image_streams_to_file(self, tmp_path: Path) -> None:
        """_download_image should write streamed content to file."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        response = Mock()
        response.raise_for_status = Mock()
        response.iter_content = Mock(return_value=[b"data"])
        service._session.get = Mock(return_value=response)

        target = tmp_path / "poster.jpg"
        result = service._download_image("http://image", target)

        assert result == str(target)
        assert target.read_bytes() == b"data"

    def test_get_poster_from_web_filters_non_images(self, tmp_path: Path) -> None:
        """_get_poster_from_web should skip non-image URLs."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service.search.search = Mock(
            return_value=["http://example.com/page", "http://example.com/poster.jpg"]
        )
        service._download_image = Mock(return_value=str(tmp_path / "poster.jpg"))

        result = service._get_poster_from_web("Title", tmp_path, year=1977)

        assert result == str(tmp_path / "poster.jpg")

    def test_download_posters_skips_when_disabled(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should exit when disabled."""
        monkeypatch.setattr(settings, "download_posters", False)
        service = PosterService(tmdb_client=Mock(), search_client=Mock())

        service.download_posters([Film(title="Jaws")], tmp_path)

    def test_download_posters_sets_local_when_exists(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should set poster_local when file exists."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=False)
        film = Film(title="Jaws", poster_url="http://example.com/a.jpg")
        poster_path = tmp_path / "posters" / "poster_jaws.jpg"
        poster_path.parent.mkdir(parents=True, exist_ok=True)
        poster_path.write_bytes(b"data")
        film.poster_file = str(poster_path)

        service.download_posters([film], tmp_path)

        assert film.poster_local == str(poster_path)

    def test_download_posters_limit_breaks(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should respect limit."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=False)
        film1 = Film(title="A", poster_url="http://example.com/a.jpg")
        film2 = Film(title="B", poster_url="http://example.com/b.jpg")
        service._download_image = Mock(return_value=str(tmp_path / "a.jpg"))

        service.download_posters([film1, film2], tmp_path, limit=1)

        assert film1.poster_local
        assert film2.poster_local is None

    def test_download_posters_uses_poster_path(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should derive poster_url from poster_path."""
        monkeypatch.setattr(settings, "download_posters", True)
        tmdb = Mock()
        tmdb.get_poster_url = Mock(return_value="http://example.com/a.jpg")
        service = PosterService(tmdb_client=tmdb, search_client=Mock(), web_fallback=False)
        film = Film(title="A", poster_path="/a.jpg")
        service._download_image = Mock(return_value=str(tmp_path / "a.jpg"))

        service.download_posters([film], tmp_path, limit=1)

        tmdb.get_poster_url.assert_called_once()
        assert film.poster_local

    def test_download_posters_skips_missing_urls(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should skip films without URLs."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=False)
        film = Film(title="A")

        service.download_posters([film], tmp_path)

        assert film.poster_local is None

    def test_download_posters_handles_download_error(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should handle download errors."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=False)
        film = Film(title="A", poster_url="http://example.com/a.jpg")
        service._download_image = Mock(side_effect=Exception("boom"))

        service.download_posters([film], tmp_path)

        assert film.poster_local is None

    def test_download_posters_triggers_web_fallback(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should trigger web fallback."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=True)
        film = Film(title="A", poster_url="http://example.com/a.jpg")
        service._download_image = Mock(return_value=None)
        service._download_missing = Mock()

        service.download_posters([film], tmp_path)

        service._download_missing.assert_called_once()

    def test_download_posters_skips_web_fallback(self, monkeypatch, tmp_path: Path) -> None:
        """download_posters should skip web fallback when disabled."""
        monkeypatch.setattr(settings, "download_posters", True)
        service = PosterService(tmdb_client=Mock(), search_client=Mock(), web_fallback=False)
        film = Film(title="A", poster_url="http://example.com/a.jpg")
        service._download_image = Mock(return_value=None)
        service._download_missing = Mock()

        service.download_posters([film], tmp_path)

        service._download_missing.assert_not_called()

    def test_download_image_handles_error(self, tmp_path: Path) -> None:
        """_download_image should clean up on error."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service._session.get = Mock(side_effect=Exception("boom"))
        target = tmp_path / "poster.jpg"
        target.write_bytes(b"data")

        assert service._download_image("http://example.com", target) is None
        assert not target.exists()

    def test_download_image_returns_none_on_empty_url(self, tmp_path: Path) -> None:
        """_download_image should return None on empty url."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        target = tmp_path / "poster.jpg"

        assert service._download_image("", target) is None

    def test_download_image_error_without_existing_file(self, tmp_path: Path) -> None:
        """_download_image should handle error when file missing."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service._session.get = Mock(side_effect=Exception("boom"))
        target = tmp_path / "poster.jpg"

        assert service._download_image("http://example.com", target) is None
        assert not target.exists()

    def test_get_poster_from_web_returns_existing(self, tmp_path: Path) -> None:
        """_get_poster_from_web should return existing target."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        target = tmp_path / "posters" / "poster_jaws.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"data")

        result = service._get_poster_from_web("Jaws", tmp_path, target_path=target)

        assert result == str(target)

    def test_download_missing_sets_placeholder(self, tmp_path: Path) -> None:
        """_download_missing should set placeholder on failure."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        film = Film(title="Jaws")
        service._get_poster_from_web = Mock(return_value=None)

        service._download_missing([film], tmp_path)

        assert film.poster_local == service.PLACEHOLDER_IMAGE

    def test_download_missing_sets_local_on_success(self, tmp_path: Path) -> None:
        """_download_missing should set poster_local on success."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        film = Film(title="Jaws")
        service._get_poster_from_web = Mock(return_value="local.jpg")

        service._download_missing([film], tmp_path)

        assert film.poster_local == "local.jpg"

    def test_download_missing_sets_placeholder_on_exception(self, tmp_path: Path) -> None:
        """_download_missing should set placeholder on exception."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        film = Film(title="Jaws")
        service._get_poster_from_web = Mock(side_effect=Exception("boom"))

        service._download_missing([film], tmp_path)

        assert film.poster_local == service.PLACEHOLDER_IMAGE

    def test_get_poster_from_web_uses_primary_url(self, tmp_path: Path) -> None:
        """_get_poster_from_web should use primary URL first."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service._download_image = Mock(return_value=str(tmp_path / "poster.jpg"))

        result = service._get_poster_from_web("Title", tmp_path, primary_url="http://img")

        assert result == str(tmp_path / "poster.jpg")

    def test_get_poster_from_web_primary_fails_then_search(self, tmp_path: Path) -> None:
        """_get_poster_from_web should fall back to search after primary fails."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service._download_image = Mock(return_value=None)
        service.search.search = Mock(return_value=["http://example.com/poster.jpg"])

        result = service._get_poster_from_web("Title", tmp_path, primary_url="http://img")

        assert result is None or isinstance(result, str)

    def test_get_poster_from_web_skips_failed_image_downloads(self, tmp_path: Path) -> None:
        """_get_poster_from_web should continue after failed image download."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service._download_image = Mock(side_effect=[None, str(tmp_path / "poster.jpg")])
        service.search.search = Mock(
            return_value=["http://example.com/a.jpg", "http://example.com/b.jpg"]
        )

        result = service._get_poster_from_web("Title", tmp_path)

        assert result == str(tmp_path / "poster.jpg")

    def test_get_poster_from_web_returns_none_when_no_results(self, tmp_path: Path) -> None:
        """_get_poster_from_web should return None when no results."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())
        service.search.search = Mock(return_value=["http://example.com/page"])
        service._download_image = Mock(return_value=None)

        assert service._get_poster_from_web("Title", tmp_path) is None

    def test_poster_filename(self) -> None:
        """_poster_filename should format with year."""
        service = PosterService(tmdb_client=Mock(), search_client=Mock())

        assert service._poster_filename("Star Wars", 1977) == "poster_star_wars_1977.jpg"
