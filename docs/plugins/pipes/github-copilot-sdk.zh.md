# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.5.1 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，深度集成了 **GitHub Copilot SDK**。它不仅支持 **GitHub Copilot 官方模型**（如 `gpt-5.2-codex`, `claude-sonnet-4.5`, `gemini-3-pro`, `gpt-5-mini`），还支持 **BYOK (自带 Key)** 模式对接自定义服务商（OpenAI, Anthropic），提供统一的 Agent 交互体验。

> [!IMPORTANT]
> [!TIP]
> **使用 BYOK 模式无需订阅**
> 如果您使用自己的 API Key (OpenAI, Anthropic) 运行 BYOK 模式，**则完全不需要** GitHub Copilot 订阅。
> 仅当您希望使用 GitHub 官方提供的模型时，才需要订阅。

## 🚀 最新特性 (v0.5.1) - 重大升级

- **🧠 智能 BYOK 检测**: 优化了 BYOK 与官方 Copilot 模型的识别逻辑，完美支持自定义模型（角色/提示词）及倍率检测（如 `(0x)`, `(1x)`）。
- **⚡ 性能飙升**: 引入 **工具缓存 (Tool Caching)** 机制，在请求间持久化工具定义，显著降低调用开销。
- **🧩 丰富工具集成**: 工具描述现包含来源分组（内置/用户/服务器）及 Docstring 元数据自动解析。
- **🛡️ 精确控制**: 完美兼容 OpenWebUI 全局函数过滤配置 (`function_name_filter_list`)，可精准控制暴露给 LLM 的函数。
- **🔑 用户级 BYOK**: 支持在用户层面配置自定义 API Key 对接 AI 供应商（OpenAI, Anthropic）。
- **📝 格式优化**: 系统提示词强制使用标准 Markdown 表格，彻底解决 HTML 表格渲染问题。

## ✨ 核心能力

- **🔑 灵活鉴权与 BYOK**: 支持 GitHub Copilot 订阅 (PAT) 或自带 Key (OpenAI/Anthropic)，完全掌控模型访问与计费。
- **🌉 强大的生态桥接**: 首个且唯一完美打通 **OpenWebUI Tools** 与 **GitHub Copilot SDK** 的插件。
- **🚀 官方原生产体验**: 基于官方 Python SDK 构建，提供最稳定、最纯正的 Copilot 交互体验。
- **🌊 深度推理展示**: 完整支持模型思考过程 (Thinking Process) 的流式渲染。
- **🖼️ 智能多模态**: 支持图像识别与附件上传，让 Copilot 拥有视觉能力。
- **🛠️ 极简部署流程**: 自动检测环境、自动下载 CLI、自动管理依赖，全自动化开箱即用。
- **🛡️ 纯净安全体系**: 支持标准 PAT 认证，确保数据安全。

## 安装与配置

### 1. 导入函数

1. 打开 OpenWebUI。
2. 进入 **Workspace** -> **Functions**。
3. 点击 **+** (创建函数)。
4. 将 `github_copilot_sdk_cn.py` 的内容完整粘贴进去。
5. 保存。

### 2. 配置 Valves (设置)

在函数列表中找到 "GitHub Copilot"，点击 **⚙️ (Valves)** 图标进行配置：

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| **GH_TOKEN** | **(必填)** GitHub 访问令牌 (PAT 或 OAuth Token)。用于聊天。 | - |
| **DEBUG** | 是否开启调试日志（输出到浏览器控制台）。 | `False` |
| **LOG_LEVEL** | Copilot CLI 日志级别: none, error, warning, info, debug, all。 | `error` |
| **SHOW_THINKING** | 是否显示模型推理/思考过程（需开启流式 + 模型支持）。 | `True` |
| **COPILOT_CLI_VERSION** | 指定安装/强制使用的 Copilot CLI 版本。 | `0.0.405` |
| **EXCLUDE_KEYWORDS** | 排除包含这些关键词的模型（逗号分隔）。 | - |
| **WORKSPACE_DIR** | 文件操作的受限工作区目录。 | - |
| **INFINITE_SESSION** | 启用无限会话（自动上下文压缩）。 | `True` |
| **COMPACTION_THRESHOLD** | 后台压缩阈值 (0.0-1.0)。 | `0.8` |
| **BUFFER_THRESHOLD** | 缓冲区耗尽阈值 (0.0-1.0)。 | `0.95` |
| **TIMEOUT** | 每个流式分块超时（秒）。 | `300` |
| **CUSTOM_ENV_VARS** | 自定义环境变量 (JSON 格式)。 | - |
| **REASONING_EFFORT** | 推理强度级别: low, medium, high. `xhigh` 仅部分模型支持。 | `medium` |
| **ENABLE_MCP_SERVER** | 启用直接 MCP 客户端连接 (建议)。 | `True` |
| **ENABLE_OPENWEBUI_TOOLS** | 启用 OpenWebUI 工具 (包括自定义和服务器工具)。 | `True` |
| **BYOK_ENABLED** | 启用 BYOK (自带 Key) 模式以使用自定义供应商。 | `False` |
| **BYOK_TYPE** | BYOK 供应商类型: `openai`, `azure`, `anthropic`。 | `openai` |
| **BYOK_BASE_URL** | BYOK 基础 URL (如 `https://api.openai.com/v1`)。 | - |
| **BYOK_API_KEY** | BYOK API Key (全局设置)。 | - |
| **BYOK_BEARER_TOKEN** | BYOK Bearer Token (全局，覆盖 API Key)。 | - |
| **BYOK_WIRE_API** | BYOK 通信协议: `completions`, `responses`。 | `completions` |

#### 用户 Valves（按用户覆盖）

以下设置可按用户单独配置（覆盖全局 Valves）：

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| **GH_TOKEN** | 个人 GitHub Token（覆盖全局设置）。 | - |
| **REASONING_EFFORT** | 推理强度级别（low/medium/high/xhigh）。 | - |
| **DEBUG** | 是否启用技术调试日志。 | `False` |
| **SHOW_THINKING** | 是否显示思考过程。 | `True` |
| **ENABLE_OPENWEBUI_TOOLS** | 启用 OpenWebUI 工具（覆盖全局设置）。 | `True` |
| **ENABLE_MCP_SERVER** | 启用动态 MCP 服务器加载（覆盖全局设置）。 | `True` |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) 点个 Star，这将是我持续改进的动力，感谢支持。

### 获取 Token

要使用 GitHub Copilot，您需要一个具有适当权限的 GitHub 个人访问令牌 (PAT)。

**获取步骤：**

1. 访问 [GitHub 令牌设置](https://github.com/settings/tokens?type=beta)。
2. 点击 **Generate new token (fine-grained)**。
3. **Repository access**: 选择 **Public Repositories** (最简单) 或 **All repositories**。
4. **Permissions**:
    - 如果您选择了 **All repositories**，则必须点击 **Account permissions**。
    - 找到 **Copilot Requests**，选择 **Access**。
5. 生成并复制令牌。

## 📋 依赖说明

该 Pipe 会自动尝试安装以下依赖（如果环境中缺失）：

- `github-copilot-sdk` (Python 包)
- `github-copilot-cli` (二进制文件，通过官方脚本安装)

## 故障排除 (Troubleshooting) ❓

- **图片及多模态使用说明**：
  - 确保 `MODEL_ID` 是支持多模态的模型。
- **看不到思考过程**：
  - 确认已开启**流式输出**，且所选模型支持推理输出。

## 更新日志

完整历史请查看 GitHub 项目： [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)
