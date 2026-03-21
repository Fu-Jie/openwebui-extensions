# Batch Install Plugins from GitHub

| By [Fu-Jie](https://github.com/Fu-Jie) · v1.1.0 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

One-click batch install plugins from GitHub repositories to your OpenWebUI instance.

## Install with Batch Install Plugins

After you install [Batch Install Plugins from GitHub](https://openwebui.com/t/fujie/batch_install_plugins) once, you can also use it to reinstall or update itself with:

```text
Install plugin from Fu-Jie/openwebui-extensions
```

When the selection dialog opens, search for this plugin, check it, and continue.

> [!IMPORTANT]
> If the official OpenWebUI Community version is already installed, remove it first. After that, Batch Install Plugins can keep this plugin updated in future runs.

> [!TIP]
> **💡 Looking to batch install or manage Workspace Skills?**
> This plugin specializes in installing global function-based plugins (Pipe, Filter, Tool, Action). If you need to manage your AI assistant's dedicated Skills, use our companion tool [OpenWebUI Skills Manager](https://openwebui.com/t/fujie/openwebui_skills_manager), which provides full CRUD capabilities, batch discovery, and interactive selection dialogs.

## Key Features

- **One-Click Install**: Install all plugins with a single command
- **Auto-Update**: Automatically updates previously installed plugins
- **Public GitHub Support**: Install plugins from one or many public GitHub repositories
- **Multi-Type Support**: Supports Pipe, Action, Filter, and Tool plugins
- **Multi-Repository Picker**: Combine multiple repositories in one request and review them in a single grouped dialog
- **Interactive Selection Dialog**: Filter by repository and type, search by keyword, review plugin descriptions, then install only the checked subset
- **i18n**: Supports 11 languages

## Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│  Discover Plugins from GitHub Repos │
│  (fetch file tree + parse .py)     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Filter by Type & Keywords         │
│  (tool/filter/pipe/action)         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Show Selection Dialog              │
│  (repo groups + filters + search)   │
└─────────────────────────────────────┘
    │
    ├── [Cancel] → End
    │
    ▼
┌─────────────────────────────────────┐
│  Install to OpenWebUI               │
│  (update or create each plugin)    │
└─────────────────────────────────────┘
    │
    ▼
   Done
```

## How to Use

1. Open OpenWebUI and go to **Workspace > Tools**
2. Install **Batch Install Plugins from GitHub** from the marketplace
3. Enable this tool for your model/chat
4. Ask the model to install plugins

## Interactive Installation Workflow

The `repo` parameter accepts one or more `owner/repo` values separated by commas, semicolons, or new lines.

After plugin discovery and filtering, OpenWebUI opens a browser dialog built with the `execute` event. The dialog merges results from every requested repository, groups them by repository, supports repository tags, type filters, and keyword search, and lets you check exactly which plugins to install before the API calls start.

If one user request mentions multiple repositories, keep them in the same request so the model can pass them into a single tool call.

## Quick Start: Install Popular Collections

Paste this prompt into your chat:

```
Install all plugins from Fu-Jie/openwebui-extensions, iChristGit/OpenWebui-Tools, Haervwe/open-webui-tools, Classic298/open-webui-plugins, suurt8ll/open_webui_functions, rbb-dev/Open-WebUI-OpenRouter-pipe
```

Once the dialog opens, use the repository tags, type filters, and keyword search to narrow the list before installing. Already installed plugins are automatically updated.

You can replace that repository list with your own collections whenever needed.

## Default Repository

When no repository is specified, the tool uses `Fu-Jie/openwebui-extensions` (my personal collection).

## Plugin Detection Rules

### Fu-Jie/openwebui-extensions (Strict)

For the default repository, the tool applies stricter filtering:
1. A `.py` file containing `class Tools:`, `class Filter:`, `class Pipe:`, or `class Action:`
2. A docstring with `title:`, `description:`, and **`openwebui_id:`** metadata
3. Filename must not end with `_cn`

### Other Public GitHub Repositories

For other repositories:
1. A `.py` file containing `class Tools:`, `class Filter:`, `class Pipe:`, or `class Action:`
2. A docstring with `title:` and `description:` fields

## Configuration (Valves)

| Parameter | Default | Description |
| --- | --- | --- |
| `SKIP_KEYWORDS` | `test,verify,example,template,mock` | Comma-separated keywords to skip |
| `TIMEOUT` | `20` | Request timeout in seconds |

## Selection Dialog Timeout

The plugin selection dialog has a default timeout of **2 minutes (120 seconds)**, allowing sufficient time for users to:
- Read and review the plugin list
- Check or uncheck the plugins they want
- Handle network delays

## Support

⭐ If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.
