"""Tests for soundtracker.clients.base."""

from __future__ import annotations

from unittest.mock import Mock

import requests

from soundtracker.clients.base import BaseClient


class DummyClient(BaseClient):
    """Concrete client for BaseClient tests."""

    def health_check(self) -> bool:  # pragma: no cover - trivial override
        return True


def test_get_success() -> None:
    """_get should return JSON payload on success."""
    client = DummyClient(base_url="https://example.com")
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"ok": True})
    client.session.get = Mock(return_value=response)

    assert client._get("/ping") == {"ok": True}
    client.session.get.assert_called_once()


def test_get_http_error_returns_none() -> None:
    """_get should return None on HTTP errors."""
    client = DummyClient(base_url="https://example.com")
    response = Mock()
    response.raise_for_status = Mock(
        side_effect=requests.HTTPError(response=Mock(status_code=500))
    )
    client.session.get = Mock(return_value=response)

    assert client._get("/ping") is None


def test_get_request_exception_returns_none() -> None:
    """_get should return None on request exceptions."""
    client = DummyClient(base_url="https://example.com")
    client.session.get = Mock(side_effect=requests.RequestException("boom"))

    assert client._get("/ping") is None


def test_post_success() -> None:
    """_post should return JSON payload on success."""
    client = DummyClient(base_url="https://example.com")
    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"ok": True})
    client.session.post = Mock(return_value=response)

    assert client._post("/ping", data={"a": "b"}) == {"ok": True}
    client.session.post.assert_called_once()


def test_post_request_exception_returns_none() -> None:
    """_post should return None on request exceptions."""
    client = DummyClient(base_url="https://example.com")
    client.session.post = Mock(side_effect=requests.RequestException("boom"))

    assert client._post("/ping", json_data={"a": "b"}) is None


def test_context_manager_closes_session() -> None:
    """__enter__/__exit__ should close the session."""
    client = DummyClient(base_url="https://example.com")
    client.close = Mock()

    with client:
        pass

    client.close.assert_called_once()


def test_health_check_base_abstract_executes() -> None:
    """BaseClient.health_check can be invoked via class to cover abstract line."""
    client = DummyClient(base_url="https://example.com")
    assert BaseClient.health_check(client) is None


def test_close_calls_session_close() -> None:
    """close should close underlying session."""
    client = DummyClient(base_url="https://example.com")
    client.session.close = Mock()
    client.close()
    client.session.close.assert_called_once()
