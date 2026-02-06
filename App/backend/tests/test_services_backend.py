"""Tests for backend services."""

import pytest
from fastapi import HTTPException

from app.services import (
    get_awards,
    get_composer,
    get_composer_filter_options,
    get_filmography,
    list_composers,
    search_composers,
    search_suggestions,
)
from app.services.playlist_service import get_playlist_by_composer, regenerate_playlist


class FakeDB:
    def __init__(self):
        self.rows = []

    async def execute_query(self, query, params=(), fetch_one=False):
        if "COUNT(*) as total" in query:
            return {"total": 1} if fetch_one else []
        if "FROM v_composer_stats" in query:
            return [{"id": 1, "name": "Composer", "slug": "composer", "film_count": 1, "wins": 0, "birth_year": 1900, "index_num": 1}]
        if "FROM composers" in query and "DISTINCT country" in query:
            return [{"country": "USA"}]
        if "FROM awards" in query and "DISTINCT award_name" in query:
            return [{"award_name": "Oscar"}]
        if "FROM films" in query:
            return []
        return []

    async def execute_fts_search(self, query, limit):
        return [{"id": 1, "name": "Composer", "slug": "composer"}]

    async def get_composer_by_slug(self, slug):
        if slug == "missing":
            return None
        return {"id": 1, "name": "Composer", "slug": slug}

    async def get_composer_stats(self, composer_id):
        return {"id": composer_id, "total_awards": 0, "wins": 0, "nominations": 0, "total_awards": 0, "source_count": 0, "film_count": 1, "top10_count": 0, "index_num": 1, "name": "Composer", "slug": "composer", "birth_year": 1900, "death_year": None, "country": "USA", "photo_local": None}

    async def get_composer_films(self, composer_id, top10_only=False, limit=None, offset=0):
        return []

    async def get_composer_awards(self, composer_id):
        return [{
            "id": 1,
            "composer_id": composer_id,
            "award_name": "Oscar",
            "status": "win",
            "year": 2000,
            "category": None,
            "film_title": None,
        }]


@pytest.mark.asyncio
async def test_list_composers_filters():
    db = FakeDB()
    result = await list_composers(
        db=db,
        page=1,
        per_page=0,
        sort_by="invalid",
        order="desc",
        decade=1900,
        has_awards=True,
        country="USA",
        award_type="Oscar",
    )
    assert result.pagination.pages == 0
    assert result.composers


@pytest.mark.asyncio
async def test_list_composers_has_awards_false():
    db = FakeDB()
    result = await list_composers(
        db=db,
        page=1,
        per_page=10,
        sort_by="name",
        order="asc",
        has_awards=False,
    )
    assert result.pagination.total >= 0


@pytest.mark.asyncio
async def test_get_composer_filter_options():
    db = FakeDB()
    options = await get_composer_filter_options(db=db)
    assert options.countries == ["USA"]
    assert options.award_types == ["Oscar"]


@pytest.mark.asyncio
async def test_get_composer_not_found():
    db = FakeDB()
    with pytest.raises(HTTPException):
        await get_composer(db=db, slug="missing")


@pytest.mark.asyncio
async def test_get_filmography_not_found():
    db = FakeDB()
    with pytest.raises(HTTPException):
        await get_filmography(db=db, slug="missing")


@pytest.mark.asyncio
async def test_get_awards_summary():
    db = FakeDB()
    result = await get_awards(db=db, slug="composer")
    assert result.summary.total == 1
    assert result.summary.wins == 1


@pytest.mark.asyncio
async def test_search_services():
    db = FakeDB()
    empty = await search_composers(db=db, query="a", limit=10)
    assert empty.count == 0
    result = await search_composers(db=db, query="Composer", limit=10)
    assert result.count == 1

    suggestions = await search_suggestions(db=db, prefix="C", limit=10)
    assert suggestions == []


@pytest.mark.asyncio
async def test_search_suggestions_with_results():
    class SuggestDB(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return [{"name": "Composer"}]

    db = SuggestDB()
    suggestions = await search_suggestions(db=db, prefix="Co", limit=10)
    assert suggestions == ["Composer"]


@pytest.mark.asyncio
async def test_playlist_service_errors(monkeypatch):
    class PlaylistDB(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return None

    db = PlaylistDB()
    with pytest.raises(HTTPException):
        await get_playlist_by_composer(db=db, slug="missing")

    class PlaylistDB2(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return {"playlist_json": "not json"}

    db2 = PlaylistDB2()
    with pytest.raises(HTTPException):
        await get_playlist_by_composer(db=db2, slug="composer")

    class PlaylistDB3(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return None

    db3 = PlaylistDB3()
    with pytest.raises(HTTPException):
        await get_playlist_by_composer(db=db3, slug="composer")


@pytest.mark.asyncio
async def test_regenerate_playlist_failure(monkeypatch):
    class PlaylistDB(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return {"playlist_json": "{}"}

    db = PlaylistDB()

    class Result:
        returncode = 1
        stderr = "fail"

    async def fake_to_thread(func, *args, **kwargs):
        return Result()

    monkeypatch.setattr("app.services.playlist_service.asyncio.to_thread", fake_to_thread)
    with pytest.raises(HTTPException):
        await regenerate_playlist(db=db, slug="composer")


@pytest.mark.asyncio
async def test_playlist_success_and_regenerate(monkeypatch):
    class PlaylistDB(FakeDB):
        async def execute_query(self, query, params=(), fetch_one=False):
            return {"playlist_json": '{"composer_slug":"composer","composer_name":"Composer","generated_at":"x","updated_at":"x","total_tracks":1,"free_count":1,"paid_count":0,"tracks":[]}'}

    db = PlaylistDB()

    class Result:
        returncode = 0
        stderr = ""

    async def fake_to_thread(func, *args, **kwargs):
        return Result()

    monkeypatch.setattr("app.services.playlist_service.asyncio.to_thread", fake_to_thread)
    playlist = await get_playlist_by_composer(db=db, slug="composer")
    assert playlist.total_tracks == 1
    refreshed = await regenerate_playlist(db=db, slug="composer")
    assert refreshed.total_tracks == 1
