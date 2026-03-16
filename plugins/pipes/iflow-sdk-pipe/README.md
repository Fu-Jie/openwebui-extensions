# iFlow Official SDK Pipe

This plugin integrates the [iFlow SDK](https://platform.iflow.cn/cli/sdk/sdk-python) into OpenWebUI as a `Pipe`.

## Install with Batch Install Plugins

If you already use [Batch Install Plugins from GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins), you can install or update this plugin with:

```text
Install plugin from Fu-Jie/openwebui-extensions
```

When the selection dialog opens, search for this plugin, check it, and continue.

> [!IMPORTANT]
> If the official OpenWebUI Community version is already installed, remove it first. After that, Batch Install Plugins can keep this plugin updated in future runs.

## Features

- **Standard iFlow Integration**: Connects to the iFlow CLI process via WebSocket (ACP).
- **Auto-Process Management**: Automatically starts the iFlow process if it's not running.
- **Streaming Support**: Direct streaming from iFlow to the chat interface.
- **Status Updates**: Real-time status updates in the UI (thinking, tool usage, etc.).
- **Tool Execution Visibility**: See when iFlow is calling and completing tools.

## Configuration

Set the following `Valves`:

- `IFLOW_PORT`: The port for the iFlow CLI process (default: `8090`).
- `IFLOW_URL`: The WebSocket URL (default: `ws://localhost:8090/acp`).
- `AUTO_START`: Automatically start the process (default: `True`).
- `TIMEOUT`: Request timeout in seconds.
- `LOG_LEVEL`: SDK logging level (DEBUG, INFO, etc.).

## Installation

This plugin requires both the **iFlow CLI** binary and the **iflow-cli-sdk** Python package.

### 1. Install iFlow CLI (System level)

Run the following command in your terminal (Linux/macOS):

```bash
bash -c "$(curl -fsSL https://platform.iflow.cn/cli/install.sh)"
```

### 2. Install Python SDK (OpenWebUI environment)

```bash
pip install iflow-cli-sdk
```
