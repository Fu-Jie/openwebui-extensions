# OpenWebUI Extras

[English](./README.md) | 中文

OpenWebUI 增强功能集合。包含个人开发与收集的### 🧩 插件 (Plugins)

位于 `plugins/` 目录，包含各类 Python 编写的功能增强插件：

#### Actions (交互增强)
- **Smart Mind Map** (`smart-mind-map`): 智能分析文本并生成交互式思维导图。
- **Smart Infographic** (`infographic`): 基于 AntV 的智能信息图生成工具。
- **Knowledge Card** (`knowledge-card`): 快速生成精美的学习记忆卡片。
- **Export to Excel** (`export_to_excel`): 将对话内容导出为 Excel 文件。
- **Export to Word** (`export_to_docx`): 将对话内容导出为 Word 文档。
- **Summary** (`summary`): 文本摘要生成工具。

#### Filters (消息处理)
- **Async Context Compression** (`async-context-compression`): 异步上下文压缩，优化 Token 使用。
- **Context Enhancement** (`context_enhancement_filter`): 上下文增强过滤器。
- **Gemini Manifold Companion** (`gemini_manifold_companion`): Gemini Manifold 配套增强。


#### Pipes (模型管道)
- **Gemini Manifold** (`gemini_mainfold`): 集成 Gemini 模型的管道。

#### Pipelines (工作流管道)
- **MoE Prompt Refiner** (`moe_prompt_refiner`): 优化多模型 (MoE) 汇总请求的提示词，生成高质量的综合报告。

### 🎯 提示词 (Prompts)

位于 `prompts/` 目录，包含精心调优的 System Prompts：

- **Coding**: 编程辅助类提示词。
- **Marketing**: 营销文案类提示词。(`/prompts/marketing`): 内容创作、品牌策划、市场分析相关的提示词

每个提示词都独立保存为 Markdown 文件，可直接在 OpenWebUI 中使用。

### 🔧 插件 (Plugins)

{{ ... }}

[贡献指南](./CONTRIBUTING.md) | [更新日志](./CHANGELOG.md)

## 📦 项目内容

### 🎯 提示词 (Prompts)

位于 `/prompts` 目录，包含针对不同领域的优质提示词模板：

- **编程类** (`/prompts/coding`): 代码生成、调试、优化相关的提示词
- **营销类** (`/prompts/marketing`): 内容创作、品牌策划、市场分析相关的提示词

每个提示词都独立保存为 Markdown 文件，可直接在 OpenWebUI 中使用。

### 🔧 插件 (Plugins)

位于 `/plugins` 目录，提供三种类型的插件扩展：

- **过滤器 (Filters)** - 在用户输入发送给 LLM 前进行处理和优化
  - 异步上下文压缩：智能压缩长上下文，优化 token 使用效率

- **动作 (Actions)** - 自定义功能，从聊天中触发
  - 思维导图生成：快速生成和导出思维导图

- **管道 (Pipes)** - 对 LLM 响应进行处理和增强
  - 各类响应处理和格式化插件

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

1. 在 `/plugins` 目录中浏览并下载你需要的插件文件 (`.py`)。
2. 打开 OpenWebUI 的 **管理员面板 (Admin Panel)** -> **设置 (Settings)** -> **插件 (Plugins)**。
3. 点击上传按钮，选择刚才下载的 `.py` 文件。
4. 上传成功后，刷新页面，你就可以在聊天设置或工具栏中启用该插件了。

### 贡献代码

如果你有优质的提示词或插件想要分享：
1. Fork 本仓库。
2. 将你的文件添加到对应的 `prompts/` 或 `plugins/` 目录。
3. 提交 Pull Request。
