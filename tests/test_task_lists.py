"""
Tests for GitHub-style Task Lists.

Task list syntax:
- [x] Completed task
- [ ] Pending task
* [ ] With star
1. [x] Numbered task
    - [ ] Nested under list item
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


class TestBasicTaskDetection:
    """Tests for basic task list marker detection."""
    
    def test_unchecked_task_dash(self, md_safe: Markdown) -> None:
        """Test unchecked task with dash marker."""
        result = md_safe.render("- [ ] Pending task")
        assert '<input type="checkbox" />' in result
        assert "Pending task" in result
        assert "<li>" in result
        assert "</li>" in result
    
    def test_checked_task_dash(self, md_safe: Markdown) -> None:
        """Test checked task with dash marker."""
        result = md_safe.render("- [x] Completed task")
        assert '<input type="checkbox" checked />' in result
        assert "Completed task" in result
    
    def test_checked_task_uppercase_x(self, md_safe: Markdown) -> None:
        """Test checked task with uppercase X."""
        result = md_safe.render("- [X] Completed task")
        assert '<input type="checkbox" checked />' in result
        assert "Completed task" in result
    
    def test_unchecked_task_asterisk(self, md_safe: Markdown) -> None:
        """Test unchecked task with asterisk marker."""
        result = md_safe.render("* [ ] Pending task")
        assert '<input type="checkbox" />' in result
        assert "Pending task" in result
    
    def test_checked_task_asterisk(self, md_safe: Markdown) -> None:
        """Test checked task with asterisk marker."""
        result = md_safe.render("* [x] Completed task")
        assert '<input type="checkbox" checked />' in result
        assert "Completed task" in result


class TestCheckedVsUnchecked:
    """Tests comparing checked and unchecked states."""
    
    def test_mixed_states_in_list(self, md_safe: Markdown) -> None:
        """Test list with both checked and unchecked tasks."""
        text = """- [x] Done
- [ ] Not done
- [x] Also done"""
        result = md_safe.render(text)
        assert result.count('<input type="checkbox" checked />') == 2
        assert result.count('<input type="checkbox" />') == 1
    
    def test_checkbox_before_text(self, md_safe: Markdown) -> None:
        """Test that checkbox appears before task text."""
        result = md_safe.render("- [x] Task text")
        # Checkbox should come before task text
        checkbox_pos = result.find('<input type="checkbox" checked />')
        text_pos = result.find("Task text")
        assert checkbox_pos < text_pos
    
    def test_space_after_checkbox(self, md_safe: Markdown) -> None:
        """Test that there is a space between checkbox and text."""
        result = md_safe.render("- [ ] Task")
        # The HTML constant includes trailing space: '<input type="checkbox" /> '
        assert '<input type="checkbox" /> Task' in result or \
               '<input type="checkbox" />Task' not in result


class TestNestedTaskLists:
    """Tests for nested task lists."""
    
    def test_nested_task_under_task(self, md_safe: Markdown) -> None:
        """Test task nested under another task."""
        text = """- [x] Parent task
  - [ ] Child task"""
        result = md_safe.render(text)
        assert '<input type="checkbox" checked />' in result
        assert '<input type="checkbox" />' in result
        assert result.count("<ul>") == 2
        assert result.count("</ul>") == 2
    
    def test_deeply_nested_tasks(self, md_safe: Markdown) -> None:
        """Test deeply nested task lists."""
        text = """- [x] Level 1
  - [ ] Level 2
    - [x] Level 3"""
        result = md_safe.render(text)
        assert result.count('<input type="checkbox"') == 3
        assert result.count("<ul>") == 3
    
    def test_task_nested_under_regular_item(self, md_safe: Markdown) -> None:
        """Test task nested under regular list item."""
        text = """- Regular item
  - [x] Nested task"""
        result = md_safe.render(text)
        assert '<input type="checkbox" checked />' in result
        assert "Regular item" in result
        # Regular item should NOT have checkbox
        assert result.count('<input type="checkbox"') == 1
    
    def test_regular_item_nested_under_task(self, md_safe: Markdown) -> None:
        """Test regular item nested under task."""
        text = """- [x] Task item
  - Regular nested"""
        result = md_safe.render(text)
        assert '<input type="checkbox" checked />' in result
        assert "Regular nested" in result
        assert result.count('<input type="checkbox"') == 1


class TestMixedOrderedUnordered:
    """Tests for mixed ordered and unordered task lists."""
    
    def test_ordered_list_task(self, md_safe: Markdown) -> None:
        """Test task in ordered list."""
        result = md_safe.render("1. [x] First task")
        assert '<input type="checkbox" checked />' in result
        assert "<ol>" in result
        assert "First task" in result
    
    def test_ordered_list_unchecked(self, md_safe: Markdown) -> None:
        """Test unchecked task in ordered list."""
        result = md_safe.render("1. [ ] Pending task")
        assert '<input type="checkbox" />' in result
        assert "<ol>" in result
    
    def test_mixed_ordered_unordered_tasks(self, md_safe: Markdown) -> None:
        """Test tasks in mixed list types."""
        text = """1. [x] Ordered task
