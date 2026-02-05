"""Batch runner for Music Crawler integration."""

from __future__ import annotations

import argparse


def main() -> None:
    """Entry point for batch processing."""
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
    parser.parse_args()


if __name__ == "__main__":
    main()
