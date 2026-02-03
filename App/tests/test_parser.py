"""Tests for scripts.etl.parser."""

from pathlib import Path

from scripts.etl import parser


class TestParserHelpers:
    """Unit tests for parser helpers."""

    def test_parse_name(self) -> None:
        """parse_name should return title heading."""
        content = "# John Williams\n\n## Biografía\nTexto"
        assert parser.parse_name(content) == "John Williams"

    def test_extract_photo_path_url(self, tmp_path: Path) -> None:
        """extract_photo_path should return URL when image is remote."""
        content = "# Name\n\n![Name](https://example.com/photo.jpg)"
        url, local = parser.extract_photo_path(content, tmp_path / "001_name.md")

        assert url == "https://example.com/photo.jpg"
        assert local is None

    def test_extract_photo_path_local(self, tmp_path: Path) -> None:
        """extract_photo_path should resolve local paths when file exists."""
        photo_dir = tmp_path / "001_name"
        photo_dir.mkdir()
        photo_file = photo_dir / "photo.jpg"
        photo_file.write_text("x", encoding="utf-8")
        content = "# Name\n\n![Name](001_name/photo.jpg)"

        url, local = parser.extract_photo_path(content, tmp_path / "001_name.md")

        assert url is None
        assert local == str(photo_file)

    def test_parse_top10(self, tmp_path: Path) -> None:
        """parse_top10 should parse ranked films."""
        content = """# Name

## Top 10 bandas sonoras
1. ***Star Wars (1977)***
2. ***Jaws (Título en España: Tiburón)***
    * **Póster:** [link](posters/jaws.jpg)
"""
        result = parser.parse_top10(content, tmp_path / "001_name.md")

        assert len(result) == 2
        assert result[0].title == "Star Wars"
        assert result[0].year == 1977
        assert result[0].top10_rank == 1
        assert result[1].title == "Jaws"
        assert result[1].title_es == "Tiburón"

    def test_parse_filmography(self, tmp_path: Path) -> None:
        """parse_filmography should parse film entries."""
        content = """# Name

## Filmografía completa
- Star Wars (1977) · [Póster](posters/sw.jpg)
- Jaws (Título en España: Tiburón) (1975)
"""
        result = parser.parse_filmography(content, tmp_path / "001_name.md")

        assert len(result) == 2
        assert result[0].title == "Star Wars"
        assert result[0].year == 1977
        assert result[1].title_es == "Tiburón"

    def test_parse_awards(self) -> None:
        """parse_awards should parse awards with status."""
        content = """# Name

## Premios y nominaciones
* 1978 – Oscar – por *Star Wars* – (Ganador)
* 1980 – BAFTA – por *Superman* – (Nominación)
"""
        awards = parser.parse_awards(content)

        assert len(awards) == 2
        assert awards[0].award_name == "Oscar"
        assert awards[0].status == "win"
        assert awards[1].status == "nomination"

    def test_parse_sources(self) -> None:
        """parse_sources should parse reference links."""
        content = """# Name

## Fuentes adicionales
* [Wikipedia](https://es.wikipedia.org) — resumen
"""
        sources = parser.parse_sources(content)

        assert len(sources) == 1
        assert sources[0].name == "Wikipedia"
        assert sources[0].url == "https://es.wikipedia.org"
        assert sources[0].snippet == "resumen"

    def test_parse_snippets(self) -> None:
        """parse_snippets should parse snippet notes."""
        content = """# Name

## Notas externas
* MundoBSO: Texto breve
"""
        snippets = parser.parse_snippets(content)

        assert len(snippets) == 1
        assert snippets[0].name == "MundoBSO"
        assert snippets[0].snippet == "Texto breve"
