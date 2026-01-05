"""
title: JS Render PoC
author: Fu-Jie
version: 0.6.0
description: Proof of concept for JS rendering + API write-back pattern. JS renders SVG and updates message via API.
"""

import time
import json
import logging
from typing import Optional, Callable, Awaitable, Any
from pydantic import BaseModel, Field
from fastapi import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Action:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def _extract_chat_id(self, body: dict, metadata: Optional[dict]) -> str:
        """Extract chat_id from body or metadata"""
        if isinstance(body, dict):
            # body["chat_id"] 是 chat_id
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
            # body["id"] 是 message_id
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
        PoC: Use __event_call__ to execute JS that renders SVG and updates message via API.
        """
        # 准备调试数据
        body_for_log = {}
        for k, v in body.items():
            if k == "messages":
                body_for_log[k] = f"[{len(v)} messages]"
            else:
                body_for_log[k] = v

        body_json = json.dumps(body_for_log, ensure_ascii=False, default=str)
        metadata_json = (
            json.dumps(__metadata__, ensure_ascii=False, default=str)
            if __metadata__
            else "null"
        )

        # 转义 JSON 中的特殊字符以便嵌入 JS
        body_json_escaped = (
            body_json.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        )
        metadata_json_escaped = (
            metadata_json.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
        )

        chat_id = self._extract_chat_id(body, __metadata__)
        message_id = self._extract_message_id(body, __metadata__)

        unique_id = f"poc_{int(time.time() * 1000)}"

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "🔄 正在渲染...", "done": False},
                }
            )

        if __event_call__:
            await __event_call__(
                {
                    "type": "execute",
                    "data": {
                        "code": f"""
(async function() {{
    const uniqueId = "{unique_id}";
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    
    // ===== DEBUG: 输出 Python 端的数据 =====
    console.log("[JS Render PoC] ===== DEBUG INFO (from Python) =====");
    console.log("[JS Render PoC] body:", `{body_json_escaped}`);
    console.log("[JS Render PoC] __metadata__:", `{metadata_json_escaped}`);
    console.log("[JS Render PoC] Extracted: chatId=", chatId, "messageId=", messageId);
    console.log("[JS Render PoC] =========================================");
    
    try {{
        console.log("[JS Render PoC] Starting SVG render...");
        
        // Create SVG
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "200");
        svg.setAttribute("height", "200");
        svg.setAttribute("viewBox", "0 0 200 200");
        svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        
        const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        const gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
        gradient.setAttribute("id", "grad-" + uniqueId);
        gradient.innerHTML = `
            <stop offset="0%" style="stop-color:#1e88e5;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#43a047;stop-opacity:1" />
        `;
        defs.appendChild(gradient);
        svg.appendChild(defs);
        
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", "100");
        circle.setAttribute("cy", "100");
        circle.setAttribute("r", "80");
        circle.setAttribute("fill", `url(#grad-${{uniqueId}})`);
        svg.appendChild(circle);
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", "100");
        text.setAttribute("y", "105");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("fill", "white");
        text.setAttribute("font-size", "16");
        text.setAttribute("font-weight", "bold");
        text.textContent = "PoC Success!";
        svg.appendChild(text);
        
        // Convert to Base64 Data URI
        const svgData = new XMLSerializer().serializeToString(svg);
        const base64 = btoa(unescape(encodeURIComponent(svgData)));
        const dataUri = "data:image/svg+xml;base64," + base64;
        
        console.log("[JS Render PoC] SVG rendered, data URI length:", dataUri.length);
        
        // Call API - 完全替换方案（更稳定）
        if (chatId && messageId) {{
            const token = localStorage.getItem("token");
            
            // 1. 获取当前消息内容
            const getResponse = await fetch(`/api/v1/chats/${{chatId}}`, {{
                method: "GET",
                headers: {{ "Authorization": `Bearer ${{token}}` }}
            }});
            
            if (!getResponse.ok) {{
                throw new Error("Failed to get chat data: " + getResponse.status);
            }}
            
            const chatData = await getResponse.json();
            console.log("[JS Render PoC] Got chat data");
            
            let originalContent = "";
            if (chatData.chat && chatData.chat.messages) {{
                const targetMsg = chatData.chat.messages.find(m => m.id === messageId);
                if (targetMsg && targetMsg.content) {{
                    originalContent = targetMsg.content;
                    console.log("[JS Render PoC] Found original content, length:", originalContent.length);
                }}
            }}
            
            // 2. 移除已存在的 PoC 图片（如果有的话）
            // 匹配 ![JS Render PoC 生成的 SVG](data:...) 格式
            const pocImagePattern = /\\n*!\\[JS Render PoC[^\\]]*\\]\\(data:image\\/svg\\+xml;base64,[^)]+\\)/g;
            let cleanedContent = originalContent.replace(pocImagePattern, "");
            // 移除可能残留的多余空行
            cleanedContent = cleanedContent.replace(/\\n{{3,}}/g, "\\n\\n").trim();
            
            if (cleanedContent !== originalContent) {{
                console.log("[JS Render PoC] Removed existing PoC image(s)");
            }}
            
            // 3. 添加新的 Markdown 图片
            const markdownImage = `![JS Render PoC 生成的 SVG](${{dataUri}})`;
            const newContent = cleanedContent + "\\n\\n" + markdownImage;
            
            // 3. 使用 chat:message 完全替换
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
                console.log("[JS Render PoC] ✅ Message updated successfully!");
            }} else {{
                console.error("[JS Render PoC] API error:", updateResponse.status, await updateResponse.text());
            }}
        }} else {{
            console.warn("[JS Render PoC] ⚠️ Missing chatId or messageId, cannot persist.");
        }}
        
    }} catch (error) {{
        console.error("[JS Render PoC] Error:", error);
    }}
}})();
                        """
                    },
                }
            )

        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": "✅ 渲染完成", "done": True}}
            )

        return body
