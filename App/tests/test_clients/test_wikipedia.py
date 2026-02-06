"""Tests for soundtracker.clients.wikipedia."""

from unittest.mock import Mock

from soundtracker.clients.wikipedia import MultiLangWikipediaClient, WikipediaClient


class TestWikipediaClient:
    """Tests for WikipediaClient."""

    def test_health_check_returns_true_on_response(self) -> None:
        """Health check should return True when API responds."""
        client = WikipediaClient()
        client._get = Mock(return_value={})

        assert client.health_check() is True

    def test_health_check_returns_false_on_failure(self) -> None:
        """Health check should return False when API fails."""
        client = WikipediaClient()
        client._get = Mock(return_value=None)

        assert client.health_check() is False

    def test_search_title_returns_none_when_no_results(self) -> None:
        """Search title should return None on empty results."""
        client = WikipediaClient()
        client._get = Mock(return_value={"query": {"search": []}})

        assert client.search_title("Missing") is None

    def test_search_title_returns_none_on_missing_data(self) -> None:
        """Search title should return None when data missing."""
        client = WikipediaClient()
        client._get = Mock(return_value=None)

        assert client.search_title("Missing") is None

    def test_search_title_returns_first_title(self) -> None:
        """Search title should return the first search result title."""
        client = WikipediaClient()
        client._get = Mock(
            return_value={"query": {"search": [{"title": "John Williams"}]}}
        )

        assert client.search_title("John Williams") == "John Williams"

    def test_get_extract_returns_text(self) -> None:
        """Get extract should return the extracted text."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(
            return_value={
                "query": {"pages": {"123": {"extract": "Sample extract"}}}
            }
        )

        assert client.get_extract("John Williams") == "Sample extract"

    def test_get_extract_returns_empty_when_missing(self) -> None:
        """Get extract should return empty string when not found."""
        client = WikipediaClient()
        client.search_title = Mock(return_value=None)

        assert client.get_extract("Missing") == ""

    def test_get_extract_returns_empty_when_no_pages(self) -> None:
        """Get extract should return empty when no pages."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value={"query": {"pages": {}}})

        assert client.get_extract("John Williams") == ""

    def test_get_extract_returns_empty_when_data_missing(self) -> None:
        """Get extract should return empty when data missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value=None)

        assert client.get_extract("John Williams") == ""

    def test_get_extract_returns_empty_when_extract_missing(self) -> None:
        """Get extract should return empty when extract missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value={"query": {"pages": {"1": {"extract": ""}}}})

        assert client.get_extract("John Williams") == ""

    def test_get_extract_respects_intro_only_false(self) -> None:
        """Get extract should work when intro_only is False."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(
            return_value={
                "query": {"pages": {"123": {"extract": "Full extract"}}}
            }
        )

        assert client.get_extract("John Williams", intro_only=False) == "Full extract"

    def test_get_image_url_returns_original(self) -> None:
        """Get image URL should return original image source."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(
            return_value={
                "query": {"pages": {"123": {"original": {"source": "http://img"}}}}
            }
        )

        assert client.get_image_url("John Williams") == "http://img"

    def test_get_image_url_returns_none_when_missing(self) -> None:
        """Get image URL should return None when missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value=None)

        assert client.get_image_url("John Williams") is None

    def test_get_image_url_returns_none_when_no_title(self) -> None:
        """Get image URL should return None when title missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value=None)

        assert client.get_image_url("Missing") is None

    def test_get_image_url_returns_none_when_source_missing(self) -> None:
        """Get image URL should return None when source missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value={"query": {"pages": {"1": {"original": {}}}}})

        assert client.get_image_url("John Williams") is None

    def test_get_infobox_image_returns_thumbnail(self) -> None:
        """Get infobox image should return thumbnail source."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(
            return_value={
                "query": {"pages": {"123": {"thumbnail": {"source": "http://thumb"}}}}
            }
        )

        assert client.get_infobox_image("John Williams") == "http://thumb"

    def test_get_infobox_image_returns_none_when_missing(self) -> None:
        """Get infobox image should return None when missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value={"query": {"pages": {}}})

        assert client.get_infobox_image("John Williams") is None

    def test_get_infobox_image_returns_none_when_source_missing(self) -> None:
        """Get infobox image should return None when source missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value={"query": {"pages": {"1": {"thumbnail": {}}}}})

        assert client.get_infobox_image("John Williams") is None

    def test_get_infobox_image_returns_none_when_data_missing(self) -> None:
        """Get infobox image should return None when data missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client._get = Mock(return_value=None)

        assert client.get_infobox_image("John Williams") is None

    def test_get_infobox_image_returns_none_when_no_title(self) -> None:
        """Get infobox image should return None when title missing."""
        client = WikipediaClient()
        client.search_title = Mock(return_value=None)

        assert client.get_infobox_image("Missing") is None

    def test_fetch_html_returns_content(self) -> None:
        """Fetch HTML should return response text on success."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        response = Mock()
        response.raise_for_status = Mock()
        response.text = "<html>ok</html>"
        client.session.get = Mock(return_value=response)

        assert client.fetch_html("John Williams") == "<html>ok</html>"

    def test_fetch_html_returns_none_when_missing_title(self) -> None:
        """Fetch HTML should return None when no title found."""
        client = WikipediaClient()
        client.search_title = Mock(return_value=None)

        assert client.fetch_html("Missing") is None

    def test_fetch_html_handles_error(self) -> None:
        """Fetch HTML should return None on request error."""
        client = WikipediaClient()
        client.search_title = Mock(return_value="John Williams")
        client.session.get = Mock(side_effect=Exception("boom"))

        assert client.fetch_html("John Williams") is None


