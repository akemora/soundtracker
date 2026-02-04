#!/usr/bin/env python3
"""Build a global master list of soundtrack composers.

Sources:
  - IMDb dataset (composer credits)
  - Existing master list (for country/backfill)

Output:
  - Markdown table sorted alphabetically
"""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from soundtracker.config import settings  # noqa: E402
from master_list_sources import DEFAULT_QUERIES, harvest_web_names  # noqa: E402

logger = logging.getLogger(__name__)

TITLE_TYPES = (
    "movie",
    "short",
    "tvSeries",
    "tvMiniSeries",
    "tvMovie",
    "tvSpecial",
    "tvShort",
    "videoGame",
)

MEDIUM_ORDER = ["cine", "corto", "serie", "tv", "videojuego", "otros"]

TYPE_TO_MEDIUM = {
    "movie": {"cine"},
    "short": {"cine", "corto"},
    "tvSeries": {"serie"},
    "tvMiniSeries": {"serie"},
    "tvMovie": {"tv"},
    "tvSpecial": {"tv"},
    "tvShort": {"tv"},
    "videoGame": {"videojuego"},
}

NON_PERSON_TOKENS = {
    "studio",
    "studios",
    "records",
    "recordings",
    "production",
    "productions",
    "company",
    "co.",
    "inc",
    "ltd",
    "llc",
    "entertainment",
    "orchestra",
    "ensemble",
    "choir",
    "band",
    "group",
    "department",
    "team",
    "music department",
    "sound department",
    "soundtrack",
    "pictures",
    "films",
    "games",
    "media",
    "various artists",
}


@dataclass
class ComposerRow:
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    country: str = ""
    mediums: set[str] = field(default_factory=set)

    def medium_text(self) -> str:
        ordered = [m for m in MEDIUM_ORDER if m in self.mediums]
        extras = sorted(self.mediums - set(MEDIUM_ORDER))
        return ", ".join(ordered + extras)


def normalize_name(name: str) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_name.lower().strip()


