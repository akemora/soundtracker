"""Batch runner for Music Crawler integration."""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = APP_ROOT / "data" / "soundtrackers.db"
MUSIC_CRAWLER_ROOT = APP_ROOT.parent / "Music Crawler"
OUTPUT_BASE = APP_ROOT / "data" / "music_crawler"

logger = logging.getLogger(__name__)


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


def fetch_composer_name(connection: sqlite3.Connection, composer_slug: str) -> str | None:
    """Fetch composer name by slug."""
    cursor = connection.execute(
        "SELECT name FROM composers WHERE slug = ?",
        (composer_slug,),
    )
    row = cursor.fetchone()
    return row["name"] if row else None


def fetch_all_composer_slugs(connection: sqlite3.Connection) -> list[str]:
    """Fetch all composer slugs."""
    cursor = connection.execute("SELECT slug FROM composers ORDER BY index_num")
    return [row["slug"] for row in cursor.fetchall()]


def build_track_list_content(rows: list[sqlite3.Row]) -> str:
    """Build track list content from Top 10 rows."""
    blocks: list[str] = []
    for index, row in enumerate(rows, start=1):
        rank = row["top10_rank"] or index
        film_title = row["title_es"] or row["title"] or row["original_title"] or "Unknown"
        blocks.append(str(rank))
        blocks.append(film_title)
        blocks.append('"Main Title"')
        blocks.append("")
    return "\n".join(blocks).strip() + "\n"


def write_track_list(rows: list[sqlite3.Row]) -> Path:
    """Write track list to a temporary file and return the path."""
    content = build_track_list_content(rows)
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    temp_file.write(content)
    temp_file.flush()
    temp_file.close()
    return Path(temp_file.name)


def build_output_dir(composer_slug: str) -> Path:
    """Create output directory for a composer."""
    output_dir = OUTPUT_BASE / composer_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_music_crawler(
    track_list_path: Path,
    output_dir: Path,
    composer_name: str,
    env: dict[str, str],
    search_only: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run Music Crawler CLI via subprocess."""
    cmd = [
        "python",
        "-m",
        "src.cli.crawl",
        str(track_list_path),
        "--output",
        str(output_dir),
        "--composer",
        composer_name,
    ]
    if search_only:
        cmd.append("--search-only")
    result = subprocess.run(
        cmd,
        cwd=MUSIC_CRAWLER_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    return result


def build_subprocess_env() -> dict[str, str]:
    """Build environment for Music Crawler subprocess."""
    env = os.environ.copy()
    if "PPLX_API_KEY" not in env:
        logger.warning("PPLX_API_KEY not set; Perplexity will be unavailable")
    return env


def main() -> None:
    """Entry point for batch processing."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )
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
    args = parser.parse_args()

    if not args.composer and not args.all:
        parser.error("Provide --composer or --all")

    connection = get_db_connection(DB_PATH)
    try:
        if args.all:
            slugs = fetch_all_composer_slugs(connection)
        else:
            slugs = [args.composer]

        env = build_subprocess_env()
        for slug in slugs:
            composer_name = fetch_composer_name(connection, slug)
            if not composer_name:
                logger.error("Composer slug not found: %s", slug)
                continue

            rows = fetch_top10_films(connection, slug)
            if not rows:
                logger.warning("No Top 10 films for composer: %s", slug)
                continue

            track_list_path = write_track_list(rows)
            output_dir = build_output_dir(slug)
            result = run_music_crawler(
                track_list_path=track_list_path,
                output_dir=output_dir,
                composer_name=composer_name,
                env=env,
                search_only=args.playlist_only,
            )

            if result.stdout:
                logger.info("Music Crawler stdout: %s", result.stdout)
            if result.stderr:
                logger.warning("Music Crawler stderr: %s", result.stderr)
            if result.returncode != 0:
                raise RuntimeError(f"Music Crawler failed for {slug}")

            results_path = output_dir / "results.json"
            etl_cmd = [
                "python",
                str(APP_ROOT / "scripts" / "etl_music.py"),
                str(results_path),
                "--db",
                str(DB_PATH),
            ]
            etl_result = subprocess.run(
                etl_cmd,
                capture_output=True,
                text=True,
            )
            if etl_result.stdout:
                logger.info("ETL stdout: %s", etl_result.stdout)
            if etl_result.stderr:
                logger.warning("ETL stderr: %s", etl_result.stderr)
            if etl_result.returncode != 0:
                raise RuntimeError(f"ETL failed for {slug}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
