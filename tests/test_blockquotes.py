"""
Tests for blockquotes.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestBlockquotes:
    """Tests for blockquote elements (>)."""
    
    def test_simple_blockquote(self, md_safe: Markdown) -> None:
        """Test basic blockquote."""
        result = md_safe.render("> Quote")
        assert "<blockquote>" in result
        assert "</blockquote>" in result
        assert "Quote" in result
    
    def test_blockquote_with_space(self, md_safe: Markdown) -> None:
        """Test blockquote with space after >."""
        result = md_safe.render("> Quote with space")
        assert "<blockquote>" in result
        assert "Quote with space" in result
    
    def test_blockquote_without_space(self, md_safe: Markdown) -> None:
        """Test blockquote without space after >."""
        result = md_safe.render(">Quote without space")
        assert "<blockquote>" in result
        assert "Quote without space" in result
    
    def test_multiline_blockquote(self, md_safe: Markdown) -> None:
        """Test multiline blockquote."""
        result = md_safe.render("> Line 1\n> Line 2\n> Line 3")
        assert "<blockquote>" in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    def test_blockquote_with_formatting(self, md_safe: Markdown) -> None:
        """Test blockquote with inline formatting."""
        result = md_safe.render("> **Bold** and *italic*")
        assert "<blockquote>" in result
        assert "<strong>Bold</strong>" in result
        assert "<em>italic</em>" in result
    
    def test_blockquote_with_inline_code(self, md_safe: Markdown) -> None:
        """Test blockquote with inline code."""
        result = md_safe.render("> Use `code` here")
        assert "<blockquote>" in result
        assert "<code>code</code>" in result
    
    def test_empty_blockquote(self, md_safe: Markdown) -> None:
        """Test empty blockquote."""
        result = md_safe.render(">")
        assert "<blockquote>" in result
        assert "</blockquote>" in result
    
    def test_blockquote_after_paragraph(self, md_safe: Markdown) -> None:
        """Test blockquote after paragraph."""
        result = md_safe.render("Paragraph\n\n> Quote")
        assert "<p>" in result
        assert "</p>" in result
        assert "<blockquote>" in result
    
    def test_paragraph_after_blockquote(self, md_safe: Markdown) -> None:
        """Test paragraph after blockquote."""
        result = md_safe.render("> Quote\n\nParagraph")
        assert "<blockquote>" in result
        assert "</blockquote>" in result
        assert "<p>" in result
        assert "Paragraph" in result


class TestNestedBlockquotes:
    """Tests for nested blockquotes."""
    
    def test_double_nested_blockquote(self, md_safe: Markdown) -> None:
        """Test double nested blockquote."""
        result = md_safe.render(">> Nested quote")
        assert result.count("<blockquote>") == 2
        assert result.count("</blockquote>") == 2
        assert "Nested quote" in result
    
    def test_triple_nested_blockquote(self, md_safe: Markdown) -> None:
        """Test triple nested blockquote."""
        result = md_safe.render(">>> Deep nested")
        assert result.count("<blockquote>") == 3
        assert result.count("</blockquote>") == 3
    
    def test_nested_with_space(self, md_safe: Markdown) -> None:
        """Test nested blockquote with space after each >."""
        result = md_safe.render("> > Nested")
        # Should handle > > or >> for nesting
        assert "<blockquote>" in result


class TestBlockquoteInteractions:
    """Tests for blockquote interactions with other elements."""
    
    def test_blockquote_before_heading(self, md_safe: Markdown) -> None:
        """Test blockquote followed by heading."""
        result = md_safe.render("> Quote\n\n# Heading")
        assert "<blockquote>" in result
        assert "<h1>" in result
    
    def test_heading_before_blockquote(self, md_safe: Markdown) -> None:
        """Test heading followed by blockquote."""
        result = md_safe.render("# Heading\n\n> Quote")
        assert "<h1>" in result
        assert "<blockquote>" in result
    
    def test_blockquote_before_list(self, md_safe: Markdown) -> None:
        """Test blockquote followed by list."""
        result = md_safe.render("> Quote\n\n- Item")
        assert "<blockquote>" in result
        assert "<ul>" in result
        assert "<li>" in result
    
    def test_list_before_blockquote(self, md_safe: Markdown) -> None:
        """Test list followed by blockquote."""
        result = md_safe.render("- Item\n\n> Quote")
        assert "<ul>" in result
        assert "<blockquote>" in result


class TestBlockquoteXSS:
    """XSS prevention tests for blockquotes."""
    
    def test_blockquote_escapes_html(self, md_safe: Markdown) -> None:
        """Test that blockquote escapes HTML."""
        result = md_safe.render("> <script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_blockquote_escapes_ampersand(self, md_safe: Markdown) -> None:
        """Test that blockquote escapes ampersand."""
        result = md_safe.render("> Tom & Jerry")
        assert "&amp;" in result


class TestBlockquoteDeterminism:
    """Determinism tests for blockquotes."""
    
    def test_simple_blockquote_deterministic(self, md_safe: Markdown) -> None:
        """Test simple blockquote is deterministic."""
        input_text = "> Quote here"
        result1 = md_safe.render(input_text)
        result2 = md_safe.render(input_text)
        assert result1 == result2
    
    def test_nested_blockquote_deterministic(self, md_safe: Markdown) -> None:
        """Test nested blockquote is deterministic."""
        input_text = ">> Nested quote"
        result1 = md_safe.render(input_text)
        result2 = md_safe.render(input_text)
        assert result1 == result2
    
    def test_complex_blockquote_deterministic(self, md_safe: Markdown) -> None:
        """Test complex blockquote document is deterministic."""
        input_text = """# Title

> First quote with **bold**

Some text

>> Nested quote

> Another quote
"""
        results = [md_safe.render(input_text) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestBlockquoteStress:
    """Stress tests for blockquotes."""
    
    def test_very_long_blockquote(self, md_safe: Markdown) -> None:
        """Test very long blockquote content."""
        long_text = "word " * 1000
        result = md_safe.render(f"> {long_text}")
        assert "<blockquote>" in result
        assert "word" in result
    
    def test_many_blockquotes(self, md_safe: Markdown) -> None:
        """Test many consecutive blockquotes."""
        lines = "\n\n".join([f"> Quote {i}" for i in range(50)])
        result = md_safe.render(lines)
        # Each separated blockquote should be its own
        assert "Quote 49" in result
    
    def test_deeply_nested_blockquote(self, md_safe: Markdown) -> None:
        """Test deeply nested blockquote."""
        prefix = ">" * 10
        result = md_safe.render(f"{prefix} Deep")
        assert result.count("<blockquote>") == 10
        assert result.count("</blockquote>") == 10
