"""Search service for FTS5 full-text search operations.

This module provides service functions for searching composers using
SQLite FTS5 full-text search with bm25 ranking.
"""

from ..database import DatabaseManager
from ..models import SearchResponse, SearchResult


async def search_composers(
    db: DatabaseManager,
    query: str,
    limit: int = 20,
) -> SearchResponse:
    """Search composers using FTS5 full-text search.

    Performs a full-text search on the fts_composers table using
    the bm25() ranking function for relevance scoring.

    Args:
        db: Database manager instance.
        query: Search query string (min 2 characters).
        limit: Maximum number of results to return.

    Returns:
        Search response with ranked results.
    """
    # Clean and validate query
    clean_query = query.strip()
    if len(clean_query) < 2:
        return SearchResponse(query=query, results=[], count=0)

    # Execute FTS search
    rows = await db.execute_fts_search(clean_query, limit)

    # Transform to Pydantic models
    results = [SearchResult.model_validate(row) for row in rows]

    return SearchResponse(
        query=query,
        results=results,
        count=len(results),
    )


async def search_suggestions(
    db: DatabaseManager,
    prefix: str,
    limit: int = 10,
) -> list[str]:
    """Get autocomplete suggestions for composer names.

    Performs a prefix search on composer names for autocomplete functionality.

    Args:
        db: Database manager instance.
        prefix: Search prefix (min 2 characters).
        limit: Maximum number of suggestions.

    Returns:
        List of matching composer names.
    """
    clean_prefix = prefix.strip()
    if len(clean_prefix) < 2:
        return []

    query = """
        SELECT name
        FROM composers
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
    """
    rows = await db.execute_query(query, (f"{clean_prefix}%", limit))

    return [row["name"] for row in rows] if rows else []
