"""Assets API router for serving static files (posters, photos).

This module defines the APIRouter for serving local asset files
such as movie posters and composer photos.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import get_settings

router = APIRouter(prefix="/api/assets", tags=["Assets"])
settings = get_settings()


@router.get("/{file_type}/{filename:path}")
async def get_asset(file_type: str, filename: str) -> FileResponse:
    """Serve a static asset file (poster or photo).

    Args:
        file_type: Type of asset ('posters' or 'photos').
        filename: Name of the file to serve.

    Returns:
        FileResponse with the requested asset.

    Raises:
        HTTPException 400: If file type is invalid.
        HTTPException 404: If file not found.
    """
    # Validate file type
    valid_types = {"posters", "photos"}
    if file_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid asset type. Must be one of: {', '.join(valid_types)}",
        )

    # Build file path
    assets_dir = Path(settings.assets_path)
    file_path = assets_dir / file_type / filename

    # Security: prevent directory traversal
    try:
        file_path = file_path.resolve()
        assets_resolved = assets_dir.resolve()
        if not str(file_path).startswith(str(assets_resolved)):
            raise HTTPException(status_code=400, detail="Invalid file path")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Check file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)
