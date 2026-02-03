"""yt-dlp wrapper for audio extraction."""

import subprocess
from pathlib import Path

from src.models.track import SearchResult


class YtDlpDownloader:
    """Download audio from YouTube using yt-dlp."""

    def __init__(
        self,
        output_dir: Path,
        audio_format: str = "mp3",
        audio_quality: str = "320",
    ):
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.audio_quality = audio_quality

    def download(self, result: SearchResult) -> SearchResult:
        """
        Download audio from a search result.
        Returns the updated SearchResult with download status.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        filename_base = result.track.filename_base()
        output_template = self.output_dir / f"{filename_base}.%(ext)s"

        cmd = [
            "yt-dlp",
            "--extract-audio",
            f"--audio-format={self.audio_format}",
            f"--audio-quality={self.audio_quality}K" if self.audio_format == "mp3" else "--audio-quality=0",
            "--no-playlist",
            "--no-warnings",
            "-o",
            str(output_template),
            result.url,
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if process.returncode == 0:
                # Find the downloaded file
                output_path = self._find_output_file(filename_base)
                if output_path:
                    result.downloaded = True
                    result.local_path = output_path
                    result.quality = f"{self.audio_quality}kbps {self.audio_format.upper()}"
                else:
                    result.error = "Download completed but file not found"
            else:
                result.error = process.stderr or "Download failed"

        except subprocess.TimeoutExpired:
            result.error = "Download timed out"
        except FileNotFoundError:
            result.error = "yt-dlp not installed"

        return result

    def _find_output_file(self, filename_base: str) -> Path | None:
        """Find the downloaded file by base name."""
        for ext in [self.audio_format, "m4a", "webm", "opus", "mp3", "wav", "flac"]:
            path = self.output_dir / f"{filename_base}.{ext}"
            if path.exists():
                return path
        return None

    def get_info(self, url: str) -> dict | None:
        """Get video info without downloading."""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            url,
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if process.returncode == 0:
                import json
                return json.loads(process.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
