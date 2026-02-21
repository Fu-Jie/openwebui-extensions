# 思维导图 - 思维导图生成插件

思维导图是一个强大的 OpenWebUI 动作插件，能够智能分析长篇文本内容，自动生成交互式思维导图，帮助用户结构化和可视化知识。

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 1.0.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

## v1.0.0 最新更新

### 嵌入式直出与 UI 细节全线重构

- **原生多语言界面 (Native i18n)**：插件界面（按钮、设置说明、状态提示）现在会根据您浏览器的语言设置自动适配系统语言。
- **原生态嵌入模式 (Direct Embed)**：针对 Open WebUI 0.8.0+ 的前端架构支持了纯正的内容内联（Inline）直出模式，不再受气泡和 Markdown 隔离，真正撑满屏幕宽度。
- **自动响应边界 (Auto-Sizing)**：突破以前高度僵死的问题。思维导图现在可以根据您的当前屏幕大小弹性伸缩（动态 `clamp()` 高度），彻底消灭丑陋的局部滚动条与白边。
- **极简专业 UI (Compact UI)**：推倒重做了头部的菜单栏，统一使用了一套干净、单行的极简全透明微拟物 Toolbar 设计，为导图画布省下极大的垂直空间。
- **模式配置自由**：为了照顾阅读流连贯的习惯，新增了 `ENABLE_DIRECT_EMBED_MODE` 配置开关。您必须在设置中显式开启才能体验宽广内联全屏模式。

## 核心特性 🔑

- ✅ **智能文本分析**：自动识别文本的核心主题、关键概念和层次结构。
- ✅ **原生多语言界面**：根据系统语言自动切换界面语言 (i18n)，提供原生交互体验。
- ✅ **交互式可视化**：基于 Markmap.js 生成美观的交互式思维导图。
- ✅ **直出全景内嵌 (Direct Embed)**：(可选开关) 对于 Open WebUI 0.8.0+，直接填补整个前端宽度，去除气泡剥离感。
- ✅ **高分辨率 PNG 导出**：导出高质量的 PNG 图片（9 倍分辨率）。
- ✅ **完整控制面板**：极简清爽的单行大屏缩放控制、展开层级选择、全局全屏等核心操作。
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
| `ENABLE_DIRECT_EMBED_MODE` | `false` | 是否开启沉浸式直出嵌入模式（需要 Open WebUI v0.8.0+ 环境）。如果保持 `false` 将会维持旧版的对话流 Markdown 渲染模式。 |

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
