# Smart Mind Map Tool - Knowledge Visualization & Structuring

Smart Mind Map Tool is the tool version of the popular Smart Mind Map action plugin for Open WebUI. It allows the model to proactively generate interactive mind maps during conversations by intelligently analyzing context and structuring knowledge into visual hierarchies.

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.0.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

> 💡 **Note**: Prefer using the manual trigger button instead? Check out the [Smart Mind Map Action Version](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a) here.

---

## Why is there a Tool version?

1. **Powered by OpenWebUI 0.8.0 Rich UI**: Previous versions of OpenWebUI did not support embedding custom HTML/iframes directly into the chat stream. Starting with 0.8.0, the platform introduced full Rich UI rendering support for **both Actions and Tools**, unleashing interactive frontend possibilities.
2. **AI Autonomous Invocation (vs. Action)**: While an **Action** is passive and requires a manual button click from the user, the **Tool** version gives the model **autonomy**. The AI can analyze the conversational context and decide on its own exactly when generating a mind map would be most helpful, offering a true "smart assistant" experience.

It is perfect for:

- Summarizing complex discussions.
- Planning projects or outlining articles.
- Explaining hierarchical concepts.

## ✨ Key Features

- ✅ **Proactive Generation**: The AI triggers the tool automatically when it senses a need for structured visualization.
- ✅ **Full Context Awareness**: Supports aggregation of the entire conversation history to generate comprehensive knowledge maps.
- ✅ **Native Multi-language UI (i18n)**: Automatically detects and adapts to your browser/system language (en-US, zh-CN, ja-JP, etc.).
- ✅ **Premium UI/UX**: Matches the Action version with a compact toolbar, glassmorphism aesthetics, and professional borders.
- ✅ **Interactive Controls**: Zoom (In/Out/Reset), Level-based expansion (Default to Level 3), and Fullscreen mode.
- ✅ **High-Quality Export**: Export your mind maps as print-ready PNG images.

## 🛠️ Installation & Setup

1. **Install**: Upload `smart_mind_map_tool.py` to your OpenWebUI Admin Settings -> Plugins -> Tools.
2. **Enable Native Tool Calling**: Navigate to `Admin Settings -> Models` or your workspace settings, and ensure that **Native Tool Calling** is enabled for your selected model. This is required for the AI to reliably and actively invoke the tool automatically.
3. **Assign**: Toggle the tool "ON" for your desired models in the workspace or model settings.
4. **Configure**:
   - `MESSAGE_COUNT`: Set to `12` (default) to use the 12 most recent messages, or `0` for the entire conversation history.
   - `MODEL_ID`: Specify a preferred model for analysis (defaults to the current chat model).

## ⚙️ Configuration (Valves)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `MODEL_ID` | (Empty) | The model used for text analysis. If empty, uses the current chat model. |
| `MESSAGE_COUNT` | `12` | Number of messages to aggregate. `0` = All messages. |
| `MIN_TEXT_LENGTH` | `100` | Minimum character count required to trigger a mind map. |

## ❓ FAQ & Troubleshooting

- **Language mismatch?**: The tool uses a 4-level detection (Frontend Script > Browser Header > User Profile > Default). Ensure your browser language is set correctly.
- **Too tiny or too large?**: We've optimized the height to `500px` for inline chat display with a responsive "Fit to Screen" logic.
- **Exporting**: Click the "⛶" for fullscreen if you want a wider view before exporting to PNG.

---

## ⭐ Support

If this tool helps you visualize ideas better, please give us a star on [GitHub](https://github.com/Fu-Jie/openwebui-extensions).

## ⚖️ License

MIT License. Developed with ❤️ by Fu-Jie.
