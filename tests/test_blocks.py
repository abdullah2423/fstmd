"""
Tests for block-level elements (headings, paragraphs, lists).
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestHeadings:
    """Tests for heading elements (# through ######)."""
    
    def test_h1(self, md_safe: Markdown) -> None:
        """Test H1 heading."""
        result = md_safe.render("# Heading 1")
        assert "<h1>" in result
        assert "</h1>" in result
        assert "Heading 1" in result
    
    def test_h2(self, md_safe: Markdown) -> None:
        """Test H2 heading."""
        result = md_safe.render("## Heading 2")
        assert "<h2>" in result
        assert "</h2>" in result
    
    def test_h3(self, md_safe: Markdown) -> None:
        """Test H3 heading."""
        result = md_safe.render("### Heading 3")
        assert "<h3>" in result
        assert "</h3>" in result
    
    def test_h4(self, md_safe: Markdown) -> None:
        """Test H4 heading."""
        result = md_safe.render("#### Heading 4")
        assert "<h4>" in result
        assert "</h4>" in result
    
    def test_h5(self, md_safe: Markdown) -> None:
        """Test H5 heading."""
        result = md_safe.render("##### Heading 5")
        assert "<h5>" in result
        assert "</h5>" in result
    
    def test_h6(self, md_safe: Markdown) -> None:
        """Test H6 heading."""
        result = md_safe.render("###### Heading 6")
        assert "<h6>" in result
        assert "</h6>" in result
    
    def test_h7_invalid(self, md_safe: Markdown) -> None:
        """Test that ####### is treated as paragraph."""
        result = md_safe.render("####### Too many")
        assert "<h7>" not in result
        # Should be treated as text
        assert "#" in result
    
    def test_heading_no_space(self, md_safe: Markdown) -> None:
        """Test heading without space after hash."""
        result = md_safe.render("#NoSpace")
        # May or may not be valid depending on implementation
        assert "#" in result or "<h1>" in result
    
    def test_heading_with_formatting(self, md_safe: Markdown) -> None:
        """Test heading with inline formatting."""
        result = md_safe.render("# **Bold** Heading")
        assert "<h1>" in result
        assert "<strong>Bold</strong>" in result
    
    def test_multiple_headings(self, md_safe: Markdown) -> None:
        """Test multiple headings."""
        result = md_safe.render("# One\n## Two\n### Three")
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<h3>" in result
    
    def test_empty_heading(self, md_safe: Markdown) -> None:
        """Test empty heading."""
        result = md_safe.render("# ")
        assert "<h1>" in result
        assert "</h1>" in result
    
    def test_heading_only_hashes(self, md_safe: Markdown) -> None:
        """Test heading with only hashes."""
        result = md_safe.render("#")
        # Should produce something
        assert result


class TestParagraphs:
    """Tests for paragraph elements."""
    
    def test_simple_paragraph(self, md_safe: Markdown) -> None:
        """Test simple paragraph."""
        result = md_safe.render("This is a paragraph.")
        assert "<p>" in result
        assert "</p>" in result
        assert "This is a paragraph." in result
    
    def test_multiple_paragraphs(self, md_safe: Markdown) -> None:
        """Test multiple paragraphs separated by blank line."""
        result = md_safe.render("Paragraph one.\n\nParagraph two.")
        assert result.count("<p>") == 2
        assert result.count("</p>") == 2
    
    def test_paragraph_soft_break(self, md_safe: Markdown) -> None:
        """Test paragraph with soft line break."""
        result = md_safe.render("Line one\nLine two")
        # Should be single paragraph with soft break
        assert "<p>" in result
        assert "Line one" in result
        assert "Line two" in result
    
    def test_paragraph_with_formatting(self, md_safe: Markdown) -> None:
        """Test paragraph with inline formatting."""
        result = md_safe.render("This is **bold** and *italic*.")
        assert "<p>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
    
    def test_empty_paragraph(self, md_safe: Markdown) -> None:
        """Test empty input."""
        result = md_safe.render("")
        assert result == ""
    
    def test_whitespace_only(self, md_safe: Markdown) -> None:
        """Test whitespace-only input."""
        result = md_safe.render("   \n\n   ")
        # Should not produce paragraph
        assert result.strip() == "" or "<p>" not in result or result == ""


class TestLists:
    """Tests for unordered lists."""
    
    def test_simple_list(self, md_safe: Markdown) -> None:
        """Test simple unordered list."""
        result = md_safe.render("- Item 1\n- Item 2\n- Item 3")
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 3
        assert result.count("</li>") == 3
    
    def test_single_item_list(self, md_safe: Markdown) -> None:
        """Test single item list."""
        result = md_safe.render("- Only item")
        assert "<ul>" in result
        assert "<li>" in result
        assert "Only item" in result
    
    def test_list_with_formatting(self, md_safe: Markdown) -> None:
        """Test list items with inline formatting."""
        result = md_safe.render("- **Bold item**\n- *Italic item*")
        assert "<ul>" in result
        assert "<strong>Bold item</strong>" in result
        assert "<em>Italic item</em>" in result
    
    def test_list_then_paragraph(self, md_safe: Markdown) -> None:
        """Test list followed by paragraph."""
        result = md_safe.render("- Item\n\nParagraph")
        assert "<ul>" in result
        assert "</ul>" in result
        assert "<p>" in result
    
    def test_paragraph_then_list(self, md_safe: Markdown) -> None:
        """Test paragraph followed by list."""
        result = md_safe.render("Paragraph\n\n- Item")
        assert "<p>" in result
        assert "<ul>" in result
    
    def test_dash_not_list(self, md_safe: Markdown) -> None:
        """Test that dash without space is not list."""
        result = md_safe.render("-notlist")
        assert "<ul>" not in result
        assert "-notlist" in result or "-" in result


class TestMixedContent:
    """Tests for mixed block-level content."""
    
    def test_heading_then_paragraph(self, md_safe: Markdown) -> None:
        """Test heading followed by paragraph."""
        result = md_safe.render("# Title\n\nContent here.")
        assert "<h1>" in result
        assert "<p>" in result
    
    def test_heading_then_list(self, md_safe: Markdown) -> None:
        """Test heading followed by list."""
        result = md_safe.render("# Title\n\n- Item 1\n- Item 2")
        assert "<h1>" in result
        assert "<ul>" in result
    
    def test_complex_document(self, md_safe: Markdown) -> None:
        """Test complex document with multiple element types."""
        doc = """# Main Title

This is the introduction paragraph with **bold** text.

## Section One

- First item
- Second item

Another paragraph here.

## Section Two

Final *italic* text.
"""
        result = md_safe.render(doc)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<p>" in result
        assert "<ul>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result


class TestNewlines:
    """Tests for newline handling."""
    
    def test_single_newline(self, md_safe: Markdown) -> None:
        """Test single newline (soft break)."""
        result = md_safe.render("line1\nline2")
        assert "line1" in result
        assert "line2" in result
        # Should be in same paragraph
        assert result.count("<p>") == 1
    
    def test_double_newline(self, md_safe: Markdown) -> None:
        """Test double newline (paragraph break)."""
        result = md_safe.render("para1\n\npara2")
        assert result.count("<p>") == 2
    
    def test_triple_newline(self, md_safe: Markdown) -> None:
        """Test triple newline."""
        result = md_safe.render("para1\n\n\npara2")
        assert result.count("<p>") == 2
    
    def test_trailing_newline(self, md_safe: Markdown) -> None:
        """Test trailing newline."""
        result = md_safe.render("text\n")
        assert "text" in result
    
    def test_leading_newline(self, md_safe: Markdown) -> None:
        """Test leading newline."""
        result = md_safe.render("\ntext")
        assert "text" in result
