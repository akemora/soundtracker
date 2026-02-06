"""Tests for soundtracker.pipeline."""

from pathlib import Path

import pytest

from soundtracker.models import ComposerInfo, ExternalSource, Film
from soundtracker.config import settings
from soundtracker.pipeline import (
    CitationManager,
    ComposerPipeline,
    _parse_master_list,
    main,
    process_composers_from_list,
)
from soundtracker.services.research import ResearchProfile, ResearchSection


def test_citation_manager_annotations():
    """Test citation markers and export ordering."""
    manager = CitationManager()
    text = manager.annotate("Bio", ["https://a.com", "https://b.com"])
    assert "[^1]" in text and "[^2]" in text

    exported = manager.export()
    assert exported[0][0] == "[^1]"
    assert exported[1][0] == "[^2]"

    assert manager.annotate("", ["https://a.com"]) == ""
    assert manager.annotate("Bio", []) == "Bio"


def test_parse_master_list_missing(tmp_path):
    """Test parsing missing master list file."""
    missing = tmp_path / "missing.md"
    assert _parse_master_list(missing) == []


def test_parse_master_list_valid(tmp_path):
    """Test parsing master list entries."""
    content = "\n".join(
        [
            "Not a table row",
            "| No. | Name |",
            "| --- | --- |",
            "|||",
            "| X | Not a Number |",
            "| 1 | Composer One |",
            "| 2 | Composer Two |",
        ]
    )
    path = tmp_path / "list.md"
    path.write_text(content, encoding="utf-8")

    result = _parse_master_list(path)
    assert result == [(1, "Composer One"), (2, "Composer Two")]


def test_process_composer_minimal(tmp_path, monkeypatch):
    """Test pipeline process_composer with mocked services."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)

    monkeypatch.setattr(pipeline.biography_service, "get_biography", lambda name: "Bio")
    monkeypatch.setattr(pipeline.biography_service, "get_musical_style", lambda name: "Style")
    monkeypatch.setattr(pipeline.biography_service, "get_anecdotes", lambda name: "Facts")
    monkeypatch.setattr(pipeline.filmography_service, "get_complete_filmography", lambda *a, **k: [])
    monkeypatch.setattr(pipeline.filmography_service, "get_tv_credits", lambda name: [])
    monkeypatch.setattr(pipeline.filmography_service, "get_video_game_credits", lambda name: [])
    monkeypatch.setattr(pipeline.awards_service, "get_awards", lambda name: [])
    monkeypatch.setattr(pipeline.top10_service, "select_top_10", lambda *a, **k: [])
    monkeypatch.setattr(pipeline.top10_service, "get_web_rankings", lambda name: {})
    pipeline.research_service.api_key = None

    info = pipeline.process_composer("Test Composer", index=1)
    assert info.name == "Test Composer"
    assert (tmp_path / "001_test_composer.md").exists()


def test_process_composer_with_posters(tmp_path, monkeypatch):
    """Test process_composer executes poster branch."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=True)

    monkeypatch.setattr(pipeline.biography_service, "get_biography", lambda name: "Bio")
    monkeypatch.setattr(pipeline.biography_service, "get_musical_style", lambda name: "Style")
    monkeypatch.setattr(pipeline.biography_service, "get_anecdotes", lambda name: "Facts")
    monkeypatch.setattr(pipeline.filmography_service, "get_complete_filmography", lambda *a, **k: [])
    monkeypatch.setattr(pipeline.filmography_service, "get_tv_credits", lambda name: [])
    monkeypatch.setattr(pipeline.filmography_service, "get_video_game_credits", lambda name: [])
    monkeypatch.setattr(pipeline.awards_service, "get_awards", lambda name: [])
    monkeypatch.setattr(pipeline.top10_service, "select_top_10", lambda *a, **k: [])
    monkeypatch.setattr(pipeline.top10_service, "get_web_rankings", lambda name: {})
    pipeline.research_service.api_key = None

    calls = {"count": 0}

    def fake_download_posters(*args, **kwargs):
        calls["count"] += 1

    monkeypatch.setattr(pipeline.poster_service, "download_posters", fake_download_posters)

    info = pipeline.process_composer("Poster Composer", index=2)
    assert info.name == "Poster Composer"
    assert calls["count"] >= 1


