"""
title: 思维导图
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.8.0
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxyZWN0IHg9IjE2IiB5PSIxNiIgd2lkdGg9IjYiIGhlaWdodD0iNiIgcng9IjEiLz48cmVjdCB4PSIyIiB5PSIxNiIgd2lkdGg9IjYiIGhlaWdodD0iNiIgcng9IjEiLz48cmVjdCB4PSI5IiB5PSIyIiB3aWR0aD0iNiIgaGVpZ2h0PSI2IiByeD0iMSIvPjxwYXRoIGQ9Ik01IDE2di0zYTEgMSAwIDAgMSAxLTFoMTJhMSAxIDAgMCAxIDEgMXYzIi8+PHBhdGggZD0iTTEyIDEyVjgiLz48L3N2Zz4=
description: 智能分析文本内容,生成交互式思维导图,帮助用户结构化和可视化知识。
"""

import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import Request
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_MINDMAP_ASSISTANT = """
你是一个专业的思维导图生成助手,能够高效地分析用户提供的长篇文本,并将其核心主题、关键概念、分支和子分支结构化为标准的Markdown列表语法,以便Markmap.js进行渲染。

请严格遵循以下指导原则:
-   **语言**: 所有输出必须使用用户指定的语言。
-   **格式**: 你的输出必须严格为Markdown列表格式,并用```markdown 和 ``` 包裹。
    -   使用 `#` 定义中心主题(根节点)。
    -   使用 `-` 和两个空格的缩进表示分支和子分支。
-   **内容**:
    -   识别文本的中心主题作为 `#` 标题。
    -   识别主要概念作为一级列表项。
    -   识别支持性细节或子概念作为嵌套的列表项。
    -   节点内容应简洁明了,避免冗长。
-   **只输出Markdown语法**: 不要包含任何额外的寒暄、解释或引导性文字。
-   **如果文本过短或无法生成有效导图**: 请输出一个简单的Markdown列表,表示无法生成,例如:
    ```markdown
    # 无法生成思维导图
    - 原因: 文本内容不足或不明确
    ```
"""

