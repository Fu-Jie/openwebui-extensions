"""
title: 智能信息图
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPgogIDxsaW5lIHgxPSIxMiIgeTE9IjIwIiB4Mj0iMTIiIHkyPSIxMCIgLz4KICA8bGluZSB4MT0iMTgiIHkxPSIyMCIgeDI9IjE4IiB5Mj0iNCIgLz4KICA8bGluZSB4MT0iNiIgeTE9IjIwIiB4Mj0iNiIgeTI9IjE2IiAvPgo8L3N2Zz4=
version: 1.5.0
openwebui_id: e04a48ff-23ee-4a41-8ea7-66c19524e7c8
description: 基于 AntV Infographic 的智能信息图生成插件。支持多种专业模板，自动图标匹配，并提供 SVG/PNG 下载功能。
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Callable, Awaitable
import logging
import time
import re
from fastapi import Request
from datetime import datetime

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================================================================
# LLM 提示词
# =================================================================

SYSTEM_PROMPT_INFOGRAPHIC_ASSISTANT = """
You are a professional infographic design expert who can analyze user-provided text content and convert it into AntV Infographic syntax format.

## Important Language Rule (语言规则)
- **Priority Input Language (优先使用输入语言)**: You must generate the text content of the infographic in the **exact same language** as the user's input content.
- **Example**: If the user provides a summary in Chinese, the labels and descriptions in the infographic must be in Chinese.

## Infographic Syntax Specification

Infographic syntax is a Mermaid-like declarative syntax for describing infographic templates, data, and themes.

### Syntax Rules
- Entry uses `infographic <template-name>`
- Key-value pairs are separated by spaces, **absolutely NO colons allowed**
- Use two spaces for indentation
- Object arrays use `-` with line breaks

⚠️ **IMPORTANT WARNING: This is NOT YAML format!**
- ❌ Wrong: `children:` `items:` `data:` (with colons)
- ✅ Correct: `children` `items` `data` (without colons)

### 模板库与选择指南

根据内容结构选择最合适的模板。

**模板选择指南 (官方):**
- 严格时序 (流程/步骤/趋势) → `sequence-*` 系列
  - 时间线 → `sequence-timeline-simple`
  - 路线图 → `sequence-roadmap-vertical-simple`
  - 折线步骤 → `sequence-horizontal-zigzag-underline-text`
  - 蛇形步骤 → `sequence-snake-steps-compact-card`
- 列举要点 → `list-row-horizontal-icon-arrow` 或 `list-column-simple-vertical-arrow`
- 对比分析 (A vs B) → `compare-binary-horizontal-underline-text-vs`
- SWOT 分析 → `compare-swot`
- 层级结构 (树状图) → `hierarchy-tree-tech-style-capsule-item`
- 数据图表 → `chart-*` 系列
- 象限分析 → `quadrant-quarter-simple-card`
- 网格列表 → `list-grid-candy-card-lite`
- 关系展示 → `relation-circle-icon-badge`

**可用模板:**

*Sequence (时序/流程):*
`sequence-timeline-simple`, `sequence-roadmap-vertical-simple`, `sequence-horizontal-zigzag-underline-text`, 
`sequence-snake-steps-compact-card`, `sequence-zigzag-steps-underline-text`, `sequence-circular-simple`

*List (列表):*
`list-grid-candy-card-lite`, `list-grid-badge-card`, `list-row-horizontal-icon-arrow`,
`list-column-simple-vertical-arrow`, `list-column-done-list`

*Compare (对比):*
`compare-binary-horizontal-underline-text-vs`, `compare-swot`

*Hierarchy (层级):*
`hierarchy-tree-tech-style-capsule-item`, `hierarchy-structure`

*Chart (图表):*
`chart-column-simple`, `chart-bar-plain-text`, `chart-pie-plain-text`, `chart-wordcloud`

*Other:*
`quadrant-quarter-simple-card`, `relation-circle-icon-badge`

**按容量分类:**
- 高容量 (长描述): `list-column-*`, `compare-binary-*`, `sequence-timeline-*`
- 中容量: `list-row-*`, `sequence-roadmap-*`
- 低容量 (短文本): `list-grid-*`, `hierarchy-*`

### 图标和插图资源

**图标 (Iconify):**
- 格式: `<集合>/<图标名>`, 如 `mdi/rocket-launch`
- 常用: `mdi/*`, `fa/*`, `bi/*`

**插图 (unDraw):**
- 格式: 文件名 (不含 .svg), 如 `coding`, `team-work`
- 使用 `illus` 字段

### Infographic Syntax Guide

#### 1. Structure
-   **Entry**: `infographic <template-name>`
-   **Blocks**: `data`, `theme`, `design` (optional)
-   **Format**: Key-value pairs separated by spaces, 2-space indentation.
-   **Arrays**: Object arrays use `-` (newline), simple arrays use inline values.

#### 2. Data Block (`data`)
-   `title`: Main title
-   `desc`: Subtitle or description
-   `items`: List of data items
-     - `label`: Item title
-     - `value`: Numerical value (required for Charts/Stats)
-     - `desc`: Item description (optional)
-     - `icon`: Icon name (e.g., `mdi/rocket-launch`)
-     - `time`: Time label (Optional, for Roadmap/Sequence)
-     - `children`: Nested items (ONLY for Tree/Mindmap/Sankey/SWOT)
-     - `illus`: Illustration name (ONLY for Quadrant)

#### 3. Theme Block (`theme`)
-   `colorPrimary`: Main color (Hex)
-   `colorBg`: Background color (Hex)
-   `palette`: Color list (Space separated)
-   `textColor`: Text color (Hex)
-   `stylize`: Style effect configuration
-     `type`: Style type (`rough`, `pattern`, `linear-gradient`, `radial-gradient`)

#### 4. Stylize Examples
**Rough Style (Hand-drawn):**
```infographic
infographic list-row-simple-horizontal-arrow
theme
  stylize rough
data
  ...
```

**Gradient Style:**
```infographic
infographic chart-bar
theme
  stylize linear-gradient
data
  ...
```

### Examples

#### Chart (Bar Chart)
infographic chart-bar
data
  title Revenue Growth
  desc Monthly revenue in 2024
  items
    - label Jan
      value 1200
    - label Feb
      value 1500
    - label Mar
      value 1800


#### Comparison (Binary Comparison)
infographic compare-binary
data
  title Advantages vs Disadvantages
  desc Compare two aspects side by side
  items
    - label Advantages
      children
        - label Strong R&D
          desc Leading technology and innovation capability
        - label High customer loyalty
          desc Repurchase rate over 60%
    - label Disadvantages
      children
        - label Weak brand exposure
          desc Insufficient marketing, low awareness
        - label Narrow channel coverage
          desc Limited online channels

#### Comparison (SWOT)
infographic compare-swot
data
  title Project SWOT
  items
    - label Strengths
      children
        - label Strong team
        - label Innovative tech
    - label Weaknesses
      children
        - label Limited budget
    - label Opportunities
      children
        - label Emerging market
    - label Threats
      children
        - label High competition

#### Relationship (Sankey)
infographic relation-sankey
data
  title Energy Flow
  items
    - label Solar
      value 100
      children
        - label Grid
          value 60
        - label Battery
          value 40
    - label Wind
      value 80
      children
        - label Grid
          value 80

#### Quadrant (Importance vs Urgency)
infographic quadrant-quarter
data
  title Task Management
  items
    - label Critical Bug
      desc Fix immediately
      illus mdi/bug
    - label Feature Request
      desc Plan for next sprint
      illus mdi/star

### Content Refinement Principles
1. **Brevity is King**: Infographics are visual. Keep text to a minimum.
2. **Title Limit**: Keep `label` (item titles) under 15 characters.
3. **Description Limit**: Keep `desc` (item descriptions) under 25 characters (approx. 2 lines).
4. **Impact**: Use strong verbs and nouns. Avoid filler words.

