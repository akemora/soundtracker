"""File-based cache implementation for SOUNDTRACKER.

Provides a thread-safe JSON file cache for storing API responses
and other data that should persist between runs.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FileCache:
    """Thread-safe file-based JSON cache.

    Stores key-value pairs in a JSON file with lazy loading and
    automatic persistence. Thread-safe for concurrent access.

    Attributes:
        path: Path to the cache file.
        auto_save: Whether to save automatically on set operations.

    Example:
        cache = FileCache(Path("cache.json"))
        cache.set("key", {"data": "value"})
        value = cache.get("key")
        cache.save()  # Persist to disk
    """

    def __init__(
        self,
        path: Path,
        auto_save: bool = True,
        default_factory: Optional[callable] = None,
    ) -> None:
        """Initialize the file cache.

        Args:
            path: Path to the JSON cache file.
            auto_save: If True, save after each set operation.
            default_factory: Optional callable to generate default values.
        """
        self._path = Path(path)
        self._auto_save = auto_save
        self._default_factory = default_factory
        self._data: dict[str, Any] = {}
        self._loaded = False
        self._dirty = False
        self._lock = threading.RLock()

    @property
    def path(self) -> Path:
        """Return the cache file path."""
        return self._path

    def _ensure_loaded(self) -> None:
        """Ensure cache data is loaded from disk."""
        if not self._loaded:
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load cache data from the JSON file."""
        with self._lock:
            if self._loaded:
                return

            if not self._path.exists():
                self._data = {}
                self._loaded = True
                logger.debug("Cache file not found, starting empty: %s", self._path)
                return

            try:
                content = self._path.read_text(encoding="utf-8")
                self._data = json.loads(content) if content.strip() else {}
                logger.debug(
                    "Loaded %d entries from cache: %s", len(self._data), self._path
                )
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Failed to load cache %s: %s", self._path, e)
                self._data = {}

            self._loaded = True

    def load(self) -> "FileCache":
        """Explicitly load cache from disk.

        Returns:
            Self for method chaining.
        """
        self._load_from_disk()
        return self

    def save(self) -> bool:
        """Save cache data to disk.

        Returns:
            True if save was successful, False otherwise.
        """
        with self._lock:
            if not self._dirty and self._loaded:
                return True

            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                content = json.dumps(self._data, ensure_ascii=False, indent=2)
                self._path.write_text(content, encoding="utf-8")
                self._dirty = False
                logger.debug("Saved %d entries to cache: %s", len(self._data), self._path)
                return True
            except OSError as e:
                logger.error("Failed to save cache %s: %s", self._path, e)
                return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache.

        Args:
            key: The cache key.
            default: Default value if key not found.

        Returns:
            The cached value or default.
        """
        with self._lock:
            self._ensure_loaded()
            value = self._data.get(key)
            if value is not None:
                return value
            if self._default_factory is not None:
                return self._default_factory()
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        with self._lock:
            self._ensure_loaded()
            self._data[key] = value
            self._dirty = True
            if self._auto_save:
                self.save()

    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if key was deleted, False if not found.
        """
        with self._lock:
            self._ensure_loaded()
            if key in self._data:
                del self._data[key]
                self._dirty = True
                if self._auto_save:
                    self.save()
                return True
            return False

    def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key.

        Returns:
            True if key exists, False otherwise.
        """
        with self._lock:
            self._ensure_loaded()
            return key in self._data

    def keys(self) -> list[str]:
        """Get all cache keys.

        Returns:
            List of all keys in the cache.
        """
        with self._lock:
            self._ensure_loaded()
            return list(self._data.keys())

    def values(self) -> list[Any]:
        """Get all cache values.

        Returns:
            List of all values in the cache.
        """
        with self._lock:
            self._ensure_loaded()
            return list(self._data.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all cache items.

        Returns:
            List of (key, value) tuples.
        """
        with self._lock:
            self._ensure_loaded()
            return list(self._data.items())

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._data = {}
            self._dirty = True
            self._loaded = True
            if self._auto_save:
                self.save()

    def update(self, data: dict[str, Any]) -> None:
        """Update cache with multiple key-value pairs.

        Args:
            data: Dictionary of key-value pairs to add.
        """
        with self._lock:
            self._ensure_loaded()
            self._data.update(data)
            self._dirty = True
            if self._auto_save:
                self.save()

    def get_or_set(self, key: str, factory: callable) -> Any:
        """Get a value or set it using a factory function.

        Args:
            key: The cache key.
            factory: Callable to generate the value if not cached.

        Returns:
            The cached or newly generated value.
        """
        with self._lock:
            self._ensure_loaded()
            if key in self._data:
                return self._data[key]

            value = factory()
            self._data[key] = value
            self._dirty = True
            if self._auto_save:
                self.save()
            return value

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        """Support dict-like access."""
        with self._lock:
            self._ensure_loaded()
            return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Support dict-like assignment."""
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """Support dict-like deletion."""
        with self._lock:
            self._ensure_loaded()
            del self._data[key]
            self._dirty = True
            if self._auto_save:
                self.save()

    def __len__(self) -> int:
        """Return number of cached items."""
        with self._lock:
            self._ensure_loaded()
            return len(self._data)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"FileCache(path={self._path}, entries={len(self)})"


class TMDBCache(FileCache):
    """Specialized cache for TMDB API responses.

    Provides convenience methods for common TMDB caching patterns.
    """

    def get_movie(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        """Get cached movie details.

        Args:
            title: Movie title.
            year: Optional release year.

        Returns:
            Cached movie details or None.
        """
        key = f"{title}|{year or ''}"
        return self.get(key)

    def set_movie(
        self, title: str, year: Optional[int], details: Optional[dict]
    ) -> None:
        """Cache movie details.

        Args:
            title: Movie title.
            year: Optional release year.
            details: Movie details to cache (or empty dict for negative cache).
        """
        key = f"{title}|{year or ''}"
        self.set(key, details or {})


class StreamingCache(FileCache):
    """Specialized cache for streaming service data.

    Caches Spotify and YouTube data for films.
    """

    def get_signals(
        self, composer: str, title: str, year: Optional[int] = None
    ) -> Optional[dict]:
        """Get cached streaming signals.

        Args:
            composer: Composer name.
            title: Film title.
            year: Optional release year.

        Returns:
            Cached streaming signals or None.
        """
        key = f"{composer}|{title}|{year or ''}"
        return self.get(key)

    def set_signals(
        self,
        composer: str,
        title: str,
        year: Optional[int],
        signals: dict,
    ) -> None:
        """Cache streaming signals.

        Args:
            composer: Composer name.
            title: Film title.
            year: Optional release year.
            signals: Streaming data to cache.
        """
        key = f"{composer}|{title}|{year or ''}"
        self.set(key, signals)
