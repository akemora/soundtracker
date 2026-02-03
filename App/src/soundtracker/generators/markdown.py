"""Markdown file generator for composer profiles.

Provides functionality to generate formatted Markdown files
from composer information.
"""

import logging
from pathlib import Path
from typing import Optional

from soundtracker.models import Award, ComposerInfo, ExternalSource, Film
from soundtracker.utils.text import format_film_title
from soundtracker.utils.urls import format_link

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """Generator for composer Markdown files.

    Creates formatted Markdown documents from ComposerInfo data.

    Example:
        generator = MarkdownGenerator()
        generator.generate(composer_info, output_path)
    """

    STATUS_MAP = {
        "Win": "Ganador",
        "WIN": "Ganador",
        "win": "Ganador",
        "Nomination": "Nominación",
        "NOMINATION": "Nominación",
        "nomination": "Nominación",
    }
    ACADEMY_KEYWORDS = ("academy", "oscar", "academia")

    def __init__(
        self,
        include_snippets: bool = True,
        include_sources: bool = True,
        max_filmography: Optional[int] = None,
    ) -> None:
        """Initialize Markdown generator.

        Args:
            include_snippets: Include external snippets section.
            include_sources: Include external sources section.
            max_filmography: Maximum films in filmography.
        """
        self.include_snippets = include_snippets
        self.include_sources = include_sources
        self.max_filmography = max_filmography

    def generate(
        self,
        info: ComposerInfo,
        output_path: Path,
    ) -> None:
        """Generate Markdown file for composer.

        Args:
            info: Composer information.
            output_path: Target file path.
        """
        content = self.build_content(info, output_path.parent)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logger.info("Generated %s", output_path)

    def build_content(
        self,
        info: ComposerInfo,
        base_path: Path,
    ) -> str:
        """Build Markdown content from composer info.

        Args:
            info: Composer information.
            base_path: Base path for relative links.

        Returns:
            Formatted Markdown string.
        """
        lines: list[str] = []

        # Header and photo
        lines.append(f"# {info.name}\n")
        if info.photo:
            link = format_link(info.photo, base_path)
            lines.append(f"![{info.name}]({link})\n")

        # Country / nationality
        lines.append("## País o nacionalidad\n")
        lines.append(f"{info.country or 'No disponible.'}\n")

        # Biography
        if info.biography:
            lines.append("## Biografía\n")
            lines.append(f"{info.biography}\n")

        # Musical style
        lines.append("## Estilo musical\n")
        lines.append(f"{info.style or 'No disponible.'}\n")

        # Fun facts / technique
        lines.append("## Datos curiosos y técnica de composición\n")
        lines.append(f"{info.anecdotes or 'No disponible.'}\n")

        # Top 10
        if info.top_10:
            lines.extend(self._build_top10(info.top_10, base_path))

        # Filmography
        if info.filmography:
            lines.extend(self._build_filmography(info.filmography, base_path))

        # Awards
        if info.awards:
            lines.extend(self._build_awards(info.awards))

        # External sources
        if self.include_sources and info.external_sources:
            lines.extend(self._build_sources(info.external_sources))

        # External snippets
        if self.include_snippets and info.external_snippets:
            lines.extend(self._build_snippets(info.external_snippets))

        return "\n".join(lines).strip() + "\n"

    def _build_top10(
        self,
        films: list[Film],
        base_path: Path,
    ) -> list[str]:
        """Build Top 10 section.

        Args:
            films: Top 10 films.
            base_path: Base path for links.

        Returns:
            Markdown lines.
        """
        lines = ["## Top 10 bandas sonoras\n"]

        for idx, film in enumerate(films, 1):
            title_display = format_film_title(film.original_title, film.title_es)
            year = f" ({film.year})" if film.year else ""
            lines.append(f"{idx}. ***{title_display}***{year}")

            poster = film.poster_local or film.poster_url
            if poster:
                link = format_link(poster, base_path)
                lines.append(f"    * **Póster:** [link]({link})")

        lines.append("")
        return lines

    def _build_filmography(
        self,
        films: list[Film],
        base_path: Path,
    ) -> list[str]:
        """Build filmography section.

        Args:
            films: All films.
            base_path: Base path for links.

        Returns:
            Markdown lines.
        """
        lines = ["## Filmografía completa\n"]

        film_list = films
        if self.max_filmography:
            film_list = films[: self.max_filmography]

        lines.append("| Año | Título | Título original | Póster |")
        lines.append("| --- | --- | --- | --- |")

        for film in film_list:
            year = str(film.year) if film.year else "—"
            title_es = film.title_es or film.title or film.original_title or "—"
            original = film.original_title or film.title or "—"
            if title_es == original:
                original = "—"
            poster = film.poster_local or film.poster_url
            if poster:
                link = format_link(poster, base_path)
                poster_cell = f"[Póster]({link})"
            else:
                poster_cell = "—"

            lines.append(
                f"| {self._escape_table_cell(year)} | "
                f"{self._escape_table_cell(title_es)} | "
                f"{self._escape_table_cell(original)} | "
                f"{self._escape_table_cell(poster_cell)} |"
            )

        lines.append("")
        return lines

    def _build_awards(self, awards: list[Award]) -> list[str]:
        """Build awards section.

        Args:
            awards: List of awards.

        Returns:
            Markdown lines.
        """
        lines = ["## Premios y nominaciones\n"]

        for award in awards:
            parts: list[str] = []

            if award.year:
                parts.append(str(award.year))
            if award.award:
                is_academy = self._is_academy_award(award.award)
                parts.append(self._format_award_label(award.award, award.status))
            else:
                is_academy = False
            if award.category:
                parts.append(award.category)
            if award.film:
                parts.append(f"por *{award.film}*")
            if award.status:
                status_str = award.status.value if hasattr(award.status, "value") else str(award.status)
                translated = self.STATUS_MAP.get(status_str, status_str)
                if not is_academy:
                    parts.append(f"({translated})")

            if parts:
                lines.append(f"* {' – '.join(parts)}")

        lines.append("")
        return lines

    def _is_academy_award(self, award_name: str) -> bool:
        """Check if award is an Academy Award (Oscar)."""
        return any(keyword in award_name.lower() for keyword in self.ACADEMY_KEYWORDS)

    def _format_award_label(self, award_name: str, status: object) -> str:
        """Format award label, mapping Academy wins/nominations."""
        if self._is_academy_award(award_name):
            status_str = status.value if hasattr(status, "value") else str(status)
            translated = self.STATUS_MAP.get(status_str, status_str)
            if translated == "Ganador":
                return "Premio de la Academia"
            if translated == "Nominación":
                return "Nominación de la Academia"
        return award_name

    @staticmethod
    def _escape_table_cell(value: str) -> str:
        """Escape pipes in Markdown table cells."""
        return value.replace("|", "\\|")

    def _build_sources(
        self,
        sources: list[ExternalSource],
    ) -> list[str]:
        """Build external sources section.

        Args:
            sources: List of sources.

        Returns:
            Markdown lines.
        """
        lines = ["## Fuentes adicionales\n"]

        for source in sources:
            snippet = source.snippet or f"Fuente: {source.name}"
            lines.append(f"* [{source.name}]({source.url}) — {snippet}")

        lines.append("")
        return lines

    def _build_snippets(
        self,
        snippets: list[ExternalSource],
    ) -> list[str]:
        """Build external snippets section.

        Args:
            snippets: List of snippets.

        Returns:
            Markdown lines.
        """
        lines = ["## Notas externas\n"]

        for snippet in snippets:
            text = snippet.snippet or snippet.text or ""
            if text:
                lines.append(f"* {snippet.name}: {text}")

        lines.append("")
        return lines


def generate_composer_file(
    info: ComposerInfo,
    output_path: Path,
    **kwargs,
) -> None:
    """Convenience function to generate composer Markdown.

    Args:
        info: Composer information.
        output_path: Target file path.
        **kwargs: Additional generator options.
    """
    generator = MarkdownGenerator(**kwargs)
    generator.generate(info, output_path)
