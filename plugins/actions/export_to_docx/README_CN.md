# 导出为 Word

将对话导出为 Word (.docx)，支持**代码语法高亮**、**原生数学公式**、**Mermaid 图表**、**引用参考**和**增强表格格式**。

## 功能特点

- **一键导出**：在聊天界面添加"导出为 Word"动作按钮。
- **Markdown 转换**：将 Markdown 语法转换为 Word 格式（标题、粗体、斜体、代码、表格、列表）。
- **代码语法高亮**：使用 Pygments 库为代码块添加语法高亮（支持 500+ 种语言）。
- **原生数学公式**：LaTeX 公式（`$$...$$`、`\[...\]`、`$...$`、`\(...\)`）转换为可编辑的 Word 公式。
- **Mermaid 图表**：Mermaid 流程图和时序图渲染为文档中的图片。
- **引用与参考**：自动从 OpenWebUI 来源生成参考资料章节，支持可点击的引用链接。
- **移除思考过程**：自动移除 AI 思考块（`<think>`、`<analysis>`）。
- **增强表格**：智能列宽、列对齐（`:---`、`---:`、`:---:`）、表头跨页重复。
- **引用块支持**：Markdown 引用块渲染为带左侧边框的灰色斜体样式。
- **多语言支持**：正确处理中文和英文文本，无乱码问题。
- **智能文件名**：可配置标题来源（对话标题、AI 生成或 Markdown 标题）。

## 配置

您可以通过插件设置中的 **Valves** 按钮配置以下选项：

- **TITLE_SOURCE**：选择文档标题/文件名的生成方式。
    - `chat_title`：使用对话标题（默认）。
    - `ai_generated`：使用 AI 根据内容生成简短标题。
    - `markdown_title`：从 Markdown 内容中提取第一个一级或二级标题。
- **MAX_EMBED_IMAGE_MB**：嵌入图片的最大大小 (MB)。默认：`20`。
- **UI_LANGUAGE**：界面语言，支持 `en` (英语) 和 `zh` (中文)。默认：`zh`。
- **FONT_LATIN**：英文字体名称。默认：`Calibri`。
- **FONT_ASIAN**：中文字体名称。默认：`SimSun`。
- **FONT_CODE**：代码字体名称。默认：`Consolas`。
- **TABLE_HEADER_COLOR**：表头背景色（十六进制，不带#）。默认：`F2F2F2`。
- **TABLE_ZEBRA_COLOR**：表格隔行背景色（十六进制，不带#）。默认：`FBFBFB`。
- **MERMAID_JS_URL**：Mermaid.js 库的 URL。
- **MERMAID_JSZIP_URL**：JSZip 库的 URL（用于 DOCX 操作）。
- **MERMAID_PNG_SCALE**：Mermaid PNG 生成缩放比例（分辨率）。默认：`3.0`。
- **MERMAID_DISPLAY_SCALE**：Mermaid 在 Word 中的显示比例（视觉大小）。默认：`1.0`。
- **MERMAID_OPTIMIZE_LAYOUT**：自动将 LR（左右）流程图转换为 TD（上下）。默认：`False`。
- **MERMAID_BACKGROUND**：Mermaid 图表背景色（如 `white`, `transparent`）。默认：`transparent`。
- **MERMAID_CAPTIONS_ENABLE**：启用/禁用 Mermaid 图表的图注。默认：`True`。
- **MERMAID_CAPTION_STYLE**：Mermaid 图注的段落样式名称。默认：`Caption`。
- **MERMAID_CAPTION_PREFIX**：图注前缀（如 '图'）。留空则根据语言自动检测。
- **MATH_ENABLE**：启用 LaTeX 数学公式块转换（`\[...\]` 和 `$$...$$`）。默认：`True`。
- **MATH_INLINE_DOLLAR_ENABLE**：启用行内 `$ ... $` 数学公式转换。默认：`True`。

## 支持的 Markdown 语法

| 语法                          | Word 效果                         |
| :---------------------------- | :-------------------------------- |
| `# 标题1` 到 `###### 标题6`   | 标题级别 1-6                      |
| `**粗体**` 或 `__粗体__`      | 粗体文本                          |
| `*斜体*` 或 `_斜体_`          | 斜体文本                          |
| `***粗斜体***`                | 粗体 + 斜体                       |
| `` `行内代码` ``              | 等宽字体 + 灰色背景               |
| ` ``` 代码块 ``` `            | **语法高亮**的代码块              |
| `> 引用文本`                  | 带左侧边框的灰色斜体文本          |
| `[链接](url)`                 | 蓝色下划线链接文本                |
| `~~删除线~~`                  | 删除线文本                        |
| `- 项目` 或 `* 项目`          | 无序列表                          |
| `1. 项目`                     | 有序列表                          |
| Markdown 表格                 | **增强表格**（智能列宽）          |
| `---` 或 `***`                | 水平分割线                        |
| `$$LaTeX$$` 或 `\[LaTeX\]`    | **原生 Word 公式**（块级）        |
| `$LaTeX$` 或 `\(LaTeX\)`      | **原生 Word 公式**（行内）        |
| ` ```mermaid ... ``` `        | **Mermaid 图表**（图片形式）      |
| `[1]` 引用标记                | **可点击链接**到参考资料          |

## 使用方法

1. 安装插件。
2. 在任意对话中，点击"导出为 Word"按钮。
3. .docx 文件将自动下载到你的设备。

## 依赖

- `python-docx==1.1.2` - Word 文档生成
- `Pygments>=2.15.0` - 语法高亮
- `latex2mathml` - LaTeX 转 MathML
- `mathml2omml` - MathML 转 Office Math (OMML)

所有依赖已在插件文档字符串中声明。

## 字体配置

- **英文文本**：Times New Roman
- **中文文本**：宋体（正文）、黑体（标题）
- **代码**：Consolas

## 更新日志

### v0.4.0

- **多语言支持**: 新增界面语言切换（中文/英文），提示信息更友好。
- **字体与样式配置**: 支持自定义中英文字体、代码字体以及表格颜色。
- **Mermaid 增强**: 
    - 客户端混合渲染（SVG+PNG），提高清晰度与兼容性。
    - 支持背景色配置，修复深色模式下的显示问题。
    - 增加错误边界，渲染失败时显示提示而非中断导出。
- **性能优化**: 导出大型文档时提供实时进度反馈。
- **Bug 修复**: 
    - 修复 Markdown 表格中包含代码块或链接时的解析错误。
    - 修复下划线（`_`）、星号（`*`）、波浪号（`~`）作为长分隔符时的解析问题。
    - 增强图片嵌入的错误处理。

### v0.3.0

- **Mermaid 图表**: 原生支持将 Mermaid 图表渲染为 Word 中的图片。
- **原生公式**: 将 LaTeX 公式转换为原生 Office MathML，支持在 Word 中编辑。
- **引用参考**: 自动生成参考文献列表并链接引用。
- **移除推理**: 选项支持从输出中移除 `<think>` 推理块。
- **表格增强**: 改进表格格式，支持智能列宽。

### v0.2.0
- 新增原生数学公式支持（LaTeX → OMML）
- 新增 Mermaid 图表渲染
- 新增引用与参考资料章节生成
- 新增自动移除 AI 思考块
- 增强表格格式（智能列宽、对齐）

### v0.1.1
- 初始版本，支持基本 Markdown 转 Word

## 作者

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## 许可证

MIT License
