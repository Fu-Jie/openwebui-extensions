# GitHub Copilot SDK Pipe - `publish_file_from_workspace` 工具指南

## 简介

`publish_file_from_workspace` 是 GitHub Copilot SDK Pipe 的文件交付工具，用于将工作区生成文件发布到 OpenWebUI 存储，并返回稳定的预览/下载链接。

## 输入参数

- `filename`（必填）：当前工作区下的相对路径文件名。

## 交付模式

- `artifacts`（默认）：返回 `[Preview]` + `[Download]`，可选在 HTML 代码块中渲染 `html_embed`。
- `richui`：返回 `[Preview]` + `[Download]`，集成预览由 Rich UI 发射器自动渲染。

## PDF 规则

PDF 必须只返回 Markdown 链接（`[Preview]`、`[Download]` 可用时），禁止 iframe 或 HTML 嵌入。

## 推荐流程

1. 在工作区生成文件。
2. 调用 `publish_file_from_workspace(filename=...)` 发布。
3. 按当前模式返回链接。
4. `.pdf` 严格执行仅链接规则。

## 参考

- 插件内完整指南：`plugins/pipes/github-copilot-sdk/PUBLISH_FILE_FROM_WORKSPACE_CN.md`
