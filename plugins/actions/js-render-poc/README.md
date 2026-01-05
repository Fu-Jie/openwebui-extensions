# Infographic to Markdown

> **Version:** 1.0.0

AI-powered infographic generator that renders SVG on the frontend and embeds it directly into Markdown as a Data URL image.

## Overview

This plugin combines the power of AI text analysis with AntV Infographic visualization to create beautiful infographics that are embedded directly into chat messages as Markdown images.

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI Plugin                         │
├─────────────────────────────────────────────────────────────┤
│  1. Python Action                                            │
│     ├── Receive message content                              │
│     ├── Call LLM to generate Infographic syntax              │
│     └── Send __event_call__ to execute frontend JS           │
├─────────────────────────────────────────────────────────────┤
│  2. Browser JS (via __event_call__)                          │
│     ├── Dynamically load AntV Infographic library            │
│     ├── Render SVG offscreen                                 │
│     ├── Export to Data URL via toDataURL()                   │
│     └── Update message content via REST API                  │
├─────────────────────────────────────────────────────────────┤
│  3. Markdown Rendering                                       │
│     └── Display ![description](data:image/svg+xml;base64,...) │
└─────────────────────────────────────────────────────────────┘
```

## Features

- 🤖 **AI-Powered**: Automatically analyzes text and selects the best infographic template
- 📊 **Multiple Templates**: Supports 18+ infographic templates (lists, charts, comparisons, etc.)
- 🖼️ **Self-Contained**: SVG/PNG embedded as Data URL, no external dependencies
- 📝 **Markdown Native**: Results are pure Markdown images, compatible everywhere
- 🔄 **API Writeback**: Updates message content via REST API for persistence

## Plugins in This Directory

### 1. `infographic_markdown.py` - Main Plugin ⭐
- **Purpose**: Production use
- **Features**: Full AI + AntV Infographic + Data URL embedding

### 2. `js_render_poc.py` - Proof of Concept
- **Purpose**: Learning and testing
- **Features**: Simple SVG creation demo, `__event_call__` pattern

## Configuration (Valves)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SHOW_STATUS` | bool | `true` | Show operation status updates |
| `MODEL_ID` | string | `""` | LLM model ID (empty = use current model) |
| `MIN_TEXT_LENGTH` | int | `50` | Minimum text length required |
| `MESSAGE_COUNT` | int | `1` | Number of recent messages to use |
| `SVG_WIDTH` | int | `800` | Width of generated SVG (pixels) |
| `EXPORT_FORMAT` | string | `"svg"` | Export format: `svg` or `png` |

## Supported Templates

| Category | Template | Description |
|----------|----------|-------------|
| List | `list-grid` | Grid cards |
| List | `list-vertical` | Vertical list |
| Tree | `tree-vertical` | Vertical tree |
| Tree | `tree-horizontal` | Horizontal tree |
| Mind Map | `mindmap` | Mind map |
| Process | `sequence-roadmap` | Roadmap |
| Process | `sequence-zigzag` | Zigzag process |
| Relation | `relation-sankey` | Sankey diagram |
| Relation | `relation-circle` | Circular relation |
| Compare | `compare-binary` | Binary comparison |
| Analysis | `compare-swot` | SWOT analysis |
| Quadrant | `quadrant-quarter` | Quadrant chart |
| Chart | `chart-bar` | Bar chart |
| Chart | `chart-column` | Column chart |
| Chart | `chart-line` | Line chart |
| Chart | `chart-pie` | Pie chart |
| Chart | `chart-doughnut` | Doughnut chart |
| Chart | `chart-area` | Area chart |

## Syntax Examples

### Grid List
```infographic
infographic list-grid
data
  title Project Overview
  items
    - label Module A
      desc Description of module A
    - label Module B
      desc Description of module B
```

### Binary Comparison
```infographic
infographic compare-binary
data
  title Pros vs Cons
  items
    - label Pros
      children
        - label Strong R&D
          desc Technology leadership
    - label Cons
      children
        - label Weak brand
          desc Insufficient marketing
```

### Bar Chart
```infographic
infographic chart-bar
data
  title Quarterly Revenue
  items
    - label Q1
      value 120
    - label Q2
      value 150
```

## Technical Details

### Data URL Embedding
```javascript
// SVG to Base64 Data URL
const svgData = new XMLSerializer().serializeToString(svg);
const base64 = btoa(unescape(encodeURIComponent(svgData)));
const dataUri = "data:image/svg+xml;base64," + base64;

// Markdown image syntax
const markdownImage = `![description](${dataUri})`;
```

### AntV toDataURL API
```javascript
// Export as SVG (recommended, supports embedded resources)
const svgUrl = await instance.toDataURL({
    type: 'svg',
    embedResources: true
});

// Export as PNG (more compatible but larger)
const pngUrl = await instance.toDataURL({
    type: 'png',
    dpr: 2
});
```

## Notes

1. **Browser Compatibility**: Requires modern browsers with ES6+ and Fetch API support
2. **Network Dependency**: First use requires loading AntV library from CDN
3. **Data URL Size**: Base64 encoding increases size by ~33%
4. **Chinese Fonts**: SVG export embeds fonts for correct display

## Related Resources

- [AntV Infographic Documentation](https://infographic.antv.vision/)
- [Infographic API Reference](https://infographic.antv.vision/reference/infographic-api)
- [Infographic Syntax Guide](https://infographic.antv.vision/learn/infographic-syntax)

## License

MIT License
