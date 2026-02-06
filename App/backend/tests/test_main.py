"""Tests for FastAPI main module."""

import pytest
from fastapi import HTTPException

from app.database import DatabaseError
from app.main import database_exception_handler, health_check, lifespan, root


class DummyDB:
    async def execute_query(self, query, params=(), fetch_one=False):
        return {"test": 1}


class FailingDB:
    async def execute_query(self, query, params=(), fetch_one=False):
        raise RuntimeError("db down")


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root returns status."""
    payload = await root()
    assert payload["status"] == "running"


@pytest.mark.asyncio
async def test_health_ok():
    """Test health check ok."""
    payload = await health_check(db=DummyDB())
    assert payload["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_error():
    """Test health check error path."""
    with pytest.raises(HTTPException):
        await health_check(db=FailingDB())


@pytest.mark.asyncio
async def test_database_exception_handler():
    """Test database exception handler response."""
    response = await database_exception_handler(None, DatabaseError("boom"))
    assert response.status_code == 500
    assert b"Database Error" in response.body


@pytest.mark.asyncio
async def test_lifespan_success(monkeypatch):
    """Test lifespan startup/shutdown success."""
    from app import main as main_module

    async def fake_init():
        return None

    monkeypatch.setattr(main_module.db_manager, "initialize", fake_init)
    async with lifespan(None):
        pass


@pytest.mark.asyncio
async def test_lifespan_failure(monkeypatch):
    """Test lifespan raises on init failure."""
    from app import main as main_module

    async def fake_init():
        raise DatabaseError("fail")

    monkeypatch.setattr(main_module.db_manager, "initialize", fake_init)
    with pytest.raises(DatabaseError):
        async with lifespan(None):
            pass


def test_main_entrypoint(monkeypatch):
    """Test __main__ block runs uvicorn."""
    import runpy
    import sys

    calls = {"ok": False}

    def fake_run(*args, **kwargs):
        calls["ok"] = True

    monkeypatch.setattr("app.main.uvicorn.run", fake_run)
    sys.modules.pop("app.main", None)
    runpy.run_module("app.main", run_name="__main__")
    assert calls["ok"] is True
