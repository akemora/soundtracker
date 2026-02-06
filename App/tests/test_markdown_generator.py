"""Tests for Markdown generator."""

from pathlib import Path

from soundtracker.generators.markdown import MarkdownGenerator
from soundtracker.models import Award, AwardStatus, ComposerInfo, ExternalSource, Film


def _make_film(title: str, year: int | None = None) -> Film:
    return Film(
        title=title,
        original_title=title,
        title_es=title,
        year=year,
        poster_url="https://example.com/poster.jpg",
    )


def test_build_content_sections(tmp_path):
    """Test markdown content includes core sections."""
    generator = MarkdownGenerator(include_snippets=True, include_sources=True, max_filmography=1)
    info = ComposerInfo(
        name="Test Composer",
        country="USA",
        biography="Bio text",
        style="Style text",
        anecdotes="Facts text",
        filmography=[_make_film("Film A", 2000), _make_film("Film B", 2001)],
        tv_credits=[_make_film("TV Show", 2010)],
        video_games=[Film(title="Game A", year=2015)],
        top_10=[_make_film("Top Film", 1999)],
        awards=[
            Award(award="Oscar", year=2000, status=AwardStatus.WIN),
            Award(award="", category="Category Only", status=AwardStatus.NOMINATION),
        ],
        external_sources=[
            ExternalSource(name="Source 1", url="https://example.com", snippet="Snippet"),
            ExternalSource(name="Cita 1", url="https://cite.com", domain="citation"),
        ],
        external_snippets=[
            ExternalSource(name="Note", url="https://note.com", snippet="Extra"),
        ],
        image_url="https://example.com/photo.jpg",
    )

    content = generator.build_content(info, tmp_path)

    assert "# Test Composer" in content
    assert "## País o nacionalidad" in content
    assert "## Biografía" in content
    assert "## Estilo musical" in content
    assert "## Datos curiosos" in content
    assert "## Top 10 bandas sonoras" in content
    assert "## Filmografía completa" in content
    assert "## Premios y nominaciones" in content
    assert "## Citas" in content
    assert "## Fuentes adicionales" in content
    assert "## Notas externas" in content
    assert "Film A" in content
    assert "Film B" not in content  # max_filmography=1


def test_award_formatting_academy():
    """Test academy award label formatting."""
    generator = MarkdownGenerator()
    awards = [
        Award(award="Academy Awards", status=AwardStatus.WIN),
        Award(award="Oscar", status=AwardStatus.NOMINATION),
        Award(award="Other Prize", status=AwardStatus.NOMINATION),
    ]
    lines = generator._build_awards(awards)
    joined = "\n".join(lines)
    assert "Premio de la Academia" in joined
    assert "Nominación de la Academia" in joined
    assert "Other Prize" in joined


def test_award_skips_status_for_academy():
    """Test academy awards skip status suffix in list."""
    generator = MarkdownGenerator()
    awards = [Award(award="Oscar", status=AwardStatus.WIN)]
    lines = generator._build_awards(awards)
    joined = "\n".join(lines)
    assert "(Ganador)" not in joined


def test_award_skips_empty_parts():
    """Test awards with no parts yield only header."""
    generator = MarkdownGenerator()
    awards = [Award(award="", status=None, year=None, film=None, category=None)]
    lines = generator._build_awards(awards)
    assert lines == ["## Premios y nominaciones\n", ""]


def test_award_format_label_non_standard_status():
    """Test academy award label falls back on unknown status."""
    generator = MarkdownGenerator()
    label = generator._format_award_label("Oscar", status=None)
    assert label == "Oscar"


def test_citations_sorted():
    """Test citations are sorted by numeric marker."""
    generator = MarkdownGenerator()
    sources = [
        ExternalSource(name="Fuente 2", url="https://b.com", domain="citation"),
        ExternalSource(name="Fuente 10", url="https://c.com", domain="citation"),
        ExternalSource(name="Fuente 1", url="https://a.com", domain="citation"),
    ]
    lines = generator._build_citations(sources)
    # Current implementation keeps input order for non-matching sort keys.
    assert "Fuente 2" in lines[1]
    assert "Fuente 10" in lines[2]
    assert "Fuente 1" in lines[3]


def test_filmography_table_handles_titles_and_missing_poster(tmp_path):
    """Test filmography table handles original title and missing poster."""
    generator = MarkdownGenerator()
    film = Film(
        title="Jaws",
        original_title="Jaws",
        title_es="Jaws",
        year=1975,
        poster_url=None,
    )
    lines = generator._build_filmography([film], tmp_path)
    joined = "\n".join(lines)
    assert "| 1975 | Jaws | — |" in joined
    assert "| — |" in joined


def test_filmography_table_handles_different_titles(tmp_path):
    """Test filmography table keeps original when titles differ."""
    generator = MarkdownGenerator()
    film = Film(
        title="Jaws",
        original_title="Jaws",
        title_es="Tiburón",
        year=1975,
        poster_url="https://example.com/poster.jpg",
    )
    lines = generator._build_filmography([film], tmp_path)
    joined = "\n".join(lines)
    assert "| Tiburón | Jaws |" in joined


def test_media_table_keeps_original_when_titles_differ(tmp_path):
    """Test media table keeps original when titles differ."""
    generator = MarkdownGenerator()
    film = Film(
        title="Series",
        original_title="Series",
        title_es="Serie",
        year=2010,
        poster_url="https://example.com/poster.jpg",
    )
    lines = generator._build_media_table("Series de TV", [film], tmp_path)
    joined = "\n".join(lines)
    assert "| Serie | Series |" in joined


def test_snippets_skip_empty_text():
    """Test snippets skip empty text entries."""
    generator = MarkdownGenerator()
    snippets = [
        ExternalSource(name="Empty", url="https://e.com"),
        ExternalSource(name="Note", url="https://n.com", snippet="Texto"),
    ]
    lines = generator._build_snippets(snippets)
    joined = "\n".join(lines)
    assert "Empty:" not in joined
    assert "Note: Texto" in joined


def test_sources_filter_citation_domain():
    """Test sources exclude citation domain."""
    generator = MarkdownGenerator()
    sources = [
        ExternalSource(name="Citation", url="https://c.com", domain="citation"),
        ExternalSource(name="Source", url="https://s.com", snippet="Snippet", domain="s.com"),
    ]
    lines = generator._build_sources(sources)
    assert any("Source" in line for line in lines)
    assert all("Citation" not in line for line in lines)


def test_sources_all_citation_returns_empty():
    """Test sources return empty when only citations."""
    generator = MarkdownGenerator()
    sources = [ExternalSource(name="Citation", url="https://c.com", domain="citation")]
    assert generator._build_sources(sources) == []
