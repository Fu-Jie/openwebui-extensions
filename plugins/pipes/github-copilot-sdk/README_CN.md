# GitHub Copilot Official SDK Pipe

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 0.9.1 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

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

## ✨ 0.9.1 最新更新：自主网页搜索与可靠性修复

- **🌐 强化自主网页搜索**：`web_search` 工具现已强制对 Agent 开启（绕过 UI 网页搜索开关），充分利用 Copilot 自身具备的搜索判断能力。
- **🛠️ 术语一致性优化**：全语种同步将“助手”更改为 **"Agent"**，并将“优化会话”统一为 **"压缩上下文"**，更准确地描述 Infinite Session 的技术本质。
- **🌐 语言一致性**：内置指令确保 Agent 输出语言与用户输入严格对齐，提供无缝的国际化交互体验。
- **🐛 修复 MCP 工具过滤逻辑**：解决了在管理员后端配置 `function_name_filter_list`（或在聊天界面勾选特定工具）时，因 ID 前缀（`server:mcp:`）识别逻辑错误导致工具意外失效的问题。
- **🔍 提升过滤稳定性**：修复了工具 ID 归一化逻辑，确保点选的工具白名单在 SDK 会话中精确生效。

---

## ✨ 核心能力 (Key Capabilities)

- **🔑 统一智能体验 (官方 + BYOK)**: 自由切换官方模型与自定义服务商（OpenAI, Anthropic, DeepSeek, xAI），支持 **BYOK (自带 Key)** 模式。
- **🛡️ 物理级工作区隔离**: 每个会话在独立的沙箱目录中运行。确保绝对的数据隐私，防止不同聊天间的文件污染，同时给予 Agent 完整的文件系统操作权限。
- **🔌 通用工具协议**:
  - **原生 MCP**: 高性能直连 Model Context Protocol 服务器。
  - **OpenAPI 桥接**: 将任何外部 REST API 一键转换为 Agent 可调用的工具。
  - **OpenWebUI 原生桥接**: 零配置接入现有的 OpenWebUI 工具及内置功能（网页搜索、记忆等）。
- **🧩 OpenWebUI Skills 桥接**: 将简单的 OpenWebUI Markdown 指令转化为包含脚本、模板 and 数据的强大 SDK 技能文件夹。
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

## 🚀 快速开始 (Quick Start)

1. **安装本插件**: 在 OpenWebUI 管道管理界面添加并启用。
2. **安装 [Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)** (必须): 以获得文件处理能力。
3. **配置凭据**:
   - **官方模式**: 默认即可。确保环境中安装了 `github-copilot-sdk`。
   - **BYOK 模式**: 填入 OpenAI/Anthropic/DeepSeek 的 Base URL 与 Key。
4. **选择模型**: 在聊天界面选择 `GitHub Copilot Official SDK Pipe` 系列模型。
5. **开始对话**: 直接上传文件或发送复杂指令。

---

## ⚙️ 配置参数 (Configuration Valves)

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `github_token` | - | GitHub Copilot 官方 Token (如果您有官方订阅且不方便本地登录时填入)。 |
| `llm_base_url` | - | BYOK 模式的基础 URL。填入后将绕过 GitHub 官方服务。 |
| `llm_api_key` | - | BYOK 模式的 API 密钥。 |
| `llm_model_id` | `gpt-4o` | 使用的模型 ID (官方、BYOK 均适用)。 |
| `workspace_root` | `./copilot_workspaces` | 所有会话沙盒的根目录。 |
| `skills_directory` | `./copilot_skills` | 自定义 SDK 技能文件夹所在的目录。 |
| `show_status` | `True` | 是否在 UI 显示 Agent 的实时运行状态和思考过程。 |
| `enable_infinite_session` | `True` | 是否开启自动上下文压缩和 TODO 列表持久化。 |
| `enable_html_artifacts` | `True` | 是否允许 Agent 生成并实时预览 HTML 应用。 |
| `enable_rich_ui` | `True` | 是否启用进度条和增强型工具调用面板。 |

---

## 🤝 支持 (Support)

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

---

## ⚠️ 故障排除 (Troubleshooting)

- **工具无法使用?** 请检查是否安装了 `github-copilot-sdk`。
- **文件找不到?** 确保已启用配套的 `Files Filter` 插件。
- **BYOK 报错?** 确认 `llm_base_url` 包含协议前缀（如 `https://`）且模型 ID 准确无误。
- **卡在 "Thinking..."?** 检查后端网络连接，流式传输可能受某些代理拦截。
