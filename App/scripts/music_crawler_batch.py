"""Batch runner for Music Crawler integration."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = APP_ROOT / "data" / "soundtrackers.db"


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection to the Soundtracker database."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def fetch_top10_films(connection: sqlite3.Connection, composer_slug: str) -> list[sqlite3.Row]:
    """Fetch Top 10 films for a composer."""
    query = """
        SELECT top10_rank, title, title_es, original_title
        FROM v_top10_films
        WHERE composer_slug = ?
        ORDER BY top10_rank
    """
    cursor = connection.execute(query, (composer_slug,))
    return list(cursor.fetchall())


def main() -> None:
    """Entry point for batch processing."""
    parser = argparse.ArgumentParser(
        description="Run Music Crawler for one or more composers",
    )
    parser.add_argument("--composer", type=str, help="Composer slug to process")
    parser.add_argument("--all", action="store_true", help="Process all composers")
    parser.add_argument(
        "--playlist-only",
        action="store_true",
        help="Only generate playlist outputs",
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
