"""
Tests for image formatting ![alt](url).
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestSimpleImages:
    """Tests for basic image functionality."""
    
    def test_simple_image(self, md_safe: Markdown) -> None:
        """Test basic image formatting."""
        result = md_safe.render("![alt text](https://example.com/image.png)")
        assert '<img src="https://example.com/image.png" alt="alt text"/>' in result
    
    def test_image_in_paragraph(self, md_safe: Markdown) -> None:
        """Test image within a paragraph."""
        result = md_safe.render("Here is ![an image](https://example.com/img.jpg) inline")
        assert '<img src="https://example.com/img.jpg" alt="an image"/>' in result
        assert "Here is" in result
        assert "inline" in result
    
    def test_multiple_images(self, md_safe: Markdown) -> None:
        """Test multiple images."""
        result = md_safe.render("![img1](url1) ![img2](url2)")
        assert '<img src="url1" alt="img1"/>' in result
        assert '<img src="url2" alt="img2"/>' in result
    
    def test_image_at_start(self, md_safe: Markdown) -> None:
        """Test image at start of text."""
        result = md_safe.render("![image](url) followed by text")
        assert '<img src="url" alt="image"/>' in result
        assert "followed by text" in result
    
    def test_image_at_end(self, md_safe: Markdown) -> None:
        """Test image at end of text."""
        result = md_safe.render("Text with ![image](url)")
        assert '<img src="url" alt="image"/>' in result
        assert "Text with" in result


class TestImageAltText:
    """Tests for image alt text handling."""
    
    def test_image_empty_alt(self, md_safe: Markdown) -> None:
        """Test image with empty alt text."""
        result = md_safe.render("![](https://example.com/image.png)")
        assert '<img src="https://example.com/image.png" alt=""/>' in result
    
    def test_image_alt_with_spaces(self, md_safe: Markdown) -> None:
        """Test image alt with spaces."""
        result = md_safe.render("![alt text with spaces](url)")
        assert 'alt="alt text with spaces"' in result
    
    def test_image_alt_with_punctuation(self, md_safe: Markdown) -> None:
        """Test image alt with punctuation."""
        result = md_safe.render("![Hello, World!](url)")
        assert 'alt="Hello, World!"' in result
    
    def test_image_alt_escaping(self, md_safe: Markdown) -> None:
        """Test that alt text special chars are escaped."""
        result = md_safe.render('![alt with "quotes"](url)')
        assert "&quot;" in result
    
    def test_image_alt_with_ampersand(self, md_safe: Markdown) -> None:
        """Test alt text with ampersand."""
        result = md_safe.render("![Tom & Jerry](url)")
        assert "&amp;" in result


class TestImageEmptyUrl:
    """Tests for images with empty URL."""
    
    def test_image_empty_url(self, md_safe: Markdown) -> None:
        """Test image with empty URL."""
        result = md_safe.render("![alt text]()")
        assert '<img src="" alt="alt text"/>' in result


class TestImageEdgeCases:
    """Tests for edge cases in image parsing."""
    
    def test_bang_without_bracket(self, md_safe: Markdown) -> None:
        """Test ! without [ following."""
        result = md_safe.render("Hello! world")
        assert "Hello!" in result
        assert "world" in result
        assert "<img" not in result
    
    def test_bang_at_end(self, md_safe: Markdown) -> None:
        """Test ! at end of text."""
        result = md_safe.render("Exciting!")
        assert "Exciting!" in result
        assert "<img" not in result
    
    def test_unclosed_image_alt(self, md_safe: Markdown) -> None:
        """Test unclosed image alt bracket."""
        result = md_safe.render("![unclosed alt")
        assert "![" in result
        assert "unclosed alt" in result
    
    def test_image_bracket_without_url(self, md_safe: Markdown) -> None:
        """Test image brackets without URL."""
        result = md_safe.render("![alt] without url")
        assert "![alt]" in result
        assert "without url" in result
    
    def test_image_with_newline_in_alt(self, md_safe: Markdown) -> None:
        """Test image with newline in alt - should break."""
        result = md_safe.render("![line1\nline2](url)")
        assert '<img src="url"' not in result
    
    def test_image_with_newline_in_url(self, md_safe: Markdown) -> None:
        """Test image with newline in URL - should break."""
        result = md_safe.render("![alt](url\npart2)")
        assert '<img src="url' not in result
    
    def test_nested_brackets_in_image(self, md_safe: Markdown) -> None:
        """Test nested brackets in image."""
        result = md_safe.render("![[nested]](url)")
        # Should not parse as image due to nested [
        assert "[[" in result
    
    def test_adjacent_images(self, md_safe: Markdown) -> None:
        """Test two images directly adjacent."""
        result = md_safe.render("![a](u1)![b](u2)")
        assert '<img src="u1" alt="a"/>' in result
        assert '<img src="u2" alt="b"/>' in result


class TestImageSecurity:
    """Tests for image URL security in safe mode."""
    
    def test_javascript_url_blocked(self, md_safe: Markdown) -> None:
        """Test javascript: URL is blocked in images."""
        result = md_safe.render("![img](javascript:alert(1))")
        assert 'src="javascript:' not in result
    
    def test_javascript_url_case_insensitive(self, md_safe: Markdown) -> None:
        """Test JavaScript: URL (mixed case) is blocked."""
        result = md_safe.render("![img](JAVASCRIPT:alert(1))")
        assert 'src="javascript:' not in result.lower()
    
    def test_vbscript_url_blocked(self, md_safe: Markdown) -> None:
        """Test vbscript: URL is blocked."""
        result = md_safe.render("![img](vbscript:msgbox(1))")
        assert 'src="vbscript:' not in result
    
    def test_data_url_blocked(self, md_safe: Markdown) -> None:
        """Test data: URL is blocked."""
        result = md_safe.render("![img](data:text/html,<script>alert(1)</script>)")
        assert 'src="data:' not in result
    
    def test_javascript_url_allowed_raw_mode(self, md_raw: Markdown) -> None:
        """Test javascript: URL passes in raw mode."""
        # Note: parens in URL would need escaping in standard Markdown
        result = md_raw.render("![img](javascript:void)")
        assert 'src="javascript:void"' in result
    
    def test_url_with_html_special_chars_escaped(self, md_safe: Markdown) -> None:
        """Test URL special characters are escaped."""
        result = md_safe.render('![img](https://example.com?a=1&b=2")')
        assert "&amp;" in result
        assert "&quot;" in result


class TestImageURLProtocols:
    """Tests for various URL protocols in images."""
    
    def test_https_image(self, md_safe: Markdown) -> None:
        """Test HTTPS image."""
        result = md_safe.render("![img](https://example.com/img.png)")
        assert 'src="https://example.com/img.png"' in result
    
    def test_http_image(self, md_safe: Markdown) -> None:
        """Test HTTP image."""
        result = md_safe.render("![img](http://example.com/img.png)")
        assert 'src="http://example.com/img.png"' in result
    
    def test_relative_image(self, md_safe: Markdown) -> None:
        """Test relative image path."""
        result = md_safe.render("![img](/images/photo.jpg)")
        assert 'src="/images/photo.jpg"' in result
    
    def test_relative_image_dot(self, md_safe: Markdown) -> None:
        """Test relative image path with dot."""
        result = md_safe.render("![img](./images/photo.jpg)")
        assert 'src="./images/photo.jpg"' in result


class TestImageStress:
    """Stress tests for images."""
    
    def test_many_images(self, md_safe: Markdown) -> None:
        """Test many images in sequence."""
        images = " ".join(f"![img{i}](url{i})" for i in range(20))
        result = md_safe.render(images)
        for i in range(20):
            assert f'<img src="url{i}" alt="img{i}"/>' in result
    
    def test_long_url(self, md_safe: Markdown) -> None:
        """Test image with very long URL."""
        long_url = "https://example.com/" + "a" * 1000
        result = md_safe.render(f"![img]({long_url})")
        assert f'src="{long_url}"' in result
    
    def test_long_alt(self, md_safe: Markdown) -> None:
        """Test image with very long alt text."""
        long_alt = "a" * 500
        result = md_safe.render(f"![{long_alt}](url)")
        assert f'alt="{long_alt}"' in result


class TestMixedLinksAndImages:
    """Tests for links and images together."""
    
    def test_link_then_image(self, md_safe: Markdown) -> None:
        """Test link followed by image."""
        result = md_safe.render("[link](url1) ![img](url2)")
        assert '<a href="url1">link</a>' in result
        assert '<img src="url2" alt="img"/>' in result
    
    def test_image_then_link(self, md_safe: Markdown) -> None:
        """Test image followed by link."""
        result = md_safe.render("![img](url1) [link](url2)")
        assert '<img src="url1" alt="img"/>' in result
        assert '<a href="url2">link</a>' in result
    
    def test_link_and_image_adjacent(self, md_safe: Markdown) -> None:
        """Test link and image directly adjacent."""
        result = md_safe.render("[link](url1)![img](url2)")
        assert '<a href="url1">link</a>' in result
        assert '<img src="url2" alt="img"/>' in result
    
    def test_alternating_links_images(self, md_safe: Markdown) -> None:
        """Test alternating links and images."""
        result = md_safe.render("[l1](u1) ![i1](u2) [l2](u3) ![i2](u4)")
        assert '<a href="u1">l1</a>' in result
        assert '<img src="u2" alt="i1"/>' in result
        assert '<a href="u3">l2</a>' in result
        assert '<img src="u4" alt="i2"/>' in result


class TestParagraphBoundaries:
    """Tests for image interaction with paragraph boundaries."""
    
    def test_image_only_paragraph(self, md_safe: Markdown) -> None:
        """Test paragraph containing only an image."""
        result = md_safe.render("![alt](url)")
        assert "<p>" in result
        assert "</p>" in result
        assert '<img src="url" alt="alt"/>' in result
    
    def test_image_between_paragraphs(self, md_safe: Markdown) -> None:
        """Test image between two paragraphs."""
        result = md_safe.render("Para 1\n\n![img](url)\n\nPara 2")
        assert "Para 1" in result
        assert "Para 2" in result
        assert '<img src="url" alt="img"/>' in result
    
    def test_image_at_paragraph_start(self, md_safe: Markdown) -> None:
        """Test image at start of paragraph."""
        result = md_safe.render("![img](url) text follows")
        assert '<img src="url" alt="img"/>' in result
        assert "text follows" in result
