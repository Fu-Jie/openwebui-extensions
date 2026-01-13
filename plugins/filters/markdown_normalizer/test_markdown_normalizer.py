import unittest
import sys
import os

# Add the current directory to sys.path to import the module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from markdown_normalizer import ContentNormalizer, NormalizerConfig


class TestMarkdownNormalizer(unittest.TestCase):
    def setUp(self):
        self.config = NormalizerConfig(
            enable_escape_fix=True,
            enable_thought_tag_fix=True,
            enable_code_block_fix=True,
            enable_latex_fix=True,
            enable_list_fix=True,
            enable_unclosed_block_fix=True,
            enable_fullwidth_symbol_fix=True,
            enable_mermaid_fix=True,
            enable_xml_tag_cleanup=True,
        )
        self.normalizer = ContentNormalizer(self.config)

    def test_escape_fix(self):
        input_text = "Line 1\\nLine 2\\tTabbed"
        expected = "Line 1\nLine 2\tTabbed"
        self.assertEqual(self.normalizer.normalize(input_text), expected)


    def test_escape_fix_respects_code_blocks(self):
        """Test that escape fix can be limited to outside code blocks"""
        # Test case: JSON string with \n should be preserved inside code block
        input_text = 'Text with\nescape\n```json\n{"message": "Line 1\\nLine 2"}\n```\nMore text\nhere'
        
        # With enable_escape_fix_in_code_blocks=False (default, safe mode)
        config_safe = NormalizerConfig(
            enable_escape_fix=True,
            enable_escape_fix_in_code_blocks=False,
            enable_code_block_fix=False  # Disable to avoid interfering with test
        )
        normalizer_safe = ContentNormalizer(config_safe)
        result_safe = normalizer_safe.normalize(input_text)
        
        # Outside code blocks: escapes should be fixed
        # Inside code blocks: escapes should be preserved
        self.assertIn('Text with', result_safe)
        self.assertIn('escape', result_safe)
        self.assertIn('{"message": "Line 1\\nLine 2"}', result_safe)  # Preserved in code
        self.assertIn('More text', result_safe)
        
        # With enable_escape_fix_in_code_blocks=True (global mode)
        config_global = NormalizerConfig(
            enable_escape_fix=True,
            enable_escape_fix_in_code_blocks=True,
            enable_code_block_fix=False
        )
        normalizer_global = ContentNormalizer(config_global)
        result_global = normalizer_global.normalize(input_text)
        
        # All escapes should be fixed (original behavior)
        self.assertNotIn('\\n', result_global)  # All backslash-n converted
    
    def test_fullwidth_quotes_in_code(self):
        """Test that explicit full-width quotation marks are converted"""
        # Test with full-width quotation marks (U+FF02 and U+FF07)
        input_text = '```python\nprint(＂hello＂)\nprint(＇world＇)\n```'
        
        config = NormalizerConfig(
            enable_fullwidth_symbol_fix=True,
            enable_code_block_fix=False
        )
        normalizer = ContentNormalizer(config)
        result = normalizer.normalize(input_text)
        
        # Full-width quotes should be converted to half-width
        self.assertIn('print("hello")', result)
        self.assertIn("print('world')", result)
        self.assertNotIn('＂', result)
        self.assertNotIn('＇', result)

    def test_thought_tag_fix(self):
        # Case 1: Standard tag spacing
        input_text = "Thinking...</thought>Result"
        expected = "Thinking...</thought>\n\nResult"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

        # Case 2: Tag standardization (<think> -> <thought>)
        input_text_deepseek = "<think>Deep thinking...</think>Result"
        expected_deepseek = "<thought>Deep thinking...</thought>\n\nResult"
        self.assertEqual(
            self.normalizer.normalize(input_text_deepseek), expected_deepseek
        )

    def test_code_block_fix(self):
        # Case 1: Indentation
        self.assertEqual(self.normalizer._fix_code_blocks("   ```python"), "```python")

        # Case 2: Prefix (newline before block)
        self.assertEqual(
            self.normalizer._fix_code_blocks("Text```python"), "Text\n```python"
        )

        # Case 3: Suffix (newline after lang)
        self.assertEqual(
            self.normalizer._fix_code_blocks("```python print('hi')"),
            "```python\nprint('hi')",
        )

    def test_latex_fix(self):
        input_text = "Block: \\[ x^2 \\] Inline: \\( E=mc^2 \\)"
        expected = "Block: $$ x^2 $$ Inline: $ E=mc^2 $"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

    def test_list_fix(self):
        input_text = "Item 1. First\nItem 2. Second"  # This is fine
        input_text_bad = "Header1. Item 1"
        expected = "Header\n1. Item 1"
        self.assertEqual(self.normalizer.normalize(input_text_bad), expected)

    def test_unclosed_code_block_fix(self):
        input_text = "```python\nprint('hello')"
        expected = "```python\nprint('hello')\n```"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

    def test_fullwidth_symbol_fix(self):
        input_text = "Outside：Fullwidth ```python\nprint（'hello'）```"
        expected = "Outside：Fullwidth \n```python\nprint('hello')\n```"

        normalized = self.normalizer.normalize(input_text)
        self.assertIn("print('hello')", normalized)
        self.assertIn("Outside：Fullwidth", normalized)
        self.assertNotIn("（", normalized)
        self.assertNotIn("）", normalized)

    def test_mermaid_fix(self):
        # Test Mermaid syntax fix for unquoted labels
        # Note: Regex-based fix handles mixed brackets well (e.g. [] inside ())
        # but cannot perfectly handle same-type nesting (e.g. {} inside {}) without a parser.
        input_text = """
```mermaid
graph TD
    A[Label with (parens)] --> B(Label with [brackets])
    C{Label with [brackets]}
```
"""
        expected_snippet = """
```mermaid
graph TD
    A["Label with (parens)"] --> B("Label with [brackets]")
    C{"Label with [brackets]"}
```
"""
        normalized = self.normalizer.normalize(input_text)

        self.assertIn('A["Label with (parens)"]', normalized)
        self.assertIn('B("Label with [brackets]")', normalized)
        self.assertIn('C{"Label with [brackets]"}', normalized)

    def test_mermaid_shapes_regression(self):
        # Regression test for "reverse optimization" where ((...)) was broken into ("(...)")
        input_text = """
```mermaid
graph TD
    Start((开始)) --> Input[[输入]]
    Input --> Verify{验证}
    Verify --> End(((结束)))
```
"""
        expected_snippet = """
```mermaid
graph TD
    Start(("开始")) --> Input[["输入"]]
    Input --> Verify{"验证"}
    Verify --> End((("结束")))
```
"""
        normalized = self.normalizer.normalize(input_text)
        self.assertIn('Start(("开始"))', normalized)
        self.assertIn('Input[["输入"]]', normalized)
        self.assertIn('Verify{"验证"}', normalized)
        self.assertIn('End((("结束")))', normalized)

    def test_xml_cleanup(self):
        input_text = "Some text <antArtifact>hidden</antArtifact> visible"
        expected = "Some text hidden visible"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

    def test_heading_fix(self):
        input_text = "#Heading 1\n##Heading 2\n### Valid Heading"
        expected = "# Heading 1\n## Heading 2\n### Valid Heading"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

    def test_table_fix(self):
        input_text = "| Col 1 | Col 2\n| Val 1 | Val 2"
        expected = "| Col 1 | Col 2|\n| Val 1 | Val 2|"
        self.assertEqual(self.normalizer.normalize(input_text), expected)

    def test_mermaid_subgraph_autoclose(self):
        """Test auto-closing of Mermaid subgraphs"""
        # Case 1: Simple unclosed subgraph
        original = """
```mermaid
graph TD
    subgraph One
        A --> B
```
"""
        expected = """
```mermaid
graph TD
    subgraph One
        A --> B
    end
```
"""
        # Note: The normalizer might add quotes to A and B if they match the node pattern,
        # but here they are simple IDs. However, our regex is strict about shapes.
        # Simple IDs like A and B are NOT matched by our mermaid_node regex because it requires a shape delimiter.
        # So A and B remain A and B.

        normalized = self.normalizer.normalize(original)
        # We need to be careful about whitespace in comparison
        self.assertIn("end", normalized)
        self.assertEqual(normalized.strip(), expected.strip())

        # Case 2: Nested unclosed subgraphs
        original_nested = """
```mermaid
graph TD
    subgraph Outer
        subgraph Inner
            C --> D
```
"""
        normalized_nested = self.normalizer.normalize(original_nested)
        self.assertEqual(normalized_nested.count("end"), 2)

    def test_mermaid_edge_labels(self):
        """Test that Mermaid edge labels are NOT modified by the node fix"""
        # This is a regression test for the issue where edge labels with parentheses
        # were being incorrectly quoted, breaking Mermaid syntax
        input_text = """
```mermaid
graph TD
    RepairLevel -- 强制修复(有损) --> DataLoss[DBCC CHECKDB]
    LockCheck -- 报错 5061 (锁冲突) --> KillProcess[执行脚本]
    Start([开始]) --> End{结束}
```
"""
        normalized = self.normalizer.normalize(input_text)
        
        # Edge labels should NOT be modified (no quotes added around parentheses content)
        self.assertIn("强制修复(有损)", normalized)
        self.assertIn("报错 5061 (锁冲突)", normalized)
        self.assertNotIn('强制修复("有损")', normalized)
        self.assertNotIn('报错 5061 ("锁冲突")', normalized)
        
        # Node labels SHOULD be quoted
        self.assertIn('(["开始"])', normalized)
        self.assertIn('{"结束"}', normalized)


