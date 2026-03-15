# GitHub Copilot Official SDK Pipe

| 作者：[Fu-Jie](https://github.com/Fu-Jie) · v0.10.0 | [⭐ 点个 Star 支持项目](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-0%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%A7%A9&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

这是一个将 **GitHub Copilot SDK** 深度集成到 **OpenWebUI** 中的强大 Agent SDK 管道。它不仅实现了 SDK 的核心功能，还支持 **智能意图识别**、**自主网页搜索** 与 **自动上下文压缩**，并能够无缝读取 OpenWebUI 已有的配置进行智能注入，让 Agent 能够具备以下能力：

- **🧠 智能意图识别**：Agent 能自主分析用户任务的深层意图，决定最有效的处理路径。
- **🌐 自主网页搜索**：具备独立的网页搜索触发判断力，无需用户手动干预。
- **♾️ 自动压缩上下文**：支持 Infinite Session，自动对长对话进行上下文压缩与摘要，确保长期任务跟进。
- **🛠️ 全功能 Skill 体系**：完美支持本地自定义 Skill 目录，通过脚本与资源的结合实现真正的功能增强。
- **🧩 深度生态复用**：直接复用您在 OpenWebUI 中配置的各种 **工具 (Tools)**、**MCP**、**OpenAPI Server** 和 **技能 (Skills)**。

为您带来更强、更完整的交互体验。

> [!IMPORTANT]
> **核心伴侣组件**
> 如需启用文件处理与数据分析能力，请务必安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。
> [!TIP]
> **BYOK 模式无需订阅**
> 如果您使用自带的 API Key (BYOK 模式对接 OpenAI/Anthropic)，**您不需要 GitHub Copilot 官方订阅**。只有在访问 GitHub 官方模型时才需要订阅。

---

## ✨ v0.10.0 最新更新：原生提示词恢复、Live TODO 小组件与 SDK v0.1.30 完善

- **⌨️ 原生提示词恢复**：恢复了原生 Copilot CLI **原生计划模式 (Native Plan Mode)** 复杂任务编排能力，并集成了基于 SQLite 的原生会话与持久化管理，提升 Agent 的状态把控能力。
- **📋 Live TODO 小组件**：新增基于 `session.db` 实时任务状态的紧凑型嵌入式 TODO 小组件，任务进度常驻可见，无需在正文中重复显示全部待办列表。
- **🧩 OpenWebUI 工具调用修复**：修复自定义工具调用时上下文注入不完整的问题，完全对齐 OpenWebUI 0.8.x 所需的系统级上下文（`__request__`、`body`、`__metadata__` 等）。
- **🔒 SDK v0.1.30 与自适应工作流**：升级到 `github-copilot-sdk==0.1.30`，将规划与执行逻辑移至系统提示词，让 Agent 根据任务复杂度自主决策工作流。
- **🐛 意图与体验优化**：修复 `report_intent` 国际化问题，优化 TODO 小组件的视觉布局，减少冗余空白。
- **🧾 嵌入结果与文档更新**：改进 HTML/嵌入式工具结果处理，同步中英 README 与 docs 镜像页，确保发布状态一致。

---

## ✨ 核心能力 (Key Capabilities)

- **🔑 统一智能体验 (官方 + BYOK)**: 自由切换官方模型与自定义服务商（OpenAI, Anthropic, DeepSeek, xAI），支持 **BYOK (自带 Key)** 模式。
- **🛡️ 物理级工作区隔离**: 每个会话在独立的沙箱目录中运行。确保绝对的数据隐私，防止不同聊天间的文件污染，同时给予 Agent 完整的文件系统操作权限。
- **🔌 通用工具协议**:
  - **原生 MCP**: 高性能直连 Model Context Protocol 服务器。
  - **OpenAPI 桥接**: 将任何外部 REST API 一键转换为 Agent 可调用的工具。
  - **OpenWebUI 原生桥接**: 零配置接入现有的 OpenWebUI 工具及内置功能（网页搜索、记忆等）。
- **🧩 OpenWebUI Skills 桥接**: 将简单的 OpenWebUI Markdown 指令转化为包含脚本、模板 and 数据的强大 SDK 技能文件夹。
- **🧭 自适应规划与执行**: Agent 会根据任务复杂度、歧义程度和用户意图，自主决定先输出结构化方案，还是直接分析、实现并验证。
- **♾️ 无限会话管理**: 先进的上下文窗口管理，支持自动“压缩”（摘要提取 + TODO 列表持久化）。支持长达数周的项目跟踪而不会丢失核心上下文。
- **📊 交互式产物与发布**:
  - **实时 HTML/JS**: 瞬间渲染并交互 Agent 生成的应用程序、可视化看板或报告。
  - **持久化发布**: Agent 可将生成的产物（Excel, CSV, 文档）发布至 OpenWebUI 文件存储，并在聊天中提供永久下载链接。
- **🌊 极致交互体验**: 完整支持深度思考过程 (Thinking Process) 流式渲染、状态指示器以及长任务实时进度条。
- **🧠 深度数据库集成**: TODO 列表与会话元数据的实时持久化，确保任务执行状态在 UI 上清晰可见。

> [!TIP]
> **💡 增强渲染建议**
> 为了获得最精美的 **HTML Artifacts** 与 **RichUI** 效果，建议在对话中通过提供的 GitHub 链接直接命令 Agent 安装：
> “请安装此技能：<https://github.com/nicobailon/visual-explainer”。>
> 该技能专为生成高质量可视化组件而设计，能够与本 Pipe 完美协作。

---

## 🧩 配套 Files Filter（原始文件必备）

`GitHub Copilot SDK Files Filter` 是本 Pipe 的配套插件，用于阻止 OpenWebUI 默认 RAG 在 Pipe 接手前抢先处理上传文件。

- **作用**: 将上传文件移动到 `copilot_files`，让 Pipe 能直接读取原始二进制。
- **必要性**: 若未安装，文件可能被提前解析/向量化，Agent 拿到原始文件。
- **v0.1.3 重点**:
  - 修复 BYOK 模型 ID 识别（支持 `github_copilot_official_sdk_pipe.xxx` 前缀匹配）。
  - 新增双通道调试日志（`show_debug_log`）：后端 logger + 浏览器控制台。

---

## ⚙️ 核心配置 (Valves)

### 1. 管理员设置（全局默认）

管理员可在函数设置中为所有用户定义默认行为。

| Valve | 默认值 | 描述 |
| :--- | :--- | :--- |
| `GH_TOKEN` | `""` | 全局 GitHub Fine-grained Token，需要 `Copilot Requests` 权限。 |
| `COPILOTSDK_CONFIG_DIR` | `/app/backend/data/.copilot` | SDK 配置与会话状态的持久化目录。 |
| `ENABLE_OPENWEBUI_TOOLS` | `True` | 启用 OpenWebUI Tools 与 Built-in Tools。 |
| `ENABLE_OPENAPI_SERVER` | `True` | 启用 OpenAPI Tool Server 连接。 |
| `ENABLE_MCP_SERVER` | `True` | 启用 MCP Server 连接。 |
| `ENABLE_OPENWEBUI_SKILLS` | `True` | 启用 OpenWebUI Skills 到 SDK 技能目录的同步。 |
| `OPENWEBUI_SKILLS_SHARED_DIR` | `/app/backend/data/cache/copilot-openwebui-skills` | Skills 共享缓存目录。 |
| `DISABLED_SKILLS` | `""` | 逗号分隔的禁用技能名列表。 |
| `REASONING_EFFORT` | `medium` | 推理强度：`low`、`medium`、`high`、`xhigh`。 |
| `SHOW_THINKING` | `True` | 是否显示思考过程。 |
| `INFINITE_SESSION` | `True` | 是否启用无限会话与上下文压缩。 |
| `MAX_MULTIPLIER` | `1.0` | 允许的最大账单倍率。`0` 表示仅允许免费模型。 |
| `EXCLUDE_KEYWORDS` | `""` | 排除包含这些关键词的模型。 |
| `TIMEOUT` | `300` | 每个流式分片的超时时间（秒）。 |
| `BYOK_TYPE` | `openai` | BYOK 提供商类型：`openai` 或 `anthropic`。 |
| `BYOK_BASE_URL` | `""` | BYOK Base URL。 |
| `BYOK_MODELS` | `""` | BYOK 模型列表，留空则尝试从 API 获取。 |
| `CUSTOM_ENV_VARS` | `""` | 自定义环境变量（JSON 格式）。 |
| `DEBUG` | `False` | 启用浏览器控制台/技术调试日志。 |

### 2. 用户设置（个人覆盖）

普通用户可在个人资料或函数设置中覆盖以下选项。

| Valve | 描述 |
| :--- | :--- |
| `GH_TOKEN` | 使用个人 GitHub Token。 |
| `REASONING_EFFORT` | 个人推理强度偏好。 |
| `SHOW_THINKING` | 是否显示思考过程。 |
| `MAX_MULTIPLIER` | 个人最大账单倍率限制。 |
| `EXCLUDE_KEYWORDS` | 个人模型排除关键词。 |
| `ENABLE_OPENWEBUI_TOOLS` | 是否启用 OpenWebUI Tools 与 Built-in Tools。 |
| `ENABLE_OPENAPI_SERVER` | 是否启用 OpenAPI Tool Server。 |
| `ENABLE_MCP_SERVER` | 是否启用 MCP Server。 |
| `ENABLE_OPENWEBUI_SKILLS` | 是否加载你可读的 OpenWebUI Skills 到 SDK 技能目录。 |
| `DISABLED_SKILLS` | 逗号分隔的个人禁用技能列表。 |
| `BYOK_API_KEY` | 个人 BYOK API Key。 |
| `BYOK_TYPE` | 个人 BYOK 提供商类型覆盖。 |
| `BYOK_BASE_URL` | 个人 BYOK Base URL 覆盖。 |
| `BYOK_BEARER_TOKEN` | 个人 BYOK Bearer Token 覆盖。 |
| `BYOK_MODELS` | 个人 BYOK 模型列表覆盖。 |
| `BYOK_WIRE_API` | 个人 BYOK Wire API 覆盖。 |

---

## 🚀 安装与配置

### 1. 导入函数

1. 打开 OpenWebUI，进入 **Workspace** -> **Functions**。
2. 点击 **+**（Create Function），粘贴 `github_copilot_sdk.py` 内容。
3. 保存并确保已启用。

### 2. 获取 Token

1. 访问 [GitHub Token Settings](https://github.com/settings/tokens?type=beta)。
2. 创建 **Fine-grained token**，授予 **Account permissions** -> **Copilot Requests** 权限。
3. 将生成的 Token 填入 `GH_TOKEN`。

### 3. 认证要求（必填其一）

必须至少配置一种凭据来源：

- `GH_TOKEN`（GitHub Copilot 官方订阅路线），或
- `BYOK_API_KEY`（OpenAI / Anthropic 自带 Key 路线）。

如果两者都未配置，模型列表将不会显示。

---

## 🤝 支持 (Support)

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

---

## ⚠️ 故障排除 (Troubleshooting)

- **工具无法使用?** 请先确认 OpenWebUI Tools / MCP / OpenAPI Server 已在对应设置中启用。
- **文件找不到?** 确保已启用配套的 `Files Filter` 插件，否则 RAG 可能会提前消费原始文件。
- **BYOK 报错?** 确认 `BYOK_BASE_URL` 包含正确协议前缀（如 `https://`），且模型 ID 准确无误。
- **卡在 "Thinking..."?** 检查后端网络连接，或打开 `DEBUG` 查看更详细的 SDK 日志。

---

## Changelog

完整历史请查看 GitHub 项目主页：[OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
