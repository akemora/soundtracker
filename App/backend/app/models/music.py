"""Pydantic models for music crawler API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MusicTrack(BaseModel):
    """Music track data from the crawler."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Track database ID")
    composer_id: int = Field(description="Composer ID")
    film_id: int | None = Field(default=None, description="Film ID")
    title: str = Field(description="Cue title")
    work: str = Field(description="Film title")
    rank: int | None = Field(default=None, description="Top 10 rank")
    status: str | None = Field(default=None, description="Crawl status")
    source: str | None = Field(default=None, description="Primary source")
    url: str | None = Field(default=None, description="Primary source URL")
    local_path: str | None = Field(default=None, description="Downloaded file path")
    alternatives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative sources",
    )
    searched_at: str | None = Field(default=None, description="Search timestamp")
    updated_at: str | None = Field(default=None, description="Update timestamp")


class MusicResponse(BaseModel):
    """Response model for composer music endpoint."""

    composer: str = Field(description="Composer slug")
    total: int = Field(description="Total tracks returned")
    tracks: list[MusicTrack] = Field(description="List of crawled tracks")
