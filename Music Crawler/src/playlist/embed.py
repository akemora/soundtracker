"""Embed URL resolver for playlist playback."""

from __future__ import annotations

import re
import urllib.parse


class EmbedResolver:
    """Resolve embeddable URLs for supported sources."""

    @staticmethod
    def resolve(source: str, url: str) -> str | None:
        """Convert a source URL into an embeddable URL."""
        if not url:
            return None

        source_key = source.lower()
        if source_key == "youtube":
            return EmbedResolver._youtube_embed(url)
        if source_key == "soundcloud":
            return EmbedResolver._soundcloud_embed(url)
        if source_key == "spotify":
            return EmbedResolver._spotify_embed(url)
        return None

    @staticmethod
    def _youtube_embed(url: str) -> str | None:
        """Convert YouTube URL to embed URL."""
        video_id = EmbedResolver._extract_youtube_id(url)
        if not video_id:
            return None
        return f"https://www.youtube.com/embed/{video_id}"

    @staticmethod
    def _soundcloud_embed(url: str) -> str | None:
        """Convert SoundCloud URL to embed player URL."""
        if not url:
            return None
        encoded = urllib.parse.quote(url, safe="")
        return f"https://w.soundcloud.com/player/?url={encoded}&auto_play=false"

    @staticmethod
    def _spotify_embed(url: str) -> str | None:
        """Convert Spotify URL to embed URL."""
        if "/track/" not in url:
            return None
        return url.replace("/track/", "/embed/track/")

    @staticmethod
    def _extract_youtube_id(url: str) -> str | None:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc in {"youtu.be"}:
            return parsed.path.lstrip("/") or None
        if "youtube.com" in parsed.netloc:
            query = urllib.parse.parse_qs(parsed.query)
            if "v" in query and query["v"]:
                return query["v"][0]
            match = re.search(r"/embed/([^/?]+)", parsed.path)
            if match:
                return match.group(1)
        return None
