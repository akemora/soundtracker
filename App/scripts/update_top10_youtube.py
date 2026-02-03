import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import create_composer_files as ccf

OUTPUT_DIR = ccf.OUTPUT_DIR
USE_WEB_TOPLISTS = os.getenv('USE_WEB_TOPLISTS', '1') == '1'


def parse_title_display(title_display: str) -> Dict[str, Optional[str]]:
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
    titles: List[str] = []
    for line in lines:
        match = re.search(r"por \*(.+?)\*", line)
        if match:
            titles.append(match.group(1).strip())
    return titles


def get_section(lines: List[str], header: str) -> List[str]:
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
    lines = ["## Top 10 bandas sonoras", ""]
    for idx, entry in enumerate(entries, 1):
        title_display = ccf.format_film_title(entry)
        lines.append(f"{idx}. ***{title_display}***")
        poster = entry.get('poster_local')
        if poster:
            lines.append(f"    * **Póster:** [link]({poster})")
    lines.append("")
    return lines


def update_file(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines:
        return
    composer = lines[0].lstrip('#').strip() if lines[0].startswith('#') else path.stem

    filmography_lines = get_section(lines, '## Filmografía completa')
    if not filmography_lines:
        return
    filmography = parse_filmography(filmography_lines)
    if not filmography:
        return

    awards_lines = get_section(lines, '## Premios y nominaciones')
    award_titles = parse_award_titles(awards_lines)
    awards = [{'film': title} for title in award_titles]

    boost_scores: Dict[str, int] = {}
    if USE_WEB_TOPLISTS and ccf.SEARCH_WEB_ENABLED:
        boost_scores.update(ccf.get_top_10_films(composer))
    if ccf.TMDB_API_KEY:
        person_id, known_for = ccf.tmdb_search_person(composer)
        for title in known_for:
            key = ccf.normalize_title_key(title)
            if key:
                boost_scores[key] = max(boost_scores.get(key, 0), 2)
    for entry in filmography:
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

    path.write_text('\n'.join(new_lines).rstrip() + '\n', encoding='utf-8')


def main() -> None:
    start_index = int(os.getenv('START_INDEX', '1'))
    if start_index < 1:
        start_index = 1
    for path in sorted(OUTPUT_DIR.glob('[0-9][0-9][0-9]_*.md')):
        try:
            index = int(path.name.split('_', 1)[0])
        except ValueError:
            index = 0
        if index and index < start_index:
            continue
        update_file(path)
        print(f"Updated Top 10: {path.name}")


if __name__ == '__main__':
    main()
