"""
title: Smart Mind Map
icon_url: lucide:git-branch
version: 0.7.4
description: Intelligently analyzes long texts and generates interactive mind maps, supporting SVG/Markdown export.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import time
import re
from fastapi import Request
from datetime import datetime
import pytz

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_MINDMAP_ASSISTANT = """
You are a professional mind map generation assistant, capable of efficiently analyzing long-form text provided by users and structuring its core themes, key concepts, branches, and sub-branches into standard Markdown list syntax for rendering by Markmap.js.

Please strictly follow these guidelines:
-   **Language**: All output must be in the language specified by the user.
-   **Format**: Your output must strictly be in Markdown list format, wrapped with ```markdown and ```.
    -   Use `#` to define the central theme (root node).
    -   Use `-` with two-space indentation to represent branches and sub-branches.
-   **Content**:
    -   Identify the central theme of the text as the `#` heading.
    -   Identify main concepts as first-level list items.
    -   Identify supporting details or sub-concepts as nested list items.
    -   Node content should be concise and clear, avoiding verbosity.
-   **Output Markdown syntax only**: Do not include any additional greetings, explanations, or guiding text.
-   **If text is too short or cannot generate a valid mind map**: Output a simple Markdown list indicating inability to generate, for example:
    ```markdown
    # Unable to Generate Mind Map
    - Reason: Insufficient or unclear text content
    ```
"""

USER_PROMPT_GENERATE_MINDMAP = """
Please analyze the following long-form text and structure its core themes, key concepts, branches, and sub-branches into standard Markdown list syntax for Markmap.js rendering.

---
**User Context Information:**
User Name: {user_name}
Current Date & Time: {current_date_time_str}
Current Weekday: {current_weekday}
Current Timezone: {current_timezone_str}
User Language: {user_language}
---

