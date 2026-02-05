"""YouTube searcher using yt-dlp."""

import json
import subprocess
from typing import Any

from src.core.logger import get_logger
from src.models.track import SearchResult, Track
from src.searchers.base import BaseSearcher

logger = get_logger(__name__)


class YouTubeSearcher(BaseSearcher):
    """Search YouTube for tracks using yt-dlp."""

    name = "youtube"
    is_free = True

    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def search(self, track: Track) -> list[SearchResult]:
        """Search YouTube for the track."""
        query = self.build_query(track)
        results: list[SearchResult] = []

        try:
            # Use yt-dlp to search YouTube
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--flat-playlist",
                "--no-warnings",
                f"ytsearch{self.max_results}:{query}",
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if process.returncode != 0:
                return results

            # Parse each JSON line (one per result)
            for line in process.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    result = self._parse_result(track, data)
                    if result:
                        results.append(result)
                except json.JSONDecodeError:
                    continue

        except subprocess.TimeoutExpired as exc:
            logger.error("YouTube search timed out for query '%s': %s", query, exc)
        except FileNotFoundError as exc:
            logger.error("yt-dlp not installed for YouTube search '%s': %s", query, exc)

        return results

    def _parse_result(self, track: Track, data: dict[str, Any]) -> SearchResult | None:
        """Parse a yt-dlp search result."""
        video_id = data.get("id")
        if not video_id:
            return None

        title = data.get("title", "Unknown")
        duration = data.get("duration")
        duration_str = self._format_duration(duration) if duration else None

        return SearchResult(
            track=track,
            source=self.name,
            url=f"https://www.youtube.com/watch?v={video_id}",
            is_free=True,
            quality="varies",  # Will be determined on download
            duration=duration_str,
            title=title,
        )

    def _format_duration(self, seconds: int | float) -> str:
        """Format duration in seconds to MM:SS or HH:MM:SS."""
        seconds = int(seconds)
        if seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
