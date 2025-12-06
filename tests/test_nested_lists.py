"""
Tests for nested list elements (unordered, ordered, and mixed).
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestSimpleNestedLists:
    """Tests for simple nested unordered lists."""
    
    def test_single_level_dash(self, md_safe: Markdown) -> None:
        """Test single level list with dash."""
        result = md_safe.render("- Item 1\n- Item 2\n- Item 3")
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 3
        assert result.count("</li>") == 3
    
    def test_single_level_asterisk(self, md_safe: Markdown) -> None:
        """Test single level list with asterisk."""
        result = md_safe.render("* Item 1\n* Item 2\n* Item 3")
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 3
    
    def test_two_level_nesting(self, md_safe: Markdown) -> None:
        """Test two level nested list."""
        text = """- Item 1
  - Nested 1
  - Nested 2
- Item 2"""
        result = md_safe.render(text)
        assert result.count("<ul>") == 2
        assert result.count("</ul>") == 2
        assert result.count("<li>") == 4
        assert "Item 1" in result
        assert "Nested 1" in result
    
    def test_three_level_nesting(self, md_safe: Markdown) -> None:
        """Test three level nested list."""
        text = """- Level 1
  - Level 2
    - Level 3
    - Level 3b
  - Level 2b
- Level 1b"""
        result = md_safe.render(text)
        assert result.count("<ul>") == 3
        assert result.count("</ul>") == 3
        assert result.count("<li>") == 6
    
    def test_dedent_properly(self, md_safe: Markdown) -> None:
        """Test that dedentation closes lists properly."""
        text = """- Item 1
  - Nested
- Item 2"""
        result = md_safe.render(text)
        # Should have proper nesting structure
        assert "<ul>" in result
        assert "</ul>" in result
        # Check that nested list is closed before Item 2
        idx_nested_close = result.find("</ul>")
        idx_item2 = result.find("Item 2")
        assert idx_nested_close < idx_item2


class TestOrderedLists:
    """Tests for ordered (numbered) lists."""
    
    def test_simple_ordered_list(self, md_safe: Markdown) -> None:
        """Test simple ordered list."""
        result = md_safe.render("1. First\n2. Second\n3. Third")
        assert "<ol>" in result
        assert "</ol>" in result
        assert result.count("<li>") == 3
        assert "First" in result
        assert "Second" in result
    
    def test_nested_ordered_list(self, md_safe: Markdown) -> None:
        """Test nested ordered list."""
        text = """1. Item 1
  1. Nested 1
  2. Nested 2
2. Item 2"""
        result = md_safe.render(text)
        assert result.count("<ol>") == 2
        assert result.count("</ol>") == 2
    
    def test_ordered_starting_not_at_one(self, md_safe: Markdown) -> None:
        """Test ordered list starting at different number."""
        result = md_safe.render("5. Fifth\n6. Sixth")
        assert "<ol>" in result
        assert result.count("<li>") == 2


class TestMixedLists:
    """Tests for mixed ordered and unordered lists."""
    
    def test_unordered_then_ordered(self, md_safe: Markdown) -> None:
        """Test unordered list followed by ordered list."""
        text = """- Unordered 1
- Unordered 2

1. Ordered 1
2. Ordered 2"""
        result = md_safe.render(text)
        assert "<ul>" in result
        assert "<ol>" in result
    
    def test_nested_mixed(self, md_safe: Markdown) -> None:
        """Test nested mixed list types."""
        text = """- Unordered
  1. Nested ordered
  2. Nested ordered 2
- Unordered 2"""
        result = md_safe.render(text)
        assert "<ul>" in result
        assert "<ol>" in result


class TestListsWithContent:
    """Tests for lists with various content."""
    
    def test_list_with_bold(self, md_safe: Markdown) -> None:
        """Test list items with bold text."""
        result = md_safe.render("- **Bold item**\n- Normal item")
        assert "<strong>Bold item</strong>" in result
        assert "<li>" in result
    
    def test_list_with_italic(self, md_safe: Markdown) -> None:
        """Test list items with italic text."""
        result = md_safe.render("- *Italic item*\n- Normal item")
        assert "<em>Italic item</em>" in result
    
    def test_list_with_code(self, md_safe: Markdown) -> None:
        """Test list items with inline code."""
        result = md_safe.render("- Item with `code`\n- Normal item")
        assert "<code>code</code>" in result
    
    def test_list_with_link(self, md_safe: Markdown) -> None:
        """Test list items with links."""
        result = md_safe.render("- [Link text](https://example.com)\n- Normal item")
        assert '<a href="https://example.com">' in result
        assert "Link text" in result


class TestListBoundaries:
    """Tests for list boundaries with other elements."""
    
    def test_list_then_paragraph(self, md_safe: Markdown) -> None:
        """Test list followed by paragraph."""
        text = """- Item 1
