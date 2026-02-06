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

    def test_health_check_reflects_enabled(self, monkeypatch) -> None:
        """health_check should reflect enabled flag."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key=None)
        assert client.health_check() is True

        monkeypatch.setattr(settings, "search_web_enabled", False)
        assert client.health_check() is False

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

    def test_search_perplexity_empty_falls_back(self, monkeypatch) -> None:
        """search should fall back when Perplexity returns empty."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        client._search_perplexity = Mock(return_value=[])
        client._search_chrome = Mock(return_value=["http://chrome"])

        assert client.search("query", num=1) == ["http://chrome"]

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

    def test_search_falls_back_to_google(self, monkeypatch) -> None:
        """search should fall back to Google when Chrome fails."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        monkeypatch.setattr(settings, "pplx_api_key", None)
        monkeypatch.setattr(settings, "perplexity_api_key", None)
        monkeypatch.setattr(SearchClient, "_search_chrome", lambda *_: [])
        monkeypatch.setattr(SearchClient, "_search_google", lambda *_: ["http://google"])
        client = SearchClient(perplexity_api_key=None)

        assert client.search("query", num=1) == ["http://google"]

    def test_search_returns_empty_when_all_fail(self, monkeypatch) -> None:
        """search should return empty when all providers fail."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        monkeypatch.setattr(settings, "pplx_api_key", None)
        monkeypatch.setattr(settings, "perplexity_api_key", None)
        monkeypatch.setattr(SearchClient, "_search_chrome", lambda *_: [])
        monkeypatch.setattr(SearchClient, "_search_google", lambda *_: [])
        client = SearchClient(perplexity_api_key=None)

        assert client.search("query", num=1) == []

    def test_search_google_dedupes(self, monkeypatch) -> None:
        """_search_google should dedupe results."""
        import sys
        import types

        def fake_search(*_args, **_kwargs):
            return ["http://a", "http://a", "http://b"]

        monkeypatch.setitem(sys.modules, "googlesearch", types.SimpleNamespace(search=fake_search))
        client = SearchClient(perplexity_api_key=None)

        assert client._search_google("query", num=3) == ["http://a", "http://b"]

    def test_search_google_handles_error(self, monkeypatch) -> None:
        """_search_google should handle errors."""
        import sys
        import types

        def fake_search(*_args, **_kwargs):
            raise Exception("boom")

        monkeypatch.setitem(sys.modules, "googlesearch", types.SimpleNamespace(search=fake_search))
        client = SearchClient(perplexity_api_key=None)

        assert client._search_google("query", num=2) == []

    def test_search_perplexity_returns_empty_without_key(self) -> None:
        """_search_perplexity should return empty without key."""
        settings.pplx_api_key = None
        settings.perplexity_api_key = None
        client = SearchClient(perplexity_api_key=None)
        assert client._search_perplexity("query", num=1) == []

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

    def test_search_perplexity_uses_search_results(self, monkeypatch) -> None:
        """_search_perplexity should extract search_results."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={"search_results": [{"url": "http://a"}, {"url": "http://b"}]}
        )
        client.session.post = Mock(return_value=response)

        result = client._search_perplexity("query", num=2)

        assert result == ["http://a", "http://b"]

    def test_search_perplexity_extracts_urls_from_content(self, monkeypatch) -> None:
        """_search_perplexity should extract URLs from content."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={"choices": [{"message": {"content": "See https://example.com."}}]}
        )
        client.session.post = Mock(return_value=response)

        result = client._search_perplexity("query", num=1)

        assert result == ["https://example.com"]

    def test_search_perplexity_handles_error(self, monkeypatch) -> None:
        """_search_perplexity should handle request errors."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        client.session.post = Mock(side_effect=Exception("boom"))

        assert client._search_perplexity("query", num=1) == []

    def test_fetch_url_text_blocks_domains(self) -> None:
        """fetch_url_text should skip blocked domains."""
        client = SearchClient(perplexity_api_key=None)

        result = client.fetch_url_text(
            "https://example.com/page",
            blocked_domains={"example.com"},
        )

        assert result == ""

    def test_fetch_url_text_handles_error(self) -> None:
        """fetch_url_text should return empty on request error."""
        client = SearchClient(perplexity_api_key=None)
        client.session.get = Mock(side_effect=Exception("boom"))

        assert client.fetch_url_text("https://example.com") == ""

    def test_fetch_url_text_success(self) -> None:
        """fetch_url_text should return response text on success."""
        client = SearchClient(perplexity_api_key=None)
        response = Mock()
        response.raise_for_status = Mock()
        response.text = "OK"
        client.session.get = Mock(return_value=response)

        assert client.fetch_url_text("https://example.com") == "OK"

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

    def test_extract_paragraphs_limits_and_min_length(self) -> None:
        """extract_paragraphs should respect limits and min length."""
        client = SearchClient(perplexity_api_key=None)
        html = """
        <html>
          <body>
            <p>Short.</p>
            <p>This is a longer paragraph with enough content to pass.</p>
            <p>Another long paragraph that should be included.</p>
          </body>
        </html>
        """

        paragraphs = client.extract_paragraphs(html, max_paragraphs=1, min_length=20)

        assert paragraphs == ["This is a longer paragraph with enough content to pass."]

    def test_extract_google_urls_skips_non_targets(self) -> None:
        """_extract_google_urls should skip invalid targets."""
        from soundtracker.clients.search import _extract_google_urls

        html = '<a href="/url?sa=U">bad</a><a href="/url?q=ftp://bad">bad2</a>'
        assert _extract_google_urls(html) == []

    def test_extract_google_urls_skips_non_http_links(self) -> None:
        """_extract_google_urls should skip non-http links."""
        from soundtracker.clients.search import _extract_google_urls

        html = '<a href="mailto:test@example.com">Mail</a>'
        assert _extract_google_urls(html) == []

    def test_extract_google_urls_dedupes_direct_links(self) -> None:
        """_extract_google_urls should dedupe direct links."""
        from soundtracker.clients.search import _extract_google_urls

        html = (
            '<a href="https://example.com/page">A</a>'
            '<a href="https://example.com/page">B</a>'
        )
        assert _extract_google_urls(html) == ["https://example.com/page"]

    def test_is_noise_text_internal_rules(self) -> None:
        """_is_noise_text should flag uppercase and long text."""
        client = SearchClient(perplexity_api_key=None)
        assert client._is_noise_text("THIS TEXT HAS MANY UPPER LETTERS HERE NOW")
        long_text = "word " * 25
        assert client._is_noise_text(long_text)

    def test_is_noise_text_returns_false_for_normal_text(self) -> None:
        """_is_noise_text should return False for normal text."""
        client = SearchClient(perplexity_api_key=None)
        assert client._is_noise_text("This is a normal sentence with mixed case.") is False

    def test_is_noise_text_handles_no_letters(self) -> None:
        """_is_noise_text should flag numeric text with no letters."""
        client = SearchClient(perplexity_api_key=None)
        text = "1 2 3 4 5 6 7 8 9 10"
        assert client._is_noise_text(text) is True

    def test_search_perplexity_handles_duplicates(self, monkeypatch) -> None:
        """_search_perplexity should skip duplicate or empty URLs."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={
                "search_results": [
                    {"url": "http://a"},
                    {"url": "http://a"},
                    {"url": None},
                ]
            }
        )
        client.session.post = Mock(return_value=response)

        assert client._search_perplexity("query", num=5) == ["http://a"]

    def test_search_perplexity_handles_duplicate_citations(self, monkeypatch) -> None:
        """_search_perplexity should dedupe citations."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"citations": ["http://a", "http://a"]})
        client.session.post = Mock(return_value=response)

        assert client._search_perplexity("query", num=5) == ["http://a"]

    def test_search_perplexity_handles_empty_choices(self, monkeypatch) -> None:
        """_search_perplexity should handle empty choices content."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"choices": []})
        client.session.post = Mock(return_value=response)

        assert client._search_perplexity("query", num=5) == []

    def test_search_perplexity_skips_duplicate_content_urls(self, monkeypatch) -> None:
        """_search_perplexity should dedupe URLs extracted from content."""
        monkeypatch.setattr(settings, "search_web_enabled", True)
        client = SearchClient(perplexity_api_key="key")
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": "See https://example.com and https://example.com again."
                        }
                    }
                ]
            }
        )
        client.session.post = Mock(return_value=response)

        assert client._search_perplexity("query", num=5) == ["https://example.com"]