def is_person_name(name: str) -> bool:
    if not name:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    lower = name.lower()
    for token in NON_PERSON_TOKENS:
        if token in lower:
            return False
    if "&" in name or "/" in name:
        return False
    tokens = [t for t in re.split(r"\\s+", name.strip()) if t]
    alpha_tokens = [t for t in tokens if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", t)]
    if len(alpha_tokens) < 2:
        return False
    return True


def parse_existing_master_list(path: Path) -> list[ComposerRow]:
    if not path.exists():
        return []
    rows: list[ComposerRow] = []
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
        if len(parts) < 2:
            continue
        name = parts[1]
        birth = _parse_int(parts[2]) if len(parts) > 2 else None
        death = _parse_int(parts[3]) if len(parts) > 3 else None
        country = parts[4] if len(parts) > 4 else ""
        rows.append(
            ComposerRow(
                name=name,
                birth_year=birth,
                death_year=death,
                country=country,
            )
        )
    return rows


def _parse_int(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def build_imdb_rows(db_path: Path, min_credits: int) -> list[ComposerRow]:
    if not db_path.exists():
        raise FileNotFoundError(f"IMDb database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    placeholders = ",".join("?" for _ in TITLE_TYPES)
    query = f"""
        SELECT c.nconst,
               p.primaryName AS name,
               p.birthYear AS birthYear,
               p.deathYear AS deathYear,
               GROUP_CONCAT(DISTINCT t.titleType) AS types,
               COUNT(DISTINCT c.tconst) AS credit_count
        FROM composer_credits c
        JOIN people p ON p.nconst = c.nconst
        JOIN titles t ON t.tconst = c.tconst
        WHERE t.titleType IN ({placeholders})
        GROUP BY c.nconst
        HAVING credit_count >= ?
    """

    rows: list[ComposerRow] = []
    for row in conn.execute(query, [*TITLE_TYPES, min_credits]):
        name = row["name"]
        if not name or not is_person_name(name):
            continue
        types = (row["types"] or "").split(",") if row["types"] else []
        mediums: set[str] = set()
        for ttype in types:
            mediums.update(TYPE_TO_MEDIUM.get(ttype, {"otros"}))
        rows.append(
            ComposerRow(
                name=name,
                birth_year=row["birthYear"],
                death_year=row["deathYear"],
                country="",
                mediums=mediums,
            )
        )

    conn.close()
    return rows


def build_imdb_name_set(rows: list[ComposerRow]) -> set[str]:
    return {normalize_name(row.name).lower() for row in rows if row.name}


def merge_rows(
    imdb_rows: list[ComposerRow],
    existing_rows: list[ComposerRow],
    web_names: dict[str, "WebName"],
    min_sources: int,
    allow_non_imdb: bool,
) -> list[ComposerRow]:
    merged: list[ComposerRow] = []

    imdb_name_set = build_imdb_name_set(imdb_rows)

    existing_by_key: dict[tuple[str, Optional[int]], ComposerRow] = {}
    existing_by_name: dict[str, ComposerRow] = {}
    for row in existing_rows:
        key = (normalize_name(row.name), row.birth_year)
        existing_by_key[key] = row
        if normalize_name(row.name) not in existing_by_name:
            existing_by_name[normalize_name(row.name)] = row

    seen_keys: set[tuple[str, Optional[int], Optional[int]]] = set()
    for row in imdb_rows:
        key = (normalize_name(row.name), row.birth_year)
        existing = existing_by_key.get(key) or existing_by_name.get(normalize_name(row.name))

        web_key = normalize_name(row.name).lower()
        web_entry = web_names.get(web_key)
        if web_entry:
            row.mediums.update(web_entry.mediums)

        if existing:
            if not row.birth_year:
                row.birth_year = existing.birth_year
            if not row.death_year:
                row.death_year = existing.death_year
            if existing.country and not row.country:
                row.country = existing.country

        dedupe_key = (normalize_name(row.name), row.birth_year, row.death_year)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        merged.append(row)

    # Add existing-only rows not present in IMDb
    for row in existing_rows:
        dedupe_key = (normalize_name(row.name), row.birth_year, row.death_year)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        if is_person_name(row.name):
            merged.append(row)

    if allow_non_imdb and web_names:
        for key, entry in web_names.items():
            if key in imdb_name_set:
                continue
            if len(entry.sources) < min_sources:
                continue
            if not is_person_name(entry.name):
                continue
            merged.append(
                ComposerRow(
                    name=entry.name,
                    birth_year=None,
                    death_year=None,
                    country="",
                    mediums=set(entry.mediums),
                )
            )

    return merged


def write_markdown(rows: list[ComposerRow], output_path: Path) -> None:
    rows_sorted = sorted(rows, key=lambda r: normalize_name(r.name))
    total = len(rows_sorted)
    width = max(3, len(str(total)))

    lines = []
    lines.append("# Film Music Composers: Global Master List (Alphabetical)")
    lines.append("")
    lines.append(f"## Lista principal ({total} entradas)")
    lines.append("")
    lines.append("| No. | Name | Birth Year | Death Year | Country | Medios |")
    lines.append("|---|---|---|---|---|---|")

    for idx, row in enumerate(rows_sorted, 1):
        index = str(idx).zfill(width)
        birth = str(row.birth_year) if row.birth_year else ""
        death = str(row.death_year) if row.death_year else ""
        country = row.country or ""
        mediums = row.medium_text()
        lines.append(
            f"| {index} | {row.name} | {birth} | {death} | {country} | {mediums} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Master list written: %s (%d entries)", output_path, total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build global master list from IMDb + existing list.")
    parser.add_argument("--imdb-db", type=Path, default=settings.imdb_db_path)
    parser.add_argument("--existing-master", type=Path, default=settings.output_dir / "composers_master_list.md")
    parser.add_argument("--output", type=Path, default=settings.output_dir / "composers_master_list.md")
    parser.add_argument("--min-credits", type=int, default=1)
    parser.add_argument("--use-web", action="store_true", help="Use web sources to add names.")
    parser.add_argument("--web-max-urls", type=int, default=60)
    parser.add_argument("--web-max-urls-per-query", type=int, default=6)
    parser.add_argument("--use-gemini", action="store_true")
    parser.add_argument("--gemini-max-urls", type=int, default=12)
    parser.add_argument("--non-imdb-min-sources", type=int, default=1)
    parser.add_argument("--allow-non-imdb", action="store_true")
    parser.add_argument("--skip-existing", action="store_true", help="Do not merge existing list data.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    imdb_rows = build_imdb_rows(args.imdb_db, args.min_credits)
    logger.info("IMDb rows loaded: %d", len(imdb_rows))
    existing_rows = [] if args.skip_existing else parse_existing_master_list(args.existing_master)
    web_names = {}
    if args.use_web:
        web_names = harvest_web_names(
            DEFAULT_QUERIES,
            max_urls_total=args.web_max_urls,
            max_urls_per_query=args.web_max_urls_per_query,
            use_gemini=args.use_gemini,
            gemini_max_urls=args.gemini_max_urls,
        )
    logger.info("Web names harvested: %d", len(web_names))
    merged = merge_rows(
        imdb_rows,
        existing_rows,
        web_names,
        min_sources=args.non_imdb_min_sources,
        allow_non_imdb=args.allow_non_imdb,
    )
    write_markdown(merged, args.output)


if __name__ == "__main__":
    main()
