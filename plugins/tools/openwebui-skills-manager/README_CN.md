# 🧰 OpenWebUI Skills 管理工具

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 0.2.1 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

一个 OpenWebUI 原生 Tool 插件，用于让任意模型直接管理 **Workspace > Skills**。

## 最新更新

- `install_skill` 新增 GitHub 技能目录自动发现（例如 `.../tree/main/skills`），可一键安装目录下所有子技能。
- 修复语言获取逻辑：前端优先（`__event_call__` + 超时保护），并回退到请求头与用户资料。

## 核心特性

- **🌐 全模型可用**：只要模型启用了 OpenWebUI Tools，即可调用。
- **🛠️ 简化技能管理**：直接管理 OpenWebUI Skills 记录。
- **🔐 用户范围安全**：仅操作当前用户可访问的技能。
- **📡 友好状态反馈**：每一步操作都有状态栏提示。

## 使用方法

1. 打开 OpenWebUI，进入 **Workspace > Tools**。
2. 在官方市场安装 **OpenWebUI Skills 管理工具**。
3. 为当前模型/聊天启用该工具。
4. 在对话中让模型调用，例如：
   - “列出我的 skills”
   - “显示名为 docs-writer 的 skill”
   - “创建一个 meeting-notes 技能，内容是 ...”
   - “更新某个 skill ...”
   - “删除某个 skill ...”

### 手动安装（备选）

- 新建 Tool，粘贴 `openwebui_skills_manager.py`。

## 示例：安装技能 (Install Skills)

该工具支持从 URL 直接抓取并安装技能（支持 GitHub tree/blob 链接、原始 Markdown 链接以及 .zip/.tar 压缩包）。

### 从 GitHub 安装单个技能

- “从 <https://github.com/anthropics/skills/tree/main/skills/xlsx> 安装技能”
- “安装技能 <https://github.com/Fu-Jie/openwebui-extensions/blob/main/.agent/skills/test-copilot-pipe/SKILL.md”>

### 批量安装多个技能

- “安装这些技能：['https://github.com/anthropics/skills/tree/main/skills/xlsx', 'https://github.com/anthropics/skills/tree/main/skills/docx']”

> **提示**：对于 GitHub 链接，工具会自动处理目录（tree）地址，并尝试查找目录下的 `SKILL.md` 或 `README.md` 文件。

## 配置参数（Valves）

| 参数 | 默认值 | 说明 |
| --- | ---: | --- |
| `SHOW_STATUS` | `True` | 是否在 OpenWebUI 状态栏显示操作状态。 |
| `ALLOW_OVERWRITE_ON_CREATE` | `False` | 是否允许 `create_skill`/`install_skill` 默认覆盖同名技能。 |
| `INSTALL_FETCH_TIMEOUT` | `12.0` | 从 URL 安装技能时的请求超时时间（秒）。 |

## 支持的方法

| 方法 | 用途 |
| --- | --- |
| `list_skills` | 列出当前用户的技能。 |
| `show_skill` | 通过 `skill_id` 或 `name` 查看单个技能。 |
| `install_skill` | 通过 URL 安装技能到 OpenWebUI 原生 Skills。 |
| `create_skill` | 创建新技能（或在允许时覆盖同名技能）。 |
| `update_skill` | 更新技能字段（`new_name`、`description`、`content`、`is_active`）。 |
| `delete_skill` | 通过 `skill_id` 或 `name` 删除技能。 |

## 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 其他说明

- 本工具管理 OpenWebUI 原生 Skills 记录，并支持通过 URL 直接安装。
- 如需更复杂的工作流编排，可结合其他 Pipe/Tool 方案使用。

## 更新记录

完整历史请查看 GitHub 仓库的 commits 与 releases。
