import unittest
import sys
import os

# Add the parent directory and plugin directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.abspath(
    os.path.join(current_dir, "..", "plugins", "filters", "markdown_normalizer")
)
sys.path.append(plugin_dir)

from markdown_normalizer import ContentNormalizer, NormalizerConfig


class TestEmphasisSpacingFix(unittest.TestCase):
    def setUp(self):
        # Explicitly enable the priority and emphasis spacing fix
        self.config = NormalizerConfig(enable_emphasis_spacing_fix=True)
        self.normalizer = ContentNormalizer(self.config)

    def test_user_reported_bug(self):
        """
        Test case from user reported issue:
        'When there are e.g. 2 bold parts on a line of text, it treats the part between them as an ill-formatted bold part and removes spaces'
        """
        input_text = "I **prefer** tea **to** coffee."
        # Before fix, it might become "I **prefer**tea**to** coffee."
        # Use a fresh normalizer to ensure state is clean
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result,
            "I **prefer** tea **to** coffee.",
            "Spaces between bold parts should be preserved.",
        )

    def test_triple_bold_parts(self):
        """Verify handling of more than 2 bold parts on a single line"""
        input_text = "The **quick** brown **fox** jumps **over** the dog."
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result, input_text, "Multiple bold parts on same line should not merge."
        )

    def test_legitimate_spacing_fix(self):
        """Verify it still fixes actual spacing issues"""
        test_cases = [
            ("** text **", "**text**"),
            ("**text **", "**text**"),
            ("** text**", "**text**"),
            ("__ bold __", "__bold__"),
            ("* italic *", "*italic*"),
            ("_ italic _", "_italic_"),
            ("*** bolditalic ***", "***bolditalic***"),
        ]
        for inp, expected in test_cases:
            with self.subTest(inp=inp):
                self.assertEqual(self.normalizer.normalize(inp), expected)

    def test_nested_emphasis(self):
        """Test recursive handling of nested emphasis (italic inside bold)"""
        # Note: ** _italic_ ** -> **_italic_**
        input_text = "** _italic _ **"
        expected = "**_italic_**"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

        # Complex nesting
        input_text_complex = "**bold and _ italic _ parts**"
        expected_complex = "**bold and _italic_ parts**"
        self.assertEqual(
            self.normalizer.normalize(input_text_complex), expected_complex
        )

    def test_math_operator_protection(self):
        """Verify that math operators are protected (e.g., ' 2 * 3 * 4 ')"""
        input_text = "Calculations: 2 * 3 * 4 = 24"
        # The spacing around * should be preserved because it's an operator
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result,
            input_text,
            "Math operators (single '*' with spaces) should not be treated as emphasis.",
        )

    def test_list_marker_protection(self):
        """Verify that list markers are not merged with bold contents"""
        # *   **bold**
        input_text = "*   **bold**"
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result,
            input_text,
            "List marker '*' should not be merged with subsequent bold marker.",
        )

    def test_mixed_single_and_double_emphasis(self):
        """Verify a mix of single and double emphasis on the same line"""
        input_text = "He is *very* **bold** today."
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result,
            input_text,
            "Mixed emphasis styles should not interfere with each other.",
        )

    def test_placeholder_protection(self):
        """Verify that placeholders (multiple underscores) are protected"""
        input_text = "Fill in the blank: ____ and ____."
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result, input_text, "Placeholders like '____' should not be modified."
        )

    def test_regression_cross_block_greedy(self):
        """Special check for the greedy regex scenario that caused the bug"""
        # User reported case
        input_text = "I **prefer** tea **to** coffee."
        result = self.normalizer.normalize(input_text)
        self.assertEqual(
            result, input_text, "User reported case should not have spaces removed."
        )

        # Another variant with different symbols
        input_text2 = "Using __bold__ and __more bold__ here."
        self.assertEqual(self.normalizer.normalize(input_text2), input_text2)


if __name__ == "__main__":
    unittest.main()
