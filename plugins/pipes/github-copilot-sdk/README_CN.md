# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.2.3 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，允许你直接在 OpenWebUI 中使用 GitHub Copilot 模型（如 `gpt-5`, `gpt-5-mini`, `claude-sonnet-4.5`）。它基于官方 [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk) 构建，提供了原生级的集成体验。

## 🚀 最新特性 (v0.2.3)

* **🧩 用户级覆盖**：新增 `REASONING_EFFORT`、`CLI_PATH`、`DEBUG`、`SHOW_THINKING`、`MODEL_ID` 的用户级覆盖。
* **🧠 思考输出可靠性**：思考显示会遵循用户设置，并正确传递到流式输出中。
* **📝 格式化输出增强**：自动优化输出格式（短句、段落、列表），并解决了在某些界面下显示过于紧凑的问题。

## ✨ 核心特性

* **🚀 官方 SDK 集成**：基于官方 SDK，稳定可靠。
* **🛠️ 自定义工具支持**：内置示例工具（随机数）。易于扩展自定义工具。
* **💬 多轮对话支持**：自动拼接历史上下文，Copilot 能理解你的前文。
* **🌊 流式输出 (Streaming)**：支持打字机效果，响应迅速。
* **🖼️ 多模态支持**：支持上传图片，自动转换为附件发送给 Copilot（需模型支持）。
* **🛠️ 零配置安装**：自动检测并下载 GitHub Copilot CLI，开箱即用。
* **🔑 安全认证**：支持 Fine-grained Personal Access Tokens，权限最小化。
* **🐛 调试模式**：内置详细的日志输出（浏览器控制台），方便排查问题。
* **⚠️ 仅支持单节点**：由于会话状态存储在本地，本插件目前仅支持 OpenWebUI 单节点部署，或开启了会话粘性 (Sticky Session) 的多节点集群。

## 📦 安装与使用

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
| **GH_TOKEN** | **(必填)** 你的 GitHub Token。 | - |
| **MODEL_ID** | 使用的模型名称。 | `gpt-5-mini` |
| **CLI_PATH** | Copilot CLI 的路径。如果未找到会自动下载。 | `/usr/local/bin/copilot` |
| **DEBUG** | 是否开启调试日志（输出到浏览器控制台）。 | `False` |
| **LOG_LEVEL** | Copilot CLI 日志级别: none, error, warning, info, debug, all。 | `error` |
| **SHOW_THINKING** | 是否显示模型推理/思考过程（需开启流式 + 模型支持）。 | `True` |
| **SHOW_WORKSPACE_INFO** | 在调试模式下显示会话工作空间路径和摘要。 | `True` |
| **EXCLUDE_KEYWORDS** | 排除包含这些关键词的模型 (逗号分隔)。 | - |
| **WORKSPACE_DIR** | 文件操作的受限工作目录。 | - |
| **INFINITE_SESSION** | 启用无限会话 (自动上下文压缩)。 | `True` |
| **COMPACTION_THRESHOLD** | 后台压缩阈值 (0.0-1.0)。 | `0.8` |
| **BUFFER_THRESHOLD** | 缓冲耗尽阈值 (0.0-1.0)。 | `0.95` |
| **TIMEOUT** | 流式数据块超时时间 (秒)。 | `300` |
| **CUSTOM_ENV_VARS** | 自定义环境变量 (JSON 格式)。 | - |
| **ENABLE_TOOLS** | 启用自定义工具 (示例：随机数)。 | `False` |
| **AVAILABLE_TOOLS** | 可用工具: 'all' 或逗号分隔列表。 | `all` |
| **REASONING_EFFORT** | 推理强度级别：low, medium, high。`gpt-5.2-codex`额外支持`xhigh`。 | `medium` |
| **ENFORCE_FORMATTING** | 是否强制添加格式化指导，以提高输出可读性。 | `True` |

#### 用户 Valves（按用户覆盖）

以下设置可按用户单独配置（覆盖全局 Valves）：

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| **REASONING_EFFORT** | 推理强度级别（low/medium/high/xhigh）。 | - |
| **CLI_PATH** | 自定义 Copilot CLI 路径。 | - |
| **DEBUG** | 是否启用技术调试日志。 | `False` |
| **SHOW_THINKING** | 是否显示思考过程（需开启流式 + 模型支持）。 | `True` |
| **MODEL_ID** | 自定义模型 ID。 | - |

### 3. 使用自定义工具 (🆕 可选)

本 Pipe 内置了 **1 个示例工具**来展示工具调用功能：

* **🎲 generate_random_number**：生成随机整数

**启用方法：**

1. 在 Valves 中设置 `ENABLE_TOOLS: true`
2. 尝试问：“给我一个随机数”

**📚 详细使用说明和创建自定义工具，请参阅 [TOOLS_USAGE.md](TOOLS_USAGE.md)**

### 4. 获取 GH_TOKEN

为了安全起见，推荐使用 **Fine-grained Personal Access Token**：

1. 访问 [GitHub Token Settings](https://github.com/settings/tokens?type=beta)。
2. 点击 **Generate new token**。
3. **Repository access**: 选择 **Public repositories** (必须选择此项才能看到 Copilot 权限)。
4. **Permissions**:
    * 点击 **Account permissions**。
    * 找到 **Copilot Requests** (默认即为 **Read-only**，无需手动修改)。
5. 生成并复制 Token。

## 📋 依赖说明

该 Pipe 会自动尝试安装以下依赖（如果环境中缺失）：

* `github-copilot-sdk` (Python 包)
* `github-copilot-cli` (二进制文件，通过官方脚本安装)

## ⚠️ 常见问题

* **一直显示 "Waiting..."**：
  * 检查 `GH_TOKEN` 是否正确且拥有 `Copilot Requests` 权限。
* **图片无法识别**：
  * 确保 `MODEL_ID` 是支持多模态的模型。
* **CLI 安装失败**：
  * 确保 OpenWebUI 容器有外网访问权限。
  * 你可以手动下载 CLI 并挂载到容器中，然后在 Valves 中指定 `CLI_PATH`。
* **看不到思考过程**：
  * 确认已开启**流式输出**，且所选模型支持推理输出。
