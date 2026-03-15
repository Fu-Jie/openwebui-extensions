# Batch Install Plugins from GitHub

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.0.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

One-click batch install plugins from GitHub repositories to your OpenWebUI instance.

## Key Features

- **One-Click Install**: Install all plugins with a single command
- **Auto-Update**: Automatically updates previously installed plugins
- **GitHub Support**: Install plugins from any GitHub repository
- **Multi-Type Support**: Supports Pipe, Action, Filter, and Tool plugins
- **Confirmation**: Shows plugin list before installing, allows selective installation
- **i18n**: Supports 11 languages

## Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│  Discover Plugins from GitHub       │
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
│  Show Confirmation Dialog           │
│  (list plugins + exclude hint)      │
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
2. Install **Batch Install Plugins from GitHub** from the official marketplace
3. Enable this tool for your model/chat
4. Ask the model to install plugins

## Usage Examples

```
"Install all plugins"
"Install all plugins from github.com/username/repo"
"Install only pipe plugins"
"Install action and filter plugins"
"Install all plugins, exclude_keywords=copilot"
```

## Popular Plugin Repositories

Here are some popular repositories with many plugins you can install:

### Community Collections

```
# Install all plugins from iChristGit's collection
"Install all plugins from iChristGit/OpenWebui-Tools"

# Install all tools from Haervwe's tools collection
"Install all plugins from Haervwe/open-webui-tools"

# Install all plugins from Classic298's repository
"Install all plugins from Classic298/open-webui-plugins"

# Install all functions from suurt8ll's collection
"Install all plugins from suurt8ll/open_webui_functions"

# Install only specific types (e.g., only tools)
"Install only tool plugins from iChristGit/OpenWebui-Tools"

# Exclude certain keywords while installing
"Install all plugins from Haervwe/open-webui-tools, exclude_keywords=test,deprecated"
```

### Supported Repositories

- `Fu-Jie/openwebui-extensions` - Default, official plugin collection
- `iChristGit/OpenWebui-Tools` - Comprehensive tool and plugin collection
- `Haervwe/open-webui-tools` - Specialized tools and utilities
- `Classic298/open-webui-plugins` - Various plugin implementations
- `suurt8ll/open_webui_functions` - Function-based plugins

## Default Repository

When no repository is specified, defaults to `Fu-Jie/openwebui-extensions`.

## Plugin Detection Rules

### Fu-Jie/openwebui-extensions (Strict)

For the default repository, plugins must have:
1. A `.py` file containing `class Tools:`, `class Filter:`, `class Pipe:`, or `class Action:`
2. A docstring with `title:`, `description:`, and **`openwebui_id:`** fields
3. Filename must not end with `_cn`

### Other GitHub Repositories

For other repositories:
1. A `.py` file containing `class Tools:`, `class Filter:`, `class Pipe:`, or `class Action:`
2. A docstring with `title:` and `description:` fields

## Configuration (Valves)

| Parameter | Default | Description |
| --- | --- | --- |
| `SKIP_KEYWORDS` | `test,verify,example,template,mock` | Comma-separated keywords to skip |
| `TIMEOUT` | `20` | Request timeout in seconds |

## Confirmation Timeout

User confirmation dialogs have a default timeout of **2 minutes (120 seconds)**, allowing sufficient time for users to:
- Read and review the plugin list
- Make installation decisions
- Handle network delays

## Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.
