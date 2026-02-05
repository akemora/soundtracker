"""Music service for crawled soundtrack tracks."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException

from ..database import DatabaseManager
from ..models import MusicResponse, MusicTrack


async def get_tracks_by_composer(
    db: DatabaseManager,
    slug: str,
    status: str | None = None,
) -> MusicResponse:
    """Get crawled music tracks for a composer.

    Args:
        db: Database manager instance.
        slug: Composer slug.
        status: Optional status filter.

    Returns:
        MusicResponse with composer info and tracks.

    Raises:
        HTTPException: If composer not found or no tracks exist.
    """
    composer_row = await db.get_composer_by_slug(slug)
    if not composer_row:
        raise HTTPException(status_code=404, detail="Composer not found")

    composer_id = composer_row["id"]
    where_clause = "composer_id = ?"
    params: list[Any] = [composer_id]

    if status:
        where_clause += " AND status = ?"
        params.append(status)

    query = f"""
        SELECT
            id,
            composer_id,
            film_id,
            title,
            work,
            rank,
            status,
            source,
            url,
            local_path,
            alternatives_json,
            searched_at,
            updated_at
        FROM music_tracks
        WHERE {where_clause}
        ORDER BY rank ASC, searched_at DESC
    """

    rows = await db.execute_query(query, tuple(params))
    if not rows:
        raise HTTPException(status_code=404, detail="No music tracks found")

    tracks: list[MusicTrack] = []
    for row in rows:
        alternatives: list[dict[str, Any]] = []
        alternatives_json = row.get("alternatives_json")
        if alternatives_json:
            try:
                alternatives = json.loads(alternatives_json)
            except json.JSONDecodeError:
                alternatives = []
        track = MusicTrack.model_validate({
            **row,
            "alternatives": alternatives,
        })
        tracks.append(track)

    return MusicResponse(
        composer=slug,
        total=len(tracks),
        tracks=tracks,
    )
