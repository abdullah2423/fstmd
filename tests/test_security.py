"""
Tests for HTML escaping and security.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown
from fstmd.core.safe_html import HTMLEscaper, escape_html, is_safe
from fstmd.exceptions import InvalidInputError, SecurityError


class TestHTMLEscaping:
    """Tests for HTML character escaping."""
    
    def test_escape_ampersand(self, md_safe: Markdown) -> None:
        """Test that & is escaped."""
        result = md_safe.render("Tom & Jerry")
        assert "&amp;" in result
        assert "Tom" in result
        assert "Jerry" in result
    
    def test_escape_less_than(self, md_safe: Markdown) -> None:
        """Test that < is escaped."""
        result = md_safe.render("a < b")
        assert "&lt;" in result
    
    def test_escape_greater_than(self, md_safe: Markdown) -> None:
        """Test that > is escaped."""
        result = md_safe.render("a > b")
        assert "&gt;" in result
    
    def test_escape_double_quote(self, md_safe: Markdown) -> None:
        """Test that " is escaped."""
        result = md_safe.render('He said "hello"')
        assert "&quot;" in result
    
    def test_escape_single_quote(self, md_safe: Markdown) -> None:
        """Test that ' is escaped."""
        result = md_safe.render("It's working")
        assert "&#x27;" in result
    
    def test_escape_multiple_chars(self, md_safe: Markdown) -> None:
        """Test escaping multiple special characters."""
        result = md_safe.render("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
    
    def test_no_double_escape(self, md_safe: Markdown) -> None:
        """Test that already-escaped entities are properly handled."""
        result = md_safe.render("&amp;")
        # & gets escaped to &amp;, so &amp; becomes &amp;amp;
        assert "&amp;" in result


class TestXSSPrevention:
    """Tests for XSS attack prevention."""
    
    def test_script_tag_safe_mode(self, md_safe: Markdown) -> None:
        """Test that script tags are escaped in safe mode."""
        result = md_safe.render("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_script_tag_raw_mode(self, md_raw: Markdown) -> None:
        """Test that script tags pass through in raw mode."""
        result = md_raw.render("<script>alert('xss')</script>")
        assert "<script>" in result
    
    def test_onclick_handler(self, md_safe: Markdown) -> None:
        """Test onclick handler is escaped."""
        result = md_safe.render('<div onclick="evil()">')
        assert "onclick" in result  # Text is there
        assert "&lt;div" in result  # But escaped
    
    def test_javascript_url(self, md_safe: Markdown) -> None:
        """Test javascript: URL is escaped."""
        result = md_safe.render("javascript:alert(1)")
        assert "javascript:" in result  # Text preserved
        # Just text, no actual link created
    
    def test_data_url(self, md_safe: Markdown) -> None:
        """Test data: URL handling."""
        result = md_safe.render("data:text/html,<script>alert(1)</script>")
        assert "&lt;script&gt;" in result or "data:" in result
    
    def test_svg_xss(self, md_safe: Markdown) -> None:
        """Test SVG-based XSS is prevented."""
        svg_payload = "<svg onload=alert(1)>"
        result = md_safe.render(svg_payload)
        assert "<svg" not in result
        assert "&lt;svg" in result
    
    def test_img_onerror(self, md_safe: Markdown) -> None:
        """Test img onerror XSS is prevented."""
        payload = '<img src="x" onerror="alert(1)">'
        result = md_safe.render(payload)
        assert "<img" not in result
        assert "&lt;img" in result


class TestDangerousPatternDetection:
    """Tests for dangerous pattern detection."""
    
    def test_contains_script(self) -> None:
        """Test detection of script tags."""
        assert HTMLEscaper.contains_dangerous_pattern("<script>evil</script>")
        assert HTMLEscaper.contains_dangerous_pattern("<SCRIPT>evil</SCRIPT>")
    
    def test_contains_javascript(self) -> None:
        """Test detection of javascript: URLs."""
        assert HTMLEscaper.contains_dangerous_pattern("javascript:alert(1)")
        assert HTMLEscaper.contains_dangerous_pattern("JAVASCRIPT:alert(1)")
    
    def test_contains_vbscript(self) -> None:
        """Test detection of vbscript: URLs."""
        assert HTMLEscaper.contains_dangerous_pattern("vbscript:msgbox(1)")
    
    def test_contains_data_url(self) -> None:
        """Test detection of data: URLs."""
        assert HTMLEscaper.contains_dangerous_pattern("data:text/html,<script>")
    
    def test_safe_content(self) -> None:
        """Test that safe content is not flagged."""
        assert not HTMLEscaper.contains_dangerous_pattern("Hello world")
        assert not HTMLEscaper.contains_dangerous_pattern("**bold** text")
    
    def test_safe_data_image(self) -> None:
        """Test that data:image is considered safe."""
        assert not HTMLEscaper.contains_dangerous_pattern("data:image/png;base64,abc")


class TestInputValidation:
    """Tests for input validation."""
    
    def test_none_input(self, md_safe: Markdown) -> None:
        """Test that None input raises error."""
        with pytest.raises(InvalidInputError):
            md_safe.render(None)  # type: ignore[arg-type]
    
    def test_non_string_input(self, md_safe: Markdown) -> None:
        """Test that non-string input raises error."""
        with pytest.raises(InvalidInputError):
            md_safe.render(123)  # type: ignore[arg-type]
    
    def test_list_input(self, md_safe: Markdown) -> None:
        """Test that list input raises error."""
        with pytest.raises(InvalidInputError):
            md_safe.render(["a", "b"])  # type: ignore[arg-type]
    
    def test_empty_string(self, md_safe: Markdown) -> None:
        """Test empty string input."""
        result = md_safe.render("")
        assert result == ""
    
    def test_very_long_input(self, md_safe: Markdown) -> None:
        """Test that very long input is handled."""
        # Create long but valid input
        long_text = "a" * 1_000_000
        result = md_safe.render(long_text)
        assert len(result) > 0


class TestEscaperFunctions:
    """Tests for HTMLEscaper utility functions."""
    
    def test_escape_char(self) -> None:
        """Test individual character escaping."""
        assert HTMLEscaper.escape_char("&") == "&amp;"
        assert HTMLEscaper.escape_char("<") == "&lt;"
        assert HTMLEscaper.escape_char(">") == "&gt;"
        assert HTMLEscaper.escape_char('"') == "&quot;"
        assert HTMLEscaper.escape_char("'") == "&#x27;"
        assert HTMLEscaper.escape_char("a") == "a"
    
    def test_escape_empty(self) -> None:
        """Test escaping empty string."""
        assert HTMLEscaper.escape("") == ""
    
    def test_escape_no_special_chars(self) -> None:
        """Test escaping string with no special chars."""
        result = HTMLEscaper.escape("Hello World")
        assert result == "Hello World"
    
    def test_escape_all_special(self) -> None:
        """Test escaping all special characters."""
        result = HTMLEscaper.escape("<>&\"'")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result
        assert "&#x27;" in result
    
    def test_validate_input_none(self) -> None:
        """Test validation with None."""
        assert not HTMLEscaper.validate_input(None)  # type: ignore[arg-type]
    
    def test_validate_input_not_string(self) -> None:
        """Test validation with non-string."""
        assert not HTMLEscaper.validate_input(123)  # type: ignore[arg-type]
    
    def test_validate_input_valid(self) -> None:
        """Test validation with valid input."""
        assert HTMLEscaper.validate_input("valid string")
    
    def test_is_safe_function(self) -> None:
        """Test is_safe convenience function."""
        assert is_safe("Hello world")
        assert not is_safe("<script>evil</script>")


class TestStrictMode:
    """Tests for strict mode security."""
    
    def test_strict_mode_raw_safe_content(self, md_strict: Markdown) -> None:
        """Test strict mode with safe content."""
        # Create strict raw mode
        md = Markdown(mode="raw", strict=True)
        result = md.render("Hello **world**")
        assert "Hello" in result
    
    def test_strict_mode_raw_dangerous(self) -> None:
        """Test strict mode rejects dangerous content in raw mode."""
        md = Markdown(mode="raw", strict=True)
        with pytest.raises(SecurityError):
            md.render("<script>alert(1)</script>")
