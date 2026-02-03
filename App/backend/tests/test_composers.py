"""Tests for composer API endpoints.

Tests cover listing, detail views, filmography, and awards endpoints
with successful responses, 404 cases, and pagination validation.
"""

import pytest
from httpx import AsyncClient

from app.models import (
    AwardListResponse,
    ComposerListResponse,
    ComposerResponse,
    FilmListResponse,
)


@pytest.mark.asyncio
async def test_list_composers_success(async_client: AsyncClient) -> None:
    """Test listing composers returns paginated results."""
    response = await async_client.get("/api/composers")
    assert response.status_code == 200

    payload = response.json()
    parsed = ComposerListResponse.model_validate(payload)

    assert parsed.composers
    assert parsed.pagination.page == 1
    assert parsed.pagination.per_page == 20
    assert parsed.pagination.total >= len(parsed.composers)
    assert parsed.pagination.pages >= 1


@pytest.mark.asyncio
async def test_list_composers_pagination(async_client: AsyncClient) -> None:
    """Test pagination parameters work correctly."""
    response = await async_client.get(
        "/api/composers",
        params={"page": 2, "per_page": 5},
    )
    assert response.status_code == 200

    parsed = ComposerListResponse.model_validate(response.json())
    assert parsed.pagination.page == 2
    assert parsed.pagination.per_page == 5
    assert len(parsed.composers) <= 5
    assert parsed.pagination.total >= len(parsed.composers)
    assert parsed.pagination.pages >= 1


@pytest.mark.asyncio
async def test_get_composer_success(
    async_client: AsyncClient,
    sample_composer_slug: str,
) -> None:
    """Test getting composer detail returns correct data."""
    response = await async_client.get(f"/api/composers/{sample_composer_slug}")
    assert response.status_code == 200

    parsed = ComposerResponse.model_validate(response.json())
    assert parsed.composer.slug == sample_composer_slug
    assert parsed.composer.name
    assert parsed.stats is None or parsed.stats.total_awards >= 0


@pytest.mark.asyncio
async def test_get_composer_not_found(async_client: AsyncClient) -> None:
    """Test 404 for non-existent composer."""
    response = await async_client.get("/api/composers/not-a-real-composer")
    assert response.status_code == 404
    assert response.json().get("detail") == "Composer not found"


@pytest.mark.asyncio
async def test_get_filmography_success(
    async_client: AsyncClient,
    sample_composer_slug: str,
) -> None:
    """Test getting filmography returns films list."""
    response = await async_client.get(f"/api/composers/{sample_composer_slug}/filmography")
    assert response.status_code == 200

    parsed = FilmListResponse.model_validate(response.json())
    assert parsed.composer_id > 0
    assert parsed.composer_name
    assert parsed.pagination["page"] == 1
    assert parsed.pagination["per_page"] == 50
    assert "total" in parsed.pagination
    assert "pages" in parsed.pagination

    for film in parsed.films:
        assert film.composer_id == parsed.composer_id


@pytest.mark.asyncio
async def test_get_filmography_pagination(
    async_client: AsyncClient,
    sample_composer_slug: str,
) -> None:
    """Test filmography pagination works correctly."""
    response = await async_client.get(
        f"/api/composers/{sample_composer_slug}/filmography",
        params={"page": 2, "per_page": 5},
    )
    assert response.status_code == 200

    parsed = FilmListResponse.model_validate(response.json())
    assert parsed.pagination["page"] == 2
    assert parsed.pagination["per_page"] == 5
    assert len(parsed.films) <= 5
    assert parsed.pagination["total"] >= len(parsed.films)
    assert parsed.pagination["pages"] >= 1


@pytest.mark.asyncio
async def test_get_filmography_not_found(async_client: AsyncClient) -> None:
    """Test 404 for filmography of non-existent composer."""
    response = await async_client.get("/api/composers/not-a-real-composer/filmography")
    assert response.status_code == 404
    assert response.json().get("detail") == "Composer not found"


@pytest.mark.asyncio
async def test_get_awards_success(
    async_client: AsyncClient,
    sample_composer_slug: str,
) -> None:
    """Test getting awards returns awards list with summary."""
    response = await async_client.get(f"/api/composers/{sample_composer_slug}/awards")
    assert response.status_code == 200

    parsed = AwardListResponse.model_validate(response.json())
    assert parsed.composer_id > 0
    assert parsed.composer_name

    wins = sum(1 for award in parsed.awards if award.status == "win")
    nominations = sum(1 for award in parsed.awards if award.status == "nomination")

    assert parsed.summary.total == len(parsed.awards)
    assert parsed.summary.wins == wins
    assert parsed.summary.nominations == nominations


@pytest.mark.asyncio
async def test_get_awards_not_found(async_client: AsyncClient) -> None:
    """Test 404 for awards of non-existent composer."""
    response = await async_client.get("/api/composers/not-a-real-composer/awards")
    assert response.status_code == 404
    assert response.json().get("detail") == "Composer not found"