class TestMultiLangWikipediaClient:
    """Tests for MultiLangWikipediaClient."""

    def test_search_title_returns_first_language_hit(self) -> None:
        """Search title should return the first language that matches."""
        client = MultiLangWikipediaClient(["es", "en"])
        client.clients["es"].search_title = Mock(return_value=None)
        client.clients["en"].search_title = Mock(return_value="John Williams")

        title, lang = client.search_title("John Williams")

        assert title == "John Williams"
        assert lang == "en"

    def test_search_title_returns_none_when_missing(self) -> None:
        """Search title should return (None, None) when missing."""
        client = MultiLangWikipediaClient(["es"])
        client.clients["es"].search_title = Mock(return_value=None)

        assert client.search_title("Missing") == (None, None)

    def test_get_extract_returns_first_available(self) -> None:
        """get_extract should return first non-empty extract."""
        client = MultiLangWikipediaClient(["es", "en"])
        client.clients["es"].get_extract = Mock(return_value="")
        client.clients["en"].get_extract = Mock(return_value="Extract")

        assert client.get_extract("John Williams") == "Extract"

    def test_get_image_url_returns_first_available(self) -> None:
        """get_image_url should return first available image."""
        client = MultiLangWikipediaClient(["es", "en"])
        client.clients["es"].get_image_url = Mock(return_value=None)
        client.clients["en"].get_image_url = Mock(return_value="http://img")

        assert client.get_image_url("John Williams") == "http://img"

    def test_get_extract_returns_empty_when_missing(self) -> None:
        """get_extract should return empty when no languages match."""
        client = MultiLangWikipediaClient(["es", "en"])
        client.clients["es"].get_extract = Mock(return_value="")
        client.clients["en"].get_extract = Mock(return_value="")

        assert client.get_extract("Missing") == ""

    def test_get_image_url_returns_none_when_missing(self) -> None:
        """get_image_url should return None when no languages match."""
        client = MultiLangWikipediaClient(["es", "en"])
        client.clients["es"].get_image_url = Mock(return_value=None)
        client.clients["en"].get_image_url = Mock(return_value=None)

        assert client.get_image_url("Missing") is None
