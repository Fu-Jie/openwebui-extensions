"""
title: GitHub Copilot SDK Files Filter
id: github_copilot_sdk_files_filter
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.3
openwebui_id: 403a62ee-a596-45e7-be65-fab9cc249dd6
description: A specialized filter to bypass OpenWebUI's default RAG for GitHub Copilot SDK models. It moves uploaded files to a safe location ('copilot_files') so the Copilot Pipe can process them natively without interference.
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable
import logging
import json


logger = logging.getLogger(__name__)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Priority level. Must be lower than RAG processors to intercept files effectively.",
        )
        target_model_keyword: str = Field(
            default="copilot_sdk",
            description="Keyword to identify Copilot models (e.g., 'copilot_sdk').",
        )
        target_model_prefixes: str = Field(
            default="github_copilot_official_sdk_pipe.,github_copilot_sdk_pipe.",
            description="Comma-separated model id prefixes to identify Copilot SDK models.",
        )
        show_debug_log: bool = Field(
            default=False,
            description="Whether to print model matching debug logs in backend console.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _is_copilot_model(self, model_id: str) -> bool:
        if not isinstance(model_id, str) or not model_id:
            return False

        current = model_id.strip().lower()
        if not current:
            return False

        # 1) Prefix match (most reliable for OpenWebUI model id formats)
        raw_prefixes = self.valves.target_model_prefixes or ""
        prefixes = [p.strip().lower() for p in raw_prefixes.split(",") if p.strip()]
        if any(current.startswith(prefix) for prefix in prefixes):
            return True

        # 2) Keyword fallback for backward compatibility
        keyword = (self.valves.target_model_keyword or "").strip().lower()
        return bool(keyword and keyword in current)

    async def _emit_debug_log(
        self,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
        title: str,
        data: dict,
    ):
        if not self.valves.show_debug_log:
            return

        logger.info("[Copilot Files Filter] %s: %s", title, data)

        if not __event_emitter__:
            return

        try:
            js_code = f"""
                (async function() {{
                    console.group('🧩 Copilot Files Filter: {title}');
                    console.log({json.dumps(data, ensure_ascii=False)});
                    console.groupEnd();
                }})();
            """
            await __event_emitter__({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            logger.debug("[Copilot Files Filter] frontend debug emit failed: %s", e)

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> dict:
        # Determine the actual model ID
        base_model_id = None
        if __model__:
            if "openai" in __model__:
                base_model_id = __model__["openai"].get("id")
            else:
                base_model_id = __model__.get("info", {}).get("base_model_id")

        current_model = base_model_id if base_model_id else body.get("model", "")

        await self._emit_debug_log(
            __event_emitter__,
            "model-debug",
            {
                "body_model": body.get("model", ""),
                "base_model_id": base_model_id,
                "current_model": current_model,
            },
        )

        # Check if it's a Copilot model
        is_copilot_model = self._is_copilot_model(current_model)

        await self._emit_debug_log(
            __event_emitter__,
            "match-result",
            {
                "is_copilot_model": is_copilot_model,
                "prefixes": self.valves.target_model_prefixes,
                "keyword": self.valves.target_model_keyword,
            },
        )

        if is_copilot_model:
            # If files exist, move them to 'copilot_files' and clear 'files'
            # This prevents OpenWebUI from triggering RAG on these files
            if "files" in body and body["files"]:
                file_count = len(body["files"])
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"Managed {file_count} files for Copilot (RAG Bypassed)",
                                "done": True,
                            },
                        }
                    )
                body["copilot_files"] = body["files"]
                body["files"] = []

        return body
