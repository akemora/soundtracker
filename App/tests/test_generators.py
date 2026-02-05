"""Tests for soundtracker.generators module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from soundtracker.generators.markdown import MarkdownGenerator, generate_composer_file
from soundtracker.models import Award, AwardStatus, ComposerInfo, ExternalSource, Film


class TestMarkdownGenerator:
    """Tests for MarkdownGenerator class."""

    def test_basic_generation(self):
        """Test basic Markdown generation."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                biography="A legendary composer known for Star Wars.",
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            assert output_path.exists()
            content = output_path.read_text()

            assert "# John Williams" in content
            assert "## País o nacionalidad" in content
            assert "## Biografía" in content
            assert "A legendary composer" in content
            assert "## Estilo musical" in content
            assert "## Datos curiosos y técnica de composición" in content

    def test_with_photo(self):
        """Test generation with photo."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                image_url="https://example.com/photo.jpg",
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "![John Williams]" in content
            assert "photo.jpg" in content

    def test_with_style(self):
        """Test generation with musical style."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                style="Orchestral, thematic compositions.",
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Estilo musical" in content
            assert "Orchestral" in content

    def test_with_anecdotes(self):
        """Test generation with anecdotes."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                anecdotes="He was born in 1932.",
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Datos curiosos y técnica de composición" in content
            assert "1932" in content

    def test_with_top10(self):
        """Test generation with top 10 films."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                top_10=[
                    Film(title="Star Wars", original_title="Star Wars", year=1977),
                    Film(title="E.T.", original_title="E.T.", year=1982),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Top 10" in content
            assert "Star Wars" in content
            assert "(1977)" in content
            assert "E.T." in content
            assert "1." in content
            assert "2." in content

    def test_with_filmography(self):
        """Test generation with filmography."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                filmography=[
                    Film(title="Star Wars", year=1977),
                    Film(title="Jaws", year=1975),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Filmografía completa" in content
            assert "| Año | Título | Título original | Traducción literal (ES) | Título en España | Póster |" in content
            assert "| 1977 |" in content
            assert "Star Wars" in content

    def test_with_awards(self):
        """Test generation with awards."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                awards=[
                    Award(award="Oscar", year=1978, film="Star Wars", status=AwardStatus.WIN),
                    Award(award="Grammy", year=1980, status=AwardStatus.NOMINATION),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Premios" in content
            assert "Premio de la Academia" in content
            assert "1978" in content
            assert "Grammy" in content
            assert "Nominación" in content

    def test_with_external_sources(self):
        """Test generation with external sources."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                external_sources=[
                    ExternalSource(name="IMDb", url="https://imdb.com", snippet="Actor filmography"),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Fuentes adicionales" in content
            assert "[IMDb]" in content
            assert "imdb.com" in content

    def test_with_external_snippets(self):
        """Test generation with external snippets."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                external_snippets=[
                    ExternalSource(
                        name="MundoBSO",
                        url="https://mundobso.com",
                        text="Great soundtrack resource.",
                    ),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Notas externas" in content
            assert "MundoBSO" in content
            assert "Great soundtrack" in content

    def test_options(self):
        """Test generator options."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                external_sources=[
                    ExternalSource(name="Test", url="https://test.com"),
                ],
                external_snippets=[
                    ExternalSource(name="Snippet", url="https://s.com", text="Text"),
                ],
            )

            generator = MarkdownGenerator(
                include_sources=False,
                include_snippets=False,
            )
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "## Fuentes adicionales" not in content
            assert "## Notas externas" not in content

    def test_filmography_limit(self):
        """Test max_filmography option."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="John Williams",
                filmography=[Film(title=f"Film {i}", year=2000 + i) for i in range(20)],
            )

            generator = MarkdownGenerator(max_filmography=5)
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "Film 4" in content
            assert "Film 5" not in content


class TestGenerateComposerFile:
    """Tests for generate_composer_file convenience function."""

    def test_basic_usage(self):
        """Test basic convenience function usage."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="Hans Zimmer",
                biography="Known for epic film scores.",
            )

            generate_composer_file(info, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "# Hans Zimmer" in content

    def test_with_options(self):
        """Test convenience function with options."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="Hans Zimmer",
                external_sources=[
                    ExternalSource(name="Test", url="https://test.com"),
                ],
            )

            generate_composer_file(info, output_path, include_sources=False)

            content = output_path.read_text()
            assert "## Fuentes adicionales" not in content


class TestMarkdownFormatting:
    """Tests for Markdown formatting details."""

    def test_film_title_formatting(self):
        """Test film title with Spanish translation."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="Test",
                filmography=[
                    Film(
                        title="Star Wars",
                        original_title="Star Wars",
                        title_es="La Guerra de las Galaxias",
                    ),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "Star Wars" in content
            assert "La Guerra de las Galaxias" in content

    def test_poster_links(self):
        """Test poster link formatting."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="Test",
                top_10=[
                    Film(
                        title="Test Film",
                        poster_url="https://example.com/poster.jpg",
                    ),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "Póster" in content
            assert "poster.jpg" in content

    def test_award_status_translation(self):
        """Test award status translation to Spanish."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.md"

            info = ComposerInfo(
                name="Test",
                awards=[
                    Award(award="Oscar", status=AwardStatus.WIN),
                    Award(award="Grammy", status=AwardStatus.NOMINATION),
                ],
            )

            generator = MarkdownGenerator()
            generator.generate(info, output_path)

            content = output_path.read_text()
            assert "Premio de la Academia" in content
            assert "Nominación" in content
