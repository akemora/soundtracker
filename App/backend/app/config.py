"""Configuration settings for SOUNDTRACKER FastAPI application.

This module defines application settings using Pydantic v2 for validation and type safety.
All configuration values can be overridden via environment variables.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    Attributes:
        app_name: Application name for logging and documentation.
        app_version: API version string.
        debug: Enable debug mode for development.
        database_url: SQLite database file path.
        cors_origins: Allowed CORS origins for frontend integration.
        max_search_results: Maximum results returned by search endpoints.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="SOUNDTRACKER API", description="Application name")
    app_version: str = Field(default="1.0.0", description="API version")
    debug: bool = Field(default=False, description="Debug mode")

    # Database settings
    database_url: str = Field(
        default="data/soundtrackers.db",
        description="SQLite database file path",
    )
    database_timeout: float = Field(default=30.0, description="Database timeout seconds")

    # API settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    max_search_results: int = Field(default=100, description="Max search results")
    page_size: int = Field(default=20, description="Default pagination size")

    # Assets settings
    assets_path: str = Field(default="outputs", description="Path to assets (posters)")

    @property
    def database_path(self) -> Path:
        """Get database path as Path object."""
        return Path(self.database_url)

    @property
    def assets_dir(self) -> Path:
        """Get assets directory as Path object."""
        return Path(self.assets_path)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance with cached configuration.
    """
    return Settings()
