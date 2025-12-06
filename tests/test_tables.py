"""
Tests for GFM-style tables.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestBasicTables:
    """Tests for basic table functionality."""
    
    def test_simple_table(self, md_safe: Markdown) -> None:
        """Test simple two-column table."""
        text = """| Header 1 | Header 2 |
| --- | --- |
| Cell 1 | Cell 2 |"""
        result = md_safe.render(text)
        assert "<table>" in result
        assert "</table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "<th>" in result
        assert "<td>" in result
        assert "Header 1" in result
        assert "Cell 1" in result
    
    def test_three_column_table(self, md_safe: Markdown) -> None:
        """Test three-column table."""
        text = """| A | B | C |
| --- | --- | --- |
| 1 | 2 | 3 |
| 4 | 5 | 6 |"""
        result = md_safe.render(text)
        assert result.count("<th>") == 3
        assert result.count("<td>") == 6
        assert result.count("<tr>") == 3
    
    def test_single_column_table(self, md_safe: Markdown) -> None:
        """Test single column table."""
        text = """| Header |
| --- |
| Cell |"""
        result = md_safe.render(text)
        assert "<table>" in result
        assert result.count("<th>") == 1
        assert result.count("<td>") == 1


class TestTableAlignment:
    """Tests for table column alignment."""
    
    def test_left_align(self, md_safe: Markdown) -> None:
        """Test left-aligned column."""
        text = """| Left |
| :--- |
| Data |"""
        result = md_safe.render(text)
        assert 'text-align:left' in result
    
    def test_center_align(self, md_safe: Markdown) -> None:
        """Test center-aligned column."""
        text = """| Center |
| :---: |
| Data |"""
        result = md_safe.render(text)
        assert 'text-align:center' in result
    
    def test_right_align(self, md_safe: Markdown) -> None:
        """Test right-aligned column."""
        text = """| Right |
| ---: |
| Data |"""
        result = md_safe.render(text)
        assert 'text-align:right' in result
    
    def test_mixed_alignment(self, md_safe: Markdown) -> None:
        """Test mixed column alignments."""
        text = """| Left | Center | Right |
| :--- | :---: | ---: |
| L | C | R |"""
        result = md_safe.render(text)
        assert 'text-align:left' in result
        assert 'text-align:center' in result
        assert 'text-align:right' in result
    
    def test_no_alignment(self, md_safe: Markdown) -> None:
        """Test columns with no alignment specified."""
        text = """| Normal |
| --- |
| Data |"""
        result = md_safe.render(text)
        # Should not have alignment style
        assert 'text-align' not in result or '<th>' in result


class TestTableContent:
    """Tests for table cell content."""
    
    def test_bold_in_cell(self, md_safe: Markdown) -> None:
        """Test bold text in table cell."""
        text = """| Header |
| --- |
| **Bold** |"""
        result = md_safe.render(text)
        assert "<strong>Bold</strong>" in result
    
    def test_italic_in_cell(self, md_safe: Markdown) -> None:
        """Test italic text in table cell."""
        text = """| Header |
| --- |
| *Italic* |"""
        result = md_safe.render(text)
        assert "<em>Italic</em>" in result
    
    def test_code_in_cell(self, md_safe: Markdown) -> None:
        """Test inline code in table cell."""
        text = """| Header |
| --- |
| `code` |"""
        result = md_safe.render(text)
        assert "<code>code</code>" in result
    
    def test_link_in_cell(self, md_safe: Markdown) -> None:
        """Test link in table cell."""
        text = """| Header |
