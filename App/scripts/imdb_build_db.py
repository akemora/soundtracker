#!/usr/bin/env python3
"""Download IMDb datasets and build a local SQLite database.

Required datasets:
  - title.principals.tsv.gz (filtered to category == 'composer')
  - name.basics.tsv.gz
  - title.basics.tsv.gz
Optional:
  - title.ratings.tsv.gz
"""

from __future__ import annotations

import argparse
import csv
import gzip
import logging
import sqlite3
import urllib.request
from pathlib import Path
from typing import Iterable, Optional

from soundtracker.config import settings

logger = logging.getLogger(__name__)

DATASET_URLS = {
    "title.principals.tsv.gz": "https://datasets.imdbws.com/title.principals.tsv.gz",
    "name.basics.tsv.gz": "https://datasets.imdbws.com/name.basics.tsv.gz",
    "title.basics.tsv.gz": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "title.ratings.tsv.gz": "https://datasets.imdbws.com/title.ratings.tsv.gz",
}

REQUIRED_FILES = [
    "title.principals.tsv.gz",
    "name.basics.tsv.gz",
    "title.basics.tsv.gz",
]


def download_file(url: str, dest: Path) -> None:
    """Download a file if it does not already exist."""
    if dest.exists():
        logger.info("Already present: %s", dest.name)
        return
    logger.info("Downloading %s -> %s", url, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def iter_tsv_gz(path: Path) -> Iterable[list[str]]:
    """Yield rows from a gzipped TSV file."""
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader, None)  # header
        yield from reader


def clean_int(value: str) -> Optional[int]:
    """Convert IMDb int field to int or None."""
    if not value or value == "\\N":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def clean_float(value: str) -> Optional[float]:
    """Convert IMDb float field to float or None."""
    if not value or value == "\\N":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def insert_batches(
    conn: sqlite3.Connection,
    sql: str,
    rows: Iterable[tuple],
    batch_size: int = 50000,
) -> None:
    """Insert rows in batches for performance."""
    batch: list[tuple] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            conn.executemany(sql, batch)
            conn.commit()
            batch.clear()
    if batch:
        conn.executemany(sql, batch)
        conn.commit()


def build_db(data_dir: Path, db_path: Path, include_ratings: bool) -> None:
    """Build SQLite database from IMDb TSV datasets."""
    logger.info("Building IMDb SQLite database at %s", db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        logger.info("Removing existing database: %s", db_path)
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=200000;")

    conn.executescript(
        """
        CREATE TABLE composer_credits (
            tconst TEXT,
            nconst TEXT,
            ordering INTEGER,
            job TEXT,
            PRIMARY KEY (tconst, nconst, ordering)
        );
        CREATE TABLE people (
            nconst TEXT PRIMARY KEY,
            primaryName TEXT,
            birthYear INTEGER,
            deathYear INTEGER,
            primaryProfession TEXT,
            knownForTitles TEXT
        );
        CREATE TABLE titles (
            tconst TEXT PRIMARY KEY,
            titleType TEXT,
            primaryTitle TEXT,
            originalTitle TEXT,
            isAdult INTEGER,
            startYear INTEGER,
            endYear INTEGER,
            runtimeMinutes INTEGER,
            genres TEXT
        );
        CREATE TABLE title_ratings (
            tconst TEXT PRIMARY KEY,
            averageRating REAL,
            numVotes INTEGER
        );
        """
    )

    principals_path = data_dir / "title.principals.tsv.gz"
    name_path = data_dir / "name.basics.tsv.gz"
    title_path = data_dir / "title.basics.tsv.gz"
    ratings_path = data_dir / "title.ratings.tsv.gz"

    logger.info("Loading composer credits...")
    def iter_composer_rows() -> Iterable[tuple]:
        for row in iter_tsv_gz(principals_path):
            if len(row) < 6:
                continue
            if row[3] != "composer":
                continue
            yield (
                row[0],
                row[2],
                clean_int(row[1]),
                None if row[4] == "\\N" else row[4],
            )

    insert_batches(
        conn,
        "INSERT INTO composer_credits (tconst, nconst, ordering, job) VALUES (?, ?, ?, ?)",
        iter_composer_rows(),
    )

    logger.info("Loading people...")
    def iter_people_rows() -> Iterable[tuple]:
        for row in iter_tsv_gz(name_path):
            if len(row) < 6:
                continue
            yield (
                row[0],
                row[1],
                clean_int(row[2]),
                clean_int(row[3]),
                None if row[4] == "\\N" else row[4],
                None if row[5] == "\\N" else row[5],
            )

    insert_batches(
        conn,
        "INSERT INTO people (nconst, primaryName, birthYear, deathYear, primaryProfession, knownForTitles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        iter_people_rows(),
    )

    logger.info("Loading titles...")
    def iter_title_rows() -> Iterable[tuple]:
        for row in iter_tsv_gz(title_path):
            if len(row) < 9:
                continue
            yield (
                row[0],
                row[1],
                row[2],
                row[3],
                clean_int(row[4]),
                clean_int(row[5]),
                clean_int(row[6]),
                clean_int(row[7]),
                None if row[8] == "\\N" else row[8],
            )

    insert_batches(
        conn,
        "INSERT INTO titles (tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, "
        "endYear, runtimeMinutes, genres) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        iter_title_rows(),
    )

    if include_ratings and ratings_path.exists():
        logger.info("Loading ratings...")
        def iter_ratings_rows() -> Iterable[tuple]:
            for row in iter_tsv_gz(ratings_path):
                if len(row) < 3:
                    continue
                yield (row[0], clean_float(row[1]), clean_int(row[2]))

        insert_batches(
            conn,
            "INSERT INTO title_ratings (tconst, averageRating, numVotes) VALUES (?, ?, ?)",
            iter_ratings_rows(),
        )

    logger.info("Creating indexes...")
    conn.executescript(
        """
        CREATE INDEX idx_composer_nconst ON composer_credits (nconst);
        CREATE INDEX idx_people_name ON people (primaryName);
        CREATE INDEX idx_people_name_nocase ON people (primaryName COLLATE NOCASE);
        CREATE INDEX idx_titles_year ON titles (startYear);
        CREATE INDEX idx_titles_type ON titles (titleType);
        """
    )
    conn.commit()
    conn.close()
    logger.info("IMDb database built successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download IMDb datasets and build SQLite DB.")
    parser.add_argument("--data-dir", type=Path, default=settings.imdb_data_dir)
    parser.add_argument("--db-path", type=Path, default=settings.imdb_db_path)
    parser.add_argument("--skip-download", action="store_true", help="Skip dataset downloads.")
    parser.add_argument("--skip-ratings", action="store_true", help="Skip ratings dataset.")
    parser.add_argument("--build", action="store_true", help="Force DB rebuild.")

    args = parser.parse_args()
    data_dir = args.data_dir
    db_path = args.db_path

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not args.skip_download:
        for filename in REQUIRED_FILES:
            download_file(DATASET_URLS[filename], data_dir / filename)
        if not args.skip_ratings:
            download_file(DATASET_URLS["title.ratings.tsv.gz"], data_dir / "title.ratings.tsv.gz")

    if args.build or not db_path.exists():
        build_db(data_dir, db_path, include_ratings=not args.skip_ratings)
    else:
        logger.info("Database already exists: %s (use --build to rebuild)", db_path)


if __name__ == "__main__":
    main()
