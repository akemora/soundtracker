"""Tests for update_top10_youtube.py script."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_top10_youtube import (
    format_top10,
    get_section,
    parse_award_titles,
    parse_filmography,
    parse_title_display,
    update_file,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_composer_md(tmp_path: Path) -> Path:
    """Create a sample composer Markdown file."""
    content = """# John Williams

## Biografía

John Williams is an American composer.

## Filmografía completa

- Jaws (1975) · [Póster](001_john_williams/posters/jaws.jpg)
- Star Wars (Título en España: La guerra de las galaxias) (1977)
- E.T. the Extra-Terrestrial (1982) · [Póster](001_john_williams/posters/et.jpg)
- Jurassic Park (1993)
- Schindler's List (1993)

## Premios y nominaciones

- 🏆 **Oscar** a la Mejor Banda Sonora por *Jaws* (1976)
- 🏆 **Oscar** a la Mejor Banda Sonora por *Star Wars* (1978)

## Top 10 bandas sonoras

1. ***Star Wars (1977)***
"""
    file_path = tmp_path / "001_john_williams.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# =============================================================================
# PARSE_TITLE_DISPLAY TESTS
# =============================================================================


class TestParseTitleDisplay:
    """Tests for parse_title_display function."""

    def test_simple_title(self) -> None:
        """Test parsing a simple title without Spanish translation."""
        result = parse_title_display("Jaws")
        assert result["original_title"] == "Jaws"
        assert result["title_es"] == "Jaws"

    def test_title_with_spanish(self) -> None:
        """Test parsing title with Spanish translation."""
        result = parse_title_display(
            "Star Wars (Título en España: La guerra de las galaxias)"
        )
        assert result["original_title"] == "Star Wars"
        assert result["title_es"] == "La guerra de las galaxias"

    def test_title_with_whitespace(self) -> None:
        """Test that whitespace is stripped."""
        result = parse_title_display("  Jaws  ")
        assert result["original_title"] == "Jaws"

    def test_title_with_parentheses(self) -> None:
        """Test title containing parentheses but not Spanish format."""
        result = parse_title_display("E.T. the Extra-Terrestrial (Director's Cut)")
        assert result["original_title"] == "E.T. the Extra-Terrestrial (Director's Cut)"


# =============================================================================
# PARSE_FILMOGRAPHY TESTS
# =============================================================================


class TestParseFilmography:
    """Tests for parse_filmography function."""

    def test_parse_simple_entries(self) -> None:
        """Test parsing simple filmography entries."""
        lines = [
            "- Jaws (1975)",
            "- Star Wars (1977)",
        ]
        result = parse_filmography(lines)

        assert len(result) == 2
        assert result[0]["original_title"] == "Jaws"
        assert result[0]["year"] == 1975
        assert result[1]["original_title"] == "Star Wars"
        assert result[1]["year"] == 1977

    def test_parse_entry_with_poster(self) -> None:
        """Test parsing entry with poster link."""
        lines = ["- Jaws (1975) · [Póster](posters/jaws.jpg)"]
        result = parse_filmography(lines)

        assert len(result) == 1
        assert result[0]["original_title"] == "Jaws"
        assert result[0]["poster_local"] == "posters/jaws.jpg"

    def test_parse_entry_with_spanish_title(self) -> None:
        """Test parsing entry with Spanish title."""
        lines = ["- Star Wars (Título en España: La guerra de las galaxias) (1977)"]
        result = parse_filmography(lines)

        assert len(result) == 1
        assert result[0]["original_title"] == "Star Wars"
        assert result[0]["title_es"] == "La guerra de las galaxias"
        assert result[0]["year"] == 1977

    def test_skip_non_list_lines(self) -> None:
        """Test that non-list lines are skipped."""
        lines = [
            "Some text",
            "- Jaws (1975)",
            "More text",
            "- Star Wars (1977)",
        ]
        result = parse_filmography(lines)
        assert len(result) == 2


# =============================================================================
# PARSE_AWARD_TITLES TESTS
# =============================================================================


class TestParseAwardTitles:
    """Tests for parse_award_titles function."""

    def test_parse_award_titles(self) -> None:
        """Test extracting film titles from award lines."""
        lines = [
            "- 🏆 **Oscar** a la Mejor Banda Sonora por *Jaws* (1976)",
            "- 🏆 **Oscar** a la Mejor Banda Sonora por *Star Wars* (1978)",
        ]
        result = parse_award_titles(lines)

        assert len(result) == 2
        assert result[0] == "Jaws"
        assert result[1] == "Star Wars"

    def test_no_awards(self) -> None:
        """Test with no matching award patterns."""
        lines = ["Some text without awards"]
        result = parse_award_titles(lines)
        assert result == []


# =============================================================================
# GET_SECTION TESTS
# =============================================================================


class TestGetSection:
    """Tests for get_section function."""

    def test_get_existing_section(self) -> None:
        """Test getting an existing section."""
        lines = [
            "# Title",
            "",
            "## Section One",
            "Content one",
            "Content two",
            "",
            "## Section Two",
            "Content three",
        ]
        result = get_section(lines, "## Section One")

        assert len(result) == 2
        assert result[0] == "Content one"
        assert result[1] == "Content two"

    def test_get_nonexistent_section(self) -> None:
        """Test getting a section that doesn't exist."""
        lines = ["# Title", "## Section One", "Content"]
        result = get_section(lines, "## Nonexistent")
        assert result == []

    def test_get_last_section(self) -> None:
        """Test getting the last section in file."""
        lines = [
            "## Section One",
            "Content one",
            "## Section Two",
            "Content two",
            "Content three",
        ]
        result = get_section(lines, "## Section Two")

        assert len(result) == 2
        assert result[0] == "Content two"
        assert result[1] == "Content three"


