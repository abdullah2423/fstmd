"""
Tests for link formatting [text](url).
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestSimpleLinks:
    """Tests for basic link functionality."""
    
    def test_simple_link(self, md_safe: Markdown) -> None:
        """Test basic link formatting."""
        result = md_safe.render("[click here](https://example.com)")
        assert '<a href="https://example.com">click here</a>' in result
    
    def test_link_in_paragraph(self, md_safe: Markdown) -> None:
        """Test link within a paragraph."""
        result = md_safe.render("Visit [our site](https://example.com) today")
        assert '<a href="https://example.com">our site</a>' in result
        assert "Visit" in result
        assert "today" in result
    
    def test_multiple_links(self, md_safe: Markdown) -> None:
        """Test multiple links in same paragraph."""
        result = md_safe.render("[one](https://one.com) and [two](https://two.com)")
        assert '<a href="https://one.com">one</a>' in result
        assert '<a href="https://two.com">two</a>' in result
    
    def test_link_at_start(self, md_safe: Markdown) -> None:
        """Test link at the start of text."""
        result = md_safe.render("[link](https://example.com) followed by text")
        assert '<a href="https://example.com">link</a>' in result
        assert "followed by text" in result
    
    def test_link_at_end(self, md_safe: Markdown) -> None:
        """Test link at the end of text."""
        result = md_safe.render("Text with [link](https://example.com)")
        assert '<a href="https://example.com">link</a>' in result
        assert "Text with" in result
    
    def test_link_empty_url(self, md_safe: Markdown) -> None:
        """Test link with empty URL."""
        result = md_safe.render("[text]()")
        assert '<a href="">text</a>' in result
    
    def test_link_empty_text(self, md_safe: Markdown) -> None:
        """Test link with empty text - treated as invalid."""
        result = md_safe.render("[](https://example.com)")
        # Empty link text is output literally
        assert "[]" in result


class TestLinkPunctuation:
    """Tests for links with punctuation."""
    
    def test_link_followed_by_period(self, md_safe: Markdown) -> None:
        """Test link followed by punctuation."""
        result = md_safe.render("See [this](https://example.com).")
        assert '<a href="https://example.com">this</a>' in result
        assert "." in result
    
    def test_link_followed_by_comma(self, md_safe: Markdown) -> None:
        """Test link followed by comma."""
        result = md_safe.render("[link](https://example.com), more text")
        assert '<a href="https://example.com">link</a>' in result
        assert ", more text" in result
    
    def test_link_with_exclamation(self, md_safe: Markdown) -> None:
        """Test link followed by exclamation."""
        result = md_safe.render("Click [here](https://example.com)!")
        assert '<a href="https://example.com">here</a>' in result
    
    def test_link_text_with_punctuation(self, md_safe: Markdown) -> None:
        """Test link text containing punctuation."""
        result = md_safe.render("[Hello, World!](https://example.com)")
        assert '<a href="https://example.com">Hello, World!</a>' in result
    
    def test_link_url_with_query_params(self, md_safe: Markdown) -> None:
        """Test link URL with query parameters."""
        result = md_safe.render("[search](https://example.com?q=test&page=1)")
        assert '<a href="https://example.com?q=test&amp;page=1">search</a>' in result
    
    def test_link_url_with_hash(self, md_safe: Markdown) -> None:
        """Test link URL with hash fragment."""
        result = md_safe.render("[section](https://example.com#section)")
        assert '<a href="https://example.com#section">section</a>' in result


class TestNestedFormattingInLinks:
    """Tests for formatting within link text."""
    
    def test_bold_in_link(self, md_safe: Markdown) -> None:
        """Test bold text inside link."""
        result = md_safe.render("[**bold link**](https://example.com)")
        assert "<strong>bold link</strong>" in result
        assert '<a href="https://example.com">' in result
        assert "</a>" in result
    
    def test_italic_in_link(self, md_safe: Markdown) -> None:
        """Test italic text inside link."""
        result = md_safe.render("[*italic link*](https://example.com)")
        assert "<em>italic link</em>" in result
        assert '<a href="https://example.com">' in result
        assert "</a>" in result
    
    def test_partial_bold_in_link(self, md_safe: Markdown) -> None:
        """Test partial bold in link text."""
        result = md_safe.render("[click **here** now](https://example.com)")
        assert "<strong>here</strong>" in result
        assert '<a href="https://example.com">' in result
    
    def test_partial_italic_in_link(self, md_safe: Markdown) -> None:
        """Test partial italic in link text."""
        result = md_safe.render("[click *here* now](https://example.com)")
        assert "<em>here</em>" in result
        assert '<a href="https://example.com">' in result


class TestLinkEdgeCases:
    """Tests for edge cases in link parsing."""
    
    def test_unclosed_bracket(self, md_safe: Markdown) -> None:
        """Test unclosed opening bracket."""
        result = md_safe.render("[unclosed text")
        assert "[" in result
        assert "unclosed text" in result
    
    def test_bracket_without_url(self, md_safe: Markdown) -> None:
        """Test brackets without URL parentheses."""
        result = md_safe.render("[text] without url")
        assert "[text]" in result
        assert "without url" in result
    
    def test_nested_brackets(self, md_safe: Markdown) -> None:
        """Test nested brackets in link."""
        result = md_safe.render("[[nested]](https://example.com)")
        # Should not parse as link due to nested [
        assert "[" in result
    
    def test_link_with_newline_in_text(self, md_safe: Markdown) -> None:
        """Test link with newline in text - should break."""
        result = md_safe.render("[line1\nline2](https://example.com)")
        # Newline breaks link syntax
        assert '<a href="https://example.com">' not in result
    
    def test_link_with_newline_in_url(self, md_safe: Markdown) -> None:
        """Test link with newline in URL - should break."""
        result = md_safe.render("[text](https://\nexample.com)")
        # Newline breaks link syntax
        assert '<a href="https://' not in result
    
    def test_adjacent_links(self, md_safe: Markdown) -> None:
        """Test two links directly adjacent."""
        result = md_safe.render("[one](https://one.com)[two](https://two.com)")
        assert '<a href="https://one.com">one</a>' in result
        assert '<a href="https://two.com">two</a>' in result


class TestLinkURLProtocols:
    """Tests for various URL protocols."""
    
    def test_https_link(self, md_safe: Markdown) -> None:
        """Test HTTPS link."""
        result = md_safe.render("[secure](https://example.com)")
        assert '<a href="https://example.com">' in result
    
    def test_http_link(self, md_safe: Markdown) -> None:
        """Test HTTP link."""
        result = md_safe.render("[link](http://example.com)")
        assert '<a href="http://example.com">' in result
    
    def test_mailto_link(self, md_safe: Markdown) -> None:
        """Test mailto link."""
        result = md_safe.render("[email](mailto:test@example.com)")
        assert '<a href="mailto:test@example.com">' in result
    
    def test_tel_link(self, md_safe: Markdown) -> None:
        """Test tel link."""
        result = md_safe.render("[call](tel:+1234567890)")
        assert '<a href="tel:+1234567890">' in result
    
    def test_anchor_link(self, md_safe: Markdown) -> None:
        """Test anchor link."""
        result = md_safe.render("[section](#section-id)")
        assert '<a href="#section-id">' in result
    
    def test_relative_link(self, md_safe: Markdown) -> None:
        """Test relative link."""
        result = md_safe.render("[page](/about)")
        assert '<a href="/about">' in result


class TestLinkSecurity:
    """Tests for link URL security in safe mode."""
    
    def test_javascript_url_blocked(self, md_safe: Markdown) -> None:
        """Test javascript: URL is blocked in safe mode."""
        result = md_safe.render("[click](javascript:alert(1))")
        # Should NOT create an actual link with javascript:
        assert 'href="javascript:' not in result
        # Should output as plain text
        assert "javascript:" in result
    
    def test_javascript_url_case_insensitive(self, md_safe: Markdown) -> None:
        """Test JavaScript: URL (mixed case) is blocked."""
        result = md_safe.render("[click](JavaScript:alert(1))")
        assert 'href="JavaScript:' not in result
        assert 'href="javascript:' not in result
    
    def test_vbscript_url_blocked(self, md_safe: Markdown) -> None:
        """Test vbscript: URL is blocked."""
        result = md_safe.render("[click](vbscript:msgbox(1))")
        assert 'href="vbscript:' not in result
    
    def test_data_url_blocked(self, md_safe: Markdown) -> None:
        """Test data: URL is blocked."""
        result = md_safe.render("[click](data:text/html,<script>alert(1)</script>)")
        assert 'href="data:' not in result
    
    def test_javascript_url_allowed_raw_mode(self, md_raw: Markdown) -> None:
        """Test javascript: URL passes in raw mode."""
        # Note: parens in URL would need escaping in standard Markdown
        result = md_raw.render("[click](javascript:void)")
        assert 'href="javascript:void"' in result
    
    def test_url_with_html_entities_escaped(self, md_safe: Markdown) -> None:
        """Test URL special characters are escaped."""
        result = md_safe.render('[link](https://example.com?a=1&b=2")')
        assert "&amp;" in result
        assert "&quot;" in result


class TestLinkStress:
    """Stress tests for links."""
    
    def test_many_links(self, md_safe: Markdown) -> None:
        """Test many links in sequence."""
        links = " ".join(f"[link{i}](https://example{i}.com)" for i in range(20))
        result = md_safe.render(links)
        for i in range(20):
            assert f'<a href="https://example{i}.com">link{i}</a>' in result
    
    def test_long_url(self, md_safe: Markdown) -> None:
        """Test link with very long URL."""
        long_url = "https://example.com/" + "a" * 1000
        result = md_safe.render(f"[link]({long_url})")
        assert f'<a href="{long_url}">link</a>' in result
    
    def test_long_text(self, md_safe: Markdown) -> None:
        """Test link with very long text."""
        long_text = "a" * 1000
        result = md_safe.render(f"[{long_text}](https://example.com)")
        assert f'<a href="https://example.com">{long_text}</a>' in result
    
    def test_alternating_links_and_text(self, md_safe: Markdown) -> None:
        """Test alternating links and text."""
        input_text = "Start [l1](u1) middle [l2](u2) end"
        result = md_safe.render(input_text)
        assert '<a href="u1">l1</a>' in result
        assert '<a href="u2">l2</a>' in result
        assert "Start" in result
        assert "middle" in result
        assert "end" in result
