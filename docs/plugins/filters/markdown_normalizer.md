# Markdown Normalizer Filter
| By [Fu-Jie](https://github.com/Fu-Jie) · v1.2.8 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-0%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%A7%A9&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

A powerful, context-aware content normalizer filter for Open WebUI designed to fix common Markdown formatting issues in LLM outputs. It ensures that code blocks, LaTeX formulas, Mermaid diagrams, and other structural Markdown elements are rendered flawlessly, without destroying valid technical content.

> 🏆 **Featured by OpenWebUI Official** — This plugin was recommended in the official OpenWebUI Community Newsletter: [January 28, 2026](https://openwebui.com/blog/newsletter-january-28-2026)

[English](https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/filters/markdown_normalizer/README.md) | [简体中文](https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/filters/markdown_normalizer/README_CN.md)

---

## 🔥 What's New in v1.2.8
* **Safe-by-Default Strategy**: The `enable_escape_fix` feature is now **disabled by default**. This prevents unwanted modifications to valid technical text like Windows file paths (`C:\new\test`) or complex LaTeX formulas.
* **LaTeX Parsing Fix**: Improved the logic for identifying display math (`$$ ... $$`). Fixed a bug where LaTeX commands starting with `\n` (like `\nabla`) were incorrectly treated as newlines.
* **Reliability Enhancement**: Complete error fallback mechanism. Guarantees 0% data loss during processing.
* **Inline Code Protection**: Upgraded escaping logic to protect inline code blocks (`` `...` ``).
* **Code Block Escaping Control**: The `enable_escape_fix_in_code_blocks` Valve now correctly targets broken newlines inside code blocks (perfect for fixing flat SQL queries) when enabled.
* **Privacy Optimization**: `show_debug_log` now defaults to `False` to prevent console noise.

---

## 🚀 Why do you need this plugin? (What does it do?)

Language Models (LLMs) often generate malformed Markdown due to tokenization artifacts, aggressive escaping, or hallucinated formatting. If you've ever seen:
- A `mermaid` diagram fail to render because of missing quotes around labels.
- A SQL block stuck on a single line because `\n` was output literally instead of a real newline.
- A `<details>` block break the entire chat rendering because of missing newlines.
- A LaTeX formula fail because the LLM used `\[` instead of `$$`.

**This plugin automatically intercepts the LLM's raw output, analyzes its structure, and surgically repairs these formatting errors in real-time before they reach your browser.**

## ✨ Comprehensive Feature List

### 1. Advanced Structural Protections (Context-Aware)
Before making any changes, the plugin builds a semantic map of the text to protect your technical content:
- **Code Block Protection**: Skips formatting inside ` ``` ` code blocks by default to protect code logic.
- **Inline Code Protection**: Recognizes `` `code` `` snippets and protects regular expressions and file paths (e.g., `C:\Windows`) from being incorrectly unescaped.
- **LaTeX Protection**: Identifies inline (`$`) and block (`$$`) formulas to prevent modifying critical math commands like `\times`, `\theta`, or `\nu`.

### 2. Auto-Healing Transformations
- **Details Tag Normalization**: `<details>` blocks (often used for Chain of Thought) require strict spacing to render correctly. The plugin automatically injects blank lines after `</details>` and self-closing `<details />` tags.
- **Mermaid Syntax Fixer**: One of the most common LLM errors is omitting quotes in Mermaid diagrams (e.g., `A --> B(Some text)`). This plugin parses the Mermaid syntax and auto-quotes labels and citations to guarantee the graph renders.
- **Emphasis Spacing Fix**: Fixes formatting-breaking extra spaces inside bold/italic markers (e.g., `** text **` becomes `**text**`) while cleverly ignoring math expressions like `2 * 3 * 4`.
- **Intelligent Escape Character Cleanup**: Removes excessive literal `\n` and `\t` generated by some models and converts them to actual structural newlines (only in safe text areas).
- **LaTeX Standardization**: Automatically upgrades old-school LaTeX delimiters (`\[...\]` and `\(...\)`) to modern Markdown standards (`$$...$$` and `$ ... $`).
- **Thought Tag Unification**: Standardizes various model thought outputs (`<think>`, `<thinking>`) into a unified `<thought>` tag.
- **Broken Code Block Repair**: Fixes indentation issues, repairs mangled language prefixes (e.g., ` ```python`), and automatically closes unclosed code blocks if a generation was cut off.
- **List & Table Formatting**: Injects missing newlines to repair broken numbered lists and adds missing closing pipes (`|`) to tables.
- **XML Artifact Cleanup**: Silently removes leftover `<antArtifact>` or `<antThinking>` tags often leaked by Claude models.

### 3. Reliability & Safety
- **100% Rollback Guarantee**: If any normalization logic fails or crashes, the plugin catches the error and silently returns the exact original text, ensuring your chat never breaks.

## 🌐 Multilingual Support

The plugin UI and status notifications automatically switch based on your language:
`English`, `简体中文`, `繁體中文 (香港)`, `繁體中文 (台灣)`, `한국어`, `日本語`, `Français`, `Deutsch`, `Español`, `Italiano`, `Tiếng Việt`, `Bahasa Indonesia`.

## How to Use 🛠️

1. Install the plugin in Open WebUI.
2. Enable the filter globally or assign it to specific models (highly recommended for models with poor formatting).
3. Tune the specific fixes you want via the **Valves** settings.

## Configuration (Valves) ⚙️

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `priority` | `50` | Filter priority. Higher runs later (recommended to run this after all other content filters). |
| `enable_escape_fix` | `False` | Convert excessive literal escape characters (`\n`, `\t`) to real spacing. (Default: False for safety). |
| `enable_escape_fix_in_code_blocks` | `False` | **Pro-tip**: Turn this ON if your SQL/HTML code blocks are constantly printing on a single line. Turn OFF for Python/C++. |
| `enable_thought_tag_fix` | `True` | Normalize `<think>` tags. |
| `enable_details_tag_fix` | `True` | Normalize `<details>` spacing. |
| `enable_code_block_fix` | `True` | Fix code block indentation and newlines. |
| `enable_latex_fix` | `True` | Standardize LaTeX delimiters (`\[` -> `$$`). |
| `enable_list_fix` | `False` | Fix list item newlines (experimental). |
| `enable_unclosed_block_fix` | `True` | Auto-close unclosed code blocks. |
| `enable_mermaid_fix` | `True` | Fix common Mermaid syntax errors (auto-quoting). |
| `enable_heading_fix` | `True` | Add missing space after heading hashes (`#Title` -> `# Title`). |
| `enable_table_fix` | `True` | Add missing closing pipe in tables. |
| `enable_xml_tag_cleanup` | `True` | Remove leftover XML artifacts. |
| `enable_emphasis_spacing_fix` | `False` | Fix extra spaces in emphasis formatting. |
| `show_status` | `True` | Show UI status notification when a fix is actively applied. |
| `show_debug_log` | `False` | Print detailed before/after diffs to browser console (F12). |

## ⭐ Support
If this plugin saves your day, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you!

## 🧩 Others
* **Troubleshooting**: Encountering "negative fixes"? Enable `show_debug_log`, check your console, and submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)
