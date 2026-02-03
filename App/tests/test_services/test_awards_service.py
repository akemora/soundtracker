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
