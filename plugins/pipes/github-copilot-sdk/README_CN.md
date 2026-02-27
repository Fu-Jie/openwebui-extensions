# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 0.9.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，深度集成了 **GitHub Copilot SDK**。它不仅支持 **GitHub Copilot 官方模型**（如 `gpt-5.2-codex`, `claude-sonnet-4.5`, `gemini-3-pro`, `gpt-5-mini`），还支持 **BYOK (自带 Key)** 模式对接自定义服务商（OpenAI, Anthropic），并具备**严格的用户与会话级工作区隔离**能力，提供统一且安全的 Agent 交互体验。

> [!IMPORTANT]
> **核心伴侣组件**
> 如需启用文件处理与数据分析能力，请务必安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。
> [!TIP]
> **BYOK 模式无需订阅**
> 如果您使用自带的 API Key (BYOK 模式对接 OpenAI/Anthropic)，**您不需要 GitHub Copilot 官方订阅**。只有在访问 GitHub 官方模型时才需要订阅。

---

## ✨ 0.9.0 核心更新：技能革命与稳定性加固

- **🧩 Copilot SDK Skills 原生支持**: 技能可作为一等上下文能力被加载和使用。
- **🔄 OpenWebUI Skills 桥接**: 实现 OpenWebUI **工作区 > Skills** 与 SDK 技能目录的深度双向同步。
- **🛠️ 确定性 `manage_skills` 工具**: 通过稳定工具契约完成技能的生命周期管理。
- **🌊 状态栏逻辑加固**: 引入 `session_finalized` 多层锁定机制，彻底解决任务完成后状态栏回弹或卡死的问题。
- **🗂️ 环境目录持久化**: 增强 `COPILOTSDK_CONFIG_DIR` 逻辑，确保会话状态跨容器重启稳定存在。

---

## ✨ 核心能力 (Key Capabilities)

- **🔑 统一智能体验 (官方 + BYOK)**: 自由切换官方模型（o1, GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash）与自定义服务商（OpenAI, Anthropic），支持 **BYOK (自带 Key)** 模式。
- **🛡️ 物理级工作区隔离**: 每个会话在独立的沙箱目录中运行。确保绝对的数据隐私，防止不同聊天间的文件污染，同时给予 Agent 完整的文件系统操作权限。
- **🔌 通用工具协议**:
  - **原生 MCP**: 高性能直连 Model Context Protocol 服务器。
  - **OpenAPI 桥接**: 将任何外部 REST API 一键转换为 Agent 可调用的工具。
  - **OpenWebUI 原生桥接**: 零配置接入现有的 OpenWebUI 工具及内置功能（网页搜索、记忆等）。
- **🧩 OpenWebUI Skills 桥接**: 将简单的 OpenWebUI Markdown 指令转化为包含脚本、模板和数据的强大 SDK 技能文件夹。
- **♾️ 无限会话管理**: 先进的上下文窗口管理，支持自动“压缩”（摘要提取 + TODO 列表持久化）。支持长达数周的项目跟踪而不会丢失核心上下文。
- **📊 交互式产物与发布**:
  - **实时 HTML/JS**: 瞬间渲染并交互 Agent 生成的应用程序、可视化看板或报告。
  - **持久化发布**: Agent 可将生成的产物（Excel, CSV, 文档）发布至 OpenWebUI 文件存储，并在聊天中提供永久下载链接。
- **🌊 极致交互体验**: 完整支持深度思考过程 (Thinking Process) 流式渲染、状态指示器以及长任务实时进度条。
- **🧠 深度数据库集成**: TOD·O 列表与会话元数据的实时持久化，确保任务执行状态在 UI 上清晰可见。

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
| `COPILOTSDK_CONFIG_DIR` | `""` | SDK 配置与会话状态持久化目录 (例如: `/app/backend/data/.copilot`)。 |
| `ENABLE_OPENWEBUI_TOOLS` | `True` | 启用 OpenWebUI 工具 (包括定义工具和内置工具)。 |
| `ENABLE_OPENAPI_SERVER` | `True` | 启用 OpenAPI 工具服务器连接。 |
| `ENABLE_MCP_SERVER` | `True` | 启用直接 MCP 客户端连接 (推荐)。 |
| `ENABLE_OPENWEBUI_SKILLS` | `True` | 开启与 OpenWebUI **工作区 > Skills** 的双向同步桥接。 |
| `OPENWEBUI_SKILLS_SHARED_DIR` | `/app/backend/data/cache/copilot-openwebui-skills` | OpenWebUI skills 转换后的共享缓存目录。 |
| `GITHUB_SKILLS_SOURCE_URL` | `""` | 可选 GitHub tree 地址，用于批量导入 skills（例如 anthropic/skills）。 |
| `DISABLED_SKILLS` | `""` | 逗号分隔的 skill 名称黑名单（如 `docs-writer,webapp-testing`）。 |
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
| `REASONING_EFFORT` | 个人偏好的推理强度。 |
| `SHOW_THINKING` | 显示模型推理/思考过程。 |
| `MAX_MULTIPLIER` | 最大允许的模型计费倍率覆盖。 |
| `EXCLUDE_KEYWORDS` | 排除包含这些关键字的模型。 |
| `ENABLE_OPENWEBUI_SKILLS` | 启用将当前用户可读的全部已启用 OpenWebUI skills 转换并加载为 SDK `SKILL.md` 目录。 |
| `GITHUB_SKILLS_SOURCE_URL` | 为当前用户会话设置可选 GitHub tree 地址以批量导入 skills。 |
| `DISABLED_SKILLS` | 为当前用户会话禁用指定 skills（逗号分隔）。 |
| `BYOK_API_KEY` | 使用个人的 OpenAI/Anthropic API Key。 |

