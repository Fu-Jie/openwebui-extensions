# Export to Word

<span class="category-badge action">Action</span>
<span class="version-badge">v0.1.0</span>

Export chat conversations to Word (.docx) with Markdown formatting, syntax highlighting, and smarter filenames.

---

## Overview

The Export to Word plugin converts chat messages from Markdown to a polished Word document. It handles headings, lists, tables, code blocks, and blockquotes while keeping both English and Chinese text rendering clean.

## Features

- :material-file-word-box: **DOCX Export**: Generate Word files with one click
- :material-format-bold: **Rich Markdown Support**: Headings, bold/italic, lists, tables
- :material-code-tags: **Syntax Highlighting**: Pygments-powered code blocks
- :material-format-quote-close: **Styled Blockquotes**: Left-border gray quote styling
- :material-file-document-outline: **Smart Filenames**: Prefers chat title → Markdown title → user/date

---

## Installation

1. Download the plugin file: [`export_to_word.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_docx)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Open the conversation you want to export
2. Click the **Export to Word** button in the message action bar
3. The `.docx` file will download automatically

---

## Supported Markdown

| Syntax | Word Result |
| :---------------------------------- | :-------------------------------- |
| `# Heading 1` to `###### Heading 6` | Heading levels 1-6 |
| `**bold**` / `__bold__` | Bold text |
| `*italic*` / `_italic_` | Italic text |
| `***bold italic***` | Bold + Italic |
| `` `inline code` `` | Monospace with gray background |
| <code>``` code block ```</code> | Syntax-highlighted code block |
| `> blockquote` | Left-bordered gray italic text |
| `[link](url)` | Blue underlined link |
| `~~strikethrough~~` | Strikethrough |
| `- item` / `* item` | Bullet list |
| `1. item` | Numbered list |
| Markdown tables | Grid table |
| `---` / `***` | Horizontal rule |

---

## Requirements

!!! note "Prerequisites"
    - `python-docx==1.1.2` (document generation)
    - `Pygments>=2.15.0` (syntax highlighting, optional but recommended)

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_docx){ .md-button }