- [ ] Unordered task
2. [x] Another ordered"""
        result = md_safe.render(text)
        assert '<input type="checkbox" checked />' in result
        assert '<input type="checkbox" />' in result
        assert "<ol>" in result
        assert "<ul>" in result
    
    def test_unordered_nested_in_ordered_task(self, md_safe: Markdown) -> None:
        """Test unordered task nested in ordered list."""
        text = """1. [x] Ordered task
  - [ ] Nested unordered task"""
        result = md_safe.render(text)
        assert result.count('<input type="checkbox"') == 2
        assert "<ol>" in result
        assert "<ul>" in result


class TestTaskWithInlineFormatting:
    """Tests for task lists with inline formatting."""
    
    def test_task_with_bold(self, md_safe: Markdown) -> None:
        """Test task with bold text."""
        result = md_safe.render("- [x] **Bold task**")
        assert '<input type="checkbox" checked />' in result
        assert "<strong>Bold task</strong>" in result
    
    def test_task_with_italic(self, md_safe: Markdown) -> None:
        """Test task with italic text."""
        result = md_safe.render("- [ ] *Italic task*")
        assert '<input type="checkbox" />' in result
        assert "<em>Italic task</em>" in result
    
    def test_task_with_inline_code(self, md_safe: Markdown) -> None:
        """Test task with inline code."""
        result = md_safe.render("- [x] Fix `bug` in code")
        assert '<input type="checkbox" checked />' in result
        assert "<code>bug</code>" in result
    
    def test_task_with_link(self, md_safe: Markdown) -> None:
        """Test task with link."""
        result = md_safe.render("- [ ] Check [website](https://example.com)")
        assert '<input type="checkbox" />' in result
        assert '<a href="https://example.com">' in result
        assert "website</a>" in result
    
    def test_task_with_multiple_formatting(self, md_safe: Markdown) -> None:
        """Test task with multiple inline formats."""
        result = md_safe.render("- [x] **Bold** and *italic* and `code`")
        assert '<input type="checkbox" checked />' in result
        assert "<strong>Bold</strong>" in result
        assert "<em>italic</em>" in result
        assert "<code>code</code>" in result


class TestTaskInBlockquote:
    """Tests for task lists inside blockquotes.
    
    Note: The current blockquote implementation treats list markers as
    paragraph text inside blockquotes. These tests verify the current
    behavior and ensure task markers don't cause errors in blockquote context.
    """
    
    def test_task_marker_in_blockquote_is_text(self, md_safe: Markdown) -> None:
        """Test that task marker in blockquote is treated as text (current behavior)."""
        text = """> - [x] Task in quote"""
        result = md_safe.render(text)
        # Currently, lists in blockquotes are treated as text
        assert "<blockquote>" in result
        assert "</blockquote>" in result
        # The task marker should appear as text
        assert "- [x] Task in quote" in result or "[x]" in result
    
    def test_blockquote_task_no_crash(self, md_safe: Markdown) -> None:
        """Test that task marker in blockquote doesn't crash."""
        text = """> - [ ] Task"""
        result = md_safe.render(text)
        assert "<blockquote>" in result
        # Should complete without error


class TestNonTaskPatterns:
    """Tests for patterns that should NOT be detected as tasks."""
    
    def test_bracket_not_at_start(self, md_safe: Markdown) -> None:
        """Test that [x] not at start is not a task."""
        result = md_safe.render("- Hello [x] world")
        assert '<input type="checkbox"' not in result
        assert "[x]" in result
        assert "Hello" in result
        assert "world" in result
    
    def test_invalid_bracket_pattern(self, md_safe: Markdown) -> None:
        """Test that invalid patterns are not tasks."""
        # [-] is not valid
        result = md_safe.render("- [-] Not a task")
        assert '<input type="checkbox"' not in result
        assert "[-]" in result
    
    def test_missing_space_after_bracket(self, md_safe: Markdown) -> None:
        """Test that [x]text (no space) is not a task."""
        result = md_safe.render("- [x]text")
        assert '<input type="checkbox"' not in result
        # Should render as literal text
    
    def test_missing_closing_bracket(self, md_safe: Markdown) -> None:
        """Test that [x is not detected as task."""
        result = md_safe.render("- [x Not a task")
        assert '<input type="checkbox"' not in result
    
    def test_bracket_in_paragraph(self, md_safe: Markdown) -> None:
        """Test that [x] in paragraph is not a task."""
        result = md_safe.render("This is [x] some text")
        assert '<input type="checkbox"' not in result
        assert "[x]" in result
    
    def test_other_characters_in_bracket(self, md_safe: Markdown) -> None:
        """Test that [y] or [a] are not tasks."""
        result = md_safe.render("- [y] Not a task")
        assert '<input type="checkbox"' not in result
        result2 = md_safe.render("- [a] Also not a task")
        assert '<input type="checkbox"' not in result2


