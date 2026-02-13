# Smart Infographic

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 1.5.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

An Open WebUI plugin powered by the AntV Infographic engine. It transforms long text into professional, beautiful infographics with a single click.

## 🔥 What's New in v1.5.0

- 🌐 **Smart Language Detection**: Automatically detects the accurate UI language from your browser.
- 🗣️ **Context-Aware Generation**: Generated infographics now strictly follow the language of your input content (e.g., input Japanese -> output Japanese infographic).
- 🐛 **Bug Fixes**: Fixed issues with language synchronization between the UI and generated content.

## ✨ Key Features

- 🚀 **AI-Powered Transformation**: Automatically analyzes text logic, extracts key points, and generates structured charts.
- 🎨 **70+ Professional Templates**: Includes various AntV official templates: Lists, Trees, Roadmaps, Timelines, Comparison Tables, SWOT, Quadrants, and Statistical Charts.
- 🔍 **Auto-Icon Matching**: Built-in logic to search and match the most relevant icons (Iconify) and illustrations (unDraw).
- 📥 **Multi-Format Export**: Download your infographics as **SVG**, **PNG**, or a **Standalone HTML** file.
- 🌈 **Highly Customizable**: Supports Dark/Light modes, auto-adapts theme colors, with bold titles and refined card layouts.
- 📱 **Responsive Design**: Generated charts look great on both desktop and mobile devices.

## 🚀 How to Use

1. **Install**: Search for "Smart Infographic" in the Open WebUI Community and install.
2. **Trigger**: Enter your text in the chat, then click the **Action Button** (📊 icon) next to the input box.
3. **AI Processing**: The AI analyzes the text and generates the infographic syntax.
4. **Preview & Download**: Preview the result and use the download buttons below to save your infographic.

## ⚙️ Configuration (Valves)

You can adjust the following parameters in the plugin settings to optimize the generation:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| **Show Status (SHOW_STATUS)** | `True` | Whether to show real-time AI analysis and generation status in the chat. |
| **Model ID (MODEL_ID)** | `Empty` | Specify the LLM model for text analysis. If empty, the current chat model is used. |
| **Min Text Length (MIN_TEXT_LENGTH)** | `100` | Minimum characters required to trigger analysis, preventing accidental triggers on short text. |
| **Clear Previous (CLEAR_PREVIOUS_HTML)** | `False` | Whether to clear previous charts. If `False`, new charts will be appended below. |
| **Message Count (MESSAGE_COUNT)** | `1` | Number of recent messages to use for analysis. Increase this for more context. |
| **Output Mode (OUTPUT_MODE)** | `image` | `image` for static image embedding (default, better compatibility), `html` for interactive chart. |

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## 🛠️ Supported Template Types

| Category | Template Name | Use Case |
| :--- | :--- | :--- |
| **Sequence** | `sequence-timeline-simple`, `sequence-roadmap-vertical-simple`, `sequence-snake-steps-compact-card` | Timelines, Roadmaps, Processes |
| **Lists** | `list-grid-candy-card-lite`, `list-row-horizontal-icon-arrow`, `list-column-simple-vertical-arrow` | Features, Bullet Points, Lists |
| **Comparison** | `compare-binary-horizontal-underline-text-vs`, `compare-swot`, `quadrant-quarter-simple-card` | Pros/Cons, SWOT, Quadrants |
| **Hierarchy** | `hierarchy-tree-tech-style-capsule-item`, `hierarchy-structure` | Org Charts, Structures |
| **Charts** | `chart-column-simple`, `chart-bar-plain-text`, `chart-line-plain-text`, `chart-wordcloud` | Trends, Distributions, Metrics |

## Troubleshooting ❓

- **Plugin not working?**: Check if the filter/action is enabled in the model settings.
- **Debug Logs**: Enable `SHOW_STATUS` in Valves to see progress updates.
- **Error Messages**: If you see an error, please copy the full error message and report it.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

## 📝 Syntax Example (For Advanced Users)

You can also input this syntax directly for AI to render:

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
