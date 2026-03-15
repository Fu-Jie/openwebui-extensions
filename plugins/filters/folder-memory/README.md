# Folder Memory

| By [Fu-Jie](https://github.com/Fu-Jie) · v0.1.0 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-0%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%A7%A9&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

**Folder Memory** is an intelligent context filter plugin for OpenWebUI. It automatically extracts consistent "Project Rules" from ongoing conversations within a folder and injects them back into the folder's system prompt.

## 🔥 What's New in v0.1.0

- **Initial Release**: Automated "Project Rules" management for OpenWebUI folders.
- **Folder-Level Persistence**: Automatically updates folder system prompts with extracted rules.
- **Optimized Performance**: Runs asynchronously and supports `PRIORITY` configuration for seamless integration with other filters.

## ✨ Core Features

- **Automatic Extraction**: Analyzes chat history every N messages to extract project rules.
- **Non-destructive Injection**: Updates only the specific "Project Rules" block in the system prompt, preserving other instructions.
- **Async Processing**: Runs in the background without blocking the user's chat experience.
- **ORM Integration**: Directly updates folder data using OpenWebUI's internal models for reliability.

## Installation & Configuration

### 1) Installation

1. Copy `folder_memory.py` to your OpenWebUI `plugins/filters/` directory (or upload via Admin UI).
2. Enable the filter in your **Settings** -> **Filters**.
3. **Prerequisite**: Conversations must occur inside a folder (create a folder and start a chat within it).

### 2) Configuration (Valves)

| Valve | Default | Description |
| :--- | :--- | :--- |
| `PRIORITY` | `20` | Priority level for the filter operations. |
| `MESSAGE_TRIGGER_COUNT` | `10` | The number of messages required to trigger a rule analysis. |
| `MODEL_ID` | `""` | The model used to generate rules. If empty, uses the current chat model. |
| `RULES_BLOCK_TITLE` | `## 📂 Project Rules` | The title displayed above the injected rules block. |
| `SHOW_DEBUG_LOG` | `False` | Show detailed debug logs in the browser console. |
| `UPDATE_ROOT_FOLDER` | `False` | If enabled, finds and updates the root folder rules instead of the current subfolder. |

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## 🛠️ How It Works

![Folder Memory Demo](https://raw.githubusercontent.com/Fu-Jie/openwebui-extensions/main/plugins/filters/folder-memory/folder-memory-demo.png)

1. **Trigger**: When a conversation reaches `MESSAGE_TRIGGER_COUNT` (e.g., 10, 20 messages).
2. **Analysis**: The plugin sends the recent conversation + existing rules to the LLM.
3. **Synthesis**: The LLM merges new insights with old rules, removing obsolete ones.
4. **Update**: The new rule set replaces the `<!-- OWUI_PROJECT_RULES_START -->` block in the folder's system prompt.

## ⚠️ Notes

- This plugin modifies the `system_prompt` of your folders.
- It uses a specific marker `<!-- OWUI_PROJECT_RULES_START -->` to locate its content. Do not manually remove these markers if you want the plugin to continue managing that section.

## 🗺️ Roadmap

See [ROADMAP.md](./ROADMAP.md) for future plans, including "Project Knowledge" collection.

## Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
