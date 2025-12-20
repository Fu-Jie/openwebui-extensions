"""
title: Deep Reading & Summary
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.1.0
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yIDNIMGEyIDIgMCAwIDAgMiAyIi8+PHBhdGggZD0iTTIyIDNIMjBhMiAyIDAgMCAwLTIgMiIvPjxwYXRoIGQ9Ik0yIDdoMjB2MTRhMiAyIDAgMCAxLTIgMmgtMTZhMiAyIDAgMCAxLTItMnYtMTQiLz48cGF0aCBkPSJNMTEgMTJ2NiIvPjxwYXRoIGQ9Ik0xNiAxMnY2Ii8+PHBhdGggZD0iTTYgMTJ2NiIvPjwvc3ZnPg==
description: Provides deep reading analysis and summarization for long texts.
requirements: jinja2, markdown
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import re
from fastapi import Request
from datetime import datetime
import pytz
import markdown
from jinja2 import Template

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================================================================
# Internal LLM Prompts
# =================================================================

SYSTEM_PROMPT_READING_ASSISTANT = """
You are a professional Deep Text Analysis Expert, specializing in reading long texts and extracting the essence. Your task is to conduct a comprehensive and in-depth analysis.

Please provide the following:
1.  **Detailed Summary**: Summarize the core content of the text in 2-3 paragraphs, ensuring accuracy and completeness. Do not be too brief; ensure the reader fully understands the main idea.
2.  **Key Information Points**: List 5-8 most important facts, viewpoints, or arguments. Each point should:
    - Be specific and insightful
    - Include necessary details and context
    - Use Markdown list format
3.  **Actionable Advice**: Identify and refine specific, actionable items from the text. Each suggestion should:
    - Be clear and actionable
    - Include execution priority or timing suggestions
    - If there are no clear action items, provide learning suggestions or thinking directions

Please strictly follow these guidelines:
-   **Language**: All output must be in the user's specified language.
-   **Format**: Please strictly follow the Markdown format below, ensuring each section has a clear header:
    ## Summary
    [Detailed summary content here, 2-3 paragraphs, use Markdown **bold** or *italic* to emphasize key points]

    ## Key Information Points
    - [Key Point 1: Include specific details and context]
    - [Key Point 2: Include specific details and context]
    - [Key Point 3: Include specific details and context]
    - [At least 5, at most 8 key points]

    ## Actionable Advice
    - [Action Item 1: Specific, actionable, include priority]
    - [Action Item 2: Specific, actionable, include priority]
    - [If no clear action items, provide learning suggestions or thinking directions]
-   **Depth First**: Analysis should be deep and comprehensive, not superficial.
-   **Action Oriented**: Focus on actionable suggestions and next steps.
-   **Analysis Results Only**: Do not include any extra pleasantries, explanations, or leading text.
"""

USER_PROMPT_GENERATE_SUMMARY = """
Please conduct a deep analysis of the following long text, providing:
1.  Detailed Summary (2-3 paragraphs, comprehensive overview)
2.  Key Information Points List (5-8 items, including specific details)
3.  Actionable Advice (Specific, clear, including priority)

---
**User Context:**
User Name: {user_name}
Current Date/Time: {current_date_time_str}
Weekday: {current_weekday}
Timezone: {current_timezone_str}
User Language: {user_language}
---

**Long Text Content:**
```
{long_text_content}
```

