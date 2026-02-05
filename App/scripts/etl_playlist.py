"""ETL for playlist.json into soundtrackers.db."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = APP_ROOT / "data" / "soundtrackers.db"


def load_playlist(path: Path) -> dict:
    """Load playlist.json file."""
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


def upsert_playlist(
    connection: sqlite3.Connection,
    composer_id: int,
    payload: dict,
) -> int:
    """Upsert composer playlist and return playlist_id."""
    tracks = payload.get("tracks", [])
    total_tracks = payload.get("total_tracks", len(tracks))
    free_count = payload.get("free_count", sum(1 for t in tracks if t.get("is_free")))
    paid_count = payload.get("paid_count", total_tracks - free_count)
    generated_at = payload.get("generated_at")

    playlist_json = json.dumps(payload, ensure_ascii=False)

    connection.execute(
        """
        INSERT INTO composer_playlists (
            composer_id,
            total_tracks,
            free_count,
            paid_count,
            playlist_json,
            generated_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(composer_id) DO UPDATE SET
            total_tracks = excluded.total_tracks,
            free_count = excluded.free_count,
            paid_count = excluded.paid_count,
            playlist_json = excluded.playlist_json,
            generated_at = excluded.generated_at,
            updated_at = datetime('now')
        """,
        (
            composer_id,
            total_tracks,
            free_count,
            paid_count,
            playlist_json,
            generated_at,
        ),
    )

    cursor = connection.execute(
        "SELECT id FROM composer_playlists WHERE composer_id = ?",
        (composer_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise RuntimeError("Failed to fetch playlist id")
    return row["id"]


def replace_playlist_tracks(
    connection: sqlite3.Connection,
    playlist_id: int,
    tracks: list[dict],
) -> None:
    """Replace playlist_tracks for a playlist."""
    connection.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))

    for track in tracks:
        status = "free" if track.get("is_free") else "paid"
        connection.execute(
            """
            INSERT INTO playlist_tracks (
                playlist_id,
                position,
                film_title,
                film_year,
                track_title,
                source,
                url,
                embed_url,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                playlist_id,
                track.get("position"),
                track.get("film"),
                track.get("film_year"),
                track.get("track_title"),
                track.get("source"),
                track.get("url"),
                track.get("embed_url"),
                status,
            ),
        )


def run_etl(playlist_path: Path, db_path: Path) -> None:
    """Run ETL for a playlist.json file."""
    payload = load_playlist(playlist_path)
    composer_slug = payload.get("composer_slug")
    if not composer_slug:
        raise RuntimeError("playlist.json missing composer_slug")

    connection = get_db_connection(db_path)
    try:
        composer_id = get_composer_id(connection, composer_slug)
        if composer_id is None:
            raise RuntimeError(f"Composer not found: {composer_slug}")

        playlist_id = upsert_playlist(connection, composer_id, payload)
        replace_playlist_tracks(connection, playlist_id, payload.get("tracks", []))
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="ETL playlist.json into soundtrackers.db")
    parser.add_argument("playlist", type=Path, help="Path to playlist.json")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    run_etl(args.playlist, args.db)


if __name__ == "__main__":
    main()
