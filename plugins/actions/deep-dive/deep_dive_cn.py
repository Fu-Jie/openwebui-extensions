"""
title: 精读
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 1.0.0
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xMiA3djE0Ii8+PHBhdGggZD0iTTMgMThhMSAxIDAgMCAxLTEtMVY0YTEgMSAwIDAgMSAxLTFoNWE0IDQgMCAwIDEgNCA0IDQgNCAwIDAgMSA0LTRoNWExIDEgMCAwIDEgMSAxdjEzYTEgMSAwIDAgMS0xIDFoLTZhMyAzIDAgMCAwLTMgMyAzIDMgMCAwIDAtMy0zeiIvPjxwYXRoIGQ9Ik02IDEyaDIiLz48cGF0aCBkPSJNMTYgMTJoMiIvPjwvc3ZnPg==
requirements: markdown
description: 全方位的思维透镜 —— 从背景全景到逻辑脉络，从深度洞察到行动路径。
"""

# Standard library imports
import re
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

# Third-party imports
from pydantic import BaseModel, Field
from fastapi import Request
import markdown

# OpenWebUI imports
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================================================================
# HTML 模板 - 过程导向设计，支持主题自适应
# =================================================================
HTML_WRAPPER_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --dd-bg-primary: #ffffff;
            --dd-bg-secondary: #f8fafc;
            --dd-bg-tertiary: #f1f5f9;
            --dd-text-primary: #0f172a;
            --dd-text-secondary: #334155;
            --dd-text-dim: #64748b;
            --dd-border: #e2e8f0;
            --dd-accent: #3b82f6;
            --dd-accent-soft: #eff6ff;
            --dd-header-gradient: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            --dd-shadow: 0 10px 40px rgba(0,0,0,0.06);
            --dd-code-bg: #f1f5f9;
        }
        .theme-dark {
            --dd-bg-primary: #1e293b;
            --dd-bg-secondary: #0f172a;
            --dd-bg-tertiary: #334155;
            --dd-text-primary: #f1f5f9;
            --dd-text-secondary: #e2e8f0;
            --dd-text-dim: #94a3b8;
            --dd-border: #475569;
            --dd-accent: #60a5fa;
            --dd-accent-soft: rgba(59, 130, 246, 0.15);
            --dd-header-gradient: linear-gradient(135deg, #0f172a 0%, #1e1e2e 100%);
            --dd-shadow: 0 10px 40px rgba(0,0,0,0.3);
            --dd-code-bg: #334155;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 10px; 
            background-color: transparent; 
        }
        #main-container { 
            display: flex; 
            flex-direction: column;
            gap: 24px; 
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
        }
        .plugin-item { 
            background: var(--dd-bg-primary); 
            border-radius: 24px; 
            box-shadow: var(--dd-shadow); 
            overflow: hidden; 
            border: 1px solid var(--dd-border); 
        }
        /* STYLES_INSERTION_POINT */
    </style>
</head>
<body>
    <div id="main-container">
        <!-- CONTENT_INSERTION_POINT -->
    </div>
    <!-- SCRIPTS_INSERTION_POINT -->
    <script>
    (function() {
        const parseColorLuma = (colorStr) => {
            if (!colorStr) return null;
            let m = colorStr.match(/^#?([0-9a-f]{6})$/i);
            if (m) {
                const hex = m[1];
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            m = colorStr.match(/rgba?\\s*\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)/i);
            if (m) {
                const r = parseInt(m[1], 10);
                const g = parseInt(m[2], 10);
                const b = parseInt(m[3], 10);
                return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
            }
            return null;
        };
        const getThemeFromMeta = (doc) => {
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
            } catch (err) { return null; }
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
            } catch (err) { return null; }
        };
        const setTheme = () => {
            const parentDoc = getParentDocumentSafe();
            const metaTheme = parentDoc ? getThemeFromMeta(parentDoc) : null;
            const parentClassTheme = getThemeFromParentClass();
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            const chosen = metaTheme || parentClassTheme || (prefersDark ? 'dark' : 'light');
            document.documentElement.classList.toggle('theme-dark', chosen === 'dark');
        };
        setTheme();
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', setTheme);
        }
    })();
    </script>
</body>
</html>
"""

# =================================================================
# LLM 提示词 - 深度下潜思维链
# =================================================================

SYSTEM_PROMPT = """
你是一位“深度下潜 (Deep Dive)”分析专家。你的目标是引导用户完成一个全面的思维过程，从表面理解深入到战略行动。

