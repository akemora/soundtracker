"""Composer API router with all composer-related endpoints.

This module defines the APIRouter for composer operations including
listing, detail views, filmography, and awards.
"""

from fastapi import APIRouter, Depends, Query

from ..database import DatabaseManager, get_database
from ..models import (
    AwardListResponse,
    ComposerFilterOptions,
    ComposerListResponse,
    ComposerResponse,
    FilmListResponse,
)
from ..services import (
    get_awards,
    get_composer,
    get_composer_filter_options,
    get_filmography,
    list_composers,
)

router = APIRouter(prefix="/api/composers", tags=["Composers"])


@router.get("", response_model=ComposerListResponse)
async def api_list_composers(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field"),
    order: str = Query("asc", description="Sort order (asc/desc)"),
    decade: int | None = Query(None, description="Filter by birth decade (e.g., 1930)"),
    has_awards: bool | None = Query(None, description="Filter by award status"),
    country: str | None = Query(None, description="Filter by country of origin"),
    award_type: str | None = Query(None, description="Filter by award type"),
    db: DatabaseManager = Depends(get_database),
) -> ComposerListResponse:
    """List composers with pagination and filters.

    Args:
        page: Page number (1-based).
        per_page: Number of items per page (max 100).
        sort_by: Field to sort by (name, film_count, wins, birth_year).
        order: Sort order (asc or desc).
        decade: Filter by birth decade (e.g., 1930 for composers born in the 1930s).
        has_awards: Filter by whether composer has awards (true/false).
        db: Database manager dependency.

    Returns:
        Paginated list of composers with statistics.
    """
    return await list_composers(
        db=db,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        decade=decade,
        has_awards=has_awards,
        country=country,
        award_type=award_type,
    )


@router.get("/filters", response_model=ComposerFilterOptions)
async def api_get_composer_filters(
    db: DatabaseManager = Depends(get_database),
) -> ComposerFilterOptions:
    """Get available filter options for composers."""
    return await get_composer_filter_options(db=db)


@router.get("/{slug}", response_model=ComposerResponse)
async def api_get_composer(
    slug: str,
    db: DatabaseManager = Depends(get_database),
) -> ComposerResponse:
    """Get detailed composer information.

    Args:
        slug: Composer URL slug.
        db: Database manager dependency.

    Returns:
        Detailed composer information with stats and Top 10 films.

    Raises:
        HTTPException 404: If composer not found.
    """
    return await get_composer(db=db, slug=slug)


@router.get("/{slug}/filmography", response_model=FilmListResponse)
async def api_get_filmography(
    slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    db: DatabaseManager = Depends(get_database),
) -> FilmListResponse:
    """Get composer filmography with pagination.

    Args:
        slug: Composer URL slug.
        page: Page number (1-based).
        per_page: Number of items per page (max 200).
        db: Database manager dependency.

    Returns:
        Paginated list of films for the composer.

    Raises:
        HTTPException 404: If composer not found.
    """
    return await get_filmography(
        db=db,
        slug=slug,
        page=page,
        per_page=per_page,
    )


@router.get("/{slug}/awards", response_model=AwardListResponse)
async def api_get_awards(
    slug: str,
    db: DatabaseManager = Depends(get_database),
) -> AwardListResponse:
    """Get composer awards and nominations.

    Args:
        slug: Composer URL slug.
        db: Database manager dependency.

    Returns:
        List of awards with summary statistics.

    Raises:
        HTTPException 404: If composer not found.
    """
    return await get_awards(db=db, slug=slug)
