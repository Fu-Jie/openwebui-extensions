# Markdown Normalizer Filter

A content normalizer filter for Open WebUI that fixes common Markdown formatting issues in LLM outputs. It ensures that code blocks, LaTeX formulas, Mermaid diagrams, and other Markdown elements are rendered correctly.

## Features

* **Details Tag Normalization**: Ensures proper spacing for `<details>` tags (used for thought chains). Adds a blank line after `</details>` and ensures a newline after self-closing `<details />` tags to prevent rendering issues.
* **Emphasis Spacing Fix**: Fixes extra spaces inside emphasis markers (e.g., `** text **` -> `**text**`) which can cause rendering failures. Includes safeguards to protect math expressions (e.g., `2 * 3 * 4`) and list variables.
* **Mermaid Syntax Fix**: Automatically fixes common Mermaid syntax errors, such as unquoted node labels (including multi-line labels and citations) and unclosed subgraphs. **New in v1.1.2**: Comprehensive protection for edge labels (text on connecting lines) across all link types (solid, dotted, thick).
* **Frontend Console Debugging**: Supports printing structured debug logs directly to the browser console (F12) for easier troubleshooting.
* **Code Block Formatting**: Fixes broken code block prefixes, suffixes, and indentation.
* **LaTeX Normalization**: Standardizes LaTeX formula delimiters (`\[` -> `$$`, `\(` -> `$`).
* **Thought Tag Normalization**: Unifies thought tags (`<think>`, `<thinking>` -> `<thought>`).
* **Escape Character Fix**: Cleans up excessive escape characters (`\\n`, `\\t`).
* **List Formatting**: Ensures proper newlines in list items.
* **Heading Fix**: Adds missing spaces in headings (`#Heading` -> `# Heading`).
* **Table Fix**: Adds missing closing pipes in tables.
* **XML Cleanup**: Removes leftover XML artifacts.

## Usage

1. Install the plugin in Open WebUI.
2. Enable the filter globally or for specific models.
3. Configure the enabled fixes in the **Valves** settings.
4. (Optional) **Show Debug Log** is enabled by default in Valves. This prints structured logs to the browser console (F12).
    > [!WARNING]
    > As this is an initial version, some "negative fixes" might occur (e.g., breaking valid Markdown). If you encounter issues, please check the console logs, copy the "Original" vs "Normalized" content, and submit an issue.

## Configuration (Valves)

* `priority`: Filter priority (default: 50).
* `enable_escape_fix`: Fix excessive escape characters.
* `enable_thought_tag_fix`: Normalize thought tags.
* `enable_details_tag_fix`: Normalize details tags (default: True).
* `enable_code_block_fix`: Fix code block formatting.
* `enable_latex_fix`: Normalize LaTeX formulas.
* `enable_list_fix`: Fix list item newlines (Experimental).
* `enable_unclosed_block_fix`: Auto-close unclosed code blocks.
* `enable_fullwidth_symbol_fix`: Fix full-width symbols in code blocks.
* `enable_mermaid_fix`: Fix Mermaid syntax errors.
* `enable_heading_fix`: Fix missing space in headings.
* `enable_table_fix`: Fix missing closing pipe in tables.
* `enable_xml_tag_cleanup`: Cleanup leftover XML tags.
* `enable_emphasis_spacing_fix`: Fix extra spaces in emphasis (default: True).
* `show_status`: Show status notification when fixes are applied.
* `show_debug_log`: Print debug logs to browser console.

## Troubleshooting ❓

* **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [Awesome OpenWebUI Issues](https://github.com/Fu-Jie/awesome-openwebui/issues)

## Changelog

### v1.2.3

* **List Marker Protection Enhancement**: Fixed a bug where list markers (`*`) followed by plain text and emphasis were having their spaces incorrectly stripped (e.g., `*   U16 forward` became `*U16 forward`).
* **Placeholder Support**: Confirmed that 4 or more underscores (e.g., `____`) are correctly treated as placeholders and not modified by the emphasis fix.

### v1.2.2

* **Code Block Indentation Fix**: Fixed an issue where code blocks nested inside lists were having their indentation incorrectly stripped. Now preserves proper indentation for nested code blocks.
* **Underscore Emphasis Support**: Extended emphasis spacing fix to support `__` (double underscore for bold) and `___` (triple underscore for bold+italic) syntax.
* **List Marker Protection**: Fixed a bug where list markers (`*`) followed by emphasis markers (`**`) were incorrectly merged (e.g., `*   **Yes**` became `***Yes**`). Added safeguard to prevent this.
* **Test Suite**: Added comprehensive pytest test suite with 56 test cases covering all major features.

### v1.2.1

* **Emphasis Spacing Fix**: Added a new fix for extra spaces inside emphasis markers (e.g., `** text **` -> `**text**`).
  * Uses a recursive approach to handle nested emphasis (e.g., `**bold _italic _**`).
  * Includes safeguards to prevent modifying math expressions (e.g., `2 * 3 * 4`) or list variables.
  * Controlled by the `enable_emphasis_spacing_fix` valve (default: True).

### v1.2.0

* **Details Tag Support**: Added normalization for `<details>` tags.
  * Ensures a blank line is added after `</details>` closing tags to separate thought content from the main response.
  * Ensures a newline is added after self-closing `<details ... />` tags to prevent them from interfering with subsequent Markdown headings (e.g., fixing `<details/>#Heading`).
  * Includes safeguard to prevent modification of `<details>` tags inside code blocks.

### v1.1.2

* **Mermaid Edge Label Protection**: Implemented comprehensive protection for edge labels (text on connecting lines) to prevent them from being incorrectly modified. Now supports all Mermaid link types including solid (`--`), dotted (`-.`), and thick (`==`) lines with or without arrows.
* **Bug Fixes**: Fixed an issue where lines without arrows (e.g., `A -- text --- B`) were not correctly protected.

### v1.1.0

* **Mermaid Fix Refinement**: Improved regex to handle nested parentheses in node labels (e.g., `ID("Label (text)")`) and avoided matching connection labels.
* **HTML Safeguard Optimization**: Refined `_contains_html` to allow common tags like `<br/>`, `<b>`, `<i>`, etc., ensuring Mermaid diagrams with these tags are still normalized.
* **Full-width Symbol Cleanup**: Fixed duplicate keys and incorrect quote mapping in `FULLWIDTH_MAP`.
* **Bug Fixes**: Fixed missing `Dict` import in Python files.

## License

MIT
