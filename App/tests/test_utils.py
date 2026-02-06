"""Tests for soundtracker.utils module."""

from pathlib import Path
from unittest.mock import Mock
import tempfile

import pytest
import requests

from soundtracker.utils.text import (
    clean_text,
    count_spanish_chars,
    extract_year,
    format_film_title,
    has_spanish_chars,
    is_noise_text,
    normalize_key,
    normalize_title,
    poster_filename,
    slugify,
    truncate_text,
)
from soundtracker.utils.urls import (
    build_wikipedia_url,
    clean_redirect_url,
    extract_domain,
    extract_urls_from_text,
    format_link,
    fetch_url_text,
    is_blocked_domain,
    is_image_url,
    is_wikipedia_url,
    normalize_wikipedia_url,
)


class TestSlugify:
    """Tests for slugify function."""

    def test_basic(self):
        """Test basic slug generation."""
        assert slugify("John Williams") == "john_williams"
        assert slugify("Hans Zimmer") == "hans_zimmer"

    def test_special_chars(self):
        """Test with special characters."""
        assert slugify("Ennio Morricone") == "ennio_morricone"
        assert slugify("Test!@#$%Name") == "test_name"

    def test_empty(self):
        """Test empty input."""
        assert slugify("") == "composer"
        assert slugify("   ") == "composer"

    def test_unicode(self):
        """Test with unicode characters."""
        # Unicode chars are stripped, leaving underscores
        result = slugify("José García")
        assert "jose" in result or "jos" in result or result == "compositor"


class TestCleanText:
    """Tests for clean_text function."""

    def test_basic(self):
        """Test basic text cleaning."""
        assert clean_text("Hello  World") == "Hello World"
        assert clean_text("  Test  ") == "Test"

    def test_punctuation(self):
        """Test punctuation spacing."""
        assert clean_text("Hello , world") == "Hello, world"
        assert clean_text("Test . Next") == "Test. Next"

    def test_newlines(self):
        """Test newline handling."""
        assert clean_text("Line1\nLine2") == "Line1 Line2"
        assert clean_text("Line1\n\n\nLine2") == "Line1 Line2"


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_short_text(self):
        """Test text shorter than max."""
        assert truncate_text("Hello", 10) == "Hello"

    def test_truncation(self):
        """Test text truncation at word boundary."""
        result = truncate_text("Hello World Test", 12)
        assert result.endswith("...")
        assert len(result) <= 15  # 12 + "..."

    def test_exact_boundary(self):
        """Test truncation at exact boundary."""
        result = truncate_text("Hello World", 11)
        assert result == "Hello World"


class TestIsNoiseText:
    """Tests for is_noise_text function."""

    def test_normal_text(self):
        """Test normal text is not noise."""
        assert not is_noise_text("This is normal text about a composer.")

    def test_all_caps(self):
        """Test all caps detection."""
        assert is_noise_text("THIS IS ALL CAPS WITH MORE THAN EIGHT WORDS IN IT")

    def test_upper_ratio_detection(self):
        """Test upper ratio detection."""
        assert is_noise_text("THIS TEXT HAS MANY UPPER WORDS HERE NOW")

    def test_long_no_punctuation(self):
        """Test long text without punctuation."""
        text = (
            "This text has many words and keeps going without punctuation to ensure "
            "the heuristic triggers on long paragraphs with no dots or commas at all"
        )
        assert is_noise_text(text)

    def test_numeric_all_caps_branch(self):
        """Test numeric text hits all-caps branch without letters."""
        text = "1 2 3 4 5 6 7 8 9 10"
        assert is_noise_text(text)

    def test_noise_keywords(self):
        """Test noise keyword detection."""
        assert is_noise_text("Please subscribe to our newsletter for updates")
        assert is_noise_text("Accept cookies to continue browsing")


class TestNormalizeTitle:
    """Tests for normalize_title function."""

    def test_basic(self):
        """Test basic title normalization."""
        assert normalize_title("Star Wars") == "Star Wars"

    def test_numbered(self):
        """Test numbered prefix removal."""
        assert normalize_title("1. Star Wars") == "Star Wars"
        assert normalize_title("10. The Matrix") == "The Matrix"

    def test_year_removal(self):
        """Test year removal."""
        assert normalize_title("Star Wars (1977)") == "Star Wars"

    def test_invalid(self):
        """Test invalid titles return None."""
        assert normalize_title("") is None
        assert normalize_title("A") is None
        assert normalize_title("x" * 100) is None


class TestNormalizeKey:
    """Tests for normalize_key function."""

    def test_basic(self):
        """Test basic key normalization."""
        assert normalize_key("Star Wars") == "starwars"
        assert normalize_key("The Matrix") == "thematrix"

    def test_special_chars(self):
        """Test special character removal."""
        assert normalize_key("Star Wars: A New Hope") == "starwarsanewhope"


