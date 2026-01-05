"""
title: 📊 Infographic to Markdown
author: Fu-Jie
version: 1.0.0
description: AI生成信息图语法，前端渲染SVG并转换为Markdown图片格式嵌入消息。支持AntV Infographic模板。
"""

import time
import json
import logging
import re
from typing import Optional, Callable, Awaitable, Any, Dict
from pydantic import BaseModel, Field
from fastapi import Request
from datetime import datetime

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================================================================
# LLM Prompts
# =================================================================

SYSTEM_PROMPT_INFOGRAPHIC = """
You are a professional infographic design expert who can analyze user-provided text content and convert it into AntV Infographic syntax format.

## Infographic Syntax Specification

Infographic syntax is a Mermaid-like declarative syntax for describing infographic templates, data, and themes.

### Syntax Rules
- Entry uses `infographic <template-name>`
- Key-value pairs are separated by spaces, **absolutely NO colons allowed**
- Use two spaces for indentation
- Object arrays use `-` with line breaks

⚠️ **IMPORTANT WARNING: This is NOT YAML format!**
- ❌ Wrong: `children:` `items:` `data:` (with colons)
- ✅ Correct: `children` `items` `data` (without colons)

### Template Library & Selection Guide

Choose the most appropriate template based on the content structure:

#### 1. List & Hierarchy
- **List**: `list-grid` (Grid Cards), `list-vertical` (Vertical List)
- **Tree**: `tree-vertical` (Vertical Tree), `tree-horizontal` (Horizontal Tree)
- **Mindmap**: `mindmap` (Mind Map)

#### 2. Sequence & Relationship
- **Process**: `sequence-roadmap` (Roadmap), `sequence-zigzag` (Zigzag Process)
- **Relationship**: `relation-sankey` (Sankey Diagram), `relation-circle` (Circular)

#### 3. Comparison & Analysis
- **Comparison**: `compare-binary` (Binary Comparison)
- **Analysis**: `compare-swot` (SWOT Analysis), `quadrant-quarter` (Quadrant Chart)

#### 4. Charts & Data
- **Charts**: `chart-bar`, `chart-column`, `chart-line`, `chart-pie`, `chart-doughnut`, `chart-area`

### Data Structure Examples

#### A. Standard List/Tree
```infographic
infographic list-grid
data
  title Project Modules
  items
    - label Module A
      desc Description of A
    - label Module B
      desc Description of B
```

#### B. Binary Comparison
```infographic
infographic compare-binary
data
  title Advantages vs Disadvantages
  items
    - label Advantages
      children
        - label Strong R&D
          desc Leading technology
    - label Disadvantages
      children
        - label Weak brand
          desc Insufficient marketing
```

#### C. Charts
```infographic
infographic chart-bar
data
  title Quarterly Revenue
  items
    - label Q1
      value 120
    - label Q2
      value 150
```

### Common Data Fields
- `label`: Main title/label (Required)
- `desc`: Description text (max 30 Chinese chars / 60 English chars for `list-grid`)
- `value`: Numeric value (for charts)
- `children`: Nested items

## Output Requirements
1. **Language**: Output content in the user's language.
2. **Format**: Wrap output in ```infographic ... ```.
3. **No Colons**: Do NOT use colons after keys.
4. **Indentation**: Use 2 spaces.
"""

