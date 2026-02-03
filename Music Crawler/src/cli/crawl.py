"""Main CLI entry point for Music Crawler."""

import argparse
import json
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.downloaders.ytdlp import YtDlpDownloader
from src.models.track import CrawlResult, SearchResult, Track
from src.parsers.track_list import parse_single_track, parse_track_list
from src.report.generator import ReportGenerator

# Free source searchers
from src.searchers.archive_org import ArchiveOrgSearcher
from src.searchers.fma import FreeMusiceArchiveSearcher
from src.searchers.jamendo import JamendoSearcher
from src.searchers.musopen import IMSLPSearcher, MusopenSearcher
from src.searchers.soundcloud import SoundCloudSearcher
from src.searchers.youtube import YouTubeSearcher

# Paid source searchers (log only)
from src.searchers.amazon import AmazonMusicSearcher
from src.searchers.bandcamp import BandcampSearcher
from src.searchers.deezer import DeezerSearcher
from src.searchers.spotify import ITunesSearcher, SpotifySearcher
from src.searchers.tidal import QobuzSearcher, TidalSearcher

console = Console()

# Default output directory (relative to project)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_DOWNLOADS = PROJECT_ROOT / "downloads"

# All available sources with metadata
ALL_SOURCES = {
    # Free sources (can download)
    "youtube": {"class": YouTubeSearcher, "free": True, "api": True, "desc": "Video extraction via yt-dlp"},
    "archive": {"class": ArchiveOrgSearcher, "free": True, "api": True, "desc": "Public domain recordings"},
    "soundcloud": {"class": SoundCloudSearcher, "free": True, "api": False, "desc": "Some free tracks"},
    "jamendo": {"class": JamendoSearcher, "free": True, "api": False, "desc": "Creative Commons music"},
    "fma": {"class": FreeMusiceArchiveSearcher, "free": True, "api": False, "desc": "Creative Commons archive"},
    "musopen": {"class": MusopenSearcher, "free": True, "api": False, "desc": "Public domain classical"},
    "imslp": {"class": IMSLPSearcher, "free": True, "api": False, "desc": "Public domain scores/recordings"},
    # Paid sources (log only)
    "spotify": {"class": SpotifySearcher, "free": False, "api": False, "desc": "Subscription streaming"},
    "itunes": {"class": ITunesSearcher, "free": False, "api": True, "desc": "Purchase per track"},
    "deezer": {"class": DeezerSearcher, "free": False, "api": True, "desc": "Hi-Fi streaming"},
    "amazon": {"class": AmazonMusicSearcher, "free": False, "api": False, "desc": "HD/Ultra HD streaming"},
    "tidal": {"class": TidalSearcher, "free": False, "api": False, "desc": "MQA Hi-Res streaming"},
    "qobuz": {"class": QobuzSearcher, "free": False, "api": False, "desc": "Hi-Res specialist"},
    "bandcamp": {"class": BandcampSearcher, "free": False, "api": False, "desc": "Artist-direct, lossless"},
}


def get_searchers(sources_filter: str | None, fast_mode: bool) -> tuple[list, list]:
    """Get searchers based on filters."""
    if sources_filter:
        selected = [s.strip().lower() for s in sources_filter.split(",")]
    elif fast_mode:
        # Fast mode: only API-based sources (no web scraping)
        selected = [name for name, info in ALL_SOURCES.items() if info["api"]]
    else:
        selected = list(ALL_SOURCES.keys())

    free_searchers = []
    paid_searchers = []

    for name in selected:
        if name not in ALL_SOURCES:
            console.print(f"[yellow]Warning: Unknown source '{name}', skipping[/yellow]")
            continue
        info = ALL_SOURCES[name]
        max_results = 3 if name == "youtube" else 2
        searcher = info["class"](max_results=max_results)
        if info["free"]:
            free_searchers.append(searcher)
        else:
            paid_searchers.append(searcher)

    return free_searchers, paid_searchers


