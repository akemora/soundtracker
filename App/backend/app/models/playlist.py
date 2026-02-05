"""Pydantic models for playlist API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlaylistTrack(BaseModel):
    """Playlist track entry."""

    model_config = ConfigDict(from_attributes=True)

    position: int = Field(description="Track position in playlist")
    film: str = Field(description="Film title")
    film_year: int | None = Field(default=None, description="Film year")
    track_title: str = Field(description="Track title")
    is_original_pick: bool = Field(description="Whether this is the original pick")
    source: str = Field(description="Source name")
    url: str = Field(description="Track URL")
    embed_url: str | None = Field(default=None, description="Embeddable URL")
    is_free: bool = Field(description="Whether track is free")
    duration: str | None = Field(default=None, description="Track duration")
    thumbnail: str | None = Field(default=None, description="Thumbnail URL")
    fallback_reason: str | None = Field(default=None, description="Fallback reason")
    alternatives: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative sources",
    )
    purchase_links: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Purchase links",
    )


class PlaylistResponse(BaseModel):
    """Playlist response model."""

    composer_slug: str = Field(description="Composer slug")
    composer_name: str = Field(description="Composer name")
    generated_at: str = Field(description="Generated timestamp")
    updated_at: str = Field(description="Updated timestamp")
    total_tracks: int = Field(description="Total tracks")
    free_count: int = Field(description="Free tracks count")
    paid_count: int = Field(description="Paid tracks count")
    tracks: list[PlaylistTrack] = Field(description="Playlist tracks")
