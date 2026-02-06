"""Tests for search providers."""

import requests
import subprocess

from src.providers.base import SearchProvider
from src.providers.chrome import ChromeProvider, _build_search_url, _extract_google_urls, _find_chrome_binary
from src.providers.perplexity import PerplexityProvider
from src.core.rate_limiter import RateLimiter


def test_base_provider_wait_rate_limit(monkeypatch):
    class DummyProvider(SearchProvider):
        def search_urls(self, query, num_results=5, site_filter=None):
            return []

        def get_rate_limit(self):
            return 0.1

    provider = DummyProvider(rate_limiter=RateLimiter())
    calls = {"wait": 0}

    def fake_wait(name, delay):
        calls["wait"] += 1

    monkeypatch.setattr(provider.rate_limiter, "wait", fake_wait)
    provider.wait_rate_limit()
    assert calls["wait"] == 1


def test_base_provider_abstract_pass_lines():
    class DummyProvider(SearchProvider):
        def search_urls(self, query, num_results=5, site_filter=None):
            return super().search_urls(query, num_results=num_results, site_filter=site_filter)

        def get_rate_limit(self):
            return super().get_rate_limit()

    provider = DummyProvider(rate_limiter=RateLimiter())
    assert provider.search_urls("q") is None
    assert provider.get_rate_limit() is None


def test_find_chrome_binary(monkeypatch):
    monkeypatch.setattr("src.providers.chrome.shutil.which", lambda name: "/bin/chrome" if name == "google-chrome" else None)
    assert _find_chrome_binary() == "/bin/chrome"


def test_build_search_url():
    url = _build_search_url("test", site_filter="example.com")
    assert "site%3Aexample.com" in url


def test_extract_google_urls():
    html = '<a href="/url?q=https%3A%2F%2Fexample.com">x</a><a href="https://foo.com">y</a>'
    urls = _extract_google_urls(html)
    assert "https://example.com" in urls
    assert "https://foo.com" in urls


def test_chrome_provider_no_binary(monkeypatch):
    monkeypatch.setattr("src.providers.chrome._find_chrome_binary", lambda: None)
    provider = ChromeProvider()
    assert provider.search_urls("test") == []


def test_chrome_provider_success(monkeypatch):
    provider = ChromeProvider()
    provider.chrome_path = "/bin/chrome"

    class Proc:
        returncode = 0
        stdout = "<html></html>"
        stderr = ""

    monkeypatch.setattr("src.providers.chrome.subprocess.run", lambda *a, **k: Proc())
    monkeypatch.setattr("src.providers.chrome._extract_google_urls", lambda html: ["https://a.com", "https://b.com"])
    urls = provider.search_urls("test", num_results=1)
    assert urls == ["https://a.com"]


def test_chrome_provider_site_filter(monkeypatch):
    provider = ChromeProvider()
    provider.chrome_path = "/bin/chrome"

    class Proc:
        returncode = 0
        stdout = "<html></html>"
        stderr = ""

    monkeypatch.setattr("src.providers.chrome.subprocess.run", lambda *a, **k: Proc())
    monkeypatch.setattr(
        "src.providers.chrome._extract_google_urls",
        lambda html: ["https://example.com/a", "https://other.com/b"],
    )
    urls = provider.search_urls("test", num_results=5, site_filter="example.com")
    assert urls == ["https://example.com/a"]


def test_chrome_provider_error(monkeypatch):
    provider = ChromeProvider()
    provider.chrome_path = "/bin/chrome"

    class Proc:
        returncode = 1
        stdout = ""
        stderr = "fail"

    monkeypatch.setattr("src.providers.chrome.subprocess.run", lambda *a, **k: Proc())
    assert provider.search_urls("test") == []


def test_chrome_provider_timeout(monkeypatch):
    provider = ChromeProvider()
    provider.chrome_path = "/bin/chrome"
    monkeypatch.setattr(
        "src.providers.chrome.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd="c", timeout=1)),
    )
    assert provider.search_urls("test") == []


def test_chrome_provider_exception(monkeypatch):
    provider = ChromeProvider()
    provider.chrome_path = "/bin/chrome"
    monkeypatch.setattr("src.providers.chrome.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert provider.search_urls("test") == []


def test_perplexity_request_no_key(monkeypatch):
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    provider = PerplexityProvider(api_key=None)
    assert provider._request("test") is None


def test_perplexity_request_http_errors(monkeypatch):
    provider = PerplexityProvider(api_key="key")

    class DummyResponse:
        def __init__(self, status):
            self.status_code = status

        def raise_for_status(self):
            raise requests.HTTPError(response=self)

    monkeypatch.setattr(provider.session, "post", lambda *a, **k: DummyResponse(401))
    assert provider._request("q") is None

    monkeypatch.setattr(provider.session, "post", lambda *a, **k: DummyResponse(403))
    assert provider._request("q") is None

    monkeypatch.setattr(provider.session, "post", lambda *a, **k: DummyResponse(429))
    assert provider._request("q") is None

    monkeypatch.setattr(provider.session, "post", lambda *a, **k: DummyResponse(500))
    assert provider._request("q") is None


def test_perplexity_request_timeout(monkeypatch):
    provider = PerplexityProvider(api_key="key")
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: (_ for _ in ()).throw(requests.Timeout()))
    assert provider._request("q") is None


def test_perplexity_request_error(monkeypatch):
    provider = PerplexityProvider(api_key="key")
    monkeypatch.setattr(provider.session, "post", lambda *a, **k: (_ for _ in ()).throw(requests.RequestException()))
    assert provider._request("q") is None


def test_perplexity_request_site_filter(monkeypatch):
    provider = PerplexityProvider(api_key="key")

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {}

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["payload"] = json
        return DummyResponse()

    monkeypatch.setattr(provider.session, "post", fake_post)
    provider._request("my query", site_filter="example.com")
    assert "site:example.com" in captured["payload"]["messages"][1]["content"]


def test_perplexity_search_urls_sources(monkeypatch):
    provider = PerplexityProvider(api_key="key")
    monkeypatch.setattr(provider, "_request", lambda *a, **k: {"search_results": [{"url": "https://a.com"}]})
    assert provider.search_urls("q") == ["https://a.com"]

    monkeypatch.setattr(provider, "_request", lambda *a, **k: {"citations": ["https://b.com"]})
    assert provider.search_urls("q") == ["https://b.com"]

    monkeypatch.setattr(provider, "_request", lambda *a, **k: {"choices": [{"message": {"content": "https://\\SSS"}}]})
    assert provider.search_urls("q") == ["https://\\SSS"]


def test_perplexity_search_urls_no_data(monkeypatch):
    provider = PerplexityProvider(api_key="key")
    monkeypatch.setattr(provider, "_request", lambda *a, **k: None)
    assert provider.search_urls("q") == []
