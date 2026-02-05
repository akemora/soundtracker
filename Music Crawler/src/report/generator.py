"""Markdown report generator."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.models.track import CrawlResult


class ReportGenerator:
    """Generate Markdown reports from crawl results."""

    # Source descriptions for the report
    SOURCE_INFO = {
        "youtube": ("YouTube", "Free (video extraction)"),
        "archive": ("Internet Archive", "Free (public domain)"),
        "soundcloud": ("SoundCloud", "Free (some tracks)"),
        "jamendo": ("Jamendo", "Free (Creative Commons)"),
        "fma": ("Free Music Archive", "Free (Creative Commons)"),
        "musopen": ("Musopen", "Free (public domain classical)"),
        "imslp": ("IMSLP", "Free (public domain scores/recordings)"),
        "spotify": ("Spotify", "Subscription ($10.99/mo)"),
        "itunes": ("iTunes/Apple Music", "Purchase ($0.99-1.29/track)"),
        "deezer": ("Deezer", "Subscription (€10.99/mo) - Hi-Fi available"),
        "amazon": ("Amazon Music", "Subscription ($9.99/mo) - HD/Ultra HD"),
        "tidal": ("Tidal", "Subscription ($10.99/mo) - MQA Hi-Res"),
        "qobuz": ("Qobuz", "Subscription (€12.99/mo) - Hi-Res specialist"),
        "bandcamp": ("Bandcamp", "Purchase (artist-direct, lossless)"),
    }

    def __init__(self, composer: str = "Herbert Stothart"):
        self.composer = composer

    def generate(self, results: list[CrawlResult], output_path: Path) -> None:
        """Generate a Markdown report from crawl results."""
        report = self._build_report(results)
        output_path.write_text(report, encoding="utf-8")

    def _build_report(self, results: list[CrawlResult]) -> str:
        """Build the complete report string."""
        lines: list[str] = []

        # Header
        lines.append(f"# Music Crawl Report - {self.composer}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # Summary
        downloaded = [r for r in results if r.status == "downloaded"]
        free_available = [r for r in results if r.status == "free_available"]
        paid_only = [r for r in results if r.status == "paid_only"]
        not_found = [r for r in results if r.status == "not_found"]

        lines.append("## Summary")
        lines.append(f"- Total tracks: {len(results)}")
        lines.append(f"- Downloaded: {len(downloaded)}")
        lines.append(f"- Free available: {len(free_available)}")
        lines.append(f"- Paid only: {len(paid_only)}")
        lines.append(f"- Not found: {len(not_found)}")
        lines.append("")

        # Sources breakdown
        lines.extend(self._format_sources_summary(results))
        lines.append("")

        # Downloaded tracks
        if downloaded:
            lines.append("## Downloaded Tracks")
            lines.append("")
            for result in downloaded:
                lines.extend(self._format_downloaded(result))
                lines.append("")

        # Free sources available (not downloaded - search-only mode)
        if free_available:
            lines.append("## Available on Free Sources")
            lines.append("")
            for result in free_available:
                lines.extend(self._format_free_available(result))
                lines.append("")

        # Paid alternatives
        if paid_only:
            lines.append("## Available on Paid Services Only")
            lines.append("")
            for result in paid_only:
                lines.extend(self._format_paid_only(result))
                lines.append("")

        # Not found
        lines.append("## Not Found")
        if not_found:
            for result in not_found:
                lines.append(f"- {result.track.rank}. {result.track.film} - \"{result.track.cue_title}\"")
        else:
            lines.append("- (none)")
        lines.append("")

        return "\n".join(lines)

    def _format_downloaded(self, result: CrawlResult) -> list[str]:
        """Format a downloaded track section."""
        lines: list[str] = []
        track = result.track
        dl = result.downloaded_from

        lines.append(f"### {track.rank}. {track.film} - \"{track.cue_title}\"")
        if track.description:
            lines.append(f"*{track.description}*")
        lines.append("")

        if dl:
            lines.append(f"- **Source:** {dl.source.capitalize()}")
            lines.append(f"- **Quality:** {dl.quality}")
            if dl.local_path:
                lines.append(f"- **File:** `{dl.local_path.name}`")
            lines.append(f"- **URL:** {dl.url}")

        # Also show paid alternatives if any
        if result.paid_alternatives:
            lines.append("")
            lines.append("**Also available on:**")
            for alt in result.paid_alternatives[:3]:
                lines.append(f"- [{alt.source.capitalize()}]({alt.url})")

        return lines

    def _format_sources_summary(self, results: list[CrawlResult]) -> list[str]:
        """Generate a summary of sources found across all tracks."""
        lines: list[str] = []
        source_counts: dict[str, int] = defaultdict(int)

        for result in results:
            free_alternatives = result.free_alternatives
            if result.downloaded_from:
                free_alternatives = [
                    alt
                    for alt in free_alternatives
                    if not (
                        alt.source == result.downloaded_from.source
                        and alt.url == result.downloaded_from.url
                    )
                ]
            for alt in free_alternatives + result.paid_alternatives:
                source_counts[alt.source] += 1
            if result.downloaded_from:
                source_counts[result.downloaded_from.source] += 1

        if source_counts:
            lines.append("### Sources Found")
            lines.append("")
            lines.append("| Source | Results | Type |")
            lines.append("|--------|---------|------|")

            # Sort by count descending
            for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
                info = self.SOURCE_INFO.get(source, (source.capitalize(), "Unknown"))
                lines.append(f"| {info[0]} | {count} | {info[1]} |")

        return lines

    def _format_free_available(self, result: CrawlResult) -> list[str]:
        """Format a free-available track section (search-only mode)."""
        lines: list[str] = []
        track = result.track

        lines.append(f"### {track.rank}. {track.film} - \"{track.cue_title}\"")
        if track.description:
            lines.append(f"*{track.description}*")
        lines.append("")

        # Group free alternatives by source
        by_source: dict[str, list] = defaultdict(list)
        for alt in result.free_alternatives:
            by_source[alt.source].append(alt)

        lines.append("**Free sources:**")
        for source, alts in by_source.items():
            source_name = self.SOURCE_INFO.get(source, (source.capitalize(),))[0]
            for alt in alts[:2]:  # Max 2 per source
                duration_str = f" ({alt.duration})" if alt.duration else ""
                lines.append(f"- **{source_name}:** [{alt.title or 'Link'}]({alt.url}){duration_str}")

        # Also show paid alternatives if any
        if result.paid_alternatives:
            lines.append("")
            lines.append("**Paid alternatives:**")
            by_source_paid: dict[str, list] = defaultdict(list)
            for alt in result.paid_alternatives:
                by_source_paid[alt.source].append(alt)

            for source, alts in by_source_paid.items():
                source_name = self.SOURCE_INFO.get(source, (source.capitalize(),))[0]
                alt = alts[0]  # Just first result per paid source
                lines.append(f"- **{source_name}:** [{alt.title or 'Link'}]({alt.url})")

        return lines

    def _format_paid_only(self, result: CrawlResult) -> list[str]:
        """Format a paid-only track section."""
        lines: list[str] = []
        track = result.track

        lines.append(f"### {track.rank}. {track.film} - \"{track.cue_title}\"")
        if track.description:
            lines.append(f"*{track.description}*")
        lines.append("")

        # Group by source
        by_source: dict[str, list] = defaultdict(list)
        for alt in result.paid_alternatives:
            by_source[alt.source].append(alt)

        for source, alts in by_source.items():
            source_name = self.SOURCE_INFO.get(source, (source.capitalize(),))[0]
            info = self.SOURCE_INFO.get(source, ("", ""))[1]
            for alt in alts[:2]:  # Max 2 per source
                lines.append(f"- **{source_name}** ({info}): [{alt.title or 'Link'}]({alt.url})")

        return lines
