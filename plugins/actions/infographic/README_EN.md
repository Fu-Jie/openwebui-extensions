# AntV Infographic Plugin

Transform text content into beautiful infographics with a single click. Supports lists, hierarchies, processes, relationships, comparisons, analysis, charts, and more.

## Features

- **Smart Analysis**: Automatically identifies text structure and selects the best template.
- **Rich Templates**: Supports 20+ AntV infographic templates, including lists, trees, mind maps, roadmaps, Sankey diagrams, SWOT, quadrant charts, bar charts, pie charts, etc.
- **Auto Icons**: Intelligently searches and matches appropriate icons.
- **Multi-format Export**: Export as SVG, PNG, or HTML.
- **Multi-language**: Output language follows user settings.

## Usage

In the Open WebUI chat interface, simply input text or upload a document, then enable this plugin. The plugin will analyze the content and generate an infographic.

### Supported Chart Types

#### 1. List & Hierarchy
- **List**: Grid Cards (`list-grid`), Vertical List (`list-vertical`)
- **Tree**: Vertical Tree (`tree-vertical`), Horizontal Tree (`tree-horizontal`)
- **Mindmap**: `mindmap`

#### 2. Sequence & Relationship
- **Process**: Roadmap (`sequence-roadmap`), Zigzag Process (`sequence-zigzag`), Horizontal Process (`sequence-horizontal`)
- **Relationship**: Sankey Diagram (`relation-sankey`), Circular Relationship (`relation-circle`)

#### 3. Comparison & Analysis
- **Comparison**: Binary Comparison (`compare-binary`), Comparison Table (`compare-table`)
- **Analysis**: SWOT Analysis (`compare-swot`), Quadrant Chart (`quadrant-quarter`)

#### 4. Charts & Data
- **Statistics**: Statistic Cards (`statistic-card`)
- **Charts**: Bar Chart (`chart-bar`), Column Chart (`chart-column`), Line Chart (`chart-line`), Pie Chart (`chart-pie`), Doughnut Chart (`chart-doughnut`)

## Installation

Place `infographic.py` (English version) or `信息图.py` (Chinese version) into your Open WebUI plugins directory.

## Dependencies

- Depends on `@antv/infographic` library (loaded via CDN).
- Requires internet access to load CDN resources and icons.
