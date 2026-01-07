# 📊 Smart Infographic (AntV)

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.4.0 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)

An Open WebUI plugin powered by the AntV Infographic engine. It transforms long text into professional, beautiful infographics with a single click.

## 🔥 What's New in v1.4.0

- ✨ **Default Mode Change**: Default output mode is now `image` (static image) for better compatibility and cleaner chat history.
- ✨ **New Image Output Mode**: Support embedding infographics as static images (SVG).
- 📱 **Responsive Sizing**: Images now auto-adapt to the chat container width.
- 🔧 **New Configuration**: `OUTPUT_MODE` valve to control output format.

## ✨ Key Features

- 🚀 **AI-Powered Transformation**: Automatically analyzes text logic, extracts key points, and generates structured charts.
- 🎨 **Professional Templates**: Includes various AntV official templates: Lists, Trees, Mindmaps, Comparison Tables, Flowcharts, and Statistical Charts.
- 🔍 **Auto-Icon Matching**: Built-in logic to search and match the most relevant Material Design Icons based on content.
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

## 🛠️ Supported Template Types

| Category | Template Name | Use Case |
| :--- | :--- | :--- |
| **Lists & Hierarchy** | `list-grid`, `tree-vertical`, `mindmap` | Features, Org Charts, Brainstorming |
| **Sequence & Relation** | `sequence-roadmap`, `relation-circle` | Roadmaps, Circular Flows, Steps |
| **Comparison & Analysis** | `compare-binary`, `compare-swot`, `quadrant-quarter` | Pros/Cons, SWOT, Quadrants |
| **Charts & Data** | `chart-bar`, `chart-line`, `chart-pie` | Trends, Distributions, Metrics |

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
