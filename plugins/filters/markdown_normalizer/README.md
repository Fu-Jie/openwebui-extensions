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

## Changelog

### v1.1.0
*   **Mermaid Fix Refinement**: Improved regex to handle nested parentheses in node labels (e.g., `ID("Label (text)")`) and avoided matching connection labels.
*   **HTML Safeguard Optimization**: Refined `_contains_html` to allow common tags like `<br/>`, `<b>`, `<i>`, etc., ensuring Mermaid diagrams with these tags are still normalized.
*   **Full-width Symbol Cleanup**: Fixed duplicate keys and incorrect quote mapping in `FULLWIDTH_MAP`.
*   **Bug Fixes**: Fixed missing `Dict` import in Python files.

## License

MIT
