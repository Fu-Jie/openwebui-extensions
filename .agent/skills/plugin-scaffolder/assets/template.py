"""
title: {{TITLE}}
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.0
description: {{DESCRIPTION}}
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List, Callable, Awaitable
from pydantic import BaseModel, Field
from fastapi import Request

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TRANSLATIONS = {
    "en-US": {"status_starting": "Starting {{TITLE}}..."},
    "zh-CN": {"status_starting": "正在启动 {{TITLE}}..."},
    "zh-HK": {"status_starting": "正在啟動 {{TITLE}}..."},
    "zh-TW": {"status_starting": "正在啟動 {{TITLE}}..."},
    "ko-KR": {"status_starting": "{{TITLE}} 시작 중..."},
    "ja-JP": {"status_starting": "{{TITLE}} を起動中..."},
    "fr-FR": {"status_starting": "Démarrage de {{TITLE}}..."},
    "de-DE": {"status_starting": "{{TITLE}} wird gestartet..."},
    "es-ES": {"status_starting": "Iniciando {{TITLE}}..."},
    "it-IT": {"status_starting": "Avvio di {{TITLE}}..."},
    "vi-VN": {"status_starting": "Đang khởi động {{TITLE}}..."},
    "id-ID": {"status_starting": "Memulai {{TITLE}}..."},
}

class {{CLASS_NAME}}:
    class Valves(BaseModel):
        priority: int = Field(default=50, description="Priority level (lower = earlier).")
        show_status: bool = Field(default=True, description="Show status updates in UI.")

    def __init__(self):
        self.valves = self.Valves()
        self.fallback_map = {
            "zh": "zh-CN", "en": "en-US", "ko": "ko-KR", "ja": "ja-JP",
            "fr": "fr-FR", "de": "de-DE", "es": "es-ES", "it": "it-IT",
            "vi": "vi-VN", "id": "id-ID"
        }

    def _get_translation(self, lang: str, key: str, **kwargs) -> str:
        target_lang = lang
        if target_lang not in TRANSLATIONS:
            base = target_lang.split("-")[0]
            target_lang = self.fallback_map.get(base, "en-US")
        
        lang_dict = TRANSLATIONS.get(target_lang, TRANSLATIONS["en-US"])
        text = lang_dict.get(key, TRANSLATIONS["en-US"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    async def _get_user_context(self, __user__: Optional[dict], __event_call__: Optional[Callable] = None, __request__: Optional[Request] = None) -> dict:
        user_data = __user__ if isinstance(__user__, dict) else {}
        user_language = user_data.get("language", "en-US")
        if __event_call__:
            try:
                js = "try { return (document.documentElement.lang || localStorage.getItem('locale') || navigator.language || 'en-US'); } catch (e) { return 'en-US'; }"
                frontend_lang = await asyncio.wait_for(__event_call__({"type": "execute", "data": {"code": js}}), timeout=2.0)
                if frontend_lang: user_language = frontend_lang
            except: pass
        return {"user_language": user_language}

    async def {{METHOD_NAME}}(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None, __event_call__=None, __request__: Optional[Request] = None) -> dict:
        if self.valves.show_status and __event_emitter__:
            user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
            msg = self._get_translation(user_ctx["user_language"], "status_starting")
            await __event_emitter__({"type": "status", "data": {"description": msg, "done": False}})
        
        # Implement core logic here
        
        if self.valves.show_status and __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": "Done", "done": True}})
        return body