### Output Rules
1.  **Strict Syntax**: Follow the indentation and formatting rules exactly.
2.  **No Explanations**: Output ONLY the syntax code block.
3.  **Language**: Use the user's requested language for content.
"""

import json

USER_PROMPT_GENERATE_INFOGRAPHIC = """
请分析以下文本内容，将其核心信息转换为 AntV Infographic 语法格式。

---
**用户上下文信息:**
用户姓名: {user_name}
当前日期时间: {current_date_time_str}
用户语言: {user_language}
---

**文本内容:**
{long_text_content}

请根据文本特点选择最合适的信息图模板，并输出规范的 infographic 语法。注意保持正确的缩进格式（两个空格）。

**视觉优化指南：** 
- **要点化生成：** 信息图不是文章。请将内容转化为“关键词+短语”的形式，严禁生成长难句。
- **标题限制：** 每个卡片的 `label`（标题）请控制在 **8个汉字**以内。
- **描述限制：** 每个卡片的 `desc`（描述）请控制在 **15个汉字**以内，确保即使在小屏幕上也能完整显示。
- **结构化思维：** 优先使用并列、递进或对比结构，使信息一目了然。
"""

# =================================================================
# HTML 容器模板
# =================================================================

HTML_WRAPPER_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 10px; 
            background-color: transparent; 
        }
        #main-container { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            align-items: flex-start; 
            width: 100%;
        }
        .plugin-item { 
            flex: 1 1 400px;
            min-width: 300px; 
            border-radius: 12px; 
            overflow: hidden; 
            transition: all 0.3s ease;
        }
        .plugin-item:hover {
            transform: translateY(-2px);
        }
        @media (max-width: 768px) { 
            .plugin-item { flex: 1 1 100%; } 
        }
        /* STYLES_INSERTION_POINT */
    </style>
</head>
<body>
    <div id="main-container">
        <!-- CONTENT_INSERTION_POINT -->
    </div>
    <!-- SCRIPTS_INSERTION_POINT -->
</body>
</html>
"""

# =================================================================
# CSS 样式模板
# =================================================================

CSS_TEMPLATE_INFOGRAPHIC = """
:root {
    --ig-primary-color: #6366f1;
    --ig-secondary-color: #8b5cf6;
    --ig-tertiary-color: #10b981;
    --ig-background-color: #f8fafc;
    --ig-card-bg-color: #ffffff;
    --ig-text-color: #1e293b;
    --ig-muted-text-color: #64748b;
    --ig-border-color: #e2e8f0;
    --ig-header-gradient: linear-gradient(135deg, #6366f1, #8b5cf6);
}
.infographic-container-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: var(--ig-text-color);
    height: 100%;
    display: flex;
    flex-direction: column;
}
.infographic-container-wrapper .header {
    background: var(--ig-header-gradient);
    color: white;
    padding: 20px 24px;
    text-align: center;
}
.infographic-container-wrapper .header h1 {
    margin: 0;
    font-size: 1.5em;
    font-weight: 600;
}
.infographic-container-wrapper .user-context {
    font-size: 0.8em;
    color: var(--ig-muted-text-color);
    background-color: #f1f5f9;
    padding: 8px 16px;
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--ig-border-color);
}
.infographic-container-wrapper .content-area {
    padding: 20px;
    flex-grow: 1;
}
.infographic-container-wrapper .infographic-render-container {
    border-radius: 8px;
    padding: 16px;
    min-height: 600px;
    background: #fff;
    overflow: visible;
    transition: height 0.3s ease;
}
.infographic-render-container svg text {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
}
.infographic-render-container svg foreignObject {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
    line-height: 1.3 !important;
    overflow: visible !important;
}
/* 主标题样式 */
.infographic-render-container svg foreignObject[data-element-type="title"] > * {
    font-size: 1.3em !important;
    font-weight: 800 !important;
    line-height: 1.3 !important;
    white-space: normal !important;
    word-break: break-word !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    text-align: center !important;
}
/* 页面副标题样式 */
.infographic-render-container svg foreignObject[data-element-type="desc"] > * {
    font-size: 0.85em !important;
    line-height: 1.3 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    text-align: center !important;
    display: block !important;
    color: var(--ig-muted-text-color) !important;
}
/* 卡片标题样式 */
.infographic-render-container svg foreignObject[data-element-type="item-label"] > * {
    font-size: 0.9em !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    white-space: normal !important;
    word-break: break-word !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    padding-bottom: 2px !important;
}
/* 卡片描述文字 */
.infographic-render-container svg foreignObject[data-element-type="item-desc"] > * {
    font-size: 0.82em !important;
    line-height: 1.3 !important;
    white-space: normal !important;
    display: -webkit-box !important;
    -webkit-line-clamp: 2 !important;
    -webkit-box-orient: vertical !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.infographic-container-wrapper .download-area {
    text-align: center;
    padding-top: 20px;
    margin-top: 20px;
    border-top: 1px solid var(--ig-border-color);
}
.infographic-container-wrapper .download-btn {
    background-color: var(--ig-primary-color);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 0.9em;
    cursor: pointer;
    transition: all 0.2s;
    margin: 4px 6px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.infographic-container-wrapper .download-btn.secondary {
    background-color: var(--ig-secondary-color);
}
.infographic-container-wrapper .download-btn.tertiary {
    background-color: var(--ig-tertiary-color);
}
.infographic-container-wrapper .download-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.infographic-container-wrapper .footer {
    text-align: center;
    padding: 16px;
    font-size: 0.8em;
    color: var(--ig-muted-text-color);
    background-color: #f8fafc;
    border-top: 1px solid var(--ig-border-color);
}
.infographic-container-wrapper .error-message {
    color: #dc2626;
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
}
"""

# =================================================================
# HTML 内容模板
# =================================================================

