"""Pydantic models for the SOUNDTRACKER API.

This package exports all API models for use in routers and services.
"""

from .award import AwardDetail, AwardListResponse, AwardSummary
from .composer import (
    ComposerDetail,
    ComposerFilterOptions,
    ComposerListResponse,
    ComposerResponse,
    ComposerStats,
    ComposerSummary,
    ComposerWithStats,
    PaginationInfo,
)
from .film import FilmDetail, FilmListResponse, FilmSummary
from .search import SearchResponse, SearchResult

__all__ = [
    # Composer models
    "ComposerSummary",
    "ComposerDetail",
    "ComposerStats",
    "ComposerWithStats",
    "ComposerListResponse",
    "ComposerFilterOptions",
    "ComposerResponse",
    "PaginationInfo",
    # Film models
    "FilmSummary",
    "FilmDetail",
    "FilmListResponse",
    # Award models
    "AwardDetail",
    "AwardSummary",
    "AwardListResponse",
    # Search models
    "SearchResult",
    "SearchResponse",
]
