"""Application configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings for Music Crawler."""

    model_config = SettingsConfigDict(env_prefix="MUSIC_CRAWLER_", case_sensitive=False)


settings = Settings()
