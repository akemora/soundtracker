"""Tests for soundtracker.clients.search."""

from unittest.mock import Mock

from soundtracker.clients.search import SearchClient
from soundtracker.config import settings


class TestSearchClient:
    """Tests for SearchClient."""

    def test_search_returns_empty_when_disabled(self, monkeypatch) -> None:
        """search should return empty list when disabled."""
        monkeypatch.setattr(settings, "search_web_enabled", False)
        client = SearchClient(perplexity_api_key=None)

        assert client.search("John Williams") == []

    def test_search_prefers_perplexity(self, monkeypatch) -> None:
        """search should return Perplexity results when available."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        client._search_perplexity = Mock(return_value=["http://a"])
        client._search_google = Mock(return_value=["http://b"])
        client._search_chrome = Mock(return_value=["http://c"])

        result = client.search("query", num=1)

        assert result == ["http://a"]
        client._search_google.assert_not_called()
        client._search_chrome.assert_not_called()

    def test_search_falls_back_to_chrome(self, monkeypatch) -> None:
        """search should fall back to Chrome when others fail."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        monkeypatch.setattr(settings, "pplx_api_key", None)
        monkeypatch.setattr(settings, "perplexity_api_key", None)
        monkeypatch.setattr(SearchClient, "_search_google", lambda *_: [])
        monkeypatch.setattr(SearchClient, "_search_chrome", lambda *_: ["http://chrome"])
        client = SearchClient(perplexity_api_key=None)

        result = client.search("query", num=1)

        assert result == ["http://chrome"]

    def test_search_perplexity_uses_citations(self, monkeypatch) -> None:
        """_search_perplexity should extract citations."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"citations": ["http://a", "http://b"]})
        client.session.post = Mock(return_value=response)

        result = client._search_perplexity("query", num=2)

        assert result == ["http://a", "http://b"]

    def test_fetch_url_text_blocks_domains(self) -> None:
        """fetch_url_text should skip blocked domains."""
        client = SearchClient(perplexity_api_key=None)

        result = client.fetch_url_text(
            "https://example.com/page",
            blocked_domains={"example.com"},
        )

        assert result == ""

    def test_extract_paragraphs_filters_noise(self) -> None:
        """extract_paragraphs should return only clean paragraphs."""
        client = SearchClient(perplexity_api_key=None)
        html = """
        <html>
          <body>
            <p>This is a valid paragraph about the composer and his work.</p>
            <p>Subscribe to our newsletter</p>
            <p>THIS IS ALL CAPS WITH TOO MANY WORDS IN IT</p>
          </body>
        </html>
        """

        paragraphs = client.extract_paragraphs(html, max_paragraphs=5, min_length=20)

        assert paragraphs == [
            "This is a valid paragraph about the composer and his work."
        ]
