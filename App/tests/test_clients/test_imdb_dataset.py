"""Tests for soundtracker.clients.imdb_dataset."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from soundtracker.clients.imdb_dataset import ImdbDataset, ImdbPerson


def _create_imdb_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE people (
            nconst TEXT PRIMARY KEY,
            primaryName TEXT,
            birthYear INTEGER,
            deathYear INTEGER,
            primaryProfession TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE composer_credits (
            nconst TEXT,
            tconst TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE titles (
            tconst TEXT PRIMARY KEY,
            primaryTitle TEXT,
            originalTitle TEXT,
            startYear INTEGER,
            titleType TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE title_ratings (
            tconst TEXT PRIMARY KEY,
            averageRating REAL,
            numVotes INTEGER
        )
        """
    )
    conn.executemany(
        "INSERT INTO people VALUES (?, ?, ?, ?, ?)",
        [
            ("nm0001", "John Williams", 1932, None, "composer,writer"),
            ("nm0002", "John Doe", 1940, None, "actor"),
            ("nm0003", "Jane Williams", 1950, None, "composer"),
        ],
    )
    conn.executemany(
        "INSERT INTO composer_credits VALUES (?, ?)",
        [
            ("nm0001", "tt0001"),
            ("nm0001", "tt0002"),
            ("nm0003", "tt0003"),
        ],
    )
    conn.executemany(
        "INSERT INTO titles VALUES (?, ?, ?, ?, ?)",
        [
            ("tt0001", "Alpha", "Alpha", 1977, "movie"),
            ("tt0002", "Beta", "Beta", 1980, "tvMovie"),
            ("tt0003", "Gamma", "Gamma", 1990, "movie"),
        ],
    )
    conn.executemany(
        "INSERT INTO title_ratings VALUES (?, ?, ?)",
        [
            ("tt0001", 7.5, 1000),
            ("tt0002", 6.2, 200),
            ("tt0003", 8.0, 1500),
        ],
    )
    conn.commit()
    conn.close()


def test_is_available_false_when_missing(tmp_path: Path) -> None:
    dataset = ImdbDataset(db_path=tmp_path / "missing.db")
    assert dataset.is_available is False


def test_connect_missing_raises(tmp_path: Path) -> None:
    dataset = ImdbDataset(db_path=tmp_path / "missing.db")
    with pytest.raises(FileNotFoundError):
        dataset._connect()


def test_imdb_person_music_professional() -> None:
    person = ImdbPerson(
        nconst="nm1",
        name="Test",
        birth_year=None,
        death_year=None,
        professions="composer,writer",
    )
    assert person.is_music_professional is True

    person = ImdbPerson(
        nconst="nm2",
        name="Test",
        birth_year=None,
        death_year=None,
        professions=None,
    )
    assert person.is_music_professional is False


def test_find_person_candidates_exact_and_credit_count(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        candidates = dataset.find_person_candidates("John Williams", conn=conn)
    finally:
        conn.close()

    assert len(candidates) == 1
    assert candidates[0].name == "John Williams"
    assert candidates[0].credit_count == 2


def test_find_person_candidates_fallback_like(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        candidates = dataset.find_person_candidates("lli", conn=conn)
    finally:
        conn.close()

    assert candidates
    assert candidates[0].name in {"John Williams", "Jane Williams"}


def test_resolve_person_prefers_composer(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        person = dataset.resolve_person("John", conn=conn)
    finally:
        conn.close()

    assert person is not None
    assert person.name == "John Williams"


def test_get_person_years_returns_person(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        person = dataset.get_person_years("John Williams", conn=conn)
    finally:
        conn.close()

    assert person is not None
    assert person.birth_year == 1932


def test_get_composer_filmography_returns_films(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        films = dataset.get_composer_filmography("John Williams", max_titles=1, conn=conn)
    finally:
        conn.close()

    assert len(films) == 1
    assert films[0].title == "Alpha"


def test_get_composer_filmography_unavailable_returns_empty(tmp_path: Path) -> None:
    dataset = ImdbDataset(db_path=tmp_path / "missing.db")
    assert dataset.get_composer_filmography("John Williams") == []


def test_find_person_candidates_unavailable_returns_empty(tmp_path: Path) -> None:
    dataset = ImdbDataset(db_path=tmp_path / "missing.db")
    assert dataset.find_person_candidates("John") == []


def test_find_person_candidates_empty_name_returns_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert dataset.find_person_candidates("   ", conn=conn) == []
    finally:
        conn.close()


def test_find_person_candidates_with_internal_connect(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    monkeypatch.setattr(dataset, "_connect", lambda: closing(conn))

    candidates = dataset.find_person_candidates("John Williams")
    assert candidates


def test_get_composer_filmography_no_person(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        assert dataset.get_composer_filmography("Unknown", conn=conn) == []
    finally:
        conn.close()


def test_fetch_films_skips_missing_title(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            "INSERT INTO titles VALUES (?, ?, ?, ?, ?)",
            ("tt0004", "", "", 2000, "movie"),
        )
        conn.execute("INSERT INTO composer_credits VALUES (?, ?)", ("nm0001", "tt0004"))
        conn.commit()
        dataset = ImdbDataset(db_path=db_path)
        films = dataset.get_composer_filmography("John Williams", max_titles=None, conn=conn)
        assert all(film.title for film in films)
    finally:
        conn.close()


def test_get_composer_filmography_with_internal_connect(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)
    monkeypatch.setattr(
        dataset,
        "_connect",
        lambda: closing(_connect_with_rows(db_path)),
    )

    films = dataset.get_composer_filmography("John Williams")
    assert films


def _connect_with_rows(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_connect_returns_connection(tmp_path: Path) -> None:
    db_path = tmp_path / "imdb.sqlite"
    _create_imdb_db(db_path)
    dataset = ImdbDataset(db_path=db_path)
    conn = dataset._connect()
    try:
        assert isinstance(conn, sqlite3.Connection)
    finally:
        conn.close()
