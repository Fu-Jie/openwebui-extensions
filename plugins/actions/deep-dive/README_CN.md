# 📖 精读

| 作者：[Fu-Jie](https://github.com/Fu-Jie) · v1.0.0 | [⭐ 点个 Star 支持项目](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

全方位的思维透镜 —— 从背景全景到逻辑脉络，从深度洞察到行动路径。

## 使用 Batch Install Plugins 安装

如果你已经安装了 [Batch Install Plugins from GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins)，可以用下面这句来安装或更新当前插件：

```text
从 Fu-Jie/openwebui-extensions 安装插件
```

当选择弹窗打开后，搜索当前插件，勾选后继续安装即可。

> [!IMPORTANT]
> 如果你已经安装了 OpenWebUI 官方社区里的同名版本，请先删除旧版本，否则重新安装时可能报错。删除后，Batch Install Plugins 后续就可以继续负责更新这个插件。

## 🔥 v1.0.0 更新内容

- ✨ **思维链结构**: 从表面理解一步步深入到战略行动。
- 🔍 **阶段 01: 全景 (The Context)**: 提供情境与背景的高层级全景视图。
- 🧠 **阶段 02: 脉络 (The Logic)**: 解构底层推理逻辑与思维模型。
- 💎 **阶段 03: 洞察 (The Insight)**: 提取非显性价值与隐藏的深层含义。
- 🚀 **阶段 04: 路径 (The Path)**: 定义具体的、按优先级排列的战略方向。
- 🎨 **高端 UI**: 现代化的过程导向设计，带有"思维导火索"时间轴。
- 🌗 **主题自适应**: 自动适配 OpenWebUI 的深色/浅色主题。

## ✨ 核心特性

- 📖 **深度思考**: 不仅仅是摘要，而是对内容的全面解构。
- 🧠 **逻辑分析**: 揭示论点是如何构建的，识别隐藏的假设。
- 💎 **价值提取**: 发现"原来如此"的时刻与思维盲点。
- 🚀 **行动导向**: 将深度理解转化为立即、可执行的步骤。
- 🌍 **多语言支持**: 自动适配用户的偏好语言。
- 🌗 **主题支持**: 根据 OpenWebUI 设置自动切换深色/浅色主题。

## 🚀 如何使用

1. **输入内容**: 在聊天中提供任何文本、文章或会议记录。
2. **触发精读**: 点击 **精读** 操作按钮。
3. **探索思维链**: 沿着视觉时间轴从"全景"探索到"路径"。

## ⚙️ 配置参数 (Valves)

| 参数 | 默认值 | 描述 |
| :--- | :--- | :--- |
| **显示状态 (SHOW_STATUS)** | `True` | 是否在思维过程中显示状态更新。 |
| **模型 ID (MODEL_ID)** | `空` | 用于分析的 LLM 模型。留空 = 使用当前模型。 |
| **最小文本长度 (MIN_TEXT_LENGTH)** | `200` | 进行有意义的精读所需的最小字符数。 |
| **清除旧 HTML (CLEAR_PREVIOUS_HTML)** | `True` | 是否清除之前的插件结果。 |
| **消息数量 (MESSAGE_COUNT)** | `1` | 要分析的最近消息数量。 |

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 🌗 主题支持

插件会自动检测并适配 OpenWebUI 的主题设置：

- **检测优先级**:
  1. 父文档 `<meta name="theme-color">` 标签
  2. 父文档 `html/body` 的 class 或 `data-theme` 属性
  3. 系统偏好 `prefers-color-scheme: dark`

- **环境要求**: 为获得最佳效果，请在 OpenWebUI 中启用 **iframe Sandbox Allow Same Origin**：
  - 进入 **设置** → **界面** → **Artifacts** → 勾选 **iframe Sandbox Allow Same Origin**

## 🎨 视觉预览

插件生成结构化的思维时间轴：

```
┌─────────────────────────────────────┐
│  📖 精读分析报告                     │
│  👤 用户  📅 日期  📊 字数           │
├─────────────────────────────────────┤
│  🔍 阶段 01: 全景 (The Context)      │
│  [高层级全景视图内容]                 │
│                                     │
│  🧠 阶段 02: 脉络 (The Logic)        │
│  • 推理结构分析...                   │
│  • 隐藏假设识别...                   │
│                                     │
│  💎 阶段 03: 洞察 (The Insight)      │
│  • 非显性价值提取...                 │
│  • 思维盲点揭示...                   │
│                                     │
│  🚀 阶段 04: 路径 (The Path)         │
│  ▸ 优先级行动 1...                   │
│  ▸ 优先级行动 2...                   │
└─────────────────────────────────────┘
```

## 📂 文件说明

- `deep_dive.py` - 英文版 (Deep Dive)
- `deep_dive_cn.py` - 中文版 (精读)

## 故障排除 (Troubleshooting) ❓

- **插件不工作？**: 请检查是否在模型设置中启用了该过滤器/动作。
- **调试日志**: 在 Valves 中启用 `SHOW_STATUS` 以查看进度更新。
- **错误信息**: 如果看到错误，请复制完整的错误信息并报告。
- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
