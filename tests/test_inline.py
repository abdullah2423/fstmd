"""
Tests for inline formatting (bold, italic).
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestItalic:
    """Tests for italic formatting (*text*)."""
    
    def test_simple_italic(self, md_safe: Markdown) -> None:
        """Test basic italic formatting."""
        result = md_safe.render("*italic*")
        assert "<em>italic</em>" in result
    
    def test_italic_in_sentence(self, md_safe: Markdown) -> None:
        """Test italic within a sentence."""
        result = md_safe.render("This is *italic* text")
        assert "<em>italic</em>" in result
        assert "This is" in result
        assert "text" in result
    
    def test_multiple_italics(self, md_safe: Markdown) -> None:
        """Test multiple italic sections."""
        result = md_safe.render("*one* and *two*")
        assert result.count("<em>") == 2
        assert result.count("</em>") == 2
    
    def test_unclosed_italic(self, md_safe: Markdown) -> None:
        """Test unclosed italic marker."""
        result = md_safe.render("*unclosed")
        # Should close at end of block
        assert "</em>" in result or "*" in result
    
    def test_italic_with_spaces(self, md_safe: Markdown) -> None:
        """Test italic with internal spaces."""
        result = md_safe.render("*italic with spaces*")
        assert "<em>italic with spaces</em>" in result
    
    def test_empty_italic(self, md_safe: Markdown) -> None:
        """Test empty italic markers."""
        result = md_safe.render("**")
        # ** is start of bold, not empty italic
        assert result  # Should produce output
    
    def test_italic_at_line_start(self, md_safe: Markdown) -> None:
        """Test italic at the start of a line."""
        result = md_safe.render("*italic* at start")
        assert "<em>italic</em>" in result


class TestBold:
    """Tests for bold formatting (**text**)."""
    
    def test_simple_bold(self, md_safe: Markdown) -> None:
        """Test basic bold formatting."""
        result = md_safe.render("**bold**")
        assert "<strong>bold</strong>" in result
    
    def test_bold_in_sentence(self, md_safe: Markdown) -> None:
        """Test bold within a sentence."""
        result = md_safe.render("This is **bold** text")
        assert "<strong>bold</strong>" in result
    
    def test_multiple_bolds(self, md_safe: Markdown) -> None:
        """Test multiple bold sections."""
        result = md_safe.render("**one** and **two**")
        assert result.count("<strong>") == 2
        assert result.count("</strong>") == 2
    
    def test_unclosed_bold(self, md_safe: Markdown) -> None:
        """Test unclosed bold markers."""
        result = md_safe.render("**unclosed")
        # Should close at end of block
        assert "</strong>" in result or "**" in result
    
    def test_bold_with_spaces(self, md_safe: Markdown) -> None:
        """Test bold with internal spaces."""
        result = md_safe.render("**bold with spaces**")
        assert "<strong>bold with spaces</strong>" in result


class TestBoldItalic:
    """Tests for combined bold and italic (***text***)."""
    
    def test_bold_italic(self, md_safe: Markdown) -> None:
        """Test combined bold and italic."""
        result = md_safe.render("***bold italic***")
        assert "<strong>" in result
        assert "<em>" in result
        assert "</em>" in result
        assert "</strong>" in result
    
    def test_bold_then_italic(self, md_safe: Markdown) -> None:
        """Test bold followed by italic."""
        result = md_safe.render("**bold** and *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
    
    def test_italic_then_bold(self, md_safe: Markdown) -> None:
        """Test italic followed by bold."""
        result = md_safe.render("*italic* and **bold**")
        assert "<em>italic</em>" in result
        assert "<strong>bold</strong>" in result
    
    def test_nested_formatting(self, md_safe: Markdown) -> None:
        """Test potentially nested formatting."""
        result = md_safe.render("**bold *with italic* inside**")
        assert "<strong>" in result
        # Nested italic might or might not be supported
        assert "bold" in result
        assert "inside" in result


class TestMixedInline:
    """Tests for mixed inline content."""
    
    def test_mixed_with_plain_text(self, md_safe: Markdown) -> None:
        """Test mixing formatted and plain text."""
        result = md_safe.render("plain **bold** plain *italic* plain")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "plain" in result
    
    def test_adjacent_formatting(self, md_safe: Markdown) -> None:
        """Test adjacent formatted sections."""
        result = md_safe.render("**bold***italic*")
        # Adjacent formatting
        assert "<strong>" in result or "<em>" in result
    
    def test_special_chars_in_formatting(self, md_safe: Markdown) -> None:
        """Test special characters inside formatting."""
        result = md_safe.render("**hello & world**")
        assert "<strong>" in result
        assert "&amp;" in result  # & should be escaped
    
    def test_numbers_in_formatting(self, md_safe: Markdown) -> None:
        """Test numbers inside formatting."""
        result = md_safe.render("**123**")
        assert "<strong>123</strong>" in result


class TestEdgeCases:
    """Edge cases for inline formatting."""
    
    def test_single_star(self, md_safe: Markdown) -> None:
        """Test single asterisk."""
        result = md_safe.render("a * b")
        # Single * with spaces is not italic
        assert "*" in result or "<em>" in result
    
    def test_stars_at_word_boundary(self, md_safe: Markdown) -> None:
        """Test stars at word boundaries."""
        result = md_safe.render("word*word")
        assert "word" in result
    
    def test_only_stars(self, md_safe: Markdown) -> None:
        """Test input with only stars."""
        result = md_safe.render("***")
        assert result  # Should produce something
    
    def test_many_stars(self, md_safe: Markdown) -> None:
        """Test many consecutive stars."""
        result = md_safe.render("*****")
        assert result
    
    def test_alternating_stars(self, md_safe: Markdown) -> None:
        """Test alternating patterns."""
        result = md_safe.render("*a**b*c**")
        assert "a" in result
        assert "b" in result
        assert "c" in result
