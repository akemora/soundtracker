"""Update Top 10 soundtrack sections in composer Markdown files.

This script reads existing composer profile files, parses their filmography
and awards sections, then recalculates and updates the Top 10 soundtracks
section using TMDB popularity data and web search boosts.

Usage:
    python update_top10_youtube.py

Environment Variables:
    START_INDEX: Start processing from this composer index (default: 1)
    USE_WEB_TOPLISTS: Use web search for top lists (default: '1' = enabled)
    TMDB_API_KEY: Required for TMDB popularity data

Example:
    START_INDEX=50 python update_top10_youtube.py
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import create_composer_files as ccf

OUTPUT_DIR = ccf.OUTPUT_DIR
USE_WEB_TOPLISTS = os.getenv('USE_WEB_TOPLISTS', '1') == '1'


def parse_title_display(title_display: str) -> Dict[str, Optional[str]]:
    """Parse a film title display string to extract original and Spanish titles.

    Args:
        title_display: Film title, optionally with Spanish title in format
                      "Original Title (Título en España: Spanish Title)"

    Returns:
        Dictionary with 'original_title' and 'title_es' keys.
    """
    title_display = title_display.strip()
    original = title_display
    title_es = None
    match = re.match(r"(.+) \(Título en España: (.+)\)$", title_display)
    if match:
        original = match.group(1).strip()
        title_es = match.group(2).strip()
    return {
        'original_title': original,
        'title_es': title_es or original,
    }


def parse_filmography(lines: List[str]) -> List[Dict[str, Optional[str]]]:
    """Parse filmography section lines into structured film entries.

    Args:
        lines: List of Markdown lines from the filmography section.

    Returns:
        List of dictionaries with film data (original_title, title_es, year, poster_local).
    """
    entries: List[Dict[str, Optional[str]]] = []
    for line in lines:
        line = line.strip()
        if not line.startswith('- '):
            continue
        content = line[2:]
        poster = None
        if ' · [Póster](' in content:
            content, poster_part = content.split(' · [Póster](', 1)
            poster = poster_part.split(')', 1)[0]
        year = None
        year_match = re.search(r"\((\d{4})\)$", content)
        if year_match:
            year = int(year_match.group(1))
            content = content[:year_match.start()].strip()
        title_bits = parse_title_display(content)
        entry = {
            'original_title': title_bits['original_title'],
            'title_es': title_bits['title_es'],
            'year': year,
            'poster_local': poster,
        }
        entries.append(entry)
    return entries


def parse_award_titles(lines: List[str]) -> List[str]:
    """Extract film titles from awards section lines.

    Looks for patterns like "por *Film Title*" to identify awarded films.

    Args:
        lines: List of Markdown lines from the awards section.

    Returns:
        List of film titles mentioned in award entries.
    """
    titles: List[str] = []
    for line in lines:
        match = re.search(r"por \*(.+?)\*", line)
        if match:
            titles.append(match.group(1).strip())
    return titles


def get_section(lines: List[str], header: str) -> List[str]:
    """Extract lines belonging to a Markdown section.

    Args:
        lines: All lines from the Markdown file.
        header: The section header to find (e.g., '## Filmografía completa').

    Returns:
        List of non-empty lines between the header and the next '## ' section.
    """
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == header:
            start = idx + 1
            break
    if start is None:
        return []
    collected: List[str] = []
    for line in lines[start:]:
        if line.startswith('## '):
            break
        if line.strip():
            collected.append(line.rstrip())
    return collected


def format_top10(entries: List[Dict[str, Optional[str]]], base_path: Path) -> List[str]:
    """Format top 10 film entries as Markdown section lines.

    Args:
        entries: List of film entry dictionaries with title and poster info.
        base_path: Base path for resolving relative poster links.

    Returns:
        List of Markdown lines for the Top 10 section.
    """
    lines = ["## Top 10 bandas sonoras", ""]
    for idx, entry in enumerate(entries, 1):
        title_display = ccf.format_film_title(entry)
        lines.append(f"{idx}. ***{title_display}***")
        poster = entry.get('poster_local')
        if poster:
            lines.append(f"    * **Póster:** [link]({poster})")
    lines.append("")
    return lines


def update_file(path: Path) -> bool:
    """Update the Top 10 section in a composer Markdown file.

    Reads the file, parses filmography and awards, fetches TMDB popularity
    data, calculates Top 10, and rewrites the file with updated section.

    Args:
        path: Path to the composer Markdown file.

    Returns:
        True if file was successfully updated, False otherwise.
    """
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as e:
        logger.error("Failed to read %s: %s", path.name, e)
        return False

    lines = text.splitlines()
    if not lines:
        logger.warning("Empty file: %s", path.name)
        return False

    composer = lines[0].lstrip('#').strip() if lines[0].startswith('#') else path.stem
    logger.debug("Processing composer: %s", composer)

    filmography_lines = get_section(lines, '## Filmografía completa')
    if not filmography_lines:
        logger.warning("No filmography section in %s", path.name)
        return False

    filmography = parse_filmography(filmography_lines)
    if not filmography:
        logger.warning("Empty filmography in %s", path.name)
        return False

    logger.debug("Found %d films in filmography", len(filmography))

    awards_lines = get_section(lines, '## Premios y nominaciones')
    award_titles = parse_award_titles(awards_lines)
    awards = [{'film': title} for title in award_titles]

    boost_scores: Dict[str, int] = {}
    try:
        if USE_WEB_TOPLISTS and ccf.SEARCH_WEB_ENABLED:
            boost_scores.update(ccf.get_top_10_films(composer))
    except Exception as e:
        logger.warning("Web search failed for %s: %s", composer, e)

    try:
        if ccf.TMDB_API_KEY:
            person_id, known_for = ccf.tmdb_search_person(composer)
            for title in known_for:
                key = ccf.normalize_title_key(title)
                if key:
                    boost_scores[key] = max(boost_scores.get(key, 0), 2)
    except Exception as e:
        logger.warning("TMDB person search failed for %s: %s", composer, e)

    for entry in filmography:
        try:
            details = ccf.tmdb_search_movie_details(entry['original_title'], entry.get('year'))
            if details:
                if details.get('popularity') is not None:
                    entry['popularity'] = details.get('popularity')
                if details.get('vote_count') is not None:
                    entry['vote_count'] = details.get('vote_count')
                if details.get('vote_average') is not None:
                    entry['vote_average'] = details.get('vote_average')
                if details.get('title_es'):
                    entry['title_es'] = details.get('title_es')
        except Exception as e:
            logger.debug("TMDB details failed for '%s': %s", entry['original_title'], e)

    top_entries = ccf.select_top_10_films(composer, filmography, awards, boost_scores)
    top10_lines = format_top10(top_entries, path.parent)

    new_lines: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.strip() == '## Top 10 bandas sonoras':
            # skip existing section
            idx += 1
            while idx < len(lines) and not lines[idx].startswith('## '):
                idx += 1
            new_lines.extend(top10_lines)
            continue
        new_lines.append(line)
        idx += 1

    try:
        path.write_text('\n'.join(new_lines).rstrip() + '\n', encoding='utf-8')
        return True
    except OSError as e:
        logger.error("Failed to write %s: %s", path.name, e)
        return False


def main() -> int:
    """Main entry point for updating Top 10 sections in all composer files.

    Processes all composer Markdown files in OUTPUT_DIR, optionally starting
    from a specific index (via START_INDEX environment variable).

    Returns:
        Exit code: 0 for success, 1 if any files failed.
    """
    start_index = int(os.getenv('START_INDEX', '1'))
    if start_index < 1:
        start_index = 1

    logger.info("Starting Top 10 update from index %d", start_index)
    logger.info("USE_WEB_TOPLISTS=%s, TMDB_API_KEY=%s",
                USE_WEB_TOPLISTS,
                "set" if ccf.TMDB_API_KEY else "not set")

    files = sorted(OUTPUT_DIR.glob('[0-9][0-9][0-9]_*.md'))
    logger.info("Found %d composer files in %s", len(files), OUTPUT_DIR)

    updated = 0
    skipped = 0
    failed = 0

    for path in files:
        try:
            index = int(path.name.split('_', 1)[0])
        except ValueError:
            logger.warning("Invalid filename format: %s", path.name)
            index = 0

        if index and index < start_index:
            skipped += 1
            continue

        if update_file(path):
            logger.info("Updated: %s", path.name)
            updated += 1
        else:
            logger.warning("Skipped: %s (no update needed or error)", path.name)
            failed += 1

    logger.info("Completed: %d updated, %d skipped, %d failed", updated, skipped, failed)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
