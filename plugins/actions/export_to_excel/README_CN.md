# 📊 导出为 Excel

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 0.3.6 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

将对话历史直接导出为 Excel (.xlsx) 文件。

## 🔥 最新更新 v0.3.6

- **OpenWebUI 风格主题**：现代深灰表头（#1f2937）与浅灰斑马纹，提升可读性。
- **斑马纹效果**：隔行变色（#ffffff / #f3f4f6），方便视觉扫描。
- **智能数据类型转换**：自动将列转换为数字或日期类型，无法转换时保持字符串。
- **全单元格粗体/斜体**：支持全单元格 Markdown 粗体与斜体格式。
- **部分 Markdown 清理**：移除部分 Markdown 格式符号，输出更整洁。
- **导出范围**：新增 `EXPORT_SCOPE`，可选择导出最后一条或所有消息。
- **智能 Sheet 命名**：按 Markdown 标题、AI 标题或消息索引命名。
- **多表格支持**：优化了多表格处理能力。
- **智能文件名生成**：支持对话标题 / AI 总结 / Markdown 标题命名。
- **配置选项**：新增 `TITLE_SOURCE` 控制文件名策略。
- **AI 标题生成**：新增 `MODEL_ID`，支持 AI 标题生成与进度提示。

## ✨ 核心特性

- 🚀 **一键导出**：在聊天界面添加“导出为 Excel”按钮。
- 🧠 **自动表头提取**：智能识别聊天内容中的表格标题。
- 📊 **多表支持**：支持单次对话中的多个表格。

## 🚀 使用方法

1. **安装**：在 Open WebUI 社区搜索“导出为 Excel”并安装。
2. **触发**：在任意对话中，点击“导出为 Excel”动作按钮。
3. **下载**：.xlsx 文件将自动下载到你的设备。

## ⚙️ 配置参数 (Valves)

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `TITLE_SOURCE` | `chat_title` | 文件名来源：`chat_title`、`ai_generated`、`markdown_title`。 |
| `EXPORT_SCOPE` | `last_message` | 导出范围：`last_message` 或 `all_messages`。 |
| `MODEL_ID` | `""` | AI 标题生成的模型 ID。为空则使用当前对话模型。 |
| `SHOW_STATUS` | `True` | 是否显示操作状态更新。 |
| `SHOW_DEBUG_LOG` | `False` | 是否在浏览器控制台输出调试日志 (F12)。 |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 故障排除 (Troubleshooting) ❓

- **插件不工作？**: 请检查是否在模型设置中启用了该过滤器/动作。
- **调试日志**: 如需排查，启用 `SHOW_STATUS` 并查看浏览器控制台 (F12)。
- **错误信息**: 如果看到错误，请复制完整的错误信息并报告。
- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)# 导出为 Excel

此插件允许你直接从聊天界面将对话历史导出为 Excel (.xlsx) 文件。

## v0.3.6 更新内容

- **OpenWebUI 风格主题**：现代深灰表头 (#1f2937)，搭配浅灰斑马纹，提升可读性。
- **斑马纹效果**：隔行变色（#ffffff / #f3f4f6），方便视觉扫描。
- **智能数据类型转换**：自动将列转换为数字或日期类型，无法转换时保持字符串。
- **全单元格粗体/斜体**：支持 Excel 中的全单元格 Markdown 粗体 (`**text**`) 和斜体 (`*text*`) 格式。
- **部分 Markdown 清理**：自动移除部分 Markdown 格式符号（如 `部分**加粗**文本` → `部分加粗文本`），使 Excel 输出更整洁。
- **导出范围**: 新增 `EXPORT_SCOPE` 配置项，可选择导出"最后一条消息"（默认）或"所有消息"中的表格。
- **智能 Sheet 命名**: 根据 Markdown 标题、AI 标题（如启用）或消息索引（如 `消息1-表1`）自动命名 Sheet。
- **多表格支持**: 优化了对单条或多条消息中包含多个表格的处理。
- **智能文件名生成**：支持根据对话标题、AI 总结或 Markdown 标题生成文件名。
- **配置选项**：新增 `TITLE_SOURCE` 设置，用于控制文件名生成策略。
- **AI 标题生成**：新增 `MODEL_ID` 设置用于指定 AI 标题生成模型，并支持生成进度通知。

## 功能特点

- **一键导出**：在聊天界面添加"导出为 Excel"按钮。
- **自动表头提取**：智能识别聊天内容中的表格标题。
- **多表支持**：支持处理单次对话中的多个表格。

## 配置

- **标题来源 (Title Source)**：选择文件名的生成方式：
  - `chat_title`：使用对话标题（默认）。
  - `ai_generated`：使用 AI 根据内容生成简洁标题。
  - `markdown_title`：提取 Markdown 内容中的第一个 H1/H2 标题。

## 使用方法

1. 安装插件。
2. 在任意对话中，点击"导出为 Excel"按钮。
3. 文件将自动下载到你的设备。

## 作者

Fu-Jie
GitHub: [Fu-Jie/openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)

## 许可证

MIT License
