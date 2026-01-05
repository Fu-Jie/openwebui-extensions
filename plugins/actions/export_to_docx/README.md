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
- **MAX_EMBED_IMAGE_MB**: Maximum image size to embed into DOCX (MB). Default: `20`.
- **UI_LANGUAGE**: User interface language, supports `en` (English) and `zh` (Chinese). Default: `en`.
- **FONT_LATIN**: Font name for Latin characters. Default: `Times New Roman`.
- **FONT_ASIAN**: Font name for Asian characters. Default: `SimSun`.
- **FONT_CODE**: Font name for code blocks. Default: `Consolas`.
- **TABLE_HEADER_COLOR**: Table header background color (Hex without #). Default: `F2F2F2`.
- **TABLE_ZEBRA_COLOR**: Table alternating row background color (Hex without #). Default: `FBFBFB`.
- **MERMAID_JS_URL**: URL for the Mermaid.js library.
- **MERMAID_JSZIP_URL**: URL for the JSZip library (required for DOCX manipulation).
- **MERMAID_PNG_SCALE**: Scale factor for Mermaid PNG generation (Resolution). Default: `3.0`.
- **MERMAID_DISPLAY_SCALE**: Scale factor for Mermaid visual size in Word. Default: `1.0`.
- **MERMAID_OPTIMIZE_LAYOUT**: Automatically convert LR (Left-Right) flowcharts to TD (Top-Down). Default: `False`.
- **MERMAID_BACKGROUND**: Background color for Mermaid diagrams (e.g., `white`, `transparent`). Default: `transparent`.
- **MERMAID_CAPTIONS_ENABLE**: Enable/disable figure captions for Mermaid diagrams. Default: `True`.
- **MERMAID_CAPTION_STYLE**: Paragraph style name for Mermaid captions. Default: `Caption`.
- **MERMAID_CAPTION_PREFIX**: Caption prefix label (e.g., 'Figure'). Empty = auto-detect based on language.
- **MATH_ENABLE**: Enable LaTeX math block conversion (`\[...\]` and `$$...$$`). Default: `True`.
- **MATH_INLINE_DOLLAR_ENABLE**: Enable inline `$ ... $` math conversion. Default: `True`.

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

### v0.4.0

- **Multi-language Support**: Added UI language switching (English/Chinese) with localized messages.
- **Font & Style Configuration**: Customizable fonts for Latin/Asian text and code, plus table colors.
- **Mermaid Enhancements**: 
    - Hybrid client-side rendering (SVG+PNG) for better clarity and compatibility.
    - Configurable background color, fixing issues in dark mode.
    - Added error boundaries to prevent export failures on render errors.
- **Performance**: Real-time progress updates for large document exports.
- **Bug Fixes**: 
    - Fixed parsing errors in Markdown tables containing code blocks or links.
    - Fixed parsing issues with underscores (`_`), asterisks (`*`), and tildes (`~`) used as long separators.
    - Enhanced error handling for image embedding.

### v0.3.0

- **Mermaid Diagrams**: Native support for rendering Mermaid diagrams as images in Word.
- **Native Math**: Converts LaTeX equations to native Office MathML for editable equations.
- **Citations**: Automatic bibliography generation and citation linking.
- **Reasoning Removal**: Option to strip `<think>` blocks from the output.
- **Table Enhancements**: Improved table formatting with smart column widths.

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
