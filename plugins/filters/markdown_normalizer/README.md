# Markdown Normalizer Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 1.2.4 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

A content normalizer filter for Open WebUI that fixes common Markdown formatting issues in LLM outputs. It ensures that code blocks, LaTeX formulas, Mermaid diagrams, and other Markdown elements are rendered correctly.

## 🔥 What's New in v1.2.4

* **Documentation Sync**: Synchronized version numbers across all documentation and code files.

## ✨ Core Features

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

## How to Use 🛠️

1. Install the plugin in Open WebUI.
2. Enable the filter globally or for specific models.
3. Configure the enabled fixes in the **Valves** settings.
4. (Optional) **Show Debug Log** is enabled by default in Valves. This prints structured logs to the browser console (F12).
    > [!WARNING]
    > As this is an initial version, some "negative fixes" might occur (e.g., breaking valid Markdown). If you encounter issues, please check the console logs, copy the "Original" vs "Normalized" content, and submit an issue.

## Configuration (Valves) ⚙️

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `priority` | `50` | Filter priority. Higher runs later (recommended after other filters). |
| `enable_escape_fix` | `True` | Fix excessive escape characters (`\n`, `\t`, etc.). |
| `enable_escape_fix_in_code_blocks` | `False` | Apply escape fix inside code blocks (may affect valid code). |
| `enable_thought_tag_fix` | `True` | Normalize thought tags (`</thought>`). |
| `enable_details_tag_fix` | `True` | Normalize `<details>` tags and add safe spacing. |
| `enable_code_block_fix` | `True` | Fix code block formatting (indentation/newlines). |
| `enable_latex_fix` | `True` | Normalize LaTeX delimiters (`\[` -> `$$`, `\(` -> `$`). |
| `enable_list_fix` | `False` | Fix list item newlines (experimental). |
| `enable_unclosed_block_fix` | `True` | Auto-close unclosed code blocks. |
| `enable_fullwidth_symbol_fix` | `False` | Fix full-width symbols in code blocks. |
| `enable_mermaid_fix` | `True` | Fix common Mermaid syntax errors. |
| `enable_heading_fix` | `True` | Fix missing space in headings. |
| `enable_table_fix` | `True` | Fix missing closing pipe in tables. |
| `enable_xml_tag_cleanup` | `True` | Cleanup leftover XML tags. |
| `enable_emphasis_spacing_fix` | `False` | Fix extra spaces in emphasis. |
| `show_status` | `True` | Show status notification when fixes are applied. |
| `show_debug_log` | `True` | Print debug logs to browser console (F12). |

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## 🧩 Others

### Troubleshooting ❓

* **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

### Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
