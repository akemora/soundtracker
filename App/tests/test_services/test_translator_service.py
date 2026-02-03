"""Tests for soundtracker.services.translator."""

from unittest.mock import Mock

from soundtracker.services.translator import TranslatorService


class TestTranslatorService:
    """Tests for TranslatorService."""

    def test_translate_detect_returns_translation(self) -> None:
        """translate_detect should return translated text and detected language."""
        service = TranslatorService()
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=[[["Hola", "Hello", None, None, 1]], None, "en"])
        service._session.get = Mock(return_value=response)

        translated, detected = service.translate_detect("Hello", "es")

        assert translated == "Hola"
        assert detected == "en"

    def test_should_translate_english_vs_spanish(self) -> None:
        """should_translate should flag English and skip Spanish."""
        service = TranslatorService()

        english = "He was a composer and he was born in 1932."
        spanish = "El compositor nació en 1932 y vivió en España."

        assert service.should_translate(english) is True
        assert service.should_translate(spanish) is False