def test_apply_deep_research_adds_citations(tmp_path, monkeypatch):
    """Test deep research enrichment."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    profile = ResearchProfile(
        biography=ResearchSection(text="Bio", citations=["https://a.com"]),
        style=ResearchSection(text="Style", citations=["https://b.com"]),
        facts=ResearchSection(text="Facts", citations=["https://c.com"]),
    )
    pipeline.research_service.api_key = "test-key"
    original_flag = settings.deep_research_enabled
    settings.deep_research_enabled = True
    monkeypatch.setattr(pipeline.research_service, "get_profile", lambda name: profile)
    try:
        info = ComposerInfo(name="Test")
        pipeline._apply_deep_research(info)

        assert "[^1]" in (info.biography or "")
        assert len(info.external_sources) == 3
        assert info.external_sources[0].domain == "citation"
    finally:
        settings.deep_research_enabled = original_flag


def test_apply_deep_research_no_profile(tmp_path, monkeypatch):
    """Test deep research returns when no profile."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    pipeline.research_service.api_key = "test-key"
    original_flag = settings.deep_research_enabled
    settings.deep_research_enabled = True
    monkeypatch.setattr(pipeline.research_service, "get_profile", lambda name: None)
    try:
        info = ComposerInfo(name="Test")
        pipeline._apply_deep_research(info)
    finally:
        settings.deep_research_enabled = original_flag


def test_apply_deep_research_skips_empty_sections(tmp_path, monkeypatch):
    """Test deep research skips empty section text."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    profile = ResearchProfile(
        biography=ResearchSection(text="", citations=["https://a.com"]),
        style=ResearchSection(text="", citations=["https://b.com"]),
        facts=ResearchSection(text="", citations=["https://c.com"]),
    )
    pipeline.research_service.api_key = "test-key"
    original_flag = settings.deep_research_enabled
    settings.deep_research_enabled = True
    monkeypatch.setattr(pipeline.research_service, "get_profile", lambda name: profile)
    try:
        info = ComposerInfo(name="Test")
        pipeline._apply_deep_research(info)
        assert info.external_sources == []
    finally:
        settings.deep_research_enabled = original_flag


def test_download_posters_branches(tmp_path, monkeypatch):
    """Test download posters branch for top10 and filmography."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=True)
    film = Film(title="Film A")
    info = ComposerInfo(name="Test", top_10=[film], filmography=[film], image_url="https://x.com/a.jpg")

    calls = {"count": 0}

    def fake_download_posters(*args, **kwargs):
        calls["count"] += 1

    def fake_download_image(url, path):
        path.write_text("img")
        return str(path)

    monkeypatch.setattr(pipeline.poster_service, "download_posters", fake_download_posters)
    monkeypatch.setattr(pipeline.poster_service, "_download_image", fake_download_image)

    pipeline._download_posters(info, tmp_path)
    assert calls["count"] >= 1
    assert info.image_local is not None


def test_download_posters_skips_filmography_when_limit_10(tmp_path, monkeypatch):
    """Test download posters skips filmography when limit <= 10."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=True)
    film = Film(title="Film A")
    info = ComposerInfo(name="Test", top_10=[film], filmography=[film])
    calls = {"count": 0}

    def fake_download_posters(*args, **kwargs):
        calls["count"] += 1

    monkeypatch.setattr(pipeline.poster_service, "download_posters", fake_download_posters)
    original_limit = settings.poster_limit
    settings.poster_limit = 10
    try:
        pipeline._download_posters(info, tmp_path)
    finally:
        settings.poster_limit = original_limit

    assert calls["count"] == 1


def test_download_posters_image_download_failure(tmp_path, monkeypatch):
    """Test download posters keeps image_local when download fails."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=True)
    film = Film(title="Film A")
    info = ComposerInfo(name="Test", top_10=[film], image_url="https://x.com/a.jpg")

    monkeypatch.setattr(pipeline.poster_service, "download_posters", lambda *a, **k: None)
    monkeypatch.setattr(pipeline.poster_service, "_download_image", lambda *_a, **_k: None)

    pipeline._download_posters(info, tmp_path)
    assert info.image_local is None


def test_collect_biography_dict_and_tmdb_wikidata(tmp_path, monkeypatch):
    """Test biography collection with dict data and external ids."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    original_tmdb_key = settings.tmdb_api_key
    settings.tmdb_api_key = "test-key"

    monkeypatch.setattr(
        pipeline.biography_service,
        "get_biography",
        lambda name: {
            "biography": "Bio",
            "style": "Style",
            "anecdotes": "Facts",
            "image_url": None,
        },
    )
    monkeypatch.setattr(pipeline.tmdb, "search_person", lambda name: (123, {}))
    monkeypatch.setattr(pipeline.tmdb, "get_person_profile_url", lambda pid: "https://img")
    monkeypatch.setattr(pipeline.wikidata, "get_qid", lambda name: "Q1")
    monkeypatch.setattr(pipeline.wikidata, "get_birth_death_years", lambda qid: (1900, 2000))
    monkeypatch.setattr(pipeline.wikidata, "get_country", lambda qid: "USA")

    try:
        info = ComposerInfo(name="Test")
        pipeline._collect_biography(info)

        assert info.tmdb_id == 123
        assert info.image_url == "https://img"
        assert info.wikidata_qid == "Q1"
        assert info.birth_year == 1900
        assert info.death_year == 2000
        assert info.country == "USA"
    finally:
        settings.tmdb_api_key = original_tmdb_key


def test_collect_biography_tmdb_missing_person(tmp_path, monkeypatch):
    """Test biography collection when TMDB person is missing."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    original_tmdb_key = settings.tmdb_api_key
    settings.tmdb_api_key = "test-key"

    monkeypatch.setattr(
        pipeline.biography_service,
        "get_biography",
        lambda name: {
            "biography": "Bio",
            "style": "Style",
            "anecdotes": "Facts",
            "image_url": None,
        },
    )
    monkeypatch.setattr(pipeline.tmdb, "search_person", lambda name: (None, {}))
    monkeypatch.setattr(pipeline.wikidata, "get_qid", lambda name: None)

    try:
        info = ComposerInfo(name="Test")
        pipeline._collect_biography(info)
        assert info.tmdb_id is None
        assert info.image_url is None
    finally:
        settings.tmdb_api_key = original_tmdb_key


