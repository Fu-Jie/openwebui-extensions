# 📊 智能信息图 (AntV Infographic)

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 1.4.9 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)

基于 AntV Infographic 引擎的 Open WebUI 插件，能够将长文本内容一键转换为专业、美观的信息图表。

## 🔥 v1.4.9 更新日志

- 🎨 **70+ 官方模板**：全面集成 AntV 官方信息图模板库。
- 🖼️ **图标与插图支持**：支持 Iconify 图标库与 unDraw 插图库，视觉效果更丰富。
- 📏 **视觉优化**：改进文本换行逻辑，优化自适应尺寸，提升卡片布局精细度。
- ✨ **PNG 上传**：信息图现在以 PNG 格式上传，与 Word 导出完美兼容。
- 🔧 **Canvas 转换**：使用浏览器 Canvas 高质量转换 SVG 为 PNG（2倍缩放）。

### 此前: v1.4.0

- ✨ **默认模式变更**：默认输出模式调整为 `image`（静态图片）。
- 📱 **响应式尺寸**：图片模式下自动适应聊天容器宽度。

## ✨ 核心特性

- 🚀 **智能转换**：自动分析文本核心逻辑，提取关键点并生成结构化图表。
- 🎨 **70+ 专业模板**：内置多种 AntV 官方模板，包括列表、树图、路线图、时间线、对比图、SWOT、象限图及统计图表等。
- 🔍 **自动图标匹配**：内置图标搜索逻辑，支持 Iconify 图标和 unDraw 插图自动匹配。
- 📥 **多格式导出**：支持一键下载为 **SVG**、**PNG** 或 **独立 HTML** 文件。
- 🌈 **高度自定义**：支持深色/浅色模式，自动适配主题颜色，主标题加粗突出，卡片布局精美。
- 📱 **响应式设计**：生成的图表在桌面端和移动端均有良好的展示效果。

## 🚀 使用方法

1. **安装插件**：在 Open WebUI 插件市场搜索并安装。
2. **触发生成**：在对话框中输入一段长文本，点击输入框旁边的 **Action 按钮**（📊 图标）。
3. **AI 处理**：AI 会自动分析文本并生成对应的信息图语法。
4. **预览与下载**：在渲染区域预览效果，满意后点击下方的下载按钮保存。

## ⚙️ 配置参数 (Valves)

在插件设置界面，你可以调整以下参数来优化生成效果：

| 参数名称 | 默认值 | 说明 |
| :--- | :--- | :--- |
| **显示状态 (SHOW_STATUS)** | `True` | 是否在聊天界面实时显示 AI 分析和生成的进度状态。 |
| **模型 ID (MODEL_ID)** | `空` | 指定用于文本分析的 LLM 模型。留空则默认使用当前对话的模型。 |
| **最小文本长度 (MIN_TEXT_LENGTH)** | `100` | 触发分析所需的最小字符数，防止对过短的对话误操作。 |
| **清除旧结果 (CLEAR_PREVIOUS_HTML)** | `False` | 每次生成是否清除之前的图表。若为 `False`，新图表将追加在下方。 |
| **上下文消息数 (MESSAGE_COUNT)** | `1` | 用于分析的最近消息条数。增加此值可让 AI 参考更多对话背景。 |
| **输出模式 (OUTPUT_MODE)** | `image` | `image` 为静态图片嵌入（默认，兼容性好），`html` 为交互式图表。 |

## 🛠️ 支持的模板类型

| 分类 | 模板名称 | 适用场景 |
| :--- | :--- | :--- |
| **时序与流程** | `sequence-timeline-simple`, `sequence-roadmap-vertical-simple`, `sequence-snake-steps-compact-card` | 时间线、路线图、步骤说明 |
| **列表与网格** | `list-grid-candy-card-lite`, `list-row-horizontal-icon-arrow`, `list-column-simple-vertical-arrow` | 功能亮点、要点列举、清单 |
| **对比与分析** | `compare-binary-horizontal-underline-text-vs`, `compare-swot`, `quadrant-quarter-simple-card` | 优劣势对比、SWOT 分析、象限图 |
| **层级与结构** | `hierarchy-tree-tech-style-capsule-item`, `hierarchy-structure` | 组织架构、层级关系 |
| **图表与数据** | `chart-column-simple`, `chart-bar-plain-text`, `chart-line-plain-text`, `chart-wordcloud` | 数据趋势、比例分布、数值对比 |

## 📝 语法示例 (高级用户)

你也可以直接输入以下语法让 AI 渲染：

```infographic
infographic list-grid
data
  title 🚀 插件优势
  desc 为什么选择智能信息图插件
  items
    - label 极速生成
      desc 秒级完成文本到图表的转换
    - label 视觉精美
      desc 采用 AntV 专业设计规范
```