## 思维结构 (严格遵守)

你必须从以下四个维度剖析输入内容：

### 1. 🔍 The Context (全景)
提供一个高层级的全景视图。内容是关于什么的？核心情境、背景或正在解决的问题是什么？（2-3 段话）

### 2. 🧠 The Logic (脉络)
解构底层结构。论点是如何构建的？其中的推理逻辑、隐藏假设或起作用的思维模型是什么？（列表形式）

### 3. 💎 The Insight (洞察)
提取非显性的价值。有哪些“原来如此”的时刻？揭示了哪些深层含义、盲点或独特视角？（列表形式）

### 4. 🚀 The Path (路径)
定义战略方向。具体的、按优先级排列的下一步行动是什么？如何立即应用这些知识？（可执行步骤）

## 规则
- 使用用户指定的语言输出。
- 保持专业、分析性且富有启发性的语调。
- 聚焦于“理解的过程”，而不仅仅是结果。
- 不要包含寒暄或元对话。
"""

USER_PROMPT = """
对以下内容发起“深度下潜”：

**用户上下文：**
- 用户：{user_name}
- 时间：{current_date_time_str}
- 语言：{user_language}

**待分析内容：**
```
{long_text_content}
```

请执行完整的思维链：全景 (Context) → 脉络 (Logic) → 洞察 (Insight) → 路径 (Path)。
"""

# =================================================================
# 现代 CSS 设计 - 深度下潜主题
# =================================================================

CSS_TEMPLATE = """
        .deep-dive {
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
            color: var(--dd-text-secondary);
        }

        .dd-header {
            background: var(--dd-header-gradient);
            padding: 40px 32px;
            color: white;
            position: relative;
        }

        .dd-header-badge {
            display: inline-block;
            padding: 4px 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        .dd-title {
            font-size: 2rem;
            font-weight: 800;
            margin: 0 0 12px 0;
            letter-spacing: -0.02em;
        }

        .dd-meta {
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            opacity: 0.7;
        }

        .dd-body {
            padding: 32px;
            display: flex;
            flex-direction: column;
            gap: 40px;
            position: relative;
            background: var(--dd-bg-primary);
        }

        /* 思维导火索 */
        .dd-body::before {
            content: '';
            position: absolute;
            left: 52px;
            top: 40px;
            bottom: 40px;
            width: 2px;
            background: var(--dd-border);
            z-index: 0;
        }

        .dd-step {
            position: relative;
            z-index: 1;
            display: flex;
            gap: 24px;
        }

        .dd-step-icon {
            flex-shrink: 0;
            width: 40px;
            height: 40px;
            background: var(--dd-bg-primary);
            border: 2px solid var(--dd-border);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            transition: all 0.3s ease;
        }

        .dd-step:hover .dd-step-icon {
            border-color: var(--dd-accent);
            transform: scale(1.1);
        }

        .dd-step-content {
            flex: 1;
        }

        .dd-step-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--dd-accent);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 4px;
        }

        .dd-step-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--dd-text-primary);
            margin: 0 0 16px 0;
        }

        .dd-text {
            line-height: 1.7;
            font-size: 1rem;
        }

        .dd-text p { margin-bottom: 16px; }
        .dd-text p:last-child { margin-bottom: 0; }

        .dd-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            gap: 12px;
        }

        .dd-list-item {
            background: var(--dd-bg-secondary);
            padding: 16px 20px;
            border-radius: 12px;
            border-left: 4px solid var(--dd-border);
            transition: all 0.2s ease;
        }

        .dd-list-item:hover {
            background: var(--dd-bg-tertiary);
            border-left-color: var(--dd-accent);
            transform: translateX(4px);
        }

        .dd-list-item strong {
            color: var(--dd-text-primary);
            display: block;
            margin-bottom: 4px;
        }

        .dd-path-item {
            background: var(--dd-accent-soft);
            border-left-color: var(--dd-accent);
        }

        .dd-footer {
            padding: 24px 32px;
            background: var(--dd-bg-secondary);
            border-top: 1px solid var(--dd-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: var(--dd-text-dim);
        }

        .dd-tag {
            padding: 2px 8px;
            background: var(--dd-bg-tertiary);
            border-radius: 4px;
            font-weight: 600;
        }

        .dd-text code,
        .dd-list-item code {
            background: var(--dd-code-bg);
            color: var(--dd-text-primary);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
            font-size: 0.85em;
        }

        .dd-list-item em {
            font-style: italic;
            color: var(--dd-text-dim);
        }
"""

CONTENT_TEMPLATE = """
        <div class="deep-dive">
            <div class="dd-header">
                <div class="dd-header-badge">思维过程</div>
                <h1 class="dd-title">精读分析报告</h1>
                <div class="dd-meta">
                    <span>👤 {user_name}</span>
                    <span>📅 {current_date_time_str}</span>
                    <span>📊 {word_count} 字</span>
                </div>
            </div>
            <div class="dd-body">
                <!-- 第一步：全景 -->
                <div class="dd-step">
                    <div class="dd-step-icon">🔍</div>
                    <div class="dd-step-content">
                        <div class="dd-step-label">Phase 01</div>
                        <h2 class="dd-step-title">全景 (The Context)</h2>
                        <div class="dd-text">{context_html}</div>
                    </div>
                </div>

                <!-- 第二步：脉络 -->
                <div class="dd-step">
                    <div class="dd-step-icon">🧠</div>
                    <div class="dd-step-content">
                        <div class="dd-step-label">Phase 02</div>
                        <h2 class="dd-step-title">脉络 (The Logic)</h2>
                        <div class="dd-text">{logic_html}</div>
                    </div>
                </div>

                <!-- 第三步：洞察 -->
                <div class="dd-step">
                    <div class="dd-step-icon">💎</div>
                    <div class="dd-step-content">
                        <div class="dd-step-label">Phase 03</div>
                        <h2 class="dd-step-title">洞察 (The Insight)</h2>
                        <div class="dd-text">{insight_html}</div>
                    </div>
                </div>

                <!-- 第四步：路径 -->
                <div class="dd-step">
                    <div class="dd-step-icon">🚀</div>
                    <div class="dd-step-content">
                        <div class="dd-step-label">Phase 04</div>
                        <h2 class="dd-step-title">路径 (The Path)</h2>
                        <div class="dd-text">{path_html}</div>
                    </div>
                </div>
            </div>
            <div class="dd-footer">
                <span>Deep Dive Engine v1.0</span>
                <span><span class="dd-tag">AI 驱动分析</span></span>
            </div>
        </div>
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="是否显示操作状态更新。",
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="是否在浏览器控制台打印调试日志。",
        )
        MODEL_ID: str = Field(
            default="",
            description="用于分析的 LLM 模型 ID。留空则使用当前模型。",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=200,
            description="深度下潜所需的最小文本长度（字符）。",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=True,
            description="是否清除之前的插件结果。",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="要分析的最近消息数量。",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """安全提取用户上下文信息。"""
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

    def _process_llm_output(self, llm_output: str) -> Dict[str, str]:
        """解析 LLM 输出并转换为样式化 HTML。"""
        # 使用灵活的正则提取各部分
        context_match = re.search(
            r"###\s*1\.\s*🔍?\s*(?:全景|The Context)\s*(?:\((.*?)\))?\s*\n(.*?)(?=\n###|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )
        logic_match = re.search(
            r"###\s*2\.\s*🧠?\s*(?:脉络|The Logic)\s*(?:\((.*?)\))?\s*\n(.*?)(?=\n###|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )
        insight_match = re.search(
            r"###\s*3\.\s*💎?\s*(?:洞察|The Insight)\s*(?:\((.*?)\))?\s*\n(.*?)(?=\n###|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )
        path_match = re.search(
            r"###\s*4\.\s*🚀?\s*(?:路径|The Path)\s*(?:\((.*?)\))?\s*\n(.*?)(?=\n###|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )

        # 兜底正则
        if not context_match:
            context_match = re.search(
                r"###\s*🔍?\s*(?:全景|The Context).*?\n(.*?)(?=\n###|$)",
                llm_output,
                re.DOTALL | re.IGNORECASE,
            )
        if not logic_match:
            logic_match = re.search(
                r"###\s*🧠?\s*(?:脉络|The Logic).*?\n(.*?)(?=\n###|$)",
                llm_output,
                re.DOTALL | re.IGNORECASE,
            )
        if not insight_match:
            insight_match = re.search(
                r"###\s*💎?\s*(?:洞察|The Insight).*?\n(.*?)(?=\n###|$)",
                llm_output,
                re.DOTALL | re.IGNORECASE,
            )
        if not path_match:
            path_match = re.search(
                r"###\s*🚀?\s*(?:路径|The Path).*?\n(.*?)(?=\n###|$)",
                llm_output,
                re.DOTALL | re.IGNORECASE,
            )

        context_md = (
            context_match.group(context_match.lastindex).strip()
            if context_match
            else ""
        )
        logic_md = (
            logic_match.group(logic_match.lastindex).strip() if logic_match else ""
        )
        insight_md = (
            insight_match.group(insight_match.lastindex).strip()
            if insight_match
            else ""
        )
        path_md = path_match.group(path_match.lastindex).strip() if path_match else ""

        if not any([context_md, logic_md, insight_md, path_md]):
            context_md = llm_output.strip()
            logger.warning("LLM 输出未遵循格式，将作为全景处理。")

        md_extensions = ["nl2br"]

        context_html = (
            markdown.markdown(context_md, extensions=md_extensions)
            if context_md
            else '<p class="dd-no-content">未能提取全景信息。</p>'
        )
        logic_html = (
            self._process_list_items(logic_md, "logic")
            if logic_md
            else '<p class="dd-no-content">未能解构脉络。</p>'
        )
        insight_html = (
            self._process_list_items(insight_md, "insight")
            if insight_md
            else '<p class="dd-no-content">未能发现洞察。</p>'
        )
        path_html = (
            self._process_list_items(path_md, "path")
            if path_md
            else '<p class="dd-no-content">未能定义路径。</p>'
        )

        return {
            "context_html": context_html,
            "logic_html": logic_html,
            "insight_html": insight_html,
            "path_html": path_html,
        }

    def _process_list_items(self, md_content: str, section_type: str) -> str:
        """将 markdown 列表转换为样式化卡片，支持完整的 markdown 格式。"""
        lines = md_content.strip().split("\n")
        items = []
        current_paragraph = []

        for line in lines:
            line = line.strip()

            # 检查列表项（无序或有序）
            bullet_match = re.match(r"^[-*]\s+(.+)$", line)
            numbered_match = re.match(r"^\d+\.\s+(.+)$", line)

            if bullet_match or numbered_match:
                # 清空累积的段落
                if current_paragraph:
                    para_text = " ".join(current_paragraph)
                    para_html = self._convert_inline_markdown(para_text)
                    items.append(f"<p>{para_html}</p>")
                    current_paragraph = []

                # 提取列表项内容
                text = (
                    bullet_match.group(1) if bullet_match else numbered_match.group(1)
                )

                # 处理粗体标题模式：**标题:** 描述 或 **标题**: 描述
                title_match = re.match(r"\*\*(.+?)\*\*[:\s：]*(.*)$", text)
                if title_match:
                    title = self._convert_inline_markdown(title_match.group(1))
                    desc = self._convert_inline_markdown(title_match.group(2).strip())
                    path_class = "dd-path-item" if section_type == "path" else ""
                    item_html = f'<div class="dd-list-item {path_class}"><strong>{title}</strong>{desc}</div>'
                else:
                    text_html = self._convert_inline_markdown(text)
                    path_class = "dd-path-item" if section_type == "path" else ""
                    item_html = (
                        f'<div class="dd-list-item {path_class}">{text_html}</div>'
                    )
                items.append(item_html)
            elif line and not line.startswith("#"):
                # 累积段落文本
                current_paragraph.append(line)
            elif not line and current_paragraph:
                # 空行结束段落
                para_text = " ".join(current_paragraph)
                para_html = self._convert_inline_markdown(para_text)
                items.append(f"<p>{para_html}</p>")
                current_paragraph = []

        # 清空剩余段落
        if current_paragraph:
            para_text = " ".join(current_paragraph)
            para_html = self._convert_inline_markdown(para_text)
            items.append(f"<p>{para_html}</p>")

        if items:
            return f'<div class="dd-list">{" ".join(items)}</div>'
        return f'<p class="dd-no-content">未找到条目。</p>'

    def _convert_inline_markdown(self, text: str) -> str:
        """将行内 markdown（粗体、斜体、代码）转换为 HTML。"""
        # 转换行内代码：`code` -> <code>code</code>
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # 转换粗体：**text** -> <strong>text</strong>
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # 转换斜体：*text* -> <em>text</em>（但不在 ** 内部）
        text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
        return text

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        """发送状态更新事件。"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        content: str,
        ntype: str = "info",
    ):
        """发送通知事件。"""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    async def _emit_debug_log(self, emitter, title: str, data: dict):
        """在浏览器控制台打印结构化调试日志"""
        if not self.valves.SHOW_DEBUG_LOG or not emitter:
            return

        try:
            import json

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
        """移除已有的插件生成的 HTML。"""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _extract_text_content(self, content) -> str:
        """从消息内容中提取文本。"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
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
        existing_html: str,
        new_content: str,
        new_styles: str = "",
        user_language: str = "zh-CN",
    ) -> str:
        """合并新内容到 HTML 容器。"""
        if "<!-- OPENWEBUI_PLUGIN_OUTPUT -->" in existing_html:
            base_html = re.sub(r"^```html\s*", "", existing_html)
            base_html = re.sub(r"\s*```$", "", base_html)
        else:
            base_html = HTML_WRAPPER_TEMPLATE.replace("{user_language}", user_language)

        wrapped = f'<div class="plugin-item">\n{new_content}\n</div>'

        if new_styles:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n/* STYLES_INSERTION_POINT */",
            )

        base_html = base_html.replace(
            "<!-- CONTENT_INSERTION_POINT -->",
            f"{wrapped}\n<!-- CONTENT_INSERTION_POINT -->",
        )

        return base_html.strip()

    def _build_content_html(self, context: dict) -> str:
        """构建内容 HTML。"""
        html = CONTENT_TEMPLATE
        for key, value in context.items():
            html = html.replace(f"{{{key}}}", str(value))
        return html

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: 精读 v1.0.0 启动")

        user_ctx = self._get_user_context(__user__)
        user_id = user_ctx["user_id"]
        user_name = user_ctx["user_name"]
        user_language = user_ctx["user_language"]

        now = datetime.now()
        current_date_time_str = now.strftime("%Y年%m月%d日 %H:%M")

        original_content = ""
        try:
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("未找到消息内容。")

            message_count = min(self.valves.MESSAGE_COUNT, len(messages))
            recent_messages = messages[-message_count:]

            aggregated_parts = []
            for msg in recent_messages:
                text = self._extract_text_content(msg.get("content"))
                if text:
                    aggregated_parts.append(text)

            if not aggregated_parts:
                raise ValueError("未找到文本内容。")

            original_content = "\n\n---\n\n".join(aggregated_parts)
            word_count = len(original_content)

            if len(original_content) < self.valves.MIN_TEXT_LENGTH:
                msg = f"内容过短（{len(original_content)} 字符）。精读至少需要 {self.valves.MIN_TEXT_LENGTH} 字符才能进行有意义的分析。"
                await self._emit_notification(__event_emitter__, msg, "warning")
                return {"messages": [{"role": "assistant", "content": f"⚠️ {msg}"}]}

            await self._emit_notification(
                __event_emitter__, "📖 正在发起精读分析...", "info"
            )
            await self._emit_status(
                __event_emitter__, "📖 精读：正在分析全景与脉络...", False
            )

            prompt = USER_PROMPT.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                user_language=user_language,
                long_text_content=original_content,
            )

            model = self.valves.MODEL_ID or body.get("model")
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }

            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"未找到用户：{user_id}")

            response = await generate_chat_completion(__request__, payload, user_obj)
            llm_output = response["choices"][0]["message"]["content"]

            processed = self._process_llm_output(llm_output)

            context = {
                "user_name": user_name,
                "current_date_time_str": current_date_time_str,
                "word_count": word_count,
                **processed,
            }

            content_html = self._build_content_html(context)

            # 处理已有 HTML
            existing = ""
            match = re.search(
                r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
                original_content,
            )
            if match:
                existing = match.group(1)

            if self.valves.CLEAR_PREVIOUS_HTML or not existing:
                original_content = self._remove_existing_html(original_content)
                final_html = self._merge_html(
                    "", content_html, CSS_TEMPLATE, user_language
                )
            else:
                original_content = self._remove_existing_html(original_content)
                final_html = self._merge_html(
                    existing, content_html, CSS_TEMPLATE, user_language
                )

            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n```html\n{final_html}\n```"

            await self._emit_status(__event_emitter__, "📖 精读完成！", True)
            await self._emit_notification(
                __event_emitter__,
                f"📖 精读完成，{user_name}！思维链已生成。",
                "success",
            )

        except Exception as e:
            logger.error(f"Deep Dive 错误：{e}", exc_info=True)
            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n❌ **错误：** {str(e)}"
            await self._emit_status(__event_emitter__, "精读失败。", True)
            await self._emit_notification(__event_emitter__, f"错误：{str(e)}", "error")

        return body
