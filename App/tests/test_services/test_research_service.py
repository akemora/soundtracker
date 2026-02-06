"""Tests for soundtracker.services.research."""

from unittest.mock import Mock

from soundtracker.services.research import ResearchService
from soundtracker.config import settings


class TestResearchService:
    """Tests for ResearchService."""

    def test_is_enabled_false_when_disabled(self, monkeypatch) -> None:
        """is_enabled should be False when feature disabled."""
        monkeypatch.setattr(settings, "deep_research_enabled", False)
        service = ResearchService(api_key="key")

        assert service.is_enabled is False

    def test_get_profile_returns_none_when_disabled(self, monkeypatch) -> None:
        """get_profile should return None when disabled."""
        monkeypatch.setattr(settings, "deep_research_enabled", False)
        service = ResearchService(api_key="key")

        assert service.get_profile("John Williams") is None

    def test_get_profile_parses_json(self, monkeypatch) -> None:
        """get_profile should parse JSON response."""
        monkeypatch.setattr(settings, "deep_research_enabled", True)
        service = ResearchService(api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"biography": {"text": "Bio", "citations": ["a"]}, '
                                '"style": {"text": "Style", "citations": ["b"]}, '
                                '"facts": {"text": "Facts", "citations": ["c"]}}'
                            )
                        }
                    }
                ]
            }
        )
        service.session.post = Mock(return_value=response)

        profile = service.get_profile("John Williams")

        assert profile is not None
        assert profile.biography.text == "Bio"
        assert profile.style.citations == ["b"]

    def test_get_profile_fallback_citations(self, monkeypatch) -> None:
        """get_profile should fall back to citations when JSON invalid."""
        monkeypatch.setattr(settings, "deep_research_enabled", True)
        service = ResearchService(api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={"choices": [{"message": {"content": "not json"}}], "citations": ["a"]}
        )
        service.session.post = Mock(return_value=response)

        profile = service.get_profile("John Williams")

        assert profile is not None
        assert profile.biography.citations == ["a"]

    def test_get_profile_fallback_with_empty_choices(self, monkeypatch) -> None:
        """get_profile should handle empty choices."""
        monkeypatch.setattr(settings, "deep_research_enabled", True)
        service = ResearchService(api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"choices": [], "citations": ["a"]})
        service.session.post = Mock(return_value=response)

        profile = service.get_profile("John Williams")

        assert profile is not None

    def test_get_profile_returns_none_without_citations(self, monkeypatch) -> None:
        """get_profile should return None when no citations."""
        monkeypatch.setattr(settings, "deep_research_enabled", True)
        service = ResearchService(api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"choices": [{"message": {"content": "bad"}}]})
        service.session.post = Mock(return_value=response)

        assert service.get_profile("John Williams") is None

    def test_get_profile_handles_exception(self, monkeypatch) -> None:
        """get_profile should return None on request error."""
        monkeypatch.setattr(settings, "deep_research_enabled", True)
        service = ResearchService(api_key="key")
        service.session.post = Mock(side_effect=Exception("boom"))

        assert service.get_profile("John Williams") is None

    def test_parse_json_extracts_block(self) -> None:
        """_parse_json should extract JSON block from text."""
        service = ResearchService(api_key="key")
        content = "prefix {\"biography\": {\"text\": \"Bio\"}} suffix"

        parsed = service._parse_json(content)

        assert parsed is not None
        assert parsed["biography"]["text"] == "Bio"

    def test_parse_json_returns_none_when_empty(self) -> None:
        """_parse_json should return None for empty content."""
        service = ResearchService(api_key="key")

        assert service._parse_json("") is None

    def test_parse_json_returns_none_when_no_match(self) -> None:
        """_parse_json should return None when no JSON block."""
        service = ResearchService(api_key="key")

        assert service._parse_json("not json here") is None

    def test_parse_json_invalid_block_returns_none(self) -> None:
        """_parse_json should return None for invalid JSON block."""
        service = ResearchService(api_key="key")

        assert service._parse_json("prefix {bad json} suffix") is None

    def test_dedupe_filters_empty(self) -> None:
        """_dedupe should filter empties and duplicates."""
        assert ResearchService._dedupe(["a", "a", "", "b"]) == ["a", "b"]
