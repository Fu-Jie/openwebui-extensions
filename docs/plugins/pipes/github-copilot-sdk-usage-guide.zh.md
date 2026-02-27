# GitHub Copilot SDK Pipe 详细使用手册

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.9.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

本手册面向“实际落地使用”，覆盖从安装、鉴权、模型选择到文件发布、Skills 管理、故障排查的完整流程。README 侧重社区展示，本页专注操作细节。

---

## 1. 适用场景

适合以下需求：

- 在 OpenWebUI 内使用 GitHub Copilot 官方模型（含流式、工具调用、多轮会话）
- 使用 BYOK（OpenAI/Anthropic）替代官方订阅
- 让 Agent 生成并发布文件（Excel/CSV/HTML/PDF）
- 使用 OpenWebUI Skills 与 `manage_skills` 做技能工程化管理

---

## 2. 部署前检查

### 2.1 OpenWebUI 与插件文件

- 已运行 OpenWebUI（建议 `v0.8.0+` 以获得 Rich UI 体验）
- 已导入 Pipe 文件：`plugins/pipes/github-copilot-sdk/github_copilot_sdk.py`
- 建议同时安装 Files Filter：
  - [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)

### 2.2 必要鉴权（至少一种）

你必须配置下列其中一种凭据，否则模型列表为空：

1. `GH_TOKEN`（访问 GitHub Copilot 官方模型）
2. `BYOK_API_KEY`（访问 OpenAI/Anthropic 等自有供应商）

---

## 3. 安装与启用

1. 进入 OpenWebUI：**工作区 → 函数**
2. 新建函数并粘贴 `github_copilot_sdk.py` 全量内容
3. 保存并启用
4. 回到聊天页，在模型列表选择：
   - `github_copilot_official_sdk_pipe.*`（官方）
   - 或 BYOK 对应模型

---

## 4. 配置建议（先跑起来再精调）

### 4.1 管理员最小可用配置

- `GH_TOKEN` 或 `BYOK_API_KEY`
- `ENABLE_OPENWEBUI_TOOLS = True`
- `ENABLE_MCP_SERVER = True`
- `ENABLE_OPENWEBUI_SKILLS = True`
- `SHOW_THINKING = True`

### 4.2 推荐增强项

- `COPILOTSDK_CONFIG_DIR=/app/backend/data/.copilot`
  - 用于 SDK 配置/会话状态持久化（重启不丢）
- `OPENWEBUI_SKILLS_SHARED_DIR=/app/backend/data/cache/copilot-openwebui-skills`
  - 统一 skills 缓存目录
- `DEBUG=True`（排障阶段）

### 4.3 用户级覆盖（Profile）

普通用户可按需覆盖：`GH_TOKEN`、`REASONING_EFFORT`、`BYOK_API_KEY`、`DISABLED_SKILLS` 等。

---

## 5. 两种模型接入模式

## 5.1 官方模式（GitHub Copilot）

- 配置 `GH_TOKEN`
- 模型来自 Copilot 官方可用列表
- 支持推理强度、工具调用、无限会话等插件能力

## 5.2 BYOK 模式（OpenAI/Anthropic）

- 配置 `BYOK_TYPE`、`BYOK_BASE_URL`、`BYOK_API_KEY`
- `BYOK_MODELS` 留空可自动拉取，或手动逗号分隔指定
- 适合无官方订阅、或需要指定厂商模型时使用

---

## 6. 文件发布完整工作流（重点）

插件内置 `publish_file_from_workspace`，推荐遵循“写入 → 发布 → 返回链接”。

### 6.1 HTML 交付模式

- `artifacts`（默认）
  - 返回 `[Preview]` + `[Download]`
  - 可输出 `html_embed`（iframe）用于完整交互展示
- `richui`
  - 返回 `[Preview]` + `[Download]`
  - 由 Rich UI 自动渲染，不在消息中输出 iframe 代码块

### 6.2 PDF 交付规则（务必遵守）

- 仅输出 Markdown 链接（可用时 `[Preview]` + `[Download]`）
- **不要**输出 PDF iframe/embed HTML

### 6.3 图片与其他文件

- 图片：优先直接展示 + 下载
- 其他文件（xlsx/csv/docx 等）：返回下载链接为主

---

## 7. Skills 使用与管理

> 关键原则：`manage_skills` 是 **工具（tool）**，不是 skill；所有 skills 统一安装在 **一个目录**：`OPENWEBUI_SKILLS_SHARED_DIR/shared/`。

## 7.1 OpenWebUI Skills 双向桥接

当 `ENABLE_OPENWEBUI_SKILLS=True` 时：

- UI 中创建/编辑的 Skills 会同步到 SDK 目录
- 目录内技能更新可回写到 OpenWebUI（按同步规则）

## 7.2 `manage_skills` 常用动作

- `list`：列出现有技能
- `install`：从 GitHub URL / `.zip` / `.tar.gz` 安装
- `create`：从当前上下文创建技能
- `edit`：更新技能内容与附加文件
- `show`：查看 `SKILL.md` 与附属文件
- `delete`：删除本地目录并清理关联记录

### 7.3 生产建议

- 用 `DISABLED_SKILLS` 关闭不需要的技能，降低误触发
- Skill 描述尽量明确（包含 Use when 语义），提高路由准确率

---

## 8. 首次验收清单

完成部署后，建议按顺序验证：

1. **基础对话**：确认模型能正常响应
2. **工具调用**：执行一条会触发工具的指令（如文件分析）
3. **文件发布**：生成一个 `csv` 并确认可下载
4. **HTML 发布**：验证 `artifacts/richui` 至少一种模式
5. **PDF 发布**：确认仅返回链接，无 iframe
6. **Skills**：执行 `manage_skills list`，确认可见

---

## 9. 常见问题排查

### 9.1 模型列表为空

- 检查 `GH_TOKEN` / `BYOK_API_KEY` 是否至少配置一个
- 检查 BYOK `BASE_URL` 是否可达、模型名是否有效

### 9.2 工具似乎不可用

- 检查 `ENABLE_OPENWEBUI_TOOLS`、`ENABLE_MCP_SERVER`、`ENABLE_OPENAPI_SERVER`
- 检查当前模型/会话是否有工具权限

### 9.3 文件发布成功但无法打开

- 检查返回链接是否来自工具原始输出
- 检查对象存储/本地存储权限与可访问性
- PDF 场景不要尝试 iframe 嵌入

### 9.4 状态栏“卡住”

- 升级到最新插件代码
- 打开 `DEBUG=True` 查看事件流
- 确认前端版本与 Rich UI 能力匹配

---

## 10. 推荐操作模板（可直接对 AI 说）

- “读取当前目录下的 `sales.csv`，按月份汇总并导出 `monthly_summary.xlsx`，最后给我下载链接。”
- “生成一个交互式 HTML 仪表盘并发布，给我 Preview 和 Download 链接。”
- “把本次流程固化成一个 skill，命名为 `finance-reporting`，并写入使用说明。”

---

如需架构细节，请结合阅读：

- [深度解析](github-copilot-sdk-deep-dive.zh.md)
- [进阶实战教程](github-copilot-sdk-tutorial.zh.md)
- [插件主文档](github-copilot-sdk.zh.md)
