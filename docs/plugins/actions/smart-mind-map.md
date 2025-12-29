# Smart Mind Map

<span class="category-badge action">Action</span>
<span class="version-badge">v0.7.2</span>

Intelligently analyzes text content and generates interactive mind maps for better visualization and understanding.

---

## Overview

The Smart Mind Map plugin transforms text content into beautiful, interactive mind maps. It uses AI to analyze the structure of your content and creates a hierarchical visualization that makes complex information easier to understand.

## Features

- :material-brain: **AI-Powered Analysis**: Intelligently extracts key concepts and relationships
- :material-gesture-swipe: **Interactive Navigation**: Zoom, pan, and explore the mind map
- :material-palette: **Beautiful Styling**: Modern design with customizable colors
- :material-download: **Export Options**: Save as image or structured data
- :material-translate: **Multi-language Support**: Works with multiple languages

---

## Installation

1. Download the plugin file: [`smart_mind_map.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/smart-mind-map)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Start a conversation and get a response from the AI
2. Click the **Mind Map** button in the message action bar
3. Wait for the mind map to generate
4. Interact with the visualization:
   - **Zoom**: Scroll to zoom in/out
   - **Pan**: Click and drag to move around
   - **Expand/Collapse**: Click nodes to show/hide children

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `show_status` | boolean | `true` | Show processing status updates |
| `max_depth` | integer | `5` | Maximum depth of the mind map |
| `theme` | string | `"default"` | Color theme for the visualization |

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

---

## Troubleshooting

??? question "Mind map is not displaying?"
    Ensure your browser supports HTML5 Canvas and JavaScript is enabled.

??? question "Generation takes too long?"
    For very long texts, the AI analysis may take more time. Consider breaking down the content into smaller sections.

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/smart-mind-map){ .md-button }
