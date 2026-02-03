"""Markdown parser for SOUNDTRACKER ETL.

Parses composer Markdown files and extracts structured data for database import.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedFilm:
    """Parsed film data from Markdown."""

    title: str
    original_title: Optional[str] = None
    title_es: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    poster_local: Optional[str] = None
    is_top10: bool = False
    top10_rank: Optional[int] = None


@dataclass
class ParsedAward:
    """Parsed award data from Markdown."""

    award_name: str
    category: Optional[str] = None
    year: Optional[int] = None
    film_title: Optional[str] = None
    status: str = "nomination"  # 'win' or 'nomination'


@dataclass
class ParsedSource:
    """Parsed external source from Markdown."""

    name: str
    url: str
    snippet: Optional[str] = None
    source_type: str = "reference"  # 'reference' or 'snippet'


@dataclass
class ParsedComposer:
    """Complete parsed composer data from Markdown file."""

    name: str
    index_num: int
    slug: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    country: Optional[str] = None
    photo_url: Optional[str] = None
    photo_local: Optional[str] = None
    biography: Optional[str] = None
    style: Optional[str] = None
    anecdotes: Optional[str] = None
    films: list[ParsedFilm] = field(default_factory=list)
    top10: list[ParsedFilm] = field(default_factory=list)
    awards: list[ParsedAward] = field(default_factory=list)
    sources: list[ParsedSource] = field(default_factory=list)
    snippets: list[ParsedSource] = field(default_factory=list)


def parse_markdown_file(file_path: Path) -> Optional[ParsedComposer]:
    """Parse a composer Markdown file.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        ParsedComposer object or None if parsing fails.
    """
    if not file_path.exists():
        logger.error("File not found: %s", file_path)
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("Failed to read %s: %s", file_path, e)
        return None

    # Extract index and slug from filename (e.g., "001_herbert_stothart.md")
    filename = file_path.stem
    match = re.match(r"^(\d{3})_(.+)$", filename)
    if not match:
        logger.warning("Invalid filename format: %s", filename)
        return None

    index_num = int(match.group(1))
    slug = match.group(2)

    # Parse name from title
    name = parse_name(content)
    if not name:
        logger.warning("Could not extract name from %s", file_path)
        return None

    composer = ParsedComposer(
        name=name,
        index_num=index_num,
        slug=slug,
    )

    # Parse sections
    composer.photo_url, composer.photo_local = extract_photo_path(content, file_path)
    composer.biography = parse_biography(content)
    composer.style = parse_style(content)
    composer.anecdotes = parse_anecdotes(content)
    composer.top10 = parse_top10(content, file_path)
    composer.films = parse_filmography(content, file_path)
    composer.awards = parse_awards(content)
    composer.sources = parse_sources(content)
    composer.snippets = parse_snippets(content)

    # Try to extract birth/death years from biography
    if composer.biography:
        years = extract_life_years(composer.biography, name)
        if years:
            composer.birth_year, composer.death_year = years

    logger.debug("Parsed composer: %s (index=%d)", name, index_num)
    return composer


def parse_name(content: str) -> Optional[str]:
    """Extract composer name from Markdown title.

    Args:
        content: Markdown content.

    Returns:
        Composer name or None.
    """
    match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def extract_photo_path(
    content: str, file_path: Path
) -> tuple[Optional[str], Optional[str]]:
    """Extract photo URL and local path from Markdown.

    Args:
        content: Markdown content.
        file_path: Path to the Markdown file.

    Returns:
        Tuple of (photo_url, photo_local).
    """
    # Look for image after title
    # Format: ![Name](path_or_url)
    match = re.search(r"!\[.*?\]\(([^)]+)\)", content)
    if not match:
        return None, None

    path_or_url = match.group(1).strip()

    if path_or_url.startswith(("http://", "https://")):
        return path_or_url, None

    # Relative path - resolve against file location
    local_path = file_path.parent / path_or_url
    if local_path.exists():
        return None, str(local_path)

    return None, path_or_url


def parse_biography(content: str) -> Optional[str]:
    """Extract biography section from Markdown.

    Args:
        content: Markdown content.

    Returns:
        Biography text or None.
    """
    return _extract_section(content, "Biografía")


def parse_style(content: str) -> Optional[str]:
    """Extract musical style section from Markdown.

    Args:
        content: Markdown content.

    Returns:
        Style text or None.
    """
    return _extract_section(content, "Estilo musical")


def parse_anecdotes(content: str) -> Optional[str]:
    """Extract anecdotes section from Markdown.

    Args:
        content: Markdown content.

    Returns:
        Anecdotes text or None.
    """
    # Try both possible header names
    text = _extract_section(content, "Anécdotas y curiosidades")
    if not text:
        text = _extract_section(content, "Anécdotas")
    return text


def _extract_section(content: str, section_name: str) -> Optional[str]:
    """Extract content of a section by header name.

    Args:
        content: Markdown content.
        section_name: Section header name (without ##).

    Returns:
        Section content or None.
    """
    # Match section header and capture until next section or end
    pattern = rf"##\s+{re.escape(section_name)}\s*\n([\s\S]*?)(?=\n##\s|\Z)"
    match = re.search(pattern, content)
    if match:
        text = match.group(1).strip()
        return text if text else None
    return None


def parse_top10(content: str, file_path: Path) -> list[ParsedFilm]:
    """Extract Top 10 films from Markdown.

    Args:
        content: Markdown content.
        file_path: Path to file for resolving relative paths.

    Returns:
        List of ParsedFilm objects.
    """
    # Try both section names
    section = _extract_section(content, "Top 10 bandas sonoras")
    if not section:
        section = _extract_section(content, "Top 10")
    if not section:
        return []

    films = []

    # Pattern for numbered list with triple asterisks (bold italic):
    # 1. ***Title (Título en España: Spanish Title)***
    #     * **Póster:** [link](path)
    # Or without Spanish title:
    # 1. ***Title***

    # Split by numbered items
    items = re.split(r'\n(?=\d+\.)', section)

    for item in items:
        item = item.strip()
        if not item:
            continue

        # Extract rank and title
        # Format: 1. ***Title (Título en España: Spanish)***
        match = re.match(r'(\d+)\.\s+\*{3}(.+?)\*{3}', item)
        if not match:
            continue

        rank = int(match.group(1))
        title_block = match.group(2).strip()

        # Extract Spanish title if present
        title = title_block
        title_es = None
        es_match = re.search(r'\(Título en España:\s*(.+?)\)', title_block)
        if es_match:
            title_es = es_match.group(1).strip()
            title = re.sub(r'\s*\(Título en España:[^)]+\)', '', title_block).strip()

        # Extract year if in title
        year = None
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = int(year_match.group(1))
            title = re.sub(r'\s*\(\d{4}\)', '', title).strip()

        # Extract poster path
        poster_path = None
        poster_match = re.search(r'\[link\]\(([^)]+)\)', item)
        if not poster_match:
            poster_match = re.search(r'\[Póster\]\(([^)]+)\)', item)
        if poster_match:
            poster_path = poster_match.group(1).strip()

        film = ParsedFilm(
            title=title,
            original_title=title,
            title_es=title_es,
            year=year,
            is_top10=True,
            top10_rank=rank,
        )

        if poster_path:
            if poster_path.startswith(("http://", "https://")):
                film.poster_url = poster_path
            else:
                local_path = file_path.parent / poster_path
                if local_path.exists():
                    film.poster_local = str(local_path)
                else:
                    film.poster_local = poster_path

        films.append(film)

    return films


def parse_filmography(content: str, file_path: Path) -> list[ParsedFilm]:
    """Extract filmography from Markdown.

    Args:
        content: Markdown content.
        file_path: Path to file for resolving paths.

    Returns:
        List of ParsedFilm objects.
    """
    # Try both section names
    section = _extract_section(content, "Filmografía completa")
    if not section:
        section = _extract_section(content, "Filmografía")
    if not section:
        return []

    films = []

    # Format: - Title (Título en España: Spanish) (Year) · [Póster](path)
    # Or: - Title (Year) · [Póster](path)
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('-'):
            continue

        line = line[1:].strip()  # Remove leading dash

        # Extract year (required)
        year_match = re.search(r'\((\d{4})\)', line)
        if not year_match:
            continue
        year = int(year_match.group(1))

        # Extract Spanish title if present
        title_es = None
        es_match = re.search(r'\(Título en España:\s*(.+?)\)', line)
        if es_match:
            title_es = es_match.group(1).strip()

        # Extract poster path
        poster_path = None
        poster_match = re.search(r'\[Póster\]\(([^)]+)\)', line)
        if poster_match:
            poster_path = poster_match.group(1).strip()

        # Extract title (everything before the first parenthesis)
        title = re.split(r'\s*\(', line)[0].strip()

        film = ParsedFilm(
            title=title,
            original_title=title,
            title_es=title_es,
            year=year,
        )

        if poster_path:
            if poster_path.startswith(("http://", "https://")):
                film.poster_url = poster_path
            else:
                local_path = file_path.parent / poster_path
                film.poster_local = str(local_path) if local_path.exists() else poster_path

        films.append(film)

    return films


def parse_awards(content: str) -> list[ParsedAward]:
    """Extract awards from Markdown.

    Args:
        content: Markdown content.

    Returns:
        List of ParsedAward objects.
    """
    # Try both section names
    section = _extract_section(content, "Premios y nominaciones")
    if not section:
        section = _extract_section(content, "Premios")
    if not section:
        return []

    awards = []

    # Format: * YEAR – Award Name – por *Film Title (Título en España: Spanish)* – (Status)
    # Or: * YEAR – Award Name – (Status)
    # Or: * Award Name – (Status)  (no year)

    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('*'):
            continue

        line = line[1:].strip()  # Remove leading asterisk

        # Extract status (Ganador/Nominación)
        status = "nomination"
        if "(Ganador)" in line or "– Ganador" in line.lower():
            status = "win"
        elif "(Nominación)" in line or "– Nominación" in line.lower():
            status = "nomination"
        else:
            # Skip lines without clear status
            continue

        # Extract year if present at the start
        year = None
        year_match = re.match(r'(\d{4})\s*–', line)
        if year_match:
            year = int(year_match.group(1))
            line = line[len(year_match.group(0)):].strip()

        # Extract film title (in *italics* with por prefix)
        film_title = None
        film_match = re.search(r'por\s+\*(.+?)\*', line)
        if film_match:
            film_title = film_match.group(1).strip()
            # Clean up Spanish title notation
            film_title = re.sub(r'\s*\(Título en España:[^)]+\)', '', film_title).strip()

        # Extract award name (first segment before 'por' or status)
        award_name = line
        # Remove film and status parts
        award_name = re.sub(r'\s*–\s*por\s+\*.+?\*.*$', '', award_name)
        award_name = re.sub(r'\s*–\s*\((?:Ganador|Nominación)\).*$', '', award_name, flags=re.IGNORECASE)
        award_name = award_name.strip(' –')

        if award_name:
            awards.append(
                ParsedAward(
                    award_name=award_name,
                    year=year,
                    film_title=film_title,
                    status=status,
                )
            )

    return awards


def parse_sources(content: str) -> list[ParsedSource]:
    """Extract external sources from Markdown.

    Args:
        content: Markdown content.

    Returns:
        List of ParsedSource objects.
    """
    section = _extract_section(content, "Fuentes adicionales")
    if not section:
        return []

    sources = []

    # Format: * [Name](URL) — snippet
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('*'):
            continue

        line = line[1:].strip()

        # Extract link: [Name](URL)
        match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', line)
        if not match:
            continue

        name = match.group(1).strip()
        url = match.group(2).strip()

        # Extract snippet (after — or -)
        snippet = None
        rest = line[match.end():].strip()
        if rest.startswith('—') or rest.startswith('-'):
            snippet = rest.lstrip('—- ').strip()

        sources.append(
            ParsedSource(
                name=name,
                url=url,
                snippet=snippet,
                source_type="reference",
            )
        )

    return sources


def parse_snippets(content: str) -> list[ParsedSource]:
    """Extract external snippets/notes from Markdown.

    Args:
        content: Markdown content.

    Returns:
        List of ParsedSource objects.
    """
    section = _extract_section(content, "Notas externas")
    if not section:
        return []

    snippets = []

    # Format: * SourceName: Text content...
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('*'):
            continue

        line = line[1:].strip()

        # Extract source name and content (Name: Content)
        match = re.match(r'([^:]+):\s*(.+)', line)
        if not match:
            continue

        name = match.group(1).strip()
        text = match.group(2).strip()

        # Try to find URL from the sources section
        url = f"https://www.{name.lower().replace(' ', '')}.com"  # Placeholder

        snippets.append(
            ParsedSource(
                name=name,
                url=url,
                snippet=text,
                source_type="snippet",
            )
        )

    return snippets


def extract_life_years(
    biography: str, name: str
) -> Optional[tuple[Optional[int], Optional[int]]]:
    """Extract birth and death years from biography text.

    Args:
        biography: Biography text.
        name: Composer name for context.

    Returns:
        Tuple of (birth_year, death_year) or None.
    """
    birth_year = None
    death_year = None

    # Pattern: (YYYY-YYYY) or (YYYY-)
    match = re.search(r'\((\d{4})\s*-\s*(\d{4})?\)', biography)
    if match:
        birth_year = int(match.group(1))
        if match.group(2):
            death_year = int(match.group(2))
        return birth_year, death_year

    # Pattern: "8 de febrero de 1932" (Spanish date format)
    match = re.search(r'(\d{1,2})\s+de\s+\w+\s+de\s+(\d{4})', biography)
    if match:
        birth_year = int(match.group(2))

    # Pattern: born/nacido in/en YYYY
    if not birth_year:
        match = re.search(r'(?:born|nacido|nació)\s+(?:in|en|el)\s+.*?(\d{4})', biography, re.IGNORECASE)
        if match:
            birth_year = int(match.group(1))

    # Pattern: died/murió in/en YYYY or fallecido en YYYY
    match = re.search(
        r'(?:died|murió|fallecido|falleció)\s+(?:in|en|el)\s+.*?(\d{4})', biography, re.IGNORECASE
    )
    if match:
        death_year = int(match.group(1))

    if birth_year:
        return birth_year, death_year

    return None


def parse_all_files(outputs_dir: Path) -> list[ParsedComposer]:
    """Parse all composer Markdown files in a directory.

    Args:
        outputs_dir: Directory containing composer Markdown files.

    Returns:
        List of ParsedComposer objects.
    """
    composers = []

    # Find all NNN_*.md files
    for md_file in sorted(outputs_dir.glob("[0-9][0-9][0-9]_*.md")):
        composer = parse_markdown_file(md_file)
        if composer:
            composers.append(composer)
        else:
            logger.warning("Failed to parse: %s", md_file)

    logger.info("Parsed %d composer files", len(composers))
    return composers
