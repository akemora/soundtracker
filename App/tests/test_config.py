"""Tests for soundtracker.config module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from soundtracker.config import Settings, get_settings


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
