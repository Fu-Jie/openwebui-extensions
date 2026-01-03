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

# HTML Wrapper Template (supports multiple plugins and grid layout)
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
            flex: 1 1 400px; /* Default width, allows shrinking/growing */
            min-width: 300px; 
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            overflow: hidden; 
            border: 1px solid #e5e7eb; 
            transition: all 0.3s ease;
        }
        .plugin-item:hover {
            box-shadow: 0 10px 15px rgba(0,0,0,0.1);
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


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates in the chat interface.",
        )
        MODEL_ID: str = Field(
            default="",
            description="Built-in LLM Model ID used for processing. If empty, uses the current conversation's model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="Minimum text length required for processing (characters).",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to force clear previous plugin results (if True, overwrites instead of merging).",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="Number of recent messages to use for generation. Set to 1 for just the last message, or higher for more context.",
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
            "current_date_time_str": now.strftime("%B %d, %Y %H:%M:%S"),
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

    def _extract_text_content(self, content) -> str:
        """Extract text from message content, supporting multimodal message formats."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Multimodal message: [{"type": "text", "text": "..."}, {"type": "image_url", ...}]
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
        user_language: str = "en-US",
    ) -> str:
        """
        Merges new content into an existing HTML container, or creates a new one.
        """
        # Check for compatible container marker
        if (
            "<!-- OPENWEBUI_PLUGIN_OUTPUT -->" in existing_html_code
            and "<!-- CONTENT_INSERTION_POINT -->" in existing_html_code
        ):
            base_html = existing_html_code
            # Remove code block markers ```html ... ``` for processing
            base_html = re.sub(r"^```html\s*", "", base_html)
            base_html = re.sub(r"\s*```$", "", base_html)
        else:
            # Initialize new container
            base_html = HTML_WRAPPER_TEMPLATE.replace("{user_language}", user_language)

        # Wrap new content
        wrapped_content = f'<div class="plugin-item">\n{new_content}\n</div>'

        # Inject Styles
        if new_styles:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n/* STYLES_INSERTION_POINT */",
            )

        # Inject Content
        base_html = base_html.replace(
            "<!-- CONTENT_INSERTION_POINT -->",
            f"{wrapped_content}\n<!-- CONTENT_INSERTION_POINT -->",
        )

        # Inject Scripts
        if new_scripts:
            base_html = base_html.replace(
                "<!-- SCRIPTS_INSERTION_POINT -->",
                f"{new_scripts}\n<!-- SCRIPTS_INSERTION_POINT -->",
            )

        return base_html.strip()

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        """Emits a status update event."""
        if self.valves.SHOW_STATUS and emitter:
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
        if not messages:
            return body  # Or handle error

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
                    "User"
                    if role == "user"
                    else "Assistant" if role == "assistant" else role
                )
                aggregated_parts.append(f"{text_content}")

        if not aggregated_parts:
            return body  # Or handle error

        original_content = "\n\n---\n\n".join(aggregated_parts)

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
            target_model = self.valves.MODEL_ID
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

            await self._emit_status(__event_emitter__, "Processing failed.", done=True)
            await self._emit_notification(
                __event_emitter__, "Action failed, please check logs.", "error"
            )

        return body
