import json
import sqlite3
from pathlib import Path

from scripts.etl_music import run_etl


def create_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE composers (id INTEGER PRIMARY KEY, slug TEXT)"
    )
    conn.execute(
        "CREATE TABLE films (id INTEGER PRIMARY KEY, composer_id INTEGER, title TEXT, title_es TEXT, original_title TEXT)"
    )
    conn.execute(
        """
        CREATE TABLE music_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composer_id INTEGER NOT NULL,
            film_id INTEGER,
            title TEXT NOT NULL,
            work TEXT NOT NULL,
            rank INTEGER,
            status TEXT,
            source TEXT,
            url TEXT,
            local_path TEXT,
            alternatives_json TEXT,
            searched_at TEXT,
            updated_at TEXT,
            UNIQUE(composer_id, film_id, title, work)
        )
        """
    )
    conn.execute("INSERT INTO composers (id, slug) VALUES (1, 'john_williams')")
    conn.execute(
        "INSERT INTO films (id, composer_id, title, title_es, original_title) VALUES (1, 1, 'Star Wars', NULL, NULL)"
    )
    conn.commit()
    conn.close()


def test_etl_music_inserts_track(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    create_db(db_path)

    results = {
        "composer": "John Williams",
        "generated_at": "2026-02-05T00:00:00",
        "tracks": [
            {
                "rank": 1,
                "film": "Star Wars",
                "cue_title": "Main Title",
                "description": "",
                "notes": "",
                "status": "free_available",
                "downloaded_from": None,
                "free_alternatives": [],
                "paid_alternatives": [],
            }
        ],
    }
    results_dir = tmp_path / "john_williams"
    results_dir.mkdir()
    results_path = results_dir / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")

    run_etl(results_path, db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT COUNT(*) FROM music_tracks").fetchone()
    conn.close()

    assert row[0] == 1


def test_etl_music_upsert_deduplicates(tmp_path) -> None:
    db_path = tmp_path / "test.db"
    create_db(db_path)

    results = {
        "composer": "John Williams",
        "generated_at": "2026-02-05T00:00:00",
        "tracks": [
            {
                "rank": 1,
                "film": "Star Wars",
                "cue_title": "Main Title",
                "description": "",
                "notes": "",
                "status": "free_available",
                "downloaded_from": None,
                "free_alternatives": [],
                "paid_alternatives": [],
            }
        ],
    }
    results_dir = tmp_path / "john_williams"
    results_dir.mkdir()
    results_path = results_dir / "results.json"
    results_path.write_text(json.dumps(results), encoding="utf-8")

    run_etl(results_path, db_path)
    run_etl(results_path, db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT COUNT(*) FROM music_tracks").fetchone()
    conn.close()

    assert row[0] == 1
