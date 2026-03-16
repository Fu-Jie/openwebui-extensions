# GitHub Copilot SDK Files Filter

| By [Fu-Jie](https://github.com/Fu-Jie) · v0.1.3 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

This is a dedicated **companion filter plugin** designed specifically for the [GitHub Copilot SDK Pipe](https://openwebui.com/posts/github_copilot_official_sdk_pipe_ce96f7b4).

Its core mission is to **protect user-uploaded files from being "pre-processed" by the OpenWebUI core system, ensuring that the Copilot Agent receives the raw files for autonomous analysis.**

## Install with Batch Install Plugins

If you already use [Batch Install Plugins from GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins), you can install or update this plugin with:

```text
Install plugin from Fu-Jie/openwebui-extensions
```

When the selection dialog opens, search for this plugin, check it, and continue.

> [!IMPORTANT]
> If the official OpenWebUI Community version is already installed, remove it first. After that, Batch Install Plugins can keep this plugin updated in future runs.

## ✨ v0.1.3 Updates (What's New)

- **🔍 BYOK Model ID Matching Fixed**: Now correctly identifies models in `github_copilot_official_sdk_pipe.xxx` format via prefix matching, in addition to keyword fallback for backward compatibility. (v0.1.3)
- **🐛 Dual-channel Debug Log**: Added `show_debug_log` valve. When enabled, logs are written to both server-side logger and browser console (`console.group`). (v0.1.3)

## 🎯 Why is this needed?

In OpenWebUI's default workflow, when you upload a file (e.g., PDF, Excel, Python script), OpenWebUI automatically initiates a **RAG (Retrieval-Augmented Generation)** process: parsing the file, vectorizing it, extracting text, and injecting it into the prompt.

While useful for standard models, this is often disruptive for a **Copilot SDK Agent**:

1. **Agent Needs Raw Files**: The Agent may need to run Python code to read an Excel file or analyze a full directory structure, not chopped-up text fragments.
2. **Context Pollution**: Large amounts of text injected by RAG consume tokens and can confuse the Agent about "where the file is."
3. **Control & Performance**: Bypassing the extraction step speeds up the response and gives the Agent full autonomy over how to handle the data.

**This plugin acts as a "bodyguard" to solve these issues.**

## 🚀 How it Works

When you select a Copilot model (name containing `copilot_sdk`) in OpenWebUI and send a file:

1. **Intercept**: This plugin runs with high priority (Priority 0), before RAG and other filters.
2. **Relocate**: Detecting a Copilot model, it moves the `files` list from the request to a secure custom field `copilot_files`.
3. **Hide**: It clears the original `files` field.
4. **Pass**: The OpenWebUI core sees an empty `files` list and **does not trigger RAG**.
5. **Deliver**: The subsequent Copilot SDK Pipe plugin checks `copilot_files`, retrieves file information, and automatically copies them into the Agent's isolated workspace.

## 📦 Installation & Configuration

### 1. Installation

Import this plugin on the OpenWebUI **Functions** page.

### 2. Enable

Ensure this Filter is enabled globally or in chat settings.

### 3. Configuration (Valves)

Default settings work for most users:

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **priority** | Execution priority. **Must be lower than OpenWebUI RAG priority**. | `0` |
| **target_model_keyword** | Keyword to identify Copilot models for interception. | `copilot_sdk` |

## ⚠️ Important Notes

- **Must be used with Copilot SDK Pipe**: If you install this plugin without the main Pipe plugin, uploaded files will simply "disappear" (as no subsequent plugin will look for them).
- **Gemini Filter Compatibility**: Fully compatible with the Gemini Multimodal Filter. Just ensure priorities don't conflict.
