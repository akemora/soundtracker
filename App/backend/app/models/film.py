"""Pydantic models for Film API endpoints.

This module defines request/response models for film-related data
including filmography listings and Top 10 film entries.
"""

from pydantic import BaseModel, ConfigDict, Field


class FilmBase(BaseModel):
    """Base film model with shared fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique film identifier")
    title: str = Field(description="Display title")
    year: int | None = Field(default=None, description="Release year")


class FilmSummary(FilmBase):
    """Summary film model for list endpoints.

    Minimal film information for displaying in lists.
    """

    original_title: str | None = Field(default=None, description="Original title")
    poster_local: str | None = Field(default=None, description="Local path to poster")
    is_top10: bool = Field(default=False, description="Whether film is in Top 10")
    top10_rank: int | None = Field(default=None, description="Position in Top 10 (1-10)")


class FilmDetail(FilmBase):
    """Detailed film model with all fields.

    Complete film information including external IDs and popularity metrics.
    """

    composer_id: int = Field(description="Associated composer ID")
    original_title: str | None = Field(default=None, description="Original title")
    title_es: str | None = Field(default=None, description="Spanish title")
    poster_url: str | None = Field(default=None, description="TMDB poster URL")
    poster_local: str | None = Field(default=None, description="Local path to poster")
    is_top10: bool = Field(default=False, description="Whether film is in Top 10")
    top10_rank: int | None = Field(default=None, description="Position in Top 10 (1-10)")
    tmdb_id: int | None = Field(default=None, description="TMDB movie ID")
    imdb_id: str | None = Field(default=None, description="IMDB ID")
    vote_average: float | None = Field(default=None, description="TMDB vote average")
    vote_count: int | None = Field(default=None, description="TMDB vote count")
    popularity: float | None = Field(default=None, description="TMDB popularity score")
    spotify_popularity: float | None = Field(default=None, description="Spotify popularity")
    youtube_views: int | None = Field(default=None, description="YouTube view count")


class FilmListResponse(BaseModel):
    """Response model for filmography endpoint."""

    composer_id: int = Field(description="Composer ID")
    composer_name: str = Field(description="Composer name")
    films: list[FilmDetail] = Field(description="List of films")
    pagination: dict = Field(description="Pagination information")
