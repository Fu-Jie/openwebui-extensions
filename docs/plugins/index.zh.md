# 插件中心

先按你要完成的结果来选插件，再进入完整目录查看更多候选项。这一页的目标不是把所有内容堆上来，而是帮你更快找到“现在最该先试哪个”。

> **推荐路径：** 先按目标找方向 → 打开对应说明页 → 再决定从 OpenWebUI Community 安装还是从仓库导入源码文件。

## 按目标选择

<div class="grid cards" markdown>

- :material-brush-variant:{ .lg .middle } **做可视化与表达**

    ---

    把原始聊天内容变成思维导图、信息图、闪记卡或结构化精读结果。

    **建议先看：** [Smart Mind Map](actions/smart-mind-map.zh.md)、[Smart Infographic](actions/smart-infographic.zh.md)、[Flash Card](actions/flash-card.zh.md)、[Deep Dive](actions/deep-dive.zh.md)

- :material-file-export:{ .lg .middle } **做导出与交付**

    ---

    把高价值对话导出成 Word、Excel 等更适合汇报、归档和交接的文件。

    **建议先看：** [Export to Word](actions/export-to-word.zh.md)、[Export to Excel](actions/export-to-excel.zh.md)

- :material-tune-variant:{ .lg .middle } **提升上下文与输出质量**

    ---

    压缩长对话、清理 Markdown、注入项目规则，并让模型在复杂场景下更稳定。

    **建议先看：** [Async Context Compression](filters/async-context-compression.zh.md)、[Markdown Normalizer](filters/markdown_normalizer.zh.md)、[Folder Memory](filters/folder-memory.zh.md)、[Context Enhancement](filters/context-enhancement.zh.md)

- :material-robot-excited-outline:{ .lg .middle } **搭建 Agent / Tool 工作流**

    ---

    为 OpenWebUI 加入更强的自主行为、工具复用和工作流式集成能力。

    **建议先看：** [GitHub Copilot SDK](pipes/github-copilot-sdk.zh.md)、[OpenWebUI Skills 管理工具](tools/openwebui-skills-manager-tool.zh.md)、[Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.zh.md)、[Smart Mind Map Tool](tools/smart-mind-map-tool.zh.md)

- :material-image-multiple:{ .lg .middle } **扩展模型能力**

    ---

    为模型增加多模态输入、原始文件可见性以及更强的上下文感知能力。

    **建议先看：** [Web Gemini Multimodal Filter](filters/web-gemini-multimodel.zh.md)、[Copilot SDK 文件过滤器](filters/github-copilot-sdk-files-filter.zh.md)、[Context Enhancement](filters/context-enhancement.zh.md)

</div>

---

## 精选起步组合

| 如果你想要... | 建议先装 | 为什么 |
| --- | --- | --- |
| 一个最容易带来“哇，这也行”的插件 | [GitHub Copilot SDK](pipes/github-copilot-sdk.zh.md) | 让 OpenWebUI 更像真正可协作、可复用工具的 Agent 工作台 |
| 快速把复杂内容讲清楚 | [Smart Mind Map](actions/smart-mind-map.zh.md) | 它通常是把复杂回答迅速变清晰的最高命中率选择 |
| 做展示级的信息表达 | [Smart Infographic](actions/smart-infographic.zh.md) | 能把原始文本转成更适合演示和汇报的视觉结果 |
| 给长对话做务实升级 | [Async Context Compression](filters/async-context-compression.zh.md) | 节省 token，同时让长会话更容易维护 |
| 输出可直接交付的文件 | [Export to Word](actions/export-to-word.zh.md) | 很适合报告、交接文档和可复用资料沉淀 |
| 更快试多个插件仓库 | [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.zh.md) | 显著减少试验阶段的重复安装成本 |

---

## 按类型浏览

<div class="grid cards" markdown>

- :material-gesture-tap:{ .lg .middle } **Actions**

    ---

    一键交互、导出、可视化和消息侧体验增强。

    [:octicons-arrow-right-24: 浏览 Actions](actions/index.zh.md)

- :material-filter:{ .lg .middle } **Filters**

    ---

    上下文处理、格式清理、质量控制与消息链路增强。

    [:octicons-arrow-right-24: 浏览 Filters](filters/index.zh.md)

