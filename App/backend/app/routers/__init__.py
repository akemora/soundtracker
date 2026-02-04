"""API routers for the SOUNDTRACKER API.

This package exports all API routers for registration with the FastAPI app.
"""

from .assets import router as assets_router
from .batch import router as batch_router
from .composers import router as composers_router
from .search import router as search_router

__all__ = [
    "composers_router",
    "search_router",
    "assets_router",
    "batch_router",
]
