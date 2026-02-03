#!/usr/bin/env python3
"""Generate composer profile files using the SOUNDTRACKER pipeline.

This script is a thin CLI wrapper around the soundtracker.pipeline module.
It replaces the monolithic create_composer_files.py with a modular approach.

Usage:
    # Process all composers from master list
    python -m scripts.generate_composers

    # Process specific range
    python -m scripts.generate_composers --start 1 --end 10

    # Process single composer by name
    python -m scripts.generate_composers --name "John Williams"

    # Dry run (no file writes)
    python -m scripts.generate_composers --dry-run

Environment Variables:
    START_INDEX: Start processing from this index (default: 1)
    END_INDEX: Stop at this index (optional)
    LOG_LEVEL: Logging verbosity (default: INFO)
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from soundtracker.config import settings
from soundtracker.logging_config import setup_logging
from soundtracker.pipeline import ComposerPipeline, process_composers_from_list


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate composer profile Markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Process single composer by name",
    )
    parser.add_argument(
        "--index",
        type=int,
        help="Index for single composer (use with --name)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=settings.start_index,
        help=f"Start index (default: {settings.start_index})",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=settings.end_index,
        help="End index (default: process all)",
    )
    parser.add_argument(
        "--master-list",
        type=Path,
        default=settings.output_dir / "composers_master_list.md",
        help="Path to master list file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.output_dir,
        help="Output directory",
    )
    parser.add_argument(
        "--no-posters",
        action="store_true",
        help="Skip poster downloads",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Configure logging
    import logging
    level = logging.DEBUG if args.verbose else (
        logging.WARNING if args.quiet else logging.INFO
    )
    setup_logging(level=level)
    logger = logging.getLogger(__name__)

    # Dry run mode
    if args.dry_run:
        logger.info("DRY RUN MODE - no files will be written")
        if args.name:
            logger.info("Would process: %s (index=%s)", args.name, args.index)
        else:
            logger.info("Would process composers %d-%s from %s",
                       args.start, args.end or "end", args.master_list)
        return 0

    # Process single composer
    if args.name:
        logger.info("Processing single composer: %s", args.name)
        pipeline = ComposerPipeline(
            output_dir=args.output_dir,
            download_posters=not args.no_posters,
        )
        try:
            info = pipeline.process_composer(args.name, index=args.index)
            logger.info("Successfully generated profile for %s", info.name)
            logger.info("  Filmography: %d films", len(info.filmography))
            logger.info("  Awards: %d", len(info.awards))
            logger.info("  Top 10: %d films", len(info.top_10))
            return 0
        except Exception as e:
            logger.error("Failed to process %s: %s", args.name, e)
            return 1

    # Process from master list
    if not args.master_list.exists():
        logger.error("Master list not found: %s", args.master_list)
        return 1

    results = process_composers_from_list(
        args.master_list,
        output_dir=args.output_dir,
        start_index=args.start,
        end_index=args.end,
    )

    logger.info("Processed %d composers successfully", len(results))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
