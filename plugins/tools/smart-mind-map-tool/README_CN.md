# 思维导图工具 - 知识可视化与结构化利器

思维导图工具（Smart Mind Map Tool）是广受好评的“思维导图”插件的工具（Tool）版本。它赋予了模型主动生成交互式思维导图的能力，通过智能分析上下文，将碎片化知识转化为层级分明的视觉架构。

| 作者：[Fu-Jie](https://github.com/Fu-Jie) · v1.0.0 | [⭐ 点个 Star 支持项目](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-0%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%A7%A9&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

> 💡 **说明**：如果您更倾向于手动点击按钮触发生成，可以获取 [思维导图 Action（动作）版本](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a)。

---

## 🚀 为什么会有工具（Tool）版本？

1. **得益于 OpenWebUI 0.8.0 的 Rich UI 特性**：在以前的版本中，是不支持直接将自定义的 HTML/iframe 嵌入到对话流中的。而从 0.8.0 开始，平台不仅支持了这种顺滑的前端组件直出（Rich UI），而且同时对 **Action** 和 **Tool** 开放了该能力。
2. **AI 自主调用（区别于 Action）**：**Action** 是被动的，需要用户在输入框或消息旁手动点击触发；而 **Tool** 赋予了模型**自主权**。AI 可以根据对话上下文，自行判断在什么时候为您生成导图最有帮助，实现真正的“智能助理”体验。

它非常适合以下场景：

- 总结复杂的对话内容。
- 规划项目、整理文章大纲。
- 解释具有层级结构的抽象概念。

## ✨ 核心特性

- ✅ **主动触发生成**：AI 在感知到需要视觉化展示时会自动调用工具生成导图。
- ✅ **全量上下文感知**：支持聚合整个会话历史（MESSAGE_COUNT 为 0），生成最完整的知识地图。
- ✅ **原生多语言 UI (i18n)**：自动检测并适配浏览器/系统语言（简体中文、繁体中文、英文、日文、韩文等）。
- ✅ **统一的高级视觉**：完全复刻 Action 版本的极简工具栏、玻璃拟态审美以及专业边框阴影。
- ✅ **深度交互控制**：支持缩放（放大/缩小/重置）、层级调节（默认为 3 级展开）以及全屏模式。
- ✅ **高品质导出**：支持将导图导出为超高清 PNG 图片。

## 🛠️ 安装与设置

1. **安装**：在 OpenWebUI 管理员设置 -> 插件 -> 工具中上传 `smart_mind_map_tool.py`。
2. **启用原生理机制**：在“管理员设置 -> 模型”或配置里，确保目标模型**启用了原生工具调用（Native Tool Calling）**。只有开启这个能力，AI 才能自主并稳定地触发 Tool 功能。
3. **分配工具**：在工作区或聊天界面处为目标模型选中并挂载本工具。
4. **配置**：
   - `MESSAGE_COUNT`：设置为 `12`（默认）以使用最近的 12 条对话记录，或设置为 `0` 聚合全部历史。
   - `MODEL_ID`：指定分析导图时偏好的模型（留空则默认使用当前模型）。

## ⚙️ 配置参数 (Valves)

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| `MODEL_ID` | (留空) | 用于文本分析的模型 ID。留空则随当前聊天模型。 |
| `MESSAGE_COUNT` | `12` | 聚合消息的数量。`0` 表示全量消息，`12` 表示截取最近的 12 条。 |
| `MIN_TEXT_LENGTH` | `100` | 触发导图分析所需的最小字符长度。 |

## ❓ 常见问题

- **语言显示不正确？**：工具采用 4 级探测机制（前端脚本 > 浏览器头 > 用户资料 > 默认）。请检查浏览器语言设置。
- **生成的导图太小或太大？**：我们针对对话流内联显示优化了 `500px` 的固定高度，并配有自适应缩放逻辑。
- **导出图片**：建议先点击“⛶”进入全屏，获得最佳构图后再点击导出。

---

## ⭐ 支持

如果这个工具帮您理清了思路，欢迎在 [GitHub](https://github.com/Fu-Jie/openwebui-extensions) 给我们一个 Star。

## ⚖️ 许可证

MIT License. Designed with ❤️ by Fu-Jie.
