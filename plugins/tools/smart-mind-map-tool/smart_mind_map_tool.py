"""
title: Smart Mind Map Tool
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 1.1.0
description: Intelligently analyzes text content and generates interactive mind maps inline to help users structure and visualize knowledge.
"""

import asyncio
import logging
import re
import time
import json
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, Dict, Optional

from fastapi import Request
from pydantic import BaseModel, Field

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logger = logging.getLogger(__name__)

class Tools:
    class Valves(BaseModel):
        MODEL_ID: str = Field(default="", description="The model ID to use for mind map generation. If empty, uses the current conversation model.")
        MIN_TEXT_LENGTH: int = Field(default=50, description="Minimum text length required for analysis.")
        SHOW_STATUS: bool = Field(default=True, description="Whether to show status messages.")

    def __init__(self):
        self.valves = self.Valves()
        self.__translations = {
            "en-US": {
                "status_analyzing": "Smart Mind Map: Analyzing text structure...",
                "status_drawing": "Smart Mind Map: Drawing completed!",
                "notification_success": "Mind map has been generated, {user_name}!",
                "error_text_too_short": "Text content is too short ({len} characters). Min: {min_len}.",
                "error_user_facing": "Sorry, Smart Mind Map encountered an error: {error}",
                "status_failed": "Smart Mind Map: Failed.",
                "ui_title": "🧠 Smart Mind Map",
                "ui_download_png": "PNG",
                "ui_download_svg": "SVG",
                "ui_download_md": "Markdown",
                "ui_zoom_out": "Zoom Out",
                "ui_zoom_reset": "Reset",
                "ui_zoom_in": "Zoom In",
                "ui_depth_select": "Expand Level",
                "ui_depth_all": "All",
                "ui_depth_2": "L2",
                "ui_depth_3": "L3",
                "ui_fullscreen": "Fullscreen",
                "ui_theme": "Theme",
                "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
                "html_error_missing_content": "⚠️ Missing content.",
                "html_error_load_failed": "⚠️ Resource load failed.",
                "js_done": "Done",
            },
            "zh-CN": {
                "status_analyzing": "思维导图：深入分析文本结构...",
                "status_drawing": "思维导图：绘制完成！",
                "notification_success": "思维导图已生成，{user_name}！",
                "error_text_too_short": "文本内容过短（{len}字符），请提供至少{min_len}字符。",
                "error_user_facing": "抱歉，思维导图处理出错：{error}",
                "status_failed": "思维导图：处理失败。",
                "ui_title": "🧠 智能思维导图",
                "ui_download_png": "PNG",
                "ui_download_svg": "SVG",
                "ui_download_md": "Markdown",
                "ui_zoom_out": "缩小",
                "ui_zoom_reset": "重置",
                "ui_zoom_in": "放大",
                "ui_depth_select": "展开层级",
                "ui_depth_all": "全部",
                "ui_depth_2": "2级",
                "ui_depth_3": "3级",
                "ui_fullscreen": "全屏",
                "ui_theme": "主题",
                "ui_footer": "<b>Powered by</b> <a href='https://markmap.js.org/' target='_blank' rel='noopener noreferrer'>Markmap</a>",
                "html_error_missing_content": "⚠️ 缺少有效内容。",
                "html_error_load_failed": "⚠️ 资源加载失败。",
                "js_done": "完成",
            }
        }
        self.__system_prompt = """You are a professional mind map assistant. Analyze text and output Markdown list syntax for Markmap.js.
Guidelines:
- Root node (#) must be ultra-compact (max 10 chars for CJK, 5 words for Latin).
- Use '-' with 2-space indentation.
- Output ONLY Markdown wrapped in ```markdown.
- Match the language of the input text."""

        self.__css_template = """
        :root {
            --primary-color: #1e88e5; --secondary-color: #43a047; --background-color: #f4f6f8;
            --card-bg-color: #ffffff; --text-color: #000000; --link-color: #546e7a;
            --node-stroke-color: #90a4ae; --muted-text-color: #546e7a; --border-color: #e0e0e0;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.05); --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .theme-dark {
            --primary-color: #3b82f6; --secondary-color: #22c55e; --background-color: #0d1117;
            --card-bg-color: #161b22; --text-color: #ffffff; --link-color: #58a6ff;
            --node-stroke-color: #8b949e; --muted-text-color: #7d8590; --border-color: #30363d;
        }
        html, body { margin: 0; padding: 0; width: 100%; height: 600px; background: transparent; overflow: hidden; font-family: var(--font-family); }
        .mindmap-wrapper { display: flex; flex-direction: column; width: 100%; height: 100%; background: var(--card-bg-color); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
        .header { display: flex; align-items: center; padding: 8px 16px; border-bottom: 1px solid var(--border-color); background: var(--card-bg-color); flex-shrink: 0; gap: 12px; }
        .header h1 { margin: 0; font-size: 1rem; flex-grow: 1; color: var(--text-color); }
        .btn-group { display: flex; gap: 2px; background: var(--background-color); padding: 2px; border-radius: 6px; }
        .control-btn { border: none; background: transparent; color: var(--text-color); padding: 4px 8px; cursor: pointer; border-radius: 4px; font-size: 0.8rem; opacity: 0.7; }
        .control-btn:hover { background: var(--card-bg-color); opacity: 1; }
        .content { flex-grow: 1; position: relative; }
        .markmap-container { position: absolute; top:0; left:0; right:0; bottom:0; }
        svg text { fill: var(--text-color) !important; }
        svg .markmap-link { stroke: var(--link-color) !important; }
        """

        self.__content_template = """
        <div class="mindmap-wrapper">
            <div class="header">
                <h1>{t_ui_title}</h1>
                <div class="btn-group">
                    <button id="z-in-{uid}" class="control-btn">+</button>
                    <button id="z-out-{uid}" class="control-btn">-</button>
                    <button id="z-res-{uid}" class="control-btn">↺</button>
                </div>
                <div class="btn-group">
                    <select id="d-sel-{uid}" class="control-btn">
                        <option value="0">{t_ui_depth_all}</option>
                        <option value="2">{t_ui_depth_2}</option>
                        <option value="3" selected>{t_ui_depth_3}</option>
                    </select>
                </div>
                <button id="t-tog-{uid}" class="control-btn">◐</button>
            </div>
            <div class="content"><div class="markmap-container" id="mm-{uid}"></div></div>
        </div>
        <script type="text/template" id="src-{uid}">{md}</script>
        """

    async def generate_mind_map(
        self,
        text: str,
        __user__: Optional[Dict[str, Any]] = None,
        __metadata__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __request__: Optional[Request] = None,
    ) -> Any:
        user_ctx = await self.__get_user_context(__user__, __request__)
        lang = user_ctx["lang"]
        name = user_ctx["name"]

        if len(text) < self.valves.MIN_TEXT_LENGTH:
            return f"⚠️ {self.__get_t(lang, 'error_text_too_short', len=len(text), min_len=self.valves.MIN_TEXT_LENGTH)}"

        await self.__emit_status(__event_emitter__, self.__get_t(lang, "status_analyzing"), False)

        try:
            target_model = self.valves.MODEL_ID or (__metadata__.get("model_id") if __metadata__ else "")
            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": self.__system_prompt},
                    {"role": "user", "content": f"Language: {lang}\nText: {text}"},
                ],
                "temperature": 0.5,
            }

            user_obj = Users.get_user_by_id(user_ctx["id"])
            response = await generate_chat_completion(__request__, llm_payload, user_obj)
            md_content = self.__extract_md(response["choices"][0]["message"]["content"])

            uid = str(int(time.time() * 1000))
            ui_t = {f"t_{k}": self.__get_t(lang, k) for k in self.__translations["en-US"] if k.startswith("ui_")}
            
            html_body = self.__content_template.format(uid=uid, md=md_content, **ui_t)
            
            script = f"""
            <script>
            (function() {{
                const uid = "{uid}";
                const load = (s, c) => c() ? Promise.resolve() : new Promise((r,e) => {{
                    const t = document.createElement('script'); t.src = s; t.onload = r; t.onerror = e; document.head.appendChild(t);
                }});
                const init = () => load('https://cdn.jsdelivr.net/npm/d3@7', () => window.d3)
                    .then(() => load('https://cdn.jsdelivr.net/npm/markmap-lib@0.17', () => window.markmap?.Transformer))
                    .then(() => load('https://cdn.jsdelivr.net/npm/markmap-view@0.17', () => window.markmap?.Markmap))
                    .then(() => {{
                        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                        svg.style.width = svg.style.height = '100%';
                        const cnt = document.getElementById('mm-'+uid); cnt.appendChild(svg);
                        const {{ Transformer, Markmap }} = window.markmap;
                        const {{ root }} = new Transformer().transform(document.getElementById('src-'+uid).textContent);
                        const mm = Markmap.create(svg, {{ autoFit: true, initialExpandLevel: 3 }}, root);
                        document.getElementById('z-in-'+uid).onclick = () => mm.rescale(1.25);
                        document.getElementById('z-out-'+uid).onclick = () => mm.rescale(0.8);
                        document.getElementById('z-res-'+uid).onclick = () => mm.fit();
                        document.getElementById('t-tog-'+uid).onclick = () => document.body.classList.toggle('theme-dark');
                        document.getElementById('d-sel-'+uid).onchange = (e) => {{
                            mm.setOptions({{ initialExpandLevel: parseInt(e.target.value) || 99 }}); mm.setData(root); mm.fit();
                        }};
                        window.addEventListener('resize', () => mm.fit());
                    }});
                if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
            }})();
            </script>
            """

            final_html = f"<!DOCTYPE html><html lang='{lang}'><head><style>{self.__css_template}</style></head><body>{html_body}{script}</body></html>"
            
            await self.__emit_status(__event_emitter__, self.__get_t(lang, "status_drawing"), True)
            await self.__emit_notification(__event_emitter__, self.__get_t(lang, "notification_success", user_name=name), "success")

            return (final_html.strip(), {"Content-Disposition": "inline", "Content-Type": "text/html"})

        except Exception as e:
            logger.error(f"Mind Map Error: {e}", exc_info=True)
            await self.__emit_status(__event_emitter__, self.__get_t(lang, "status_failed"), True)
            return f"❌ {self.__get_t(lang, 'error_user_facing', error=str(e))}"

    async def __get_user_context(self, __user__, __request__) -> Dict[str, str]:
        u = __user__ or {}
        lang = u.get("language") or (__request__.headers.get("accept-language") or "en-US").split(",")[0].split(";")[0]
        return {"id": u.get("id", "unknown"), "name": u.get("name", "User"), "lang": lang}

    def __get_t(self, lang: str, key: str, **kwargs) -> str:
        base = lang.split("-")[0]
        t = self.__translations.get(lang, self.__translations.get(base, self.__translations["en-US"])).get(key, key)
        return t.format(**kwargs) if kwargs else t

    def __extract_md(self, content: str) -> str:
        match = re.search(r"```markdown\s*(.*?)\s*```", content, re.DOTALL)
        return (match.group(1).strip() if match else content.strip()).replace("</script>", "<\\/script>")

    async def __emit_status(self, emitter, description: str, done: bool):
        if self.valves.SHOW_STATUS and emitter:
            await emitter({"type": "status", "data": {"description": description, "done": done}})

    async def __emit_notification(self, emitter, content: str, ntype: str):
        if emitter:
            await emitter({"type": "notification", "data": {"type": ntype, "content": content}})
