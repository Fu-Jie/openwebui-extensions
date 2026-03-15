# 🌊 Deep Dive

| By [Fu-Jie](https://github.com/Fu-Jie) · v1.0.0 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-0%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%A7%A9&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

A comprehensive thinking lens that dives deep into any content - from context to logic, insights, and action paths.

## 🔥 What's New in v1.0.0

- ✨ **Thinking Chain Structure**: Moves from surface understanding to deep strategic action.
- 🔍 **Phase 01: The Context**: Panoramic view of the situation and background.
- 🧠 **Phase 02: The Logic**: Deconstruction of the underlying reasoning and mental models.
- 💎 **Phase 03: The Insight**: Extraction of non-obvious value and hidden implications.
- 🚀 **Phase 04: The Path**: Definition of specific, prioritized strategic directions.
- 🎨 **Premium UI**: Modern, process-oriented design with a "Thinking Line" timeline.
- 🌗 **Theme Adaptive**: Automatically adapts to OpenWebUI's light/dark theme.

## ✨ Key Features

- 🌊 **Deep Thinking**: Not just a summary, but a full deconstruction of content.
- 🧠 **Logical Analysis**: Reveals how arguments are built and identifies hidden assumptions.
- 💎 **Value Extraction**: Finds the "Aha!" moments and blind spots.
- 🚀 **Action Oriented**: Translates deep understanding into immediate, actionable steps.
- 🌍 **Multi-language**: Automatically adapts to the user's preferred language.
- 🌗 **Theme Support**: Seamlessly switches between light and dark themes based on OpenWebUI settings.

## 🚀 How to Use

1. **Input Content**: Provide any text, article, or meeting notes in the chat.
2. **Trigger Deep Dive**: Click the **Deep Dive** action button.
3. **Explore the Chain**: Follow the visual timeline from Context to Path.

## ⚙️ Configuration (Valves)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| **Show Status (SHOW_STATUS)** | `True` | Whether to show status updates during the thinking process. |
| **Model ID (MODEL_ID)** | `Empty` | LLM model for analysis. Empty = use current model. |
| **Min Text Length (MIN_TEXT_LENGTH)** | `200` | Minimum characters required for a meaningful deep dive. |
| **Clear Previous HTML (CLEAR_PREVIOUS_HTML)** | `True` | Whether to clear previous plugin results. |
| **Message Count (MESSAGE_COUNT)** | `1` | Number of recent messages to analyze. |

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## 🌗 Theme Support

The plugin automatically detects and adapts to OpenWebUI's theme settings:

- **Detection Priority**:
  1. Parent document `<meta name="theme-color">` tag
  2. Parent document `html/body` class or `data-theme` attribute
  3. System preference via `prefers-color-scheme: dark`

- **Requirements**: For best results, enable **iframe Sandbox Allow Same Origin** in OpenWebUI:
  - Go to **Settings** → **Interface** → **Artifacts** → Check **iframe Sandbox Allow Same Origin**

## 🎨 Visual Preview

The plugin generates a structured thinking timeline:

```
┌─────────────────────────────────────┐
│  🌊 Deep Dive Analysis              │
│  👤 User  📅 Date  📊 Word count    │
├─────────────────────────────────────┤
│  🔍 Phase 01: The Context           │
│  [High-level panoramic view]        │
│                                     │
│  🧠 Phase 02: The Logic             │
│  • Reasoning structure...           │
│  • Hidden assumptions...            │
│                                     │
│  💎 Phase 03: The Insight           │
│  • Non-obvious value...             │
│  • Blind spots revealed...          │
│                                     │
│  🚀 Phase 04: The Path              │
│  ▸ Priority Action 1...             │
│  ▸ Priority Action 2...             │
└─────────────────────────────────────┘
```

## 📂 Files

- `deep_dive.py` - English version
- `deep_dive_cn.py` - Chinese version (精读)

## Troubleshooting ❓

- **Plugin not working?**: Check if the filter/action is enabled in the model settings.
- **Debug Logs**: Enable `SHOW_STATUS` in Valves to see progress updates.
- **Error Messages**: If you see an error, please copy the full error message and report it.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
