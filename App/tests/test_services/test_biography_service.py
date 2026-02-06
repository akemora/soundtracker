"""Tests for soundtracker.services.biography."""

from unittest.mock import Mock

from soundtracker.services.biography import BiographyService


class TestBiographyService:
    """Tests for BiographyService."""

    def test_get_biography_prefers_spanish_wikipedia(self) -> None:
        """get_biography should return Spanish extract when available."""
        wikipedia = Mock()
        wikipedia.get_extract.return_value = "Texto biográfico en español."
        translator = Mock()
        search = Mock()

        service = BiographyService(
            wikipedia_client=wikipedia,
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia_en = Mock()

        result = service.get_biography("John Williams")

        assert result == "Texto biográfico en español."
        translator.to_spanish.assert_not_called()

    def test_extract_section_finds_heading(self) -> None:
        """_extract_section should return HTML under matching heading."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        html = "<h2>Musical style</h2><p>Text</p><h2>Other</h2>"

        section = service._extract_section(html, ["musical style"])

        assert "Text" in section

    def test_extract_section_returns_empty(self) -> None:
        """_extract_section should return empty when no heading matches."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        html = "<h2>Biography</h2><p>Text</p>"

        assert service._extract_section(html, ["musical style"]) == ""

    def test_format_biography_filters_short_paragraphs(self) -> None:
        """_format_biography should drop short paragraphs."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=10,
        )
        text = "Short.\n\nThis is a longer paragraph with enough length."

        result = service._format_biography(text)

        assert result == "This is a longer paragraph with enough length."

    def test_format_biography_limits_paragraphs(self) -> None:
        """_format_biography should respect max_paragraphs."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=1,
            max_paragraphs=1,
        )
        text = "Para one.\n\nPara two."

        result = service._format_biography(text)

        assert result == "Para one."

    def test_get_biography_english_fallback_translates(self) -> None:
        """get_biography should translate English extract."""
        wikipedia = Mock()
        wikipedia.get_extract = Mock(return_value="")
        translator = Mock()
        translator.to_spanish = Mock(return_value="Bio ES")
        search = Mock()

        service = BiographyService(
            wikipedia_client=wikipedia,
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia_en = Mock()
        service.wikipedia_en.get_extract = Mock(return_value="Bio EN")

        result = service.get_biography("John Williams")

        assert result == "Bio ES"
        translator.to_spanish.assert_called_once()

    def test_get_biography_search_fallback(self) -> None:
        """get_biography should fall back to search."""
        wikipedia = Mock()
        wikipedia.get_extract = Mock(return_value="")
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>Paragraph about composer.</p>")
        search.extract_paragraphs = Mock(return_value=["Paragraph about composer."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto ES")

        service = BiographyService(
            wikipedia_client=wikipedia,
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia_en = Mock()
        service.wikipedia_en.get_extract = Mock(return_value="")

        assert service.get_biography("John Williams") == "Texto ES"

    def test_section_to_text_empty(self) -> None:
        """_section_to_text should return empty on empty html."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        assert service._section_to_text("") == ""

    def test_section_to_text_parses_paragraphs(self) -> None:
        """_section_to_text should join extracted paragraphs."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Para 1", "Para 2"])
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=Mock(),
        )

        assert service._section_to_text("<p>Para</p>") == "Para 1\n\nPara 2"

    def test_search_for_text_returns_match(self) -> None:
        """_search_for_text should return paragraph containing keyword."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>style and influence</p>")
        search.extract_paragraphs = Mock(return_value=["A style and influence note."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto ES")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_for_text("query", ["style"]) == "Texto ES"

    def test_search_for_text_returns_empty_when_no_match(self) -> None:
        """_search_for_text should return empty when no match."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>Nothing</p>")
        search.extract_paragraphs = Mock(return_value=["No keywords here."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto ES")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_for_text("query", ["style"]) == ""

    def test_search_for_text_skips_empty_html(self) -> None:
        """_search_for_text should skip empty html."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="")
        search.extract_paragraphs = Mock(return_value=["style text"])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_for_text("query", ["style"]) == ""

    def test_get_musical_style_from_section_en(self) -> None:
        """get_musical_style should translate English section."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Style paragraph."])
        translator = Mock()
        translator.to_spanish = Mock(return_value="Estilo")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(return_value=None)
        service.wikipedia_en.fetch_html = Mock(
            return_value="<h2>Musical style</h2><p>Style paragraph.</p>"
        )

        assert service.get_musical_style("John Williams") == "Estilo"

    def test_get_musical_style_from_section_es(self) -> None:
        """get_musical_style should use Spanish section."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Estilo texto"])
        translator = Mock()

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(
            return_value="<h2>Estilo musical</h2><p>Estilo texto</p>"
        )

        assert service.get_musical_style("John Williams") == "Estilo texto"

    def test_get_musical_style_fallback_to_search(self) -> None:
        """get_musical_style should fall back to search."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>style text</p>")
        search.extract_paragraphs = Mock(return_value=["style text"])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )
        service.wikipedia.fetch_html = Mock(return_value="<h2>Other</h2>")
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        assert service.get_musical_style("Composer") == "Texto"

    def test_get_anecdotes_search_fallback(self) -> None:
        """get_anecdotes should fall back to search."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>Known for collaboration.</p>")
        search.extract_paragraphs = Mock(return_value=["Known for collaboration."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Curiosidad")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(return_value=None)
        service.wikipedia_en.fetch_html = Mock(return_value=None)

        assert service.get_anecdotes("John Williams") == "Curiosidad"

    def test_get_anecdotes_from_section_en(self) -> None:
        """get_anecdotes should translate English section."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Anecdote paragraph."])
        translator = Mock()
        translator.to_spanish = Mock(return_value="Anecdota")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(return_value=None)
        service.wikipedia_en.fetch_html = Mock(
            return_value="<h2>Personal life</h2><p>Anecdote paragraph.</p>"
        )

        assert service.get_anecdotes("John Williams") == "Anecdota"

    def test_get_anecdotes_from_section_es(self) -> None:
        """get_anecdotes should use Spanish section."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Anecdota texto."])
        translator = Mock()

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(
            return_value="<h2>Vida personal</h2><p>Anecdota texto.</p>"
        )

        assert service.get_anecdotes("Composer") == "Anecdota texto."

    def test_get_anecdotes_es_section_missing_then_en(self) -> None:
        """get_anecdotes should try English if Spanish section missing."""
        search = Mock()
        search.extract_paragraphs = Mock(return_value=["Anecdote paragraph."])
        translator = Mock()
        translator.to_spanish = Mock(return_value="Anecdota")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )
        service.wikipedia.fetch_html = Mock(return_value="<h2>Other</h2>")
        service.wikipedia_en.fetch_html = Mock(
            return_value="<h2>Personal life</h2><p>Anecdote paragraph.</p>"
        )

        assert service.get_anecdotes("Composer") == "Anecdota"

    def test_derive_fun_facts_from_style(self) -> None:
        """derive_fun_facts should select from style first."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=1,
        )
        style = "Fue un compositor y ganó premios."
        biography = ""

        facts = service.derive_fun_facts(biography, style)

        assert facts

    def test_select_sentences_filters_short(self) -> None:
        """_select_sentences should filter short sentences."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=50,
        )
        text = "Composer won awards. Short."

        assert service._select_sentences(text, ["composer"]) == []

    def test_select_sentences_limits(self) -> None:
        """_select_sentences should limit sentences."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
            min_paragraph_len=1,
        )
        text = "Composer won awards. Composer collaborated. Composer innovated."

        selected = service._select_sentences(text, ["composer"], max_sentences=2)

        assert len(selected) == 2

    def test_search_biography_returns_empty_when_no_paragraphs(self) -> None:
        """_search_biography should return empty when no paragraphs."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>Short</p>")
        search.extract_paragraphs = Mock(return_value=[])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Texto")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
        )

        assert service._search_biography("Composer") == ""

    def test_search_biography_returns_text(self) -> None:
        """_search_biography should return translated text."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="<p>Bio</p>")
        search.extract_paragraphs = Mock(return_value=["Bio paragraph."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Bio ES")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )

        assert service._search_biography("Composer") == "Bio ES"

    def test_search_biography_skips_empty_html(self) -> None:
        """_search_biography should skip empty html."""
        search = Mock()
        search.search = Mock(return_value=["http://example.com"])
        search.fetch_url_text = Mock(return_value="")
        search.extract_paragraphs = Mock(return_value=["Bio paragraph."])
        translator = Mock()
        translator.ensure_spanish = Mock(return_value="Bio ES")

        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=search,
            translator=translator,
            min_paragraph_len=1,
        )

        assert service._search_biography("Composer") == ""

    def test_derive_fun_facts_returns_empty_when_none(self) -> None:
        """derive_fun_facts should return empty when no facts."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        assert service.derive_fun_facts("", "") == ""

    def test_select_sentences_empty_text(self) -> None:
        """_select_sentences should return empty on empty text."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )

        assert service._select_sentences("", ["keyword"]) == []

    def test_clean_text_normalizes(self) -> None:
        """_clean_text should normalize spacing."""
        service = BiographyService(
            wikipedia_client=Mock(),
            search_client=Mock(),
            translator=Mock(),
        )
        assert service._clean_text("Hello   ,  world") == "Hello, world"
