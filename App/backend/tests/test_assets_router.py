"""Tests for assets router."""

import pytest
from fastapi import HTTPException

from app.routers import assets


@pytest.mark.asyncio
async def test_get_asset_invalid_type():
    """Test invalid asset type returns 400."""
    with pytest.raises(HTTPException) as exc:
        await assets.get_asset("invalid", "file.jpg")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_asset_invalid_path(tmp_path, monkeypatch):
    """Test directory traversal blocked."""
    monkeypatch.setattr(assets.settings, "assets_path", str(tmp_path))
    with pytest.raises(HTTPException) as exc:
        await assets.get_asset("posters", "../secret.txt")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_asset_not_found(tmp_path, monkeypatch):
    """Test missing file returns 404."""
    monkeypatch.setattr(assets.settings, "assets_path", str(tmp_path))
    with pytest.raises(HTTPException) as exc:
        await assets.get_asset("posters", "missing.jpg")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_asset_success(tmp_path, monkeypatch):
    """Test serving a valid asset."""
    monkeypatch.setattr(assets.settings, "assets_path", str(tmp_path))
    file_path = tmp_path / "poster.jpg"
    file_path.write_text("data", encoding="utf-8")

    response = await assets.get_asset("posters", "poster.jpg")
    assert response.path == file_path