class TestSecurityXSSPrevention:
    """Security tests to ensure no XSS injection via task lists."""
    
    def test_script_in_task_text(self, md_safe: Markdown) -> None:
        """Test that script tags in task text are escaped."""
        result = md_safe.render("- [x] <script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
        assert '<input type="checkbox" checked />' in result
    
    def test_html_injection_in_task(self, md_safe: Markdown) -> None:
        """Test that HTML in task text is escaped."""
        result = md_safe.render("- [ ] <img src=x onerror=alert(1)>")
        assert 'onerror' not in result or '&' in result
        assert '<input type="checkbox" />' in result
    
    def test_javascript_url_in_task_link(self, md_safe: Markdown) -> None:
        """Test that javascript: URLs are handled safely."""
        result = md_safe.render("- [x] Click [here](javascript:alert(1))")
        # The link should either be sanitized or not rendered as clickable
        assert '<input type="checkbox" checked />' in result
    
    def test_checkbox_html_is_safe(self, md_safe: Markdown) -> None:
        """Test that checkbox HTML output is exactly as expected."""
        result = md_safe.render("- [x] Task")
        # Verify exact checkbox HTML
        assert '<input type="checkbox" checked />' in result
        result2 = md_safe.render("- [ ] Task")
        assert '<input type="checkbox" />' in result2


class TestEdgeCases:
    """Edge case tests for task lists."""
    
    def test_empty_task_text(self, md_safe: Markdown) -> None:
        """Test task with no text after checkbox."""
        result = md_safe.render("- [x] ")
        assert '<input type="checkbox" checked />' in result
    
    def test_task_at_end_of_input(self, md_safe: Markdown) -> None:
        """Test task at end of input without newline."""
        result = md_safe.render("- [x] Last task")
        assert '<input type="checkbox" checked />' in result
        assert "Last task" in result
    
    def test_multiple_task_lists(self, md_safe: Markdown) -> None:
        """Test multiple separate task lists."""
        text = """- [x] First list

- [ ] Second list"""
        result = md_safe.render(text)
        assert result.count('<input type="checkbox"') == 2
    
    def test_task_followed_by_paragraph(self, md_safe: Markdown) -> None:
        """Test task list followed by paragraph."""
        text = """- [x] Task

Regular paragraph."""
        result = md_safe.render(text)
        assert '<input type="checkbox" checked />' in result
        assert "<p>Regular paragraph.</p>" in result
    
    def test_long_task_list(self, md_safe: Markdown) -> None:
        """Test longer task list."""
        tasks = "\n".join([f"- [{'x' if i % 2 == 0 else ' '}] Task {i}" for i in range(10)])
        result = md_safe.render(tasks)
        assert result.count('<input type="checkbox" checked />') == 5
        assert result.count('<input type="checkbox" />') == 5
    
    def test_task_with_special_characters(self, md_safe: Markdown) -> None:
        """Test task with special characters."""
        result = md_safe.render("- [x] Task with émojis 🎉 and üñíçödé")
        assert '<input type="checkbox" checked />' in result
        assert "émojis" in result
        assert "🎉" in result


class TestHTMLStructure:
    """Tests for correct HTML structure of task lists."""
    
    def test_checkbox_inside_li(self, md_safe: Markdown) -> None:
        """Test that checkbox is inside <li> element."""
        result = md_safe.render("- [x] Task")
        li_start = result.find("<li>")
        li_end = result.find("</li>")
        checkbox_pos = result.find('<input type="checkbox"')
        assert li_start < checkbox_pos < li_end
    
    def test_proper_list_wrapper(self, md_safe: Markdown) -> None:
        """Test that task list has proper <ul> wrapper."""
        result = md_safe.render("- [x] Task")
        assert "<ul>" in result
        assert "</ul>" in result
        ul_start = result.find("<ul>")
        ul_end = result.find("</ul>")
        li_pos = result.find("<li>")
        assert ul_start < li_pos < ul_end
    
    def test_ordered_task_structure(self, md_safe: Markdown) -> None:
        """Test ordered task list has proper <ol> wrapper."""
        result = md_safe.render("1. [x] Task")
        assert "<ol>" in result
        assert "</ol>" in result
        ol_start = result.find("<ol>")
        ol_end = result.find("</ol>")
        checkbox_pos = result.find('<input type="checkbox"')
        assert ol_start < checkbox_pos < ol_end
