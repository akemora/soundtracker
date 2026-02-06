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

    def test_health_check_returns_false_on_failure(self) -> None:
        """Health check should return False when API fails."""
        client = WikidataClient()
        client._get = Mock(return_value=None)

        assert client.health_check() is False

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

    def test_get_qid_returns_none_when_no_data(self) -> None:
        """Get QID should return None when request fails."""
        client = WikidataClient()
        client._get = Mock(return_value=None)

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

    def test_get_filmography_handles_invalid_year(self) -> None:
        """Filmography should handle invalid year values."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {
                            "filmLabel": {"value": "Test Film"},
                            "year": {"value": "bad"},
                        }
                    ]
                }
            }
        )

        films = client.get_filmography("Q1")

        assert len(films) == 1
        assert films[0].year is None

    def test_get_filmography_handles_missing_year(self) -> None:
        """Filmography should handle missing year values."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {"filmLabel": {"value": "No Year Film"}},
                    ]
                }
            }
        )

        films = client.get_filmography("Q1")

        assert len(films) == 1
        assert films[0].year is None

    def test_get_filmography_handles_missing_data(self) -> None:
        """Filmography should return empty when data missing."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        assert client.get_filmography("Q1") == []

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

    def test_get_awards_skips_missing_award_name(self) -> None:
        """Awards should skip entries without award label."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {"status": {"value": "Win"}},
                        {"awardLabel": {"value": "Oscar"}, "status": {"value": "Win"}},
                    ]
                }
            }
        )

        awards = client.get_awards("Q1")

        assert len(awards) == 1
        assert awards[0].award == "Oscar"

    def test_get_awards_handles_invalid_year(self) -> None:
        """Awards should handle invalid year values."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {"awardLabel": {"value": "Oscar"}, "year": {"value": "bad"}}
                    ]
                }
            }
        )

        awards = client.get_awards("Q1")

        assert len(awards) == 1
        assert awards[0].year is None

    def test_get_awards_handles_missing_data(self) -> None:
        """Awards should return empty when data missing."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        assert client.get_awards("Q1") == []

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

    def test_get_birth_death_years_handles_invalid_values(self) -> None:
        """Birth/death years should ignore invalid values."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {"birthYear": {"value": "bad"}, "deathYear": {"value": "nope"}}
                    ]
                }
            }
        )

        birth, death = client.get_birth_death_years("Q1")

        assert birth is None
        assert death is None

    def test_get_birth_death_years_handles_missing_birth(self) -> None:
        """Birth/death years should handle missing birth year."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {"bindings": [{"deathYear": {"value": "2020"}}]}
            }
        )

        birth, death = client.get_birth_death_years("Q1")

        assert birth is None
        assert death == 2020

    def test_get_birth_death_years_handles_missing_death(self) -> None:
        """Birth/death years should handle missing death year."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {"bindings": [{"birthYear": {"value": "1950"}}]}
            }
        )

        birth, death = client.get_birth_death_years("Q1")

        assert birth == 1950
        assert death is None

    def test_get_birth_death_years_handles_missing(self) -> None:
        """Birth/death years should return (None, None) when missing."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        assert client.get_birth_death_years("Q1") == (None, None)

    def test_get_birth_death_years_handles_empty_bindings(self) -> None:
        """Birth/death years should return (None, None) when no bindings."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value={"results": {"bindings": []}})

        assert client.get_birth_death_years("Q1") == (None, None)

    def test_get_birth_death_dates_handles_missing(self) -> None:
        """Birth/death dates should return (None, None) when missing."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        assert client.get_birth_death_dates("Q1") == (None, None)

    def test_get_birth_death_dates_parses_values(self) -> None:
        """Birth/death dates should parse values when available."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={"results": {"bindings": [{"birthDate": {"value": "1932-02-08"}}]}}
        )

        birth, death = client.get_birth_death_dates("Q1")
        assert birth == "1932-02-08"
        assert death is None

    def test_get_birth_death_dates_handles_empty_bindings(self) -> None:
        """Birth/death dates should return None when bindings empty."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value={"results": {"bindings": []}})

        assert client.get_birth_death_dates("Q1") == (None, None)

    def test_get_country_returns_label(self) -> None:
        """Country should return the label value."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {"bindings": [{"countryLabel": {"value": "USA"}}]}
            }
        )

        assert client.get_country("Q1") == "USA"

    def test_get_country_returns_none_when_no_bindings(self) -> None:
        """Country should return None when bindings empty."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value={"results": {"bindings": []}})

        assert client.get_country("Q1") is None

    def test_get_country_returns_none_when_missing(self) -> None:
        """Country should return None when no data."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        assert client.get_country("Q1") is None

    def test_get_person_summary_returns_defaults(self) -> None:
        """get_person_summary should return defaults when missing."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value=None)

        summary = client.get_person_summary("Q1")

        assert summary["birth"] is None
        assert summary["wins"] is None

    def test_get_person_summary_returns_defaults_when_empty_bindings(self) -> None:
        """get_person_summary should return defaults when bindings empty."""
        client = WikidataClient()
        client._sparql_query = Mock(return_value={"results": {"bindings": []}})

        summary = client.get_person_summary("Q1")

        assert summary["country"] is None
        assert summary["nominations"] is None

    def test_get_person_summary_returns_data(self) -> None:
        """get_person_summary should return parsed values."""
        client = WikidataClient()
        client._sparql_query = Mock(
            return_value={
                "results": {
                    "bindings": [
                        {
                            "birthDate": {"value": "1932-02-08"},
                            "deathDate": {"value": "2023-01-01"},
                            "countryLabel": {"value": "USA"},
                            "wins": {"value": "5"},
                            "noms": {"value": "10"},
                        }
                    ]
                }
            }
        )

        summary = client.get_person_summary("Q1")

        assert summary["country"] == "USA"
        assert summary["wins"] == "5"

    def test_sparql_query_handles_exception(self) -> None:
        """_sparql_query should return None on request error."""
        client = WikidataClient()
        client.session.get = Mock(side_effect=Exception("boom"))

        assert client._sparql_query("SELECT * WHERE {}") is None

    def test_sparql_query_returns_data(self) -> None:
        """_sparql_query should return parsed JSON on success."""
        client = WikidataClient()
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"ok": True})
        client.session.get = Mock(return_value=response)

        assert client._sparql_query("SELECT * WHERE {}") == {"ok": True}
