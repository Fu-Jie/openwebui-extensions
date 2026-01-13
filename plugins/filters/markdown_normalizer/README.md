# Markdown Normalizer Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie)
**Version:** 1.1.0

A content normalizer filter for Open WebUI that fixes common Markdown formatting issues in LLM outputs. It ensures that code blocks, LaTeX formulas, Mermaid diagrams, and other Markdown elements are rendered correctly.

## Features

*   **Mermaid Syntax Fix**: Automatically fixes common Mermaid syntax errors, such as unquoted node labels (including multi-line labels and citations) and unclosed subgraphs, ensuring diagrams render correctly.
*   **Frontend Console Debugging**: Supports printing structured debug logs directly to the browser console (F12) for easier troubleshooting.
*   **Code Block Formatting**: Fixes broken code block prefixes, suffixes, and indentation.
*   **LaTeX Normalization**: Standardizes LaTeX formula delimiters (`\[` -> `$$`, `\(` -> `$`).
*   **Thought Tag Normalization**: Unifies thought tags (`<think>`, `<thinking>` -> `<thought>`).
*   **Escape Character Fix**: Cleans up excessive escape characters (`\\n`, `\\t`).
*   **List Formatting**: Ensures proper newlines in list items.
*   **Heading Fix**: Adds missing spaces in headings (`#Heading` -> `# Heading`).
*   **Table Fix**: Adds missing closing pipes in tables.
*   **XML Cleanup**: Removes leftover XML artifacts.

## Usage

1.  Install the plugin in Open WebUI.
2.  Enable the filter globally or for specific models.
3.  Configure the enabled fixes in the **Valves** settings.
4.  (Optional) **Show Debug Log** is enabled by default in Valves. This prints structured logs to the browser console (F12).
    > [!WARNING]
    > As this is an initial version, some "negative fixes" might occur (e.g., breaking valid Markdown). If you encounter issues, please check the console logs, copy the "Original" vs "Normalized" content, and submit an issue.

## Configuration (Valves)

*   `priority`: Filter priority (default: 50).
*   `enable_escape_fix`: Fix excessive escape characters.
*   `enable_escape_fix_in_code_blocks`: Apply escape fix inside code blocks (⚠️ Warning: May break valid code like JSON strings or regex patterns. Default: False for safety).
*   `enable_thought_tag_fix`: Normalize thought tags.
*   `enable_code_block_fix`: Fix code block formatting.
*   `enable_latex_fix`: Normalize LaTeX formulas.
*   `enable_list_fix`: Fix list item newlines (Experimental).
*   `enable_unclosed_block_fix`: Auto-close unclosed code blocks.
*   `enable_fullwidth_symbol_fix`: Fix full-width symbols in code blocks.
*   `enable_mermaid_fix`: Fix Mermaid syntax errors.
*   `enable_heading_fix`: Fix missing space in headings.
*   `enable_table_fix`: Fix missing closing pipe in tables.
*   `enable_xml_tag_cleanup`: Cleanup leftover XML tags.
*   `show_status`: Show status notification when fixes are applied.
*   `show_debug_log`: Print debug logs to browser console.

## Testing

Comprehensive testing has been performed to validate all fixes. See [TESTING.md](TESTING.md) for detailed test coverage including:

- ✅ JSON strings with escape sequences
- ✅ Python regex patterns
- ✅ Multiple code blocks
- ✅ Fullwidth symbol conversion
- ✅ Mixed content (code + LaTeX + tables)
- ✅ Edge cases and error handling
- ✅ Thought tag normalization
- ✅ Mermaid edge label preservation

All 16 unit tests and 7 comprehensive integration tests pass.

## Changelog

### v1.1.1
*   **🐛 Mermaid Edge Label Fix**: Fixed issue where edge labels (text on arrows like `-- label -->`) with parentheses were incorrectly being quoted, breaking Mermaid syntax. Edge labels are now protected from node label normalization.

### v1.1.0
*   **🛡️ Safe Escape Fixing**: Added `enable_escape_fix_in_code_blocks` valve (default: False) to prevent corrupting valid code examples (JSON strings, regex patterns, etc.). Escape fixes now only apply outside code blocks by default.
*   **📝 Enhanced Full-width Symbol Map**: Added explicit full-width quotation marks (＂ U+FF02, ＇ U+FF07) and Unicode comments to all 16 mappings for better maintainability.
*   **🧹 Code Cleanup**: Removed duplicate `import logging` statement and fixed docstring warnings.
*   **✅ Improved Test Coverage**: Added comprehensive tests for code-block-aware escape fixing and full-width quote conversion.
*   **Mermaid Fix Refinement**: Improved regex to handle nested parentheses in node labels (e.g., `ID("Label (text)")`) and avoided matching connection labels.
*   **HTML Safeguard Optimization**: Refined `_contains_html` to allow common tags like `<br/>`, `<b>`, `<i>`, etc., ensuring Mermaid diagrams with these tags are still normalized.
*   **Bug Fixes**: Fixed missing `Dict` import in Python files.

## License

MIT
