"""Tests for soundtracker.clients.wikidata."""

from unittest.mock import Mock

from soundtracker.clients.wikidata import WikidataClient
from soundtracker.models import AwardStatus


class TestWikidataClient:
    """Tests for WikidataClient."""

    def test_health_check_returns_true_on_response(self) -> None:
        """Health check should return True when API responds."""
        client = WikidataClient()
        client._get = Mock(return_value={})

        assert client.health_check() is True

    def test_get_qid_returns_id(self) -> None:
        """Get QID should return the first search ID."""
        client = WikidataClient()
        client._get = Mock(return_value={"search": [{"id": "Q123"}]})

        assert client.get_qid("John Williams") == "Q123"

    def test_get_qid_returns_none_when_missing(self) -> None:
        """Get QID should return None if no results."""
        client = WikidataClient()
        client._get = Mock(return_value={"search": []})

        assert client.get_qid("Missing") is None

    def test_get_filmography_parses_films(self) -> None:
        """Filmography should parse films and skip invalid titles."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {
                            "filmLabel": {"value": "Star Wars"},
                            "labelEn": {"value": "Star Wars"},
                            "labelEs": {"value": "La guerra de las galaxias"},
                            "year": {"value": "1977"},
                        },
                        {
                            "filmLabel": {"value": "Q123"},
                            "labelEn": {"value": "Q123"},
                        },
                    ]
                }
            }
        )

        films = client.get_filmography("Q1")

        assert len(films) == 1
        assert films[0].title == "Star Wars"
        assert films[0].title_es == "La guerra de las galaxias"
        assert films[0].year == 1977

    def test_get_awards_maps_status(self) -> None:
        """Awards should map Win/Nomination correctly."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {
                            "awardLabel": {"value": "Oscar"},
                            "year": {"value": "1978"},
                            "workLabel": {"value": "Star Wars"},
                            "status": {"value": "Win"},
                        },
                        {
                            "awardLabel": {"value": "BAFTA"},
                            "status": {"value": "Nomination"},
                        },
                    ]
                }
            }
        )

        awards = client.get_awards("Q1")

        assert len(awards) == 2
        assert awards[0].status == AwardStatus.WIN
        assert awards[1].status == AwardStatus.NOMINATION

    def test_get_birth_death_years(self) -> None:
        """Birth/death years should be parsed from SPARQL results."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {
                            "birthYear": {"value": "1932"},
                            "deathYear": {"value": "2023"},
                        }
                    ]
                }
            }
        )

        birth, death = client.get_birth_death_years("Q1")

        assert birth == 1932
        assert death == 2023

    def test_get_country_returns_label(self) -> None:
        """Country should return the label value."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {"bindings": [{"countryLabel": {"value": "USA"}}]}
            }
        )

        assert client.get_country("Q1") == "USA"
