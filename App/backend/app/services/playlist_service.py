"""Playlist service for business logic and data access."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from fastapi import HTTPException

from ..database import DatabaseManager
from ..models import PlaylistResponse

APP_ROOT = Path(__file__).resolve().parents[3]
BATCH_SCRIPT = APP_ROOT / "scripts" / "music_crawler_batch.py"


async def get_playlist_by_composer(
    db: DatabaseManager,
    slug: str,
) -> PlaylistResponse:
    """Get playlist by composer slug.

    Args:
        db: Database manager instance.
        slug: Composer slug.

    Returns:
        PlaylistResponse with playlist details.

    Raises:
        HTTPException: If composer or playlist not found.
    """
    composer_row = await db.get_composer_by_slug(slug)
    if not composer_row:
        raise HTTPException(status_code=404, detail="Composer not found")

    composer_id = composer_row["id"]
    row = await db.execute_query(
        "SELECT playlist_json FROM composer_playlists WHERE composer_id = ?",
        (composer_id,),
        fetch_one=True,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Playlist not found")

    try:
        payload = json.loads(row["playlist_json"])
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Invalid playlist data") from exc

    return PlaylistResponse.model_validate(payload)


async def regenerate_playlist(
    db: DatabaseManager,
    slug: str,
) -> PlaylistResponse:
    """Regenerate playlist for a composer.

    Args:
        db: Database manager instance.
        slug: Composer slug.

    Returns:
        Updated playlist response.
    """
    cmd = [
        sys.executable,
        str(BATCH_SCRIPT),
        "--composer",
        slug,
        "--playlist-only",
        "--force",
    ]

    result = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Playlist refresh failed: {result.stderr.strip()}",
        )

    return await get_playlist_by_composer(db=db, slug=slug)
