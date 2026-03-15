# 🎉 Introducing Batch Install Plugins v1.0.0

## Headline
**One-Click Batch Installation of OpenWebUI Plugins - Solving the Plugin Setup Headache**

## Introduction
Installing plugins in OpenWebUI used to be tedious: searching for plugins, downloading them one by one, and hoping everything works in your environment. Today, we're excited to announce **Batch Install Plugins from GitHub** v1.0.0 — a powerful new tool that transforms plugin installation from a chore into a single command.

## Key Highlights

### 🚀 One-Click Bulk Installation
- Install multiple plugins from any public GitHub repository with a single command
- Automatically discovers plugins and validates them
- Updates previously installed plugins seamlessly

### ✅ Smart Safety Features
- Shows a confirmation dialog with the plugin list before installation
- Users can review and approve before proceeding
- Automatically excludes the tool itself from installation

### 🌍 Multi-Repository Support
Install plugins from **any public GitHub repository**, including your own community collections:
- Use one request per repository, then call the tool again to combine multiple sources
- **Default**: Fu-Jie/openwebui-extensions (my personal collection)
- Works with public repositories in `owner/repo` format
- Mix and match plugins: install from my collection first, then add community collections in subsequent calls

### 🔧 Container-Friendly
- Automatically handles port mapping issues in containerized deployments
- Smart fallback: retries with localhost:8080 if the primary connection fails
- Rich debugging logs for troubleshooting

### 🌐 Global Support
- Complete i18n support for 11 languages
- All error messages localized and user-friendly
- Works seamlessly across different deployment scenarios

## How It Works: Interactive Installation Workflow

Each request handles one repository. To combine multiple repositories, send another request after the previous installation completes.

1. **Start with My Collection**
   ```
   "Install all plugins from Fu-Jie/openwebui-extensions"
   ```
   Review the confirmation dialog, approve, and the plugins are installed.

2. **Add a Community Collection**
   ```
   "Install all plugins from iChristGit/OpenWebui-Tools"
   ```
   Add more plugins from a different repository. Already installed plugins are updated seamlessly.

3. **Install a Specific Type**
   ```
   "Install only pipe plugins from Haervwe/open-webui-tools"
   ```
   Pick specific plugin types from another repository, or exclude certain keywords.

4. **Use Your Own Public Repository**
   ```
   "Install all plugins from your-username/your-collection"
   ```
   Works with any public GitHub repository in `owner/repo` format.

## Popular Community Collections

Ready-to-install from these community favorites:

#### **iChristGit/OpenWebui-Tools**
Comprehensive tools and plugins for various use cases.

#### **Haervwe/open-webui-tools**
Specialized utilities for extending OpenWebUI functionality.

#### **Classic298/open-webui-plugins**
Diverse plugin implementations for different scenarios.

#### **suurt8ll/open_webui_functions**
Function-based plugins for custom integrations.

#### **rbb-dev/Open-WebUI-OpenRouter-pipe**
OpenRouter API pipe integration for advanced model access.

## Usage Examples

Each line below is a separate request:

```
# Start with my collection
"Install all plugins"

# Add community plugins in a new request
"Install all plugins from iChristGit/OpenWebui-Tools"

# Add only one plugin type from another repository
"Install only tool plugins from Haervwe/open-webui-tools"

# Continue building your setup
"Install only action plugins from Classic298/open-webui-plugins"

# Filter out unwanted plugins
"Install all plugins from Haervwe/open-webui-tools, exclude_keywords=test,deprecated"

# Install from your own public repository
"Install all plugins from your-username/my-plugin-collection"
```

## Technical Excellence

- **Async Architecture**: Non-blocking I/O for better performance
- **httpx Integration**: Modern async HTTP client with timeout protection
- **Comprehensive Tests**: 8 regression tests with 100% pass rate
- **Full Event Support**: Proper OpenWebUI event injection with fallback handling

## Installation

1. Open OpenWebUI → Workspace > Tools
2. Install **Batch Install Plugins from GitHub** from the marketplace
3. Enable it for your model/chat
4. Start using it with commands like "Install all plugins"

## Links

- **GitHub Repository**: https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins
- **Release Notes**: https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/tools/batch-install-plugins/v1.0.0.md

## Community Love

If this tool has been helpful to you, please give us a ⭐ on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) — it truly motivates us to keep improving!

**Thank you for supporting the OpenWebUI community! 🙏**
