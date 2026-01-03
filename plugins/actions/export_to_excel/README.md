# Export to Excel

This plugin allows you to export your chat history to an Excel (.xlsx) file directly from the chat interface.

### What's New in v0.3.5
- **Export Scope**: Added `EXPORT_SCOPE` valve to choose between exporting tables from the "Last Message" (default) or "All Messages".
- **Smart Sheet Naming**: Automatically names sheets based on Markdown headers, AI titles (if enabled), or message index (e.g., `Msg1-Tab1`).
- **Multiple Tables Support**: Improved handling of multiple tables within single or multiple messages.

## What's New in v0.3.4

- **Smart Filename Generation**: Now supports generating filenames based on Chat Title, AI Summary, or Markdown Headers.
- **Configuration Options**: Added `TITLE_SOURCE` setting to control filename generation strategy.

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
