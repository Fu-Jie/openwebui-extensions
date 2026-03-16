# Batch Install Plugins from GitHub

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.1.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

One-click batch install plugins from GitHub repositories to your OpenWebUI instance.

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

The plugin selection dialog has a default timeout of **15 minutes (900 seconds)**, allowing sufficient time for users to:
- Read and review the plugin list
- Check or uncheck the plugins they want
- Handle network delays

## Support

⭐ If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.
