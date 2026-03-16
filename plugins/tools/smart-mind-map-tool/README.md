# Smart Mind Map Tool - Knowledge Visualization & Structuring

Smart Mind Map Tool is the tool version of the popular Smart Mind Map action plugin for Open WebUI. It allows the model to proactively generate interactive mind maps during conversations by intelligently analyzing context and structuring knowledge into visual hierarchies.

| By [Fu-Jie](https://github.com/Fu-Jie) · v1.0.0 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

> 💡 **Note**: Prefer using the manual trigger button instead? Check out the [Smart Mind Map Action Version](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a) here.

---

## Install with Batch Install Plugins

If you already use [Batch Install Plugins from GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins), you can install or update this plugin with:

```text
Install plugin from Fu-Jie/openwebui-extensions
```

When the selection dialog opens, search for this plugin, check it, and continue.

> [!IMPORTANT]
> If the official OpenWebUI Community version is already installed, remove it first. After that, Batch Install Plugins can keep this plugin updated in future runs.

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
