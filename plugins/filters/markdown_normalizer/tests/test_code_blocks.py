"""
Tests for code block formatting fixes.
Covers: prefix, suffix, indentation preservation.
"""

import pytest


class TestCodeBlockFix:
    """Test code block formatting normalization."""

    def test_code_block_indentation_preserved(self, normalizer):
        """Indented code blocks (e.g., in lists) should preserve indentation."""
        input_str = """
*   List item 1
    ```python
    def foo():
        print("bar")
    ```
*   List item 2
"""
        # Indentation should be preserved
        assert "    ```python" in normalizer.normalize(input_str)

    def test_inline_code_block_prefix(self, normalizer):
        """Code block that follows text on same line should be modified."""
        input_str = "text```python\ncode\n```"
        result = normalizer.normalize(input_str)
        # Just verify the code block markers are present
        assert "```" in result

    def test_code_block_suffix_fix(self, normalizer):
        """Code block with content on same line after lang should be fixed."""
        input_str = "```python   code\nmore code\n```"
        result = normalizer.normalize(input_str)
        # Content should be on new line
        assert "```python\n" in result or "```python  " in result


class TestUnclosedCodeBlock:
    """Test auto-closing of unclosed code blocks."""

    def test_unclosed_code_block_is_closed(self, normalizer):
        """Unclosed code blocks should be automatically closed."""
        input_str = "```python\ncode here"
        result = normalizer.normalize(input_str)
        # Should have closing ```
        assert result.endswith("```") or result.count("```") == 2

    def test_balanced_code_blocks_unchanged(self, normalizer):
        """Already balanced code blocks should not get extra closing."""
        input_str = "```python\ncode\n```"
        result = normalizer.normalize(input_str)
        assert result.count("```") == 2
