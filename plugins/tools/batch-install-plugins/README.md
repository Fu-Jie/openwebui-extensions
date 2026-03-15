# Batch Install Plugins from GitHub

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.0.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

One-click batch install plugins from GitHub repositories to your OpenWebUI instance.

## Key Features

- **One-Click Install**: Install all plugins with a single command
- **Auto-Update**: Automatically updates previously installed plugins
- **Public GitHub Support**: Install plugins from any public GitHub repository
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
2. Install **Batch Install Plugins from GitHub** from the marketplace
3. Enable this tool for your model/chat
4. Ask the model to install plugins

## Interactive Installation Workflow

Each request handles one repository. To mix repositories, send another request after the previous installation completes.

## Quick Start: Install Popular Collections

Copy any of these prompts and paste them into your chat:

```
# Install all from my collection (default)
Install all plugins

# Add popular community tools
Install all plugins from iChristGit/OpenWebui-Tools

# Add utility-focused extensions
Install all plugins from Haervwe/open-webui-tools

# Add mixed community implementations
Install all plugins from Classic298/open-webui-plugins

# Add function-based plugins
Install all plugins from suurt8ll/open_webui_functions

# Add OpenRouter pipe integration
Install all plugins from rbb-dev/Open-WebUI-OpenRouter-pipe
```

Each line is a separate request. Already installed plugins are automatically updated.

## Usage Examples

For more advanced usage patterns:

```
# Filter by plugin type
"Install only tool plugins from iChristGit/OpenWebui-Tools"
"Install only action plugins from Classic298/open-webui-plugins"

# Exclude specific plugins
"Install all plugins from Haervwe/open-webui-tools, exclude_keywords=test,deprecated"

# Install from your own repository
"Install all plugins from your-username/my-plugin-collection"
```

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

## Confirmation Timeout

User confirmation dialogs have a default timeout of **2 minutes (120 seconds)**, allowing sufficient time for users to:
- Read and review the plugin list
- Make installation decisions
- Handle network delays

## Support

⭐ If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.
