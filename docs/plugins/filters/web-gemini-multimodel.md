# Web Gemini Multimodal Filter

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.3.2</span>

A powerful filter that provides multimodal capabilities (PDF, Office, Images, Audio, Video) to any model in OpenWebUI.

---

## Overview

This plugin enables multimodal processing for any model by leveraging Gemini as an analyzer. It supports direct file processing for Gemini models and "Analyzer Mode" for other models (like DeepSeek, Llama), where Gemini analyzes the file and injects the result as context.

## Features

- :material-file-document-multiple: **Multimodal Support**: Process PDF, Word, Excel, PowerPoint, EPUB, MP3, MP4, and Images.
- :material-router-network: **Smart Routing**:
    - **Direct Mode**: Files are passed directly to Gemini models.
    - **Analyzer Mode**: Files are analyzed by Gemini, and results are injected into the context for other models.
- :material-history: **Persistent Context**: Maintains session history across multiple turns using OpenWebUI Chat ID.
- :material-database-check: **Deduplication**: Automatically tracks analyzed file hashes to prevent redundant processing.
- :material-subtitles: **Subtitle Enhancement**: Specialized mode for generating high-quality SRT subtitles from video/audio.

---

## Installation

1. Download the plugin file: [`web_gemini_multimodel.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/filters/web_gemini_multimodel_filter)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Configure the Gemini Adapter URL and other settings.
4. Enable the filter globally or per chat.

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `gemini_adapter_url` | string | `http://...` | URL of the Gemini Adapter service |
| `target_model_keyword` | string | `"webgemini"` | Keyword to identify Gemini models |
| `mode` | string | `"auto"` | `auto`, `direct`, or `analyzer` |
| `analyzer_base_model_id` | string | `"gemini-3.0-pro"` | Model used for document analysis |
| `subtitle_keywords` | string | `"字幕,srt"` | Keywords to trigger subtitle flow |

---

## Usage

1. **Upload a file** (PDF, Image, Video, etc.) in the chat.
2. **Ask a question** about the file.
3. The plugin will automatically process the file and provide context to your selected model.
