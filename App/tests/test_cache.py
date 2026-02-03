"""Tests for soundtracker.cache module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from soundtracker.cache.file_cache import FileCache, TMDBCache, StreamingCache


class TestFileCache:
    """Tests for FileCache class."""

    def test_basic_operations(self):
        """Test basic get/set operations."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            # Set value
            cache["key1"] = "value1"
            assert cache["key1"] == "value1"

            # Get with default
            assert cache.get("nonexistent", "default") == "default"

    def test_persistence(self):
        """Test cache persistence to file."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Write cache
            cache1 = FileCache(cache_path)
            cache1["key1"] = "value1"
            cache1.save()

            # Read cache in new instance
            cache2 = FileCache(cache_path)
            assert cache2["key1"] == "value1"

    def test_auto_save(self):
        """Test auto-save functionality."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path, auto_save=True)

            cache["key1"] = "value1"

            # Check file was written
            assert cache_path.exists()
            data = json.loads(cache_path.read_text())
            assert data["key1"] == "value1"

    def test_contains(self):
        """Test __contains__ method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            assert "key1" in cache
            assert "key2" not in cache

    def test_delete(self):
        """Test __delitem__ method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            del cache["key1"]
            assert "key1" not in cache

    def test_len(self):
        """Test __len__ method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            assert len(cache) == 0
            cache["key1"] = "value1"
            cache["key2"] = "value2"
            assert len(cache) == 2

    def test_keys(self):
        """Test keys method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            cache["key2"] = "value2"

            keys = list(cache.keys())
            assert "key1" in keys
            assert "key2" in keys

    def test_values(self):
        """Test values method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            cache["key2"] = "value2"

            values = list(cache.values())
            assert "value1" in values
            assert "value2" in values

    def test_items(self):
        """Test items method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            items = list(cache.items())
            assert ("key1", "value1") in items

    def test_clear(self):
        """Test clear method."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            cache["key1"] = "value1"
            cache["key2"] = "value2"
            cache.clear()

            assert len(cache) == 0

    def test_corrupted_file(self):
        """Test handling of corrupted cache file."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Write invalid JSON
            cache_path.write_text("not valid json")

            # Should handle gracefully
            cache = FileCache(cache_path)
            assert len(cache) == 0


class TestTMDBCache:
    """Tests for TMDBCache class."""

    def test_movie_operations(self):
        """Test movie get/set operations."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "tmdb_cache.json"
            cache = TMDBCache(cache_path)

            movie_data = {
                "original_title": "Star Wars",
                "title_es": "La Guerra de las Galaxias",
                "poster_path": "/poster.jpg",
            }

            cache.set_movie("Star Wars", 1977, movie_data)
            result = cache.get_movie("Star Wars", 1977)

            assert result is not None
            assert result["original_title"] == "Star Wars"

    def test_movie_not_found(self):
        """Test movie not in cache."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "tmdb_cache.json"
            cache = TMDBCache(cache_path)

            result = cache.get_movie("Nonexistent", 2000)
            assert result is None

    def test_movie_key_format(self):
        """Test movie cache key format."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "tmdb_cache.json"
            cache = TMDBCache(cache_path)

            cache.set_movie("Test", 2000, {"title": "Test"})

            # Key should be "title|year"
            assert "Test|2000" in cache

    def test_movie_without_year(self):
        """Test movie without year."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "tmdb_cache.json"
            cache = TMDBCache(cache_path)

            cache.set_movie("Test", None, {"title": "Test"})
            result = cache.get_movie("Test", None)

            assert result is not None


class TestStreamingCache:
    """Tests for StreamingCache class."""

    def test_signals_operations(self):
        """Test streaming signals get/set operations."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "streaming_cache.json"
            cache = StreamingCache(cache_path)

            signals = {
                "spotify_popularity": 75.0,
                "youtube_views": 1000000,
            }

            cache.set_signals("John Williams", "Star Wars", 1977, signals)
            result = cache.get_signals("John Williams", "Star Wars", 1977)

            assert result is not None
            assert result["spotify_popularity"] == 75.0
            assert result["youtube_views"] == 1000000

    def test_signals_not_found(self):
        """Test signals not in cache."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "streaming_cache.json"
            cache = StreamingCache(cache_path)

            result = cache.get_signals("Unknown", "Unknown", 2000)
            assert result is None

    def test_signals_key_format(self):
        """Test streaming cache key format."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "streaming_cache.json"
            cache = StreamingCache(cache_path)

            cache.set_signals("Composer", "Title", 2000, {"test": True})

            # Key should be "composer|title|year"
            assert "Composer|Title|2000" in cache

    def test_signals_without_year(self):
        """Test signals without year."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "streaming_cache.json"
            cache = StreamingCache(cache_path)

            cache.set_signals("Composer", "Title", None, {"test": True})
            result = cache.get_signals("Composer", "Title", None)

            assert result is not None


class TestCacheThreadSafety:
    """Tests for cache thread safety."""

    def test_concurrent_writes(self):
        """Test concurrent write operations."""
        import threading

        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            def write_values(prefix, count):
                for i in range(count):
                    cache[f"{prefix}_{i}"] = f"value_{i}"

            threads = [
                threading.Thread(target=write_values, args=(f"t{i}", 10))
                for i in range(5)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All values should be present
            assert len(cache) == 50

    def test_concurrent_reads(self):
        """Test concurrent read operations."""
        import threading

        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache = FileCache(cache_path)

            # Pre-populate
            for i in range(100):
                cache[f"key_{i}"] = f"value_{i}"

            results = []

            def read_values():
                for i in range(100):
                    results.append(cache.get(f"key_{i}"))

            threads = [
                threading.Thread(target=read_values)
                for _ in range(5)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All reads should succeed
            assert len(results) == 500
            assert all(r is not None for r in results)
