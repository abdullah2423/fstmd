"""
Tests for footnote support [^label] and [^label]: definitions.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestBasicFootnotes:
    """Tests for basic footnote functionality."""
    
    def test_single_footnote(self, md_safe: Markdown) -> None:
        """Test basic single footnote reference and definition."""
        text = "This is a sentence with a footnote.[^1]\n\n[^1]: This is the footnote text."
        result = md_safe.render(text)
        
        # Check the reference is rendered correctly
        assert '<sup id="fnref-1"><a href="#fn-1">1</a></sup>' in result
        
        # Check the footnotes section structure
        assert '<section class="footnotes">' in result
        assert '<ol>' in result
        assert '<li id="fn-1">' in result
        assert 'This is the footnote text.' in result
        assert '</section>' in result
    
    def test_footnote_in_paragraph(self, md_safe: Markdown) -> None:
        """Test footnote reference within a paragraph."""
        text = "Some text[^note] and more text.\n\n[^note]: The footnote."
        result = md_safe.render(text)
        
        assert "Some text" in result
        assert '<sup id="fnref-note"><a href="#fn-note">1</a></sup>' in result
        assert "and more text" in result
    
    def test_footnote_at_end_of_sentence(self, md_safe: Markdown) -> None:
        """Test footnote at the end of a sentence."""
        text = "End of sentence.[^1]\n\n[^1]: Footnote text."
        result = md_safe.render(text)
        
        assert "End of sentence." in result
        assert '<sup id="fnref-1">' in result


class TestMultipleFootnotes:
    """Tests for multiple footnotes."""
    
    def test_two_footnotes(self, md_safe: Markdown) -> None:
        """Test two different footnotes."""
        text = "First[^1] and second[^2].\n\n[^1]: First note.\n[^2]: Second note."
        result = md_safe.render(text)
        
        # Check both references
        assert '<sup id="fnref-1"><a href="#fn-1">1</a></sup>' in result
        assert '<sup id="fnref-2"><a href="#fn-2">2</a></sup>' in result
        
        # Check both definitions
        assert '<li id="fn-1">' in result
        assert '<li id="fn-2">' in result
        assert "First note." in result
        assert "Second note." in result
    
    def test_footnote_numbering_by_reference_order(self, md_safe: Markdown) -> None:
        """Test that footnote numbering follows reference order, not definition order."""
        text = "Second ref[^b] then first ref[^a].\n\n[^a]: First defined.\n[^b]: Second defined."
        result = md_safe.render(text)
        
        # [^b] is referenced first, so it gets number 1
        assert '<sup id="fnref-b"><a href="#fn-b">1</a></sup>' in result
        # [^a] is referenced second, so it gets number 2
        assert '<sup id="fnref-a"><a href="#fn-a">2</a></sup>' in result
    
    def test_adjacent_footnotes(self, md_safe: Markdown) -> None:
        """Test two footnotes next to each other."""
        text = "Text[^1][^2] more.\n\n[^1]: First.\n[^2]: Second."
        result = md_safe.render(text)
        
        # Both should be present
        assert 'fnref-1' in result
        assert 'fnref-2' in result


class TestMultipleReferencesToSameFootnote:
    """Tests for multiple references to the same footnote."""
    
    def test_same_footnote_twice(self, md_safe: Markdown) -> None:
        """Test two references to the same footnote."""
        text = "First ref[^1] and second ref[^1].\n\n[^1]: Shared footnote."
        result = md_safe.render(text)
        
        # Both should have the same number (1)
        count = result.count('<a href="#fn-1">1</a>')
        assert count == 2
        
        # Only one definition
        assert result.count('<li id="fn-1">') == 1
    
    def test_many_refs_to_same_footnote(self, md_safe: Markdown) -> None:
        """Test many references to the same footnote."""
        text = "A[^x] B[^x] C[^x] D[^x].\n\n[^x]: Shared note."
        result = md_safe.render(text)
        
        # All four should link to the same footnote
        count = result.count('href="#fn-x"')
        assert count == 4
        
        # Only one definition
        assert result.count('<li id="fn-x">') == 1


class TestMultiLineDefinitions:
    """Tests for multi-line footnote definitions."""
    
    def test_two_line_definition(self, md_safe: Markdown) -> None:
        """Test footnote definition spanning two lines."""
        text = "Text[^1].\n\n[^1]: First line\n      second line."
        result = md_safe.render(text)
        
        # The content should be joined
        assert '<li id="fn-1">' in result
        assert "First line" in result
    
    def test_multiline_with_paragraph(self, md_safe: Markdown) -> None:
        """Test multi-line footnote forms a paragraph."""
        text = "Ref[^1].\n\n[^1]: Line one\n      line two\n      line three."
        result = md_safe.render(text)
        
        assert '<li id="fn-1">' in result


class TestInlineFormattingInFootnotes:
    """Tests for inline formatting inside footnote definitions."""
    
    def test_bold_in_footnote(self, md_safe: Markdown) -> None:
        """Test bold text inside footnote content."""
        text = "Text[^1].\n\n[^1]: This is **bold** text."
        result = md_safe.render(text)
        
        assert '<strong>bold</strong>' in result
    
    def test_italic_in_footnote(self, md_safe: Markdown) -> None:
        """Test italic text inside footnote content."""
        text = "Text[^1].\n\n[^1]: This is *italic* text."
        result = md_safe.render(text)
        
        assert '<em>italic</em>' in result
    
    def test_code_in_footnote(self, md_safe: Markdown) -> None:
        """Test inline code inside footnote content."""
        text = "Text[^1].\n\n[^1]: Use `code` here."
        result = md_safe.render(text)
        
        assert '<code>code</code>' in result
    
    def test_link_in_footnote(self, md_safe: Markdown) -> None:
        """Test link inside footnote content."""
        text = "Text[^1].\n\n[^1]: See [example](https://example.com) site."
        result = md_safe.render(text)
        
        assert '<a href="https://example.com">example</a>' in result
    
    def test_mixed_formatting_in_footnote(self, md_safe: Markdown) -> None:
        """Test mixed formatting in footnote."""
        text = "Text[^1].\n\n[^1]: A **bold** and *italic* and `code` mix."
        result = md_safe.render(text)
        
        assert '<strong>bold</strong>' in result
        assert '<em>italic</em>' in result
        assert '<code>code</code>' in result


class TestSafeModeFootnotes:
    """Tests for SAFE mode escaping in footnotes."""
    
    def test_html_escaped_in_footnote(self, md_safe: Markdown) -> None:
        """Test HTML tags are escaped inside footnote content."""
        text = "Text[^1].\n\n[^1]: Contains <script>alert('xss')</script> tag."
        result = md_safe.render(text)
        
        # The script tag should be escaped
        assert '<script>' not in result
        assert '&lt;script&gt;' in result
    
    def test_html_entities_in_footnote(self, md_safe: Markdown) -> None:
        """Test HTML entities are properly escaped."""
        text = "Text[^1].\n\n[^1]: Has < and > and & symbols."
        result = md_safe.render(text)
        
        assert '&lt;' in result
        assert '&gt;' in result
        assert '&amp;' in result
    
    def test_javascript_url_blocked_in_footnote(self, md_safe: Markdown) -> None:
        """Test javascript: URLs are blocked in footnote links."""
        text = "Text[^1].\n\n[^1]: Bad [link](javascript:alert('xss'))."
        result = md_safe.render(text)
        
        # Should not contain href with javascript:
        assert 'javascript:' not in result or 'href="javascript:' not in result
    
    def test_label_escaped_in_attributes(self, md_safe: Markdown) -> None:
        """Test footnote labels are escaped when used in attributes."""
        # Use a label with special chars (within allowed set)
        text = 'Text[^a-b_c].\n\n[^a-b_c]: Note content.'
        result = md_safe.render(text)
        
        assert 'fnref-a-b_c' in result
        assert 'fn-a-b_c' in result


class TestEdgeCases:
    """Tests for edge cases in footnote handling."""
    
    def test_reference_without_definition(self, md_safe: Markdown) -> None:
        """Test footnote reference with no corresponding definition."""
        text = "Text with orphan[^orphan] reference."
        result = md_safe.render(text)
        
        # The reference should still be rendered
        assert 'fnref-orphan' in result
        # But no footnotes section or it's empty
        # (The reference is output but won't appear in the footnotes list)
        assert '<li id="fn-orphan">' not in result
    
    def test_definition_without_reference(self, md_safe: Markdown) -> None:
        """Test footnote definition that is never referenced."""
        text = "No references here.\n\n[^unused]: This is never used."
        result = md_safe.render(text)
        
        # The definition should not appear in output (no section created)
        assert '<section class="footnotes">' not in result
        assert 'fn-unused' not in result
    
    def test_footnote_at_end_without_newline(self, md_safe: Markdown) -> None:
        """Test footnote at end of document without trailing newline."""
        text = "Text[^1].\n\n[^1]: Footnote at end"
        result = md_safe.render(text)
        
        assert '<li id="fn-1">' in result
        assert "Footnote at end" in result
    
    def test_empty_footnote_label(self, md_safe: Markdown) -> None:
        """Test empty footnote label [^] is treated literally."""
        text = "Text with [^] empty label."
        result = md_safe.render(text)
        
        # Should be treated as literal text, not a footnote
        assert '[^]' in result or ('[' in result and '^]' in result)
        assert '<sup' not in result
    
    def test_invalid_label_chars(self, md_safe: Markdown) -> None:
        """Test footnote with invalid label characters."""
        text = "Text[^hello world] with space."
        result = md_safe.render(text)
        
        # Space breaks the footnote reference
        assert '<sup' not in result or 'fnref-hello world' not in result
    
    def test_footnote_with_numeric_label(self, md_safe: Markdown) -> None:
        """Test footnote with purely numeric label."""
        text = "Text[^123].\n\n[^123]: Numeric note."
        result = md_safe.render(text)
        
        assert 'fnref-123' in result
        assert '<li id="fn-123">' in result
    
    def test_footnote_with_mixed_alphanumeric(self, md_safe: Markdown) -> None:
        """Test footnote with mixed alphanumeric label."""
        text = "Text[^note_1a].\n\n[^note_1a]: Mixed label."
        result = md_safe.render(text)
        
        assert 'fnref-note_1a' in result
        assert '<li id="fn-note_1a">' in result
    
    def test_bracket_not_footnote(self, md_safe: Markdown) -> None:
        """Test [text] without ^ is not a footnote."""
        text = "This is [not a footnote]."
        result = md_safe.render(text)
        
        # Should not create a footnote reference
        assert '<sup' not in result
    
    def test_caret_without_bracket(self, md_safe: Markdown) -> None:
        """Test ^ without [ is regular text."""
        text = "Power of 2^10 is 1024."
        result = md_safe.render(text)
        
        assert "2^10" in result or ("2" in result and "^" in result and "10" in result)


class TestFootnoteHTMLStructure:
    """Tests for correct HTML structure of footnotes."""
    
    def test_section_structure(self, md_safe: Markdown) -> None:
        """Test the overall section structure."""
        text = "Ref[^1].\n\n[^1]: Content."
        result = md_safe.render(text)
        
        # Check structure order
        section_start = result.find('<section class="footnotes">')
        ol_start = result.find('<ol>')
        li_start = result.find('<li id="fn-1">')
        p_start = result.find('Content.')
        li_end = result.find('</li>')
        ol_end = result.find('</ol>')
        section_end = result.find('</section>')
        
        assert section_start < ol_start < li_start < p_start < li_end < ol_end < section_end
    
    def test_multiple_footnotes_ordered(self, md_safe: Markdown) -> None:
        """Test multiple footnotes appear in reference order in the list."""
        text = "A[^z] B[^a].\n\n[^a]: Alpha.\n[^z]: Zulu."
        result = md_safe.render(text)
        
        # z should come first (referenced first)
        z_pos = result.find('fn-z')
        a_pos = result.find('fn-a')
        
        # In the footnotes section (at the end), z should be before a
        # We need to find them in the <li> section
        li_z = result.find('<li id="fn-z">')
        li_a = result.find('<li id="fn-a">')
        
        assert li_z < li_a  # z appears first because it was referenced first
    
    def test_footnote_content_wrapped_in_p(self, md_safe: Markdown) -> None:
        """Test footnote content is wrapped in paragraph tags."""
        text = "Ref[^1].\n\n[^1]: Paragraph content."
        result = md_safe.render(text)
        
        # Content should be inside <p> tags within the <li>
        li_start = result.find('<li id="fn-1">')
        li_end = result.find('</li>', li_start)
        li_content = result[li_start:li_end]
        
        assert '<p>' in li_content
        assert '</p>' in li_content


class TestFootnoteLabelVariations:
    """Tests for various valid footnote label formats."""
    
    def test_single_letter_label(self, md_safe: Markdown) -> None:
        """Test single letter label."""
        text = "Text[^a].\n\n[^a]: Note."
        result = md_safe.render(text)
        assert 'fn-a' in result
    
    def test_single_digit_label(self, md_safe: Markdown) -> None:
        """Test single digit label."""
        text = "Text[^1].\n\n[^1]: Note."
        result = md_safe.render(text)
        assert 'fn-1' in result
    
    def test_underscore_label(self, md_safe: Markdown) -> None:
        """Test label with underscores."""
        text = "Text[^my_note].\n\n[^my_note]: Note."
        result = md_safe.render(text)
        assert 'fn-my_note' in result
    
    def test_dash_label(self, md_safe: Markdown) -> None:
        """Test label with dashes."""
        text = "Text[^my-note].\n\n[^my-note]: Note."
        result = md_safe.render(text)
        assert 'fn-my-note' in result
    
    def test_long_label(self, md_safe: Markdown) -> None:
        """Test long label."""
        text = "Text[^very_long_footnote_label_123].\n\n[^very_long_footnote_label_123]: Note."
        result = md_safe.render(text)
        assert 'fn-very_long_footnote_label_123' in result
    
    def test_case_sensitive_labels(self, md_safe: Markdown) -> None:
        """Test that labels are case-sensitive."""
        text = "A[^Note] B[^note].\n\n[^Note]: Upper.\n[^note]: Lower."
        result = md_safe.render(text)
        
        assert 'fn-Note' in result
        assert 'fn-note' in result


class TestFootnotesWithOtherElements:
    """Tests for footnotes interacting with other Markdown elements."""
    
    def test_footnote_in_heading(self, md_safe: Markdown) -> None:
        """Test footnote reference in a heading."""
        text = "# Heading with note[^1]\n\n[^1]: Heading footnote."
        result = md_safe.render(text)
        
        assert '<h1>' in result
        assert 'fnref-1' in result
    
    def test_footnote_in_list(self, md_safe: Markdown) -> None:
        """Test footnote reference in a list item."""
        text = "- Item with note[^1]\n\n[^1]: List footnote."
        result = md_safe.render(text)
        
        assert '<li>' in result
        assert 'fnref-1' in result
    
    def test_footnote_in_blockquote(self, md_safe: Markdown) -> None:
        """Test footnote reference in a blockquote."""
        text = "> Quote with note[^1]\n\n[^1]: Quote footnote."
        result = md_safe.render(text)
        
        assert '<blockquote>' in result
        assert 'fnref-1' in result
    
    def test_footnote_not_in_code_block(self, md_safe: Markdown) -> None:
        """Test footnote syntax in code block is not parsed."""
        text = "```\n[^1]\n```\n\n[^1]: Not rendered."
        result = md_safe.render(text)
        
        # The [^1] inside code should be literal
        assert '<code>[^1]' in result or '<code>\n[^1]' in result
    
    def test_footnote_not_in_inline_code(self, md_safe: Markdown) -> None:
        """Test footnote syntax in inline code is not parsed."""
        text = "Use `[^1]` for footnotes.[^1]\n\n[^1]: Real note."
        result = md_safe.render(text)
        
        # One is in code (literal), one is a real reference
        assert '<code>[^1]</code>' in result
        # The real reference
        assert 'fnref-1' in result


class TestRawModeFootnotes:
    """Tests for footnotes in raw mode."""
    
    def test_footnote_in_raw_mode(self, md_raw: Markdown) -> None:
        """Test footnotes work in raw mode."""
        text = "Text[^1].\n\n[^1]: Note."
        result = md_raw.render(text)
        
        assert 'fnref-1' in result
        assert 'fn-1' in result
    
    def test_html_not_escaped_in_raw_footnote(self, md_raw: Markdown) -> None:
        """Test HTML is not escaped in raw mode footnotes."""
        text = "Text[^1].\n\n[^1]: Has <b>bold</b> HTML."
        result = md_raw.render(text)
        
        # In raw mode, HTML passes through
        assert '<b>bold</b>' in result
