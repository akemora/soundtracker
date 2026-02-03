#!/usr/bin/env python3
"""Update composer countries from master list.

This script reads the master list markdown file and updates
the country field in the database for all composers.
"""

import re
import sqlite3
from pathlib import Path


def parse_master_list(master_list_path: Path) -> dict[str, str]:
    """Parse the master list and extract country by composer name.

    Returns:
        Dictionary mapping composer name to country.
    """
    countries = {}

    with open(master_list_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match table rows: | 001 | Name | Birth | Death | Country |
    pattern = r"\|\s*\d+\s*\|\s*([^|]+)\s*\|\s*\d+\s*\|\s*\d*\s*\|\s*([^|]+)\s*\|"

    for match in re.finditer(pattern, content):
        name = match.group(1).strip()
        country = match.group(2).strip()
        if name and country:
            countries[name] = country

    return countries


def update_database(db_path: Path, countries: dict[str, str]) -> tuple[int, int]:
    """Update composer countries in database.

    Returns:
        Tuple of (updated_count, not_found_count)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    not_found = 0

    for name, country in countries.items():
        cursor.execute(
            "UPDATE composers SET country = ? WHERE name = ?",
            (country, name)
        )
        if cursor.rowcount > 0:
            updated += 1
            print(f"  Updated: {name} -> {country}")
        else:
            not_found += 1
            print(f"  Not found in DB: {name}")

    conn.commit()
    conn.close()

    return updated, not_found


def main():
    """Main entry point."""
    # Paths
    project_root = Path(__file__).parent.parent
    master_list_path = project_root / "outputs" / "composers_master_list.md"
    db_path = project_root / "data" / "soundtrackers.db"

    print(f"Reading master list from: {master_list_path}")
    print(f"Database: {db_path}")
    print()

    if not master_list_path.exists():
        print(f"Error: Master list not found at {master_list_path}")
        return 1

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return 1

    # Parse master list
    countries = parse_master_list(master_list_path)
    print(f"Found {len(countries)} composers in master list")
    print()

    # Update database
    print("Updating database...")
    updated, not_found = update_database(db_path, countries)

    print()
    print(f"Summary:")
    print(f"  Updated: {updated}")
    print(f"  Not found: {not_found}")

    return 0


if __name__ == "__main__":
    exit(main())
