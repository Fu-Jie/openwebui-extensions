# Export to Excel

<span class="category-badge action">Action</span>
<span class="version-badge">v1.0.0</span>

Export chat conversations to Excel spreadsheet format for analysis, archiving, and sharing.

---

## Overview

The Export to Excel plugin allows you to download your chat conversations as Excel files. This is useful for:

- Archiving important conversations
- Analyzing chat data
- Sharing conversations with colleagues
- Creating documentation from AI-assisted research

## Features

- :material-file-excel: **Excel Export**: Standard `.xlsx` format
- :material-table: **Formatted Output**: Clean table structure
- :material-download: **One-Click Download**: Instant file generation
- :material-history: **Full History**: Exports complete conversation

---

## Installation

1. Download the plugin file: [`export_to_excel.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_excel)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Have a conversation you want to export
2. Click the **Export** button in the message action bar
3. The Excel file will be automatically downloaded

---

## Output Format

The exported Excel file contains:

| Column | Description |
|--------|-------------|
| Timestamp | When the message was sent |
| Role | User or Assistant |
| Content | The message text |
| Model | The AI model used (for assistant messages) |

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - No additional Python packages required (uses built-in libraries)

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_excel){ .md-button }
