# Export to Word

Export conversation to Word (.docx) with **syntax highlighting**, **native math equations**, **Mermaid diagrams**, **citations**, and **enhanced table formatting**.

## Features

- **One-Click Export**: Adds an "Export to Word" action button to the chat.
- **Markdown Conversion**: Converts Markdown syntax to Word formatting (headings, bold, italic, code, tables, lists).
- **Syntax Highlighting**: Code blocks are highlighted with Pygments (supports 500+ languages).
- **Native Math Equations**: LaTeX math (`$$...$$`, `\[...\]`, `$...$`, `\(...\)`) converted to editable Word equations.
- **Mermaid Diagrams**: Mermaid flowcharts and sequence diagrams rendered as images in the document.
- **Citations & References**: Auto-generates a References section from OpenWebUI sources with clickable citation links.
- **Reasoning Stripping**: Automatically removes AI thinking blocks (`<think>`, `<analysis>`) from exports.
- **Enhanced Tables**: Smart column widths, column alignment (`:---`, `---:`, `:---:`), header row repeat across pages.
- **Blockquote Support**: Markdown blockquotes are rendered with left border and gray styling.
- **Multi-language Support**: Properly handles both Chinese and English text.
- **Smarter Filenames**: Configurable title source (Chat Title, AI Generated, or Markdown Title).

## Configuration

You can configure the following settings via the **Valves** button in the plugin settings:

- **TITLE_SOURCE**: Choose how the document title/filename is generated.
    - `chat_title`: Use the conversation title (default).
    - `ai_generated`: Use AI to generate a short title based on the content.
    - `markdown_title`: Extract the first h1/h2 heading from the Markdown content.
- **MERMAID_JS_URL**: URL for the Mermaid.js library (for diagram rendering).
- **MERMAID_PNG_SCALE**: Scale factor for Mermaid PNG generation (Resolution). Default: `3.0`.
- **MERMAID_DISPLAY_SCALE**: Scale factor for Mermaid visual size in Word. Default: `1.5`.
- **MERMAID_OPTIMIZE_LAYOUT**: Automatically convert LR (Left-Right) flowcharts to TD (Top-Down). Default: `True`.
- **MERMAID_CAPTIONS_ENABLE**: Enable/disable figure captions for Mermaid diagrams.

## Supported Markdown Syntax

| Syntax                              | Word Result                           |
| :---------------------------------- | :------------------------------------ |
| `# Heading 1` to `###### Heading 6` | Heading levels 1-6                    |
| `**bold**` or `__bold__`            | Bold text                             |
| `*italic*` or `_italic_`            | Italic text                           |
| `***bold italic***`                 | Bold + Italic                         |
| `` `inline code` ``                 | Monospace with gray background        |
| ` ``` code block ``` `              | **Syntax highlighted** code block     |
| `> blockquote`                      | Left-bordered gray italic text        |
| `[link](url)`                       | Blue underlined link text             |
| `~~strikethrough~~`                 | Strikethrough text                    |
| `- item` or `* item`                | Bullet list                           |
| `1. item`                           | Numbered list                         |
| Markdown tables                     | **Enhanced table** with smart widths  |
| `---` or `***`                      | Horizontal rule                       |
| `$$LaTeX$$` or `\[LaTeX\]`          | **Native Word equation** (display)    |
| `$LaTeX$` or `\(LaTeX\)`            | **Native Word equation** (inline)     |
| ` ```mermaid ... ``` `              | **Mermaid diagram** as image          |
| `[1]` citation markers              | **Clickable links** to References     |

## Usage

1. Install the plugin.
2. In any chat, click the "Export to Word" button.
3. The .docx file will be automatically downloaded to your device.

## Requirements

- `python-docx==1.1.2` - Word document generation
- `Pygments>=2.15.0` - Syntax highlighting
- `latex2mathml` - LaTeX to MathML conversion
- `mathml2omml` - MathML to Office Math (OMML) conversion

All dependencies are declared in the plugin docstring.

## Font Configuration

- **English Text**: Times New Roman
- **Chinese Text**: SimSun (宋体) for body, SimHei (黑体) for headings
- **Code**: Consolas

## Changelog

### v0.2.0
- Added native math equation support (LaTeX → OMML)
- Added Mermaid diagram rendering
- Added citations and references section generation
- Added automatic reasoning block stripping
- Enhanced table formatting with smart column widths and alignment

### v0.1.1
- Initial release with basic Markdown to Word conversion

## Author

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License