USER_PROMPT_GENERATE = """
Please analyze the following text content and convert its core information into AntV Infographic syntax format.

---
**User Context:**
User Name: {user_name}
Current Date/Time: {current_date_time_str}
User Language: {user_language}
---

**Text Content:**
{long_text_content}

Please select the most appropriate infographic template based on text characteristics and output standard infographic syntax.

**Important Note:** 
- If using `list-grid` format, ensure each card's `desc` description is limited to **maximum 30 Chinese characters** (or **approximately 60 English characters**).
- Descriptions should be concise and highlight key points.
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True, description="Show operation status updates in chat interface."
        )
        MODEL_ID: str = Field(
            default="",
            description="LLM model ID for text analysis. If empty, uses current conversation model.",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="Minimum text length (characters) required for infographic analysis.",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="Number of recent messages to use for generation.",
        )
        SVG_WIDTH: int = Field(
            default=800,
            description="Width of generated SVG in pixels.",
        )
        EXPORT_FORMAT: str = Field(
            default="svg",
            description="Export format: 'svg' or 'png'.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _extract_chat_id(self, body: dict, metadata: Optional[dict]) -> str:
        """Extract chat_id from body or metadata"""
        if isinstance(body, dict):
            chat_id = body.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()

            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                chat_id = body_metadata.get("chat_id")
                if isinstance(chat_id, str) and chat_id.strip():
                    return chat_id.strip()

        if isinstance(metadata, dict):
            chat_id = metadata.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()

        return ""

    def _extract_message_id(self, body: dict, metadata: Optional[dict]) -> str:
        """Extract message_id from body or metadata"""
        if isinstance(body, dict):
            message_id = body.get("id")
            if isinstance(message_id, str) and message_id.strip():
                return message_id.strip()

            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                message_id = body_metadata.get("message_id")
                if isinstance(message_id, str) and message_id.strip():
                    return message_id.strip()

        if isinstance(metadata, dict):
            message_id = metadata.get("message_id")
            if isinstance(message_id, str) and message_id.strip():
                return message_id.strip()

        return ""

    def _extract_infographic_syntax(self, llm_output: str) -> str:
        """Extract infographic syntax from LLM output"""
        match = re.search(r"```infographic\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            logger.warning("LLM output did not follow expected format, treating entire output as syntax.")
            return llm_output.strip()

    def _extract_text_content(self, content) -> str:
        """Extract text from message content, supporting multimodal formats"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)
        return str(content) if content else ""

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """Send status update event"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    def _generate_js_code(
        self,
        unique_id: str,
        chat_id: str,
        message_id: str,
        infographic_syntax: str,
        svg_width: int,
        export_format: str,
    ) -> str:
        """Generate JavaScript code for frontend SVG rendering"""
        
        # Escape the syntax for JS embedding
        syntax_escaped = (
            infographic_syntax
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
            .replace("</script>", "<\\/script>")
        )
        
        # Template mapping (same as infographic.py)
        template_mapping_js = """
        const TEMPLATE_MAPPING = {
            'list-grid': 'list-grid-compact-card',
            'list-vertical': 'list-column-simple-vertical-arrow',
            'tree-vertical': 'hierarchy-tree-tech-style-capsule-item',
            'tree-horizontal': 'hierarchy-tree-lr-tech-style-capsule-item',
            'mindmap': 'hierarchy-mindmap-branch-gradient-capsule-item',
            'sequence-roadmap': 'sequence-roadmap-vertical-simple',
            'sequence-zigzag': 'sequence-horizontal-zigzag-simple',
            'sequence-horizontal': 'sequence-horizontal-zigzag-simple',
            'relation-sankey': 'relation-sankey-simple',
            'relation-circle': 'relation-circle-icon-badge',
            'compare-binary': 'compare-binary-horizontal-simple-vs',
            'compare-swot': 'compare-swot',
            'quadrant-quarter': 'quadrant-quarter-simple-card',
            'statistic-card': 'list-grid-compact-card',
            'chart-bar': 'chart-bar-plain-text',
            'chart-column': 'chart-column-simple',
            'chart-line': 'chart-line-plain-text',
            'chart-area': 'chart-area-simple',
            'chart-pie': 'chart-pie-plain-text',
            'chart-doughnut': 'chart-pie-donut-plain-text'
        };
        """
        
        return f"""
