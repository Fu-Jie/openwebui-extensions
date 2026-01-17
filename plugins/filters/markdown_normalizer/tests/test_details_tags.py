"""
Tests for details tag normalization.
Covers: </details> spacing, self-closing tags.
"""

import pytest


class TestDetailsTagFix:
    """Test details tag normalization."""

    def test_details_end_gets_newlines(self, normalizer):
        """</details> should be followed by double newline."""
        input_str = "</details>Content after"
        result = normalizer.normalize(input_str)
        assert "</details>\n\n" in result

    def test_self_closing_details_gets_newline(self, normalizer):
        """Self-closing <details .../> should get newline after."""
        input_str = "<details open />## Heading"
        result = normalizer.normalize(input_str)
        # Should have newline between tag and heading
        assert "/>\n" in result or "/> \n" in result

    def test_details_in_code_block_unchanged(self, normalizer):
        """Details tags inside code blocks should not be modified."""
        input_str = "```html\n<details>content</details>more\n```"
        result = normalizer.normalize(input_str)
        # Content inside code block should be unchanged
        assert "</details>more" in result


class TestThoughtTagFix:
    """Test thought tag normalization."""

    def test_think_tag_normalized(self, normalizer):
        """<think> should be normalized to <thought>."""
        input_str = "<think>content</think>"
        result = normalizer.normalize(input_str)
        assert "<thought>" in result
        assert "</thought>" in result

    def test_thinking_tag_normalized(self, normalizer):
        """<thinking> should be normalized to <thought>."""
        input_str = "<thinking>content</thinking>"
        result = normalizer.normalize(input_str)
        assert "<thought>" in result
        assert "</thought>" in result