class TestPosterFilename:
    """Tests for poster_filename function."""

    def test_basic(self):
        """Test basic filename generation."""
        assert poster_filename("Star Wars") == "poster_star_wars.jpg"

    def test_with_year(self):
        """Test filename with year."""
        assert poster_filename("Star Wars", 1977) == "poster_star_wars_1977.jpg"

    def test_empty(self):
        """Test empty title."""
        assert poster_filename("") == "poster_poster.jpg"

    def test_blank_title_hits_composer_branch(self):
        """Test blank title triggers composer fallback."""
        assert poster_filename("   ") == "poster_poster.jpg"


class TestFormatFilmTitle:
    """Tests for format_film_title function."""

    def test_same_titles(self):
        """Test when titles are the same."""
        result = format_film_title("Star Wars", "Star Wars")
        assert result == "Star Wars"

    def test_different_titles(self):
        """Test when titles differ."""
        result = format_film_title("Star Wars", "La Guerra de las Galaxias")
        assert "Star Wars" in result
        assert "La Guerra de las Galaxias" in result

    def test_only_original(self):
        """Test with only original title."""
        assert format_film_title("Star Wars") == "Star Wars"

    def test_only_spanish(self):
        """Test with only Spanish title."""
        assert format_film_title("", "La Guerra") == "La Guerra"


class TestExtractYear:
    """Tests for extract_year function."""

    def test_basic(self):
        """Test basic year extraction."""
        assert extract_year("Released in 1977") == 1977
        assert extract_year("Film from 2020") == 2020

    def test_no_year(self):
        """Test no year found."""
        assert extract_year("No year here") is None

    def test_invalid_year(self):
        """Test invalid year range."""
        assert extract_year("Year 1800") is None
        assert extract_year("Year 2100") is None
        assert extract_year("Year 2031") is None


class TestHasSpanishChars:
    """Tests for has_spanish_chars function."""

    def test_spanish_text(self):
        """Test Spanish text detection."""
        assert has_spanish_chars("José García")
        assert has_spanish_chars("niño")
        assert has_spanish_chars("¿Qué?")

    def test_english_text(self):
        """Test English text."""
        assert not has_spanish_chars("Hello World")


class TestCountSpanishChars:
    """Tests for count_spanish_chars function."""

    def test_counting(self):
        """Test Spanish character counting."""
        assert count_spanish_chars("José") == 1
        assert count_spanish_chars("niño") == 1
        assert count_spanish_chars("Hello") == 0


# URL utilities tests

class TestIsBlockedDomain:
    """Tests for is_blocked_domain function."""

    def test_blocked(self):
        """Test blocked domains."""
        assert is_blocked_domain("https://shutterstock.com/image")
        assert is_blocked_domain("https://letterboxd.com/film")

    def test_allowed(self):
        """Test allowed domains."""
        assert not is_blocked_domain("https://wikipedia.org/wiki/Test")
        assert not is_blocked_domain("https://imdb.com/title")

    def test_invalid_url(self, monkeypatch):
        """Test invalid URL handling."""
        monkeypatch.setattr("soundtracker.utils.urls.urlparse", Mock(side_effect=ValueError))
        assert not is_blocked_domain("bad-url")


class TestIsImageUrl:
    """Tests for is_image_url function."""

    def test_images(self):
        """Test image URL detection."""
        assert is_image_url("https://example.com/image.jpg")
        assert is_image_url("https://example.com/photo.png")
        assert is_image_url("https://example.com/pic.webp")
        assert is_image_url("https://example.com/anim.gif")

    def test_non_images(self):
        """Test non-image URLs."""
        assert not is_image_url("https://example.com/page.html")
        assert not is_image_url("https://example.com/doc.pdf")


class TestFormatLink:
    """Tests for format_link function."""

    def test_url(self):
        """Test URL passthrough."""
        assert format_link("https://example.com", Path("/tmp")) == "https://example.com"

    def test_relative_path(self):
        """Test relative path formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "a" / "b" / "c.txt"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("ok", encoding="utf-8")
            assert format_link(str(file_path), base) == "a/b/c.txt"

    def test_relative_path_not_under_base(self):
        """Test fallback when path is not under base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "base"
            base.mkdir()
            other = Path(tmpdir) / "other.txt"
            other.write_text("ok", encoding="utf-8")
            assert format_link(str(other), base) == str(other)

    def test_missing_path(self):
        """Test missing file returns original path."""
        assert format_link("/tmp/does_not_exist.txt", Path("/tmp")) == "/tmp/does_not_exist.txt"


