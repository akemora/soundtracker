"""Extra tests for playlist generator."""

import sqlite3
from pathlib import Path

import pytest

from src.models.track import SearchResult, Track
from src.playlist.generator import PlaylistGenerator, Film


def _create_db(path: Path, with_top10: bool = True) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE composers (id INTEGER PRIMARY KEY, name TEXT, slug TEXT)")
    conn.execute("INSERT INTO composers (id, name, slug) VALUES (1, 'Composer', 'composer')")
    conn.execute(
        """
        CREATE TABLE v_top10_films (
            top10_rank INTEGER,
            title TEXT,
            title_es TEXT,
            original_title TEXT,
            year INTEGER,
            composer_slug TEXT
        )
        """
    )
    if with_top10:
        conn.execute(
            "INSERT INTO v_top10_films (top10_rank, title, title_es, original_title, year, composer_slug) VALUES (1, 'Film', 'Film', 'Film', 2000, 'composer')"
        )
    conn.execute(
        """
        CREATE TABLE films (
            id INTEGER PRIMARY KEY,
            composer_id INTEGER,
            title TEXT,
            title_es TEXT,
            original_title TEXT,
            year INTEGER,
            is_top10 INTEGER,
            top10_rank INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO films (id, composer_id, title, title_es, original_title, year, is_top10, top10_rank) VALUES (1, 1, 'Film2', 'Film2', 'Film2', 2001, 1, 1)"
    )
    conn.commit()
    conn.close()


class DummySearcher:
    name = "youtube"

    def __init__(self, results):
        self._results = results

    def search(self, track):
        return self._results


def _result(track, source="youtube", is_free=True):
    return SearchResult(track=track, source=source, url="u", is_free=is_free, title="t")


def test_get_composer_name_missing(tmp_path):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE composers (id INTEGER PRIMARY KEY, name TEXT, slug TEXT)")
    conn.commit()
    conn.close()
    with pytest.raises(RuntimeError):
        PlaylistGenerator("missing", db_path)


def test_get_top_films_fallback(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path, with_top10=False)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    films = generator._get_top_films()
    assert films and films[0].title == "Film2"


def test_get_popular_and_alternatives(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    film = Film(title="Film", year=2000)
    track = generator._get_popular_track(film, 1)
    assert track.cue_title == "Main Title"
    alternatives = generator._get_alternative_tracks(film, 1)
    assert alternatives


def test_generate_no_playable_tracks(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    monkeypatch.setattr(generator, "_get_top_films", lambda: [Film(title="Film", year=2000)])
    monkeypatch.setattr(generator, "_find_playable_track", lambda *a, **k: None)
    playlist = generator.generate()
    assert playlist.tracks == []


def test_find_playable_track_free(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    track = Track(rank=1, film="Film", cue_title="Main Title", description="", composer="Composer")
    free = _result(track, is_free=True)
    generator = PlaylistGenerator(
        "composer",
        db_path,
        searchers={"free": [DummySearcher([free])], "paid": []},
    )
    playlist = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist and playlist.is_free is True


def test_find_playable_track_fallback(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    free_alt = _result(Track(rank=1, film="Film", cue_title="Theme", description="", composer="Composer"), is_free=True)

    class AltOnlySearcher(DummySearcher):
        def search(self, track):
            if track.cue_title != "Main Title":
                return self._results
            return []

    generator = PlaylistGenerator(
        "composer",
        db_path,
        searchers={"free": [AltOnlySearcher([free_alt])], "paid": []},
    )
    playlist = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist and playlist.fallback_reason


def test_find_playable_track_paid(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    track = Track(rank=1, film="Film", cue_title="Main Title", description="", composer="Composer")
    paid = _result(track, source="spotify", is_free=False)
    generator = PlaylistGenerator(
        "composer",
        db_path,
        searchers={"free": [DummySearcher([])], "paid": [DummySearcher([paid])]},
    )
    playlist = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist and playlist.is_free is False

    monkeypatch.setattr(generator, "_pick_best_result", lambda results: None)
    playlist2 = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist2 is not None


def test_find_playable_track_paid_placeholder(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    paid_track = Track(rank=1, film="Film", cue_title="Main Title", description="", composer="Composer")
    generator = PlaylistGenerator(
        "composer",
        db_path,
        searchers={"free": [DummySearcher([])], "paid": [DummySearcher([_result(paid_track, source="amazon", is_free=False)])]},
    )
    monkeypatch.setattr(generator, "_pick_best_result", lambda results: None)
    playlist = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist and playlist.purchase_links


def test_find_playable_track_none(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    playlist = generator._find_playable_track(Film(title="Film", year=2000), 1)
    assert playlist is None


def test_priority_and_thumbnail(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    assert generator._priority_for_source("unknown") == 0
    assert generator._youtube_thumbnail("https://youtu.be/abc") is not None
    assert generator._youtube_thumbnail("invalid") is None


def test_init_searchers_and_provider(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)

    generator = PlaylistGenerator("composer", db_path, searchers={"free": [1], "paid": [2]})
    assert generator.free_searchers == [1]
    assert generator.paid_searchers == [2]

    class DummyProvider:
        api_key = None

    monkeypatch.setattr("src.playlist.generator.PerplexityProvider", lambda: DummyProvider())
    generator2 = PlaylistGenerator("composer", db_path, searchers=None)
    assert generator2.free_searchers


def test_build_provider_prefers_perplexity(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)

    class DummyProvider:
        api_key = "key"

    monkeypatch.setattr("src.playlist.generator.PerplexityProvider", lambda: DummyProvider())
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})
    provider = generator._build_provider()
    assert provider is not None


def test_safe_init_searcher(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)
    generator = PlaylistGenerator("composer", db_path, searchers={"free": [], "paid": []})

    class Dummy:
        def __init__(self, provider=None, max_results=1):
            self.provider = provider

    class DummyNoProvider:
        def __init__(self, max_results=1):
            self.max_results = max_results

    assert generator._safe_init_searcher(Dummy, provider=None, max_results=1)
    assert generator._safe_init_searcher(DummyNoProvider, provider=None, max_results=1)


def test_search_error_handling(tmp_path):
    db_path = tmp_path / "db.sqlite"
    _create_db(db_path)

    class ErrorSearcher:
        name = "youtube"

        def search(self, track):
            raise RuntimeError("fail")

    generator = PlaylistGenerator(
        "composer",
        db_path,
        searchers={"free": [ErrorSearcher()], "paid": [ErrorSearcher()]},
    )
    track = Track(rank=1, film="Film", cue_title="Main Title", description="", composer="Composer")
    assert generator._search_free_source(track) == []
    assert generator._search_paid_sources(track) == []
