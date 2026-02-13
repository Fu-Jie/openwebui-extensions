"""
title: UI Language Debugger
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.0
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPgogIDxwYXRoIGQ9Im01IDggNiA2Ii8+CiAgPHBhdGggZD0ibTQgMTQgNi02IDItMiIvPgogIDxwYXRoIGQ9Ik0yIDVoMTIiLz4KICA8cGF0aCBkPSJNNyAyaDEiLz4KICA8cGF0aCBkPSJtMjIgMjItNS0xMC01IDEwIi8+CiAgPHBhdGggZD0iTTE0IDE4aDYiLz4KPC9zdmc+Cg==
description: Debug UI language detection in the browser console and on-page panel.
"""

import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
            gap: 16px;
            width: 100%;
            max-width: 100%;
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

CONTENT_TEMPLATE = """
<div class="lang-debug-card" id="lang-debug-card-{unique_id}">
    <div class="lang-debug-header">
        🧭 UI Language Debugger
    </div>
    <div class="lang-debug-body">
        <div class="lang-debug-row"><span>python.ui_language</span><code id="lang-py-{unique_id}">{python_language}</code></div>
        <div class="lang-debug-row"><span>document.documentElement.lang</span><code id="lang-html-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>document.documentElement.getAttribute('lang')</span><code id="lang-attr-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>document.documentElement.dir</span><code id="lang-dir-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>document.body.lang</span><code id="lang-body-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>navigator.language</span><code id="lang-nav-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>navigator.languages</span><code id="lang-navs-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>localStorage.language</span><code id="lang-store-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>localStorage.locale</span><code id="lang-locale-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>localStorage.i18n</span><code id="lang-i18n-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>localStorage.settings</span><code id="lang-settings-{unique_id}">-</code></div>
        <div class="lang-debug-row"><span>document.documentElement.dataset</span><code id="lang-dataset-{unique_id}">-</code></div>
    </div>
</div>
"""

STYLE_TEMPLATE = """
.lang-debug-card {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    background: #ffffff;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
}
.lang-debug-header {
    padding: 12px 16px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;
    font-weight: 600;
}
.lang-debug-body {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.lang-debug-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 0.9em;
    color: #1f2937;
}
.lang-debug-row code {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 2px 6px;
    border-radius: 6px;
    color: #0f172a;
}
"""

