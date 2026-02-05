"""Music API router for crawled track endpoints."""

from fastapi import APIRouter, Depends, Query

from ..database import DatabaseManager, get_database
from ..models import MusicResponse
from ..services import get_tracks_by_composer

router = APIRouter(prefix="/api/composers", tags=["Music"])


@router.get("/{slug}/music", response_model=MusicResponse)
async def api_get_composer_music(
    slug: str,
    status: str | None = Query(None, description="Filter by crawl status"),
    db: DatabaseManager = Depends(get_database),
) -> MusicResponse:
    """Get crawled music tracks for a composer."""
    return await get_tracks_by_composer(db=db, slug=slug, status=status)
