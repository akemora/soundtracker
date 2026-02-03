"""Pydantic models for Search API endpoints.

This module defines request/response models for the FTS5 full-text
search functionality.
"""

from pydantic import BaseModel, ConfigDict, Field


class SearchResult(BaseModel):
    """Individual search result from FTS5 query.

    Contains composer data with relevance ranking from bm25() function.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Composer ID")
    name: str = Field(description="Composer name")
    slug: str = Field(description="URL-friendly identifier")
    country: str | None = Field(default=None, description="Country of origin")
    birth_year: int | None = Field(default=None, description="Year of birth")
    death_year: int | None = Field(default=None, description="Year of death")
    photo_local: str | None = Field(default=None, description="Local path to photo")
    biography: str | None = Field(default=None, description="Biography text")
    rank: float = Field(default=0.0, description="FTS5 relevance score (bm25)")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    query: str = Field(description="Original search query")
    results: list[SearchResult] = Field(description="List of matching composers")
    count: int = Field(description="Number of results returned")