# =============================================================================
# FORMAT_TOP10 TESTS
# =============================================================================


class TestFormatTop10:
    """Tests for format_top10 function."""

    def test_format_entries(self) -> None:
        """Test formatting Top 10 entries."""
        entries = [
            {"original_title": "Jaws", "year": 1975, "title_es": "Tiburón"},
            {"original_title": "Star Wars", "year": 1977, "title_es": "Star Wars"},
        ]

        # Mock ccf.format_film_title
        with patch("update_top10_youtube.ccf") as mock_ccf:
            mock_ccf.format_film_title.side_effect = lambda e: f"{e['original_title']} ({e['year']})"
            result = format_top10(entries, Path("/tmp"))

        assert result[0] == "## Top 10 bandas sonoras"
        assert "1. ***Jaws (1975)***" in result
        assert "2. ***Star Wars (1977)***" in result

    def test_format_with_poster(self) -> None:
        """Test formatting entry with poster link."""
        entries = [
            {
                "original_title": "Jaws",
                "year": 1975,
                "title_es": "Tiburón",
                "poster_local": "posters/jaws.jpg",
            }
        ]

        with patch("update_top10_youtube.ccf") as mock_ccf:
            mock_ccf.format_film_title.return_value = "Jaws (1975)"
            result = format_top10(entries, Path("/tmp"))

        assert any("**Póster:**" in line for line in result)
        assert any("posters/jaws.jpg" in line for line in result)


# =============================================================================
# UPDATE_FILE TESTS
# =============================================================================


class TestUpdateFile:
    """Tests for update_file function."""

    def test_update_file_empty(self, tmp_path: Path) -> None:
        """Test handling empty file."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("", encoding="utf-8")

        result = update_file(empty_file)
        assert result is False

    def test_update_file_no_filmography(self, tmp_path: Path) -> None:
        """Test handling file without filmography section."""
        no_film = tmp_path / "001_test.md"
        no_film.write_text("# Test Composer\n\n## Biografía\n\nSome text.", encoding="utf-8")

        result = update_file(no_film)
        assert result is False

    def test_update_file_nonexistent(self, tmp_path: Path) -> None:
        """Test handling nonexistent file."""
        missing = tmp_path / "nonexistent.md"
        result = update_file(missing)
        assert result is False
