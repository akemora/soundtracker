"""Cache manager for crawl results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict


class CacheEntry(TypedDict):
    status: str
    timestamp: str
    path: str
    url: str


CACHE_STATUSES = {
    "downloaded",
    "free_available",
    "paid_only",
    "not_found",
    "error",
}


DEFAULT_CACHE_TTL_DAYS = 7


def _current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class CacheManager:
    """Handle cache persistence for search results."""

    def __init__(self, path: Path, ttl_days: int = DEFAULT_CACHE_TTL_DAYS):
        self.path = path
        self.ttl_days = ttl_days
        self.data: dict[str, CacheEntry] = {}

    def load(self) -> None:
        """Load cache data from disk."""
        if not self.path.exists():
            self.data = {}
            return
        try:
            self.data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            self.data = {}

    def save(self) -> None:
        """Persist cache data to disk."""
        self.path.write_text(json.dumps(self.data, indent=2))

    def is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired based on its timestamp."""
        timestamp = entry.get("timestamp")
        if not timestamp:
            return True
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError:
            return True
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - parsed
        return age.total_seconds() > self.ttl_days * 86400

    def get(self, query: str) -> CacheEntry | None:
        """Get a cache entry if present and not expired."""
        entry = self.data.get(query)
        if not entry:
            return None
        if self.is_expired(entry):
            self.data.pop(query, None)
            return None
        return entry

    def set(self, query: str, status: str, path: str | Path | None, url: str | None) -> None:
        """Set a cache entry."""
        if status not in CACHE_STATUSES:
            raise ValueError(f"Unsupported cache status: {status}")
        self.data[query] = {
            "status": status,
            "timestamp": _current_timestamp(),
            "path": str(path) if path else "",
            "url": url or "",
        }
