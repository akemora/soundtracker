import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from create_composer_files import (
    OUTPUT_DIR,
    create_markdown_file,
    get_composer_info,
    get_composers_from_file,
    slugify,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Generate a single composer markdown for trial.')
    parser.add_argument('--composer', '-c', help='Composer name to process (defaults to first from list).')
    return parser


def main() -> None:
    args = build_parser().parse_args()
    composers = get_composers_from_file(OUTPUT_DIR / 'composers_master_list.md')
    if not composers:
        print('Master list empty.')
        return
    chosen = args.composer or composers[0]
    slug = slugify(chosen)
    composer_folder = OUTPUT_DIR / f"test_{slug}"
    info = get_composer_info(chosen, composer_folder)
    target = OUTPUT_DIR / f"test_{slug}.md"
    create_markdown_file(info, target)
    print(f"Generated {target}")
    print(f"Biography length: {len(info.get('biography') or '')}")
    print(f"Top films: {len(info.get('top_10_films', []))}")
    if not os.getenv('TMDB_API_KEY'):
        print("TMDB_API_KEY not set (posters will be limited to public sources).")
    if info.get('external_sources'):
        print('External sources:')
        for source in info['external_sources']:
            print(f" - {source['name']}: {source['url']}")


if __name__ == '__main__':
    main()
