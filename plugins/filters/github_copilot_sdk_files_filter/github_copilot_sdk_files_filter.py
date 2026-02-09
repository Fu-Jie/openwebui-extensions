"""
title: GitHub Copilot SDK Files Filter
id: github_copilot_sdk_files_filter
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
version: 0.1.2
description: A specialized filter to bypass OpenWebUI's default RAG for GitHub Copilot SDK models. It moves uploaded files to a safe location ('copilot_files') so the Copilot Pipe can process them natively without interference.
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable


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

    def __init__(self):
        self.valves = self.Valves()

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

        # Check if it's a Copilot model
        if self.valves.target_model_keyword.lower() in current_model.lower():
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
