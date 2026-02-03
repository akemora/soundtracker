"""Tests for soundtracker.services.biography."""

from unittest.mock import Mock

from soundtracker.services.biography import BiographyService


class TestBiographyService:
    """Tests for BiographyService."""

    def test_get_biography_prefers_spanish_wikipedia(self) -> None:
        """get_biography should return Spanish extract when available."""
        wikipedia = Mock()
        wikipedia.get_extract.return_value = "Texto biográfico en español."
        translator = Mock()
        search = Mock()

        service = BiographyService(
            wikipedia_client=wikipedia,
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia_en = Mock()

        result = service.get_biography("John Williams")

        assert result == "Texto biográfico en español."
        translator.to_spanish.assert_not_called()

    def test_extract_section_finds_heading(self) -> None:
        """_extract_section should return HTML under matching heading."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        html = "<h2>Musical style</h2><p>Text</p><h2>Other</h2>"

        section = service._extract_section(html, ["musical style"])

        assert "Text" in section

    def test_format_biography_filters_short_paragraphs(self) -> None:
        """_format_biography should drop short paragraphs."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=10,
        )
        text = "Short.\n\nThis is a longer paragraph with enough length."

        result = service._format_biography(text)

        assert result == "This is a longer paragraph with enough length."
