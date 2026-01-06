# Smart Infographic

<span class="category-badge action">Action</span>
<span class="version-badge">v1.4.0</span>

An AntV Infographic engine powered plugin that transforms long text into professional, beautiful infographics with a single click.

---

## Overview

The Smart Infographic plugin uses AI to analyze text content and generate professional infographics using the AntV visualization engine. It automatically extracts key points and structures them into visually appealing charts and diagrams.

## Features

- :material-robot: **AI-Powered Transformation**: Automatically analyzes text logic, extracts key points, and generates structured charts
- :material-palette: **Professional Templates**: Includes various AntV official templates: Lists, Trees, Mindmaps, Comparison Tables, Flowcharts, and Statistical Charts
- :material-magnify: **Auto-Icon Matching**: Built-in logic to search and match the most relevant Material Design Icons based on content
- :material-download: **Multi-Format Export**: Download your infographics as **SVG**, **PNG**, or **Standalone HTML** file
- :material-theme-light-dark: **Theme Support**: Supports Dark/Light modes, auto-adapts theme colors
- :material-cellphone-link: **Responsive Design**: Generated charts look great on both desktop and mobile devices
- :material-image: **Image Embedding**: Option to embed charts as static images for better compatibility
- :material-monitor-screenshot: **Adaptive Sizing**: Images automatically adapt to the chat container width

---

## Installation

1. Download the plugin file: [`infographic.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/infographic)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Configure plugin settings (optional)
4. Enable the plugin

---

## Supported Template Types

| Category | Template Name | Use Case |
|:---------|:--------------|:---------|
| **Lists & Hierarchy** | `list-grid`, `tree-vertical`, `mindmap` | Features, Org Charts, Brainstorming |
| **Sequence & Relation** | `sequence-roadmap`, `relation-circle` | Roadmaps, Circular Flows, Steps |
| **Comparison & Analysis** | `compare-binary`, `compare-swot`, `quadrant-quarter` | Pros/Cons, SWOT, Quadrants |
| **Charts & Data** | `chart-bar`, `chart-line`, `chart-pie` | Trends, Distributions, Metrics |

---

## Usage

1. Enter your text content in the chat
2. Click the **Infographic** button (📊 icon) in the message action bar
3. Wait for AI to analyze and generate the infographic
4. Preview the result and use the download buttons to save

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `SHOW_STATUS` | boolean | `true` | Show real-time AI analysis and generation status |
| `MODEL_ID` | string | `""` | Specify the LLM model for text analysis. If empty, uses current chat model |
| `MIN_TEXT_LENGTH` | integer | `100` | Minimum characters required to trigger analysis |
| `CLEAR_PREVIOUS_HTML` | boolean | `false` | Whether to clear previous charts |
| `MESSAGE_COUNT` | integer | `1` | Number of recent messages to use for analysis |
| `OUTPUT_MODE` | string | `image` | `image` for static image embedding (default), `html` for interactive chart |

---

## Syntax Example (Advanced Users)

You can also input infographic syntax directly for rendering:

```infographic
infographic list-grid
data
  title 🚀 Plugin Benefits
  desc Why use the Smart Infographic plugin
  items
    - label Fast Generation
      desc Convert text to charts in seconds
    - label Beautiful Design
      desc Uses AntV professional design standards
```

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - No additional Python packages required (uses built-in OpenWebUI dependencies)

---

## Troubleshooting

??? question "Infographic not generating?"
    Make sure your text content is at least 100 characters (configurable via `MIN_TEXT_LENGTH`).

??? question "Template not matching content?"
    The AI automatically selects the best template based on content structure. For specific templates, you can use the advanced syntax.

??? question "Export not working?"
    Ensure your browser supports HTML5 Canvas and SVG. Try refreshing the page.

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/infographic){ .md-button }
