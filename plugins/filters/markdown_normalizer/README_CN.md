# Markdown 格式化过滤器 (Markdown Normalizer)

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 1.2.0 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 Open WebUI 的内容格式化过滤器，旨在修复 LLM 输出中常见的 Markdown 格式问题。它能确保代码块、LaTeX 公式、Mermaid 图表和其他 Markdown 元素被正确渲染。

## 功能特性

*   **Details 标签规范化**: 确保 `<details>` 标签（常用于思维链）有正确的间距。在 `</details>` 后添加空行，并在自闭合 `<details />` 标签后添加换行，防止渲染问题。
*   **Mermaid 语法修复**: 自动修复常见的 Mermaid 语法错误，如未加引号的节点标签（支持多行标签和引用标记）和未闭合的子图 (Subgraph)。**v1.1.2 新增**: 全面保护各种类型的连线标签（实线、虚线、粗线），防止被误修改。
*   **前端控制台调试**: 支持将结构化的调试日志直接打印到浏览器控制台 (F12)，方便排查问题。
*   **代码块格式化**: 修复破损的代码块前缀、后缀和缩进问题。
*   **LaTeX 规范化**: 标准化 LaTeX 公式定界符 (`\[` -> `$$`, `\(` -> `$`)。
*   **思维标签规范化**: 统一思维链标签 (`<think>`, `<thinking>` -> `<thought>`)。
*   **转义字符修复**: 清理过度的转义字符 (`\\n`, `\\t`)。
*   **列表格式化**: 确保列表项有正确的换行。
*   **标题修复**: 修复标题中缺失的空格 (`#标题` -> `# 标题`)。
*   **表格修复**: 修复表格中缺失的闭合管道符。
*   **XML 清理**: 移除残留的 XML 标签。

## 使用方法

1.  在 Open WebUI 中安装此插件。
2.  全局启用或为特定模型启用此过滤器。
3.  在 **Valves** 设置中配置需要启用的修复项。
4.  (可选) **显示调试日志 (Show Debug Log)** 在 Valves 中默认开启。这会将结构化的日志打印到浏览器控制台 (F12)。
    > [!WARNING]
    > 由于这是初版，可能会出现“负向修复”的情况（例如破坏了原本正确的格式）。如果您遇到问题，请务必查看控制台日志，复制“原始 (Original)”与“规范化 (Normalized)”的内容对比，并提交 Issue 反馈。

## 配置项 (Valves)

*   `priority`: 过滤器优先级 (默认: 50)。
*   `enable_escape_fix`: 修复过度的转义字符。
*   `enable_thought_tag_fix`: 规范化思维标签。
*   `enable_details_tag_fix`: 规范化 Details 标签 (默认: True)。
*   `enable_code_block_fix`: 修复代码块格式。
*   `enable_latex_fix`: 规范化 LaTeX 公式。
*   `enable_list_fix`: 修复列表项换行 (实验性)。
*   `enable_unclosed_block_fix`: 自动闭合未闭合的代码块。
*   `enable_fullwidth_symbol_fix`: 修复代码块中的全角符号。
*   `enable_mermaid_fix`: 修复 Mermaid 语法错误。
*   `enable_heading_fix`: 修复标题中缺失的空格。
*   `enable_table_fix`: 修复表格中缺失的闭合管道符。
*   `enable_xml_tag_cleanup`: 清理残留的 XML 标签。
*   `show_status`: 应用修复时显示状态通知。
*   `show_debug_log`: 在浏览器控制台打印调试日志。

## 故障排除 (Troubleshooting) ❓

- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[Awesome OpenWebUI Issues](https://github.com/Fu-Jie/awesome-openwebui/issues)

## 更新日志

### v1.2.0
*   **Details 标签支持**: 新增了对 `<details>` 标签的规范化支持。
    *   确保在 `</details>` 闭合标签后添加空行，将思维内容与正文分隔开。
    *   确保在自闭合 `<details ... />` 标签后添加换行，防止其干扰后续的 Markdown 标题（例如修复 `<details/>#标题`）。
    *   包含保护机制，防止修改代码块内部的 `<details>` 标签。

### v1.1.2
*   **Mermaid 连线标签保护**: 实现了全面的连线标签保护机制，防止连接线上的文字被误修改。现在支持所有 Mermaid 连线类型，包括实线 (`--`)、虚线 (`-.`) 和粗线 (`==`)，无论是否带有箭头。
*   **Bug 修复**: 修复了无箭头连线（如 `A -- text --- B`）未被正确保护的问题。

### v1.1.0
*   **Mermaid 修复优化**: 改进了正则表达式以处理节点标签中的嵌套括号（如 `ID("标签 (文本)")`），并避免误匹配连接线上的文字。
*   **HTML 保护机制优化**: 优化了 `_contains_html` 检测，允许 `<br/>`, `<b>`, `<i>` 等常见标签，确保包含这些标签的 Mermaid 图表能被正常规范化。
*   **全角符号清理**: 修复了 `FULLWIDTH_MAP` 中的重复键名和错误的引号映射。
*   **Bug 修复**: 修复了 Python 文件中缺失的 `Dict` 类型导入。

