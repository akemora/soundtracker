"""Music API router for crawled track endpoints."""

from fastapi import APIRouter, Depends, Query

from ..database import DatabaseManager, get_database
from ..models import MusicResponse, PlaylistResponse
from ..services import get_playlist_by_composer, get_tracks_by_composer, regenerate_playlist

router = APIRouter(prefix="/api/composers", tags=["Music"])


@router.get("/{slug}/music", response_model=MusicResponse)
async def api_get_composer_music(
    slug: str,
    status: str | None = Query(None, description="Filter by crawl status"),
    db: DatabaseManager = Depends(get_database),
) -> MusicResponse:
    """Get crawled music tracks for a composer."""
    return await get_tracks_by_composer(db=db, slug=slug, status=status)


@router.get("/{slug}/playlist", response_model=PlaylistResponse)
async def api_get_composer_playlist(
    slug: str,
    db: DatabaseManager = Depends(get_database),
) -> PlaylistResponse:
    """Get playable playlist for a composer."""
    return await get_playlist_by_composer(db=db, slug=slug)


@router.post("/{slug}/playlist/refresh")
async def api_refresh_playlist(
    slug: str,
    db: DatabaseManager = Depends(get_database),
) -> dict[str, int | str]:
    """Regenerate playlist for a composer."""
    playlist = await regenerate_playlist(db=db, slug=slug)
    return {"status": "refreshed", "tracks_updated": playlist.total_tracks}
