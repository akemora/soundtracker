"""Tests for cache manager."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.cache.manager import CacheManager, CACHE_STATUSES


def test_cache_manager_load_missing(tmp_path):
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    cache.load()
    assert cache.data == {}


def test_cache_manager_load_invalid(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("not json", encoding="utf-8")
    cache = CacheManager(path, ttl_days=1)
    cache.load()
    assert cache.data == {}


def test_cache_manager_save_and_get(tmp_path):
    path = tmp_path / "cache.json"
    cache = CacheManager(path, ttl_days=1)
    cache.set("q", "downloaded", path="file", url="u")
    cache.save()
    cache2 = CacheManager(path, ttl_days=1)
    cache2.load()
    assert cache2.get("q")["status"] == "downloaded"


def test_cache_manager_is_expired(tmp_path):
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    entry = {"status": "downloaded", "timestamp": "", "path": "", "url": ""}
    assert cache.is_expired(entry) is True

    entry["timestamp"] = "invalid"
    assert cache.is_expired(entry) is True

    naive = datetime.now().isoformat()
    entry["timestamp"] = naive
    assert cache.is_expired(entry) is False

    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    entry["timestamp"] = old
    assert cache.is_expired(entry) is True


def test_cache_manager_get_expired(tmp_path):
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    cache.data["q"] = {"status": "downloaded", "timestamp": old, "path": "", "url": ""}
    assert cache.get("q") is None


def test_cache_manager_set_invalid_status(tmp_path):
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    with pytest.raises(ValueError):
        cache.set("q", "invalid", path=None, url=None)


def test_cache_statuses_constant():
    assert "downloaded" in CACHE_STATUSES