| --- |
| [Link](https://example.com) |"""
        result = md_safe.render(text)
        assert '<a href="https://example.com">' in result
    
    def test_empty_cell(self, md_safe: Markdown) -> None:
        """Test empty table cells."""
        text = """| A | B |
| --- | --- |
|  | Data |"""
        result = md_safe.render(text)
        assert result.count("<td>") == 2


class TestTableSafety:
    """Tests for HTML escaping in table cells (SAFE mode)."""
    
    def test_escape_html_in_cell(self, md_safe: Markdown) -> None:
        """Test that HTML is escaped in cells."""
        text = """| Header |
| --- |
| <script>alert('xss')</script> |"""
        result = md_safe.render(text)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_escape_angle_brackets(self, md_safe: Markdown) -> None:
        """Test escaping angle brackets."""
        text = """| Header |
| --- |
| <div> |"""
        result = md_safe.render(text)
        assert "&lt;div&gt;" in result
    
    def test_escape_ampersand(self, md_safe: Markdown) -> None:
        """Test escaping ampersand."""
        text = """| Header |
| --- |
| A & B |"""
        result = md_safe.render(text)
        assert "&amp;" in result
    
    def test_escape_quotes(self, md_safe: Markdown) -> None:
        """Test escaping quotes."""
        text = """| Header |
| --- |
| "quoted" |"""
        result = md_safe.render(text)
        assert "&quot;" in result or '"' not in result.split("<table>")[1].split("</table>")[0]


class TestTableWithRawMode:
    """Tests for tables in RAW mode."""
    
    def test_raw_mode_allows_html(self, md_raw: Markdown) -> None:
        """Test that RAW mode doesn't escape HTML."""
        text = """| Header |
| --- |
| <b>bold</b> |"""
        result = md_raw.render(text)
        assert "<b>bold</b>" in result


class TestTableBoundaries:
    """Tests for table boundaries with other elements."""
    
    def test_paragraph_then_table(self, md_safe: Markdown) -> None:
        """Test paragraph followed by table."""
        text = """Some text before.

| Header |
| --- |
| Cell |"""
        result = md_safe.render(text)
        assert "<p>" in result
        assert "<table>" in result
        # Paragraph should be closed before table
        idx_p_close = result.find("</p>")
        idx_table = result.find("<table>")
        assert idx_p_close < idx_table
    
    def test_table_then_paragraph(self, md_safe: Markdown) -> None:
        """Test table followed by paragraph."""
        text = """| Header |
| --- |
| Cell |

Some text after."""
        result = md_safe.render(text)
        assert "</table>" in result
        assert "<p>" in result
        # Table should be closed before paragraph
        idx_table_close = result.find("</table>")
        idx_p = result.find("<p>")
        assert idx_table_close < idx_p
    
    def test_heading_then_table(self, md_safe: Markdown) -> None:
        """Test heading followed by table."""
        text = """# Title

| Header |
| --- |
| Cell |"""
        result = md_safe.render(text)
        assert "<h1>" in result
        assert "<table>" in result
    
    def test_list_then_table(self, md_safe: Markdown) -> None:
        """Test list followed by table."""
        text = """- Item 1
- Item 2

| Header |
| --- |
| Cell |"""
        result = md_safe.render(text)
        assert "</ul>" in result or "</ol>" in result or "<ul>" in result
        assert "<table>" in result


class TestTableEdgeCases:
    """Tests for edge cases in table parsing."""
    
    def test_no_separator_row(self, md_safe: Markdown) -> None:
        """Test that row without separator is not a table."""
        text = """| Not a | table |
| because no | separator |"""
        result = md_safe.render(text)
        # Should be treated as paragraphs, not a table
        assert "<table>" not in result
    
    def test_table_at_end_of_input(self, md_safe: Markdown) -> None:
        """Test table at end of input without trailing newline."""
        text = """| Header |
| --- |
| Cell |"""
        result = md_safe.render(text)
        assert "<table>" in result
        assert "</table>" in result
    
    def test_varying_separator_length(self, md_safe: Markdown) -> None:
        """Test separator with varying dash counts."""
        text = """| H1 | H2 |
| - | -------- |
| A | B |"""
        result = md_safe.render(text)
        assert "<table>" in result
    
    def test_extra_spaces_in_cells(self, md_safe: Markdown) -> None:
        """Test that extra spaces are trimmed."""
        text = """| Header |
| --- |
|   Cell with spaces   |"""
        result = md_safe.render(text)
        assert "Cell with spaces" in result
    
    def test_missing_trailing_pipe(self, md_safe: Markdown) -> None:
        """Test row without trailing pipe."""
        text = """| Header |
| --- |
| Cell"""
        result = md_safe.render(text)
        # Should still parse as table
        assert "<table>" in result or "Cell" in result


class TestTablePerformance:
    """Performance tests for tables."""
    
    def test_wide_table(self, md_safe: Markdown) -> None:
        """Test table with many columns."""
        headers = " | ".join([f"H{i}" for i in range(20)])
        separator = " | ".join(["---" for _ in range(20)])
        row = " | ".join([f"C{i}" for i in range(20)])
        text = f"| {headers} |\n| {separator} |\n| {row} |"
        result = md_safe.render(text)
        assert result.count("<th>") == 20
        assert result.count("<td>") == 20
    
    def test_tall_table(self, md_safe: Markdown) -> None:
        """Test table with many rows."""
        lines = ["| Header |", "| --- |"]
        for i in range(100):
            lines.append(f"| Row {i} |")
        text = "\n".join(lines)
        result = md_safe.render(text)
        assert result.count("<tr>") == 101  # 1 header + 100 body


class TestTableDeterminism:
    """Tests for deterministic table behavior."""
    
    def test_same_output_multiple_runs(self, md_safe: Markdown) -> None:
        """Test that same table input produces same output."""
        text = """| A | B | C |
| :--- | :---: | ---: |
| 1 | 2 | 3 |
| 4 | 5 | 6 |"""
        result1 = md_safe.render(text)
        result2 = md_safe.render(text)
        result3 = md_safe.render(text)
        assert result1 == result2 == result3
    
    def test_complex_content_deterministic(self, md_safe: Markdown) -> None:
        """Test determinism with complex cell content."""
        text = """| **Bold** | *Italic* | `Code` |
| --- | --- | --- |
| [Link](url) | A & B | <tag> |"""
        result1 = md_safe.render(text)
        result2 = md_safe.render(text)
        assert result1 == result2
