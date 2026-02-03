#!/usr/bin/env python3
"""Build SOUNDTRACKER SQLite database from Markdown files.

This script reads composer Markdown files from outputs/ directory,
parses them, and populates a SQLite database.

Usage:
    python scripts/build_database.py
    python scripts/build_database.py --output data/soundtrackers.db
    python scripts/build_database.py --rebuild  # Drop and recreate
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.etl.parser import ParsedComposer, parse_all_files

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class DatabaseBuilder:
    """Builds and populates the SOUNDTRACKER database."""

    def __init__(self, db_path: Path, schema_path: Path):
        """Initialize the database builder.

        Args:
            db_path: Path to the SQLite database file.
            schema_path: Path to the schema.sql file.
        """
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        logger.info("Connected to database: %s", self.db_path)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def create_schema(self, rebuild: bool = False) -> None:
        """Create database schema from SQL file.

        Args:
            rebuild: If True, drop existing tables first.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        if rebuild:
            logger.warning("Rebuilding database - dropping all tables")
            self._drop_all_tables()

        # Read and execute schema
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        self.conn.commit()
        logger.info("Database schema created")

    def _drop_all_tables(self) -> None:
        """Drop all tables in the database."""
        if not self.conn:
            return

        cursor = self.conn.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        # Get all triggers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = [row[0] for row in cursor.fetchall()]

        # Get all views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]

        # Drop triggers first
        for trigger in triggers:
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger}")

        # Drop views
        for view in views:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")

        # Drop FTS tables (virtual tables)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%USING fts5%'"
        )
        fts_tables = [row[0] for row in cursor.fetchall()]
        for table in fts_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        # Drop regular tables
        for table in tables:
            if table not in fts_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

        self.conn.commit()
        logger.info("Dropped %d tables, %d views, %d triggers", len(tables), len(views), len(triggers))

    def insert_composer(self, composer: ParsedComposer) -> int:
        """Insert a composer into the database.

        Args:
            composer: Parsed composer data.

        Returns:
            The composer's database ID.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO composers (
                index_num, name, slug, birth_year, death_year, country,
                photo_url, photo_local, biography, style, anecdotes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                composer.index_num,
                composer.name,
                composer.slug,
                composer.birth_year,
                composer.death_year,
                composer.country,
                composer.photo_url,
                composer.photo_local,
                composer.biography,
                composer.style,
                composer.anecdotes,
            ),
        )
        composer_id = cursor.lastrowid
        logger.debug("Inserted composer: %s (id=%d)", composer.name, composer_id)
        return composer_id

    def insert_films(self, composer_id: int, composer: ParsedComposer) -> int:
        """Insert films for a composer.

        Args:
            composer_id: Database ID of the composer.
            composer: Parsed composer data.

        Returns:
            Number of films inserted.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        count = 0

        # Insert Top 10 films
        for film in composer.top10:
            cursor.execute(
                """
                INSERT INTO films (
                    composer_id, title, original_title, title_es, year,
                    poster_url, poster_local, is_top10, top10_rank
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    composer_id,
                    film.title,
                    film.original_title,
                    film.title_es,
                    film.year,
                    film.poster_url,
                    film.poster_local,
                    film.top10_rank,
                ),
            )
            count += 1

        # Insert filmography (avoiding duplicates with top 10)
        top10_titles = {f.title.lower() for f in composer.top10}
        for film in composer.films:
            if film.title.lower() not in top10_titles:
                cursor.execute(
                    """
                    INSERT INTO films (
                        composer_id, title, original_title, title_es, year,
                        poster_url, poster_local, is_top10, top10_rank
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL)
                    """,
                    (
                        composer_id,
                        film.title,
                        film.original_title,
                        film.title_es,
                        film.year,
                        film.poster_url,
                        film.poster_local,
                    ),
                )
                count += 1

        logger.debug("Inserted %d films for composer %d", count, composer_id)
        return count

    def insert_awards(self, composer_id: int, composer: ParsedComposer) -> int:
        """Insert awards for a composer.

        Args:
            composer_id: Database ID of the composer.
            composer: Parsed composer data.

        Returns:
            Number of awards inserted.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        count = 0

        for award in composer.awards:
            cursor.execute(
                """
                INSERT INTO awards (
                    composer_id, award_name, category, year, film_title, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    composer_id,
                    award.award_name,
                    award.category,
                    award.year,
                    award.film_title,
                    award.status,
                ),
            )
            count += 1

        logger.debug("Inserted %d awards for composer %d", count, composer_id)
        return count

    def insert_sources(self, composer_id: int, composer: ParsedComposer) -> int:
        """Insert sources for a composer.

        Args:
            composer_id: Database ID of the composer.
            composer: Parsed composer data.

        Returns:
            Number of sources inserted.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        count = 0

        # Insert reference sources
        for source in composer.sources:
            cursor.execute(
                """
                INSERT INTO sources (
                    composer_id, name, url, snippet, source_type
                ) VALUES (?, ?, ?, ?, 'reference')
                """,
                (composer_id, source.name, source.url, source.snippet),
            )
            count += 1

        # Insert snippet sources
        for snippet in composer.snippets:
            cursor.execute(
                """
                INSERT INTO sources (
                    composer_id, name, url, snippet, source_type
                ) VALUES (?, ?, ?, ?, 'snippet')
                """,
                (composer_id, snippet.name, snippet.url, snippet.snippet),
            )
            count += 1

        logger.debug("Inserted %d sources for composer %d", count, composer_id)
        return count

    def rebuild_fts_index(self) -> None:
        """Rebuild the FTS5 full-text search index."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        logger.info("Rebuilding FTS index...")
        self.conn.execute("INSERT INTO fts_composers(fts_composers) VALUES('rebuild')")
        self.conn.commit()
        logger.info("FTS index rebuilt")

    def validate_integrity(self) -> dict:
        """Validate database integrity.

        Returns:
            Dictionary with validation results.
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        results = {}

        # Count records
        cursor.execute("SELECT COUNT(*) FROM composers")
        results["composers"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM films")
        results["films"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM films WHERE is_top10 = 1")
        results["top10_films"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM awards")
        results["awards"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM awards WHERE status = 'win'")
        results["award_wins"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sources")
        results["sources"] = cursor.fetchone()[0]

        # Check FTS
        cursor.execute("SELECT COUNT(*) FROM fts_composers")
        results["fts_entries"] = cursor.fetchone()[0]

        # Check foreign key integrity
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        results["foreign_key_errors"] = len(fk_errors)

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        results["integrity_check"] = integrity

        return results

    def import_composers(self, composers: list[ParsedComposer]) -> dict:
        """Import all composers into the database.

        Args:
            composers: List of parsed composer data.

        Returns:
            Dictionary with import statistics.
        """
        stats = {
            "composers": 0,
            "films": 0,
            "awards": 0,
            "sources": 0,
            "errors": 0,
        }

        for composer in composers:
            try:
                composer_id = self.insert_composer(composer)
                stats["composers"] += 1
                stats["films"] += self.insert_films(composer_id, composer)
                stats["awards"] += self.insert_awards(composer_id, composer)
                stats["sources"] += self.insert_sources(composer_id, composer)
            except Exception as e:
                logger.error("Failed to import %s: %s", composer.name, e)
                stats["errors"] += 1

        # Commit all changes
        if self.conn:
            self.conn.commit()

        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build SOUNDTRACKER database from Markdown files"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=project_root / "data" / "soundtrackers.db",
        help="Output database path (default: data/soundtrackers.db)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=project_root / "scripts" / "schema.sql",
        help="Schema SQL file path",
    )
    parser.add_argument(
        "--inputs",
        "-i",
        type=Path,
        default=project_root / "outputs",
        help="Input directory with Markdown files (default: outputs/)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and recreate database",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Parse Markdown files
    logger.info("Parsing Markdown files from: %s", args.inputs)
    composers = parse_all_files(args.inputs)

    if not composers:
        logger.error("No composer files found in %s", args.inputs)
        sys.exit(1)

    logger.info("Found %d composers to import", len(composers))

    # Build database
    builder = DatabaseBuilder(args.output, args.schema)

    try:
        builder.connect()
        builder.create_schema(rebuild=args.rebuild)

        # Import data
        logger.info("Importing composers...")
        stats = builder.import_composers(composers)

        logger.info(
            "Import complete: %d composers, %d films, %d awards, %d sources, %d errors",
            stats["composers"],
            stats["films"],
            stats["awards"],
            stats["sources"],
            stats["errors"],
        )

        # Rebuild FTS index
        builder.rebuild_fts_index()

        # Validate
        validation = builder.validate_integrity()
        logger.info("Validation results:")
        for key, value in validation.items():
            logger.info("  %s: %s", key, value)

        if validation["foreign_key_errors"] > 0:
            logger.warning("Database has foreign key errors!")

        if validation["integrity_check"] != "ok":
            logger.warning("Database integrity check failed: %s", validation["integrity_check"])

        # Report database size
        db_size = args.output.stat().st_size
        logger.info("Database size: %.2f MB", db_size / (1024 * 1024))

    finally:
        builder.close()

    logger.info("Database built successfully: %s", args.output)


if __name__ == "__main__":
    main()
