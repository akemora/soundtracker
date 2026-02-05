from datetime import datetime, timedelta, timezone

from src.cache.manager import CacheManager, CACHE_STATUSES


def test_cache_set_get(tmp_path) -> None:
    cache_path = tmp_path / ".crawl_cache.json"
    cache = CacheManager(cache_path, ttl_days=7)
    cache.set("query", "downloaded", "/tmp/file.mp3", "http://example.com")
    cache.save()

    reloaded = CacheManager(cache_path, ttl_days=7)
    reloaded.load()
    entry = reloaded.get("query")

    assert entry is not None
    assert entry["status"] == "downloaded"


def test_cache_ttl_expiration(tmp_path) -> None:
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    old_timestamp = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    cache.data["query"] = {
        "status": "downloaded",
        "timestamp": old_timestamp,
        "path": "",
        "url": "",
    }

    assert cache.get("query") is None


def test_cache_statuses_supported(tmp_path) -> None:
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    for status in CACHE_STATUSES:
        cache.set("query", status, None, None)
        assert cache.data["query"]["status"] == status


def test_cache_refresh_like_behavior(tmp_path) -> None:
    cache_path = tmp_path / "cache.json"
    cache = CacheManager(cache_path, ttl_days=0)
    cache.set("query", "downloaded", "/tmp/file.mp3", "http://example.com")

    assert cache.get("query") is None
