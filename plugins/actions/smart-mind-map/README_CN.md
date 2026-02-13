# 思维导图 - 思维导图生成插件

思维导图是一个强大的 OpenWebUI 动作插件，能够智能分析长篇文本内容，自动生成交互式思维导图，帮助用户结构化和可视化知识。

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 0.9.2 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

## v0.9.2 更新亮点

**语言规则对齐**

- **输入语言优先**：导图输出严格与输入文本语言一致。
- **一致性提升**：与信息图语言规则保持一致，多语言输出更可预期。

## 核心特性 🔑

- ✅ **智能文本分析**：自动识别文本的核心主题、关键概念和层次结构。
- ✅ **交互式可视化**：基于 Markmap.js 生成美观的交互式思维导图。
- ✅ **高分辨率 PNG 导出**：导出高质量的 PNG 图片（9 倍分辨率）。
- ✅ **完整控制面板**：缩放控制、展开层级选择、全屏模式。
- ✅ **主题切换**：手动主题切换按钮与自动主题检测。
- ✅ **图片输出模式**：生成静态 SVG 图片直接嵌入 Markdown，聊天记录更简洁。

## 使用方法 🛠️

1. **安装**: 在 OpenWebUI 管理员设置 -> 插件 -> 动作中上传 `smart_mind_map_cn.py`。
2. **配置**: 确保配置了 LLM 模型（如 `gemini-2.5-flash`）。
3. **触发**: 在聊天设置中启用“思维导图”动作，并发送文本（至少 100 字符）。
4. **结果**: 思维导图将在聊天界面中直接渲染显示。

## 配置参数 (Valves) ⚙️

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `show_status` | `true` | 是否在聊天界面显示操作状态更新。 |
| `LLM_MODEL_ID` | `gemini-2.5-flash` | 用于文本分析的 LLM 模型 ID。 |
| `MIN_TEXT_LENGTH` | `100` | 进行思维导图分析所需的最小文本长度。 |
| `CLEAR_PREVIOUS_HTML` | `false` | 在生成新的思维导图时，是否清除之前的 HTML 内容。 |
| `MESSAGE_COUNT` | `1` | 用于生成思维导图的最近消息数量（1-5）。 |
| `OUTPUT_MODE` | `html` | 输出模式：`html`（交互式）或 `image`（静态图片）。 |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 故障排除 (Troubleshooting) ❓

- **插件无法启动**：检查 OpenWebUI 日志，确认插件已正确上传并启用。
- **文本内容过短**：确保输入的文本至少包含 100 个字符。
- **渲染失败**：检查浏览器控制台，确认 Markmap.js 和 D3.js 库是否正确加载。
- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

---

## 技术架构

- **Markmap.js**：开源的思维导图渲染引擎。
- **PNG 导出技术**：9 倍缩放因子，输出打印级质量。
- **主题检测机制**：4 级优先级检测（手动 > Meta > Class > 系统）。
- **安全性增强**：XSS 防护与输入验证。

## 最佳实践

1. **文本准备**：提供结构清晰、层次分明的文本内容。
2. **模型选择**：日常使用推荐 `gemini-2.5-flash` 等快速模型。
3. **导出质量**：PNG 适合演示分享，SVG 适合进一步矢量编辑。

## 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
