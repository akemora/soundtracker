"""Cache manager for crawl results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CacheManager:
    """Handle cache persistence for search results."""

    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, dict[str, Any]] = {}

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
