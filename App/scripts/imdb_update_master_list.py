#!/usr/bin/env python3
"""Update the master list using IMDb dataset metadata."""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from soundtracker.clients.imdb_dataset import ImdbDataset
from soundtracker.config import settings

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR / "scripts"))
from manage_master_list import MASTER_LIST_PATH, MasterListManager  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update master list with IMDb data.")
    parser.add_argument(
        "--master-list",
        type=Path,
        default=MASTER_LIST_PATH,
        help="Path to master list Markdown file",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=settings.imdb_db_path,
        help="Path to IMDb SQLite database",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only fill missing birth/death years",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing years if IMDb differs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write changes to disk",
    )
    parser.add_argument(
        "--preserve-order",
        action="store_true",
        help="Preserve current row order (do not sort by index)",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    imdb = ImdbDataset(args.db_path)
    if not imdb.is_available:
        logger.error("IMDb database not found: %s", args.db_path)
        return

    manager = MasterListManager(args.master_list)
    manager.load()

    updates = 0
    mismatches = 0

    conn = sqlite3.connect(imdb.db_path)
    conn.row_factory = sqlite3.Row

    for entry in manager.entries:
        person = imdb.get_person_years(entry.name, conn=conn)
        if not person:
            continue

        new_birth = person.birth_year
        new_death = person.death_year

        # Birth year
        if new_birth:
            if entry.birth_year is None:
                entry.birth_year = new_birth
                updates += 1
            elif entry.birth_year != new_birth:
                if args.overwrite:
                    entry.birth_year = new_birth
                    updates += 1
                elif not args.only_missing:
                    mismatches += 1

        # Death year
        if new_death:
            if entry.death_year is None:
                entry.death_year = new_death
                updates += 1
            elif entry.death_year != new_death:
                if args.overwrite:
                    entry.death_year = new_death
                    updates += 1
                elif not args.only_missing:
                    mismatches += 1

    conn.close()

    logger.info("IMDb update completed. Updates=%d, mismatches=%d", updates, mismatches)

    if args.dry_run:
        logger.info("Dry run enabled; no changes written.")
        return

    manager.save(sort_by_index=not args.preserve_order)


if __name__ == "__main__":
    main()
