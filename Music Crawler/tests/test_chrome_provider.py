from types import SimpleNamespace

import src.providers.chrome as chrome
from src.providers.chrome import ChromeProvider


def test_chrome_provider_parses_dom(monkeypatch) -> None:
    html = '<a href="/url?q=http%3A%2F%2Fexample.com&sa=U">Result</a>'

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=html, stderr="")

    monkeypatch.setattr(chrome.subprocess, "run", fake_run)
    monkeypatch.setattr(chrome, "_find_chrome_binary", lambda: "/usr/bin/google-chrome")

    provider = ChromeProvider()
    urls = provider.search_urls("query", num_results=1)

    assert urls == ["http://example.com"]