- :material-pipe:{ .lg .middle } **Pipes**

    ---

    模型集成与更偏 Agent 风格的运行时工作流。

    [:octicons-arrow-right-24: 浏览 Pipes](pipes/index.zh.md)

- :material-tools:{ .lg .middle } **Tools**

    ---

    可跨模型复用的原生 Tool 插件，适合工作流拼装与能力调用。

    [:octicons-arrow-right-24: 浏览 Tools](tools/index.zh.md)

- :material-pipe-wrench:{ .lg .middle } **Pipelines / 参考项**

    ---

    历史或实验性的编排型工作流参考。

    [:octicons-arrow-right-24: 浏览 Pipelines](pipelines/index.zh.md)

</div>

---

## 当前有源码支撑的目录

| 插件 | 类型 | 最适合 |
| --- | --- | --- |
| [Smart Mind Map](actions/smart-mind-map.zh.md) | Action | 把对话转成交互式思维导图 |
| [Smart Infographic](actions/smart-infographic.zh.md) | Action | 把原始文本升级成展示级信息图 |
| [Flash Card](actions/flash-card.zh.md) | Action | 学习卡片与记忆型摘要 |
| [Export to Excel](actions/export-to-excel.zh.md) | Action | 导出聊天数据到电子表格 |
| [Export to Word](actions/export-to-word.zh.md) | Action | 输出高保真的 Word 交付文档 |
| [Deep Dive](actions/deep-dive.zh.md) | Action | 按背景 → 逻辑 → 洞察做结构化精读 |
| [Async Context Compression](filters/async-context-compression.zh.md) | Filter | 长对话压缩与 token 节省 |
| [Context Enhancement](filters/context-enhancement.zh.md) | Filter | 在生成前注入更有帮助的上下文 |
| [Folder Memory](filters/folder-memory.zh.md) | Filter | 从文件夹对话中提炼并复用项目规则 |
| [Markdown Normalizer](filters/markdown_normalizer.zh.md) | Filter | 修复 Mermaid、LaTeX、代码块和 Markdown 格式问题 |
| [Web Gemini Multimodal Filter](filters/web-gemini-multimodel.zh.md) | Filter | 为兼容工作流增加多模态输入能力 |
| [Copilot SDK 文件过滤器](filters/github-copilot-sdk-files-filter.zh.md) | Filter | 把原始仓库文件直接交给 Copilot SDK Agent |
| [GitHub Copilot SDK](pipes/github-copilot-sdk.zh.md) | Pipe | 自主 Agent 工作流与工具复用 |
| [Smart Mind Map Tool](tools/smart-mind-map-tool.zh.md) | Tool | 跨模型复用的思维导图生成能力 |
| [OpenWebUI Skills 管理工具](tools/openwebui-skills-manager-tool.zh.md) | Tool | 安装、管理与维护工作区 Skills |
| [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.zh.md) | Tool | 更快接入多个插件仓库 |

---

## Repo-only 条目

| 插件 | 类型 | 说明 |
| --- | --- | --- |
| [iFlow Official SDK Pipe](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/pipes/iflow-sdk-pipe) | Pipe | 仓库内已有源码和本地 README，但暂时没有镜像到文档站 |
| [Chat Session Mapping Filter](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/chat-session-mapping-filter) | Filter | 一个轻量的会话映射辅助过滤器，目前主要通过仓库入口发现 |

> **说明：** 像 **Multi-Model Context Merger**、**MoE Prompt Refiner** 这样的历史 / docs-only 参考内容仍然保留在分类索引页中。当前页面优先呈现“现在有源码支撑”以及“当前能从 repo 发现”的条目。

---

## 安装路径

1. **OpenWebUI Community（推荐）** — 直接从 [Fu-Jie 的主页](https://openwebui.com/u/Fu-Jie) 安装
2. **文档页 + 仓库源码** — 先阅读说明页，再手动上传对应 `.py` 文件
3. **批量安装 / 快速搭环境** — 使用 [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.zh.md) 或本地执行 `python scripts/install_all_plugins.py`
