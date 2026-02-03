"""Centralized configuration for SOUNDTRACKER.

This module provides a Pydantic-based Settings class that loads configuration
from environment variables with validation and sensible defaults.

Usage:
    from soundtracker.config import settings

    if settings.tmdb_api_key:
        # Use TMDB API
        pass
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Boolean settings accept '1', 'true', 'yes' as truthy values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Paths
    # ==========================================================================

    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2],
        description="Base directory of the project",
    )
    output_dir: Path = Field(
        default=None,
        description="Directory for output files",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def set_output_dir(cls, v, info):
        """Set default output_dir based on base_dir if not provided."""
        if v is None:
            base = info.data.get("base_dir") or Path(__file__).resolve().parents[2]
            return Path(base) / "outputs"
        return Path(v)

    # ==========================================================================
    # API Keys
    # ==========================================================================

    tmdb_api_key: Optional[str] = Field(
        default=None,
        alias="TMDB_API_KEY",
        description="The Movie Database API key",
    )
    pplx_api_key: Optional[str] = Field(
        default=None,
        alias="PPLX_API_KEY",
        description="Perplexity API key",
    )
    perplexity_api_key: Optional[str] = Field(
        default=None,
        alias="PERPLEXITY_API_KEY",
        description="Perplexity API key (alternative)",
    )
    youtube_api_key: Optional[str] = Field(
        default=None,
        alias="YOUTUBE_API_KEY",
        description="YouTube Data API v3 key",
    )
    spotify_client_id: Optional[str] = Field(
        default=None,
        alias="SPOTIFY_CLIENT_ID",
        description="Spotify API client ID",
    )
    spotify_client_secret: Optional[str] = Field(
        default=None,
        alias="SPOTIFY_CLIENT_SECRET",
        description="Spotify API client secret",
    )

    @property
    def perplexity_key(self) -> Optional[str]:
        """Get Perplexity API key from either env var."""
        return self.pplx_api_key or self.perplexity_api_key

    # ==========================================================================
    # API Endpoints
    # ==========================================================================

    tmdb_api_url: str = Field(
        default="https://api.themoviedb.org/3",
        description="TMDB API base URL",
    )
    tmdb_image_url: str = Field(
        default="https://image.tmdb.org/t/p/w500",
        description="TMDB image base URL",
    )
    pplx_api_url: str = Field(
        default="https://api.perplexity.ai/v2",
        alias="PPLX_API",
        description="Perplexity API base URL",
    )
    translate_endpoint: str = Field(
        default="https://translate.googleapis.com/translate_a/single",
        description="Google Translate API endpoint",
    )

    # ==========================================================================
    # Feature Flags
    # ==========================================================================

    search_web_enabled: bool = Field(
        default=True,
        alias="SEARCH_WEB_ENABLED",
        description="Enable web search functionality",
    )
    download_posters: bool = Field(
        default=True,
        alias="DOWNLOAD_POSTERS",
        description="Download film posters",
    )
    spotify_enabled: bool = Field(
        default=True,
        alias="SPOTIFY_ENABLED",
        description="Enable Spotify integration",
    )
    youtube_enabled: bool = Field(
        default=True,
        alias="YOUTUBE_ENABLED",
        description="Enable YouTube integration",
    )
    use_web_toplists: bool = Field(
        default=True,
        alias="USE_WEB_TOPLISTS",
        description="Use web search for top lists",
    )
    poster_web_fallback: bool = Field(
        default=True,
        alias="POSTER_WEB_FALLBACK",
        description="Fall back to web search for posters",
    )
    top_force_awards: bool = Field(
        default=True,
        alias="TOP_FORCE_AWARDS",
        description="Force award-winning films in Top 10",
    )

    @property
    def is_spotify_available(self) -> bool:
        """Check if Spotify integration is available."""
        return (
            self.spotify_enabled
            and bool(self.spotify_client_id)
            and bool(self.spotify_client_secret)
        )

    @property
    def is_youtube_available(self) -> bool:
        """Check if YouTube integration is available."""
        return self.youtube_enabled and bool(self.youtube_api_key)

    @property
    def is_tmdb_available(self) -> bool:
        """Check if TMDB integration is available."""
        return bool(self.tmdb_api_key)

    @property
    def is_perplexity_available(self) -> bool:
        """Check if Perplexity integration is available."""
        return self.search_web_enabled and bool(self.perplexity_key)

    # ==========================================================================
    # Numeric Limits
    # ==========================================================================

    request_timeout: int = Field(
        default=10,
        alias="REQUEST_TIMEOUT",
        description="HTTP request timeout in seconds",
    )
    poster_limit: int = Field(
        default=0,
        alias="POSTER_LIMIT",
        description="Max posters to download (0 = unlimited)",
    )
    poster_search_results: int = Field(
        default=2,
        description="Number of poster search results",
    )
    poster_workers: int = Field(
        default=8,
        alias="POSTER_WORKERS",
        description="Concurrent poster download workers",
    )
    film_limit: int = Field(
        default=200,
        alias="FILM_LIMIT",
        description="Maximum films to process per composer",
    )
    external_snippet_max_chars: int = Field(
        default=700,
        alias="EXTERNAL_SNIPPET_MAX_CHARS",
        description="Max characters for external snippets",
    )
    external_snippet_sources: int = Field(
        default=12,
        alias="EXTERNAL_SNIPPET_SOURCES",
        description="Number of external sources to fetch",
    )
    external_domain_results: int = Field(
        default=3,
        alias="EXTERNAL_DOMAIN_RESULTS",
        description="Results per external domain",
    )
    min_paragraph_len: int = Field(
        default=50,
        alias="MIN_PARAGRAPH_LEN",
        description="Minimum paragraph length to include",
    )
    max_bio_paragraphs: int = Field(
        default=6,
        alias="MAX_BIO_PARAGRAPHS",
        description="Maximum biography paragraphs",
    )
    top_min_vote_count: int = Field(
        default=50,
        alias="TOP_MIN_VOTE_COUNT",
        description="Minimum TMDB votes for Top 10 eligibility",
    )
    streaming_candidate_limit: int = Field(
        default=30,
        alias="STREAMING_CANDIDATE_LIMIT",
        description="Films to check for streaming signals",
    )

    # ==========================================================================
    # Model Settings
    # ==========================================================================

    pplx_model: str = Field(
        default="sonar",
        alias="PPLX_MODEL",
        description="Perplexity model to use",
    )
    translate_target: str = Field(
        default="es",
        alias="TRANSLATE_TARGET",
        description="Target language for translations",
    )

    # ==========================================================================
    # Cache Paths
    # ==========================================================================

    @property
    def tmdb_cache_path(self) -> Path:
        """Path to TMDB cache file."""
        return self.output_dir / "tmdb_cache.json"

    @property
    def streaming_cache_path(self) -> Path:
        """Path to streaming cache file."""
        return self.output_dir / "streaming_cache.json"

    # ==========================================================================
    # Logging
    # ==========================================================================

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level",
    )
    log_format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        description="Logging format string",
    )

    # ==========================================================================
    # Batch Processing
    # ==========================================================================

    start_index: int = Field(
        default=1,
        alias="START_INDEX",
        description="Start processing from this index",
    )
    end_index: Optional[int] = Field(
        default=None,
        alias="END_INDEX",
        description="Stop processing at this index",
    )
    batch_size: int = Field(
        default=10,
        alias="BATCH_SIZE",
        description="Batch size for processing",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings singleton.
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
