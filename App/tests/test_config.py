"""Tests for soundtracker.config module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from soundtracker.config import Settings, _disable_dotenv, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self):
        """Test default setting values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.request_timeout == 10
            assert settings.poster_limit == 0
            assert settings.poster_workers == 8
            assert settings.film_limit == 200
            assert settings.download_posters is True
            assert settings.search_web_enabled is True

    def test_output_dir_default(self):
        """Test output_dir defaults to outputs folder."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.output_dir.name == "outputs"

    def test_cache_paths(self):
        """Test cache path properties."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.tmdb_cache_path.name == "tmdb_cache.json"
            assert settings.streaming_cache_path.name == "streaming_cache.json"

    def test_api_availability_without_keys(self):
        """Test API availability when keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert not settings.is_tmdb_available
            assert not settings.is_youtube_available
            assert not settings.is_spotify_available

    def test_tmdb_available_with_key(self):
        """Test TMDB availability with key."""
        with patch.dict(os.environ, {"TMDB_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            assert settings.is_tmdb_available

    def test_youtube_available_with_key(self):
        """Test YouTube availability with key."""
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "test_key"}, clear=True):
            settings = Settings()
            assert settings.is_youtube_available

    def test_spotify_available_with_credentials(self):
        """Test Spotify availability with full credentials."""
        with patch.dict(os.environ, {
            "SPOTIFY_CLIENT_ID": "client_id",
            "SPOTIFY_CLIENT_SECRET": "client_secret",
        }, clear=True):
            settings = Settings()
            assert settings.is_spotify_available

    def test_spotify_unavailable_partial_credentials(self):
        """Test Spotify unavailable with partial credentials."""
        with patch.dict(os.environ, {"SPOTIFY_CLIENT_ID": "client_id"}, clear=True):
            settings = Settings()
            assert not settings.is_spotify_available

    def test_perplexity_key_fallback(self):
        """Test Perplexity key from either env var."""
        with patch.dict(os.environ, {"PPLX_API_KEY": "key1"}, clear=True):
            settings = Settings()
            assert settings.perplexity_key == "key1"

        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "key2"}, clear=True):
            settings = Settings()
            assert settings.perplexity_key == "key2"

    def test_log_level_default(self):
        """Test default log level."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.log_level == "INFO"

    def test_log_level_override(self):
        """Test log level override."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_batch_processing_defaults(self):
        """Test batch processing defaults."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.start_index == 1
            assert settings.end_index is None
            assert settings.batch_size == 10

    def test_start_index_override(self):
        """Test start_index override."""
        with patch.dict(os.environ, {"START_INDEX": "5"}, clear=True):
            settings = Settings()
            assert settings.start_index == 5


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        # Clear the cache first
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caching(self):
        """Test that get_settings is cached."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Same instance due to caching
        assert settings1 is settings2


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        with patch.dict(os.environ, {"DOWNLOAD_POSTERS": "0"}, clear=True):
            settings = Settings()
            assert settings.download_posters is False

        with patch.dict(os.environ, {"DOWNLOAD_POSTERS": "1"}, clear=True):
            settings = Settings()
            assert settings.download_posters is True

    def test_integer_parsing(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {"POSTER_LIMIT": "50"}, clear=True):
            settings = Settings()
            assert settings.poster_limit == 50

    def test_api_endpoints(self):
        """Test API endpoint defaults."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert "themoviedb.org" in settings.tmdb_api_url
            assert "image.tmdb.org" in settings.tmdb_image_url
            assert "perplexity.ai" in settings.pplx_api_url

    def test_imdb_paths_default(self, tmp_path):
        """Test imdb paths derived from base_dir."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(base_dir=tmp_path)
            assert settings.imdb_data_dir == tmp_path / "data" / "imdb_data"
            assert settings.imdb_db_path == tmp_path / "data" / "imdb_data" / "imdb.sqlite"

    def test_paths_override(self, tmp_path):
        """Test path overrides."""
        custom_output = tmp_path / "out"
        custom_imdb = tmp_path / "imdb"
        custom_db = tmp_path / "imdb.sqlite"
        with patch.dict(
            os.environ,
            {"IMDB_DATA_DIR": str(custom_imdb), "IMDB_DB_PATH": str(custom_db)},
            clear=True,
        ):
            settings = Settings(base_dir=tmp_path, output_dir=custom_output)
            assert settings.output_dir == custom_output
            assert settings.imdb_data_dir == custom_imdb
            assert settings.imdb_db_path == custom_db

    def test_imdb_available(self, tmp_path):
        """Test imdb availability when file exists."""
        imdb_dir = tmp_path / "data" / "imdb_data"
        imdb_dir.mkdir(parents=True)
        db_path = imdb_dir / "imdb.sqlite"
        db_path.write_text("test")
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(base_dir=tmp_path)
            assert settings.is_imdb_available is True

    def test_perplexity_available_flag(self):
        """Test perplexity availability respects flags."""
        with patch.dict(os.environ, {"PPLX_API_KEY": "key"}, clear=True):
            settings = Settings()
            assert settings.is_perplexity_available
        with patch.dict(os.environ, {"PPLX_API_KEY": "key", "SEARCH_WEB_ENABLED": "0"}, clear=True):
            settings = Settings()
            assert not settings.is_perplexity_available


class TestDotenvBehavior:
    """Tests for dotenv disabling behavior."""

    def test_disable_dotenv_env_flag(self):
        """Test explicit disable flag."""
        with patch.dict(os.environ, {"SOUNDTRACKER_DISABLE_DOTENV": "1"}, clear=True):
            assert _disable_dotenv() is True

    def test_disable_dotenv_in_pytest(self, monkeypatch):
        """Test pytest detection disables dotenv."""
        with patch.dict(os.environ, {}, clear=True):
            assert _disable_dotenv() is True

    def test_settings_customise_sources(self, monkeypatch):
        """Test settings sources omit dotenv when disabled."""
        with patch.dict(os.environ, {"SOUNDTRACKER_DISABLE_DOTENV": "1"}, clear=True):
            sources = Settings.settings_customise_sources(
                Settings,
                init_settings="init",
                env_settings="env",
                dotenv_settings="dotenv",
                file_secret_settings="secrets",
            )
            assert sources == ("init", "env", "secrets")

    def test_settings_customise_sources_includes_dotenv(self, monkeypatch):
        """Test settings sources include dotenv when enabled."""
        with patch.dict(os.environ, {}, clear=True):
            # Temporarily remove pytest indicator
            import sys
            original_pytest = sys.modules.pop("pytest", None)
            try:
                sources = Settings.settings_customise_sources(
                    Settings,
                    init_settings="init",
                    env_settings="env",
                    dotenv_settings="dotenv",
                    file_secret_settings="secrets",
                )
                assert sources == ("init", "env", "dotenv", "secrets")
            finally:
                if original_pytest is not None:
                    sys.modules["pytest"] = original_pytest


def test_set_imdb_db_path_fallback():
    """Test imdb_db_path fallback uses base_dir when imdb_data_dir missing."""
    class DummyInfo:
        data = {"base_dir": Path("/tmp/base")}

    value = Settings.set_imdb_db_path(None, DummyInfo())
    assert value == Path("/tmp/base") / "data" / "imdb_data" / "imdb.sqlite"
