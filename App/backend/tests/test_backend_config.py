"""Tests for backend config settings."""

from app.config import Settings, get_settings


def test_settings_properties(tmp_path):
    """Test database_path and assets_dir properties."""
    settings = Settings(database_url=str(tmp_path / "db.sqlite"), assets_path=str(tmp_path / "assets"))
    assert settings.database_path == tmp_path / "db.sqlite"
    assert settings.assets_dir == tmp_path / "assets"


def test_get_settings_cached():
    """Test cached settings instance."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
