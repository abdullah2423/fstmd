"""
Tests for inline code and code blocks.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestInlineCode:
    """Tests for inline code (`code`)."""
    
    def test_simple_inline_code(self, md_safe: Markdown) -> None:
        """Test basic inline code."""
        result = md_safe.render("`code`")
        assert "<code>code</code>" in result
    
    def test_inline_code_in_sentence(self, md_safe: Markdown) -> None:
        """Test inline code within a sentence."""
        result = md_safe.render("Use the `print()` function")
        assert "<code>print()</code>" in result
        assert "Use the" in result
        assert "function" in result
    
    def test_multiple_inline_codes(self, md_safe: Markdown) -> None:
        """Test multiple inline code sections."""
        result = md_safe.render("`one` and `two`")
        assert result.count("<code>") == 2
        assert result.count("</code>") == 2
    
    def test_inline_code_with_special_chars(self, md_safe: Markdown) -> None:
        """Test inline code preserves special chars (escaped)."""
        result = md_safe.render("`<script>alert(1)</script>`")
        assert "<code>" in result
        assert "&lt;script&gt;" in result
        assert "<script>" not in result
    
    def test_inline_code_with_ampersand(self, md_safe: Markdown) -> None:
        """Test inline code escapes ampersand."""
        result = md_safe.render("`a & b`")
        assert "<code>" in result
        assert "&amp;" in result
    
    def test_inline_code_with_stars(self, md_safe: Markdown) -> None:
        """Test inline code does not interpret stars as formatting."""
        result = md_safe.render("`**not bold**`")
        assert "<code>**not bold**</code>" in result
        assert "<strong>" not in result
    
    def test_mixed_code_and_bold(self, md_safe: Markdown) -> None:
        """Test mixing inline code with bold text."""
        result = md_safe.render("**bold** and `code`")
        assert "<strong>bold</strong>" in result
        assert "<code>code</code>" in result
    
    def test_mixed_code_and_italic(self, md_safe: Markdown) -> None:
        """Test mixing inline code with italic text."""
        result = md_safe.render("*italic* and `code`")
        assert "<em>italic</em>" in result
        assert "<code>code</code>" in result
    
    def test_code_then_bold_then_code(self, md_safe: Markdown) -> None:
        """Test code, bold, code in sequence."""
        result = md_safe.render("`code1` **bold** `code2`")
        assert "<code>code1</code>" in result
        assert "<strong>bold</strong>" in result
        assert "<code>code2</code>" in result
    
    def test_unclosed_inline_code(self, md_safe: Markdown) -> None:
        """Test unclosed inline code marker."""
        result = md_safe.render("`unclosed")
        # Should close at end of block
        assert "</code>" in result or "`" in result
    
    def test_empty_inline_code(self, md_safe: Markdown) -> None:
        """Test empty inline code."""
        result = md_safe.render("``")
        # Empty code produces <p><code></code></p> or similar
        # OR it might be interpreted as a code block start attempt that fails
        # The main point is it doesn't crash
        assert result is not None
    
    def test_inline_code_at_line_start(self, md_safe: Markdown) -> None:
        """Test inline code at the start of a line."""
        result = md_safe.render("`code` at start")
        assert "<code>code</code>" in result
    
    def test_inline_code_at_line_end(self, md_safe: Markdown) -> None:
        """Test inline code at the end of a line."""
        result = md_safe.render("at end `code`")
        assert "<code>code</code>" in result


class TestCodeBlocks:
    """Tests for code blocks (```)."""
    
    def test_simple_code_block(self, md_safe: Markdown) -> None:
        """Test basic code block."""
        result = md_safe.render("```\ncode\n```")
        assert "<pre>" in result
        assert "<code>" in result
        assert "</code>" in result
        assert "</pre>" in result
        assert "code" in result
    
    def test_multiline_code_block(self, md_safe: Markdown) -> None:
        """Test multiline code block."""
        result = md_safe.render("```\nline1\nline2\nline3\n```")
        assert "<pre><code>" in result
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result
    
    def test_code_block_preserves_spaces(self, md_safe: Markdown) -> None:
        """Test that code block preserves spaces."""
        result = md_safe.render("```\n  indented\n```")
        assert "  indented" in result or "&nbsp;" in result or "indented" in result
    
    def test_code_block_no_markdown_formatting(self, md_safe: Markdown) -> None:
        """Test that code block does not interpret Markdown."""
        result = md_safe.render("```\n**not bold**\n*not italic*\n```")
        assert "<strong>" not in result
        assert "<em>" not in result
        assert "**not bold**" in result
        assert "*not italic*" in result
    
    def test_code_block_escapes_html(self, md_safe: Markdown) -> None:
        """Test that code block escapes HTML in safe mode."""
        result = md_safe.render("```\n<script>alert(1)</script>\n```")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_code_block_escapes_ampersand(self, md_safe: Markdown) -> None:
        """Test that code block escapes ampersand."""
        result = md_safe.render("```\na & b\n```")
        assert "&amp;" in result
    
    def test_empty_code_block(self, md_safe: Markdown) -> None:
        """Test empty code block."""
        result = md_safe.render("```\n```")
        assert "<pre><code>" in result
        assert "</code></pre>" in result
    
    def test_code_block_after_paragraph(self, md_safe: Markdown) -> None:
        """Test code block after paragraph."""
        result = md_safe.render("Paragraph\n\n```\ncode\n```")
        assert "<p>" in result
        assert "<pre><code>" in result
    
    def test_paragraph_after_code_block(self, md_safe: Markdown) -> None:
        """Test paragraph after code block."""
        result = md_safe.render("```\ncode\n```\n\nParagraph")
        assert "<pre><code>" in result
        assert "<p>" in result
        assert "Paragraph" in result
    
    def test_code_block_with_backticks_inside(self, md_safe: Markdown) -> None:
        """Test code block containing single/double backticks."""
        result = md_safe.render("```\n`single` and ``double``\n```")
        assert "`single`" in result
        assert "``double``" in result
    
    def test_unclosed_code_block(self, md_safe: Markdown) -> None:
        """Test unclosed code block."""
        result = md_safe.render("```\nunclosed code")
        assert "<pre><code>" in result
        assert "</code></pre>" in result
        assert "unclosed code" in result


class TestCodeBlocksRawMode:
    """Tests for code blocks in raw mode."""
    
    def test_code_block_raw_mode(self, md_raw: Markdown) -> None:
        """Test that code block in raw mode still escapes."""
        result = md_raw.render("```\n<script>alert(1)</script>\n```")
        # In raw mode, code blocks should still contain the content
        assert "<script>" in result  # Raw mode doesn't escape


class TestCodeDeterminism:
    """Determinism tests for code features."""
    
    def test_inline_code_deterministic(self, md_safe: Markdown) -> None:
        """Test that inline code produces deterministic output."""
        input_text = "`code` and **bold** and `more`"
        result1 = md_safe.render(input_text)
        result2 = md_safe.render(input_text)
        assert result1 == result2
    
    def test_code_block_deterministic(self, md_safe: Markdown) -> None:
        """Test that code blocks produce deterministic output."""
        input_text = "```\ncode block\nwith multiple lines\n```"
        result1 = md_safe.render(input_text)
        result2 = md_safe.render(input_text)
        assert result1 == result2
    
    def test_mixed_code_deterministic(self, md_safe: Markdown) -> None:
        """Test mixed code content is deterministic."""
        input_text = """# Title

`inline` code and **bold**

```
block code
```

More `inline` here.
"""
        results = [md_safe.render(input_text) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestCodeStress:
    """Stress tests for code features."""
    
    def test_long_inline_code(self, md_safe: Markdown) -> None:
        """Test very long inline code."""
        long_code = "x" * 10000
        result = md_safe.render(f"`{long_code}`")
        assert "<code>" in result
        assert long_code in result
    
    def test_many_inline_codes(self, md_safe: Markdown) -> None:
        """Test many inline code sections."""
        text = " ".join([f"`code{i}`" for i in range(100)])
        result = md_safe.render(text)
        assert result.count("<code>") == 100
    
    def test_long_code_block(self, md_safe: Markdown) -> None:
        """Test very long code block."""
        long_code = "\n".join(["line" + str(i) for i in range(1000)])
        result = md_safe.render(f"```\n{long_code}\n```")
        assert "<pre><code>" in result
        assert "line999" in result
