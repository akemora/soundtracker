"""Tests for chrome fallback in SearchClient."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import subprocess

from soundtracker.clients.search import SearchClient, _extract_google_urls, _find_chrome_binary


def test_find_chrome_binary_first_match(monkeypatch) -> None:
    calls = []

    def fake_which(name: str):
        calls.append(name)
        return "/usr/bin/chrome" if name == "google-chrome" else None

    monkeypatch.setattr("soundtracker.clients.search.shutil.which", fake_which)
    assert _find_chrome_binary() == "/usr/bin/chrome"
    assert "google-chrome" in calls


def test_find_chrome_binary_returns_none(monkeypatch) -> None:
    """_find_chrome_binary should return None when no candidates exist."""

    def fake_which(_name: str):
        return None

    monkeypatch.setattr("soundtracker.clients.search.shutil.which", fake_which)
    assert _find_chrome_binary() is None


def test_extract_google_urls_parses_results() -> None:
    html = """
    <html>
      <body>
        <a href="/url?q=https://example.com&sa=U">Result</a>
        <a href="https://another.com/page">Other</a>
        <a href="https://www.google.com/search?q=test">Google</a>
      </body>
    </html>
    """
    urls = _extract_google_urls(html)
    assert "https://example.com" in urls
    assert "https://another.com/page" in urls
    assert all("google.com" not in url for url in urls)


def test_search_chrome_success(monkeypatch) -> None:
    client = SearchClient(perplexity_api_key=None)
    client._chrome_path = "/usr/bin/chrome"

    result = SimpleNamespace(
        returncode=0,
        stdout='<a href="/url?q=https://example.com&sa=U">ok</a>',
        stderr="",
    )
    monkeypatch.setattr("soundtracker.clients.search.subprocess.run", Mock(return_value=result))

    urls = client._search_chrome("query", num=1)
    assert urls == ["https://example.com"]


def test_search_chrome_returncode_failure(monkeypatch) -> None:
    client = SearchClient(perplexity_api_key=None)
    client._chrome_path = "/usr/bin/chrome"

    result = SimpleNamespace(returncode=1, stdout="", stderr="fail")
    monkeypatch.setattr("soundtracker.clients.search.subprocess.run", Mock(return_value=result))

    assert client._search_chrome("query", num=1) == []


def test_search_chrome_timeout(monkeypatch) -> None:
    client = SearchClient(perplexity_api_key=None)
    client._chrome_path = "/usr/bin/chrome"

    def raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="chrome", timeout=1)

    monkeypatch.setattr("soundtracker.clients.search.subprocess.run", raise_timeout)
    assert client._search_chrome("query", num=1) == []


def test_search_chrome_disabled_when_no_binary() -> None:
    client = SearchClient(perplexity_api_key=None)
    client._chrome_path = None
    assert client._search_chrome("query", num=1) == []


def test_search_chrome_handles_exception(monkeypatch) -> None:
    """_search_chrome should handle unexpected exceptions."""
    client = SearchClient(perplexity_api_key=None)
    client._chrome_path = "/usr/bin/chrome"

    monkeypatch.setattr(
        "soundtracker.clients.search.subprocess.run",
        Mock(side_effect=Exception("boom")),
    )

    assert client._search_chrome("query", num=1) == []
