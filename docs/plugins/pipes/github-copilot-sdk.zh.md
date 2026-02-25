# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 0.8.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，深度集成了 **GitHub Copilot SDK**。它不仅支持 **GitHub Copilot 官方模型**（如 `gpt-5.2-codex`, `claude-sonnet-4.5`, `gemini-3-pro`, `gpt-5-mini`），还支持 **BYOK (自带 Key)** 模式对接自定义服务商（OpenAI, Anthropic），并具备**严格的用户与会话级工作区隔离**能力，提供统一且安全的 Agent 交互体验。

> [!IMPORTANT]
> **核心伴侣组件**
> 如需启用文件处理与数据分析能力，请务必安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。

> [!TIP]
> **BYOK 模式无需订阅**
> 如果您使用自带的 API Key (BYOK 模式对接 OpenAI/Anthropic)，**您不需要 GitHub Copilot 官方订阅**。只有在访问 GitHub 官方模型时才需要订阅。

---

## ✨ 0.9.0 更新内容 (What's New)

- **🛠️ 工作区技能支持**: 在工作区的 `.copilot-skills/` 目录中使用 `@define_tool` 装饰器定义自定义工具。SDK 会自动发现并注册它们。详见 [工作区技能指南](#工作区技能) 部分。(v0.9.0)

---

## ✨ 0.8.0 更新内容 (存档)

- **🎛️ 条件工具过滤 (P1~P4)**: 四优先级工具权限体系。**默认全开**: 若未在 Chat UI (P4) 勾选任何工具，则默认启用所有工具；**白名单模式**: 一旦勾选特定工具，即刻进入严格过滤模式，且 MCP server 同步受控；管理员亦可通过 `config.enable` (P2) 全局禁用工具服务器。(v0.8.0)
- **🔧 文件发布全面修复**: 通过在回退路径直接调用 `Storage.upload_file()`，彻底修复了所有存储后端（local/S3/GCS/Azure）下的 `Error getting file content` 问题；同时上传时自动携带 `?process=false`，HTML 文件不再被 `ALLOWED_FILE_EXTENSIONS` 拦截。(v0.8.0)
- **🌐 HTML 直达链接**: 当 `publish_file_from_workspace` 发布的是 HTML 文件时，插件会额外提供可直接访问的 HTML 链接，便于在聊天中即时预览/打开。(v0.8.0)
- **🔒 文件链接格式严格约束**: 发布链接必须是以 `/api/v1/files/` 开头的相对路径（例如 `/api/v1/files/{id}/content/html`）。禁止使用 `api/...`，也禁止拼接任何域名。(v0.8.0)
- **🛠️ CLI 内置工具始终可用**: `available_tools` 统一设为 `None`，Copilot CLI 内置工具（如 `bash`、`create_file`）无论 MCP 配置如何都不会被静默屏蔽。(v0.8.0)
- **📌 发布工具始终注入**: 即使 `ENABLE_OPENWEBUI_TOOLS` 关闭，`publish_file_from_workspace` 工具也不再丢失。(v0.8.0)
- **⚠️ 代码解释器限制**: `code_interpreter` 工具运行在远程临时环境中。系统提示词现已包含警告，明确指出该工具无法访问本地文件或持久化更改。(v0.8.0)

### 🐞 v0.8.0 Bug 修复说明

- 修复了对象存储后端发布文件时出现的 `{"detail":"[ERROR: Error getting file content]"}`，回退路径从手动复制/写库改为 `Storage.upload_file()`。
- 修复了 HTML 产物被 `ALLOWED_FILE_EXTENSIONS` 拦截的问题，上传接口统一追加 `?process=false`。
- 修复了产物链接偶发被生成成 `api/...` 或带域名绝对 URL 的问题，现统一限制为 `/api/v1/files/...` 相对路径。
- 修复了在未配置/未加载任何 server 工具时（最终出现 `available_tools=[]`）Copilot CLI 内置工具被静默禁用的问题，现统一保持 `available_tools=None`。
- 修复了 `ENABLE_OPENWEBUI_TOOLS` 关闭时 `publish_file_from_workspace` 工具丢失的问题。

---

## ✨ 核心能力 (Key Capabilities)

- **🔑 灵活鉴权与 BYOK**: 支持 GitHub Copilot 官方订阅 (PAT) 或自带 Key (OpenAI/Anthropic)。
- **🔌 通用工具协议**: 原生支持 **MCP (Model Context Protocol)**、OpenAPI 以及 OpenWebUI 内置工具。
- **🛡️ 物理级工作区隔离**: 强制执行严格的用户特定沙箱，确保数据隐私与文件安全。
- **♾️ 无限会话管理**: 智能上下文窗口管理与自动压缩算法，支持无限时长的对话交互。
- **🧠 深度数据库集成**: 实时持久化 TOD·O 列表到 UI 进度条。
- **🌊 深度推理展示**: 完整支持模型思考过程 (Thinking Process) 的流式渲染。
- **🖼️ 智能多模态**: 完整支持图像识别与附件上传分析（绕过 RAG 直接访问原始二进制内容）。
- **📤 工作区产物工具 (`publish_file_from_workspace`)**: Agent 可生成文件（Excel、CSV、HTML 报告等）并直接提供**持久化下载链接**。管理员还可额外获得通过 `/content/html` 接口的**聊天内 HTML 预览**链接。
- **🖼️ 交互式伪影 (Artifacts)**: 自动渲染 Agent 生成的 HTML/JS 应用程序，直接在聊天界面交互。

---

## 🧩 配套 Files Filter（原始文件必备）

`GitHub Copilot SDK Files Filter` 是本 Pipe 的配套插件，用于阻止 OpenWebUI 默认 RAG 在 Pipe 接手前抢先处理上传文件。

- **作用**: 将上传文件移动到 `copilot_files`，让 Pipe 能直接读取原始二进制。
- **必要性**: 若未安装，文件可能被提前解析/向量化，Agent 难以拿到原始文件。
- **v0.1.3 重点**:
  - 修复 BYOK 模型 ID 识别（支持 `github_copilot_official_sdk_pipe.xxx` 前缀匹配）。
  - 新增双通道调试日志（`show_debug_log`）：后端 logger + 浏览器控制台。

---

## ⚙️ 核心配置参数 (Valves)

### 1. 管理员配置 (基础设置)

管理员可在函数设置中定义全局默认行为。

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `GH_TOKEN` | `""` | 全局 GitHub Token (需具备 'Copilot Requests' 权限)。 |
| `ENABLE_OPENWEBUI_TOOLS` | `True` | 启用 OpenWebUI 工具 (包括定义工具和内置工具)。 |
| `ENABLE_OPENAPI_SERVER` | `True` | 启用 OpenAPI 工具服务器连接。 |
| `ENABLE_MCP_SERVER` | `True` | 启用直接 MCP 客户端连接 (推荐)。 |
| `REASONING_EFFORT` | `medium` | 推理强度：low, medium, high。 |
| `SHOW_THINKING` | `True` | 显示模型推理/思考过程。 |
| `INFINITE_SESSION` | `True` | 启用无限会话 (自动上下文压缩)。 |
| `MAX_MULTIPLIER` | `1.0` | 最大允许的模型计费倍率 (0x 为仅限免费模型)。 |
| `EXCLUDE_KEYWORDS` | `""` | 排除包含这些关键字的模型 (逗号分隔)。 |
| `TIMEOUT` | `300` | 每个流数据块的超时时间 (秒)。 |
| `BYOK_TYPE` | `openai` | BYOK 服务商类型：`openai`, `anthropic`。 |
| `BYOK_BASE_URL` | `""` | BYOK 基础 URL (例如: <https://api.openai.com/v1>)。 |
| `BYOK_MODELS` | `""` | BYOK 模型列表 (逗号分隔)。留空则从 API 获取。 |
| `CUSTOM_ENV_VARS` | `""` | 自定义环境变量 (JSON 格式)。 |
| `DEBUG` | `False` | 开启此项以在前端控制台输出详细调试日志。 |

### 2. 用户配置 (个人覆盖)

普通用户可在各自的个人设置中根据需要覆盖以下参数。

| 参数 | 说明 |
| :--- | :--- |
| `GH_TOKEN` | 使用个人的 GitHub Token。 |
| `REASONING_EFFORT` | 个人偏好的推理强度。 |
| `SHOW_THINKING` | 显示模型推理/思考过程。 |
| `MAX_MULTIPLIER` | 最大允许的模型计费倍率覆盖。 |
| `EXCLUDE_KEYWORDS` | 排除包含这些关键字的模型。 |
| `BYOK_API_KEY` | 使用个人的 OpenAI/Anthropic API Key。 |

---

## 🎯 典型应用场景 (Use Cases)

- **📁 全自主仓库维护**: Agent 在隔离工作区内自动分析代码、运行测试并应用补丁。
- **📊 深度财务数据审计**: 直接通过 Python 加载 Excel/CSV 原始数据（绕过 RAG），生成图表并实时预览。
- **📝 长任务项目管理**: 自动拆解复杂任务并持久化 TOD·O 进度，跨会话跟踪执行状态。

---

## ⭐ 支持与交流 (Support)

如果这个插件对您有所帮助，请在 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 项目上点个 **Star** 💫，这是对我最大的鼓励。

---

## 🚀 安装与配置 (Installation)

### 1) 导入函数

1. 打开 OpenWebUI，前往 **工作区** -> **函数**。
2. 点击 **+** (创建函数)，完整粘贴 `github_copilot_sdk.py` 的内容。
3. 点击保存并确保已启用。

### 2) 获取 Token (Get Token)

1. 访问 [GitHub Token 设置](https://github.com/settings/tokens?type=beta)。
2. 创建 **Fine-grained token**，授予 **Account permissions** -> **Copilot Requests** 访问权限。
3. 将生成的 Token 填入插件的 `GH_TOKEN` 配置项中。

### 3) 认证配置要求（必填）

你必须至少配置以下一种凭据：

- `GH_TOKEN`（GitHub Copilot 官方订阅路径），或
- `BYOK_API_KEY`（OpenAI/Anthropic 自带 Key 路径）。

如果两者都未配置，模型列表将不会出现。

---

## 📋 常见问题与依赖 (Troubleshooting)

- **Agent 无法识别文件？**: 请确保已安装并启用了 Files Filter 插件，否则原始文件会被 RAG 干扰。
- **看不到 TODO 进度条？**: 进度条仅在 Agent 使用 `update_todo` 工具（通常是处理复杂任务）时出现。
- **依赖安装**: 本管道会自动管理 `github-copilot-sdk` (Python 包) 并优先直接使用内置的二进制 CLI，无需手动干预。

---

## 更新日志 (Changelog)

完整历史记录请见 GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
