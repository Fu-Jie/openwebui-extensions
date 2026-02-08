# GitHub Copilot SDK Pipe for OpenWebUI

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 0.5.1 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **License:** MIT

This is an advanced Pipe function for [OpenWebUI](https://github.com/open-webui/open-webui) that integrates the official [GitHub Copilot SDK](https://github.com/github/copilot-sdk). It enables you to use **GitHub Copilot models** (e.g., `gpt-5.2-codex`, `claude-sonnet-4.5`,`gemini-3-pro`, `gpt-5-mini`) **AND** your own models via **BYOK** (OpenAI, Anthropic) directly within OpenWebUI, providing a unified agentic experience.

> [!TIP]
> **No Subscription Required for BYOK**
> If you are using your own API keys (BYOK mode with OpenAI/Anthropic), **you do NOT need a GitHub Copilot subscription.**
> A subscription is only required to access GitHub's official models.

## 🚀 What's New (v0.5.1) - Major Upgrade

- **🧠 Smarter BYOK Detection**: Improved logic to correctly identify BYOK vs. Official Copilot models, supporting custom models (Characters/Prompts) and fixing multiplier detection (e.g., `(0x)`, `(1x)`).
- **⚡ Performance Boost**: Implemented **Tool Caching** to persist tool definitions across requests, significantly reducing overhead.
- **🧩 Enriched Tool Integration**: Tool descriptions now include source grouping (Built-in/User/Server) and automatic metadata extraction (Title/Description) from Python docstrings.
- **🛡️ Precise Control**: Added support for OpenWebUI's `function_name_filter_list` to filter MCP and OpenAPI functions.
- **🔑 User-Level BYOK**: Fully leverage Copilot SDK with your own Model Providers (OpenAI, Anthropic) with user-level API Key overrides.
- **📝 Better Formatting**: Enforced standard Markdown tables in system prompts to prevent rendering issues with HTML tables.

## ✨ Key Capabilities

- **🔑 Flexible Auth & BYOK**: Supports GitHub Copilot subscription (PAT) OR Bring Your Own Key (OpenAI/Anthropic), giving you total control over model access and billing.
- **🌉 The Ultimate Bridge**: The first and only plugin that creates a seamless bridge between **OpenWebUI Tools** and **GitHub Copilot SDK**.
- **🚀 Official & Native**: Built directly on the official Python SDK, providing the most stable and authentic Copilot experience.
- **🌊 Advanced Streaming (Thought Process)**: Supports full model reasoning/thinking display with typewriter effects.
- **🖼️ Intelligent Multimodal**: Full support for images and attachments, enabling Copilot to "see" your workspace.
- **🛠️ Effortless Setup**: Automatic CLI detection, version enforcement, and dependency management.
- **🛡️ Integrated Security**: Supports secure PAT authentication for standard and extended capabilities.

## Installation & Configuration

### 1) Import Function

1. Open OpenWebUI.
2. Go to **Workspace** -> **Functions**.
3. Click **+** (Create Function).
4. Paste the content of `github_copilot_sdk.py` (or `github_copilot_sdk_cn.py` for Chinese) completely.
5. Save.

### 2) Configure Valves (Settings)

Find "GitHub Copilot" in the function list and click the **⚙️ (Valves)** icon to configure:

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **GH_TOKEN** | **(Required)** GitHub Access Token (PAT or OAuth Token). Access to Chat. | - |
| **DEBUG** | Whether to enable debug logs (output to browser console). | `False` |
| **LOG_LEVEL** | Copilot CLI log level: none, error, warning, info, debug, all. | `error` |
| **SHOW_THINKING** | Show model reasoning/thinking process (requires streaming + model support). | `True` |
| **COPILOT_CLI_VERSION** | Specific Copilot CLI version to install/enforce. | `0.0.405` |
| **EXCLUDE_KEYWORDS** | Exclude models containing these keywords (comma separated). | - |
| **WORKSPACE_DIR** | Restricted workspace directory for file operations. | - |
| **INFINITE_SESSION** | Enable Infinite Sessions (automatic context compaction). | `True` |
| **COMPACTION_THRESHOLD** | Background compaction threshold (0.0-1.0). | `0.8` |
| **BUFFER_THRESHOLD** | Buffer exhaustion threshold (0.0-1.0). | `0.95` |
| **TIMEOUT** | Timeout for each stream chunk (seconds). | `300` |
| **CUSTOM_ENV_VARS** | Custom environment variables (JSON format). | - |
| **REASONING_EFFORT** | Reasoning effort level: low, medium, high. `xhigh` is supported for some models. | `medium` |

| **ENABLE_MCP_SERVER** | Enable Direct MCP Client connection (Recommended). | `True` |
| **ENABLE_OPENWEBUI_TOOLS** | Enable OpenWebUI Tools (includes defined and server tools). | `True` |
| **BYOK_ENABLED** | Enable BYOK (Bring Your Own Key) to use custom providers. | `False` |
| **BYOK_TYPE** | BYOK Provider Type: `openai`, `azure`, `anthropic`. | `openai` |
| **BYOK_BASE_URL** | BYOK Base URL (e.g., `https://api.openai.com/v1`). | - |
| **BYOK_API_KEY** | BYOK API Key (Global Setting). | - |
| **BYOK_BEARER_TOKEN** | BYOK Bearer Token (Global, overrides API Key). | - |
| **BYOK_WIRE_API** | BYOK Wire API: `completions`, `responses`. | `completions` |

#### User Valves (per-user overrides)

These optional settings can be set per user (overrides global Valves):

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **GH_TOKEN** | Personal GitHub Token (overrides global setting). | - |
| **REASONING_EFFORT** | Reasoning effort level (low/medium/high/xhigh). | - |
| **DEBUG** | Enable technical debug logs. | `False` |
| **SHOW_THINKING** | Show model reasoning/thinking process. | `True` |
| **ENABLE_OPENWEBUI_TOOLS** | Enable OpenWebUI Tools (overrides global). | `True` |
| **ENABLE_MCP_SERVER** | Enable MCP server loading (overrides global). | `True` |

| **BYOK_API_KEY** | BYOK API Key (User override). | - |

## ⭐ Support

If this plugin has been useful, a star on [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) is a big motivation for me. Thank you for the support.

### Get Token

To use GitHub Copilot, you need a GitHub Personal Access Token (PAT) with appropriate permissions.

**Steps to generate your token:**

1. Visit [GitHub Token Settings](https://github.com/settings/tokens?type=beta).
2. Click **Generate new token (fine-grained)**.
3. **Repository access**: Select **Public Repositories** (simplest) or **All repositories**.
4. **Permissions**:
    - If you chose **All repositories**, you must click **Account permissions**.
    - Find **Copilot Requests**, and select **Access**.
5. Generate and copy the Token.

## 📋 Dependencies

This Pipe will automatically attempt to install the following dependencies:

- `github-copilot-sdk` (Python package)
- `github-copilot-cli` (Binary file, installed via official script)

## Troubleshooting ❓

- **Images not recognized**:
  - Ensure `MODEL_ID` is a model that supports multimodal input.
- **Thinking not shown**:
  - Ensure **streaming is enabled** and the selected model supports reasoning output.

## Changelog

See the full history on GitHub: [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)