class TestExtractDomain:
    """Tests for extract_domain function."""

    def test_basic(self):
        """Test basic domain extraction."""
        assert extract_domain("https://example.com/path") == "example.com"
        assert extract_domain("https://www.test.org") == "www.test.org"

    def test_invalid(self):
        """Test invalid URL."""
        assert extract_domain("not-a-url") == "unknown"

    def test_exception_returns_unknown(self, monkeypatch):
        monkeypatch.setattr("soundtracker.utils.urls.urlparse", Mock(side_effect=ValueError))
        assert extract_domain("bad-url") == "unknown"


class TestIsWikipediaUrl:
    """Tests for is_wikipedia_url function."""

    def test_wikipedia(self):
        """Test Wikipedia URL detection."""
        assert is_wikipedia_url("https://en.wikipedia.org/wiki/Test")
        assert is_wikipedia_url("https://es.wikipedia.org/wiki/Prueba")
        assert is_wikipedia_url("https://www.wikidata.org/wiki/Q123")

    def test_other(self):
        """Test non-Wikipedia URLs."""
        assert not is_wikipedia_url("https://imdb.com")


class TestBuildWikipediaUrl:
    """Tests for build_wikipedia_url function."""

    def test_english(self):
        """Test English Wikipedia URL."""
        url = build_wikipedia_url("John Williams", "en")
        assert "en.wikipedia.org" in url
        assert "John_Williams" in url

    def test_spanish(self):
        """Test Spanish Wikipedia URL."""
        url = build_wikipedia_url("John Williams", "es")
        assert "es.wikipedia.org" in url


class TestNormalizeWikipediaUrl:
    """Tests for normalize_wikipedia_url function."""

    def test_protocol_relative(self):
        """Test protocol-relative URL."""
        assert normalize_wikipedia_url("//upload.wikimedia.org/image.jpg").startswith("https:")

    def test_absolute_path(self):
        """Test absolute path."""
        assert normalize_wikipedia_url("/wiki/Test").startswith("https://en.wikipedia.org")

    def test_full_url(self):
        """Test full URL passthrough."""
        url = "https://example.com/image.jpg"
        assert normalize_wikipedia_url(url) == url


class TestCleanRedirectUrl:
    """Tests for clean_redirect_url function."""

    def test_non_redirect(self):
        """Test non-redirect URL passthrough."""
        url = "https://example.com"
        assert clean_redirect_url(url) == url

    def test_google_redirect(self):
        """Test Google redirect cleaning."""
        url = "https://www.google.com/url?q=https%3A%2F%2Fexample.com%2Fpage"
        assert clean_redirect_url(url) == "https://example.com/page"

    def test_google_redirect_url_param(self):
        """Test Google redirect cleaning via url param."""
        url = "https://www.google.com/url?url=https%3A%2F%2Fexample.com%2Falt"
        assert clean_redirect_url(url) == "https://example.com/alt"

    def test_google_redirect_missing_params(self):
        """Test Google redirect with missing params returns original."""
        url = "https://www.google.com/url?sa=U"
        assert clean_redirect_url(url) == url


class TestFetchUrlText:
    """Tests for fetch_url_text function."""

    def test_blocked_domain(self, monkeypatch):
        monkeypatch.setattr("soundtracker.utils.urls.is_blocked_domain", Mock(return_value=True))
        assert fetch_url_text("https://blocked.com") == ""

    def test_success(self, monkeypatch):
        response = Mock()
        response.raise_for_status = Mock()
        response.text = "OK"
        monkeypatch.setattr("soundtracker.utils.urls.requests.get", Mock(return_value=response))
        assert fetch_url_text("https://example.com") == "OK"

    def test_request_exception(self, monkeypatch):
        monkeypatch.setattr(
            "soundtracker.utils.urls.requests.get",
            Mock(side_effect=requests.RequestException("boom")),
        )
        assert fetch_url_text("https://example.com") == ""


class TestExtractUrlsFromText:
    """Tests for extract_urls_from_text function."""

    def test_single_url(self):
        """Test single URL extraction."""
        text = "Check out https://example.com for more info"
        urls = extract_urls_from_text(text)
        assert "https://example.com" in urls

    def test_multiple_urls(self):
        """Test multiple URL extraction."""
        text = "Visit https://a.com and https://b.com"
        urls = extract_urls_from_text(text)
        assert len(urls) == 2

    def test_no_urls(self):
        """Test no URLs found."""
        urls = extract_urls_from_text("No URLs here")
        assert urls == []

    def test_duplicate_urls(self):
        """Test duplicate URL de-duplication."""
        text = "Visit https://a.com and https://a.com again."
        urls = extract_urls_from_text(text)
        assert urls == ["https://a.com"]


def test_utils_exports() -> None:
    """Ensure utils __all__ exports are available."""
    from soundtracker import utils

    assert "slugify" in utils.__all__
    assert callable(utils.slugify)
