"""
title: Flash Card
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.2.1
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjRkZENzAwIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjRkZBNzAwIi8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHBhdGggZD0iTTEzIDJMMyA3djEzbDEwIDV2LTZ6IiBmaWxsPSJ1cmwoI2cpIi8+PHBhdGggZD0iTTEzIDJ2Nmw4LTN2MTNsLTggM3YtNnoiIGZpbGw9IiM2NjdlZWEiLz48cGF0aCBkPSJNMTMgMnY2bTAgNXYxMCIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLW9wYWNpdHk9IjAuMyIvPjwvc3ZnPg==
description: Quickly generates beautiful flashcards from text, extracting key points and categories.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import logging
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Action:
    class Valves(BaseModel):
        model_id: str = Field(
            default="",
            description="Model ID used for generating card content. If empty, uses the current model.",
        )
        min_text_length: int = Field(
            default=50,
            description="Minimum text length required to generate a flashcard (characters).",
        )
        max_text_length: int = Field(
            default=2000,
            description="Recommended maximum text length. For longer texts, deep analysis tools are recommended.",
        )
        language: str = Field(
            default="en",
            description="Target language for card content (e.g., 'en', 'zh').",
        )
        show_status: bool = Field(
            default=True,
            description="Whether to show status updates in the chat interface.",
        )
        clear_previous_html: bool = Field(
            default=False,
            description="Whether to clear existing plugin-generated HTML content in the message before appending new results (identified by marker).",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __request__: Optional[Any] = None,
    ) -> Optional[dict]:
        print(f"action:{__name__} triggered")

        if not __event_emitter__:
            return body

        # Get the last user message
        messages = body.get("messages", [])
        if not messages:
            return body

        # Usually the action is triggered on the last message
        target_message = messages[-1]["content"]

        # Check text length
        text_length = len(target_message)
        if text_length < self.valves.min_text_length:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "warning",
                            "content": f"Text too short ({text_length} chars), recommended at least {self.valves.min_text_length} chars.",
                        },
                    }
                )
            return body

        if text_length > self.valves.max_text_length:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "info",
                            "content": f"Text quite long ({text_length} chars), consider using 'Deep Reading' for deep analysis.",
                        },
                    }
                )

        # Notify user that we are generating the card
        if self.valves.show_status:
            await __event_emitter__(
                {
                    "type": "notification",
                    "data": {
                        "type": "info",
                        "content": "⚡ Generating Flash Card...",
                    },
                }
            )

        try:
            # 1. Extract information using LLM
            user_id = __user__.get("id") if __user__ else "default"
            user_obj = Users.get_user_by_id(user_id)

            model = self.valves.model_id if self.valves.model_id else body.get("model")

            system_prompt = f"""
You are a Flash Card Generation Expert, specializing in creating knowledge cards suitable for learning and memorization. Your task is to distill text into concise, easy-to-remember flashcards.

Please extract the following fields and return them in JSON format:
1. "title": Create a short, precise title (3-8 words), highlighting the core concept.
2. "summary": Summarize the core essence in one sentence (10-25 words), making it easy to understand and remember.
3. "key_points": List 3-5 key memory points (5-15 words each).
   - Each point should be an independent knowledge unit.
   - Use concise, conversational expression.
   - Avoid long sentences.
4. "tags": List 2-4 classification tags (1-3 words each).
5. "category": Choose a main category (e.g., Concept, Skill, Fact, Method, etc.).

Target Language: {self.valves.language}

