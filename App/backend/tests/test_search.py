"""Tests for search API endpoints.

Tests cover FTS5 full-text search functionality including
successful searches, empty results, and query validation.
"""

import pytest
from httpx import AsyncClient

from app.models import SearchResponse


@pytest.mark.asyncio
async def test_search_success(
    async_client: AsyncClient,
    sample_search_query: str,
) -> None:
    """Test search returns matching results."""
    response = await async_client.get("/api/search", params={"q": sample_search_query})
    assert response.status_code == 200

    parsed = SearchResponse.model_validate(response.json())
    assert parsed.query == sample_search_query
    assert parsed.count >= 0
    assert len(parsed.results) == parsed.count


@pytest.mark.asyncio
async def test_search_with_results(async_client: AsyncClient) -> None:
    """Test search for common term returns results."""
    response = await async_client.get("/api/search", params={"q": "Williams"})
    assert response.status_code == 200

    parsed = SearchResponse.model_validate(response.json())
    assert parsed.count > 0

    # Check result structure
    for result in parsed.results:
        assert result.id > 0
        assert result.name
        assert result.slug


@pytest.mark.asyncio
async def test_search_no_results(async_client: AsyncClient) -> None:
    """Test search with no matches returns empty list."""
    response = await async_client.get("/api/search", params={"q": "zzzznonexistent"})
    assert response.status_code == 200

    parsed = SearchResponse.model_validate(response.json())
    assert parsed.count == 0
    assert parsed.results == []


@pytest.mark.asyncio
async def test_search_limit_parameter(async_client: AsyncClient) -> None:
    """Test search limit parameter is respected."""
    response = await async_client.get(
        "/api/search",
        params={"q": "composer", "limit": 5},
    )
    assert response.status_code == 200

    parsed = SearchResponse.model_validate(response.json())
    assert len(parsed.results) <= 5


@pytest.mark.asyncio
async def test_search_query_too_short(async_client: AsyncClient) -> None:
    """Test search rejects queries shorter than 2 characters."""
    response = await async_client.get("/api/search", params={"q": "a"})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_search_suggestions_success(async_client: AsyncClient) -> None:
    """Test autocomplete suggestions endpoint."""
    response = await async_client.get("/api/search/suggestions", params={"q": "John"})
    assert response.status_code == 200

    suggestions = response.json()
    assert isinstance(suggestions, list)
    for name in suggestions:
        assert "John" in name or "john" in name.lower()


@pytest.mark.asyncio
async def test_search_suggestions_limit(async_client: AsyncClient) -> None:
    """Test suggestions limit parameter."""
    response = await async_client.get(
        "/api/search/suggestions",
        params={"q": "Max", "limit": 3},
    )
    assert response.status_code == 200

    suggestions = response.json()
    assert len(suggestions) <= 3
