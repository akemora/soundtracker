"""ETL for Music Crawler results.json into soundtrackers.db."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = APP_ROOT / "data" / "soundtrackers.db"


def load_results(path: Path) -> dict:
    """Load results.json file."""
    return json.loads(path.read_text(encoding="utf-8"))


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def get_composer_id(connection: sqlite3.Connection, slug: str) -> int | None:
    """Fetch composer id by slug."""
    cursor = connection.execute("SELECT id FROM composers WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    return row["id"] if row else None


def get_film_id(
    connection: sqlite3.Connection,
    composer_id: int,
    film_title: str,
) -> int | None:
    """Fetch film id by title for a composer."""
    cursor = connection.execute(
        """
        SELECT id FROM films
        WHERE composer_id = ?
          AND (title = ? OR title_es = ? OR original_title = ?)
        LIMIT 1
        """,
        (composer_id, film_title, film_title, film_title),
    )
    row = cursor.fetchone()
    return row["id"] if row else None


def upsert_music_track(
    connection: sqlite3.Connection,
    composer_id: int,
    film_id: int | None,
    track: dict,
    searched_at: str,
) -> None:
    """Upsert a single track into music_tracks."""
    alternatives = track.get("free_alternatives", []) + track.get("paid_alternatives", [])
    alternatives_json = json.dumps(alternatives, ensure_ascii=False)

    best = track.get("downloaded_from")
    source = best.get("source") if best else None
    url = best.get("url") if best else None
    local_path = best.get("local_path") if best else None

    connection.execute(
        """
        INSERT INTO music_tracks (
            composer_id,
            film_id,
            title,
            work,
            rank,
            status,
            source,
            url,
            local_path,
            alternatives_json,
            searched_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(composer_id, film_id, title, work)
        DO UPDATE SET
            rank = excluded.rank,
            status = excluded.status,
            source = excluded.source,
            url = excluded.url,
            local_path = excluded.local_path,
            alternatives_json = excluded.alternatives_json,
            searched_at = excluded.searched_at,
            updated_at = datetime('now')
        """,
        (
            composer_id,
            film_id,
            track.get("cue_title"),
            track.get("film"),
            track.get("rank"),
            track.get("status"),
            source,
            url,
            local_path,
            alternatives_json,
            searched_at,
        ),
    )


def run_etl(results_path: Path, db_path: Path) -> None:
    """Run ETL for a results.json file."""
    payload = load_results(results_path)
    composer_slug = results_path.parent.name
    searched_at = payload.get("generated_at")

    connection = get_db_connection(db_path)
    try:
        composer_id = get_composer_id(connection, composer_slug)
        if composer_id is None:
            raise RuntimeError(f"Composer not found: {composer_slug}")

        for track in payload.get("tracks", []):
            film_id = get_film_id(connection, composer_id, track.get("film", ""))
            upsert_music_track(connection, composer_id, film_id, track, searched_at)

        connection.commit()
    finally:
        connection.close()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="ETL results.json into soundtrackers.db")
    parser.add_argument("results", type=Path, help="Path to results.json")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    run_etl(args.results, args.db)


if __name__ == "__main__":
    main()
