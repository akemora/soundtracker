"""Pytest configuration and fixtures for backend tests.

This module provides shared test fixtures including database setup,
test client configuration, and sample data.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
import os
os.environ["DATABASE_URL"] = str(Path(__file__).parent.parent.parent / "data" / "soundtrackers.db")

from app.database import DatabaseManager, db_manager
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def sync_client() -> Generator[TestClient, None, None]:
    """Create synchronous test client for simple tests."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for async endpoint tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[DatabaseManager, None]:
    """Provide database manager for direct database tests."""
    await db_manager.initialize()
    yield db_manager


@pytest.fixture
def sample_composer_slug() -> str:
    """Provide a known composer slug for testing."""
    return "john_williams"


@pytest.fixture
def sample_search_query() -> str:
    """Provide a sample search query for testing."""
    return "John Williams"
