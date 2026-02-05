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


def get_pending_composers(db_path: Path) -> list[tuple[str, str]]:
    """Fetch composers without generated playlists."""
    connection = get_db_connection(db_path)
    try:
        cursor = connection.execute(
            """
            SELECT c.slug, c.name
            FROM composers c
            LEFT JOIN composer_playlists p ON c.id = p.composer_id
            WHERE p.id IS NULL
            ORDER BY c.name
            """
        )
        return [(row["slug"], row["name"]) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_outdated_composers(db_path: Path, days: int = 30) -> list[tuple[str, str, str]]:
    """Fetch composers with playlists older than N days."""
    connection = get_db_connection(db_path)
    try:
        cursor = connection.execute(
            """
            SELECT c.slug, c.name, p.updated_at
            FROM composers c
            JOIN composer_playlists p ON c.id = p.composer_id
            WHERE p.updated_at < datetime('now', ?)
            ORDER BY p.updated_at ASC
            """,
            (f"-{days} days",),
        )
        return [(row["slug"], row["name"], row["updated_at"]) for row in cursor.fetchall()]
    finally:
        connection.close()


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
    refresh: bool = False,
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
    if refresh:
        cmd.append("--refresh")
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


def commit_outputs(output_dir: Path, composer_slug: str) -> None:
    """Commit generated outputs for a composer if requested."""
    repo_root = APP_ROOT.parent
    candidate_files = [
        output_dir / "results.json",
        output_dir / "playlist.json",
        output_dir / "REPORT.md",
    ]
    existing_files = [str(path) for path in candidate_files if path.exists()]
    if not existing_files:
        logger.info("No output files to commit for %s", composer_slug)
        return

    add_result = subprocess.run(
        ["git", "add", *existing_files],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if add_result.returncode != 0:
        logger.error("Git add failed for %s: %s", composer_slug, add_result.stderr)
        return

    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_root,
    )
    if diff_result.returncode == 0:
        logger.info("No staged changes to commit for %s", composer_slug)
        return

    commit_result = subprocess.run(
        ["git", "commit", "-m", f"feat(music): sync {composer_slug}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if commit_result.returncode != 0:
        logger.error("Git commit failed for %s: %s", composer_slug, commit_result.stderr)
        return
    logger.info("Committed outputs for %s", composer_slug)


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
    parser.add_argument(
        "--pending",
        action="store_true",
        help="List composers without playlists",
    )
    parser.add_argument(
        "--outdated",
        action="store_true",
        help="List composers with playlists older than N days",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days threshold for outdated playlists",
    )
    parser.add_argument(
        "--sync-new",
        action="store_true",
        help="Process composers without playlists",
    )
    parser.add_argument(
        "--sync-outdated",
        action="store_true",
        help="Process composers with outdated playlists",
    )
    parser.add_argument(
        "--sync-all",
        action="store_true",
        help="Process pending + outdated composers",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh (ignore Music Crawler cache)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Auto-commit generated outputs",
    )
    args = parser.parse_args()

    mode_flags = [
        args.composer is not None,
        args.all,
        args.pending,
        args.outdated,
        args.sync_new,
        args.sync_outdated,
        args.sync_all,
    ]
    if sum(1 for flag in mode_flags if flag) != 1:
        parser.error(
            "Choose exactly one mode: --composer, --all, --pending, --outdated, "
            "--sync-new, --sync-outdated, or --sync-all"
        )

    if args.pending:
        pending = get_pending_composers(DB_PATH)
        logger.info("Pendientes (sin playlist): %s compositores", len(pending))
        for slug, name in pending:
            logger.info("  - %s (%s)", slug, name)
        return

    if args.outdated:
        outdated = get_outdated_composers(DB_PATH, args.days)
        logger.info("Desactualizados (>%s días): %s compositores", args.days, len(outdated))
        for slug, name, updated_at in outdated:
            logger.info("  - %s (%s) última: %s", slug, name, updated_at)
        return

    connection = get_db_connection(DB_PATH)
    try:
        if args.all:
            slugs = fetch_all_composer_slugs(connection)
        elif args.sync_new:
            slugs = [slug for slug, _ in get_pending_composers(DB_PATH)]
        elif args.sync_outdated:
            slugs = [slug for slug, _, _ in get_outdated_composers(DB_PATH, args.days)]
        elif args.sync_all:
            pending = [slug for slug, _ in get_pending_composers(DB_PATH)]
            outdated = [slug for slug, _, _ in get_outdated_composers(DB_PATH, args.days)]
            slugs = list(dict.fromkeys([*pending, *outdated]))
        else:
            slugs = [args.composer]

        if not slugs:
            logger.info("No composers to process for requested mode.")
            return

        env = build_subprocess_env()
        processed: list[str] = []
        failed: list[str] = []
        total = len(slugs)
        for index, slug in enumerate(slugs, start=1):
            logger.info("Processing %s/%s: %s", index, total, slug)
            try:
                composer_name = fetch_composer_name(connection, slug)
                if not composer_name:
                    raise RuntimeError(f"Composer slug not found: {slug}")

                rows = fetch_top10_films(connection, slug)
                if not rows:
                    logger.warning("No Top 10 films for composer: %s", slug)
                    continue

                track_list_path = write_track_list(rows)
                output_dir = build_output_dir(slug)
                try:
                    result = run_music_crawler(
                        track_list_path=track_list_path,
                        output_dir=output_dir,
                        composer_name=composer_name,
                        env=env,
                        search_only=args.playlist_only,
                        refresh=args.force,
                    )
                finally:
                    track_list_path.unlink(missing_ok=True)

                if result.stdout:
                    logger.info("Music Crawler stdout: %s", result.stdout)
                if result.stderr:
                    logger.warning("Music Crawler stderr: %s", result.stderr)
                if result.returncode != 0:
                    raise RuntimeError(f"Music Crawler failed for {slug}")

                results_path = output_dir / "results.json"
                if not results_path.exists():
                    raise RuntimeError(f"Missing results.json for {slug}")

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

                if args.commit:
                    commit_outputs(output_dir, slug)

                processed.append(slug)
            except Exception as exc:
                logger.error("Failed to process %s: %s", slug, exc, exc_info=True)
                failed.append(slug)

        logger.info("Batch complete. Success: %s | Failed: %s", len(processed), len(failed))
        if failed:
            raise RuntimeError(f"Failed composers: {', '.join(failed)}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