def print_available_sources() -> None:
    """Print all available sources."""
    table = Table(title="Available Music Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Method")
    table.add_column("Description")

    for name, info in ALL_SOURCES.items():
        source_type = "Free" if info["free"] else "Paid"
        method = "API" if info["api"] else "Web Search"
        table.add_row(name, source_type, method, info["desc"])

    console.print(table)
    console.print("\n[dim]Use --sources=youtube,deezer,spotify to select specific sources[/dim]")
    console.print("[dim]Use --fast to only use API-based sources (faster, no rate limiting)[/dim]")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Search and download music tracks from legal sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli.crawl tracks.txt
  python -m src.cli.crawl tracks.txt --output ~/Music/Stothart
  python -m src.cli.crawl tracks.txt --search-only
  python -m src.cli.crawl --track "Treasure Island Main Title"
        """,
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Path to track list file",
    )
    parser.add_argument(
        "--track",
        "-t",
        type=str,
        help="Search for a single track (format: 'Film - Title' or just 'Title')",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output directory (default: downloads/{composer}/)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["mp3", "flac", "wav", "best"],
        default="mp3",
        help="Audio format (default: mp3)",
    )
    parser.add_argument(
        "--quality",
        "-q",
        choices=["128", "192", "256", "320", "best"],
        default="320",
        help="Audio quality for MP3 (default: 320)",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=Path,
        help="Report output path (default: OUTPUT_DIR/REPORT.md)",
    )
    parser.add_argument(
        "--search-only",
        "-s",
        action="store_true",
        help="Search only, don't download",
    )
    parser.add_argument(
        "--composer",
        default="Herbert Stothart",
        help="Composer name for search queries",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cache and re-search all tracks",
    )
    parser.add_argument(
        "--sources",
        type=str,
        help="Comma-separated list of sources to use (e.g., youtube,deezer,spotify)",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List all available sources and exit",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: only use API-based sources (youtube, archive, deezer, itunes)",
    )

    args = parser.parse_args()

    # List sources and exit if requested
    if args.list_sources:
        print_available_sources()
        sys.exit(0)

    # Validate input
    if not args.input_file and not args.track:
        parser.error("Either input_file or --track is required")

    # Parse tracks
    if args.track:
        track = parse_single_track(args.track)
        if track:
            track.composer = args.composer
            tracks = [track]
        else:
            console.print("[red]Failed to parse track[/red]")
            sys.exit(1)
    else:
        if not args.input_file.exists():
            console.print(f"[red]File not found: {args.input_file}[/red]")
            sys.exit(1)
        tracks = parse_track_list(args.input_file)
        for t in tracks:
            t.composer = args.composer

    if not tracks:
        console.print("[red]No tracks found in input[/red]")
        sys.exit(1)

    console.print(f"[green]Found {len(tracks)} tracks to search[/green]")

    # Setup output directory (use composer name if not specified)
    if args.output is None:
        # Create safe folder name from composer
        safe_composer = args.composer.replace(" ", "_").replace("/", "-")
        args.output = DEFAULT_DOWNLOADS / safe_composer
    args.output.mkdir(parents=True, exist_ok=True)
    console.print(f"[dim]Output: {args.output}[/dim]")

    # Load cache
    cache_path = args.output / ".crawl_cache.json"
    cache = load_cache(cache_path) if not args.no_cache else {}

    # Setup searchers and downloader
    free_searchers, paid_searchers = get_searchers(args.sources, args.fast)

    # Show which sources are being used
    all_sources = [s.name for s in free_searchers + paid_searchers]
    console.print(f"[dim]Using sources: {', '.join(all_sources)}[/dim]")

    downloader = YtDlpDownloader(
        output_dir=args.output,
        audio_format=args.format if args.format != "best" else "mp3",
        audio_quality=args.quality if args.quality != "best" else "0",
    )

    # Process tracks
    results: list[CrawlResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for track in tracks:
            task_desc = f"Searching: {track.film} - {track.cue_title}"
            task = progress.add_task(task_desc, total=None)

            crawl_result = process_track(
                track=track,
                free_searchers=free_searchers,
                paid_searchers=paid_searchers,
                downloader=downloader,
                search_only=args.search_only,
                cache=cache,
            )
            results.append(crawl_result)

            # Update cache
            if crawl_result.downloaded_from:
                cache[track.search_query()] = {
                    "status": "downloaded",
                    "path": str(crawl_result.downloaded_from.local_path),
                }

            progress.remove_task(task)

            # Print result
            status_color = {
                "downloaded": "green",
                "free_available": "cyan",
                "paid_only": "yellow",
                "not_found": "red",
            }[crawl_result.status]
            console.print(
                f"  [{status_color}]{crawl_result.status.upper()}[/{status_color}] "
                f"{track.rank}. {track.film} - \"{track.cue_title}\""
            )

    # Save cache
    save_cache(cache_path, cache)

    # Generate report
    report_path = args.report or (args.output / "REPORT.md")
    generator = ReportGenerator(composer=args.composer)
    generator.generate(results, report_path)
    console.print(f"\n[green]Report saved to: {report_path}[/green]")

    # Print summary
    print_summary(results)


def process_track(
    track: Track,
    free_searchers: list,
    paid_searchers: list,
    downloader: YtDlpDownloader,
    search_only: bool,
    cache: dict,
) -> CrawlResult:
    """Process a single track: search and optionally download."""
    result = CrawlResult(track=track)

    # Check cache
    cache_key = track.search_query()
    if cache_key in cache and cache[cache_key].get("status") == "downloaded":
        cached_path = Path(cache[cache_key]["path"])
        if cached_path.exists():
            result.downloaded_from = SearchResult(
                track=track,
                source="cache",
                url="",
                is_free=True,
                quality="cached",
                downloaded=True,
                local_path=cached_path,
            )
            return result

    # Search free sources first
    free_results: list[SearchResult] = []
    for searcher in free_searchers:
        free_results.extend(searcher.search(track))
        time.sleep(0.3)  # Rate limit: 300ms between searches

    # Search paid sources
    paid_results: list[SearchResult] = []
    for searcher in paid_searchers:
        paid_results.extend(searcher.search(track))
        time.sleep(0.3)  # Rate limit: 300ms between searches

    result.results = free_results + paid_results
    result.free_alternatives = free_results
    result.paid_alternatives = paid_results

    # Try to download from free sources
    if not search_only and free_results:
        for search_result in free_results:
            if search_result.source == "youtube":
                downloaded = downloader.download(search_result)
                if downloaded.downloaded:
                    result.downloaded_from = downloaded
                    break

    # If nothing found
    if not free_results and not paid_results:
        result.not_found = True

    return result


def load_cache(path: Path) -> dict:
    """Load cache from JSON file."""
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_cache(path: Path, cache: dict) -> None:
    """Save cache to JSON file."""
    path.write_text(json.dumps(cache, indent=2))


def print_summary(results: list[CrawlResult]) -> None:
    """Print a summary table."""
    table = Table(title="Crawl Summary")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")

    downloaded = len([r for r in results if r.status == "downloaded"])
    free_available = len([r for r in results if r.status == "free_available"])
    paid_only = len([r for r in results if r.status == "paid_only"])
    not_found = len([r for r in results if r.status == "not_found"])

    table.add_row("Downloaded", str(downloaded), style="green")
    table.add_row("Free Available", str(free_available), style="cyan")
    table.add_row("Paid Only", str(paid_only), style="yellow")
    table.add_row("Not Found", str(not_found), style="red")
    table.add_row("Total", str(len(results)), style="bold")

    console.print()
    console.print(table)


if __name__ == "__main__":
    main()
