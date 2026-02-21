# Export to Excel（导出到 Excel）

<span class="category-badge action">Action</span>
<span class="version-badge">v0.3.7</span>

将聊天记录导出为 Excel 表格，便于分析、归档和分享。


### v0.3.6 更新内容
- **OpenWebUI 风格主题**：现代深灰表头，搭配浅灰斑马纹，提升可读性。
- **斑马纹效果**：隔行变色，方便视觉扫描。
- **智能数据类型转换**：自动将列转换为数字或日期类型。
- **全单元格粗体/斜体**：支持 Markdown 粗体/斜体格式。
- **部分 Markdown 清理**：移除部分 Markdown 符号，输出更整洁。
- **导出范围**：可选择导出"最后一条消息"或"所有消息"。
- **智能 Sheet 命名**：根据 Markdown 标题或消息索引命名 Sheet。
- **智能文件名生成**：支持对话标题、AI 总结或 Markdown 标题生成文件名。
- **AI 标题生成**：支持指定模型 (`MODEL_ID`) 生成标题，并提供生成进度通知。

---


## 概览

Export to Excel 插件可以把你的聊天记录下载为 Excel 文件，适用于：

- 归档重要对话
- 分析聊天数据
- 与同事共享对话内容
- 将 AI 辅助的研究整理成文档

## 功能特性

- :material-file-excel: **Excel 导出**：标准 `.xlsx` 格式
- :material-table: **格式化输出**：整洁的表格结构
- :material-download: **一键下载**：即时生成文件
- :material-history: **完整历史**：导出完整会话内容

## 配置

- **标题来源 (Title Source)**：选择文件名的生成方式：
  - `chat_title`：使用对话标题（默认）。
  - `ai_generated`：使用 AI 根据内容生成简洁标题。
  - `markdown_title`：提取 Markdown 内容中的第一个 H1/H2 标题。

---

## 安装

1. 下载插件文件：[`export_to_excel.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/export_to_excel)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 启用插件

---

## 使用方法

1. 打开想要导出的对话
2. 点击消息操作栏中的 **Export** 按钮
3. Excel 文件会自动下载

---

## 导出格式

生成的 Excel 文件包含：

| 列 | 说明 |
|--------|-------------|
| Timestamp | 消息发送时间 |
| Role | 角色（用户 / 助手） |
| Content | 消息文本内容 |
| Model | 使用的模型（助手消息） |

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上
    - 无需额外 Python 依赖（使用内置库）

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/export_to_excel){ .md-button }
