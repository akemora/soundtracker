"""Pydantic models for Award API endpoints.

This module defines request/response models for award-related data
including wins and nominations.
"""

from pydantic import BaseModel, ConfigDict, Field


class AwardBase(BaseModel):
    """Base award model with shared fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique award identifier")
    award_name: str = Field(description="Award name (Oscar, Grammy, etc.)")
    year: int | None = Field(default=None, description="Year awarded/nominated")
    status: str = Field(description="Status: 'win' or 'nomination'")


class AwardDetail(AwardBase):
    """Detailed award model with all fields."""

    composer_id: int = Field(description="Associated composer ID")
    category: str | None = Field(default=None, description="Award category")
    film_title: str | None = Field(default=None, description="Associated film title")


class AwardSummary(BaseModel):
    """Summary of awards for a composer."""

    total: int = Field(default=0, description="Total awards count")
    wins: int = Field(default=0, description="Number of wins")
    nominations: int = Field(default=0, description="Number of nominations")


class AwardListResponse(BaseModel):
    """Response model for composer awards endpoint."""

    composer_id: int = Field(description="Composer ID")
    composer_name: str = Field(description="Composer name")
    awards: list[AwardDetail] = Field(description="List of awards")
    summary: AwardSummary = Field(description="Awards summary")