---

### 🌊 细粒度反馈与流畅体验 (Fluid UX)

彻底告别复杂任务执行过程中的“卡顿”感：

- **🔄 实时状态气泡**: 将 SDK 内部事件（如 `turn_start`, `compaction`, `subagent_started`）直接映射为 OpenWebUI 的状态栏信息。
- **🧭 分阶段状态描述增强**: 状态栏会明确显示处理阶段（处理中、技能触发、工具执行、工具完成/失败、发布中、任务完成）。
- **⏱️ 长任务心跳提示**: 长时间处理中会周期性显示“仍在处理中（已耗时 X 秒）”，避免用户误判为卡死。
- **📈 工具执行进度追踪**: 长耗时工具（如代码分析）会在状态栏实时显示进度百分比及当前子任务描述。
- **⚡ 即时响应反馈**: 从响应开始第一秒即显示“助手正在处理您的请求...”，减少等待空窗感。

---

### 🛡️ 智能版本兼容

插件会自动根据您的 OpenWebUI 版本调整功能集：

- **v0.8.0+**: 开启 Rich UI、实时状态气泡及集成 HTML 预览。
- **旧版本**: 自动回退至标准 Markdown 代码块模式，确保最大稳定性。

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

### 4) 配套插件 (强烈推荐)

为了获得最佳的文件处理体验，请安装 [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)。

---

### 📤 增强型发布工具与交互式组件

`publish_file_from_workspace` 现采用更清晰、可落地的交付规范：

- **Artifacts 模式（`artifacts`，默认）**：返回 `[Preview]` + `[Download]`，并可附带 `html_embed`，在 ```html 代码块中直接渲染。
- **Rich UI 模式（`richui`）**：仅返回 `[Preview]` + `[Download]`，由发射器自动触发集成式预览（消息中不输出 iframe 代码块）。
- **📄 PDF 安全交付规则**：仅输出 Markdown 链接（可用时为 `[Preview]` + `[Download]`）。**禁止通过 iframe/html 方式嵌入 PDF。**
- **⚡ 稳定双通道发布**：在本地与对象存储后端下，保持交互预览与持久下载链接一致可用。
- **✅ 状态集成**：通过 OpenWebUI 状态栏实时反馈发布进度与完成状态。
- **📘 发布工具指南（GitHub）**：[publish_file_from_workspace 工具指南（中文）](https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/pipes/github-copilot-sdk/PUBLISH_FILE_FROM_WORKSPACE_CN.md)

---

### 🧩 OpenWebUI Skills 桥接与 `manage_skills` 工具

SDK 现在具备与 OpenWebUI **工作区 > Skills** 的双向同步能力：

- **🔄 自动同步**: 每次请求时，前端定义的技能会自动作为 `SKILL.md` 文件夹同步至 SDK 共享缓存，Agent 可直接调用。
- **🛠️ `manage_skills` 工具**: 内置专业工具，赋予 Agent (或用户) 绝对的技能管理权。
  - `list`: 列出所有已安装技能及描述。
  - `install`: 从 GitHub URL (自动转换归档链接) 或直接从 `.zip`/`.tar.gz` 安装。
  - `create`: 从当前会话内容创建新技能目录，支持写入 `SKILL.md` 及辅助资源文件 (脚本、模板)。
  - `edit`: 更新现有技能文件夹。
  - `delete`: 原子化删除本地目录及关联的数据库条目，防止僵尸技能复活。
- **📁 完整的文件夹支持**: 不同于数据库中单文件存储，SDK 会加载技能的**整个目录**。这使得技能可以携带二进制脚本、数据文件或复杂模板。
- **🌐 持久化共享缓存**: 技能存储在 `OPENWEBUI_SKILLS_SHARED_DIR/shared/`，跨会话及容器重启持久存在。
- **📚 技能完整文档（GitHub）**: [manage_skills 工具指南（中文）](https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/pipes/github-copilot-sdk/SKILLS_MANAGER_CN.md) | [Skills Best Practices（中文）](https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/pipes/github-copilot-sdk/SKILLS_BEST_PRACTICES_CN.md)

---

## 📋 常见问题与依赖 (Troubleshooting)

- **Agent 无法识别文件？**: 请确保已安装并启用了 Files Filter 插件，否则原始文件会被 RAG 干扰。
- **看不到状态更新或 TODO 进度条？**: 状态气泡会覆盖处理/工具阶段；而 TODO 进度条仅在 Agent 使用 `update_todo` 工具（通常是复杂任务）时出现。
- **依赖安装**: 本管道会自动管理 `github-copilot-sdk` (Python 包) 并优先直接使用内置的二进制 CLI，无需手动干预。

---

## 更新日志 (Changelog)

完整历史记录请见 GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
