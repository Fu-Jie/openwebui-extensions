# AntV Infographic 智能信息图插件

将文本内容一键转换为精美的信息图。支持列表、层级、流程、关系、对比、分析、图表等多种可视化形式。

## 功能特性

- **智能分析**: 自动识别文本结构，选择最合适的图表模板。
- **丰富模板**: 支持 20+ 种 AntV 信息图模板，涵盖列表、树图、思维导图、流程图、桑基图、SWOT、象限图、柱状图、饼图等。
- **自动配图**: 智能搜索并匹配合适的图标。
- **多格式导出**: 支持导出为 SVG, PNG, HTML 格式。
- **多语言支持**: 输出语言跟随用户设定。

## 使用方法

在 Open WebUI 聊天框中，直接输入文本或上传文档，然后启用该插件。插件会自动分析内容并生成信息图。

### 支持的图表类型

#### 1. 列表与层级
- **列表**: 网格卡片 (`list-grid`), 垂直列表 (`list-vertical`)
- **树图**: 垂直树 (`tree-vertical`), 水平树 (`tree-horizontal`)
- **思维导图**: `mindmap`

#### 2. 顺序与关系
- **流程**: 路线图 (`sequence-roadmap`), 之字形流程 (`sequence-zigzag`), 水平流程 (`sequence-horizontal`)
- **关系**: 桑基图 (`relation-sankey`), 循环关系 (`relation-circle`)

#### 3. 对比与分析
- **对比**: 二元对比 (`compare-binary`), 对比表 (`compare-table`)
- **分析**: SWOT 分析 (`compare-swot`), 象限图 (`quadrant-quarter`)

#### 4. 图表与数据
- **统计**: 统计卡片 (`statistic-card`)
- **图表**: 柱状图 (`chart-bar`), 条形图 (`chart-column`), 折线图 (`chart-line`), 饼图 (`chart-pie`), 环形图 (`chart-doughnut`)

## 安装

将 `infographic.py` (英文版) 或 `信息图.py` (中文版) 放入 Open WebUI 的插件目录即可。

## 依赖

- 插件依赖 `@antv/infographic` 库 (通过 CDN 加载)。
- 需要联网权限以加载 CDN 资源和图标。
