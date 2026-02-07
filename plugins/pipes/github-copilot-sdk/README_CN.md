# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.3.0 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，允许你直接在 OpenWebUI 中使用 GitHub Copilot 模型（如 `gpt-5`, `gpt-5-mini`, `claude-sonnet-4.5`）。它基于官方 [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk) 构建，提供了原生级的集成体验。

## 🚀 最新特性 (v0.3.0) - “统一生态”的力量

* **🔌 零配置工具桥接 (Unified Tool Bridge)**: 自动将您现有的 OpenWebUI Functions (工具) 转换为 Copilot 兼容工具。**Copilot 现在可以无缝调用您手头所有的 WebUI 工具！**
* **🔗 动态 MCP 自动发现**: 直接联动 OpenWebUI **管理面板 -> 连接**。无需编写任何配置文件，即插即用，瞬间扩展 Copilot 能力边界。
* **⚡ 高性能异步引擎**: 异步 CLI 更新检查与高度优化的事件驱动流式处理，确保对话毫秒级响应。
* **🛡️ 卓越的兼容性**: 独创的动态 Pydantic 模型生成技术，确保复杂工具参数在 Copilot 端也能得到精准验证。

## ✨ 核心能力

* **🌉 强大的生态桥接**: 首个且唯一完美打通 **OpenWebUI Tools** 与 **GitHub Copilot SDK** 的插件。
* **🚀 官方原生产体验**: 基于官方 Python SDK 构建，提供最稳定、最纯正的 Copilot 交互体验。
* **🌊 深度推理展示**: 完整支持模型思考过程 (Thinking Process) 的流式渲染。
* **🖼️ 智能多模态**: 支持图像识别与附件上传，让 Copilot 拥有视觉能力。
* **🛠️ 极简部署流程**: 自动检测环境、自动下载 CLI、自动管理依赖，全自动化开箱即用。
* **🔑 安全认证体系**: 完美支持 OAuth 授权与 PAT 模式，兼顾便捷与安全性。

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
| **ENFORCE_FORMATTING** | 在系统提示词中添加格式化指导。 | `True` |
| **ENABLE_MCP_SERVER** | 启用直接 MCP 客户端连接 (建议)。 | `True` |
| **ENABLE_OPENWEBUI_TOOLS** | 启用 OpenWebUI 工具 (包括自定义和服务器工具)。 | `True` |

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
| **ENFORCE_FORMATTING** | 强制启用格式化指导（覆盖全局设置）。 | `True` |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) 点个 Star，这将是我持续改进的动力，感谢支持。

### 获取 Token

要使用 GitHub Copilot，您需要一个具有适当权限的 GitHub 个人访问令牌 (PAT)。

**获取步骤：**

1. 访问 [GitHub 令牌设置](https://github.com/settings/tokens?type=beta)。
2. 点击 **Generate new token (fine-grained)**。
3. **Repository access**: 选择 **Public Repositories** (最简单) 或 **All repositories**。
4. **Permissions**:
    * 如果您选择了 **All repositories**，则必须点击 **Account permissions**。
    * 找到 **Copilot Requests**，选择 **Access**。
5. 生成并复制令牌。

## 📋 依赖说明

该 Pipe 会自动尝试安装以下依赖（如果环境中缺失）：

* `github-copilot-sdk` (Python 包)
* `github-copilot-cli` (二进制文件，通过官方脚本安装)

## 故障排除 (Troubleshooting) ❓

* **图片及多模态使用说明**：
  * 确保 `MODEL_ID` 是支持多模态的模型。
* **看不到思考过程**：
  * 确认已开启**流式输出**，且所选模型支持推理输出。

## 更新日志

完整历史请查看 GitHub 项目： [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)
