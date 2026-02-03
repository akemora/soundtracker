"""Composer service for business logic and data transformation.

This module provides service functions for composer-related operations,
coordinating between the database layer and Pydantic models.
"""

from fastapi import HTTPException

from ..database import DatabaseManager
from ..models import (
    AwardDetail,
    AwardListResponse,
    AwardSummary,
    ComposerDetail,
    ComposerFilterOptions,
    ComposerListResponse,
    ComposerResponse,
    ComposerStats,
    ComposerWithStats,
    FilmDetail,
    FilmListResponse,
    PaginationInfo,
)


async def list_composers(
    db: DatabaseManager,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "name",
    order: str = "asc",
    decade: int | None = None,
    has_awards: bool | None = None,
    country: str | None = None,
    award_type: str | None = None,
) -> ComposerListResponse:
    """List composers with pagination, sorting, and filtering.

    Args:
        db: Database manager instance.
        page: Page number (1-based).
        per_page: Number of items per page.
        sort_by: Field to sort by (name, film_count, wins, career_start).
        order: Sort order (asc/desc).
        decade: Filter by birth decade (e.g., 1930 for 1930s).
        has_awards: Filter by whether composer has awards (True/False).
        country: Filter by country of origin.
        award_type: Filter by award type (e.g., Oscar, BAFTA).

    Returns:
        Paginated list of composers with statistics.
    """
    offset = (page - 1) * per_page

    # Validate sort field
    valid_sort_fields = {"name", "film_count", "wins", "birth_year", "index_num"}
    if sort_by not in valid_sort_fields:
        sort_by = "name"

    order_dir = "DESC" if order.lower() == "desc" else "ASC"

    # Build WHERE clause for filters
    where_clauses: list[str] = []
    params: list[int | str] = []

    if decade is not None:
        where_clauses.append("birth_year >= ? AND birth_year < ?")
        params.extend([decade, decade + 10])

    if has_awards is True:
        where_clauses.append("total_awards > 0")
    elif has_awards is False:
        where_clauses.append("total_awards = 0")

    if country:
        where_clauses.append("LOWER(country) = LOWER(?)")
        params.append(country)

    if award_type:
        where_clauses.append(
            "EXISTS (SELECT 1 FROM awards a WHERE a.composer_id = v.id AND a.award_name = ?)"
        )
        params.append(award_type)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count with filters
    count_query = f"SELECT COUNT(*) as total FROM v_composer_stats v WHERE {where_sql}"
    count_result = await db.execute_query(count_query, tuple(params), fetch_one=True)
    total = count_result["total"] if count_result else 0

    # Get paginated results from stats view with filters
    query = f"""
        SELECT *
        FROM v_composer_stats v
        WHERE {where_sql}
        ORDER BY {sort_by} {order_dir}
        LIMIT ? OFFSET ?
    """
    rows = await db.execute_query(query, (*params, per_page, offset))

    composers = [ComposerWithStats.model_validate(row) for row in rows]

    pagination = PaginationInfo(
        page=page,
        per_page=per_page,
        total=total,
        pages=(total + per_page - 1) // per_page if per_page > 0 else 0,
    )

    return ComposerListResponse(composers=composers, pagination=pagination)


async def get_composer_filter_options(db: DatabaseManager) -> ComposerFilterOptions:
    """Get available filter options for composers.

    Args:
        db: Database manager instance.

    Returns:
        Available countries and award types.
    """
    country_rows = await db.execute_query(
        """
        SELECT DISTINCT country
        FROM composers
        WHERE country IS NOT NULL AND country != ''
        ORDER BY country
        """
    )
    award_rows = await db.execute_query(
        """
        SELECT DISTINCT award_name
        FROM awards
        WHERE award_name IS NOT NULL AND award_name != ''
        ORDER BY award_name
        """
    )

    countries = [row["country"] for row in country_rows]
    award_types = [row["award_name"] for row in award_rows]
    return ComposerFilterOptions(countries=countries, award_types=award_types)


async def get_composer(db: DatabaseManager, slug: str) -> ComposerResponse:
    """Get detailed composer information by slug.

    Args:
        db: Database manager instance.
        slug: Composer URL slug.

    Returns:
        Detailed composer with stats and top10 films.

    Raises:
        HTTPException: If composer not found.
    """
    composer_row = await db.get_composer_by_slug(slug)

    if not composer_row:
        raise HTTPException(status_code=404, detail="Composer not found")

    composer = ComposerDetail.model_validate(composer_row)

    # Get stats
    stats_row = await db.get_composer_stats(composer.id)
    stats = ComposerStats.model_validate(stats_row) if stats_row else None

    # Get Top 10 films
    top10_rows = await db.get_composer_films(composer.id, top10_only=True)
    top10 = [FilmDetail.model_validate(row) for row in top10_rows]

    return ComposerResponse(composer=composer, stats=stats, top10=top10)


async def get_filmography(
    db: DatabaseManager,
    slug: str,
    page: int = 1,
    per_page: int = 50,
) -> FilmListResponse:
    """Get paginated filmography for a composer.

    Args:
        db: Database manager instance.
        slug: Composer URL slug.
        page: Page number (1-based).
        per_page: Number of items per page.

    Returns:
        Paginated list of films.

    Raises:
        HTTPException: If composer not found.
    """
    composer_row = await db.get_composer_by_slug(slug)

    if not composer_row:
        raise HTTPException(status_code=404, detail="Composer not found")

    composer_id = composer_row["id"]
    composer_name = composer_row["name"]
    offset = (page - 1) * per_page

    # Get total film count
    count_query = "SELECT COUNT(*) as total FROM films WHERE composer_id = ?"
    count_result = await db.execute_query(count_query, (composer_id,), fetch_one=True)
    total = count_result["total"] if count_result else 0

    # Get paginated films
    film_rows = await db.get_composer_films(composer_id, limit=per_page, offset=offset)
    films = [FilmDetail.model_validate(row) for row in film_rows]

    return FilmListResponse(
        composer_id=composer_id,
        composer_name=composer_name,
        films=films,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
        },
    )


async def get_awards(db: DatabaseManager, slug: str) -> AwardListResponse:
    """Get awards and nominations for a composer.

    Args:
        db: Database manager instance.
        slug: Composer URL slug.

    Returns:
        List of awards with summary.

    Raises:
        HTTPException: If composer not found.
    """
    composer_row = await db.get_composer_by_slug(slug)

    if not composer_row:
        raise HTTPException(status_code=404, detail="Composer not found")

    composer_id = composer_row["id"]
    composer_name = composer_row["name"]

    # Get all awards
    award_rows = await db.get_composer_awards(composer_id)
    awards = [AwardDetail.model_validate(row) for row in award_rows]

    # Calculate summary
    wins = sum(1 for a in awards if a.status == "win")
    nominations = sum(1 for a in awards if a.status == "nomination")

    summary = AwardSummary(
        total=len(awards),
        wins=wins,
        nominations=nominations,
    )

    return AwardListResponse(
        composer_id=composer_id,
        composer_name=composer_name,
        awards=awards,
        summary=summary,
    )
