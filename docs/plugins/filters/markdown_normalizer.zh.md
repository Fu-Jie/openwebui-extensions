# Markdown 格式化过滤器 (Markdown Normalizer)

这是一个用于 Open WebUI 的生产级内容格式化过滤器，旨在修复 LLM 输出中常见的 Markdown 格式问题。它能确保代码块、LaTeX 公式、Mermaid 图表和其他 Markdown 元素被正确渲染。

## 功能特性

*   **Mermaid 语法修复**: 自动修复常见的 Mermaid 语法错误，如未加引号的节点标签（支持多行标签和引用标记）和未闭合的子图 (Subgraph)，确保图表能正确渲染。
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
*   `enable_escape_fix_in_code_blocks`: 在代码块内应用转义修复 (⚠️ 警告: 可能破坏 JSON 字符串或正则表达式等有效代码。默认: False 更安全)。
*   `enable_thought_tag_fix`: 规范化思维标签。
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

## 许可证

MIT
