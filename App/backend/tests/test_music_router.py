"""Tests for music and playlist endpoints."""

import json
import sqlite3
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.models import MusicResponse, PlaylistResponse

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "soundtrackers.db"


def _get_composer_id(slug: str) -> int | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT id FROM composers WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return row[0] if row else None


def _insert_music_track(composer_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO music_tracks (
            composer_id,
            film_id,
            title,
            work,
            rank,
            status,
            source,
            url,
            local_path,
            alternatives_json,
            searched_at,
            updated_at
        )
        VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            composer_id,
            "Test Track",
            "Test Film",
            1,
            "free_available",
            "youtube",
            "https://www.youtube.com/watch?v=abc",
            "",
            json.dumps([]),
        ),
    )
    conn.commit()
    conn.close()


def _delete_music_track(composer_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM music_tracks WHERE composer_id = ? AND title = ?",
        (composer_id, "Test Track"),
    )
    conn.commit()
    conn.close()


def _insert_playlist(composer_id: int, slug: str) -> None:
    payload = {
        "composer_slug": slug,
        "composer_name": "Test Composer",
        "generated_at": "2026-02-05T00:00:00",
        "updated_at": "2026-02-05T00:00:00",
        "total_tracks": 1,
        "free_count": 1,
        "paid_count": 0,
        "tracks": [
            {
                "position": 1,
                "film": "Test Film",
                "film_year": 2020,
                "track_title": "Test Track",
                "is_original_pick": True,
                "source": "youtube",
                "url": "https://www.youtube.com/watch?v=abc",
                "embed_url": "https://www.youtube.com/embed/abc",
                "is_free": True,
                "duration": "1:00",
                "thumbnail": None,
                "alternatives": [],
            }
        ],
    }
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO composer_playlists (
            composer_id,
            total_tracks,
            free_count,
            paid_count,
            playlist_json,
            generated_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(composer_id) DO UPDATE SET
            total_tracks = excluded.total_tracks,
            free_count = excluded.free_count,
            paid_count = excluded.paid_count,
            playlist_json = excluded.playlist_json,
            generated_at = excluded.generated_at,
            updated_at = datetime('now')
        """,
        (
            composer_id,
            1,
            1,
            0,
            json.dumps(payload),
            payload["generated_at"],
        ),
    )
    conn.commit()
    conn.close()


def _delete_playlist(composer_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM composer_playlists WHERE composer_id = ?", (composer_id,))
    conn.commit()
    conn.close()


@pytest.mark.asyncio
async def test_get_music_success(async_client: AsyncClient, sample_composer_slug: str) -> None:
    composer_id = _get_composer_id(sample_composer_slug)
    if composer_id is None:
        pytest.skip("Composer not found in test database")

    _insert_music_track(composer_id)
    try:
        response = await async_client.get(f"/api/composers/{sample_composer_slug}/music")
        assert response.status_code == 200
        parsed = MusicResponse.model_validate(response.json())
        assert parsed.total >= 1
    finally:
        _delete_music_track(composer_id)


@pytest.mark.asyncio
async def test_get_playlist_success(async_client: AsyncClient, sample_composer_slug: str) -> None:
    composer_id = _get_composer_id(sample_composer_slug)
    if composer_id is None:
        pytest.skip("Composer not found in test database")

    _insert_playlist(composer_id, sample_composer_slug)
    try:
        response = await async_client.get(f"/api/composers/{sample_composer_slug}/playlist")
        assert response.status_code == 200
        parsed = PlaylistResponse.model_validate(response.json())
        assert parsed.composer_slug == sample_composer_slug
        assert parsed.total_tracks >= 1
    finally:
        _delete_playlist(composer_id)


@pytest.mark.asyncio
async def test_get_music_not_found(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/composers/not-a-real-composer/music")
    assert response.status_code == 404
