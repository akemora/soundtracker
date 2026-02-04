#!/usr/bin/env python3
"""Build Top 100 composer list from web sources and master list."""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from soundtracker.config import settings  # noqa: E402
from master_list_sources import TOP100_QUERIES, harvest_web_names, normalize_name  # noqa: E402

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


def build_imdb_person_checker(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_people_name_nocase "
        "ON people (primaryName COLLATE NOCASE)"
    )
    conn.commit()
    cache: dict[str, bool] = {}

    def is_person(name: str) -> bool:
        key = name.lower().strip()
        if not key:
            return False
        if key in cache:
            return cache[key]
        row = conn.execute(
            "SELECT 1 FROM people WHERE primaryName = ? COLLATE NOCASE LIMIT 1",
            (name,),
        ).fetchone()
        cache[key] = row is not None
        return cache[key]

    return conn, is_person


def load_master_names(path: Path) -> dict[str, str]:
    names: dict[str, str] = {}
    if not path.exists():
        return names
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
        names[normalize_name(name).lower()] = name
    return names


def write_top100(
    top_names: list[tuple[str, int]],
    output_path: Path,
) -> None:
    lines = []
    lines.append("# Top 100 Compositores de Bandas Sonoras (Web Consensus)")
    lines.append("")
    lines.append(f"## Lista principal ({len(top_names)} entradas)")
    lines.append("")
    lines.append("| No. | Name | Mentions |")
    lines.append("|---|---|---|")
    for idx, (name, count) in enumerate(top_names, 1):
        lines.append(f"| {idx:03d} | {name} | {count} |")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Top 100 list written: %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Top 100 list from web sources.")
    parser.add_argument("--master-list", type=Path, default=settings.output_dir / "composers_master_list.md")
    parser.add_argument("--output", type=Path, default=settings.output_dir / "top_100_composers.md")
    parser.add_argument("--use-gemini", action="store_true")
    parser.add_argument("--web-max-urls", type=int, default=60)
    parser.add_argument("--web-max-urls-per-query", type=int, default=6)
    parser.add_argument("--gemini-max-urls", type=int, default=12)
    parser.add_argument("--min-sources", type=int, default=1)
    parser.add_argument("--imdb-db", type=Path, default=settings.imdb_db_path)
    parser.add_argument("--require-imdb-person", action="store_true", default=True)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    master_names = load_master_names(args.master_list)
    if not master_names:
        logger.error("Master list not found or empty: %s", args.master_list)
        return

    web_names = harvest_web_names(
        TOP100_QUERIES,
        max_urls_total=args.web_max_urls,
        max_urls_per_query=args.web_max_urls_per_query,
        use_gemini=args.use_gemini,
        gemini_max_urls=args.gemini_max_urls,
    )

    imdb_conn = None
    imdb_checker = None
    if args.require_imdb_person:
        imdb_conn, imdb_checker = build_imdb_person_checker(args.imdb_db)

    counts: dict[str, int] = {}
    for key, entry in web_names.items():
        if len(entry.sources) < args.min_sources:
            continue
        if not is_person_name(entry.name):
            continue
        if is_probable_title(entry.name) or is_noise_name(entry.name):
            continue
        if imdb_checker and not imdb_checker(entry.name):
            continue
        if key not in master_names:
            continue
        counts[master_names[key]] = max(counts.get(master_names[key], 0), len(entry.sources))

    if imdb_conn:
        imdb_conn.close()

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top100 = ranked[:100]
    write_top100(top100, args.output)


if __name__ == "__main__":
    main()