SCRIPT_TEMPLATE = """
<script>
(function() {{
    const uniqueId = "{unique_id}";
    const get = (id) => document.getElementById(id + '-' + uniqueId);

    const safe = (value) => {
        if (value === undefined || value === null || value === "") return "-";
        if (Array.isArray(value)) return value.join(", ");
        if (typeof value === "object") return JSON.stringify(value);
        return String(value);
    };

    const safeJson = (value) => {
        try {
            return value ? JSON.stringify(JSON.parse(value)) : "-";
        } catch (e) {
            return value ? String(value) : "-";
        }
    };

    const settingsRaw = localStorage.getItem('settings');
    const i18nRaw = localStorage.getItem('i18n');
    const localeRaw = localStorage.getItem('locale');

    const payload = {{
        htmlLang: document.documentElement.lang,
        htmlAttr: document.documentElement.getAttribute('lang'),
        htmlDir: document.documentElement.dir,
        bodyLang: document.body ? document.body.lang : "",
        navigatorLanguage: navigator.language,
        navigatorLanguages: navigator.languages,
        localStorageLanguage: localStorage.getItem('language'),
        localStorageLocale: localeRaw,
        localStorageI18n: i18nRaw,
        localStorageSettings: settingsRaw,
        htmlDataset: document.documentElement.dataset,
    }};

    get('lang-html').textContent = safe(payload.htmlLang);
    get('lang-attr').textContent = safe(payload.htmlAttr);
    get('lang-dir').textContent = safe(payload.htmlDir);
    get('lang-body').textContent = safe(payload.bodyLang);
    get('lang-nav').textContent = safe(payload.navigatorLanguage);
    get('lang-navs').textContent = safe(payload.navigatorLanguages);
    get('lang-store').textContent = safe(payload.localStorageLanguage);
    get('lang-locale').textContent = safe(payload.localStorageLocale);
    get('lang-i18n').textContent = safeJson(payload.localStorageI18n);
    get('lang-settings').textContent = safeJson(payload.localStorageSettings);
    get('lang-dataset').textContent = safe(payload.htmlDataset);

    console.group('🧭 UI Language Debugger');
    console.log(payload);
    console.groupEnd();
}})();
</script>
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates.",
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=True,
            description="Whether to print debug logs in the browser console.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", "unknown_user"),
            "user_name": user_data.get("name", "User"),
            "user_language": user_data.get("language", ""),
        }

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        chat_id = ""
        message_id = ""

        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")

            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_debug_log(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        title: str,
        data: dict,
    ):
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
            logger.error("Error emitting debug log: %s", e, exc_info=True)

    def _merge_html(
        self,
        existing_html: str,
        new_content: str,
        new_styles: str = "",
        new_scripts: str = "",
        user_language: str = "en-US",
    ) -> str:
        if not existing_html:
            base_html = HTML_WRAPPER_TEMPLATE.replace("{user_language}", user_language)
        else:
            base_html = existing_html

        if "<!-- CONTENT_INSERTION_POINT -->" in base_html:
            base_html = base_html.replace(
                "<!-- CONTENT_INSERTION_POINT -->",
                f"{new_content}\n        <!-- CONTENT_INSERTION_POINT -->",
            )

        if new_styles and "/* STYLES_INSERTION_POINT */" in base_html:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n        /* STYLES_INSERTION_POINT */",
            )

        if new_scripts and "<!-- SCRIPTS_INSERTION_POINT -->" in base_html:
            base_html = base_html.replace(
                "<!-- SCRIPTS_INSERTION_POINT -->",
                f"{new_scripts}\n    <!-- SCRIPTS_INSERTION_POINT -->",
            )

        return base_html

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __metadata__: Optional[dict] = None,
        __request__: Optional[Any] = None,
    ) -> Optional[dict]:
        await self._emit_status(__event_emitter__, "Detecting UI language...", False)

        user_ctx = self._get_user_context(__user__)
        await self._emit_debug_log(
            __event_emitter__,
            "Language Debugger: user context",
            user_ctx,
        )

        ui_language = ""
        if __event_call__:
            try:
                response = await __event_call__(
                    {
                        "type": "execute",
                        "data": {
                            "code": "return (localStorage.getItem('locale') || localStorage.getItem('language') || (navigator.languages && navigator.languages[0]) || navigator.language || document.documentElement.lang || '')",
                        },
                    }
                )
                await self._emit_debug_log(
                    __event_emitter__,
                    "Language Debugger: execute response",
                    {"response": response},
                )
                if isinstance(response, dict) and "value" in response:
                    ui_language = response.get("value", "") or ""
                elif isinstance(response, str):
                    ui_language = response
            except Exception as e:
                logger.error(
                    "Failed to read UI language from frontend: %s", e, exc_info=True
                )

        unique_id = f"lang_{int(__import__('time').time() * 1000)}"
        content_html = CONTENT_TEMPLATE.replace("{unique_id}", unique_id).replace(
            "{python_language}", ui_language or "-"
        )
        script_html = SCRIPT_TEMPLATE.replace("{unique_id}", unique_id)
        script_html = script_html.replace("{{", "{").replace("}}", "}")

        final_html = self._merge_html(
            "",
            content_html,
            STYLE_TEMPLATE,
            script_html,
            "en",
        )

        html_embed_tag = f"```html\n{final_html}\n```"
        body["messages"][-1]["content"] = (
            body["messages"][-1].get("content", "") + "\n\n" + html_embed_tag
        )

        await self._emit_status(__event_emitter__, "UI language captured.", True)
        return body
