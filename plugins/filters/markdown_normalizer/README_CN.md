# Markdown 格式化过滤器 (Markdown Normalizer)

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 1.2.7 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

这是一个用于 Open WebUI 的内容格式化过滤器，旨在修复 LLM 输出中常见的 Markdown 格式问题。它能确保代码块、LaTeX 公式、Mermaid 图表和其他 Markdown 元素被正确渲染。

> 🏆 **OpenWebUI 官方推荐** — 本插件获得 OpenWebUI 社区 Newsletter 官方推荐：[2026 年 1 月 28 日](https://openwebui.com/blog/newsletter-january-28-2026) · [2026 年 2 月 3 日](https://openwebui.com/blog/open-webui-community-newsletter-february-3rd-2026)

## 🔥 最新更新 v1.2.7

* **LaTeX 公式保护**: 增强了转义字符清理逻辑，自动保护 `$ $` 或 `$$ $$` 内的 LaTeX 命令（如 `\times`、`\nu`、`\theta`），防止渲染失效。
* **扩展国际化 (i18n) 支持**: 现已支持 12 种语言，具备自动探测与回退机制。
* **配置项优化**: 将 Valves 配置项的描述统一为英文，保持界面一致性。
* **修复 Bug**: 
    * 修复了 [Issue #49](https://github.com/Fu-Jie/openwebui-extensions/issues/49)：解决了当同一行存在多个加粗部分时，由于正则匹配过于贪婪导致中间内容丢失空格的问题。
    * 修复了插件代码中的 `NameError` 错误，确保测试脚本能正常运行。

## 🌐 多语言支持 (i18n)

支持以下语言的界面与状态自动切换：
`English`, `简体中文`, `繁體中文 (香港)`, `繁體中文 (台灣)`, `한국어`, `日本語`, `Français`, `Deutsch`, `Español`, `Italiano`, `Tiếng Việt`, `Bahasa Indonesia`

## ✨ 核心特性

* **Details 标签规范化**: 确保 `<details>` 标签（常用于思维链）有正确的间距。在 `</details>` 后添加空行，并在自闭合 `<details />` 标签后添加换行，防止渲染问题。
* **强调空格修复**: 修复强调标记内部的多余空格（例如 `** 文本 **` -> `**文本**`），这会导致 Markdown 渲染失败。包含保护机制，防止误修改数学表达式（如 `2 * 3 * 4`）或列表变量。
* **Mermaid 语法修复**: 自动修复常见的 Mermaid 语法错误，如未加引号的节点标签（支持多行标签和引用标记）和未闭合的子图 (Subgraph)。**v1.1.2 新增**: 全面保护各种类型的连线标签（实线、虚线、粗线），防止被误修改。
* **前端控制台调试**: 支持将结构化的调试日志直接打印到浏览器控制台 (F12)，方便排查问题。
* **代码块格式化**: 修复破损的代码块前缀、后缀和缩进问题。
* **LaTeX 规范化**: 标准化 LaTeX 公式定界符 (`\[` -> `$$`, `\(` -> `$`)。
* **思维标签规范化**: 统一思维链标签 (`<think>`, `<thinking>` -> `<thought>`)。
* **转义字符修复**: 清理过度的转义字符 (`\\n`, `\\t`)。
* **列表格式化**: 确保列表项有正确的换行。
* **标题修复**: 修复标题中缺失的空格 (`#标题` -> `# 标题`)。
* **表格修复**: 修复表格中缺失的闭合管道符。
* **XML 清理**: 移除残留的 XML 标签。

## 使用方法

1. 在 Open WebUI 中安装此插件。
2. 全局启用或为特定模型启用此过滤器。
3. 在 **Valves** 设置中配置需要启用的修复项。
4. (可选) **显示调试日志 (Show Debug Log)** 在 Valves 中默认开启。这会将结构化的日志打印到浏览器控制台 (F12)。
    > [!WARNING]
    > 由于这是初版，可能会出现“负向修复”的情况（例如破坏了原本正确的格式）。如果您遇到问题，请务必查看控制台日志，复制“原始 (Original)”与“规范化 (Normalized)”的内容对比，并提交 Issue 反馈。

## 配置参数 (Valves) ⚙️

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `priority` | `50` | 过滤器优先级。数值越大越靠后（建议在其他过滤器之后运行）。 |
| `enable_escape_fix` | `True` | 修复过度的转义字符（`\n`, `\t` 等）。 |
| `enable_escape_fix_in_code_blocks` | `False` | 在代码块内应用转义修复（可能影响有效代码）。 |
| `enable_thought_tag_fix` | `True` | 规范化思维标签（`</thought>`）。 |
| `enable_details_tag_fix` | `True` | 规范化 `<details>` 标签并添加安全间距。 |
| `enable_code_block_fix` | `True` | 修复代码块格式（缩进/换行）。 |
| `enable_latex_fix` | `True` | 规范化 LaTeX 定界符（`\[` -> `$$`, `\(` -> `$`）。 |
| `enable_list_fix` | `False` | 修复列表项换行（实验性）。 |
| `enable_unclosed_block_fix` | `True` | 自动闭合未闭合的代码块。 |
| `enable_fullwidth_symbol_fix` | `False` | 修复代码块中的全角符号。 |
| `enable_mermaid_fix` | `True` | 修复常见 Mermaid 语法错误。 |
| `enable_heading_fix` | `True` | 修复标题中缺失的空格。 |
| `enable_table_fix` | `True` | 修复表格中缺失的闭合管道符。 |
| `enable_xml_tag_cleanup` | `True` | 清理残留的 XML 标签。 |
| `enable_emphasis_spacing_fix` | `False` | 修复强调语法中的多余空格。 |
| `show_status` | `True` | 应用修复时显示状态通知。 |
| `show_debug_log` | `True` | 在浏览器控制台打印调试日志。 |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 其他

### 故障排除 (Troubleshooting) ❓

* **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

### 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