(async function() {{
    const uniqueId = "{unique_id}";
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    const svgWidth = {svg_width};
    const exportFormat = "{export_format}";
    
    console.log("[Infographic Markdown] Starting render...");
    console.log("[Infographic Markdown] chatId:", chatId, "messageId:", messageId);
    
    try {{
        // Load AntV Infographic if not loaded
        if (typeof AntVInfographic === 'undefined') {{
            console.log("[Infographic Markdown] Loading AntV Infographic library...");
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://unpkg.com/@antv/infographic@latest/dist/infographic.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
            console.log("[Infographic Markdown] Library loaded.");
        }}
        
        const {{ Infographic }} = AntVInfographic;
        
        // Get infographic syntax
        let syntaxContent = `{syntax_escaped}`;
        console.log("[Infographic Markdown] Original syntax:", syntaxContent.substring(0, 200) + "...");
        
        // Clean up syntax
        const backtick = String.fromCharCode(96);
        const prefix = backtick + backtick + backtick + 'infographic';
        const simplePrefix = backtick + backtick + backtick;
        
        if (syntaxContent.toLowerCase().startsWith(prefix)) {{
            syntaxContent = syntaxContent.substring(prefix.length).trim();
        }} else if (syntaxContent.startsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(simplePrefix.length).trim();
        }}
        
        if (syntaxContent.endsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(0, syntaxContent.length - simplePrefix.length).trim();
        }}
        
        // Fix colons after keywords
        syntaxContent = syntaxContent.replace(/^(data|items|children|theme|config):/gm, '$1');
        syntaxContent = syntaxContent.replace(/(\\s)(children|items):/g, '$1$2');
        
        // Ensure infographic prefix
        if (!syntaxContent.trim().toLowerCase().startsWith('infographic')) {{
            syntaxContent = 'infographic list-grid\\n' + syntaxContent;
        }}
        
        // Apply template mapping
        {template_mapping_js}
        
        for (const [key, value] of Object.entries(TEMPLATE_MAPPING)) {{
            const regex = new RegExp(`infographic\\\\s+${{key}}(?=\\\\s|$)`, 'i');
            if (regex.test(syntaxContent)) {{
                console.log(`[Infographic Markdown] Auto-mapping: ${{key}} -> ${{value}}`);
                syntaxContent = syntaxContent.replace(regex, `infographic ${{value}}`);
                break;
            }}
        }}
        
        console.log("[Infographic Markdown] Cleaned syntax:", syntaxContent.substring(0, 200) + "...");
        
        // Create offscreen container
        const container = document.createElement('div');
        container.id = 'infographic-offscreen-' + uniqueId;
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:' + svgWidth + 'px;';
        document.body.appendChild(container);
        
        // Create and render infographic
        const instance = new Infographic({{
            container: '#' + container.id,
            width: svgWidth,
            padding: 24,
        }});
        
        console.log("[Infographic Markdown] Rendering infographic...");
        instance.render(syntaxContent);
        
        // Wait for render and export
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        let dataUrl;
        if (exportFormat === 'png') {{
            dataUrl = await instance.toDataURL({{ type: 'png', dpr: 2 }});
        }} else {{
            dataUrl = await instance.toDataURL({{ type: 'svg', embedResources: true }});
        }}
        
        console.log("[Infographic Markdown] Data URL generated, length:", dataUrl.length);
        
        // Cleanup
        instance.destroy();
        document.body.removeChild(container);
        
        // Generate markdown image
        const markdownImage = `![📊 AI 生成的信息图](${{dataUrl}})`;
        
        // Update message via API
        if (chatId && messageId) {{
            const token = localStorage.getItem("token");
            
            // Get current message content
            const getResponse = await fetch(`/api/v1/chats/${{chatId}}`, {{
                method: "GET",
                headers: {{ "Authorization": `Bearer ${{token}}` }}
            }});
            
            if (!getResponse.ok) {{
                throw new Error("Failed to get chat data: " + getResponse.status);
            }}
            
            const chatData = await getResponse.json();
            let originalContent = "";
            
            if (chatData.chat && chatData.chat.messages) {{
                const targetMsg = chatData.chat.messages.find(m => m.id === messageId);
                if (targetMsg && targetMsg.content) {{
                    originalContent = targetMsg.content;
                }}
            }}
            
            // Remove existing infographic images
            const infographicPattern = /\\n*!\\[📊[^\\]]*\\]\\(data:image\\/[^)]+\\)/g;
            let cleanedContent = originalContent.replace(infographicPattern, "");
            cleanedContent = cleanedContent.replace(/\\n{{3,}}/g, "\\n\\n").trim();
            
            // Append new image
            const newContent = cleanedContent + "\\n\\n" + markdownImage;
            
            // Update message
            const updateResponse = await fetch(`/api/v1/chats/${{chatId}}/messages/${{messageId}}/event`, {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${{token}}`
                }},
                body: JSON.stringify({{
                    type: "chat:message",
                    data: {{ content: newContent }}
                }})
            }});
            
            if (updateResponse.ok) {{
                console.log("[Infographic Markdown] ✅ Message updated successfully!");
            }} else {{
                console.error("[Infographic Markdown] API error:", updateResponse.status);
            }}
        }} else {{
            console.warn("[Infographic Markdown] ⚠️ Missing chatId or messageId");
        }}
        
    }} catch (error) {{
        console.error("[Infographic Markdown] Error:", error);
    }}
}})();
"""

    async def action(
        self,
        body: dict,
        __user__: dict = None,
        __event_emitter__=None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __metadata__: Optional[dict] = None,
        __request__: Request = None,
    ) -> dict:
        """
        Generate infographic using AntV and embed as Markdown image.
        """
        logger.info("Action: Infographic to Markdown started")

        # Get user information
        if isinstance(__user__, (list, tuple)):
            user_language = __user__[0].get("language", "en") if __user__ else "en"
            user_name = __user__[0].get("name", "User") if __user__[0] else "User"
            user_id = __user__[0].get("id", "unknown_user") if __user__ else "unknown_user"
        elif isinstance(__user__, dict):
            user_language = __user__.get("language", "en")
            user_name = __user__.get("name", "User")
            user_id = __user__.get("id", "unknown_user")
        else:
            user_language = "en"
            user_name = "User"
            user_id = "unknown_user"

        # Get current time
        now = datetime.now()
        current_date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("No messages available.")

            # Get recent messages
            message_count = min(self.valves.MESSAGE_COUNT, len(messages))
            recent_messages = messages[-message_count:]

            # Aggregate content
            aggregated_parts = []
            for msg in recent_messages:
                text_content = self._extract_text_content(msg.get("content"))
                if text_content:
                    aggregated_parts.append(text_content)

            if not aggregated_parts:
                raise ValueError("No text content found in messages.")

            long_text_content = "\n\n---\n\n".join(aggregated_parts)

            # Remove existing HTML blocks
            parts = re.split(r"```html.*?```", long_text_content, flags=re.DOTALL)
            clean_content = ""
            for part in reversed(parts):
                if part.strip():
                    clean_content = part.strip()
                    break

            if not clean_content:
                clean_content = long_text_content.strip()

            # Check minimum length
            if len(clean_content) < self.valves.MIN_TEXT_LENGTH:
                await self._emit_status(
                    __event_emitter__,
                    f"⚠️ 内容太短 ({len(clean_content)} 字符)，至少需要 {self.valves.MIN_TEXT_LENGTH} 字符",
                    True,
                )
                return body

            await self._emit_status(__event_emitter__, "📊 正在分析内容...", False)

            # Generate infographic syntax via LLM
            formatted_user_prompt = USER_PROMPT_GENERATE.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                user_language=user_language,
                long_text_content=clean_content,
            )

            target_model = self.valves.MODEL_ID or body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_INFOGRAPHIC},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "stream": False,
            }

            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"Unable to get user object: {user_id}")

            await self._emit_status(__event_emitter__, "📊 AI 正在生成信息图语法...", False)

            llm_response = await generate_chat_completion(__request__, llm_payload, user_obj)

            if not llm_response or "choices" not in llm_response or not llm_response["choices"]:
                raise ValueError("Invalid LLM response.")

            assistant_content = llm_response["choices"][0]["message"]["content"]
            infographic_syntax = self._extract_infographic_syntax(assistant_content)

            logger.info(f"Generated syntax: {infographic_syntax[:200]}...")

            # Extract IDs for API callback
            chat_id = self._extract_chat_id(body, __metadata__)
            message_id = self._extract_message_id(body, __metadata__)
            unique_id = f"ig_{int(time.time() * 1000)}"

            await self._emit_status(__event_emitter__, "📊 正在渲染 SVG...", False)

            # Execute JS to render and embed
            if __event_call__:
                js_code = self._generate_js_code(
                    unique_id=unique_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    infographic_syntax=infographic_syntax,
                    svg_width=self.valves.SVG_WIDTH,
                    export_format=self.valves.EXPORT_FORMAT,
                )

                await __event_call__(
                    {
                        "type": "execute",
                        "data": {"code": js_code},
                    }
                )

            await self._emit_status(__event_emitter__, "✅ 信息图生成完成！", True)
            logger.info("Infographic to Markdown completed")

        except Exception as e:
            error_message = f"Infographic generation failed: {str(e)}"
            logger.error(error_message, exc_info=True)
            await self._emit_status(__event_emitter__, f"❌ {error_message}", True)

        return body
