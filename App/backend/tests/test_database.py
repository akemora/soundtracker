"""Tests for database manager."""

import sqlite3
from pathlib import Path

import pytest
import aiosqlite

from app.database import DatabaseError, DatabaseManager


def _create_db(path: Path, include_fts: bool = True) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE composers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            slug TEXT,
            biography_es TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE films (
            id INTEGER PRIMARY KEY,
            composer_id INTEGER,
            title TEXT,
            is_top10 INTEGER DEFAULT 0,
            top10_rank INTEGER,
            year INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE awards (
            id INTEGER PRIMARY KEY,
            composer_id INTEGER,
            award_name TEXT,
            status TEXT,
            year INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY,
            composer_id INTEGER,
            name TEXT
        )
        """
    )
    if include_fts:
        conn.execute("CREATE VIRTUAL TABLE fts_composers USING fts5(name, biography_es)")
    conn.commit()
    conn.close()


@pytest.mark.asyncio
async def test_initialize_missing_db(tmp_path):
    """Test initialize fails when database missing."""
    db = DatabaseManager(database_url=str(tmp_path / "missing.db"))
    with pytest.raises(DatabaseError):
        await db.initialize()


@pytest.mark.asyncio
async def test_initialize_missing_table(tmp_path):
    """Test initialize fails when required table missing."""
    db_path = tmp_path / "test.db"
    _create_db(db_path, include_fts=False)
    db = DatabaseManager(database_url=str(db_path))
    with pytest.raises(DatabaseError):
        await db.initialize()


@pytest.mark.asyncio
async def test_initialize_aiosqlite_error(tmp_path, monkeypatch):
    """Test initialize handles aiosqlite errors."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    db = DatabaseManager(database_url=str(db_path))

    class DummyConn:
        async def execute(self, *args, **kwargs):
            raise aiosqlite.Error("fail")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    import app.database as database
    monkeypatch.setattr(db, "get_connection", lambda: DummyConn())
    with pytest.raises(DatabaseError):
        await db.initialize()


@pytest.mark.asyncio
async def test_execute_query_fetch_one(tmp_path):
    """Test execute_query fetch_one."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO composers (id, name, slug) VALUES (1, 'A', 'a')")
    conn.commit()
    conn.close()

    db = DatabaseManager(database_url=str(db_path))
    row = await db.execute_query("SELECT * FROM composers WHERE id = ?", (1,), fetch_one=True)
    assert row["name"] == "A"


@pytest.mark.asyncio
async def test_execute_query_list(tmp_path):
    """Test execute_query returns list."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO composers (id, name, slug) VALUES (1, 'A', 'a')")
    conn.execute("INSERT INTO composers (id, name, slug) VALUES (2, 'B', 'b')")
    conn.commit()
    conn.close()

    db = DatabaseManager(database_url=str(db_path))
    rows = await db.execute_query("SELECT * FROM composers ORDER BY id")
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_execute_query_error(tmp_path):
    """Test execute_query raises DatabaseError on bad SQL."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    db = DatabaseManager(database_url=str(db_path))
    with pytest.raises(DatabaseError):
        await db.execute_query("SELECT * FROM missing_table")


@pytest.mark.asyncio
async def test_execute_query_sqlite_error(monkeypatch, tmp_path):
    """Test execute_query handles sqlite3.Error."""
    db = DatabaseManager(database_url=str(tmp_path / "test.db"))

    class DummyConn:
        async def execute(self, *args, **kwargs):
            raise sqlite3.Error("fail")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(db, "get_connection", lambda: DummyConn())
    with pytest.raises(DatabaseError):
        await db.execute_query("SELECT 1")


@pytest.mark.asyncio
async def test_get_connection_error(monkeypatch, tmp_path):
    """Test connection error raises DatabaseError."""
    from app import database

    async def fake_connect(*args, **kwargs):
        raise sqlite3.Error("fail")

    monkeypatch.setattr(database.aiosqlite, "connect", fake_connect)
    db = DatabaseManager(database_url=str(tmp_path / "test.db"))
    with pytest.raises(DatabaseError):
        async with db.get_connection():
            pass


@pytest.mark.asyncio
async def test_execute_fts_search_empty(tmp_path):
    """Test execute_fts_search returns empty for blank query."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    db = DatabaseManager(database_url=str(db_path))
    results = await db.execute_fts_search("   ")
    assert results == []


@pytest.mark.asyncio
async def test_execute_fts_search_fallback(tmp_path, monkeypatch):
    """Test execute_fts_search fallback on DatabaseError."""
    db_path = tmp_path / "test.db"
    _create_db(db_path)
    db = DatabaseManager(database_url=str(db_path))

    async def fake_execute_query(query, params=(), fetch_one=False):
        if "fts_composers" in query:
            raise DatabaseError("fts failed")
        return [{"name": "Composer"}]

    monkeypatch.setattr(db, "execute_query", fake_execute_query)
    results = await db.execute_fts_search("Composer", limit=5)
    assert results and results[0]["name"] == "Composer"


@pytest.mark.asyncio
async def test_get_composer_helpers(tmp_path, monkeypatch):
    """Test composer helper methods."""
    db = DatabaseManager(database_url=str(tmp_path / "test.db"))

    async def fake_execute_query(query, params=(), fetch_one=False):
        if "WHERE id" in query:
            return {"id": 1, "slug": "a"} if fetch_one else []
        if "WHERE slug" in query:
            return None
        return []

    monkeypatch.setattr(db, "execute_query", fake_execute_query)
    assert await db.get_composer_by_id(1) == {"id": 1, "slug": "a"}
    assert await db.get_composer_by_slug("missing") is None


@pytest.mark.asyncio
async def test_get_composer_films_builds_query(tmp_path, monkeypatch):
    """Test get_composer_films parameters."""
    db = DatabaseManager(database_url=str(tmp_path / "test.db"))
    seen = {"query": ""}

    async def fake_execute_query(query, params=()):
        seen["query"] = query
        return []

    monkeypatch.setattr(db, "execute_query", fake_execute_query)
    await db.get_composer_films(1, top10_only=True, limit=10, offset=5)
    assert "is_top10 = 1" in seen["query"]
    assert "LIMIT 10 OFFSET 5" in seen["query"]


@pytest.mark.asyncio
async def test_get_composer_awards_stats(tmp_path, monkeypatch):
    """Test awards and stats helpers."""
    db = DatabaseManager(database_url=str(tmp_path / "test.db"))

    async def fake_execute_query(query, params=(), fetch_one=False):
        if "v_composer_stats" in query:
            return {"id": 1} if fetch_one else []
        return [{"id": 1}]

    monkeypatch.setattr(db, "execute_query", fake_execute_query)
    awards = await db.get_composer_awards(1)
    stats = await db.get_composer_stats(1)
    assert awards == [{"id": 1}]
    assert stats == {"id": 1}
