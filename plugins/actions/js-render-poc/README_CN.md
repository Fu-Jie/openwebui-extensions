# 信息图转 Markdown

> **版本:** 1.0.0

AI 驱动的信息图生成器，在前端渲染 SVG 并以 Data URL 图片格式直接嵌入到 Markdown 中。

## 概述

这个插件结合了 AI 文本分析能力和 AntV Infographic 可视化引擎，生成精美的信息图并以 Markdown 图片格式直接嵌入到聊天消息中。

### 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI 插件                           │
├─────────────────────────────────────────────────────────────┤
│  1. Python Action                                            │
│     ├── 接收消息内容                                          │
│     ├── 调用 LLM 生成 Infographic 语法                        │
│     └── 发送 __event_call__ 执行前端 JS                      │
├─────────────────────────────────────────────────────────────┤
│  2. 浏览器 JS (通过 __event_call__)                          │
│     ├── 动态加载 AntV Infographic 库                          │
│     ├── 离屏渲染 SVG                                          │
│     ├── 使用 toDataURL() 导出 Data URL                        │
│     └── 通过 REST API 更新消息内容                            │
├─────────────────────────────────────────────────────────────┤
│  3. Markdown 渲染                                            │
│     └── 显示 ![描述](data:image/svg+xml;base64,...)          │
└─────────────────────────────────────────────────────────────┘
```

## 功能特点

- 🤖 **AI 驱动**: 自动分析文本并选择最佳的信息图模板
- 📊 **多种模板**: 支持 18+ 种信息图模板（列表、图表、对比等）
- 🖼️ **自包含**: SVG/PNG 以 Data URL 嵌入，无外部依赖
- 📝 **Markdown 原生**: 结果是纯 Markdown 图片，兼容任何平台
- 🔄 **API 回写**: 通过 REST API 更新消息内容实现持久化

## 目录中的插件

### 1. `infographic_markdown.py` - 主插件 ⭐
- **用途**: 生产使用
- **功能**: 完整的 AI + AntV Infographic + Data URL 嵌入

### 2. `infographic_markdown_cn.py` - 主插件（中文版）
- **用途**: 生产使用
- **功能**: 与英文版相同，界面文字为中文

### 3. `js_render_poc.py` - 概念验证
- **用途**: 学习和测试
- **功能**: 简单的 SVG 创建演示，`__event_call__` 模式

## 配置选项 (Valves)

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `SHOW_STATUS` | bool | `true` | 是否显示操作状态 |
| `MODEL_ID` | string | `""` | LLM 模型 ID（空则使用当前模型） |
| `MIN_TEXT_LENGTH` | int | `50` | 最小文本长度要求 |
| `MESSAGE_COUNT` | int | `1` | 用于生成的最近消息数量 |
| `SVG_WIDTH` | int | `800` | 生成的 SVG 宽度（像素） |
| `EXPORT_FORMAT` | string | `"svg"` | 导出格式：`svg` 或 `png` |

## 支持的模板

| 类别 | 模板名称 | 描述 |
|------|----------|------|
| 列表 | `list-grid` | 网格卡片 |
| 列表 | `list-vertical` | 垂直列表 |
| 树形 | `tree-vertical` | 垂直树 |
| 树形 | `tree-horizontal` | 水平树 |
| 思维导图 | `mindmap` | 思维导图 |
| 流程 | `sequence-roadmap` | 路线图 |
| 流程 | `sequence-zigzag` | 折线流程 |
| 关系 | `relation-sankey` | 桑基图 |
| 关系 | `relation-circle` | 圆形关系 |
| 对比 | `compare-binary` | 二元对比 |
| 分析 | `compare-swot` | SWOT 分析 |
| 象限 | `quadrant-quarter` | 四象限图 |
| 图表 | `chart-bar` | 条形图 |
| 图表 | `chart-column` | 柱状图 |
| 图表 | `chart-line` | 折线图 |
| 图表 | `chart-pie` | 饼图 |
| 图表 | `chart-doughnut` | 环形图 |
| 图表 | `chart-area` | 面积图 |

## 语法示例

### 网格列表
```infographic
infographic list-grid
data
  title 项目概览
  items
    - label 模块一
      desc 这是第一个模块的描述
    - label 模块二
      desc 这是第二个模块的描述
```

### 二元对比
```infographic
infographic compare-binary
data
  title 优劣对比
  items
    - label 优势
      children
        - label 研发能力强
          desc 技术领先
    - label 劣势
      children
        - label 品牌曝光不足
          desc 营销力度不够
```

### 条形图
```infographic
infographic chart-bar
data
  title 季度收入
  items
    - label Q1
      value 120
    - label Q2
      value 150
```

## 技术细节

### Data URL 嵌入
```javascript
// SVG 转 Base64 Data URL
const svgData = new XMLSerializer().serializeToString(svg);
const base64 = btoa(unescape(encodeURIComponent(svgData)));
const dataUri = "data:image/svg+xml;base64," + base64;

// Markdown 图片语法
const markdownImage = `![描述](${dataUri})`;
```

### AntV toDataURL API
```javascript
// 导出 SVG（推荐，支持嵌入资源）
const svgUrl = await instance.toDataURL({
    type: 'svg',
    embedResources: true
});

// 导出 PNG（更兼容但体积更大）
const pngUrl = await instance.toDataURL({
    type: 'png',
    dpr: 2
});
```

## 注意事项

1. **浏览器兼容性**: 需要现代浏览器支持 ES6+ 和 Fetch API
2. **网络依赖**: 首次使用需要从 CDN 加载 AntV Infographic 库
3. **Data URL 大小**: Base64 编码会增加约 33% 的体积
4. **中文字体**: SVG 导出时会嵌入字体以确保正确显示

## 相关资源

- [AntV Infographic 官方文档](https://infographic.antv.vision/)
- [Infographic API 参考](https://infographic.antv.vision/reference/infographic-api)
- [Infographic 语法规范](https://infographic.antv.vision/learn/infographic-syntax)

## 许可证

MIT License
