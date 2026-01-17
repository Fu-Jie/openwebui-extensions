"""
Tests for heading fix.
Covers: Missing space after # in headings.
"""

import pytest


class TestHeadingFix:
    """Test heading space normalization."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("#Heading", "# Heading"),
            ("##Heading", "## Heading"),
            ("###Heading", "### Heading"),
            ("#中文标题", "# 中文标题"),
            ("#123", "# 123"),  # Numbers after # also get space
        ],
    )
    def test_missing_space_added(self, normalizer, input_str, expected):
        """Headings missing space after # should be fixed."""
        assert normalizer.normalize(input_str) == expected

    @pytest.mark.parametrize(
        "input_str",
        [
            "# Heading",
            "## Already Correct",
            "###",  # Just hashes
        ],
    )
    def test_correct_headings_unchanged(self, normalizer, input_str):
        """Already correct headings should not be modified."""
        assert normalizer.normalize(input_str) == input_str


class TestTableFix:
    """Test table pipe normalization."""

    def test_missing_closing_pipe_added(self, normalizer):
        """Tables missing closing | should have it added."""
        input_str = "| col1 | col2"
        result = normalizer.normalize(input_str)
        assert result.endswith("|") or "col2 |" in result

    def test_already_closed_table_unchanged(self, normalizer):
        """Tables with closing | should not be modified."""
        input_str = "| col1 | col2 |"
        assert normalizer.normalize(input_str) == input_str
