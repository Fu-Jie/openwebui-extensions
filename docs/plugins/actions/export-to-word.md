# Export to Word

<span class="category-badge action">Action</span>
<span class="version-badge">v0.2.0</span>

Export conversation to Word (.docx) with **syntax highlighting**, **native math equations**, **Mermaid diagrams**, **citations**, and **enhanced table formatting**.

---

## Overview

The Export to Word plugin converts chat messages from Markdown to a polished Word document. It handles headings, lists, tables, code blocks, and blockquotes while keeping both English and Chinese text rendering clean.

## Features

- :material-file-word-box: **One-Click Export**: Adds an "Export to Word" action button to the chat.
- :material-format-bold: **Markdown Conversion**: Converts Markdown syntax to Word formatting (headings, bold, italic, code, tables, lists).
- :material-code-tags: **Syntax Highlighting**: Code blocks are highlighted with Pygments (supports 500+ languages).
- :material-sigma: **Native Math Equations**: LaTeX math (`$$...$$`, `\[...\]`, `$...$`, `\(...\)`) converted to editable Word equations.
- :material-graph: **Mermaid Diagrams**: Mermaid flowcharts and sequence diagrams rendered as images in the document.
- :material-book-open-page-variant: **Citations & References**: Auto-generates a References section from OpenWebUI sources with clickable citation links.
- :material-brain-off: **Reasoning Stripping**: Automatically removes AI thinking blocks (`<think>`, `<analysis>`) from exports.
- :material-table: **Enhanced Tables**: Smart column widths, column alignment (`:---`, `---:`, `:---:`), header row repeat across pages.
- :material-format-quote-close: **Blockquote Support**: Markdown blockquotes are rendered with left border and gray styling.
- :material-translate: **Multi-language Support**: Properly handles both Chinese and English text.
- :material-file-document-outline: **Smarter Filenames**: Configurable title source (Chat Title, AI Generated, or Markdown Title).

---

## Configuration

You can configure the following settings via the **Valves** button in the plugin settings:

| Valve | Description | Default |
| :--- | :--- | :--- |
| `TITLE_SOURCE` | Source for document title/filename. Options: `chat_title`, `ai_generated`, `markdown_title` | `chat_title` |
| `MERMAID_JS_URL` | URL for the Mermaid.js library (for diagram rendering). | `https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js` |
| `MERMAID_PNG_SCALE` | Scale factor for Mermaid PNG generation (Resolution). Higher = clearer but larger file size. | `3.0` |
| `MERMAID_DISPLAY_SCALE` | Scale factor for Mermaid visual size in Word. >1.0 to enlarge, <1.0 to shrink. | `1.5` |
| `MERMAID_OPTIMIZE_LAYOUT` | Automatically convert LR (Left-Right) flowcharts to TD (Top-Down) for better fit. | `True` |
| `MERMAID_CAPTIONS_ENABLE` | Enable/disable figure captions for Mermaid diagrams. | `True` |

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

## Supported Markdown Syntax

| Syntax | Word Result |
| :--- | :--- |
| `# Heading 1` to `###### Heading 6` | Heading levels 1-6 |
| `**bold**` or `__bold__` | Bold text |
| `*italic*` or `_italic_` | Italic text |
| `***bold italic***` | Bold + Italic |
| `` `inline code` `` | Monospace with gray background |
| ` ``` code block ``` ` | **Syntax highlighted** code block |
| `> blockquote` | Left-bordered gray italic text |
| `[link](url)` | Blue underlined link text |
| `~~strikethrough~~` | Strikethrough text |
| `- item` or `* item` | Bullet list |
| `1. item` | Numbered list |
| Markdown tables | **Enhanced table** with smart widths |
| `---` or `***` | Horizontal rule |
| `$$LaTeX$$` or `\[LaTeX\]` | **Native Word equation** (display) |
| `$LaTeX$` or `\(LaTeX\)` | **Native Word equation** (inline) |
| ` ```mermaid ... ``` ` | **Mermaid diagram** as image |
| `[1]` citation markers | **Clickable links** to References |

---

## Requirements

!!! note "Prerequisites"
    - `python-docx==1.1.2` - Word document generation
    - `Pygments>=2.15.0` - Syntax highlighting
    - `latex2mathml` - LaTeX to MathML conversion
    - `mathml2omml` - MathML to Office Math (OMML) conversion

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_docx){ .md-button }