**Long-form Text Content:**
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
            flex-wrap: wrap; 
            gap: 20px; 
            align-items: flex-start; 
            width: 100%;
        }
        .plugin-item { 
            flex: 1 1 400px; /* Default width, allows stretching */
            min-width: 300px; 
            border-radius: 12px; 
            overflow: hidden; 
            transition: all 0.3s ease;
        }
        .plugin-item:hover {
            transform: translateY(-2px);
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

CSS_TEMPLATE_MINDMAP = """
        :root {
            --primary-color: #1e88e5;
            --secondary-color: #43a047;
            --background-color: #f4f6f8;
            --card-bg-color: #ffffff;
            --text-color: #263238;
            --muted-text-color: #546e7a;
            --border-color: #e0e0e0;
            --header-gradient: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            --shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
            --border-radius: 12px;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .mindmap-container-wrapper {
            font-family: var(--font-family);
            line-height: 1.7;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: var(--header-gradient);
            color: white;
            padding: 20px 24px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 1.5em;
            font-weight: 600;
            text-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .user-context {
            font-size: 0.8em;
            color: var(--muted-text-color);
            background-color: #eceff1;
            padding: 8px 16px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
        }
        .user-context span { margin: 2px 8px; }
        .content-area { 
            padding: 20px;
            flex-grow: 1;
        }
        .markmap-container {
            position: relative;
            background-color: #fff;
            background-image: radial-gradient(var(--border-color) 0.5px, transparent 0.5px);
            background-size: 20px 20px;
            border-radius: 8px;
            padding: 16px;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid var(--border-color);
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.03);
        }
        .download-area {
            text-align: center;
            padding-top: 20px;
            margin-top: 20px;
            border-top: 1px solid var(--border-color);
        }
        .download-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            margin: 0 6px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .download-btn.secondary {
            background-color: var(--secondary-color);
        }
        .download-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .download-btn.copied {
            background-color: #2e7d32;
        }
        .footer {
            text-align: center;
            padding: 16px;
            font-size: 0.8em;
            color: #90a4ae;
            background-color: #eceff1;
            border-top: 1px solid var(--border-color);
        }
        .footer a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .error-message {
            color: #c62828;
            background-color: #ffcdd2;
            border: 1px solid #ef9a9a;
            padding: 16px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 1em;
        }
"""

CONTENT_TEMPLATE_MINDMAP = """
        <div class="mindmap-container-wrapper">
            <div class="header">
                <h1>🧠 Smart Mind Map</h1>
            </div>
            <div class="user-context">
                <span><strong>User:</strong> {user_name}</span>
                <span><strong>Time:</strong> {current_date_time_str}</span>
            </div>
            <div class="content-area">
                <div class="markmap-container" id="markmap-container-{unique_id}"></div>
                <div class="download-area">
                    <button id="download-svg-btn-{unique_id}" class="download-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        <span class="btn-text">SVG</span>
                    </button>
                    <button id="download-md-btn-{unique_id}" class="download-btn secondary">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                        <span class="btn-text">Markdown</span>
                    </button>
                </div>
            </div>
            <div class="footer">
                <p>© {current_year} Smart Mind Map • <a href="https://markmap.js.org/" target="_blank">Markmap</a></p>
            </div>
        </div>
        
        <script type="text/template" id="markdown-source-{unique_id}">{markdown_syntax}</script>
"""

SCRIPT_TEMPLATE_MINDMAP = """
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.17"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.17"></script>
    <script>
      (function() {
        const renderMindmap = () => {
            const uniqueId = "{unique_id}";
            const containerEl = document.getElementById('markmap-container-' + uniqueId);
            if (!containerEl || containerEl.dataset.markmapRendered) return;

            const sourceEl = document.getElementById('markdown-source-' + uniqueId);
            if (!sourceEl) return;

            const markdownContent = sourceEl.textContent.trim();
            if (!markdownContent) {
                containerEl.innerHTML = '<div class="error-message">⚠️ Unable to load mind map: Missing valid content.</div>';
                return;
            }

            try {
                const svgEl = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                svgEl.style.width = '100%';
                svgEl.style.height = 'auto';
                svgEl.style.minHeight = '300px';
                containerEl.innerHTML = ''; 
                containerEl.appendChild(svgEl);

                const { Transformer, Markmap } = window.markmap;
                const transformer = new Transformer();
                const { root } = transformer.transform(markdownContent);
                
                const style = (id) => `${id} text { font-size: 14px !important; }`;

                const options = { 
                    autoFit: true,
                    style: style
                };
                Markmap.create(svgEl, options, root);
                
                containerEl.dataset.markmapRendered = 'true';
                
                attachDownloadHandlers(uniqueId);

            } catch (error) {
                console.error('Markmap rendering error:', error);
                containerEl.innerHTML = '<div class="error-message">⚠️ Mind map rendering failed!<br>Reason: ' + error.message + '</div>';
            }
        };

        const attachDownloadHandlers = (uniqueId) => {
            const downloadSvgBtn = document.getElementById('download-svg-btn-' + uniqueId);
            const downloadMdBtn = document.getElementById('download-md-btn-' + uniqueId);
            const containerEl = document.getElementById('markmap-container-' + uniqueId);

            const showFeedback = (button, isSuccess) => {
                const buttonText = button.querySelector('.btn-text');
                const originalText = buttonText.textContent;
                
                button.disabled = true;
                if (isSuccess) {
                    buttonText.textContent = '✅';
                    button.classList.add('copied');
                } else {
                    buttonText.textContent = '❌';
                }

                setTimeout(() => {
                    buttonText.textContent = originalText;
                    button.disabled = false;
                    button.classList.remove('copied');
                }, 2500);
            };

            const copyToClipboard = (content, button) => {
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(content).then(() => {
                        showFeedback(button, true);
                    }, () => {
                        showFeedback(button, false);
                    });
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
                        showFeedback(button, true);
                    } catch (err) {
                        showFeedback(button, false);
                    }
                    document.body.removeChild(textArea);
                }
            };

            if (downloadSvgBtn) {
                downloadSvgBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    const svgEl = containerEl.querySelector('svg');
                    if (svgEl) {
                        const svgData = new XMLSerializer().serializeToString(svgEl);
                        copyToClipboard(svgData, downloadSvgBtn);
                    }
                });
            }

            if (downloadMdBtn) {
                downloadMdBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    const markdownContent = document.getElementById('markdown-source-' + uniqueId).textContent;
                    copyToClipboard(markdownContent, downloadMdBtn);
                });
            }
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
            default=True,
            description="Whether to show action status updates in the chat interface.",
        )
        MODEL_ID: str = Field(
            default="",
            description="Built-in LLM model ID for text analysis. If empty, uses the current conversation's model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=100,
            description="Minimum text length (character count) required for mind map analysis.",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to force clear previous plugin results (if True, overwrites instead of merging).",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="Number of recent messages to use for generation. Set to 1 for just the last message, or higher for more context.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.weekday_map = {
            "Monday": "Monday",
            "Tuesday": "Tuesday",
            "Wednesday": "Wednesday",
            "Thursday": "Thursday",
            "Friday": "Friday",
            "Saturday": "Saturday",
            "Sunday": "Sunday",
        }

    def _extract_markdown_syntax(self, llm_output: str) -> str:
        match = re.search(r"```markdown\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            extracted_content = match.group(1).strip()
        else:
            logger.warning(
                "LLM output did not strictly follow the expected Markdown format, treating the entire output as summary."
            )
            extracted_content = llm_output.strip()
        return extracted_content.replace("</script>", "<\\/script>")

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """Emits a status update event."""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        """Emits a notification event (info/success/warning/error)."""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    def _remove_existing_html(self, content: str) -> str:
        """Removes existing plugin-generated HTML code blocks from the content."""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _extract_text_content(self, content) -> str:
        """Extract text from message content, supporting multimodal message formats"""
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
        logger.info("Action: Smart Mind Map (v0.7.2) started")

        if isinstance(__user__, (list, tuple)):
            user_language = (
                __user__[0].get("language", "en-US") if __user__ else "en-US"
            )
            user_name = __user__[0].get("name", "User") if __user__[0] else "User"
            user_id = (
                __user__[0]["id"]
                if __user__ and "id" in __user__[0]
                else "unknown_user"
            )
        elif isinstance(__user__, dict):
            user_language = __user__.get("language", "en-US")
            user_name = __user__.get("name", "User")
            user_id = __user__.get("id", "unknown_user")

        try:
            shanghai_tz = pytz.timezone("Asia/Shanghai")
            current_datetime_shanghai = datetime.now(shanghai_tz)
            current_date_time_str = current_datetime_shanghai.strftime(
                "%B %d, %Y %H:%M:%S"
            )
            current_weekday_en = current_datetime_shanghai.strftime("%A")
            current_weekday_zh = self.weekday_map.get(current_weekday_en, "Unknown")
            current_year = current_datetime_shanghai.strftime("%Y")
            current_timezone_str = "Asia/Shanghai"
        except Exception as e:
            logger.warning(f"Failed to get timezone info: {e}, using default values.")
            now = datetime.now()
            current_date_time_str = now.strftime("%B %d, %Y %H:%M:%S")
            current_weekday_zh = "Unknown"
            current_year = now.strftime("%Y")
            current_timezone_str = "Unknown"

        await self._emit_notification(
            __event_emitter__,
            "Smart Mind Map is starting, generating mind map for you...",
            "info",
        )

        messages = body.get("messages")
        if not messages or not isinstance(messages, list):
            error_message = "Unable to retrieve valid user message content."
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
                    "User"
                    if role == "user"
                    else "Assistant" if role == "assistant" else role
                )
                aggregated_parts.append(f"[{role_label} Message {i}]\n{text_content}")

        if not aggregated_parts:
            error_message = "Unable to retrieve valid user message content."
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
            short_text_message = f"Text content is too short ({len(long_text_content)} characters), unable to perform effective analysis. Please provide at least {self.valves.MIN_TEXT_LENGTH} characters of text."
            await self._emit_notification(
                __event_emitter__, short_text_message, "warning"
            )
            return {
                "messages": [
                    {"role": "assistant", "content": f"⚠️ {short_text_message}"}
                ]
            }

        await self._emit_status(
            __event_emitter__,
            "Smart Mind Map: Analyzing text structure in depth...",
            False,
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

            # Determine model to use
            target_model = self.valves.MODEL_ID
            if not target_model:
                target_model = body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_MINDMAP_ASSISTANT},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "temperature": 0.5,
                "stream": False,
            }
            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"Unable to get user object, user ID: {user_id}")

            llm_response = await generate_chat_completion(
                __request__, llm_payload, user_obj
            )

            if (
                not llm_response
                or "choices" not in llm_response
                or not llm_response["choices"]
            ):
                raise ValueError("LLM response format is incorrect or empty.")

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

            await self._emit_status(
                __event_emitter__, "Smart Mind Map: Drawing completed!", True
            )
            await self._emit_notification(
                __event_emitter__,
                f"Mind map has been generated, {user_name}!",
                "success",
            )
            logger.info("Action: Smart Mind Map (v0.7.2) completed successfully")

        except Exception as e:
            error_message = f"Smart Mind Map processing failed: {str(e)}"
            logger.error(f"Smart Mind Map error: {error_message}", exc_info=True)
            user_facing_error = f"Sorry, Smart Mind Map encountered an error during processing: {str(e)}.\nPlease check the Open WebUI backend logs for more details."
            body["messages"][-1][
                "content"
            ] = f"{long_text_content}\n\n❌ **Error:** {user_facing_error}"

            await self._emit_status(
                __event_emitter__, "Smart Mind Map: Processing failed.", True
            )
            await self._emit_notification(
                __event_emitter__,
                f"Smart Mind Map generation failed, {user_name}!",
                "error",
            )

        return body
