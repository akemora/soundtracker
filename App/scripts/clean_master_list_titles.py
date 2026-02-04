#!/usr/bin/env python3
"""Remove title and noise entries from the master list using IMDb tables."""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from soundtracker.config import settings  # noqa: E402

logger = logging.getLogger(__name__)

NOISE_TOKENS = {
    "about",
    "contact",
    "privacy",
    "policy",
    "terms",
    "cookies",
    "sitemap",
    "home",
    "login",
    "sign",
    "subscribe",
    "language",
    "bahasa",
    "política",
    "aviso",
    "legal",
    "press",
    "news",
    "newsletter",
    "careers",
}

NOISE_PHRASES = {
    "about us",
    "contact us",
    "privacy policy",
    "terms of use",
    "all time",
}

TITLE_SEPARATORS = (":", " - ", " – ", " — ", "/")


def is_person_name(name: str) -> bool:
    if not name:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    if "&" in name or "/" in name:
        return False
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    alpha_tokens = [t for t in tokens if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", t)]
    if len(alpha_tokens) < 2:
        return False
    return True


def is_probable_title(name: str) -> bool:
    if any(sep in name for sep in TITLE_SEPARATORS):
        return True
    tokens = [t.strip(".,:;!?()[]{}\"'") for t in name.lower().split()]
    if not tokens:
        return False
    if tokens[0] in {"the", "a", "an"}:
        return True
    if any(token in {"and", "or", "of", "for", "with", "from", "to", "in", "on", "at"} for token in tokens):
        return True
    return False


def is_noise_name(name: str) -> bool:
    lower = name.lower()
    for phrase in NOISE_PHRASES:
        if phrase in lower:
            return True
    for token in NOISE_TOKENS:
        if token in lower:
            return True
    return False


def parse_master_list(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        if not parts or parts[0].lower() in {"no.", "name", "#"} or parts[0].startswith("---"):
            continue
        rows.append(parts)
    return rows


def build_title_match_set(conn: sqlite3.Connection, names: list[str]) -> set[str]:
    if not names:
        return set()

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_titles_primary_nocase "
        "ON titles (primaryTitle COLLATE NOCASE)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_titles_original_nocase "
        "ON titles (originalTitle COLLATE NOCASE)"
    )
    conn.commit()

    conn.execute("DROP TABLE IF EXISTS temp_candidate_names")
    conn.execute("CREATE TEMP TABLE temp_candidate_names (name TEXT PRIMARY KEY)")

    chunk_size = 5000
    for start in range(0, len(names), chunk_size):
        chunk = names[start : start + chunk_size]
        conn.executemany(
            "INSERT OR IGNORE INTO temp_candidate_names (name) VALUES (?)",
            [(name,) for name in chunk],
        )
    conn.commit()

    query = """
        SELECT DISTINCT n.name
        FROM temp_candidate_names n
        JOIN titles t
          ON (t.primaryTitle = n.name OR t.originalTitle = n.name)
    """
    matches = {row[0] for row in conn.execute(query)}
    return matches


def build_people_match_set(conn: sqlite3.Connection, names: list[str]) -> set[str]:
    if not names:
        return set()

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_people_name_nocase "
        "ON people (primaryName COLLATE NOCASE)"
    )
    conn.commit()

    conn.execute("DROP TABLE IF EXISTS temp_candidate_people")
    conn.execute("CREATE TEMP TABLE temp_candidate_people (name TEXT PRIMARY KEY)")

    chunk_size = 5000
    for start in range(0, len(names), chunk_size):
        chunk = names[start : start + chunk_size]
        conn.executemany(
            "INSERT OR IGNORE INTO temp_candidate_people (name) VALUES (?)",
            [(name,) for name in chunk],
        )
    conn.commit()

    query = """
        SELECT DISTINCT n.name
        FROM temp_candidate_people n
        JOIN people p
          ON p.primaryName = n.name
    """
    matches = {row[0] for row in conn.execute(query)}
    return matches


def write_master_list(path: Path, rows: list[list[str]]) -> None:
    total = len(rows)
    width = max(3, len(str(total)))

    lines = []
    lines.append("# Film Music Composers: Global Master List (Alphabetical)")
    lines.append("")
    lines.append(f"## Lista principal ({total} entradas)")
    lines.append("")
    lines.append("| No. | Name | Birth Year | Death Year | Country | Medios |")
    lines.append("|---|---|---|---|---|---|")

    for idx, row in enumerate(rows, 1):
        name = row[1] if len(row) > 1 else ""
        birth = row[2] if len(row) > 2 else ""
        death = row[3] if len(row) > 3 else ""
        country = row[4] if len(row) > 4 else ""
        medios = row[5] if len(row) > 5 else ""
        index = str(idx).zfill(width)
        lines.append(f"| {index} | {name} | {birth} | {death} | {country} | {medios} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Master list updated: %s (%d entries)", path, total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove title entries from master list.")
    parser.add_argument("--master-list", type=Path, default=settings.output_dir / "composers_master_list.md")
    parser.add_argument("--imdb-db", type=Path, default=settings.imdb_db_path)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rows = parse_master_list(args.master_list)
    if not rows:
        logger.error("Master list not found or empty: %s", args.master_list)
        return

    names = [row[1] for row in rows if len(row) > 1]
    conn = sqlite3.connect(args.imdb_db)
    title_matches = build_title_match_set(conn, names)
    people_matches = build_people_match_set(conn, names)
    conn.close()

    filtered = []
    removed = 0
    for row in rows:
        if len(row) <= 1:
            continue
        name = row[1]
        if name in title_matches:
            removed += 1
            continue
        if name in people_matches:
            filtered.append(row)
            continue
        if not is_person_name(name):
            removed += 1
            continue
        if is_probable_title(name) or is_noise_name(name):
            removed += 1
            continue
        filtered.append(row)

    logger.info("Removed %d non-composer entries.", removed)
    write_master_list(args.master_list, filtered)


if __name__ == "__main__":
    main()
