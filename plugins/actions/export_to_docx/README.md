# Export to Word

Export current conversation from Markdown to Word (.docx) with proper Chinese and English encoding and smarter filenames.

## Features

- **One-Click Export**: Adds an "Export to Word" action button to the chat.
- **Markdown Conversion**: Converts Markdown syntax to Word formatting (headings, bold, italic, code, tables, lists).
- **Multi-language Support**: Properly handles both Chinese and English text without garbled characters.
- **Smarter Filenames**: Prefers chat title (from body or chat_id lookup) → first Markdown h1/h2 → user + date.

## Supported Markdown Syntax

| Syntax                              | Word Result                    |
| :---------------------------------- | :----------------------------- |
| `# Heading 1` to `###### Heading 6` | Heading levels 1-6             |
| `**bold**` or `__bold__`            | Bold text                      |
| `*italic*` or `_italic_`            | Italic text                    |
| `***bold italic***`                 | Bold + Italic                  |
| `` `inline code` ``                 | Monospace with gray background |
| ` ``` code block ``` `              | Code block with indentation    |
| `[link](url)`                       | Blue underlined link text      |
| `~~strikethrough~~`                 | Strikethrough text             |
| `- item` or `* item`                | Bullet list                    |
| `1. item`                           | Numbered list                  |
| Markdown tables                     | Table with grid                |
| `---` or `***`                      | Horizontal rule                |

## Usage

1. Install the plugin.
2. In any chat, click the "Export to Word" button.
3. The .docx file will be automatically downloaded to your device.


### Notes

- Title detection only considers h1/h2 headings.
- If the request carries `chat_id` (body or metadata), the plugin will fetch the chat title from the database when the body lacks one.
- Default fonts: Times New Roman (en), SimSun/SimHei (zh), Consolas (code).

### Requirements

- python-docx==1.1.2 (already declared in the plugin docstring; ensure installed in your environment).

## Font Configuration

- **English Text**: Times New Roman
- **Chinese Text**: SimSun (宋体) for body, SimHei (黑体) for headings
- **Code**: Consolas

## Author

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License
