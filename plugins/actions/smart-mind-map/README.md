# Smart Mind Map - Mind Mapping Generation Plugin

Smart Mind Map is a powerful OpenWebUI action plugin that intelligently analyzes long-form text content and automatically generates interactive mind maps, helping users structure and visualize knowledge.

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.9.2 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

## What's New in v0.9.2

**Language Rule Alignment**

- **Input Language First**: Mind map output now strictly matches the input text language.
- **Consistent Behavior**: Matches the infographic language rule for predictable multilingual output.

## Key Features 🔑

- ✅ **Intelligent Text Analysis**: Automatically identifies core themes, key concepts, and hierarchical structures.
- ✅ **Interactive Visualization**: Generates beautiful interactive mind maps based on Markmap.js.
- ✅ **High-Resolution PNG Export**: Export mind maps as high-quality PNG images (9x scale).
- ✅ **Complete Control Panel**: Zoom controls, expand level selection, and fullscreen mode.
- ✅ **Theme Switching**: Manual theme toggle button with automatic theme detection.
- ✅ **Image Output Mode**: Generate static SVG images embedded directly in Markdown for cleaner history.

## How to Use 🛠️

1. **Install**: Upload the `smart_mind_map.py` file in OpenWebUI Admin Settings -> Plugins -> Actions.
2. **Configure**: Ensure you have an LLM model configured (e.g., `gemini-2.5-flash`).
3. **Trigger**: Enable the "Smart Mind Map" action in chat settings and send text (at least 100 characters).
4. **Result**: The mind map will be rendered directly in the chat interface.

## Configuration (Valves) ⚙️

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `show_status` | `true` | Whether to display operation status updates. |
| `LLM_MODEL_ID` | `gemini-2.5-flash` | LLM model ID for text analysis. |
| `MIN_TEXT_LENGTH` | `100` | Minimum text length required for analysis. |
| `CLEAR_PREVIOUS_HTML` | `false` | Whether to clear previous plugin-generated HTML content. |
| `MESSAGE_COUNT` | `1` | Number of recent messages to use for generation (1-5). |
| `OUTPUT_MODE` | `html` | Output mode: `html` (interactive) or `image` (static). |

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## Troubleshooting ❓

- **Plugin not working?**: Check if the action is enabled in the chat settings.
- **Text too short**: Ensure input text contains at least 100 characters.
- **Rendering failed**: Check browser console for errors related to Markmap.js or D3.js.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

---

## Technical Architecture

- **Markmap.js**: Open-source mind mapping rendering engine.
- **PNG Export**: 9x scale factor for print-quality output (~1-2MB file size).
- **Theme Detection**: 4-level priority detection (Manual > Meta > Class > System).
- **Security**: XSS protection and input validation.

## Best Practices

1. **Text Preparation**: Provide text with clear structure and distinct hierarchies.
2. **Model Selection**: Use fast models like `gemini-2.5-flash` for daily use.
3. **Export Quality**: Use PNG for presentations and SVG for further editing.

## Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
