"""Search API router for FTS5 full-text search endpoints.

This module defines the APIRouter for search operations using
SQLite FTS5 with bm25 ranking.
"""

from fastapi import APIRouter, Depends, Query

from ..database import DatabaseManager, get_database
from ..models import SearchResponse
from ..services import search_composers, search_suggestions

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def api_search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: DatabaseManager = Depends(get_database),
) -> SearchResponse:
    """Full-text search for composers using FTS5.

    Searches across composer names, biographies, styles, and anecdotes
    using SQLite FTS5 with bm25 relevance ranking.

    Args:
        q: Search query string (minimum 2 characters).
        limit: Maximum number of results to return (max 100).
        db: Database manager dependency.

    Returns:
        Search results with relevance ranking.
    """
    return await search_composers(db=db, query=q, limit=limit)


@router.get("/suggestions", response_model=list[str])
async def api_suggestions(
    q: str = Query(..., min_length=2, description="Search prefix"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    db: DatabaseManager = Depends(get_database),
) -> list[str]:
    """Get autocomplete suggestions for composer names.

    Performs a prefix search for autocomplete functionality.

    Args:
        q: Search prefix (minimum 2 characters).
        limit: Maximum number of suggestions (max 20).
        db: Database manager dependency.

    Returns:
        List of matching composer names.
    """
    return await search_suggestions(db=db, prefix=q, limit=limit)
