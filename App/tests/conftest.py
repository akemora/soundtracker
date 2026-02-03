"""Pytest configuration and shared fixtures.

This module provides fixtures that are available to all tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_composer_data() -> dict:
    """Return sample composer data for testing."""
    return {
        "name": "John Williams",
        "slug": "john_williams",
        "birth_year": 1932,
        "nationality": "American",
    }


@pytest.fixture
def sample_film_data() -> dict:
    """Return sample film data for testing."""
    return {
        "title_original": "Star Wars",
        "title_es": "La guerra de las galaxias",
        "year": 1977,
        "tmdb_id": 11,
    }


@pytest.fixture
def sample_award_data() -> dict:
    """Return sample award data for testing."""
    return {
        "award_name": "Academy Award",
        "year": 1978,
        "film_title": "Star Wars",
        "status": "Win",
    }