Please conduct a deep and comprehensive analysis, focusing on actionable advice.
"""

# =================================================================
# Frontend HTML Template (Jinja2 Syntax)
# =================================================================

HTML_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{{ user_language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Reading: Deep Analysis Report</title>
    <style>
        :root {
            --primary-color: #4285f4;
            --secondary-color: #1e88e5;
            --action-color: #34a853;
            --background-color: #f8f9fa;
            --card-bg-color: #ffffff;
            --text-color: #202124;
            --muted-text-color: #5f6368;
            --border-color: #dadce0;
            --header-gradient: linear-gradient(135deg, #4285f4, #1e88e5);
            --shadow: 0 1px 3px rgba(60,64,67,.3);
            --border-radius: 8px;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        body {
            font-family: var(--font-family);
            line-height: 1.8;
            color: var(--text-color);
            margin: 0;
            padding: 24px;
            background-color: var(--background-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        .container {
            max-width: 900px;
            margin: 20px auto;
            background: var(--card-bg-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        .header {
            background: var(--header-gradient);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.2em;
            font-weight: 500;
            letter-spacing: -0.5px;
        }
        .user-context {
            font-size: 0.9em;
            color: var(--muted-text-color);
            background-color: #f1f3f4;
            padding: 16px 40px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
        }
        .user-context span { margin: 4px 12px; }
        .content { padding: 40px; }
        .section {
            margin-bottom: 32px;
            padding-bottom: 32px;
            border-bottom: 1px solid #e8eaed;
        }
        .section:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .section h2 {
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.5em;
            font-weight: 500;
            color: var(--text-color);
            display: flex;
            align-items: center;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--primary-color);
        }
        .section h2 .icon {
            margin-right: 12px;
            font-size: 1.3em;
            line-height: 1;
        }
        .summary-section h2 { border-bottom-color: var(--primary-color); }
        .keypoints-section h2 { border-bottom-color: var(--secondary-color); }
        .actions-section h2 { border-bottom-color: var(--action-color); }

        .html-content {
            font-size: 1.05em;
            line-height: 1.8;
        }
        .html-content p:first-child { margin-top: 0; }
        .html-content p:last-child { margin-bottom: 0; }
        .html-content ul {
            list-style: none;
            padding-left: 0;
            margin: 16px 0;
        }
        .html-content li {
            padding: 12px 0 12px 32px;
            position: relative;
            margin-bottom: 8px;
            line-height: 1.7;
        }
        .html-content li::before {
            position: absolute;
            left: 0;
            top: 12px;
            font-family: 'Arial';
            font-weight: bold;
            font-size: 1.1em;
        }
        .keypoints-section .html-content li::before { 
            content: '•'; 
            color: var(--secondary-color);
            font-size: 1.5em;
            top: 8px;
        }
        .actions-section .html-content li::before { 
            content: '▸'; 
            color: var(--action-color); 
        }
        
        .no-content { 
            color: var(--muted-text-color); 
            font-style: italic;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .footer {
            text-align: center;
            padding: 24px;
            font-size: 0.85em;
            color: #5f6368;
            background-color: #f8f9fa;
            border-top: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📖 Deep Reading: Deep Analysis Report</h1>
        </div>
        <div class="user-context">
            <span><strong>User:</strong> {{ user_name }}</span>
            <span><strong>Analysis Time:</strong> {{ current_date_time_str }}</span>
            <span><strong>Weekday:</strong> {{ current_weekday }}</span>
        </div>
        <div class="content">
            <div class="section summary-section">
                <h2><span class="icon">📝</span>Detailed Summary</h2>
                <div class="html-content">{{ summary_html | safe }}</div>
            </div>
            <div class="section keypoints-section">
                <h2><span class="icon">💡</span>Key Information Points</h2>
                <div class="html-content">{{ keypoints_html | safe }}</div>
            </div>
            <div class="section actions-section">
                <h2><span class="icon">🎯</span>Actionable Advice</h2>
                <div class="html-content">{{ actions_html | safe }}</div>
            </div>
        </div>
        <div class="footer">
            <p>&copy; {{ current_year }} Deep Reading - Deep Text Analysis Service</p>
        </div>
    </div>
</body>
</html>"""


