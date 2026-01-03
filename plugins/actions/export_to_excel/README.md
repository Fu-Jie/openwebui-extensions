# Export to Excel

This plugin allows you to export your chat history to an Excel (.xlsx) file directly from the chat interface.

## What's New in v0.3.6

- **OpenWebUI-Style Theme**: Modern dark header (#1f2937) with light gray zebra striping for better readability.
- **Zebra Striping**: Alternating row colors (#ffffff / #f3f4f6) for improved visual scanning.
- **Smart Data Type Conversion**: Automatically converts columns to numeric or datetime types with fallback to string.
- **Full Cell Bold/Italic**: Supports full cell Markdown bold (`**text**`) and italic (`*text*`) formatting in Excel.
- **Partial Markdown Cleanup**: Automatically removes partial Markdown formatting symbols (e.g., `Some **bold** text` → `Some bold text`) for cleaner Excel output.
- **Export Scope**: Added `EXPORT_SCOPE` valve to choose between exporting tables from the "Last Message" (default) or "All Messages".
- **Smart Sheet Naming**: Automatically names sheets based on Markdown headers, AI titles (if enabled), or message index (e.g., `Msg1-Tab1`).
- **Multiple Tables Support**: Improved handling of multiple tables within single or multiple messages.
- **Smart Filename Generation**: Supports generating filenames based on Chat Title, AI Summary, or Markdown Headers.
- **Configuration Options**: Added `TITLE_SOURCE` setting to control filename generation strategy.
- **AI Title Generation**: Added `MODEL_ID` setting to specify the model for AI title generation, with progress notifications.

## Features

- **One-Click Export**: Adds an "Export to Excel" button to the chat.
- **Automatic Header Extraction**: Intelligently identifies table headers from the chat content.
- **Multi-Table Support**: Handles multiple tables within a single chat session.

## Configuration

- **Title Source**: Choose how the filename is generated:
  - `chat_title`: Use the chat title (default).
  - `ai_generated`: Use AI to generate a concise title from the content.
  - `markdown_title`: Extract the first H1/H2 header from the markdown content.

## Usage

1. Install the plugin.
2. In any chat, click the "Export to Excel" button.
3. The file will be automatically downloaded to your device.

## Author

Fu-Jie
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License
