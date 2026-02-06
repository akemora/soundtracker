"""Tests for CLI crawl module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from src.cache.manager import CacheManager
from src.cli import crawl as crawl_module
from src.models.track import CrawlResult, SearchResult, Track


class DummySearcher:
    name = "youtube"

    def __init__(self, results):
        self._results = results

    def search(self, track):
        return self._results


class DummyDownloader:
    def __init__(self, *args, **kwargs):
        pass

    def download(self, result):
        result.downloaded = True
        return result


def _track():
    return Track(rank=1, film="Film", cue_title="Cue", description="desc")


def test_get_searchers_unknown(monkeypatch):
    dummy_provider = object()
    monkeypatch.setattr(crawl_module, "_build_web_provider", lambda: dummy_provider)
    free, paid = crawl_module.get_searchers("unknown", fast_mode=False)
    assert free == []
    assert paid == []


def test_get_searchers_fast_mode(monkeypatch):
    dummy_provider = object()
    monkeypatch.setattr(crawl_module, "_build_web_provider", lambda: dummy_provider)
    free, paid = crawl_module.get_searchers(None, fast_mode=True)
    assert free


def test_get_searchers_default(monkeypatch):
    dummy_provider = object()
    monkeypatch.setattr(crawl_module, "_build_web_provider", lambda: dummy_provider)
    free, paid = crawl_module.get_searchers(None, fast_mode=False)
    assert free or paid


def test_print_available_sources(caplog):
    crawl_module.print_available_sources()


def test_build_web_provider_prefers_perplexity(monkeypatch):
    class DummyProvider:
        api_key = "key"

    monkeypatch.setattr(crawl_module, "PerplexityProvider", lambda: DummyProvider())
    dummy_chrome = object()
    monkeypatch.setattr(crawl_module, "ChromeProvider", lambda: dummy_chrome)
    provider = crawl_module._build_web_provider()
    assert provider is not dummy_chrome


def test_build_web_provider_chrome_fallback(monkeypatch):
    class DummyProvider:
        api_key = None

    monkeypatch.setattr(crawl_module, "PerplexityProvider", lambda: DummyProvider())
    dummy_chrome = object()
    monkeypatch.setattr(crawl_module, "ChromeProvider", lambda: dummy_chrome)
    provider = crawl_module._build_web_provider()
    assert provider is dummy_chrome


def test_run_crawl_list_sources(monkeypatch):
    args = argparse.Namespace(
        list_sources=True,
        input_file=None,
        track=None,
        output=None,
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "print_available_sources", lambda: None)
    with pytest.raises(SystemExit):
        crawl_module.run_crawl(args)


def test_run_crawl_no_input():
    args = argparse.Namespace(
        list_sources=False,
        input_file=None,
        track=None,
        output=None,
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    with pytest.raises(SystemExit):
        crawl_module.run_crawl(args)


def test_run_crawl_track_parse_fail(monkeypatch):
    args = argparse.Namespace(
        list_sources=False,
        input_file=None,
        track="bad",
        output=None,
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "parse_single_track", lambda t: None)
    with pytest.raises(SystemExit):
        crawl_module.run_crawl(args)


def test_run_crawl_single_track_success(tmp_path, monkeypatch):
    args = argparse.Namespace(
        list_sources=False,
        input_file=None,
        track="Film - Title",
        output=tmp_path / "out",
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=True,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "parse_single_track", lambda t: Track(rank=1, film="Film", cue_title="Title", description=""))
    monkeypatch.setattr(crawl_module, "get_searchers", lambda *a, **k: ([], []))
    monkeypatch.setattr(crawl_module, "YtDlpDownloader", DummyDownloader)
    monkeypatch.setattr(crawl_module, "process_track", lambda **k: CrawlResult(track=_track()))
    monkeypatch.setattr(crawl_module, "ReportGenerator", lambda composer: type("G", (), {"generate": lambda self, r, p: None})())
    monkeypatch.setattr(crawl_module, "write_results_json", lambda *a, **k: None)
    monkeypatch.setattr(crawl_module, "print_summary", lambda *a, **k: None)
    crawl_module.run_crawl(args)
    assert args.output.exists()


def test_run_crawl_file_not_found(tmp_path):
    args = argparse.Namespace(
        list_sources=False,
        input_file=tmp_path / "missing.txt",
        track=None,
        output=None,
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    with pytest.raises(SystemExit):
        crawl_module.run_crawl(args)


def test_run_crawl_no_tracks(tmp_path, monkeypatch):
    file_path = tmp_path / "tracks.txt"
    file_path.write_text("", encoding="utf-8")
    args = argparse.Namespace(
        list_sources=False,
        input_file=file_path,
        track=None,
        output=None,
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "parse_track_list", lambda p: [])
    with pytest.raises(SystemExit):
        crawl_module.run_crawl(args)


def test_run_crawl_success(tmp_path, monkeypatch):
    file_path = tmp_path / "tracks.txt"
    file_path.write_text("1\nFilm\nTitle\n", encoding="utf-8")
    args = argparse.Namespace(
        list_sources=False,
        input_file=file_path,
        track=None,
        output=None,
        format="best",
        quality="best",
        report=None,
        json=None,
        search_only=False,
        composer="Composer",
        no_cache=True,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "parse_track_list", lambda p: [_track()])
    monkeypatch.setattr(crawl_module, "get_searchers", lambda *a, **k: ([], []))
    monkeypatch.setattr(crawl_module, "YtDlpDownloader", DummyDownloader)
    def fake_process_track(**k):
        result = CrawlResult(track=_track())
        result.downloaded_from = SearchResult(track=_track(), source="youtube", url="u", is_free=True, downloaded=True, local_path=tmp_path / "f.mp3")
        return result

    monkeypatch.setattr(crawl_module, "process_track", fake_process_track)
    monkeypatch.setattr(crawl_module, "ReportGenerator", lambda composer: type("G", (), {"generate": lambda self, r, p: None})())
    monkeypatch.setattr(crawl_module, "write_results_json", lambda *a, **k: None)
    monkeypatch.setattr(crawl_module, "print_summary", lambda *a, **k: None)
    monkeypatch.setattr(crawl_module, "DEFAULT_DOWNLOADS", tmp_path / "downloads")
    crawl_module.run_crawl(args)
    assert (tmp_path / "downloads" / "Composer").exists()


def test_run_crawl_with_cache_load(tmp_path, monkeypatch):
    file_path = tmp_path / "tracks.txt"
    file_path.write_text("1\nFilm\nTitle\n", encoding="utf-8")
    args = argparse.Namespace(
        list_sources=False,
        input_file=file_path,
        track=None,
        output=tmp_path / "out",
        format="mp3",
        quality="320",
        report=None,
        json=None,
        search_only=True,
        composer="Composer",
        no_cache=False,
        refresh=False,
        sources=None,
        fast=False,
    )
    monkeypatch.setattr(crawl_module, "parse_track_list", lambda p: [_track()])
    monkeypatch.setattr(crawl_module, "get_searchers", lambda *a, **k: ([], []))
    monkeypatch.setattr(crawl_module, "YtDlpDownloader", DummyDownloader)
    monkeypatch.setattr(crawl_module, "process_track", lambda **k: CrawlResult(track=_track()))
    monkeypatch.setattr(crawl_module, "ReportGenerator", lambda composer: type("G", (), {"generate": lambda self, r, p: None})())
    monkeypatch.setattr(crawl_module, "write_results_json", lambda *a, **k: None)
    monkeypatch.setattr(crawl_module, "print_summary", lambda *a, **k: None)
    crawl_module.run_crawl(args)


def test_run_playlist(tmp_path, monkeypatch):
    args = argparse.Namespace(composer="composer", db_path=tmp_path / "db.sqlite", output=tmp_path / "out")
    monkeypatch.setattr(
        crawl_module,
        "PlaylistGenerator",
        lambda composer_slug, db_path: type(
            "G",
            (),
            {
                "generate": lambda self: type("P", (), {"to_json": lambda self: {"x": 1}})(),
                "close": lambda self: None,
            },
        )(),
    )
    crawl_module.run_playlist(args)
    assert (tmp_path / "out" / "playlist.json").exists()


def test_process_track_cache_hit(tmp_path):
    track = _track()
    cache = CacheManager(tmp_path / "cache.json", ttl_days=1)
    cached_file = tmp_path / "file.mp3"
    cached_file.write_text("x", encoding="utf-8")
    cache.data[track.search_query()] = {
        "status": "downloaded",
        "timestamp": "2099-01-01T00:00:00+00:00",
        "path": str(cached_file),
        "url": "",
    }
    result = crawl_module.process_track(
        track=track,
        free_searchers=[],
        paid_searchers=[],
        downloader=DummyDownloader(),
        search_only=False,
        cache_manager=cache,
    )
    assert result.downloaded_from is not None


def test_process_track_search_and_download(monkeypatch, tmp_path):
    track = _track()
    free = SearchResult(track=track, source="youtube", url="u", is_free=True)
    paid = SearchResult(track=track, source="spotify", url="u2", is_free=False)
    result = crawl_module.process_track(
        track=track,
        free_searchers=[DummySearcher([free])],
        paid_searchers=[DummySearcher([paid])],
        downloader=DummyDownloader(),
        search_only=False,
        cache_manager=CacheManager(tmp_path / "cache.json", ttl_days=1),
    )
    assert result.downloaded_from is not None


def test_process_track_not_found(tmp_path):
    track = _track()
    result = crawl_module.process_track(
        track=track,
        free_searchers=[],
        paid_searchers=[],
        downloader=DummyDownloader(),
        search_only=True,
        cache_manager=CacheManager(tmp_path / "cache.json", ttl_days=1),
    )
    assert result.not_found is True


def test_serializers_and_summary(tmp_path, caplog):
    track = _track()
    result = CrawlResult(track=track)
    crawl_module.print_summary([result])
    data = crawl_module._serialize_crawl_result(result)
    assert data["status"] == "not_found"
    result.downloaded_from = SearchResult(track=track, source="youtube", url="u", is_free=True)
    serialized = crawl_module._serialize_search_result(result.downloaded_from)
    assert serialized["source"] == "youtube"

    output_path = tmp_path / "results.json"
    crawl_module.write_results_json([result], output_path, "Composer")
    payload = json.loads(output_path.read_text())
    assert payload["composer"] == "Composer"


def test_main_entrypoints(monkeypatch):
    monkeypatch.setattr(crawl_module, "run_playlist", lambda args: None)
    monkeypatch.setattr(crawl_module, "run_crawl", lambda args: None)
    monkeypatch.setattr(crawl_module, "configure_logging", lambda *a, **k: None)

    monkeypatch.setattr(crawl_module.sys, "argv", ["crawl.py", "playlist", "--composer", "x"])
    crawl_module.main()

    monkeypatch.setattr(crawl_module.sys, "argv", ["crawl.py", "tracks.txt"])
    crawl_module.main()

    monkeypatch.setattr(crawl_module.sys, "argv", ["crawl.py"])
    with pytest.raises(SystemExit):
        crawl_module.main()


def test_module_main_executes(monkeypatch):
    import runpy
    import sys

    monkeypatch.setattr(crawl_module, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(crawl_module.sys, "argv", ["crawl.py", "crawl", "--list-sources"])
    sys.modules.pop("src.cli.crawl", None)
    with pytest.raises(SystemExit):
        runpy.run_module("src.cli.crawl", run_name="__main__")