class Action:
    class Valves(BaseModel):
        show_status: bool = Field(
            default=True,
            description="Whether to show operation status updates in the chat interface.",
        )
        LLM_MODEL_ID: str = Field(
            default="",
            description="Built-in LLM Model ID used for text analysis. If empty, uses the current conversation's model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=200,
            description="Minimum text length required for deep analysis (characters). Recommended 200+.",
        )
        RECOMMENDED_MIN_LENGTH: int = Field(
            default=500,
            description="Recommended minimum text length for best analysis results.",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to clear existing plugin-generated HTML content in the message before appending new results (identified by marker).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _process_llm_output(self, llm_output: str) -> Dict[str, str]:
        """
        Parse LLM Markdown output and convert to HTML fragments.
        """
        summary_match = re.search(
            r"##\s*Summary\s*\n(.*?)(?=\n##|$)", llm_output, re.DOTALL | re.IGNORECASE
        )
        keypoints_match = re.search(
            r"##\s*Key Information Points\s*\n(.*?)(?=\n##|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )
        actions_match = re.search(
            r"##\s*Actionable Advice\s*\n(.*?)(?=\n##|$)",
            llm_output,
            re.DOTALL | re.IGNORECASE,
        )

        summary_md = summary_match.group(1).strip() if summary_match else ""
        keypoints_md = keypoints_match.group(1).strip() if keypoints_match else ""
        actions_md = actions_match.group(1).strip() if actions_match else ""

        if not any([summary_md, keypoints_md, actions_md]):
            summary_md = llm_output.strip()
            logger.warning(
                "LLM output did not follow expected Markdown format. Treating entire output as summary."
            )

        # Use 'nl2br' extension to convert newlines \n to <br>
        md_extensions = ["nl2br"]
        summary_html = (
            markdown.markdown(summary_md, extensions=md_extensions)
            if summary_md
            else '<p class="no-content">Failed to extract summary.</p>'
        )
        keypoints_html = (
            markdown.markdown(keypoints_md, extensions=md_extensions)
            if keypoints_md
            else '<p class="no-content">Failed to extract key information points.</p>'
        )
        actions_html = (
            markdown.markdown(actions_md, extensions=md_extensions)
            if actions_md
            else '<p class="no-content">No explicit actionable advice.</p>'
        )

        return {
            "summary_html": summary_html,
            "keypoints_html": keypoints_html,
            "actions_html": actions_html,
        }

    def _remove_existing_html(self, content: str) -> str:
        """Removes existing plugin-generated HTML code blocks from the content."""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _build_html(self, context: dict) -> str:
        """
        Build final HTML content using Jinja2 template and context data.
        """
        template = Template(HTML_TEMPLATE)
        return template.render(context)

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: Deep Reading Started (v2.0.0)")

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

        now = datetime.now()
        current_date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        current_weekday = now.strftime("%A")
        current_year = now.strftime("%Y")
        current_timezone_str = "Unknown Timezone"

        original_content = ""
        try:
            messages = body.get("messages", [])
            if not messages or not messages[-1].get("content"):
                raise ValueError("Unable to get valid user message content.")

            original_content = messages[-1]["content"]

            if len(original_content) < self.valves.MIN_TEXT_LENGTH:
                short_text_message = f"Text content too short ({len(original_content)} chars), recommended at least {self.valves.MIN_TEXT_LENGTH} chars for effective deep analysis.\n\n💡 Tip: For short texts, consider using '⚡ Flash Card' for quick refinement."
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "notification",
                            "data": {"type": "warning", "content": short_text_message},
                        }
                    )
                return {
                    "messages": [
                        {"role": "assistant", "content": f"⚠️ {short_text_message}"}
                    ]
                }

            # Recommend for longer texts
            if len(original_content) < self.valves.RECOMMENDED_MIN_LENGTH:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "notification",
                            "data": {
                                "type": "info",
                                "content": f"Text length is {len(original_content)} chars. Recommended {self.valves.RECOMMENDED_MIN_LENGTH}+ chars for best analysis results.",
                            },
                        }
                    )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "info",
                            "content": "📖 Deep Reading started, analyzing deeply...",
                        },
                    }
                )
                if self.valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "📖 Deep Reading: Analyzing text, extracting essence...",
                                "done": False,
                            },
                        }
                    )

            formatted_user_prompt = USER_PROMPT_GENERATE_SUMMARY.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                current_weekday=current_weekday,
                current_timezone_str=current_timezone_str,
                user_language=user_language,
                long_text_content=original_content,
            )

            # Determine model to use
            target_model = self.valves.LLM_MODEL_ID
            if not target_model:
                target_model = body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_READING_ASSISTANT},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "stream": False,
            }

            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"Unable to get user object, User ID: {user_id}")

            llm_response = await generate_chat_completion(
                __request__, llm_payload, user_obj
            )
            assistant_response_content = llm_response["choices"][0]["message"][
                "content"
            ]

            processed_content = self._process_llm_output(assistant_response_content)

            context = {
                "user_language": user_language,
                "user_name": user_name,
                "current_date_time_str": current_date_time_str,
                "current_weekday": current_weekday,
                "current_year": current_year,
                **processed_content,
            }

            final_html_content = self._build_html(context)

            if self.valves.CLEAR_PREVIOUS_HTML:
                original_content = self._remove_existing_html(original_content)

            html_embed_tag = f"```html\n{final_html_content}\n```"
            body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"

            if self.valves.show_status and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "📖 Deep Reading: Analysis complete!",
                            "done": True,
                        },
                    }
                )
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "success",
                            "content": f"📖 Deep Reading complete, {user_name}! Deep analysis report generated.",
                        },
                    }
                )

        except Exception as e:
            error_message = f"Deep Reading processing failed: {str(e)}"
            logger.error(f"Deep Reading Error: {error_message}", exc_info=True)
            user_facing_error = f"Sorry, Deep Reading encountered an error while processing: {str(e)}.\nPlease check Open WebUI backend logs for more details."
            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n❌ **Error:** {user_facing_error}"

            if __event_emitter__:
                if self.valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Deep Reading: Processing failed.",
                                "done": True,
                            },
                        }
                    )
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "error",
                            "content": f"Deep Reading processing failed, {user_name}!",
                        },
                    }
                )

        return body