def test_collect_biography_derives_facts(tmp_path, monkeypatch):
    """Test biography collection when anecdotes missing."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)

    monkeypatch.setattr(pipeline.biography_service, "get_biography", lambda name: "Bio")
    monkeypatch.setattr(pipeline.biography_service, "get_musical_style", lambda name: "Style")
    monkeypatch.setattr(pipeline.biography_service, "get_anecdotes", lambda name: "")
    monkeypatch.setattr(pipeline.biography_service, "derive_fun_facts", lambda bio, style: "Derived")

    info = ComposerInfo(name="Test")
    pipeline._collect_biography(info)
    assert info.anecdotes == "Derived"


def test_process_composers_from_list_empty(tmp_path):
    """Test processing with no composers in list."""
    list_path = tmp_path / "empty.md"
    list_path.write_text("", encoding="utf-8")
    results = process_composers_from_list(list_path, output_dir=tmp_path)
    assert results == []


def test_process_composers_from_list_handles_errors(tmp_path, monkeypatch):
    """Test processing continues when composer fails."""
    content = "\n".join(
        [
            "| No. | Name |",
            "| --- | --- |",
            "| 1 | Good Composer |",
            "| 2 | Bad Composer |",
        ]
    )
    list_path = tmp_path / "list.md"
    list_path.write_text(content, encoding="utf-8")

    class DummyPipeline(ComposerPipeline):
        def process_composer(self, name, index=None):
            if "Bad" in name:
                raise RuntimeError("fail")
            return ComposerInfo(name=name, index=index)

    monkeypatch.setattr("soundtracker.pipeline.ComposerPipeline", DummyPipeline)
    results = process_composers_from_list(list_path, output_dir=tmp_path)
    assert len(results) == 1
    assert results[0].name == "Good Composer"


def test_select_top10_without_web_toplists(tmp_path, monkeypatch):
    """Test _select_top10 skips web rankings when disabled."""
    pipeline = ComposerPipeline(output_dir=tmp_path, download_posters=False)
    info = ComposerInfo(name="Test", filmography=[], awards=[])
    original_flag = settings.use_web_toplists
    settings.use_web_toplists = False
    called = {"ok": False}

    def fake_get_web_rankings(_name):
        called["ok"] = True
        return {}

    monkeypatch.setattr(pipeline.top10_service, "get_web_rankings", fake_get_web_rankings)
    monkeypatch.setattr(pipeline.top10_service, "select_top_10", lambda *a, **k: [])
    try:
        pipeline._select_top10(info)
        assert called["ok"] is False
    finally:
        settings.use_web_toplists = original_flag


def test_main_missing_master_list(tmp_path, monkeypatch):
    """Test main exits when master list missing."""
    original_dir = settings.output_dir
    settings.output_dir = tmp_path
    try:
        main()
    finally:
        settings.output_dir = original_dir


def test_main_with_master_list(tmp_path, monkeypatch):
    """Test main calls process_composers_from_list."""
    master_list = tmp_path / "composers_master_list.md"
    master_list.write_text("| 1 | Composer |", encoding="utf-8")

    original_dir = settings.output_dir
    settings.output_dir = tmp_path
    called = {"ok": False}

    def fake_process(path, start_index=1, end_index=None, output_dir=None):
        called["ok"] = True
        return []

    monkeypatch.setattr("soundtracker.pipeline.process_composers_from_list", fake_process)
    try:
        main()
        assert called["ok"] is True
    finally:
        settings.output_dir = original_dir


def test_module_main_executes(tmp_path, monkeypatch):
    """Test __main__ execution path."""
    master_list = tmp_path / "composers_master_list.md"
    master_list.write_text("", encoding="utf-8")

    original_dir = settings.output_dir
    settings.output_dir = tmp_path
    monkeypatch.setattr("soundtracker.pipeline.process_composers_from_list", lambda *a, **k: [])
    try:
        import runpy
        import sys
        import warnings

        sys.modules.pop("soundtracker.pipeline", None)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*sys.modules.*")
            runpy.run_module("soundtracker.pipeline", run_name="__main__")
    finally:
        settings.output_dir = original_dir
