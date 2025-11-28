"""
Integration tests for the complete Markdown parser.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown, __version__


class TestPublicAPI:
    """Tests for the public API."""
    
    def test_version(self) -> None:
        """Test version is defined."""
        assert __version__
        assert isinstance(__version__, str)
    
    def test_markdown_class_exists(self) -> None:
        """Test Markdown class is importable."""
        from fstmd import Markdown
        assert Markdown is not None
    
    def test_default_mode(self) -> None:
        """Test default mode is safe."""
        md = Markdown()
        assert md.mode == "safe"
    
    def test_custom_mode(self) -> None:
        """Test custom mode setting."""
        md = Markdown(mode="raw")
        assert md.mode == "raw"
    
    def test_repr(self) -> None:
        """Test string representation."""
        md = Markdown(mode="safe", strict=True)
        repr_str = repr(md)
        assert "Markdown" in repr_str
        assert "safe" in repr_str


class TestRenderFunction:
    """Tests for the render convenience function."""
    
    def test_render_function(self) -> None:
        """Test render function."""
        from fstmd.parser import render
        result = render("**bold**")
        assert "<strong>bold</strong>" in result
    
    def test_render_unsafe_function(self) -> None:
        """Test render_unsafe function."""
        from fstmd.parser import render_unsafe
        result = render_unsafe("<b>raw</b>")
        assert "<b>raw</b>" in result


class TestRealWorldDocuments:
    """Tests with real-world document patterns."""
    
    def test_readme_style_document(self, md_safe: Markdown) -> None:
        """Test README-style document."""
        doc = """# Project Name

A short description of the project.

## Installation

Run the following command:

- Install with pip

## Usage

Use **bold** for emphasis and *italic* for alternatives.

## License

MIT License
"""
        result = md_safe.render(doc)
        assert "<h1>Project Name</h1>" in result
        assert "<h2>Installation</h2>" in result
        assert "<h2>Usage</h2>" in result
        assert "<ul>" in result
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result
    
    def test_blog_post_style(self, md_safe: Markdown) -> None:
        """Test blog post style document."""
        doc = """# My Blog Post

Welcome to my **awesome** blog post!

Today we'll discuss *important* topics.

## First Point

Here's what I think:

- Point one
- Point two
- Point three

## Conclusion

Thanks for reading!
"""
        result = md_safe.render(doc)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<p>" in result
        assert "<ul>" in result
    
    def test_technical_doc_style(self, md_safe: Markdown) -> None:
        """Test technical documentation style."""
        doc = """# API Reference

## Function: process

Processes the input **synchronously**.

### Parameters

- *input* - The input string
- *options* - Optional configuration

### Returns

Returns a **string** result.
"""
        result = md_safe.render(doc)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<h3>" in result
        assert "<ul>" in result


class TestEdgeCases:
    """Edge case tests."""
    
    def test_unicode_content(self, md_safe: Markdown) -> None:
        """Test Unicode content handling."""
        result = md_safe.render("# こんにちは\n\n**世界**")
        assert "こんにちは" in result
        assert "世界" in result
    
    def test_emoji_content(self, md_safe: Markdown) -> None:
        """Test emoji handling."""
        result = md_safe.render("# Hello 👋\n\n**World** 🌍")
        assert "👋" in result
        assert "🌍" in result
    
    def test_very_long_line(self, md_safe: Markdown) -> None:
        """Test very long line."""
        long_line = "word " * 1000
        result = md_safe.render(long_line)
        assert "word" in result
    
    def test_many_short_lines(self, md_safe: Markdown) -> None:
        """Test many short lines."""
        lines = "\n".join(["line"] * 100)
        result = md_safe.render(lines)
        assert "line" in result
    
    def test_deep_formatting(self, md_safe: Markdown) -> None:
        """Test deeply nested formatting attempts."""
        # Not truly nested, but multiple markers
        text = "***bold and italic***"
        result = md_safe.render(text)
        assert "bold and italic" in result
    
    def test_all_special_chars(self, md_safe: Markdown) -> None:
        """Test all HTML special characters."""
        text = "Test: < > & \" '"
        result = md_safe.render(text)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
        assert "&#x27;" in result


class TestRenderSafe:
    """Tests for render_safe method."""
    
    def test_render_safe_from_raw_instance(self) -> None:
        """Test render_safe works on raw instance."""
        md = Markdown(mode="raw")
        result = md.render_safe("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_render_safe_escapes(self) -> None:
        """Test render_safe always escapes."""
        md = Markdown(mode="raw")
        result = md.render_safe("**<b>test</b>**")
        assert "<b>" not in result
        assert "&lt;b&gt;" in result
