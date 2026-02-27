# 📤 `publish_file_from_workspace` 工具指南

本文档说明 GitHub Copilot SDK Pipe 内置工具 `publish_file_from_workspace` 的推荐使用规范。

## 工具用途

当 Agent 在当前工作区生成文件后，使用此工具可实现：

- 将文件发布到 OpenWebUI 文件存储。
- 返回稳定可用的预览/下载链接。
- 在本地磁盘与对象存储后端保持一致交付行为。

## 必填参数

- `filename`：工作区内的相对路径文件名。
  - ✅ 示例：`report.xlsx`
  - ✅ 示例：`output/summary.html`
  - ❌ 避免工作区外临时路径（如 `/tmp/...`）。

## 返回结构（常见字段）

该工具通常返回用于构建前端链接与渲染的数据：

- `filename`
- `download_url`
- `preview_url`（如可预览）
- 渲染元数据（HTML 场景可含 `html_embed`）

## 发布模式

### 1) `artifacts`（默认）

- 消息中返回 `[Preview]` + `[Download]`。
- 对于 HTML 可预览内容，可在 ```html 代码块中渲染 `html_embed`。
- 适用于聊天内联交互式预览。

### 2) `richui`

- 消息中返回 `[Preview]` + `[Download]`。
- 由 Rich UI 渲染器自动输出集成预览。
- 聊天正文中不输出 iframe/html 预览块。

## PDF 安全规则（强制）

针对 PDF 文件，必须只输出 Markdown 链接：

- `[Preview](...)`
- `[Download](...)`（可用时）

禁止使用 iframe 或 HTML 代码块嵌入 PDF。

## 推荐流程

1. 在工作区生成文件。
2. 调用 `publish_file_from_workspace(filename=...)`。
3. 按模式返回链接。
4. 若为 `.pdf`，严格执行“仅链接”规则。

## 示例

### 示例 A：HTML 报告（artifacts）

- 发布 `analysis.html`。
- 返回链接。
- 允许渲染 `html_embed` 进行直接预览。

### 示例 B：PDF 报告

- 发布 `audit.pdf`。
- 仅返回链接。
- 完全跳过 iframe/html 嵌入。

## 相关文档

- [manage_skills 工具指南](./SKILLS_MANAGER_CN.md)
- [Skills 最佳实践](./SKILLS_BEST_PRACTICES_CN.md)
