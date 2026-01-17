"""
Tests for emphasis spacing fix.
Covers: *, **, ***, _, __, ___ with spaces inside.
"""

import pytest


class TestEmphasisSpacingFix:
    """Test emphasis spacing normalization."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            # Double asterisk (bold)
            ("** bold **", "**bold**"),
            ("** bold text **", "**bold text**"),
            ("**text **", "**text**"),
            ("** text**", "**text**"),
            # Triple asterisk (bold+italic)
            ("*** bold italic ***", "***bold italic***"),
            # Double underscore (bold)
            ("__ bold __", "__bold__"),
            ("__ bold text __", "__bold text__"),
            ("__text __", "__text__"),
            ("__ text__", "__text__"),
            # Triple underscore (bold+italic)
            ("___ bold italic ___", "___bold italic___"),
            # Mixed markers
            ("** bold ** and __ also __", "**bold** and __also__"),
        ],
    )
    def test_emphasis_with_spaces_fixed(
        self, emphasis_only_normalizer, input_str, expected
    ):
        """Test that emphasis with spaces is correctly fixed."""
        assert emphasis_only_normalizer.normalize(input_str) == expected

    @pytest.mark.parametrize(
        "input_str",
        [
            # Single * and _ with spaces on both sides - treated as operator (safeguard)
            "* italic *",
            "_ italic _",
            # Already correct emphasis
            "**bold**",
            "__bold__",
            "*italic*",
            "_italic_",
            "***bold italic***",
            "___bold italic___",
        ],
    )
    def test_safeguard_and_correct_emphasis_unchanged(
        self, emphasis_only_normalizer, input_str
    ):
        """Test that safeguard cases and already correct emphasis are not modified."""
        assert emphasis_only_normalizer.normalize(input_str) == input_str


class TestEmphasisSideEffects:
    """Test that emphasis fix does NOT affect unrelated content."""

    @pytest.mark.parametrize(
        "input_str,description",
        [
            # URLs with underscores
            ("https://example.com/path_with_underscore", "URL"),
            ("Visit https://api.example.com/get_user_info for info", "URL in text"),
            # Variable names (snake_case)
            ("The `my_variable_name` is important", "Variable in backticks"),
            ("Use `get_user_data()` function", "Function name"),
            # File names
            ("Edit the `config_file_name.py` file", "File name"),
            ("See `my_script__v2.py` for details", "Double underscore in filename"),
            # Math-like subscripts
            ("The variable a_1 and b_2 are defined", "Math subscripts"),
            # Single underscores not matching emphasis pattern
            ("word_with_underscore", "Underscore in word"),
            ("a_b_c_d", "Multiple underscores"),
            # Horizontal rules
            ("---", "HR with dashes"),
            ("***", "HR with asterisks"),
            ("___", "HR with underscores"),
            # List items
            ("- item_one\n- item_two", "List items"),
        ],
    )
    def test_no_side_effects(self, emphasis_only_normalizer, input_str, description):
        """Test that various content types are NOT modified by emphasis fix."""
        assert (
            emphasis_only_normalizer.normalize(input_str) == input_str
        ), f"Failed for: {description}"

    def test_list_marker_not_merged_with_emphasis(self, emphasis_only_normalizer):
        """Test that list markers (*) are not merged with emphasis (**).

        Regression test for: "*   **Yes**" should NOT become "***Yes**"
        """
        input_str = """1.  **Start**: The user opens the login page.
    *   **Yes**: Login successful.
    *   **No**: Show error message."""
        result = emphasis_only_normalizer.normalize(input_str)
        assert (
            "*   **Yes**" in result
        ), "List marker was incorrectly merged with emphasis"
        assert (
            "*   **No**" in result
        ), "List marker was incorrectly merged with emphasis"
        assert "***Yes**" not in result, "BUG: List marker merged with emphasis"
        assert "***No**" not in result, "BUG: List marker merged with emphasis"

    def test_list_marker_with_plain_text_then_emphasis(self, emphasis_only_normalizer):
        """Test that list items with plain text before emphasis are preserved.

        Regression test for: "*   U16 forward **Kuang**" should NOT become "*U16 forward **Kuang**"
        """
        input_str = "*   U16 China forward **Kuang Zhaolei**"
        result = emphasis_only_normalizer.normalize(input_str)
        assert "*   U16" in result, "List marker spaces were incorrectly stripped"
        assert (
            "*U16" not in result or "*   U16" in result
        ), "BUG: List marker spaces stripped"


class TestEmphasisInCodeBlocks:
    """Test that emphasis inside code blocks is NOT modified."""

    def test_emphasis_in_code_block_unchanged(self, emphasis_only_normalizer):
        """Code blocks should be completely skipped."""
        input_str = "```python\nmy_var = get_data__from_api()\n```"
        assert emphasis_only_normalizer.normalize(input_str) == input_str

    def test_mixed_emphasis_and_code(self, emphasis_only_normalizer):
        """Text outside code blocks should be fixed, inside should not."""
        input_str = "** bold ** text\n```python\n** not bold **\n```"
        expected = "**bold** text\n```python\n** not bold **\n```"
        assert emphasis_only_normalizer.normalize(input_str) == expected
