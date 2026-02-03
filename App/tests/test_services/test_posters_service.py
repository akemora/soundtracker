"""Tests for soundtracker.services.posters."""

from pathlib import Path
from unittest.mock import Mock

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