CONTENT_TEMPLATE_INFOGRAPHIC = """
<div class="infographic-container-wrapper">
    <div class="header">
        <h1>📊 智能信息图</h1>
    </div>
    <div class="user-context">
        <span><strong>用户:</strong> {user_name}</span>
        <span><strong>时间:</strong> {current_date_time_str}</span>
    </div>
    <div class="content-area">
        <div class="infographic-render-container" id="infographic-container-{unique_id}"></div>
        <div class="download-area">
            <button id="download-svg-btn-{unique_id}" class="download-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                <span class="btn-text">下载 SVG</span>
            </button>
            <button id="download-png-btn-{unique_id}" class="download-btn secondary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                </svg>
                <span class="btn-text">下载 PNG</span>
            </button>
            <button id="download-html-btn-{unique_id}" class="download-btn tertiary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="16 18 22 12 16 6"/>
                    <polyline points="8 6 2 12 8 18"/>
                </svg>
                <span class="btn-text">下载 HTML</span>
            </button>
        </div>
    </div>
    <div class="footer">
        <p>© {current_year} 信息图 • <a href="https://infographic.antv.vision/" target="_blank" style="display: inline-flex; align-items: center; vertical-align: middle;">
            <svg width="24" height="25" viewBox="0 0 291 300" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-left: 4px;">
                <g><path d="M140.904 239.376C128.83 239.683 119.675 239.299 115.448 243.843C110.902 248.07 111.288 257.227 110.979 269.302C111.118 274.675 111.118 279.478 111.472 283.52C111.662 285.638 111.95 287.547 112.406 289.224C112.411 289.243 112.416 289.259 112.422 289.28C112.462 289.419 112.496 289.558 112.539 289.691C113.168 291.787 114.088 293.491 115.446 294.758C116.662 296.064 118.283 296.963 120.264 297.59C120.36 297.614 120.464 297.646 120.555 297.675C120.56 297.68 120.56 297.68 120.566 297.68C120.848 297.768 121.142 297.846 121.443 297.923C121.454 297.923 121.464 297.928 121.478 297.934C122.875 298.272 124.424 298.507 126.11 298.678C126.326 298.696 126.542 298.718 126.763 298.739C130.79 299.086 135.558 299.088 140.904 299.222C152.974 298.912 162.128 299.302 166.36 294.758C170.904 290.526 170.515 281.371 170.824 269.302C170.515 257.227 170.907 248.07 166.36 243.843C162.131 239.299 152.974 239.683 140.904 239.376Z" fill="#FF6376"></path><path d="M21.2155 128.398C12.6555 128.616 6.16484 128.339 3.16751 131.56C-0.0538222 134.56 0.218178 141.054 -0.000488281 149.608C0.218178 158.168 -0.0538222 164.659 3.16751 167.656C6.16484 170.878 12.6555 170.606 21.2155 170.824C25.0262 170.726 28.4288 170.726 31.2955 170.475C32.7968 170.342 34.1488 170.136 35.3382 169.814C35.3542 169.811 35.3648 169.806 35.3782 169.803C35.4768 169.774 35.5755 169.747 35.6688 169.718C37.1568 169.272 38.3648 168.622 39.2635 167.656C40.1915 166.795 40.8262 165.646 41.2715 164.243C41.2875 164.174 41.3115 164.102 41.3328 164.035C41.3328 164.035 41.3355 164.032 41.3355 164.027C41.3968 163.827 41.4529 163.622 41.5062 163.406C41.5062 163.398 41.5115 163.392 41.5142 163.382C41.7542 162.392 41.9222 161.294 42.0422 160.096C42.0555 159.944 42.0715 159.792 42.0848 159.635C42.3328 156.779 42.3328 153.398 42.4262 149.608C42.2075 141.054 42.4848 134.56 39.2635 131.56C36.2635 128.339 29.7728 128.616 21.2155 128.398Z" fill="#FFCCCC"></path><path d="M81.0595 184.171C70.8568 184.433 63.1208 184.102 59.5475 187.942C55.7075 191.518 56.0328 199.254 55.7742 209.454C56.0328 219.657 55.7075 227.393 59.5475 230.963C63.1208 234.803 70.8568 234.478 81.0595 234.739C85.6008 234.622 89.6595 234.622 93.0728 234.323C94.8648 234.163 96.4755 233.921 97.8942 233.534C97.9102 233.529 97.9235 233.526 97.9422 233.521C98.0568 233.486 98.1742 233.457 98.2888 233.422C100.06 232.889 101.5 232.113 102.569 230.963C103.676 229.937 104.433 228.566 104.964 226.894C104.985 226.811 105.012 226.726 105.036 226.646C105.041 226.643 105.041 226.643 105.041 226.638C105.116 226.401 105.18 226.153 105.244 225.897C105.244 225.889 105.249 225.881 105.254 225.867C105.54 224.689 105.74 223.379 105.881 221.953C105.9 221.771 105.916 221.59 105.934 221.403C106.228 218.001 106.228 213.969 106.342 209.454C106.081 199.254 106.412 191.518 102.572 187.942C98.9955 184.102 91.2568 184.433 81.0595 184.171Z" fill="#FF939F"></path><path d="M260.591 151.87C215.652 151.87 203.02 164.523 203.02 209.462H198.476C198.476 164.523 185.836 151.881 140.895 151.881V147.337C185.836 147.337 198.487 134.705 198.487 89.7659H203.02C203.02 134.705 215.652 147.337 260.591 147.337V151.87ZM286.052 124.158C281.82 119.614 272.66 120.001 260.591 119.689C248.521 119.385 239.361 119.771 235.129 115.227C230.585 110.995 230.983 101.846 230.671 89.7659C230.513 83.7312 230.535 78.4272 230.023 74.1019C229.513 69.7659 228.481 66.4219 226.209 64.3046C221.967 59.7606 212.817 60.1472 200.748 59.8459C188.681 60.1472 179.519 59.7606 175.287 64.3046C170.753 68.5366 171.129 77.6966 170.828 89.7659C170.516 101.835 170.9 110.995 166.356 115.227C162.124 119.771 152.985 119.374 140.905 119.689C138.873 119.739 136.924 119.771 135.071 119.811C119.313 118.697 106.337 112.318 106.337 89.7659C106.212 84.6699 106.233 80.1792 105.807 76.5206C105.367 72.8726 104.492 70.0379 102.575 68.2566C99.0013 64.4112 91.2573 64.7446 81.0653 64.4832C70.86 64.7446 63.1186 64.4112 59.5533 68.2566C55.708 71.8299 56.0306 79.5632 55.7693 89.7659C56.0306 99.9686 55.708 107.702 59.5533 111.278C63.1186 115.113 70.86 114.79 81.0653 115.049C103.617 115.049 109.996 128.035 111.1 143.803C111.068 145.659 111.028 147.587 110.975 149.619C111.121 154.987 111.121 159.79 111.476 163.835C111.663 165.95 111.945 167.857 112.404 169.534C112.412 169.555 112.412 169.566 112.423 169.598C112.465 169.734 112.497 169.867 112.537 170.003C113.164 172.099 114.092 173.809 115.447 175.07C116.665 176.371 118.281 177.278 120.271 177.905C120.364 177.934 120.46 177.955 120.564 177.987C120.855 178.081 121.145 178.153 121.439 178.238C121.46 178.238 121.471 178.238 121.479 178.249C122.876 178.582 124.42 178.822 126.108 178.987C126.327 179.009 126.545 179.03 126.764 179.051C130.788 179.395 135.559 179.395 140.905 179.529C152.975 179.843 162.124 179.457 166.356 184.001C170.9 188.233 170.516 197.371 170.828 209.451C171.129 221.529 170.743 230.681 175.287 234.91C179.519 239.454 188.681 239.07 200.748 239.371C206.127 239.235 210.921 239.235 214.975 238.881C217.079 238.694 218.985 238.403 220.676 237.955C220.695 237.945 220.705 237.934 220.727 237.934C220.873 237.891 220.999 237.859 221.135 237.819C223.228 237.193 224.937 236.265 226.209 234.91C227.511 233.691 228.409 232.065 229.044 230.097C229.065 230.003 229.095 229.899 229.127 229.803V229.793C229.22 229.513 229.295 229.222 229.367 228.918C229.367 228.897 229.377 228.897 229.377 228.878C229.721 227.481 229.951 225.937 230.127 224.249C230.137 224.03 230.169 223.811 230.191 223.593C230.535 219.571 230.535 214.798 230.671 209.451C230.972 197.371 230.585 188.233 235.129 184.001C239.361 179.457 248.511 179.843 260.591 179.529C272.66 179.227 281.82 179.614 286.052 175.07C290.596 170.838 290.209 161.689 290.511 149.619C290.209 137.539 290.596 128.379 286.052 124.158Z" fill="#FF356A"></path><path d="M112.405 49.848C112.411 49.8694 112.416 49.8827 112.421 49.904C112.461 50.0427 112.499 50.1814 112.539 50.3147C113.171 52.4134 114.088 54.1147 115.448 55.384C116.661 56.6907 118.283 57.5894 120.264 58.2134C120.36 58.24 120.464 58.2694 120.555 58.3014C120.56 58.3067 120.56 58.3067 120.565 58.3067C120.848 58.3947 121.141 58.4694 121.443 58.5467C121.453 58.5467 121.464 58.552 121.48 58.5574C122.875 58.896 124.424 59.1334 126.112 59.3014C126.325 59.3227 126.541 59.3414 126.763 59.3627C130.789 59.712 135.56 59.712 140.904 59.8454C152.973 59.5387 162.128 59.928 166.36 55.384C170.907 51.152 170.515 41.9947 170.824 29.9254C170.517 17.8507 170.907 8.69602 166.363 4.46935C162.131 -0.0746511 152.973 0.309349 140.904 1.52588e-05C128.829 0.309349 119.675 -0.0746511 115.448 4.46935C110.904 8.69602 111.288 17.8507 110.979 29.9254C111.117 35.3014 111.117 40.1014 111.472 44.144C111.661 46.2614 111.949 48.1707 112.405 49.848Z" fill="#FF6376"></path></g>
            </svg>
        </a></p>
    </div>
</div>

<script type="text/template" id="infographic-source-{unique_id}">{infographic_syntax}</script>
"""

