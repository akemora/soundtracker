"""Data models for playlist generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PlaylistTrack:
    """Single track entry in a playlist."""

    position: int
    film: str
    film_year: int | None
    track_title: str
    source: str
    url: str
    embed_url: str | None
    is_free: bool
    duration: str | None = None
    thumbnail: str | None = None
    is_original_pick: bool = True
    fallback_reason: str | None = None
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    purchase_links: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert playlist track to JSON-serializable dict."""
        payload: dict[str, Any] = {
            "position": self.position,
            "film": self.film,
            "film_year": self.film_year,
            "track_title": self.track_title,
            "is_original_pick": self.is_original_pick,
            "source": self.source,
            "url": self.url,
            "embed_url": self.embed_url,
            "is_free": self.is_free,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "alternatives": self.alternatives,
        }
        if self.fallback_reason:
            payload["fallback_reason"] = self.fallback_reason
        if self.purchase_links:
            payload["purchase_links"] = self.purchase_links
        return payload


@dataclass
class Playlist:
    """Playlist container with metadata."""

    composer_slug: str
    composer_name: str
    tracks: list[PlaylistTrack]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> dict[str, Any]:
        """Convert playlist to JSON-serializable dict."""
        total_tracks = len(self.tracks)
        free_count = sum(1 for track in self.tracks if track.is_free)
        paid_count = total_tracks - free_count

        return {
            "composer_slug": self.composer_slug,
            "composer_name": self.composer_name,
            "generated_at": self.generated_at,
            "updated_at": self.updated_at,
            "total_tracks": total_tracks,
            "free_count": free_count,
            "paid_count": paid_count,
            "tracks": [track.to_dict() for track in self.tracks],
        }
