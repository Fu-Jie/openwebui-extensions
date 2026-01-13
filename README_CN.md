# OpenWebUI Extras

[English](./README.md) | 中文

OpenWebUI 增强功能集合。包含个人开发与收集的插件、提示词等资源。

<!-- STATS_START -->
## 📊 社区统计

> 🕐 自动更新于 2026-01-13 10:45

| 👤 作者 | 👥 粉丝 | ⭐ 积分 | 🏆 贡献 |
|:---:|:---:|:---:|:---:|
| [Fu-Jie](https://openwebui.com/u/Fu-Jie) | **94** | **99** | **23** |

| 📝 发布 | ⬇️ 下载 | 👁️ 浏览 | 👍 点赞 | 💾 收藏 |
|:---:|:---:|:---:|:---:|:---:|
| **15** | **1272** | **14208** | **88** | **90** |

### 🔥 热门插件 Top 6

> 🕐 自动更新于 2026-01-13 10:45

| 排名 | 插件 | 版本 | 下载 | 浏览 | 更新日期 |
|:---:|------|:---:|:---:|:---:|:---:|
| 🥇 | [Smart Mind Map](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a) | 0.9.1 | 403 | 3631 | 2026-01-07 |
| 🥈 | [Export to Excel](https://openwebui.com/posts/export_mulit_table_to_excel_244b8f9d) | 0.3.7 | 189 | 613 | 2026-01-07 |
| 🥉 | [📊 Smart Infographic (AntV)](https://openwebui.com/posts/smart_infographic_ad6f0c7f) | 1.4.9 | 153 | 1656 | 2026-01-11 |
| 4️⃣ | [Async Context Compression](https://openwebui.com/posts/async_context_compression_b1655bc8) | 1.1.3 | 145 | 1615 | 2026-01-11 |
| 5️⃣ | [Export to Word (Enhanced)](https://openwebui.com/posts/export_to_word_enhanced_formatting_fca6a315) | 0.4.3 | 107 | 961 | 2026-01-07 |
| 6️⃣ | [Flash Card](https://openwebui.com/posts/flash_card_65a2ea8f) | 0.2.4 | 106 | 1925 | 2026-01-07 |

*完整统计请查看 [社区统计报告](./docs/community-stats.zh.md)*
<!-- STATS_END -->

## 📦 项目内容

### 🧩 插件 (Plugins)

位于 `plugins/` 目录，包含各类 Python 编写的功能增强插件：

#### Actions (交互增强)
- **Smart Mind Map** (`smart-mind-map`): 智能分析文本并生成交互式思维导图。
- **Smart Infographic** (`infographic`): 基于 AntV 的智能信息图生成工具。
- **Flash Card** (`flash-card`): 快速生成精美的学习记忆卡片。
- **Deep Dive** (`deep-dive`): 深度思考透镜，从背景、逻辑、洞察到行动路径的全方位分析。
- **Export to Excel** (`export_to_excel`): 将对话内容导出为 Excel 文件。
- **Export to Word** (`export_to_docx`): 将对话内容导出为 Word 文档。

#### Filters (消息处理)
- **Async Context Compression** (`async-context-compression`): 异步上下文压缩，优化 Token 使用。
- **Context Enhancement** (`context_enhancement_filter`): 上下文增强过滤器。
- **Gemini Manifold Companion** (`gemini_manifold_companion`): Gemini Manifold 配套增强。
- **Gemini Multimodal Filter** (`web_gemini_multimodel_filter`): 为任意模型提供多模态能力（PDF、Office、视频等），支持智能路由和字幕精修。
- **Markdown Normalizer** (`markdown_normalizer`): 修复 LLM 输出中常见的 Markdown 格式问题。
- **Multi-Model Context Merger** (`multi_model_context_merger`): 自动合并并注入多模型回答的上下文。

#### Pipes (模型管道)
- **Gemini Manifold** (`gemini_mainfold`): 集成 Gemini 模型的管道。

#### Pipelines (工作流管道)
- **MoE Prompt Refiner** (`moe_prompt_refiner`): 优化多模型 (MoE) 汇总请求的提示词，生成高质量的综合报告。

### 🎯 提示词 (Prompts)

位于 `prompts/` 目录，包含精心调优的 System Prompts：

- **Coding**: 编程辅助类提示词。
- **Marketing**: 营销文案类提示词。

每个提示词都独立保存为 Markdown 文件，可直接在 OpenWebUI 中使用。

## 📖 开发文档

位于 `docs/zh/` 目录：

- **[插件开发权威指南](./docs/zh/plugin_development_guide.md)** - 整合了入门教程、核心 SDK 详解及最佳实践的系统化指南。 ⭐
- **[从问一个AI到运营一支AI团队](./docs/zh/从问一个AI到运营一支AI团队.md)** - 深度运营经验分享。

更多示例请查看 `docs/examples/` 目录。

## 🚀 快速开始

本项目是一个资源集合，无需安装 Python 环境。你只需要下载对应的文件并导入到你的 OpenWebUI 实例中即可。

### 使用提示词 (Prompts)

1. 在 `/prompts` 目录中浏览并选择你感兴趣的提示词文件 (`.md`)。
2. 复制文件内容。
3. 在 OpenWebUI 聊天界面中，点击输入框上方的 "Prompt" 按钮。
4. 粘贴内容并保存。

### 使用插件 (Plugins)

1. **从 OpenWebUI 社区安装 (推荐)**:
   - 访问我的主页: [Fu-Jie's Profile](https://openwebui.com/u/Fu-Jie)
   - 浏览插件列表，选择你喜欢的插件。
   - 点击 "Get" 按钮，将其直接导入到你的 OpenWebUI 实例中。

2. **手动安装**:
   - 在 `/plugins` 目录中浏览并下载你需要的插件文件 (`.py`)。
   - 打开 OpenWebUI 的 **管理员面板 (Admin Panel)** -> **设置 (Settings)** -> **插件 (Plugins)**。
   - 点击上传按钮，选择刚才下载的 `.py` 文件。
   - 上传成功后，刷新页面，你就可以在聊天设置或工具栏中启用该插件了。

### 贡献代码

如果你有优质的提示词或插件想要分享：
1. Fork 本仓库。
2. 将你的文件添加到对应的 `prompts/` 或 `plugins/` 目录。
3. 提交 Pull Request。

[贡献指南](./CONTRIBUTING_CN.md) | [更新日志](./CHANGELOG.md)