# =================================================================
# JavaScript 渲染脚本
# =================================================================

SCRIPT_TEMPLATE_INFOGRAPHIC = """
<script src="https://registry.npmmirror.com/@antv/infographic/0.2.1/files/dist/infographic.min.js"></script>
<script>
(function() {{
    const renderInfographic = () => {{
        const uniqueId = "{unique_id}";
        const containerEl = document.getElementById('infographic-container-' + uniqueId);
        if (!containerEl || containerEl.dataset.infographicRendered) return;

        const sourceEl = document.getElementById('infographic-source-' + uniqueId);
        if (!sourceEl) return;

        let syntaxContent = sourceEl.textContent.trim();
        if (!syntaxContent) {{
            containerEl.innerHTML = '<div class="error-message">⚠️ 无法加载信息图：缺少有效内容。</div>';
            return;
        }}

        console.log('[Infographic] 原始语法内容:', syntaxContent);

        // 尝试提取代码块内容
        const bt = String.fromCharCode(96);
        const tripleBt = bt + bt + bt;
        
        const startBlockIdx = syntaxContent.indexOf(tripleBt);
        if (startBlockIdx !== -1) {
            const endBlockIdx = syntaxContent.lastIndexOf(tripleBt);
            if (endBlockIdx > startBlockIdx) {
                let content = syntaxContent.substring(startBlockIdx + 3, endBlockIdx).trim();
                if (content.toLowerCase().startsWith('infographic')) {
                    const lineBreakChar = String.fromCharCode(10);
                    const firstLineBreak = content.indexOf(lineBreakChar);
                    if (firstLineBreak !== -1) {
                        const firstLine = content.substring(0, firstLineBreak).trim();
                        if (firstLine.toLowerCase() === 'infographic') {
                            content = content.substring(firstLineBreak).trim();
                        }
                    }
                }
                syntaxContent = content;
            }
        } else {
            const keyStart = syntaxContent.indexOf('infographic ');
            if (keyStart !== -1) {
                syntaxContent = syntaxContent.substring(keyStart).trim();
            }
        }

        // 修复语法：移除关键字后面的冒号
        syntaxContent = syntaxContent.replace(/^(data|items|children|theme|config):/gm, '$1');
        syntaxContent = syntaxContent.replace(/(\\s)(children|items):/g, '$1$2');

        // 1. 兜底检查：确保以 infographic 开头
        if (!syntaxContent.trim().toLowerCase().startsWith('infographic')) {
            const firstWord = syntaxContent.trim().split(/\s+/)[0].toLowerCase();
            if (!['data', 'theme', 'design', 'items'].includes(firstWord)) {
                console.log('[Infographic] 检测到缺失 infographic 前缀，自动补全');
                syntaxContent = 'infographic ' + syntaxContent;
            }
        }

        // 2. 模板映射配置 (官方 AntV 结构 ID)
        const TEMPLATE_MAPPING = {
            // 列表与层级 - 短名称映射到完整模板名
            'list-grid': 'list-grid-compact-card',
            'list-column': 'list-column-simple-vertical-arrow',
            'list-row': 'list-row-simple-horizontal-arrow',
            'hierarchy-tree': 'hierarchy-tree-tech-style-capsule-item',
            
            // 时序与时间线
            'sequence-roadmap-vertical': 'sequence-roadmap-vertical-simple',
            'sequence-timeline': 'sequence-timeline-simple',
            'sequence-steps': 'sequence-steps-simple',
            'sequence-horizontal-zigzag': 'sequence-horizontal-zigzag-simple',
            
            // 对比
            'compare-binary-horizontal': 'compare-binary-horizontal-simple-vs',
            'compare-hierarchy-row': 'compare-hierarchy-row-simple',
            
            // 图表
            'chart-column': 'chart-column-simple',
            'quadrant': 'quadrant-quarter-simple-card',
            
            // 向后兼容的旧映射
            'list-vertical': 'list-column-simple-vertical-arrow',
            'tree-vertical': 'hierarchy-tree-tech-style-capsule-item',
            'sequence-roadmap': 'sequence-roadmap-vertical-simple',
            'sequence-zigzag': 'sequence-horizontal-zigzag-simple',
            'compare-binary': 'compare-binary-horizontal-simple-vs',
            'chart-bar': 'chart-bar-plain-text',
            'chart-line': 'chart-line-plain-text',
            'chart-pie': 'chart-pie-plain-text',
            'chart-doughnut': 'chart-pie-donut-plain-text'
        };

        // 3. 应用映射策略
        for (const [key, value] of Object.entries(TEMPLATE_MAPPING)) {
            const regex = new RegExp(`infographic\\\\s+${key}(?=\\\\s|$)`, 'i');
            if (regex.test(syntaxContent)) {
                console.log(`[Infographic] 自动映射模板: ${key} -> ${value}`);
                syntaxContent = syntaxContent.replace(regex, `infographic ${value}`);
                break; // 找到一个匹配后即停止
            }
        }

        // --- 样式提取与应用 ---
        const bgMatch = syntaxContent.match(/backgroundColor\s+(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|[a-zA-Z]+)/);
        if (bgMatch && bgMatch[1]) {
            containerEl.style.backgroundColor = bgMatch[1];
        } else {
            containerEl.style.backgroundColor = '#ffffff';
        }

        const textMatch = syntaxContent.match(/textColor\s+(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|[a-zA-Z]+)/);
        if (textMatch && textMatch[1]) {
            containerEl.style.color = textMatch[1];
        } else {
             containerEl.style.color = '';
        }

        // --- 语法清理 ---
        // 移除不支持的 theme 属性
        const nl = String.fromCharCode(10);
        const cleanRegex = new RegExp('^\\\\s*(roughness|stylize|backgroundColor|textColor|colorBg).*(' + nl + '\\\\s+.*)*', 'gm');
        syntaxContent = syntaxContent.replace(cleanRegex, '');
        
        syntaxContent = syntaxContent.trim();
        
        // 临时降级策略
        if (/infographic\s+list-vertical/.test(syntaxContent)) {
             console.log('[Infographic] 检测到 list-vertical 模板，为保证稳定性，临时降级为 list-row-simple-horizontal-arrow');
             syntaxContent = syntaxContent.replace(/infographic\s+list-vertical/, 'infographic list-row-simple-horizontal-arrow');
        }

        console.log('[Infographic] 清理后的语法内容:', syntaxContent);

        if (typeof AntVInfographic === 'undefined') {{
            console.error('[Infographic] AntVInfographic 库未加载');
            containerEl.innerHTML = '<div class="error-message">⚠️ 无法加载 AntV Infographic 库，请检查网络或稍后重试。</div>';
            return;
        }}

        try {{
            const {{ Infographic }} = AntVInfographic;
            const containerId = '#' + containerEl.id;
            
            const instance = new Infographic({
                container: containerId,
                padding: 24,
            });

            if (instance.on) {
                instance.on('error', (err) => {
                    console.error('[Infographic] 内部错误:', err);
                });
            }
            
            console.log('[Infographic] 开始渲染...');
            instance.render(syntaxContent);
            
            // 强制检查并挂载节点
            if (instance.node) {
                const existingSvg = containerEl.querySelector('svg');
                if (!existingSvg) {
                    console.log('[Infographic] 未检测到 SVG，执行强制手动挂载...');
                    containerEl.appendChild(instance.node);
                }
            } else {
                console.warn('[Infographic] 实例无 node 属性，尝试备用渲染...');
                try {
                    const tempInstance = new Infographic({});
                    tempInstance.render(syntaxContent);
                    if (tempInstance.node) {
                        containerEl.appendChild(tempInstance.node);
                    }
                } catch (e) {
                    console.error('[Infographic] 备用渲染也失败:', e);
                }
            }
            
            containerEl.dataset.infographicRendered = 'true';
            console.log('[Infographic] 渲染完成');

            // 自动调整高度与元素标记
            setTimeout(() => {
                const svg = containerEl.querySelector('svg');
                if (svg) {
                    // 1. 标记元素以便 CSS 应用样式
                    const fos = Array.from(svg.querySelectorAll('foreignObject'));
                    let titleFound = false;
                    let descFound = false;
                    
                    fos.forEach((fo) => {
                        const text = fo.textContent.trim();
                        if (!text || fo.querySelector('i') || (fo.querySelector('svg') && fo.querySelectorAll('*').length < 5)) {
                            fo.setAttribute('data-element-type', 'icon');
                            return;
                        }
                        
                        // 动态增加高度和宽度，容纳换行后的文字
                        const currentHeight = parseInt(fo.getAttribute('height') || '0');
                        if (currentHeight > 0 && currentHeight < 200) {
                            fo.setAttribute('height', Math.round(currentHeight * 1.8).toString());
                        }
                        const currentWidth = parseInt(fo.getAttribute('width') || '0');
                        if (currentWidth > 0 && currentWidth < 300) {
                            fo.setAttribute('width', Math.max(Math.round(currentWidth * 1.2), 180).toString());
                        }

                        if (!titleFound) {
                            fo.setAttribute('data-element-type', 'title');
                            titleFound = true;
                        } else if (!descFound) {
                            fo.setAttribute('data-element-type', 'desc');
                            descFound = true;
                        } else {
                            if (fo.querySelector('strong') || fo.style.fontWeight === 'bold' || text.length < 15) {
                                fo.setAttribute('data-element-type', 'item-label');
                            } else {
                                fo.setAttribute('data-element-type', 'item-desc');
                            }
                        }
                    });

                    // 2. 调整高度
                    const bbox = svg.getBoundingClientRect();
                    let contentHeight = bbox.height;
                    if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.height) {
                        contentHeight = svg.viewBox.baseVal.height;
                    }
                    const finalHeight = contentHeight + 40; 
                    containerEl.style.minHeight = finalHeight + 'px';
                    containerEl.style.height = 'auto';
                }
            }, 500);
            
            attachDownloadHandlers(uniqueId, syntaxContent);

        }} catch (error) {{
            console.error('[Infographic] 渲染出错:', error);
            containerEl.innerHTML = '<div class="error-message">⚠️ 信息图渲染失败！<br>原因：' + error.message + '</div>';
        }}
    }};

    const attachDownloadHandlers = (uniqueId, syntaxContent) => {{
        const downloadSvgBtn = document.getElementById('download-svg-btn-' + uniqueId);
        const downloadPngBtn = document.getElementById('download-png-btn-' + uniqueId);
        const downloadHtmlBtn = document.getElementById('download-html-btn-' + uniqueId);
        const containerEl = document.getElementById('infographic-container-' + uniqueId);

        const showFeedback = (button, isSuccess, msg) => {{
            const buttonText = button.querySelector('.btn-text');
            const originalText = buttonText.textContent;
            button.disabled = true;
            buttonText.textContent = isSuccess ? '✅ ' + (msg || '成功') : '❌ 失败';
            setTimeout(() => {{
                buttonText.textContent = originalText;
                button.disabled = false;
            }}, 2000);
        }};

        const downloadFile = (content, filename, mimeType) => {{
            const blob = new Blob([content], {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }};

        if (downloadSvgBtn) {{
            downloadSvgBtn.addEventListener('click', (event) => {{
                event.stopPropagation();
                const svgEl = containerEl.querySelector('svg');
                if (svgEl) {{
                    const svgData = new XMLSerializer().serializeToString(svgEl);
                    downloadFile(svgData, 'infographic_' + uniqueId + '.svg', 'image/svg+xml');
                    showFeedback(downloadSvgBtn, true, '已下载');
                }} else {{
                    showFeedback(downloadSvgBtn, false);
                }}
            }});
        }}

        if (downloadPngBtn) {{
            downloadPngBtn.addEventListener('click', (event) => {{
                event.stopPropagation();
                const svgEl = containerEl.querySelector('svg');
                if (svgEl) {{
                    // 获取 SVG 的实际尺寸
                    const bbox = svgEl.getBoundingClientRect();
                    const width = bbox.width || svgEl.viewBox?.baseVal?.width || 800;
                    const height = bbox.height || svgEl.viewBox?.baseVal?.height || 600;
                    
                    // 克隆 SVG 并设置明确的宽高
                    const clonedSvg = svgEl.cloneNode(true);
                    clonedSvg.setAttribute('width', width);
                    clonedSvg.setAttribute('height', height);
                    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                    
                    const svgData = new XMLSerializer().serializeToString(clonedSvg);
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const img = new Image();
                    
                    // 使用 Base64 编码避免特殊字符问题
                    const base64Data = btoa(unescape(encodeURIComponent(svgData)));
                    const dataUrl = 'data:image/svg+xml;base64,' + base64Data;
                    
                    img.onload = () => {{
                        const scale = 2;
                        canvas.width = width * scale;
                        canvas.height = height * scale;
                        ctx.scale(scale, scale);
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, width, height);
                        
                        canvas.toBlob((blob) => {{
                            if (blob) {{
                                const pngUrl = URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = pngUrl;
                                a.download = 'infographic_' + uniqueId + '.png';
                                a.click();
                                URL.revokeObjectURL(pngUrl);
                                showFeedback(downloadPngBtn, true, '已下载');
                            }} else {{
                                console.error('[Infographic] PNG blob 创建失败');
                                showFeedback(downloadPngBtn, false);
                            }}
                        }}, 'image/png');
                    }};
                    
                    img.onerror = (err) => {{
                        console.error('[Infographic] SVG 转图片失败:', err);
                        showFeedback(downloadPngBtn, false);
                    }};
                    
                    img.src = dataUrl;
                }} else {{
                    showFeedback(downloadPngBtn, false);
                }}
            }});
        }}

        if (downloadHtmlBtn) {{
            downloadHtmlBtn.addEventListener('click', (event) => {{
                event.stopPropagation();
                const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>信息图</title>
    <script src="https://registry.npmmirror.com/@antv/infographic/0.2.1/files/dist/infographic.min.js"><\\/script>
    <style>
        body {{ margin: 0; padding: 20px; background: #f5f5f5; }}
        #container {{ background: white; border-radius: 8px; padding: 20px; max-width: 900px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        const {{ Infographic }} = AntVInfographic;
        const instance = new Infographic({{
            container: '#container',
            width: '100%',
            padding: 24,
        }});
        instance.render(\`${{syntaxContent.replace(/`/g, '\\\\`')}}\`);
    <\\/script>
</body>
</html>`;
                downloadFile(htmlContent, 'infographic_' + uniqueId + '.html', 'text/html');
                showFeedback(downloadHtmlBtn, true, '已下载');
            }});
        }}
    }};

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', renderInfographic);
    }} else {{
        renderInfographic();
    }}
}})();
</script>
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True, description="是否在聊天界面显示操作状态更新。"
        )
        MODEL_ID: str = Field(
            default="",
            description="用于文本分析的内置LLM模型ID。如果为空，则使用当前对话的模型。",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=100,
            description="进行信息图分析所需的最小文本长度（字符数）。",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="是否强制清除旧的插件结果（如果为 True，则不合并，直接覆盖）。",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="用于生成的最近消息数量。设置为1仅使用最后一条消息，更大值可包含更多上下文。",
        )
        OUTPUT_MODE: str = Field(
            default="image",
            description="输出模式：'html' 为交互式HTML，'image' 将嵌入为Markdown图片（默认）。",
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="是否在浏览器控制台打印调试日志。",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.weekday_map = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日",
        }

    async def _get_user_context(
        self,
        __user__: Optional[Dict[str, Any]],
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> Dict[str, str]:
        """安全提取用户上下文信息。"""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id", "unknown_user")
        user_name = user_data.get("name", "用户")
        user_language = user_data.get("language", "zh-CN")

        if __event_call__:
            try:
                js_code = """
                    return (
                        localStorage.getItem('locale') || 
                        localStorage.getItem('language') || 
                        navigator.language || 
                        'zh-CN'
                    );
                """
                frontend_lang = await __event_call__(
                    {"type": "execute", "data": {"code": js_code}}
                )
                if frontend_lang and isinstance(frontend_lang, str):
                    user_language = frontend_lang
            except Exception as e:
                pass

        return {
            "user_id": user_id,
            "user_name": user_name,
            "user_language": user_language,
        }

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        统一提取聊天上下文信息 (chat_id, message_id)。
        优先从 body 中提取，其次从 metadata 中提取。
        """
        chat_id = ""
        message_id = ""

        # 1. 尝试从 body 获取
        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")  # message_id 在 body 中通常是 id

            # 再次检查 body.metadata
            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        # 2. 尝试从 __metadata__ 获取 (作为补充)
        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

    def _extract_infographic_syntax(self, llm_output: str) -> str:
        """提取LLM输出中的infographic语法"""
        # 1. 优先匹配 ```infographic
        match = re.search(r"```infographic\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            return match.group(1).strip().replace("</script>", "<\\/script>")

        # 2. 其次匹配 ```mermaid (有时 LLM 会混淆)
        match = re.search(r"```mermaid\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 简单检查是否包含 infographic 关键字
            if "infographic" in content or "data" in content:
                return content.replace("</script>", "<\\/script>")

        # 3. 再次匹配通用 ``` (无语言标记)
        match = re.search(r"```\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # 简单的启发式检查
            if "infographic" in content or "data" in content:
                return content.replace("</script>", "<\\/script>")

        # 4. 兜底：如果看起来像直接输出了语法（以 infographic 或 list-grid 等开头）
        cleaned_output = llm_output.strip()
        first_line = cleaned_output.split("\n")[0].lower()
        if (
            first_line.startswith("infographic")
            or first_line.startswith("list-")
            or first_line.startswith("tree-")
            or first_line.startswith("mindmap")
        ):
            return cleaned_output.replace("</script>", "<\\/script>")

        logger.warning("LLM输出未严格遵循预期格式，将整个输出作为语法处理。")
        return cleaned_output.replace("</script>", "<\\/script>")

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """发送状态更新事件"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        """发送通知事件 (info/success/warning/error)"""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    async def _emit_debug_log(self, emitter, title: str, data: dict):
        """在浏览器控制台打印结构化调试日志"""
        if not self.valves.SHOW_DEBUG_LOG or not emitter:
            return

        try:
            js_code = f"""
                (async function() {{
                    console.group("🛠️ {title}");
                    console.log({json.dumps(data, ensure_ascii=False)});
                    console.groupEnd();
                }})();
            """

            await emitter({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            print(f"Error emitting debug log: {e}")

    def _remove_existing_html(self, content: str) -> str:
        """移除内容中已有的插件生成 HTML 代码块"""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _extract_text_content(self, content) -> str:
        """从消息内容中提取文本，支持多模态消息格式"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # 多模态消息: [{"type": "text", "text": "..."}, {"type": "image_url", ...}]
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)
        return str(content) if content else ""

    def _merge_html(
        self,
        existing_html_code: str,
        new_content: str,
        new_styles: str = "",
        new_scripts: str = "",
        user_language: str = "zh-CN",
    ) -> str:
        """将新内容合并到现有的 HTML 容器中，或者创建一个新的容器"""
        if (
            "<!-- OPENWEBUI_PLUGIN_OUTPUT -->" in existing_html_code
            and "<!-- CONTENT_INSERTION_POINT -->" in existing_html_code
        ):
            base_html = existing_html_code
            base_html = re.sub(r"^```html\s*", "", base_html)
            base_html = re.sub(r"\s*```$", "", base_html)
        else:
            base_html = HTML_WRAPPER_TEMPLATE.replace("{user_language}", user_language)

        wrapped_content = f'<div class="plugin-item">\n{new_content}\n</div>'

        if new_styles:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n/* STYLES_INSERTION_POINT */",
            )

        base_html = base_html.replace(
            "<!-- CONTENT_INSERTION_POINT -->",
            f"{wrapped_content}\n<!-- CONTENT_INSERTION_POINT -->",
        )

        if new_scripts:
            base_html = base_html.replace(
                "<!-- SCRIPTS_INSERTION_POINT -->",
                f"{new_scripts}\n<!-- SCRIPTS_INSERTION_POINT -->",
            )

        return base_html.strip()

    def _generate_image_js_code(
        self,
        unique_id: str,
        chat_id: str,
        message_id: str,
        infographic_syntax: str,
    ) -> str:
        """生成前端 SVG 渲染和图片嵌入的 JavaScript 代码"""

        # 转义语法以便在 JS 中嵌入
        syntax_escaped = (
            infographic_syntax.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
            .replace("</script>", "<\\/script>")
        )

        return f"""
(async function() {{
    const uniqueId = "{unique_id}";
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    const defaultWidth = 1100;
    const defaultHeight = 500;
    
    // 自动检测聊天容器宽度以实现响应式尺寸
    let svgWidth = defaultWidth;
    let svgHeight = defaultHeight;
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {{
        const containerWidth = chatContainer.clientWidth;
        if (containerWidth > 100) {{
            // 使用容器宽度的 80%（右边留更多空间）
            svgWidth = Math.floor(containerWidth * 0.8);
            // 根据默认尺寸保持宽高比
            svgHeight = Math.floor(svgWidth * (defaultHeight / defaultWidth));
            console.log("[Infographic Image] 自动检测容器宽度:", containerWidth, "-> SVG:", svgWidth, "x", svgHeight);
        }}
    }}
    
    console.log("[Infographic Image] 开始渲染...");
    console.log("[Infographic Image] chatId:", chatId, "messageId:", messageId);
    
    try {{
        // 加载 AntV Infographic（如果未加载）
        if (typeof AntVInfographic === 'undefined') {{
            console.log("[Infographic Image] 加载 AntV Infographic...");
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://registry.npmmirror.com/@antv/infographic/0.2.1/files/dist/infographic.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
        }}
        
        const {{ Infographic }} = AntVInfographic;
        
        // 获取语法内容
        let syntaxContent = `{syntax_escaped}`;
        console.log("[Infographic Image] 语法长度:", syntaxContent.length);
        
        // 清理语法：移除代码块标记
        const backtick = String.fromCharCode(96);
        const prefix = backtick + backtick + backtick + 'infographic';
        const simplePrefix = backtick + backtick + backtick;
        
        if (syntaxContent.toLowerCase().startsWith(prefix)) {{
            syntaxContent = syntaxContent.substring(prefix.length).trim();
        }} else if (syntaxContent.startsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(simplePrefix.length).trim();
        }}
        
        if (syntaxContent.endsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(0, syntaxContent.length - simplePrefix.length).trim();
        }}
        
        // 修复语法：移除关键字后的冒号
        syntaxContent = syntaxContent.replace(/^(data|items|children|theme|config):/gm, '$1');
        syntaxContent = syntaxContent.replace(/(\\s)(children|items):/g, '$1$2');
        
        // 确保 infographic 前缀
        if (!syntaxContent.trim().toLowerCase().startsWith('infographic')) {{
            const firstWord = syntaxContent.trim().split(/\\s+/)[0].toLowerCase();
            if (!['data', 'theme', 'design', 'items'].includes(firstWord)) {{
                syntaxContent = 'infographic ' + syntaxContent;
            }}
        }}
        
        // 模板映射
        const TEMPLATE_MAPPING = {{
            'list-grid': 'list-grid-compact-card',
            'list-vertical': 'list-column-simple-vertical-arrow',
            'tree-vertical': 'hierarchy-tree-tech-style-capsule-item',
            'tree-horizontal': 'hierarchy-tree-lr-tech-style-capsule-item',
            'mindmap': 'hierarchy-mindmap-branch-gradient-capsule-item',
            'sequence-roadmap': 'sequence-roadmap-vertical-simple',
            'sequence-zigzag': 'sequence-horizontal-zigzag-simple',
            'sequence-horizontal': 'sequence-horizontal-zigzag-simple',
            'relation-sankey': 'relation-sankey-simple',
            'relation-circle': 'relation-circle-icon-badge',
            'compare-binary': 'compare-binary-horizontal-simple-vs',
            'compare-swot': 'compare-swot',
            'quadrant-quarter': 'quadrant-quarter-simple-card',
            'statistic-card': 'list-grid-compact-card',
            'chart-bar': 'chart-bar-plain-text',
            'chart-column': 'chart-column-simple',
            'chart-line': 'chart-line-plain-text',
            'chart-area': 'chart-area-simple',
            'chart-pie': 'chart-pie-plain-text',
            'chart-doughnut': 'chart-pie-donut-plain-text'
        }};
        
        for (const [key, value] of Object.entries(TEMPLATE_MAPPING)) {{
            const regex = new RegExp(`infographic\\\\s+${{key}}(?=\\\\s|$)`, 'i');
            if (regex.test(syntaxContent)) {{
                syntaxContent = syntaxContent.replace(regex, `infographic ${{value}}`);
                break;
            }}
        }}
        
        // 创建离屏容器
        const container = document.createElement('div');
        container.id = 'infographic-offscreen-' + uniqueId;
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:' + svgWidth + 'px;height:' + svgHeight + 'px;background:#ffffff;';
        document.body.appendChild(container);
        
        // 创建信息图实例
        const instance = new Infographic({{
            container: '#' + container.id,
            width: svgWidth,
            height: svgHeight,
            padding: 12,
        }});
        
        console.log("[Infographic Image] 渲染信息图...");
        instance.render(syntaxContent);
        
        // 等待渲染完成
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 获取 SVG 元素
        const svgEl = container.querySelector('svg');
        if (!svgEl) {{
            throw new Error('渲染后未找到 SVG 元素');
        }}
        
        // 获取实际尺寸
        const bbox = svgEl.getBoundingClientRect();
        const width = bbox.width || svgWidth;
        const height = bbox.height || svgHeight;
        
        // 克隆并准备导出的 SVG
        const clonedSvg = svgEl.cloneNode(true);
        clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
        clonedSvg.setAttribute('width', width);
        clonedSvg.setAttribute('height', height);
        
        // 添加背景矩形
        const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bgRect.setAttribute('width', '100%');
        bgRect.setAttribute('height', '100%');
        bgRect.setAttribute('fill', '#ffffff');
        clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);
        
        // 序列化 SVG 为字符串
        const svgData = new XMLSerializer().serializeToString(clonedSvg);
        
        // 清理容器
        document.body.removeChild(container);
        
        // 使用 canvas 将 SVG 转换为 PNG 以提高兼容性
        console.log("[Infographic Image] 正在将 SVG 转换为 PNG...");
        const pngBlob = await new Promise((resolve, reject) => {{
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const scale = 2; // 更高分辨率以提高清晰度
            canvas.width = Math.round(width * scale);
            canvas.height = Math.round(height * scale);
            
            // 填充白色背景
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.scale(scale, scale);
            
            const img = new Image();
            img.onload = () => {{
                ctx.drawImage(img, 0, 0, width, height);
                canvas.toBlob((blob) => {{
                    if (blob) {{
                        resolve(blob);
                    }} else {{
                        reject(new Error('Canvas toBlob 失败'));
                    }}
                }}, 'image/png');
            }};
            img.onerror = (e) => reject(new Error('加载 SVG 图片失败: ' + e));
            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
        }});
        
        const file = new File([pngBlob], `infographic-${{uniqueId}}.png`, {{ type: 'image/png' }});
        
        // 上传文件到 OpenWebUI API
        console.log("[Infographic Image] 上传 PNG 文件...");
        const token = localStorage.getItem("token");
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadResponse = await fetch('/api/v1/files/', {{
            method: 'POST',
            headers: {{
                'Authorization': `Bearer ${{token}}`
            }},
            body: formData
        }});
        
        if (!uploadResponse.ok) {{
            throw new Error(`上传失败: ${{uploadResponse.statusText}}`);
        }}
        
        const fileData = await uploadResponse.json();
        const fileId = fileData.id;
        const imageUrl = `/api/v1/files/${{fileId}}/content`;
        
        console.log("[Infographic Image] PNG 文件已上传, ID:", fileId);
        
        // 生成带文件 URL 的 markdown 图片
        const markdownImage = `![📊 信息图](${{imageUrl}})`;
        
        // 通过 API 更新消息
        if (chatId && messageId) {{
            
            // 带重试逻辑的辅助函数
            const fetchWithRetry = async (url, options, retries = 3) => {{
                for (let i = 0; i < retries; i++) {{
                    try {{
                        const response = await fetch(url, options);
                        if (response.ok) return response;
                        if (i < retries - 1) {{
                            console.log(`[Infographic Image] 重试 ${{i + 1}}/${{retries}} for ${{url}}`);
                            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
                        }}
                    }} catch (e) {{
                        if (i === retries - 1) throw e;
                        await new Promise(r => setTimeout(r, 1000 * (i + 1)));
                    }}
                }}
                return null;
            }};
            
            // 获取当前聊天数据
            const getResponse = await fetch(`/api/v1/chats/${{chatId}}`, {{
                method: "GET",
                headers: {{ "Authorization": `Bearer ${{token}}` }}
            }});
            
            if (!getResponse.ok) {{
                throw new Error("获取聊天数据失败: " + getResponse.status);
            }}
            
            const chatData = await getResponse.json();
            let updatedMessages = [];
            let newContent = "";
            
            if (chatData.chat && chatData.chat.messages) {{
                updatedMessages = chatData.chat.messages.map(m => {{
                    if (m.id === messageId) {{
                        const originalContent = m.content || "";
                        // 移除已有的信息图图片
                        const infographicPattern = /\\n*!\\[📊[^\\]]*\\]\\((?:data:image\\/[^)]+|(?:\\/api\\/v1\\/files\\/[^)]+))\\)/g;
                        let cleanedContent = originalContent.replace(infographicPattern, "");
                        cleanedContent = cleanedContent.replace(/\\n{{3,}}/g, "\\n\\n").trim();
                        // 追加新图片
                        newContent = cleanedContent + "\\n\\n" + markdownImage;
                        
                        // 同时更新 history 对象
                        if (chatData.chat.history && chatData.chat.history.messages) {{
                            if (chatData.chat.history.messages[messageId]) {{
                                chatData.chat.history.messages[messageId].content = newContent;
                            }}
                        }}
                        
                        return {{ ...m, content: newContent }};
                    }}
                    return m;
                }});
            }}
            
            if (!newContent) {{
                console.warn("[Infographic Image] 找不到要更新的消息");
                return;
            }}
            
            // 尝试通过事件 API 更新前端显示
            try {{
                await fetch(`/api/v1/chats/${{chatId}}/messages/${{messageId}}/event`, {{
                    method: "POST",
                    headers: {{
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${{token}}`
                    }},
                    body: JSON.stringify({{
                        type: "chat:message",
                        data: {{ content: newContent }}
                    }})
                }});
            }} catch (eventErr) {{
                console.log("[Infographic Image] 事件 API 不可用，继续...");
            }}
            
            // 持久化到数据库
            const updatePayload = {{
                chat: {{
                    ...chatData.chat,
                    messages: updatedMessages
                }}
            }};
            
            const persistResponse = await fetchWithRetry(`/api/v1/chats/${{chatId}}`, {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${{token}}`
                }},
                body: JSON.stringify(updatePayload)
            }});
            
            if (persistResponse && persistResponse.ok) {{
                console.log("[Infographic Image] ✅ 消息持久化成功!");
            }} else {{
                console.error("[Infographic Image] ❌ 重试后消息持久化失败");
            }}
        }} else {{
            console.warn("[Infographic Image] ⚠️ 缺少 chatId 或 messageId，无法持久化");
        }}
        
    }} catch (error) {{
        console.error("[Infographic Image] 错误:", error);
    }}
}})();
"""

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __metadata__: Optional[dict] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: 信息图启动 (v1.4.0)")

        # 获取用户信息
        user_ctx = await self._get_user_context(__user__, __event_call__)
        user_name = user_ctx["user_name"]
        user_id = user_ctx["user_id"]
        user_language = user_ctx["user_language"]

        # 获取当前时间
        now = datetime.now()
        current_date_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
        current_weekday_en = now.strftime("%A")
        current_weekday = self.weekday_map.get(current_weekday_en, current_weekday_en)
        current_year = now.strftime("%Y")

        original_content = ""
        try:
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("无法获取有效的用户消息内容。")

            # 根据 MESSAGE_COUNT 获取最近 N 条消息
            message_count = min(self.valves.MESSAGE_COUNT, len(messages))
            recent_messages = messages[-message_count:]

            # 聚合选中消息的内容，带标签
            aggregated_parts = []
            for i, msg in enumerate(recent_messages, 1):
                text_content = self._extract_text_content(msg.get("content"))
                if text_content:
                    role = msg.get("role", "unknown")
                    role_label = (
                        "用户"
                        if role == "user"
                        else "助手" if role == "assistant" else role
                    )
                    aggregated_parts.append(f"{text_content}")

            if not aggregated_parts:
                raise ValueError("无法获取有效的用户消息内容。")

            original_content = "\n\n---\n\n".join(aggregated_parts)

            # 提取非HTML部分的文本
            parts = re.split(r"```html.*?```", original_content, flags=re.DOTALL)
            long_text_content = ""
            if parts:
                for part in reversed(parts):
                    if part.strip():
                        long_text_content = part.strip()
                        break

            if not long_text_content:
                long_text_content = original_content.strip()

            # 检查文本长度
            if len(long_text_content) < self.valves.MIN_TEXT_LENGTH:
                short_text_message = f"文本内容过短({len(long_text_content)}字符)，无法进行有效分析。请提供至少{self.valves.MIN_TEXT_LENGTH}字符的文本。"
                await self._emit_notification(
                    __event_emitter__, short_text_message, "warning"
                )
                return {
                    "messages": [
                        {"role": "assistant", "content": f"⚠️ {short_text_message}"}
                    ]
                }

            await self._emit_notification(
                __event_emitter__, "📊 信息图已启动，正在生成...", "info"
            )
            await self._emit_status(__event_emitter__, "📊 信息图: 开始生成...", False)

            # 生成唯一ID
            unique_id = f"id_{int(time.time() * 1000)}"

            # 构建提示词
            await self._emit_status(
                __event_emitter__, "📊 信息图: 正在调用 AI 模型分析内容...", False
            )
            formatted_user_prompt = USER_PROMPT_GENERATE_INFOGRAPHIC.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                user_language=user_language,
                long_text_content=long_text_content,
            )

            # 确定使用的模型
            target_model = self.valves.MODEL_ID
            if not target_model:
                target_model = body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_INFOGRAPHIC_ASSISTANT},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "stream": False,
            }

            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"无法获取用户对象，用户ID: {user_id}")

            llm_response = await generate_chat_completion(
                __request__, llm_payload, user_obj
            )

            if (
                not llm_response
                or "choices" not in llm_response
                or not llm_response["choices"]
            ):
                raise ValueError("无效的 LLM 响应格式或为空。")

            await self._emit_status(
                __event_emitter__, "📊 信息图: AI 分析完成，正在解析语法...", False
            )

            assistant_response_content = llm_response["choices"][0]["message"][
                "content"
            ]
            infographic_syntax = self._extract_infographic_syntax(
                assistant_response_content
            )

            # 准备内容组件
            await self._emit_status(
                __event_emitter__, "📊 信息图: 正在渲染图表...", False
            )
            content_html = (
                CONTENT_TEMPLATE_INFOGRAPHIC.replace("{unique_id}", unique_id)
                .replace("{user_name}", user_name)
                .replace("{current_date_time_str}", current_date_time_str)
                .replace("{current_year}", current_year)
                .replace("{infographic_syntax}", infographic_syntax)
            )

            # 先替换占位符，然后将 {{ 转为 { 和 }} 转为 }
            script_html = SCRIPT_TEMPLATE_INFOGRAPHIC.replace("{unique_id}", unique_id)
            script_html = script_html.replace("{{", "{").replace("}}", "}")

            # 提取现有HTML（如果有）
            existing_html_block = ""
            match = re.search(
                r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
                original_content,
            )
            if match:
                existing_html_block = match.group(1)

            if self.valves.CLEAR_PREVIOUS_HTML:
                original_content = self._remove_existing_html(original_content)
                final_html = self._merge_html(
                    "",
                    content_html,
                    CSS_TEMPLATE_INFOGRAPHIC,
                    script_html,
                    user_language,
                )
            else:
                if existing_html_block:
                    original_content = self._remove_existing_html(original_content)
                    final_html = self._merge_html(
                        existing_html_block,
                        content_html,
                        CSS_TEMPLATE_INFOGRAPHIC,
                        script_html,
                        user_language,
                    )
                else:
                    final_html = self._merge_html(
                        "",
                        content_html,
                        CSS_TEMPLATE_INFOGRAPHIC,
                        script_html,
                        user_language,
                    )

            # 检查输出模式
            if self.valves.OUTPUT_MODE == "image":
                # 图片模式：使用 JavaScript 渲染并嵌入为 Markdown 图片
                chat_ctx = self._get_chat_context(body, __metadata__)
                chat_id = chat_ctx["chat_id"]
                message_id = chat_ctx["message_id"]

                await self._emit_status(
                    __event_emitter__,
                    "📊 信息图: 正在渲染图片...",
                    False,
                )

                if __event_call__:
                    js_code = self._generate_image_js_code(
                        unique_id=unique_id,
                        chat_id=chat_id,
                        message_id=message_id,
                        infographic_syntax=infographic_syntax,
                    )

                    await __event_call__(
                        {
                            "type": "execute",
                            "data": {"code": js_code},
                        }
                    )

                await self._emit_status(
                    __event_emitter__, "✅ 信息图: 图片生成完成!", True
                )
                await self._emit_notification(
                    __event_emitter__,
                    f"📊 信息图图片已生成，{user_name}！",
                    "success",
                )
                logger.info("信息图生成完成（图片模式）")
                return body

            # HTML 模式（默认）：嵌入为 HTML 块
            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"

            await self._emit_status(__event_emitter__, "✅ 信息图: 生成完成!", True)
            await self._emit_notification(
                __event_emitter__,
                f"📊 信息图已生成，{user_name}！",
                "success",
            )
            logger.info("信息图生成完成")

        except Exception as e:
            error_message = f"信息图处理失败: {str(e)}"
            logger.error(f"信息图错误: {error_message}", exc_info=True)
            user_facing_error = f"抱歉，信息图在处理时遇到错误: {str(e)}。\n请检查Open WebUI后端日志获取更多详情。"
            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n❌ **错误:** {user_facing_error}"

            await self._emit_status(__event_emitter__, "❌ 信息图: 生成失败", True)
            await self._emit_notification(
                __event_emitter__, f"❌ 信息图生成失败, {user_name}!", "error"
            )

        return body
