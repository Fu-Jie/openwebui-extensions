# 插件中心

欢迎来到 OpenWebUI Extras 插件中心！在这里你可以找到完整的插件集合，帮助你强化 OpenWebUI 的体验。

## 插件类型

OpenWebUI 支持四种类型的插件，每种都有不同的用途：

<div class="grid cards" markdown>

-   :material-gesture-tap:{ .lg .middle } **Actions（动作）**

    ---

    在消息下方添加自定义按钮，一键触发思维导图、数据导出或可视化等操作。

    [:octicons-arrow-right-24: 浏览 Actions](actions/index.md)

-   :material-filter:{ .lg .middle } **Filters（过滤器）**

    ---

    在请求到达 LLM 之前或响应生成之后处理和修改消息，适合做上下文增强和压缩。

    [:octicons-arrow-right-24: 浏览 Filters](filters/index.md)

-   :material-pipe:{ .lg .middle } **Pipes（管道）**

    ---

    创建自定义模型集成或转换 LLM 响应，可连接外部 API 或自定义模型逻辑。

    [:octicons-arrow-right-24: 浏览 Pipes](pipes/index.md)

-   :material-pipe-wrench:{ .lg .middle } **Pipelines（流水线）**

    ---

    将多步处理组合为复杂工作流，适合需要多阶段转换的高级场景。

    [:octicons-arrow-right-24: 浏览 Pipelines](pipelines/index.md)

</div>

---

## 插件总览

| 插件 | 类型 | 描述 | 版本 |
|--------|------|-------------|---------|
| [Smart Mind Map（智能思维导图）](actions/smart-mind-map.md) | Action | 从文本生成交互式思维导图 | 0.8.0 |
| [Smart Infographic（智能信息图）](actions/smart-infographic.md) | Action | 将文本转成专业信息图 | 1.0.0 |
| [Knowledge Card（知识卡片）](actions/knowledge-card.md) | Action | 生成精美学习卡片 | 0.2.0 |
| [Export to Excel（导出到 Excel）](actions/export-to-excel.md) | Action | 导出聊天记录为 Excel | 1.0.0 |
| [Export to Word（导出为 Word）](actions/export-to-word.md) | Action | 将聊天内容导出为 Word (.docx) 并保留格式 | 0.1.0 |
| [Summary（摘要）](actions/summary.md) | Action | 文本摘要工具 | 1.0.0 |
| [Async Context Compression（异步上下文压缩）](filters/async-context-compression.md) | Filter | 智能上下文压缩 | 1.0.0 |
| [Context Enhancement（上下文增强）](filters/context-enhancement.md) | Filter | 提升对话上下文 | 1.0.0 |
| [Gemini Manifold Companion](filters/gemini-manifold-companion.md) | Filter | Gemini Manifold 伴侣 | 1.0.0 |
| [Gemini Manifold](pipes/gemini-manifold.md) | Pipe | Gemini 模型集成 | 1.0.0 |
| [MoE Prompt Refiner](pipelines/moe-prompt-refiner.md) | Pipeline | 多模型提示词优化 | 1.0.0 |

---

## 安装指南

### 步骤 1：下载插件

点击上方任意插件，查看文档并下载对应的 `.py` 文件。

### 步骤 2：上传到 OpenWebUI

1. 打开 OpenWebUI，进入 **Admin Panel** → **Settings** → **Functions**
2. 点击 **+** 按钮添加新的 Function
3. 上传下载好的 `.py` 文件
4. 配置必要的设置（如 API Key、选项等）

### 步骤 3：启用并使用

1. 上传后刷新页面
2. **Actions**：在消息操作栏中找到插件按钮
3. **Filters**：在聊天设置或全局启用
4. **Pipes**：在模型下拉中选择自定义模型
5. **Pipelines**：在流水线设置中配置并启用

---

## 兼容性提示

!!! info "OpenWebUI 版本"
    本仓库的大多数插件面向 **OpenWebUI v0.3.0** 及以上版本。具体要求请查看各插件文档。

!!! warning "依赖说明"
    部分插件可能需要额外的 Python 依赖，请查看对应插件文档确认。
