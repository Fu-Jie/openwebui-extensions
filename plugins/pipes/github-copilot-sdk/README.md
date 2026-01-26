# GitHub Copilot SDK Pipe for OpenWebUI

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 0.2.3 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **License:** MIT

This is an advanced Pipe function for [OpenWebUI](https://github.com/open-webui/open-webui) that allows you to use GitHub Copilot models (such as `gpt-5`, `gpt-5-mini`, `claude-sonnet-4.5`) directly within OpenWebUI. It is built upon the official [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk), providing a native integration experience.

## 🚀 What's New (v0.2.3)

* **🧩 Per-user Overrides**: Added user-level overrides for `REASONING_EFFORT`, `CLI_PATH`, `DEBUG`, `SHOW_THINKING`, and `MODEL_ID`.
* **🧠 Thinking Output Reliability**: Thinking visibility now respects the user setting and is correctly passed into streaming.
* **📝 Formatting Enforcement**: Added automatic formatting hints to ensure outputs are well-structured (paragraphs, lists) and addressed "tight output" issues.

## ✨ Core Features

* **🚀 Official SDK Integration**: Built on the official SDK for stability and reliability.
* **🛠️ Custom Tools Support**: Example tools included (random number). Easy to extend with your own tools.
* **💬 Multi-turn Conversation**: Automatically concatenates history context so Copilot understands your previous messages.
* **🌊 Streaming Output**: Supports typewriter effect for fast responses.
* **🖼️ Multimodal Support**: Supports image uploads, automatically converting them to attachments for Copilot (requires model support).
* **🛠️ Zero-config Installation**: Automatically detects and downloads the GitHub Copilot CLI, ready to use out of the box.
* **🔑 Secure Authentication**: Supports Fine-grained Personal Access Tokens for minimized permissions.
* **🐛 Debug Mode**: Built-in detailed log output (browser console) for easy troubleshooting.
* **⚠️ Single Node Only**: Due to local session storage, this plugin currently supports single-node OpenWebUI deployment or multi-node with sticky sessions enabled.

## 📦 Installation & Usage

### 1. Import Function

1. Open OpenWebUI.
2. Go to **Workspace** -> **Functions**.
3. Click **+** (Create Function).
4. Paste the content of `github_copilot_sdk.py` (or `github_copilot_sdk_cn.py` for Chinese) completely.
5. Save.

### 2. Configure Valves (Settings)

Find "GitHub Copilot" in the function list and click the **⚙️ (Valves)** icon to configure:

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **GH_TOKEN** | **(Required)** Your GitHub Token. | - |
| **MODEL_ID** | The model name to use. | `gpt-5-mini` |
| **CLI_PATH** | Path to the Copilot CLI. Will download automatically if not found. | `/usr/local/bin/copilot` |
| **DEBUG** | Whether to enable debug logs (output to browser console). | `False` |
| **LOG_LEVEL** | Copilot CLI log level: none, error, warning, info, debug, all. | `error` |
| **SHOW_THINKING** | Show model reasoning/thinking process (requires streaming + model support). | `True` |
| **SHOW_WORKSPACE_INFO** | Show session workspace path and summary in debug mode. | `True` |
| **EXCLUDE_KEYWORDS** | Exclude models containing these keywords (comma separated). | - |
| **WORKSPACE_DIR** | Restricted workspace directory for file operations. | - |
| **INFINITE_SESSION** | Enable Infinite Sessions (automatic context compaction). | `True` |
| **COMPACTION_THRESHOLD** | Background compaction threshold (0.0-1.0). | `0.8` |
| **BUFFER_THRESHOLD** | Buffer exhaustion threshold (0.0-1.0). | `0.95` |
| **TIMEOUT** | Timeout for each stream chunk (seconds). | `300` |
| **CUSTOM_ENV_VARS** | Custom environment variables (JSON format). | - |
| **REASONING_EFFORT** | Reasoning effort level: low, medium, high. `xhigh` is supported for gpt-5.2-codex. | `medium` |
| **ENFORCE_FORMATTING** | Add formatting instructions to system prompt for better readability. | `True` |
| **ENABLE_TOOLS** | Enable custom tools (example: random number). | `False` |
| **AVAILABLE_TOOLS** | Available tools: 'all' or comma-separated list. | `all` |

#### User Valves (per-user overrides)

These optional settings can be set per user (overrides global Valves):

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **REASONING_EFFORT** | Reasoning effort level (low/medium/high/xhigh). | - |
| **CLI_PATH** | Custom path to Copilot CLI. | - |
| **DEBUG** | Enable technical debug logs. | `False` |
| **SHOW_THINKING** | Show model reasoning/thinking process (requires streaming + model support). | `True` |
| **MODEL_ID** | Custom model ID. | - |

### 3. Using Custom Tools (🆕 Optional)

This pipe includes **1 example tool** to demonstrate tool calling:

* **🎲 generate_random_number**: Generate random integers

**To enable:**

1. Set `ENABLE_TOOLS: true` in Valves
2. Try: "Give me a random number"

**📚 For detailed usage and creating your own tools, see [TOOLS_USAGE.md](TOOLS_USAGE.md)**

### 4. Get GH_TOKEN

For security, it is recommended to use a **Fine-grained Personal Access Token**:

1. Visit [GitHub Token Settings](https://github.com/settings/tokens?type=beta).
2. Click **Generate new token**.
3. **Repository access**: Select **Public repositories** (Required to access Copilot permissions).
4. **Permissions**:
    * Click **Account permissions**.
    * Find **Copilot Requests** (It defaults to **Read-only**, no selection needed).
5. Generate and copy the Token.

## 📋 Dependencies

This Pipe will automatically attempt to install the following dependencies:

* `github-copilot-sdk` (Python package)
* `github-copilot-cli` (Binary file, installed via official script)

## ⚠️ FAQ

* **Stuck on "Waiting..."**:
  * Check if `GH_TOKEN` is correct and has `Copilot Requests` permission.
* **Images not recognized**:
  * Ensure `MODEL_ID` is a model that supports multimodal input.
* **Thinking not shown**:
  * Ensure **streaming is enabled** and the selected model supports reasoning output.
* **CLI Installation Failed**:
  * Ensure the OpenWebUI container has internet access.
  * You can manually download the CLI and specify `CLI_PATH` in Valves.