Important Principles:
- **Minimalism**: Refine each point to the extreme.
- **Memory First**: Content should be easy to memorize and recall.
- **Core Focus**: Extract only the most core knowledge points.
- **Conversational**: Use easy-to-understand language.
- Return ONLY the JSON object, do not include markdown formatting.
            """

            prompt = f"Please refine the following text into a learning flashcard:\n\n{target_message}"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            }

            response = await generate_chat_completion(__request__, payload, user_obj)
            content = response["choices"][0]["message"]["content"]

            # Parse JSON
            try:
                # simple cleanup in case of markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                card_data = json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse JSON: {e}, content: {content}")
                if self.valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "notification",
                            "data": {
                                "type": "error",
                                "content": "Failed to generate card data, please try again.",
                            },
                        }
                    )
                return body

            # 2. Generate HTML
            html_card = self.generate_html_card(card_data)

            # 3. Append to message
            if self.valves.clear_previous_html:
                body["messages"][-1]["content"] = self._remove_existing_html(
                    body["messages"][-1]["content"]
                )

            html_embed_tag = f"```html\n{html_card}\n```"
            body["messages"][-1]["content"] += f"\n\n{html_embed_tag}"

            if self.valves.show_status:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "success",
                            "content": "⚡ Flash Card generated successfully!",
                        },
                    }
                )

            return body

        except Exception as e:
            logger.error(f"Error generating knowledge card: {e}")
            if self.valves.show_status:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "error",
                            "content": f"Error generating knowledge card: {str(e)}",
                        },
                    }
                )
            return body

    def _remove_existing_html(self, content: str) -> str:
        """Removes existing plugin-generated HTML code blocks from the content."""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def generate_html_card(self, data):
        # Enhanced CSS with premium styling
        style = """
        <!-- OPENWEBUI_PLUGIN_OUTPUT -->
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            .knowledge-card-container {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                display: flex;
                justify-content: center;
                margin: 30px 0;
                padding: 0 10px;
            }
            
            .knowledge-card {
                width: 100%;
                max-width: 500px;
                border-radius: 20px;
                overflow: hidden;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 3px;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
            }
            
            .knowledge-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 25px 50px -12px rgba(102, 126, 234, 0.4);
            }
            
            .knowledge-card::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #4facfe);
                border-radius: 20px;
                opacity: 0;
                transition: opacity 0.4s ease;
                z-index: -1;
                filter: blur(10px);
            }
            
            .knowledge-card:hover::before {
                opacity: 0.7;
                animation: glow 2s ease-in-out infinite;
            }
            
            @keyframes glow {
                0%, 100% { opacity: 0.5; }
                50% { opacity: 0.8; }
            }
            
            .card-inner {
                background: #ffffff;
                border-radius: 18px;
                overflow: hidden;
            }
            
            .card-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 32px 28px;
                position: relative;
                overflow: hidden;
            }
            
            .card-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: rotate 15s linear infinite;
            }
            
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .card-category {
                font-size: 0.7em;
                text-transform: uppercase;
                letter-spacing: 2px;
                opacity: 0.95;
                margin-bottom: 10px;
                font-weight: 700;
                display: inline-block;
                padding: 4px 12px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            
            .card-title {
                font-size: 1.75em;
                font-weight: 800;
                margin: 0;
                line-height: 1.3;
                position: relative;
                z-index: 1;
                letter-spacing: -0.5px;
            }
            
            .card-body {
                padding: 28px;
                color: #1a1a1a;
                background: linear-gradient(to bottom, #ffffff 0%, #fafafa 100%);
            }
            
            .card-summary {
                font-size: 1.05em;
                color: #374151;
                margin-bottom: 24px;
                line-height: 1.7;
                border-left: 5px solid #764ba2;
                padding: 16px 20px;
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
                border-radius: 0 12px 12px 0;
                font-weight: 500;
                position: relative;
                overflow: hidden;
            }
            
            .card-summary::before {
                content: '"';
                position: absolute;
                top: -10px;
                left: 10px;
                font-size: 4em;
                color: rgba(118, 75, 162, 0.1);
                font-family: Georgia, serif;
                font-weight: bold;
            }
            
            .card-section-title {
                font-size: 0.85em;
                font-weight: 700;
                color: #764ba2;
                margin-bottom: 14px;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .card-section-title::before {
                content: '';
                width: 4px;
                height: 16px;
                background: linear-gradient(to bottom, #667eea, #764ba2);
                border-radius: 2px;
            }
            
            .card-points {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            
            .card-points li {
                margin-bottom: 14px;
                padding: 12px 16px 12px 44px;
                position: relative;
                line-height: 1.6;
                color: #374151;
                background: #ffffff;
                border-radius: 10px;
                transition: all 0.3s ease;
                border: 1px solid #e5e7eb;
                font-weight: 500;
            }
            
            .card-points li:hover {
                transform: translateX(5px);
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
                border-color: #764ba2;
                box-shadow: 0 4px 12px rgba(118, 75, 162, 0.1);
            }
            
            .card-points li::before {
                content: '✓';
                color: #ffffff;
                background: linear-gradient(135deg, #667eea, #764ba2);
                font-weight: bold;
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                font-size: 0.85em;
                box-shadow: 0 2px 8px rgba(118, 75, 162, 0.3);
            }
            
            .card-footer {
                padding: 20px 28px;
                background: linear-gradient(to right, #f8fafc 0%, #f1f5f9 100%);
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                border-top: 2px solid #e5e7eb;
                align-items: center;
            }
            
            .card-tag-label {
                font-size: 0.75em;
                font-weight: 700;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-right: 4px;
            }
            
            .card-tag {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
                transition: all 0.3s ease;
                border: 2px solid transparent;
                cursor: default;
                letter-spacing: 0.3px;
            }
            
            .card-tag:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            /* Dark mode support */
            @media (prefers-color-scheme: dark) {
                .card-inner {
                    background: #1e1e1e;
                }
                
                .card-body {
                    background: linear-gradient(to bottom, #1e1e1e 0%, #252525 100%);
                    color: #e5e7eb;
                }
                
                .card-summary {
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                    color: #d1d5db;
                }
                
                .card-summary::before {
                    color: rgba(118, 75, 162, 0.2);
                }
                
                .card-points li {
                    color: #d1d5db;
                    background: #2d2d2d;
                    border-color: #404040;
                }
                
                .card-points li:hover {
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                    border-color: #667eea;
                }
                
                .card-footer {
                    background: linear-gradient(to right, #252525 0%, #2d2d2d 100%);
                    border-top-color: #404040;
                }
                
                .card-tag-label {
                    color: #9ca3af;
                }
            }
            
            /* Mobile responsive */
            @media (max-width: 640px) {
                .knowledge-card {
                    max-width: 100%;
                }
                
                .card-header {
                    padding: 24px 20px;
                }
                
                .card-title {
                    font-size: 1.5em;
                }
                
                .card-body {
                    padding: 20px;
                }
                
                .card-footer {
                    padding: 16px 20px;
                }
            }
        </style>
        """

        # Enhanced HTML structure
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {style}
</head>
<body>
    <div class="knowledge-card-container">
        <div class="knowledge-card">
            <div class="card-inner">
                <div class="card-header">
                    <div class="card-category">{data.get('category', 'General Knowledge')}</div>
                    <h2 class="card-title">{data.get('title', 'Flash Card')}</h2>
                </div>
                <div class="card-body">
                    <div class="card-summary">
                        {data.get('summary', '')}
                    </div>
                    <div class="card-section-title">Key Points</div>
                    <ul class="card-points">
                        {''.join([f'<li>{point}</li>' for point in data.get('key_points', [])])}
                    </ul>
                </div>
                <div class="card-footer">
                    <span class="card-tag-label">Tags</span>
                    {''.join([f'<span class="card-tag">#{tag}</span>' for tag in data.get('tags', [])])}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