- Item 2

This is a paragraph."""
        result = md_safe.render(text)
        assert "<ul>" in result
        assert "</ul>" in result
        assert "<p>" in result
        # Ensure list is closed before paragraph
        idx_ul_close = result.find("</ul>")
        idx_p = result.find("<p>")
        assert idx_ul_close < idx_p
    
    def test_paragraph_then_list(self, md_safe: Markdown) -> None:
        """Test paragraph followed by list."""
        text = """This is a paragraph.

- Item 1
- Item 2"""
        result = md_safe.render(text)
        assert "<p>" in result
        assert "</p>" in result
        assert "<ul>" in result
    
    def test_heading_then_list(self, md_safe: Markdown) -> None:
        """Test heading followed by list."""
        text = """# Heading

- Item 1
- Item 2"""
        result = md_safe.render(text)
        assert "<h1>" in result
        assert "<ul>" in result
    
    def test_list_then_heading(self, md_safe: Markdown) -> None:
        """Test list followed by heading."""
        text = """- Item 1
- Item 2

# Heading"""
        result = md_safe.render(text)
        assert "</ul>" in result
        assert "<h1>" in result
    
    def test_list_then_code_block(self, md_safe: Markdown) -> None:
        """Test list followed by code block."""
        text = """- Item 1
- Item 2

```
code
```"""
        result = md_safe.render(text)
        assert "</ul>" in result
        assert "<pre>" in result


class TestEdgeCases:
    """Tests for edge cases in list parsing."""
    
    def test_dash_without_space(self, md_safe: Markdown) -> None:
        """Test that dash without space is not a list."""
        result = md_safe.render("-notalist")
        assert "<ul>" not in result
    
    def test_asterisk_without_space(self, md_safe: Markdown) -> None:
        """Test that asterisk without space is not a list."""
        result = md_safe.render("*notalist")
        # Should be italic start, not a list
        assert "<ul>" not in result
    
    def test_number_without_dot_space(self, md_safe: Markdown) -> None:
        """Test that number without dot-space is not a list."""
        result = md_safe.render("1notalist")
        assert "<ol>" not in result
    
    def test_empty_list_item(self, md_safe: Markdown) -> None:
        """Test list with empty item."""
        result = md_safe.render("- \n- Item 2")
        assert "<li>" in result
        assert result.count("<li>") == 2
    
    def test_list_at_end_of_input(self, md_safe: Markdown) -> None:
        """Test list at end of input without trailing newline."""
        result = md_safe.render("- Item 1\n- Item 2")
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 2


class TestPerformance:
    """Performance tests for nested lists."""
    
    def test_deeply_nested_list(self, md_safe: Markdown) -> None:
        """Test deeply nested list (10 levels)."""
        lines = []
        for i in range(10):
            indent = "  " * i
            lines.append(f"{indent}- Level {i}")
        text = "\n".join(lines)
        result = md_safe.render(text)
        assert result.count("<ul>") == 10
        assert result.count("</ul>") == 10
    
    def test_many_list_items(self, md_safe: Markdown) -> None:
        """Test list with many items."""
        items = [f"- Item {i}" for i in range(100)]
        text = "\n".join(items)
        result = md_safe.render(text)
        assert result.count("<li>") == 100
        assert result.count("</li>") == 100


class TestDeterminism:
    """Tests for deterministic behavior."""
    
    def test_same_output_multiple_runs(self, md_safe: Markdown) -> None:
        """Test that same input produces same output."""
        text = """- Item 1
  - Nested 1
    - Deep nested
  - Nested 2
- Item 2"""
        result1 = md_safe.render(text)
        result2 = md_safe.render(text)
        result3 = md_safe.render(text)
        assert result1 == result2 == result3
    
    def test_mixed_markers_deterministic(self, md_safe: Markdown) -> None:
        """Test that mixed markers produce deterministic output."""
        text = """- Dash item
* Asterisk item
- Another dash"""
        result1 = md_safe.render(text)
        result2 = md_safe.render(text)
        assert result1 == result2
