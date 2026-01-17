# 📝 Export to Word (Enhanced)

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 0.4.3 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **License:** MIT

Export conversation to Word (.docx) with **syntax highlighting**, **native math equations**, **Mermaid diagrams**, **citations**, and **enhanced table formatting**.

## 🔥 What's New in v0.4.3

- ✨ **S3 Object Storage Support**: Direct access to images stored in S3/MinIO via boto3, bypassing API layer for faster exports.
- 🔧 **Multi-level File Fallback**: 6-level fallback mechanism for file retrieval (DB → S3 → Local → URL → API → Attributes).
- 🛡️ **Improved Error Handling**: Better logging and error messages for file retrieval failures.

## ✨ Key Features

- 🚀 **One-Click Export**: Adds an "Export to Word" action button to the chat.
- 📄 **Markdown Conversion**: Full Markdown syntax support (headings, bold, italic, code, tables, lists).
- 🎨 **Syntax Highlighting**: Code blocks highlighted with Pygments (500+ languages).
- 🔢 **Native Math Equations**: LaTeX math (`$$...$$`, `\[...\]`, `$...$`) converted to editable Word equations.
- 📊 **Mermaid Diagrams**: Flowcharts and sequence diagrams rendered as images.
- 📚 **Citations & References**: Auto-generates References section with clickable citation links.
- 🧹 **Reasoning Stripping**: Automatically removes AI thinking blocks (`<think>`, `<analysis>`).
- 📋 **Enhanced Tables**: Smart column widths, alignment, header row repeat across pages.
- 💬 **Blockquote Support**: Markdown blockquotes with left border and gray styling.
- 🌐 **Multi-language Support**: Proper handling of Chinese and English text.

## 🚀 How to Use

1. **Install**: Search for "Export to Word" in the Open WebUI Community and install.
2. **Trigger**: In any chat, click the "Export to Word" action button.
3. **Download**: The .docx file will be automatically downloaded.

## ⚙️ Configuration (Valves)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| **Title Source (TITLE_SOURCE)** | `chat_title` | `chat_title`, `ai_generated`, or `markdown_title` |
| **Max Image Size (MAX_EMBED_IMAGE_MB)** | `20` | Maximum image size to embed (MB) |
| **UI Language (UI_LANGUAGE)** | `en` | `en` (English) or `zh` (Chinese) |
| **Latin Font (FONT_LATIN)** | `Times New Roman` | Font for Latin characters |
| **Asian Font (FONT_ASIAN)** | `SimSun` | Font for Asian characters |
| **Code Font (FONT_CODE)** | `Consolas` | Font for code blocks |
| **Table Header Color** | `F2F2F2` | Header background color (hex) |
| **Table Zebra Color** | `FBFBFB` | Alternating row color (hex) |
| **Mermaid PNG Scale** | `3.0` | Resolution multiplier for Mermaid images |
| **Math Enable** | `True` | Enable LaTeX math conversion |

## 🛠️ Supported Markdown Syntax

| Syntax | Word Result |
| :--- | :--- |
| `# Heading 1` to `###### Heading 6` | Heading levels 1-6 |
| `**bold**` or `__bold__` | Bold text |
| `*italic*` or `_italic_` | Italic text |
| `` `inline code` `` | Monospace with gray background |
| ` ``` code block ``` ` | **Syntax highlighted** code block |
| `> blockquote` | Left-bordered gray italic text |
| `[link](url)` | Blue underlined link |
| `~~strikethrough~~` | Strikethrough text |
| `- item` or `* item` | Bullet list |
| `1. item` | Numbered list |
| Markdown tables | **Enhanced table** with smart widths |
| `$$LaTeX$$` or `\[LaTeX\]` | **Native Word equation** (display) |
| `$LaTeX$` or `\(LaTeX\)` | **Native Word equation** (inline) |
| ` ```mermaid ... ``` ` | **Mermaid diagram** as image |
| `[1]` citation markers | **Clickable links** to References |

## 📦 Requirements

- `python-docx==1.1.2` - Word document generation
- `Pygments>=2.15.0` - Syntax highlighting
- `latex2mathml` - LaTeX to MathML conversion
- `mathml2omml` - MathML to Office Math (OMML) conversion

## 📝 Changelog

### v0.4.3
- **S3 Object Storage**: Direct S3/MinIO access via boto3 for faster image retrieval.
- **6-Level Fallback**: Robust file retrieval: DB → S3 → Local → URL → API → Attributes.
- **Better Logging**: Improved error messages for debugging file access issues.

### v0.4.1
- **Chinese Parameter Names**: Localized configuration names for Chinese version.

### v0.4.0
- **Multi-language Support**: UI language switching (English/Chinese).
- **Font & Style Configuration**: Customizable fonts and table colors.
- **Mermaid Enhancements**: Hybrid SVG+PNG rendering, background color config.
- **Performance**: Real-time progress updates for large exports.

## Troubleshooting ❓

- **Plugin not working?**: Check if the filter/action is enabled in the model settings.
- **Debug Logs**: Check the browser console (F12) for detailed logs if available.
- **Error Messages**: If you see an error, please copy the full error message and report it.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [Awesome OpenWebUI Issues](https://github.com/Fu-Jie/awesome-openwebui/issues)
