from src.providers.perplexity import PerplexityProvider


def test_perplexity_provider_parses_urls(monkeypatch) -> None:
    provider = PerplexityProvider(api_key="key")
    data = {
        "search_results": [
            {"url": "http://a.example"},
            {"url": "http://b.example"},
        ]
    }

    monkeypatch.setattr(provider, "_request", lambda *args, **kwargs: data)

    assert provider.search_urls("query", num_results=1) == ["http://a.example"]
