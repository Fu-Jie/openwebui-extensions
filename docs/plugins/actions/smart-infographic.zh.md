# Smart Infographic（智能信息图）

<span class="category-badge action">Action</span>
<span class="version-badge">v1.4.0</span>

基于 AntV 信息图引擎，将长文本一键转成专业、美观的信息图。

---

## 概览

Smart Infographic 使用 AI 分析文本，并基于 AntV 可视化引擎生成专业的信息图。它会自动提取要点，并用合适的图表/结构呈现。

## 功能特性

- :material-robot: **AI 转换**：自动分析文本逻辑，提取要点并生成结构化图表
- :material-palette: **专业模板**：内置 AntV 官方模板：列表、树、思维导图、对比表、流程图、统计图等
- :material-magnify: **自动匹配图标**：根据内容自动选择最合适的 Material Design Icons
- :material-download: **多格式导出**：支持下载 **SVG**、**PNG**、**独立 HTML**
- :material-theme-light-dark: **主题支持**：适配深色/浅色模式
- :material-cellphone-link: **响应式**：桌面与移动端都能良好展示
- :material-image: **图片嵌入**：支持将图表作为静态图片嵌入，兼容性更好
- :material-monitor-screenshot: **自适应尺寸**：图片模式下自动适应聊天容器宽度

---

## 安装

1. 下载插件文件：[`infographic.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/infographic)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 可选：根据需要配置插件选项
4. 启用插件

---

## 支持的模板类型

| 分类 | 模板名称 | 典型场景 |
|:---------|:--------------|:---------|
| **列表与层级** | `list-grid`, `tree-vertical`, `mindmap` | 特性列表、组织结构、头脑风暴 |
| **序列与关系** | `sequence-roadmap`, `relation-circle` | 路线图、循环流程、步骤拆解 |
| **对比与分析** | `compare-binary`, `compare-swot`, `quadrant-quarter` | 优劣势、SWOT、象限分析 |
| **图表与数据** | `chart-bar`, `chart-line`, `chart-pie` | 趋势、分布、指标对比 |

---

## 使用方法

1. 在聊天中输入需要可视化的文本
2. 点击消息操作栏的 **Infographic**（📊）按钮
3. 等待 AI 分析并生成信息图
4. 预览结果，可用下载按钮保存

---

## 配置项

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `SHOW_STATUS` | boolean | `true` | 是否展示实时的分析/生成状态 |
| `MODEL_ID` | string | `""` | 指定用于分析的 LLM 模型，留空则使用当前会话模型 |
| `MIN_TEXT_LENGTH` | integer | `100` | 触发分析的最小字符数 |
| `CLEAR_PREVIOUS_HTML` | boolean | `false` | 是否清空之前生成的图表 |
| `MESSAGE_COUNT` | integer | `1` | 参与分析的最近消息条数 |
| `OUTPUT_MODE` | string | `image` | `image` 为静态图片嵌入（默认），`html` 为交互式图表 |

---

## 语法示例（高级用法）

也可以直接输入信息图语法进行渲染：

```infographic
infographic list-grid
data
  title 🚀 Plugin Benefits
  desc Why use the Smart Infographic plugin
  items
    - label Fast Generation
      desc Convert text to charts in seconds
    - label Beautiful Design
      desc Uses AntV professional design standards
```

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上
    - 无需额外 Python 依赖（使用 OpenWebUI 内置依赖）

---

## 常见问题

??? question "没有生成信息图？"
    请确认文本长度至少 100 字符（可通过 `MIN_TEXT_LENGTH` 调整）。

??? question "模板与内容不匹配？"
    AI 会根据内容结构自动选择模板，如需指定可使用高级语法。

??? question "导出失败？"
    确认浏览器支持 HTML5 Canvas 和 SVG，尝试刷新页面。

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/infographic){ .md-button }
