# Export to Word（导出为 Word）

<span class="category-badge action">Action</span>
<span class="version-badge">v0.1.0</span>

将聊天记录按 Markdown 格式导出为 Word (.docx)，支持语法高亮、引用样式和更智能的文件命名。

---

## 概览

Export to Word 插件会把聊天消息从 Markdown 转成精致的 Word 文档。它完整支持标题、列表、表格、代码块和引用，同时兼顾中英文显示效果。

## 功能特性

- :material-file-word-box: **DOCX 导出**：一键生成 Word 文件
- :material-format-bold: **丰富 Markdown 支持**：标题、粗斜体、列表、表格
- :material-code-tags: **语法高亮**：Pygments 驱动的代码块上色
- :material-format-quote-close: **引用样式**：左侧边框的灰色斜体引用
- :material-file-document-outline: **智能文件名**：优先对话标题 → Markdown 标题 → 用户/日期

---

## 安装

1. 下载插件文件：[`export_to_word.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_docx)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 启用插件

---

## 使用方法

1. 打开想要导出的对话
2. 点击消息操作栏的 **Export to Word** 按钮
3. `.docx` 文件会自动下载

---

## 支持的 Markdown

| 语法 | Word 效果 |
| :---------------------------------- | :-------------------------------- |
| `# 标题1` 到 `###### 标题6` | 标题级别 1-6 |
| `**粗体**` / `__粗体__` | 粗体文本 |
| `*斜体*` / `_斜体_` | 斜体文本 |
| `***粗斜体***` | 粗体 + 斜体 |
| `` `行内代码` `` | 等宽字体 + 灰色背景 |
| <code>``` 代码块 ```</code> | 语法高亮代码块 |
| `> 引用文本` | 左侧边框的灰色斜体 |
| `[链接](url)` | 蓝色下划线链接 |
| `~~删除线~~` | 删除线 |
| `- 项目` / `* 项目` | 无序列表 |
| `1. 项目` | 有序列表 |
| Markdown 表格 | 带边框表格 |
| `---` / `***` | 水平分割线 |

---

## 运行要求

!!! note "前置条件"
    - `python-docx==1.1.2`（文档生成）
    - `Pygments>=2.15.0`（语法高亮，建议安装）

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/export_to_docx){ .md-button }
