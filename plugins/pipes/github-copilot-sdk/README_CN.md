# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.6.1 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，深度集成了 **GitHub Copilot SDK**。它不仅支持 **GitHub Copilot 官方模型**（如 `gpt-5.2-codex`, `claude-sonnet-4.5`, `gemini-3-pro`, `gpt-5-mini`），还支持 **BYOK (自带 Key)** 模式对接自定义服务商（OpenAI, Anthropic），并具备**严格的用户与会话级工作区隔离**能力，提供统一且安全的 Agent 交互体验。

> [!IMPORTANT]
> **核心伴侣组件**
> 如需启用文件处理与数据分析能力，请务必安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。

> [!TIP]
> **BYOK 模式无需订阅**
> 如果您使用自带的 API Key (BYOK 模式对接 OpenAI/Anthropic)，**您不需要 GitHub Copilot 官方订阅**。只有在访问 GitHub 官方模型时才需要订阅。

---

## ✨ 0.6.1 更新内容 (What's New)

- **👥 多用户与会话管理**: 采用 `user_id/chat_id` 的物理隔离架构，确保资源独立与稳健管理。
- **🤖 赋予 Agent 文件自主权**: 自动将上传的文件同步至物理工作区，支持 Python 直接分析 Excel/CSV。
- **🔧 OpenAPI & 外部工具修复**: 完美支持通过 OpenAPI 服务器挂载的工具调用。
- **📊 计费与成本控制**: 增强的**计费倍率限制** (`MAX_MULTIPLIER`，例如设为 0 即仅限免费模型) 和**模型关键词过滤** (`EXCLUDE_KEYWORDS`)，实现更精准的成本管控。
- **🧠 数据库持久化 TODO**: 任务进度跨会话保存，Agent 拥有更持久的任务记忆。

---

## ✨ 核心能力 (Key Capabilities)

- **🔑 灵活鉴权与 BYOK**: 支持 GitHub Copilot 官方订阅 (PAT) 或自带 Key (OpenAI/Anthropic)。
- **🔌 通用工具协议**: 原生支持 **MCP (Model Context Protocol)**、OpenAPI 以及 OpenWebUI 内置工具。
- **🛡️ 物理级工作区隔离**: 强制执行严格的用户特定沙箱，确保数据隐私与文件安全。
- **♾️ 无限会话管理**: 智能上下文窗口管理与自动压缩算法，支持无限时长的对话交互。
- **🧠 深度数据库集成**: 实时持久化 TOD·O 列表到 UI 进度条。
- **🌊 深度推理展示**: 完整支持模型思考过程 (Thinking Process) 的流式渲染。
- **🖼️ 智能多模态**: 完整支持图像识别与附件上传分析。
- **⚡ 交互式伪影 (Artifacts)**: 自动渲染 Agent 生成的 HTML/JS 应用程序，直接在聊天界面交互。

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
| `BYOK_BASE_URL` | `""` | BYOK 基础 URL (例如: <https://api.openai.com/v1)。> |
| `BYOK_MODELS` | `""` | BYOK 模型列表 (逗号分隔)。留空则从 API 获取。 |
| `CUSTOM_ENV_VARS` | `""` | 自定义环境变量 (JSON 格式)。 |
| `DEBUG` | `False` | 开启此项以在前端控制台输出详细调试日志。 |

### 2. 用户配置 (个人覆盖)

普通用户可在各自的个人设置中根据需要覆盖以下参数。

| 参数 | 说明 |
| :--- | :--- |
| `GH_TOKEN` | 使用个人的 GitHub Token。 |
| `REASONING_EFFORT`| 个人偏好的推理强度。 |
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

如果这个插件对您有所帮助，请在 [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) 项目上点个 **Star** 💫，这是对我最大的鼓励。

---

## 🚀 安装与配置 (Installation)

### 1) 导入函数

1. 打开 OpenWebUI，前往 **工作区** -> **函数**。
2. 点击 **+** (创建函数)，完整粘贴 `github_copilot_sdk_cn.py` 的内容。
3. 点击保存并确保已启用。

### 2) 获取 Token (Get Token)

1. 访问 [GitHub Token 设置](https://github.com/settings/tokens?type=beta)。
2. 创建 **Fine-grained token**，授予 **Account permissions** -> **Copilot Requests** 访问权限。
3. 将生成的 Token 填入插件的 `GH_TOKEN` 配置项中。

### 3) 配套插件 (强烈推荐)

为了获得最佳的文件处理体验，请安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。

---

## 📋 常见问题与依赖 (Troubleshooting)

- **Agent 无法识别文件？**: 请确保已安装并启用了 Files Filter 插件，否则原始文件会被 RAG 干扰。
- **看不到 TODO 进度条？**: 进度条仅在 Agent 使用 `update_todo` 工具（通常是处理复杂任务）时出现。
- **依赖安装**: 本管道会自动尝试安装 `github-copilot-sdk` (Python 包) 和 `github-copilot-cli` (官方二进制)。

---

## 更新日志 (Changelog)

完整历史记录请见 GitHub: [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)
