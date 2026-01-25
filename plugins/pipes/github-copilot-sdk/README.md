# GitHub Copilot SDK Pipe for OpenWebUI

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 0.1.1 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **License:** MIT

This is an advanced Pipe function for [OpenWebUI](https://github.com/open-webui/open-webui) that allows you to use GitHub Copilot models (such as `gpt-5`, `gpt-5-mini`, `claude-sonnet-4.5`) directly within OpenWebUI. It is built upon the official [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk), providing a native integration experience.

## 🚀 What's New (v0.1.1)

* **♾️ Infinite Sessions**: Automatic context compaction for long-running conversations. No more context limit errors!
* **🧠 Thinking Process**: Real-time display of model reasoning/thinking process (for supported models).
* **📂 Workspace Control**: Restricted workspace directory for secure file operations.
* **🔍 Model Filtering**: Exclude specific models using keywords (e.g., `codex`, `haiku`).
* **💾 Session Persistence**: Improved session resume logic using OpenWebUI chat ID mapping.

## ✨ Core Features

* **🚀 Official SDK Integration**: Built on the official SDK for stability and reliability.
* **💬 Multi-turn Conversation**: Automatically concatenates history context so Copilot understands your previous messages.
* **🌊 Streaming Output**: Supports typewriter effect for fast responses.
* **🖼️ Multimodal Support**: Supports image uploads, automatically converting them to attachments for Copilot (requires model support).
* **🛠️ Zero-config Installation**: Automatically detects and downloads the GitHub Copilot CLI, ready to use out of the box.
* **🔑 Secure Authentication**: Supports Fine-grained Personal Access Tokens for minimized permissions.
* **🐛 Debug Mode**: Built-in detailed log output for easy connection troubleshooting.

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
| **MODEL_ID** | The model name to use. Recommended `gpt-5-mini` or `gpt-5`. | `gpt-5-mini` |
| **CLI_PATH** | Path to the Copilot CLI. Will download automatically if not found. | `/usr/local/bin/copilot` |
| **DEBUG** | Whether to enable debug logs (output to chat). | `True` |
| **SHOW_THINKING** | Show model reasoning/thinking process. | `True` |
| **EXCLUDE_KEYWORDS** | Exclude models containing these keywords (comma separated). | - |
| **WORKSPACE_DIR** | Restricted workspace directory for file operations. | - |
| **INFINITE_SESSION** | Enable Infinite Sessions (automatic context compaction). | `True` |
| **COMPACTION_THRESHOLD** | Background compaction threshold (0.0-1.0). | `0.8` |
| **BUFFER_THRESHOLD** | Buffer exhaustion threshold (0.0-1.0). | `0.95` |
| **TIMEOUT** | Timeout for each stream chunk (seconds). | `300` |

### 3. Get GH_TOKEN

For security, it is recommended to use a **Fine-grained Personal Access Token**:

1. Visit [GitHub Token Settings](https://github.com/settings/tokens?type=beta).
2. Click **Generate new token**.
3. **Repository access**: Select `All repositories` or `Public Repositories`.
4. **Permissions**:
    * Click **Account permissions**.
    * Find **Copilot Requests**, select **Read and write** (or Access).
5. Generate and copy the Token.

## 📋 Dependencies

This Pipe will automatically attempt to install the following dependencies:

* `github-copilot-sdk` (Python package)
* `github-copilot-cli` (Binary file, installed via official script)

## ⚠️ FAQ

* **Stuck on "Waiting..."**:
  * Check if `GH_TOKEN` is correct and has `Copilot Requests` permission.
  * Try changing `MODEL_ID` to `gpt-4o` or `copilot-chat`.
* **Images not recognized**:
  * Ensure `MODEL_ID` is a model that supports multimodal input.
* **CLI Installation Failed**:
  * Ensure the OpenWebUI container has internet access.
  * You can manually download the CLI and specify `CLI_PATH` in Valves.
