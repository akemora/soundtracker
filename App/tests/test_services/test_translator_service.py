"""Tests for soundtracker.services.translator."""

from unittest.mock import Mock

import requests

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

    def test_translate_empty_returns_input(self) -> None:
        """translate should return input for empty text."""
        service = TranslatorService()

        assert service.translate("") == ""

    def test_translate_calls_translate_detect(self) -> None:
        """translate should use translate_detect."""
        service = TranslatorService()
        service.translate_detect = Mock(return_value=("Hola", "en"))

        assert service.translate("Hello", "es") == "Hola"

    def test_translate_detect_handles_error(self) -> None:
        """translate_detect should return original on request error."""
        service = TranslatorService()
        service._session.get = Mock(side_effect=requests.RequestException("boom"))

        translated, detected = service.translate_detect("Hello", "es")

        assert translated == "Hello"
        assert detected == ""

    def test_translate_detect_handles_bad_json(self) -> None:
        """translate_detect should return original on bad JSON."""
        service = TranslatorService()
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(side_effect=ValueError("bad"))
        service._session.get = Mock(return_value=response)

        translated, detected = service.translate_detect("Hello", "es")

        assert translated == "Hello"
        assert detected == ""

    def test_translate_detect_empty_text(self) -> None:
        """translate_detect should return empty when text empty."""
        service = TranslatorService()

        translated, detected = service.translate_detect("", "es")

        assert translated == ""
        assert detected == ""

    def test_translate_detect_handles_no_detected_language(self) -> None:
        """translate_detect should handle missing detected language."""
        service = TranslatorService()
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=[[["Hola", "Hello", None, None, 1]], None, None])
        service._session.get = Mock(return_value=response)

        translated, detected = service.translate_detect("Hello", "es")

        assert translated == "Hola"
        assert detected == ""

    def test_translate_detect_skips_empty_parts(self) -> None:
        """translate_detect should skip empty parts."""
        service = TranslatorService()
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value=[[[None, "Hello", None, None, 1]], None, "en"])
        service._session.get = Mock(return_value=response)

        translated, _ = service.translate_detect("Hello", "es")

        assert translated == "Hello"

    def test_to_spanish_returns_original_when_detected(self) -> None:
        """to_spanish should return original when detected Spanish."""
        service = TranslatorService()
        service.translate_detect = Mock(return_value=("Hola", "es"))

        assert service.to_spanish("Hola") == "Hola"

    def test_to_spanish_empty(self) -> None:
        """to_spanish should return empty when text empty."""
        service = TranslatorService()

        assert service.to_spanish("") == ""

    def test_to_spanish_returns_translated(self) -> None:
        """to_spanish should return translated when not Spanish."""
        service = TranslatorService()
        service.translate_detect = Mock(return_value=("Hola", "en"))

        assert service.to_spanish("Hello") == "Hola"

    def test_to_english_uses_translate(self) -> None:
        """to_english should use translate."""
        service = TranslatorService()
        service.translate = Mock(return_value="Hello")

        assert service.to_english("Hola") == "Hello"

    def test_ensure_spanish_translates_when_needed(self) -> None:
        """ensure_spanish should translate when needed."""
        service = TranslatorService()
        service.translate_detect = Mock(return_value=("Hola", "en"))

        assert service.ensure_spanish("Hello") == "Hola"

    def test_ensure_spanish_empty(self) -> None:
        """ensure_spanish should return empty when text empty."""
        service = TranslatorService()

        assert service.ensure_spanish("") == ""

    def test_ensure_spanish_returns_original_when_detected(self) -> None:
        """ensure_spanish should return original when detected Spanish."""
        service = TranslatorService()
        service.translate_detect = Mock(return_value=("Hola", "es"))

        assert service.ensure_spanish("Hola") == "Hola"

    def test_translate_paragraphs_filters_empty(self) -> None:
        """translate_paragraphs should skip empty entries."""
        service = TranslatorService()
        service.to_spanish = Mock(side_effect=lambda text: f"ES-{text}")

        assert service.translate_paragraphs(["a", "", "b"]) == ["ES-a", "ES-b"]

    def test_should_translate_spanish_chars(self) -> None:
        """should_translate should skip when many Spanish chars."""
        service = TranslatorService()
        text = "áéíóúñü¿¡"

        assert service.should_translate(text) is False
