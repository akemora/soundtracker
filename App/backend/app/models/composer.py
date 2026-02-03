"""Pydantic models for Composer API endpoints.

This module defines request/response models for the composer-related endpoints
using Pydantic v2 with SQLite compatibility and OpenAPI documentation support.
"""

from pydantic import BaseModel, ConfigDict, Field


class ComposerBase(BaseModel):
    """Base composer model with shared fields.

    Used as a base class for other composer models to ensure consistency
    and avoid field duplication.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique composer identifier")
    name: str = Field(description="Full composer name")
    slug: str = Field(description="URL-friendly identifier")
    country: str | None = Field(default=None, description="Country of origin")


class ComposerSummary(ComposerBase):
    """Summary composer model for list endpoints.

    Contains minimal information for displaying composers in lists
    and search results. Optimized for performance.
    """

    index_num: int | None = Field(default=None, description="Position in master list")
    birth_year: int | None = Field(default=None, description="Year of birth")
    death_year: int | None = Field(default=None, description="Year of death (null if alive)")
    photo_local: str | None = Field(default=None, description="Local path to photo")


class ComposerStats(BaseModel):
    """Composer statistics from v_composer_stats view.

    Aggregated statistics including film counts, awards, and nominations.
    """

    model_config = ConfigDict(from_attributes=True)

    film_count: int = Field(default=0, description="Total number of films")
    top10_count: int = Field(default=0, description="Number of Top 10 films")
    wins: int = Field(default=0, description="Number of award wins")
    nominations: int = Field(default=0, description="Number of nominations")
    total_awards: int = Field(default=0, description="Total awards (wins + nominations)")
    source_count: int = Field(default=0, description="Number of information sources")


class ComposerDetail(ComposerBase):
    """Detailed composer model with all fields.

    Complete composer information including biography, style, and media URLs.
    Used for individual composer pages.
    """

    index_num: int | None = Field(default=None, description="Position in master list")
    birth_year: int | None = Field(default=None, description="Year of birth")
    death_year: int | None = Field(default=None, description="Year of death (null if alive)")
    photo_url: str | None = Field(default=None, description="External photo URL")
    photo_local: str | None = Field(default=None, description="Local path to photo")
    biography: str | None = Field(default=None, description="Composer biography text")
    style: str | None = Field(default=None, description="Musical style description")
    anecdotes: str | None = Field(default=None, description="Interesting anecdotes")


class ComposerWithStats(ComposerSummary):
    """Composer with statistics for list endpoints.

    Combines summary fields with aggregated statistics from the stats view.
    Used for paginated list responses with stats.
    """

    film_count: int = Field(default=0, description="Total number of films")
    top10_count: int = Field(default=0, description="Number of Top 10 films")
    wins: int = Field(default=0, description="Number of award wins")
    nominations: int = Field(default=0, description="Number of nominations")
    total_awards: int = Field(default=0, description="Total awards")
    source_count: int = Field(default=0, description="Number of sources")


class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(description="Current page number (1-based)")
    per_page: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")


class ComposerListResponse(BaseModel):
    """Paginated response for composer list endpoint."""

    composers: list[ComposerWithStats] = Field(description="List of composers with stats")
    pagination: PaginationInfo = Field(description="Pagination information")


class ComposerFilterOptions(BaseModel):
    """Available filter options for composer list."""

    countries: list[str] = Field(description="Available countries")


class ComposerResponse(BaseModel):
    """Response model for single composer endpoint.

    Contains detailed composer info, statistics, and Top 10 films.
    """

    composer: ComposerDetail = Field(description="Detailed composer information")
    stats: ComposerStats | None = Field(default=None, description="Composer statistics")
    top10: list = Field(default_factory=list, description="Top 10 films")
