#!/usr/bin/env python3
"""Detect and remove duplicate poster images in outputs/.

By default scans per-composer poster folders and reports duplicates.
Use --delete to remove duplicates. Optionally remove legacy photo.jpg files.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Iterable

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
CHUNK_SIZE = 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find and remove duplicate poster images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("outputs"),
        help="Root outputs directory",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicate poster files",
    )
    parser.add_argument(
        "--remove-photo-jpg",
        action="store_true",
        help="Delete legacy photo.jpg files under outputs",
    )
    parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Detect duplicates across all composers (not just per composer)",
    )
    return parser.parse_args()


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def iter_poster_files(root: Path) -> Iterable[Path]:
    for composer_dir in sorted(root.iterdir()):
        if not composer_dir.is_dir():
            continue
        if composer_dir.name.startswith("_"):
            continue
        posters_dir = composer_dir / "posters"
        if not posters_dir.is_dir():
            continue
        for poster in sorted(posters_dir.iterdir()):
            if poster.is_file() and poster.suffix.lower() in IMAGE_EXTS:
                yield poster


def iter_composer_posters(root: Path) -> Iterable[tuple[Path, list[Path]]]:
    for composer_dir in sorted(root.iterdir()):
        if not composer_dir.is_dir():
            continue
        if composer_dir.name.startswith("_"):
            continue
        posters_dir = composer_dir / "posters"
        if not posters_dir.is_dir():
            continue
        posters = [
            poster
            for poster in sorted(posters_dir.iterdir())
            if poster.is_file() and poster.suffix.lower() in IMAGE_EXTS
        ]
        if posters:
            yield composer_dir, posters


def remove_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def main() -> int:
    args = parse_args()
    root = args.root
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root directory not found: {root}")

    duplicates: list[tuple[Path, Path]] = []
    bytes_freed = 0

    if args.global_scope:
        seen: dict[str, Path] = {}
        for poster in iter_poster_files(root):
            digest = file_hash(poster)
            if digest in seen:
                duplicates.append((poster, seen[digest]))
            else:
                seen[digest] = poster
    else:
        for composer_dir, posters in iter_composer_posters(root):
            seen: dict[str, Path] = {}
            for poster in posters:
                digest = file_hash(poster)
                if digest in seen:
                    duplicates.append((poster, seen[digest]))
                else:
                    seen[digest] = poster

    if duplicates:
        print(f"Found {len(duplicates)} duplicate posters")
        for dupe, keep in duplicates:
            print(f"DUPLICATE: {dupe} (keep {keep})")
            if args.delete:
                try:
                    bytes_freed += dupe.stat().st_size
                except OSError:
                    pass
                remove_file(dupe)
        if args.delete:
            print(f"Deleted {len(duplicates)} duplicate posters")
            print(f"Approx bytes freed: {bytes_freed}")
    else:
        print("No duplicate posters found")

    if args.remove_photo_jpg:
        removed = 0
        for photo in root.rglob("photo.jpg"):
            if photo.is_file():
                remove_file(photo)
                removed += 1
        print(f"Removed photo.jpg files: {removed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
