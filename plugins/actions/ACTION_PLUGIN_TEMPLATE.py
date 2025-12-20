"""
title: [Plugin Name] (e.g., Smart Mind Map)
author: [Your Name]
author_url: [Your URL]
funding_url: [Funding URL]
version: 0.1.0
icon_url: [Data URI or URL for Icon]
description: [Brief description of what the plugin does]
requirements: [List of dependencies, e.g., jinja2, markdown]
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Callable, Awaitable
import logging
import re
import json
from fastapi import Request
from datetime import datetime
import pytz

# Import OpenWebUI utilities
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================================================================
# Constants & Prompts
# =================================================================

SYSTEM_PROMPT = """
[Insert System Prompt Here]
You are a helpful assistant...
Please output in [JSON/Markdown] format...
"""

USER_PROMPT_TEMPLATE = """
[Insert User Prompt Template Here]
User Context:
Name: {user_name}
Time: {current_date_time_str}

Content to process:
{content}
"""

# HTML Template for rendering the result in the chat
HTML_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Plugin Title]</title>
    <style>
        /* Add your CSS styles here */
        body { font-family: sans-serif; padding: 20px; }
        .container { border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[Result Title]</h1>
        <div id="content">{result_content}</div>
    </div>
</body>
</html>
"""


class Action:
    class Valves(BaseModel):
        show_status: bool = Field(
            default=True,
            description="Whether to show operation status updates in the chat interface.",
        )
        LLM_MODEL_ID: str = Field(
            default="",
            description="Built-in LLM Model ID used for processing. If empty, uses the current conversation's model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="Minimum text length required for processing (characters).",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to clear existing plugin-generated HTML content in the message before appending new results (identified by marker).",
        )
        # Add other configuration fields as needed
        # MAX_TEXT_LENGTH: int = Field(default=2000, description="...")

    def __init__(self):
        self.valves = self.Valves()

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extracts user context information."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", "unknown_user"),
            "user_name": user_data.get("name", "User"),
            "user_language": user_data.get("language", "en-US"),
        }

    def _get_current_time_context(self) -> Dict[str, str]:
        """Gets current time context."""
        try:
            # Default to a specific timezone or system time
            tz = pytz.timezone("Asia/Shanghai")  # Change as needed
            now = datetime.now(tz)
        except Exception:
            now = datetime.now()

        return {
            "current_date_time_str": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_weekday": now.strftime("%A"),
            "current_year": now.strftime("%Y"),
            "current_timezone_str": str(now.tzinfo) if now.tzinfo else "Unknown",
        }

    def _process_llm_output(self, llm_output: str) -> Any:
        """
        Process the raw output from the LLM.
        Override this method to parse JSON, extract Markdown, etc.
        """
        # Example: Extract JSON
        # try:
        #     start = llm_output.find('{')
        #     end = llm_output.rfind('}') + 1
        #     if start != -1 and end != -1:
        #         return json.loads(llm_output[start:end])
        # except Exception:
        #     pass
        return llm_output.strip()

    def _remove_existing_html(self, content: str) -> str:
        """Removes existing plugin-generated HTML code blocks from the content."""
        # Match ```html <!-- OPENWEBUI_PLUGIN_OUTPUT --> ... ``` pattern
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        """Emits a status update event."""
        if self.valves.show_status and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        content: str,
        type: str = "info",
    ):
        """Emits a notification event (info, success, warning, error)."""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": type, "content": content}}
            )

    async def _emit_message(
        self, emitter: Optional[Callable[[Any], Awaitable[None]]], content: str
    ):
        """Emits a message event (appends to current message)."""
        if emitter:
            await emitter({"type": "message", "data": {"content": content}})

    async def _emit_replace(
        self, emitter: Optional[Callable[[Any], Awaitable[None]]], content: str
    ):
        """Emits a replace event (replaces current message)."""
        if emitter:
            await emitter({"type": "replace", "data": {"content": content}})

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[Any], Awaitable[Any]]] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info(f"Action: {__name__} started")

        # 1. Context Setup
        user_context = self._get_user_context(__user__)
        time_context = self._get_current_time_context()

        # 2. Input Validation
        messages = body.get("messages", [])
        if not messages or not messages[-1].get("content"):
            return body  # Or handle error

        original_content = messages[-1]["content"]

        if len(original_content) < self.valves.MIN_TEXT_LENGTH:
            warning_msg = f"Text too short ({len(original_content)} chars). Minimum required: {self.valves.MIN_TEXT_LENGTH}."
            await self._emit_notification(__event_emitter__, warning_msg, "warning")
            return body  # Or return a message indicating failure

        # 3. Status Notification (Start)
        await self._emit_status(__event_emitter__, "Processing...", done=False)

        try:
            # 4. Prepare Prompt
            formatted_prompt = USER_PROMPT_TEMPLATE.format(
                user_name=user_context["user_name"],
                current_date_time_str=time_context["current_date_time_str"],
                content=original_content,
                # Add other context variables
            )

            # 5. Determine Model
            target_model = self.valves.LLM_MODEL_ID
            if not target_model:
                target_model = body.get("model")
                # Note: No hardcoded fallback here, relies on system/user context

            # 6. Call LLM
            user_obj = Users.get_user_by_id(user_context["user_id"])

            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": formatted_prompt},
                ],
                "stream": False,
                # "temperature": 0.5,
            }

            llm_response = await generate_chat_completion(
                __request__, payload, user_obj
            )

            if not llm_response or "choices" not in llm_response:
                raise ValueError("Invalid LLM response")

            assistant_content = llm_response["choices"][0]["message"]["content"]

            # 7. Process Output
            processed_data = self._process_llm_output(assistant_content)

            # 8. Generate HTML/Result
            # Example: simple string replacement
            final_html = HTML_TEMPLATE.replace("{result_content}", str(processed_data))
            final_html = final_html.replace(
                "{user_language}", user_context["user_language"]
            )

            # 9. Inject Result
            if self.valves.CLEAR_PREVIOUS_HTML:
                body["messages"][-1]["content"] = self._remove_existing_html(
                    body["messages"][-1]["content"]
                )

            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] += f"\n\n{html_embed_tag}"

            # 10. Status Notification (Success)
            await self._emit_status(
                __event_emitter__, "Completed successfully!", done=True
            )
            await self._emit_notification(
                __event_emitter__, "Action completed successfully.", "success"
            )

        except Exception as e:
            logger.error(f"Action failed: {e}", exc_info=True)
            error_msg = f"Error: {str(e)}"

            # Append error to chat (optional)
            body["messages"][-1]["content"] += f"\n\n❌ **Error**: {error_msg}"

        return body
