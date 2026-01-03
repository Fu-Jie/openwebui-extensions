# 导出为 Excel

此插件允许你直接从聊天界面将对话历史导出为 Excel (.xlsx) 文件。

## v0.3.4 更新内容

- **智能文件名生成**：支持根据对话标题、AI 总结或 Markdown 标题生成文件名。
- **配置选项**：新增 `TITLE_SOURCE` 设置，用于控制文件名生成策略。

## 功能特点

- **一键导出**：在聊天界面添加“导出为 Excel”按钮。
- **自动表头提取**：智能识别聊天内容中的表格标题。
- **多表支持**：支持处理单次对话中的多个表格。

## 配置

- **标题来源 (Title Source)**：选择文件名的生成方式：
  - `chat_title`：使用对话标题（默认）。
  - `ai_generated`：使用 AI 根据内容生成简洁标题。
  - `markdown_title`：提取 Markdown 内容中的第一个 H1/H2 标题。

## 使用方法

1. 安装插件。
2. 在任意对话中，点击“导出为 Excel”按钮。
3. 文件将自动下载到你的设备。

## 作者

Fu-Jie
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## 许可证

MIT License
