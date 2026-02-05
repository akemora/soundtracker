from src.providers.duckduckgo import DuckDuckGoProvider
import src.providers.duckduckgo as ddg


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_duckduckgo_provider_parses_html(monkeypatch) -> None:
    html = (
        '<a class="result__a" '
        'href="https://duckduckgo.com/l/?uddg=http%3A%2F%2Fexample.com">'
        "Example"
        "</a>"
    )

    monkeypatch.setattr(ddg.requests, "get", lambda *args, **kwargs: DummyResponse(html))

    provider = DuckDuckGoProvider()
    urls = provider.search_urls("query", num_results=1)

    assert urls == ["http://example.com"]