USER_PROMPT_GENERATE_MINDMAP = """
请分析以下长篇文本,并将其核心主题、关键概念、分支和子分支结构化为标准的Markdown列表语法,以供Markmap.js渲染。

---
**用户上下文信息:**
用户姓名: {user_name}
当前日期时间: {current_date_time_str}
当前星期: {current_weekday}
当前时区: {current_timezone_str}
用户语言: {user_language}
---

**长篇文本内容:**
{long_text_content}
"""

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
            flex-direction: column; 
            gap: 20px; 
            align-items: stretch; 
            width: 100%;
        }
        .plugin-item { 
            width: 100%; 
            border-radius: 12px; 
            overflow: visible; 
            transition: all 0.3s ease;
        }
        .plugin-item:hover {
            transform: translateY(-2px);
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

CSS_TEMPLATE_MINDMAP = """
        :root {
            --primary-color: #1e88e5;
            --secondary-color: #43a047;
            --background-color: #f4f6f8;
            --card-bg-color: #ffffff;
            --text-color: #000000;
            --link-color: #546e7a;
            --node-stroke-color: #90a4ae;
            --muted-text-color: #546e7a;
            --border-color: #e0e0e0;
            --header-gradient: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            --shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
            --border-radius: 12px;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .theme-dark {
            --primary-color: #64b5f6;
            --secondary-color: #81c784;
            --background-color: #111827;
            --card-bg-color: #1f2937;
            --text-color: #ffffff;
            --link-color: #cbd5e1;
            --node-stroke-color: #94a3b8;
            --muted-text-color: #9ca3af;
            --border-color: #374151;
            --header-gradient: linear-gradient(135deg, #0ea5e9, #22c55e);
            --shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }
        .mindmap-container-wrapper {
            font-family: var(--font-family);
            line-height: 1.6;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            height: 100%;
            display: flex;
            flex-direction: column;
            background: var(--background-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
        }
        .header {
            background: var(--header-gradient);
            color: white;
            padding: 18px 20px;
            text-align: center;
            border-top-left-radius: var(--border-radius);
            border-top-right-radius: var(--border-radius);
        }
        .header h1 {
            margin: 0;
            font-size: 1.4em;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .user-context {
            font-size: 0.85em;
            color: var(--muted-text-color);
            background-color: rgba(255, 255, 255, 0.6);
            padding: 8px 14px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
            gap: 6px;
        }
        .theme-dark .user-context {
            background-color: rgba(31, 41, 55, 0.7);
        }
        .user-context span { margin: 2px 6px; }
        .content-area {
            padding: 16px;
            flex-grow: 1;
            background: var(--card-bg-color);
        }
        .markmap-container {
            position: relative;
            background-color: var(--card-bg-color);
            border-radius: 10px;
            padding: 12px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid var(--border-color);
            width: 100%;
            min-height: 60vh;
            overflow: visible;
        }
        .markmap-container svg {
            width: 100%;
            height: 100%;
        }
        .markmap-container svg text {
            fill: var(--text-color) !important;
            font-family: var(--font-family);
        }
        .markmap-container svg foreignObject,
        .markmap-container svg .markmap-foreign,
        .markmap-container svg .markmap-foreign div {
            color: var(--text-color) !important;
            font-family: var(--font-family);
        }
        .markmap-container svg .markmap-link {
            stroke: var(--link-color) !important;
        }
        .markmap-container svg .markmap-node circle,
        .markmap-container svg .markmap-node rect {
            stroke: var(--node-stroke-color) !important;
        }
        .control-rows {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-top: 12px;
        }
        .btn-group {
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }
        .control-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.15s ease, transform 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            height: 36px;
            box-sizing: border-box;
        }
        select.control-btn {
            appearance: none;
            padding-right: 28px;
            background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23FFFFFF%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
            background-repeat: no-repeat;
            background-position: right 8px center;
            background-size: 10px;
        }
        .control-btn.secondary { background-color: var(--secondary-color); }
        .control-btn.neutral { background-color: #64748b; }
        .control-btn:hover { transform: translateY(-1px); }
        .control-btn.copied { background-color: #2e7d32; }
        .control-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .footer {
            text-align: center;
            padding: 12px;
            font-size: 0.85em;
            color: var(--muted-text-color);
            background-color: var(--card-bg-color);
            border-top: 1px solid var(--border-color);
            border-bottom-left-radius: var(--border-radius);
            border-bottom-right-radius: var(--border-radius);
        }

        .footer a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }
        .footer a:hover { text-decoration: underline; }
        .error-message {
            color: #c62828;
            background-color: #ffcdd2;
            border: 1px solid #ef9a9a;
            padding: 14px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 1em;
        }
"""

CONTENT_TEMPLATE_MINDMAP = """
        <div class="mindmap-container-wrapper">
            <div class="header">
                <h1>🧠 智能思维导图</h1>
            </div>
            <div class="user-context">
                <span><strong>用户:</strong> {user_name}</span>
                <span><strong>时间:</strong> {current_date_time_str}</span>
            </div>
            <div class="content-area">
                <div class="markmap-container" id="markmap-container-{unique_id}"></div>
                <div class="control-rows">
                    <div class="btn-group">
                        <button id="download-png-btn-{unique_id}" class="control-btn secondary">
                            <span class="btn-text">PNG</span>
                        </button>
                        <button id="download-svg-btn-{unique_id}" class="control-btn">
                            <span class="btn-text">SVG</span>
                        </button>
                        <button id="download-md-btn-{unique_id}" class="control-btn neutral">
                            <span class="btn-text">Markdown</span>
                        </button>
                    </div>
                    <div class="btn-group">
                        <button id="zoom-out-btn-{unique_id}" class="control-btn neutral" title="缩小">-</button>
                        <button id="zoom-reset-btn-{unique_id}" class="control-btn neutral" title="重置">重置</button>
                        <button id="zoom-in-btn-{unique_id}" class="control-btn neutral" title="放大">+</button>
                    </div>
                    <div class="btn-group">
                        <select id="depth-select-{unique_id}" class="control-btn secondary" title="展开层级">
                            <option value="0" selected>全部展开</option>
                            <option value="2">展开 2 级</option>
                            <option value="3">展开 3 级</option>
                        </select>
                        <button id="fullscreen-btn-{unique_id}" class="control-btn">全屏</button>
                        <button id="theme-toggle-btn-{unique_id}" class="control-btn neutral">主题</button>
                    </div>
                </div>
            </div>
            <div class="footer">
                <p>© {current_year} 智能思维导图 • <a href="https://markmap.js.org/" target="_blank">Markmap</a></p>
            </div>
        </div>
        
        <script type="text/template" id="markdown-source-{unique_id}">{markdown_syntax}</script>
"""

SCRIPT_TEMPLATE_MINDMAP = """
    <script>
      (function() {
        const uniqueId = "{unique_id}";

        const loadScriptOnce = (src, checkFn) => {
            if (checkFn()) return Promise.resolve();
            return new Promise((resolve, reject) => {
                const existing = document.querySelector(`script[data-src="${src}"]`);
                if (existing) {
                    existing.addEventListener('load', () => resolve());
                    existing.addEventListener('error', () => reject(new Error('加载失败: ' + src)));
                    return;
                }
                const script = document.createElement('script');
                script.src = src;
                script.async = true;
                script.dataset.src = src;
                script.onload = () => resolve();
                script.onerror = () => reject(new Error('加载失败: ' + src));
                document.head.appendChild(script);
            });
        };

        const ensureMarkmapReady = () =>
            loadScriptOnce('https://cdn.jsdelivr.net/npm/d3@7', () => window.d3)
                .then(() => loadScriptOnce('https://cdn.jsdelivr.net/npm/markmap-lib@0.17', () => window.markmap && window.markmap.Transformer))
                .then(() => loadScriptOnce('https://cdn.jsdelivr.net/npm/markmap-view@0.17', () => window.markmap && window.markmap.Markmap));

        const parseColorLuma = (colorStr) => {
            if (!colorStr) return null;
            // hex #rrggbb or rrggbb
            let m = colorStr.match(/^#?([0-9a-f]{6})$/i);
            if (m) {
                const hex = m[1];
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            // rgb(r, g, b) or rgba(r, g, b, a)
            m = colorStr.match(/rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
            if (m) {
                const r = parseInt(m[1], 10);
                const g = parseInt(m[2], 10);
                const b = parseInt(m[3], 10);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            return null;
        };

        const getThemeFromMeta = (doc, scope = 'self') => {
            const metas = Array.from((doc || document).querySelectorAll('meta[name="theme-color"]'));
            if (!metas.length) return null;
            const color = metas[metas.length - 1].content.trim();
            const luma = parseColorLuma(color);
            if (luma === null) return null;
            return luma < 0.5 ? 'dark' : 'light';
        };

        const getParentDocumentSafe = () => {
            try {
                if (!window.parent || window.parent === window) return null;
                const pDoc = window.parent.document;
                void pDoc.title;
                return pDoc;
            } catch (err) {
                return null;
            }
        };

        const getThemeFromParentClass = () => {
            try {
                if (!window.parent || window.parent === window) return null;
                const pDoc = window.parent.document;
                const html = pDoc.documentElement;
                const body = pDoc.body;
                const htmlClass = html ? html.className : '';
                const bodyClass = body ? body.className : '';
                const htmlDataTheme = html ? html.getAttribute('data-theme') : '';
                if (htmlDataTheme === 'dark' || bodyClass.includes('dark') || htmlClass.includes('dark')) return 'dark';
                if (htmlDataTheme === 'light' || bodyClass.includes('light') || htmlClass.includes('light')) return 'light';
                return null;
            } catch (err) {
                return null;
            }
        };

        const setTheme = (wrapperEl, explicitTheme) => {
            const parentDoc = getParentDocumentSafe();
            const metaThemeParent = parentDoc ? getThemeFromMeta(parentDoc, 'parent') : null;
            const parentClassTheme = getThemeFromParentClass();
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            const chosen = explicitTheme || metaThemeParent || parentClassTheme || (prefersDark ? 'dark' : 'light');
            wrapperEl.classList.toggle('theme-dark', chosen === 'dark');
            return chosen;
        };

        const renderMindmap = () => {
            const containerEl = document.getElementById('markmap-container-' + uniqueId);
            if (!containerEl || containerEl.dataset.markmapRendered) return;

            const sourceEl = document.getElementById('markdown-source-' + uniqueId);
            if (!sourceEl) return;

            const markdownContent = sourceEl.textContent.trim();
            if (!markdownContent) {
                containerEl.innerHTML = '<div class="error-message">⚠️ 无法加载思维导图：缺少有效内容。</div>';
                return;
            }

            ensureMarkmapReady().then(() => {
                const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svgEl.style.width = '100%';
                svgEl.style.height = '100%';
                svgEl.style.minHeight = '60vh';
                containerEl.innerHTML = '';
                containerEl.appendChild(svgEl);

                const { Transformer, Markmap } = window.markmap;
                const transformer = new Transformer();
                const { root } = transformer.transform(markdownContent);

                const style = (id) => `
                    ${id} text, ${id} foreignObject { font-size: 14px; }
                    ${id} foreignObject h1 { font-size: 22px; font-weight: 700; margin: 0; }
                    ${id} foreignObject h2 { font-size: 18px; font-weight: 600; margin: 0; }
                    ${id} foreignObject strong { font-weight: 700; }
                `;
                const options = {
                    autoFit: true,
                    style: style,
                    initialExpandLevel: Infinity,
                    zoom: true,
                    pan: true
                };

                const markmapInstance = Markmap.create(svgEl, options, root);
                containerEl.dataset.markmapRendered = 'true';

                setupControls({
                    containerEl,
                    svgEl,
                    markmapInstance,
                    root,
                });

            }).catch((error) => {
                console.error('Markmap loading error:', error);
                containerEl.innerHTML = '<div class="error-message">⚠️ 资源加载失败，请稍后重试。</div>';
            });
        };

        const setupControls = ({ containerEl, svgEl, markmapInstance, root }) => {
            const downloadSvgBtn = document.getElementById('download-svg-btn-' + uniqueId);
            const downloadPngBtn = document.getElementById('download-png-btn-' + uniqueId);
            const downloadMdBtn = document.getElementById('download-md-btn-' + uniqueId);
            const zoomInBtn = document.getElementById('zoom-in-btn-' + uniqueId);
            const zoomOutBtn = document.getElementById('zoom-out-btn-' + uniqueId);
            const zoomResetBtn = document.getElementById('zoom-reset-btn-' + uniqueId);
            const depthSelect = document.getElementById('depth-select-' + uniqueId);
            const fullscreenBtn = document.getElementById('fullscreen-btn-' + uniqueId);
            const themeToggleBtn = document.getElementById('theme-toggle-btn-' + uniqueId);

            const wrapper = containerEl.closest('.mindmap-container-wrapper');
            let currentTheme = setTheme(wrapper);

            const showFeedback = (button, textOk = '完成', textFail = '失败') => {
                if (!button) return;
                const buttonText = button.querySelector('.btn-text') || button;
                const originalText = buttonText.textContent;
                button.disabled = true;
                buttonText.textContent = textOk;
                button.classList.add('copied');
                setTimeout(() => {
                    buttonText.textContent = originalText;
                    button.disabled = false;
                    button.classList.remove('copied');
                }, 1800);
            };

            const copyToClipboard = (content, button) => {
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(content).then(() => showFeedback(button), () => showFeedback(button, '失败', '失败'));
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = content;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        showFeedback(button);
                    } catch (err) {
                        showFeedback(button, '失败', '失败');
                    }
                    document.body.removeChild(textArea);
                }
            };

            const handleDownloadSVG = () => {
                const svg = containerEl.querySelector('svg');
                if (!svg) return;
                // Inline styles before export
                const clonedSvg = svg.cloneNode(true);
                const style = document.createElement('style');
                style.textContent = `
                    text { font-family: sans-serif; fill: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; }
                    foreignObject, .markmap-foreign, .markmap-foreign div { color: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; font-family: sans-serif; font-size: 14px; }
                    h1 { font-size: 22px; font-weight: 700; margin: 0; }
                    h2 { font-size: 18px; font-weight: 600; margin: 0; }
                    strong { font-weight: 700; }
                    .markmap-link { stroke: ${currentTheme === 'dark' ? '#cbd5e1' : '#546e7a'}; }
                    .markmap-node circle, .markmap-node rect { stroke: ${currentTheme === 'dark' ? '#94a3b8' : '#94a3b8'}; }
                `;
                clonedSvg.prepend(style);
                const svgData = new XMLSerializer().serializeToString(clonedSvg);
                copyToClipboard(svgData, downloadSvgBtn);
            };

            const handleDownloadMD = () => {
                const markdownContent = document.getElementById('markdown-source-' + uniqueId)?.textContent || '';
                if (!markdownContent) return;
                copyToClipboard(markdownContent, downloadMdBtn);
            };

            const handleDownloadPNG = () => {
                const btn = downloadPngBtn;
                const originalText = btn.querySelector('.btn-text').textContent;
                btn.querySelector('.btn-text').textContent = '生成中...';
                btn.disabled = true;

                const svg = containerEl.querySelector('svg');
                if (!svg) {
                    btn.querySelector('.btn-text').textContent = originalText;
                    btn.disabled = false;
                    showFeedback(btn, '失败', '失败');
                    return;
                }

                try {
                    // Clone SVG and inline styles
                    const clonedSvg = svg.cloneNode(true);
                    clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                    clonedSvg.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
                    
                    const rect = svg.getBoundingClientRect();
                    const width = rect.width || 800;
                    const height = rect.height || 600;
                    clonedSvg.setAttribute('width', width);
                    clonedSvg.setAttribute('height', height);

                    // Remove foreignObject (HTML content) and replace with text
                    const foreignObjects = clonedSvg.querySelectorAll('foreignObject');
                    foreignObjects.forEach(fo => {
                        const text = fo.textContent || '';
                        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                        const textEl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        textEl.setAttribute('x', fo.getAttribute('x') || '0');
                        textEl.setAttribute('y', (parseFloat(fo.getAttribute('y') || '0') + 14).toString());
                        textEl.setAttribute('fill', currentTheme === 'dark' ? '#ffffff' : '#000000');
                        textEl.setAttribute('font-family', 'sans-serif');
                        textEl.setAttribute('font-size', '14');
                        textEl.textContent = text.trim();
                        g.appendChild(textEl);
                        fo.parentNode.replaceChild(g, fo);
                    });

                    // Inline styles
                    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
                    style.textContent = `
                        text { font-family: sans-serif; font-size: 14px; fill: ${currentTheme === 'dark' ? '#ffffff' : '#000000'}; }
                        .markmap-link { fill: none; stroke: ${currentTheme === 'dark' ? '#cbd5e1' : '#546e7a'}; stroke-width: 2; }
                        .markmap-node circle { stroke: ${currentTheme === 'dark' ? '#94a3b8' : '#94a3b8'}; stroke-width: 2; }
                    `;
                    clonedSvg.insertBefore(style, clonedSvg.firstChild);

                    // Add background rect
                    const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    bgRect.setAttribute('width', '100%');
                    bgRect.setAttribute('height', '100%');
                    bgRect.setAttribute('fill', currentTheme === 'dark' ? '#1f2937' : '#ffffff');
                    clonedSvg.insertBefore(bgRect, clonedSvg.firstChild);

                    const svgData = new XMLSerializer().serializeToString(clonedSvg);
                    const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
                    const dataUrl = 'data:image/svg+xml;base64,' + svgBase64;

                    const img = new Image();
                    img.onload = () => {
                        const canvas = document.createElement('canvas');
                        const scale = 9;
                        canvas.width = width * scale;
                        canvas.height = height * scale;
                        const ctx = canvas.getContext('2d');
                        ctx.scale(scale, scale);
                        ctx.fillStyle = currentTheme === 'dark' ? '#1f2937' : '#ffffff';
                        ctx.fillRect(0, 0, width, height);
                        ctx.drawImage(img, 0, 0, width, height);

                        canvas.toBlob((blob) => {
                            if (!blob) {
                                btn.querySelector('.btn-text').textContent = originalText;
                                btn.disabled = false;
                                showFeedback(btn, '失败', '失败');
                                return;
                            }
                            
                            // Use non-bubbling MouseEvent to avoid router interception
                            const a = document.createElement('a');
                            a.download = '思维导图.png';
                            a.href = URL.createObjectURL(blob);
                            a.style.display = 'none';
                            document.body.appendChild(a);
                            
                            const evt = new MouseEvent('click', {
                                view: window,
                                bubbles: false,
                                cancelable: false
                            });
                            a.dispatchEvent(evt);
                            
                            setTimeout(() => {
                                document.body.removeChild(a);
                                URL.revokeObjectURL(a.href);
                            }, 100);

                            btn.querySelector('.btn-text').textContent = originalText;
                            btn.disabled = false;
                            showFeedback(btn);
                        }, 'image/png');
                    };
                    
                    img.onerror = (e) => {
                        console.error('PNG image load error:', e);
                        btn.querySelector('.btn-text').textContent = originalText;
                        btn.disabled = false;
                        showFeedback(btn, '失败', '失败');
                    };
                    
                    img.src = dataUrl;
                } catch (err) {
                    console.error('PNG export error:', err);
                    btn.querySelector('.btn-text').textContent = originalText;
                    btn.disabled = false;
                    showFeedback(btn, '失败', '失败');
                }
            };

            const handleZoom = (direction) => {
                if (direction === 'reset') {
                    markmapInstance.fit();
                    return;
                }
                // Simple zoom simulation if d3 zoom instance is not accessible
                // Markmap uses d3-zoom, so we can try to select the svg and transition
                const svg = d3.select(svgEl);
                // We can't easily access the internal zoom behavior object created by markmap
                // So we rely on fit() for reset, and maybe just let user scroll/pinch for zoom
                // Or we can try to rescale if supported
                if (markmapInstance.rescale) {
                    const scale = direction === 'in' ? 1.25 : 0.8;
                    markmapInstance.rescale(scale);
                } else {
                    // Fallback: just fit, as manual transform manipulation conflicts with d3
                    // Or we could try to find the zoom behavior attached to the node
                    // const zoom = d3.zoomTransform(svgEl);
                    // But we need the zoom behavior function to call scaleBy
                }
            };

            const handleDepthChange = (e) => {
                const level = parseInt(e.target.value, 10);
                const expandLevel = level === 0 ? Infinity : level;
                
                // Deep clone root to reset internal state (payload.fold) added by markmap
                const cleanRoot = JSON.parse(JSON.stringify(root));
                
                markmapInstance.setOptions({ initialExpandLevel: expandLevel });
                markmapInstance.setData(cleanRoot);
                markmapInstance.fit();
            };

            const handleFullscreen = () => {
                const el = containerEl;
                if (!document.fullscreenElement) {
                    el.requestFullscreen().then(() => {
                        setTimeout(() => markmapInstance.fit(), 200);
                    });
                } else {
                    document.exitFullscreen();
                }
            };
            
            document.addEventListener('fullscreenchange', () => {
                if (document.fullscreenElement === containerEl) {
                    setTimeout(() => markmapInstance.fit(), 200);
                }
            });

            const handleThemeToggle = () => {
                currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
                setTheme(wrapper, currentTheme);
            };

            downloadSvgBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadSVG(); });
            downloadMdBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadMD(); });
            downloadPngBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleDownloadPNG(); });
            zoomInBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('in'); });
            zoomOutBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('out'); });
            zoomResetBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleZoom('reset'); });
            depthSelect?.addEventListener('change', (e) => { e.stopPropagation(); handleDepthChange(e); });
            fullscreenBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleFullscreen(); });
            themeToggleBtn?.addEventListener('click', (e) => { e.stopPropagation(); handleThemeToggle(); });
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', renderMindmap);
        } else {
            renderMindmap();
        }
      })();
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
            description="进行思维导图分析所需的最小文本长度（字符数）。",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="是否强制清除旧的插件结果（如果为 True，则不合并，直接覆盖）。",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="用于生成的最近消息数量。设置为1仅使用最后一条消息，更大值可包含更多上下文。",
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

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extract basic user context with safe fallbacks."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", "unknown_user"),
            "user_name": user_data.get("name", "用户"),
            "user_language": user_data.get("language", "zh-CN"),
        }

    def _extract_markdown_syntax(self, llm_output: str) -> str:
        match = re.search(r"```markdown\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
        else:
            logger.warning(
                "LLM输出未严格遵循预期Markdown格式，将整个输出作为摘要处理。"
            )
            extracted_content = llm_output.strip()
        return extracted_content.replace("</script>", "<\\/script>")

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """发送状态更新事件。"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        """发送通知事件 (info/success/warning/error)。"""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    def _remove_existing_html(self, content: str) -> str:
        """移除内容中已有的插件生成 HTML 代码块 (通过标记识别)。"""
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
        """
        将新内容合并到现有的 HTML 容器中，或者创建一个新的容器。
        """
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

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: 思维导图 (v12 - Final Feedback Fix) started")
        user_ctx = self._get_user_context(__user__)
        user_language = user_ctx["user_language"]
        user_name = user_ctx["user_name"]
        user_id = user_ctx["user_id"]

        try:
            tz_env = os.environ.get("TZ")
            tzinfo = ZoneInfo(tz_env) if tz_env else None
            now_dt = datetime.now(tzinfo or timezone.utc)
            current_date_time_str = now_dt.strftime("%Y年%m月%d日 %H:%M:%S")
            current_weekday_en = now_dt.strftime("%A")
            current_weekday_zh = self.weekday_map.get(current_weekday_en, "未知星期")
            current_year = now_dt.strftime("%Y")
            current_timezone_str = tz_env or "UTC"
        except Exception as e:
            logger.warning(f"获取时区信息失败: {e}，使用默认值。")
            now = datetime.now()
            current_date_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
            current_weekday_zh = "未知星期"
            current_year = now.strftime("%Y")
            current_timezone_str = "未知时区"

        await self._emit_notification(
            __event_emitter__, "思维导图已启动，正在为您生成思维导图...", "info"
        )

        messages = body.get("messages")
        if not messages or not isinstance(messages, list):
            error_message = "无法获取有效的用户消息内容。"
            await self._emit_notification(__event_emitter__, error_message, "error")
            return {
                "messages": [{"role": "assistant", "content": f"❌ {error_message}"}]
            }

        # Get last N messages based on MESSAGE_COUNT
        message_count = min(self.valves.MESSAGE_COUNT, len(messages))
        recent_messages = messages[-message_count:]

        # Aggregate content from selected messages with labels
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
                aggregated_parts.append(f"[{role_label} 消息 {i}]\n{text_content}")

        if not aggregated_parts:
            error_message = "无法获取有效的用户消息内容。"
            await self._emit_notification(__event_emitter__, error_message, "error")
            return {
                "messages": [{"role": "assistant", "content": f"❌ {error_message}"}]
            }

        original_content = "\n\n---\n\n".join(aggregated_parts)

        parts = re.split(r"```html.*?```", original_content, flags=re.DOTALL)
        long_text_content = ""
        if parts:
            for part in reversed(parts):
                if part.strip():
                    long_text_content = part.strip()
                    break

        if not long_text_content:
            long_text_content = original_content.strip()

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

        await self._emit_status(
            __event_emitter__, "思维导图: 深入分析文本结构...", False
        )

        try:
            unique_id = f"id_{int(time.time() * 1000)}"

            formatted_user_prompt = USER_PROMPT_GENERATE_MINDMAP.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                current_weekday=current_weekday_zh,
                current_timezone_str=current_timezone_str,
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
                    {"role": "system", "content": SYSTEM_PROMPT_MINDMAP_ASSISTANT},
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
                raise ValueError("LLM响应格式不正确或为空。")

            assistant_response_content = llm_response["choices"][0]["message"][
                "content"
            ]
            markdown_syntax = self._extract_markdown_syntax(assistant_response_content)

            # Prepare content components
            content_html = (
                CONTENT_TEMPLATE_MINDMAP.replace("{unique_id}", unique_id)
                .replace("{user_name}", user_name)
                .replace("{current_date_time_str}", current_date_time_str)
                .replace("{current_year}", current_year)
                .replace("{markdown_syntax}", markdown_syntax)
            )

            script_html = SCRIPT_TEMPLATE_MINDMAP.replace("{unique_id}", unique_id)

            # Extract existing HTML if any
            existing_html_block = ""
            match = re.search(
                r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
                long_text_content,
            )
            if match:
                existing_html_block = match.group(1)

            if self.valves.CLEAR_PREVIOUS_HTML:
                long_text_content = self._remove_existing_html(long_text_content)
                final_html = self._merge_html(
                    "", content_html, CSS_TEMPLATE_MINDMAP, script_html, user_language
                )
            else:
                # If we found existing HTML, we remove the old block from text and merge into it
                if existing_html_block:
                    long_text_content = self._remove_existing_html(long_text_content)
                    final_html = self._merge_html(
                        existing_html_block,
                        content_html,
                        CSS_TEMPLATE_MINDMAP,
                        script_html,
                        user_language,
                    )
                else:
                    final_html = self._merge_html(
                        "",
                        content_html,
                        CSS_TEMPLATE_MINDMAP,
                        script_html,
                        user_language,
                    )

            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] = f"{long_text_content}\n\n{html_embed_tag}"

            await self._emit_status(__event_emitter__, "思维导图: 绘制完成！", True)
            await self._emit_notification(
                __event_emitter__, f"思维导图已生成，{user_name}！", "success"
            )
            logger.info("Action: 思维导图 (v12) completed successfully")

        except Exception as e:
            error_message = f"思维导图处理失败: {str(e)}"
            logger.error(f"思维导图错误: {error_message}", exc_info=True)
            user_facing_error = f"抱歉，思维导图在处理时遇到错误: {str(e)}。\n请检查Open WebUI后端日志获取更多详情。"
            body["messages"][-1][
                "content"
            ] = f"{long_text_content}\n\n❌ **错误:** {user_facing_error}"

            await self._emit_status(__event_emitter__, "思维导图: 处理失败。", True)
            await self._emit_notification(
                __event_emitter__, f"思维导图生成失败, {user_name}！", "error"
            )

        return body
