# Smart Mind Map

<span class="category-badge action">Action</span>
<span class="version-badge">v0.9.2</span>

Intelligently analyzes text content and generates interactive mind maps for better visualization and understanding.

---

## Overview

The Smart Mind Map plugin transforms text content into beautiful, interactive mind maps. It uses AI to analyze the structure of your content and creates a hierarchical visualization that makes complex information easier to understand.

## Features

- :material-brain: **LLM Analysis**: Uses configurable models to extract key concepts and hierarchy
- :material-gesture-swipe: **Rich Controls**: Zoom, reset view, expand level selector (All/2/3) and fullscreen
- :material-palette: **Theme Aware**: Auto-detects OpenWebUI light/dark theme with manual toggle
- :material-download: **One-Click Export**: Download high-res PNG, copy SVG, or copy Markdown source
- :material-translate: **Multi-language**: Matches output language to the input text

---

## Installation

1. Download the plugin file: [`smart_mind_map.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/smart-mind-map)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions** (Actions)
3. Enable the plugin, and optionally allow iframe same-origin access so theme auto-detection works

---

## Usage

1. Enable **Smart Mind Map** in chat settings, then provide at least ~100 characters of text
2. Click the **Mind Map** action button on a message to trigger generation
3. Interact with the visualization:
   - **Zoom & Reset**: Scroll or use the + / - / ↻ controls
   - **Expand Levels**: Switch between All / 2 / 3 levels
   - **Theme & Fullscreen**: Toggle light/dark or enter fullscreen
4. Export with one click: **PNG**, **Copy SVG**, or **Copy Markdown**

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `SHOW_STATUS` | boolean | `true` | Show status updates in chat during processing |
| `MODEL_ID` | string | `""` | Built-in LLM ID for analysis (empty uses current chat model) |
| `MIN_TEXT_LENGTH` | integer | `100` | Minimum characters required before analysis runs |
| `CLEAR_PREVIOUS_HTML` | boolean | `false` | Clear previous plugin HTML instead of merging |
| `MESSAGE_COUNT` | integer | `1` | Number of recent messages to include (1–5) |

---

## Example Output

The plugin generates an interactive HTML mind map embedded in the chat:

```
📊 Mind Map Generated
├── Main Topic
│   ├── Subtopic 1
│   │   ├── Detail A
│   │   └── Detail B
│   ├── Subtopic 2
│   └── Subtopic 3
└── Related Concepts
```

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - No additional Python packages required
    - For theme auto-detection/PNG export accuracy, allow iframe same-origin access in **User Settings → Interface → Artifacts**

---

## Troubleshooting

??? question "Mind map is not displaying?"
    - Ensure the input text is at least `MIN_TEXT_LENGTH` characters
    - Confirm a valid `MODEL_ID` is available (or leave empty to use current model)
    - Refresh and re-run after enabling the plugin

??? question "Theme looks wrong or PNG export is blank?"
    - Enable iframe same-origin access so the plugin can read the parent theme
    - Wait for the mind map to fully render before exporting

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/smart-mind-map){ .md-button }
