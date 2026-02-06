"""Tests for soundtracker.services.awards."""

from unittest.mock import Mock

from soundtracker.models import Award, AwardStatus
from soundtracker.services.awards import AwardsService


class TestAwardsService:
    """Tests for AwardsService."""

    def test_parse_award_line_extracts_fields(self) -> None:
        """_parse_award_line should parse award details."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        award = service._parse_award_line("1995 Oscar win for Titanic")

        assert award is not None
        assert award.award == "Oscar"
        assert award.year == 1995
        assert award.film == "Titanic"
        assert award.status == AwardStatus.WIN

    def test_dedupe_and_translate(self) -> None:
        """_dedupe_and_translate should dedupe and translate awards."""
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: f"ES-{text}")
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=translator,
        )

        awards = [
            Award(award="Oscar", year=1995, film="Titanic", status=AwardStatus.WIN),
            Award(award="Oscar", year=1995, film="Titanic", status=AwardStatus.WIN),
        ]

        result = service._dedupe_and_translate(awards)

        assert len(result) == 1
        assert result[0].award == "ES-Oscar"

    def test_get_awards_prefers_wikidata(self) -> None:
        """get_awards should return wikidata awards when available."""
        wikidata = Mock()
        wikidata.get_qid.return_value = "Q1"
        wikidata.get_awards.return_value = [
            Award(award="Oscar", year=1995, film="Titanic", status=AwardStatus.WIN)
        ]
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: f"ES-{text}")

        service = AwardsService(
            wikidata_client=wikidata,
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=translator,
        )

        result = service.get_awards("John Williams")

        assert len(result) == 1
        assert result[0].award == "ES-Oscar"

    def test_get_awards_wikipedia_fallback(self) -> None:
        """get_awards should fall back to Wikipedia."""
        wikidata = Mock()
        wikidata.get_qid.return_value = None
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(
            return_value="<h2>Awards</h2><ul><li>1995 Oscar win for Titanic</li></ul>"
        )
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: f"ES-{text}")

        service = AwardsService(
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=Mock(),
            translator=translator,
        )
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        result = service.get_awards("John Williams")

        assert result[0].award.startswith("ES-")

    def test_get_awards_search_fallback(self) -> None:
        """get_awards should fall back to search."""
        wikidata = Mock()
        wikidata.get_qid.return_value = None
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(return_value=None)
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(
            return_value="<html><body>1995 Oscar win for Titanic</body></html>"
        )
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=search,
            translator=translator,
        )
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        result = service.get_awards("John Williams")

        assert len(result) == 1

    def test_get_awards_wikidata_empty_then_wikipedia(self) -> None:
        """get_awards should continue when wikidata returns empty."""
        wikidata = Mock()
        wikidata.get_qid.return_value = "Q1"
        wikidata.get_awards.return_value = []
        wikipedia = Mock()
        wikipedia.fetch_html = Mock(
            return_value="<h2>Awards</h2><ul><li>1995 Oscar win for Titanic</li></ul>"
        )
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=wikidata,
            wikipedia_client=wikipedia,
            search_client=Mock(),
            translator=translator,
        )
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        result = service.get_awards("John Williams")

        assert len(result) == 1

    def test_get_from_wikipedia_returns_empty_when_no_section(self) -> None:
        """_get_from_wikipedia should return empty when no section."""
        wiki = Mock()
        wiki.fetch_html = Mock(return_value="<h2>Biography</h2><p>Text</p>")
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=wiki,
            search_client=Mock(),
            translator=Mock(),
        )
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        assert service._get_from_wikipedia("Composer") == []

    def test_get_from_wikipedia_skips_non_award_lines(self) -> None:
        """_get_from_wikipedia should skip lines without awards."""
        wiki = Mock()
        wiki.fetch_html = Mock(
            return_value="<h2>Awards</h2><ul><li>Some unrelated text</li></ul>"
        )
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=wiki,
            search_client=Mock(),
            translator=Mock(),
        )
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        assert service._get_from_wikipedia("Composer") == []

    def test_extract_section_stops_at_next_heading(self) -> None:
        """_extract_section should stop at next heading."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        html = "<h2>Awards</h2><p>A</p><h2>Other</h2><p>B</p>"

        section = service._extract_section(html)

        assert "A" in section
        assert "B" not in section

    def test_search_awards_handles_empty_html(self) -> None:
        """_search_awards should handle empty html results."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="")
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_awards("Composer") == []

    def test_search_awards_skips_non_award_lines(self) -> None:
        """_search_awards should skip non-award lines."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<html><body>Nothing here</body></html>")
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_awards("Composer") == []

    def test_search_awards_breaks_on_first_results(self) -> None:
        """_search_awards should stop after finding awards."""
        search = Mock()
        search.search = Mock(return_value=["http://a", "http://b"])
        search.fetch_url_text = Mock(
            side_effect=[
                "<html><body>Nothing</body></html>",
                "<html><body>1995 Oscar win for Titanic</body></html>",
            ]
        )
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        awards = service._search_awards("Composer")

        assert len(awards) == 1

    def test_dedupe_and_translate_skips_missing_award(self) -> None:
        """_dedupe_and_translate should skip translation for empty award."""
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: f"ES-{text}")
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=translator,
        )

        awards = [
            Award(award=None, year=1995, film="Titanic", status=AwardStatus.WIN),
            Award(award="Oscar", year=1990, film="Jaws", status=AwardStatus.WIN),
        ]

        result = service._dedupe_and_translate(awards)

        assert result[0].award is None or result[0].award.startswith("ES-")

    def test_parse_award_line_returns_none_without_keywords(self) -> None:
        """_parse_award_line should return None without keywords."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        assert service._parse_award_line("1995 Best Score for Titanic") is None

    def test_parse_award_line_invalid_year_returns_none(self) -> None:
        """_parse_award_line should reject invalid year."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        assert service._parse_award_line("2099 Oscar for Movie") is None

    def test_parse_award_line_nomination_status(self) -> None:
        """_parse_award_line should default to nomination."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        award = service._parse_award_line("1999 Golden Globe for Film")

        assert award is not None
        assert award.status == AwardStatus.NOMINATION

    def test_get_from_wikipedia_returns_empty_without_html(self) -> None:
        """_get_from_wikipedia should return empty when no html."""
        wiki = Mock()
        wiki.fetch_html = Mock(return_value=None)
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=wiki,
            search_client=Mock(),
            translator=Mock(),
        )
        service.wikipedia_en = Mock()
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        assert service._get_from_wikipedia("John Williams") == []

    def test_get_from_wikipedia_uses_en_fallback(self) -> None:
        """_get_from_wikipedia should fall back to English."""
        wiki = Mock()
        wiki.fetch_html = Mock(return_value=None)
        wiki_en = Mock()
        wiki_en.fetch_html = Mock(
            return_value="<h2>Awards</h2><ul><li>1995 Oscar win for Titanic</li></ul>"
        )
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=wiki,
            search_client=Mock(),
            translator=Mock(),
        )
        service.wikipedia_en = wiki_en

        awards = service._get_from_wikipedia("John Williams")

        assert len(awards) == 1
        assert awards[0].award == "Oscar"

    def test_extract_section_returns_empty_when_missing(self) -> None:
        """_extract_section should return empty when no heading matches."""
        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        html = "<h2>Biography</h2><p>Text</p>"

        assert service._extract_section(html) == ""

    def test_search_awards_fallback(self) -> None:
        """_search_awards should parse awards from search results."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(
            return_value="<html><body>1995 Oscar win for Titanic</body></html>"
        )
        translator = Mock()
        translator.to_spanish = Mock(side_effect=lambda text: text)

        service = AwardsService(
            wikidata_client=Mock(),
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        awards = service._search_awards("John Williams")

        assert len(awards) == 1
