"""
title: GitHub Copilot SDK 文件过滤器(GitHub Copilot SDK Files Filter)
id: github_copilot_sdk_files_filter
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
version: 0.1.2
description: 一个专门的过滤器，用于绕过 OpenWebUI 默认的 RAG 机制，针对 GitHub Copilot SDK 模型。它将上传的文件移动到安全位置 ('copilot_files')，以便 Copilot Pipe 可以原生处理它们而不受干扰。
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="优先级。必须低于 RAG 处理器的优先级，以便有效拦截文件。",
        )
        target_model_keyword: str = Field(
            default="copilot_sdk",
            description="用于识别 Copilot 模型的关键词（例如 'copilot_sdk'）。",
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
                                "description": f"已为 Copilot 管理 {file_count} 个文件 (已绕过 RAG)",
                                "done": True,
                            },
                        }
                    )
                body["copilot_files"] = body["files"]
                body["files"] = []

        return body
