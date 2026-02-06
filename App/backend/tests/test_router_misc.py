"""Tests for router helper endpoints."""

import pytest

from app.routers.composers import api_get_composer_filters
from app.routers.music import api_refresh_playlist
from app.models import ComposerFilterOptions, PlaylistResponse


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_api_get_composer_filters(monkeypatch):
    async def fake_filters(db):
        return ComposerFilterOptions(countries=["USA"], award_types=["Oscar"])

    monkeypatch.setattr("app.routers.composers.get_composer_filter_options", fake_filters)
    result = await api_get_composer_filters(db=DummyDB())
    assert result.countries == ["USA"]


@pytest.mark.asyncio
async def test_api_refresh_playlist(monkeypatch):
    async def fake_regenerate(db, slug):
        return PlaylistResponse(
            composer_slug=slug,
            composer_name="Composer",
            generated_at="x",
            updated_at="x",
            total_tracks=2,
            free_count=2,
            paid_count=0,
            tracks=[],
        )

    monkeypatch.setattr("app.routers.music.regenerate_playlist", fake_regenerate)
    result = await api_refresh_playlist(slug="composer", db=DummyDB())
    assert result["tracks_updated"] == 2
