# 📝 导出为 Word (增强版)

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.4.4 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

将对话导出为 Word (.docx)，支持**代码语法高亮**、**原生数学公式**、**Mermaid 图表**、**引用参考**和**增强表格格式**。

## 🔥 v0.4.4 更新内容

- 🧹 **内容清理加强**: 增强了对 `<details>` 块（通常包含工具调用或思考过程）的清理，确保最终文档整洁。
- 📄 **文档格式标准化**: 采用了专业的文档排版标准（兼容中文 GB/T 规范），标题居中加粗，各级标题使用标准字号和间距。
- 🔠 **字体渲染修复**: 修复了 CJK 字符在 Word 中回退到 MS Gothic 的问题；现在正确使用配置的中文字体（例如宋体）。
- ⚙️ **标题对齐配置**: 新增 `标题对齐方式` Valve，支持配置文档标题的对齐方式（左对齐、居中、右对齐）。

## ✨ 核心特性

- 🚀 **一键导出**: 在聊天界面添加"导出为 Word"动作按钮。
- 📄 **Markdown 转换**: 完整支持 Markdown 语法（标题、粗体、斜体、代码、表格、列表）。
- 🎨 **代码语法高亮**: 使用 Pygments 库高亮代码块（支持 500+ 种语言）。
- 🔢 **原生数学公式**: LaTeX 公式（`$$...$$`、`\[...\]`、`$...$`）转换为可编辑的 Word 公式。
- 📊 **Mermaid 图表**: 流程图和时序图渲染为文档中的图片。
- 📚 **引用与参考**: 自动生成参考资料章节，支持可点击的引用链接。
- 🧹 **移除思考过程**: 自动移除 AI 思考块（`<think>`、`<analysis>`）。
- 📋 **增强表格**: 智能列宽、对齐、表头跨页重复。
- 💬 **引用块支持**: Markdown 引用块渲染为带左侧边框的灰色斜体样式。
- 🌐 **多语言支持**: 正确处理中文和英文文本。

## 🚀 使用方法

1. **安装**: 在 Open WebUI 社区搜索 "导出为 Word" 并安装。
2. **触发**: 在任意对话中，点击"导出为 Word"动作按钮。
3. **下载**: .docx 文件将自动下载到你的设备。

## ⚙️ 配置参数 (Valves)

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| **文档标题来源** | `chat_title` | `chat_title`（对话标题）、`ai_generated`（AI 生成）、`markdown_title`（Markdown 标题）|
| **最大嵌入图片大小MB** | `20` | 嵌入图片的最大大小 (MB) |
| **界面语言** | `zh` | `en`（英语）或 `zh`（中文）|
| **英文字体** | `Calibri` | 英文字体名称 |
| **中文字体** | `SimSun` | 中文字体名称 |
| **代码字体** | `Consolas` | 代码块字体名称 |
| **表头背景色** | `F2F2F2` | 表头背景色（十六进制）|
| **表格隔行背景色** | `FBFBFB` | 表格隔行背景色（十六进制）|
| **Mermaid_PNG缩放比例** | `3.0` | Mermaid 图片分辨率倍数 |
| **启用数学公式** | `True` | 启用 LaTeX 公式转换 |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 🛠️ 支持的 Markdown 语法

| 语法 | Word 效果 |
| :--- | :--- |
| `# 标题1` 到 `###### 标题6` | 标题级别 1-6 |
| `**粗体**` 或 `__粗体__` | 粗体文本 |
| `*斜体*` 或 `_斜体_` | 斜体文本 |
| `` `行内代码` `` | 等宽字体 + 灰色背景 |
| ` ``` 代码块 ``` ` | **语法高亮**的代码块 |
| `> 引用文本` | 带左侧边框的灰色斜体文本 |
| `[链接](url)` | 蓝色下划线链接文本 |
| `~~删除线~~` | 删除线文本 |
| `- 项目` 或 `* 项目` | 无序列表 |
| `1. 项目` | 有序列表 |
| Markdown 表格 | **增强表格**（智能列宽）|
| `$$LaTeX$$` 或 `\[LaTeX\]` | **原生 Word 公式**（块级）|
| `$LaTeX$` 或 `\(LaTeX\)` | **原生 Word 公式**（行内）|
| ` ```mermaid ... ``` ` | **Mermaid 图表**（图片形式）|
| `[1]` 引用标记 | **可点击链接**到参考资料 |

## 📦 依赖

- `python-docx==1.1.2` - Word 文档生成
- `Pygments>=2.15.0` - 语法高亮
- `latex2mathml` - LaTeX 转 MathML
- `mathml2omml` - MathML 转 Office Math (OMML)

## 故障排除 (Troubleshooting) ❓

- **插件不工作？**: 请检查是否在模型设置中启用了该过滤器/动作。
- **调试日志**: 请查看浏览器控制台 (F12) 获取详细日志（如果可用）。
- **错误信息**: 如果看到错误，请复制完整的错误信息并报告。
- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## 📝 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
