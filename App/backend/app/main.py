"""SOUNDTRACKER FastAPI application main module.

This module sets up the FastAPI application with CORS support, database initialization,
routing, error handling, and API documentation for the film composer encyclopedia.
"""

from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import DatabaseError, DatabaseManager, db_manager, get_database
from .routers import assets_router, batch_router, composers_router, music_router, search_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: FastAPI application instance.
    """
    # Startup
    try:
        await db_manager.initialize()
        print(f"Database initialized: {settings.database_url}")
    except DatabaseError as e:
        print(f"Database initialization failed: {e}")
        raise

    yield

    # Shutdown
    print("Shutting down SOUNDTRACKER API")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Film composer encyclopedia API with full-text search capabilities",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request,  # noqa: ARG001
    exc: DatabaseError,
) -> JSONResponse:
    """Handle database errors with proper HTTP responses."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": str(exc),
            "type": "database_error",
        },
    )


# =============================================================================
# Root and Health Endpoints
# =============================================================================


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """API root endpoint with basic information.

    Returns:
        Dict containing API name and version.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check(
    db: DatabaseManager = Depends(get_database),
) -> dict[str, Any]:
    """Health check endpoint with database connectivity test.

    Args:
        db: Database manager dependency.

    Returns:
        Health status information.

    Raises:
        HTTPException: If health check fails.
    """
    try:
        await db.execute_query("SELECT 1 as test", fetch_one=True)

        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.app_version,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {e}") from e


# =============================================================================
# Include API Routers
# =============================================================================

app.include_router(composers_router)
app.include_router(search_router)
app.include_router(assets_router)
app.include_router(batch_router)
app.include_router(music_router)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
