"""Application configuration."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings for Music Crawler."""

    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    jamendo_client_id: str | None = Field(default=None, alias="JAMENDO_CLIENT_ID")
    cache_ttl_days: int = Field(default=7, alias="CACHE_TTL_DAYS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str | None = Field(default=None, alias="LOG_FILE")


settings = Settings()
