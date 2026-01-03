"""
title: 精读 (Deep Reading)
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNDI4NWY0Ii8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMWU4OGU1Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHBhdGggZD0iTTYgMmg4bDYgNnYxMmEyIDIgMCAwIDEtMiAySDZhMiAyIDAgMCAxLTItMlY0YTIgMiAwIDAgMSAyLTJ6IiBmaWxsPSJ1cmwoI2cpIi8+PHBhdGggZD0iTTE0IDJsNiA2aC02eiIgZmlsbD0iIzFlODhlNSIgb3BhY2l0eT0iMC42Ii8+PGxpbmUgeDE9IjgiIHkxPSIxMyIgeDI9IjE2IiB5Mj0iMTMiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48bGluZSB4MT0iOCIgeTE9IjE3IiB4Mj0iMTQiIHkyPSIxNyIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTgiIHI9IjMiIGZpbGw9IiNmZmQ3MDAiLz48cGF0aCBkPSJNMTYgMTZsMS41IDEuNSIgc3Ryb2tlPSIjNDI4NWY0IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==
version: 0.1.1
description: 深度分析长篇文本，提炼详细摘要、关键信息点和可执行的行动建议，适合工作和学习场景。
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
# HTML 容器模板 (支持多插件共存与网格布局)
# =================================================================
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
            flex: 1 1 400px; /* 默认宽度，允许伸缩 */
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

# =================================================================
# 内部 LLM 提示词设计
# =================================================================

SYSTEM_PROMPT_READING_ASSISTANT = """
你是一个专业的深度文本分析专家，擅长精读长篇文本并提炼精华。你的任务是进行全面、深入的分析。

请提供以下内容：
1.  **详细摘要**：用 2-3 段话全面总结文本的核心内容，确保准确性和完整性。不要过于简略，要让读者充分理解文本主旨。
2.  **关键信息点**：列出 5-8 个最重要的事实、观点或论据。每个信息点应该：
    - 具体且有深度
    - 包含必要的细节和背景
    - 使用 Markdown 列表格式
3.  **行动建议**：从文本中识别并提炼出具体的、可执行的行动项。每个建议应该：
    - 明确且可操作
    - 包含执行的优先级或时间建议
    - 如果没有明确的行动项，可以提供学习建议或思考方向

请严格遵循以下指导原则：
-   **语言**：所有输出必须使用用户指定的语言。
-   **格式**：请严格按照以下 Markdown 格式输出，确保每个部分都有明确的标题：
    ## 摘要
    [这里是详细的摘要内容，2-3段话，可以使用 Markdown 进行**加粗**或*斜体*强调重点]

    ## 关键信息点
    - [关键点1：包含具体细节和背景]
    - [关键点2：包含具体细节和背景]
    - [关键点3：包含具体细节和背景]
    - [至少5个，最多8个关键点]

    ## 行动建议
    - [行动项1：具体、可执行，包含优先级]
    - [行动项2：具体、可执行，包含优先级]
    - [如果没有明确行动项，提供学习建议或思考方向]
-   **深度优先**：分析要深入、全面，不要浮于表面。
-   **行动导向**：重点关注可执行的建议和下一步行动。
-   **只输出分析结果**：不要包含任何额外的寒暄、解释或引导性文字。
"""

USER_PROMPT_GENERATE_SUMMARY = """
请对以下长篇文本进行深度分析，提供：
1.  详细的摘要（2-3段话，全面概括文本内容）
2.  关键信息点列表（5-8个，包含具体细节）
3.  可执行的行动建议（具体、明确，包含优先级）

---
**用户上下文信息:**
用户姓名: {user_name}
当前日期时间: {current_date_time_str}
当前星期: {current_weekday}
当前时区: {current_timezone_str}
用户语言: {user_language}
---

**长篇文本内容:**
```
{long_text_content}
```

请进行深入、全面的分析，重点关注可执行的行动建议。
"""

# =================================================================
# 前端 HTML 模板 (Jinja2 语法)
# =================================================================

CSS_TEMPLATE_SUMMARY = """
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
        .summary-container-wrapper {
            font-family: var(--font-family);
            line-height: 1.8;
            color: var(--text-color);
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .summary-container-wrapper .header {
            background: var(--header-gradient);
            color: white;
            padding: 20px 24px;
            text-align: center;
        }
        .summary-container-wrapper .header h1 {
            margin: 0;
            font-size: 1.5em;
            font-weight: 500;
            letter-spacing: -0.5px;
        }
        .summary-container-wrapper .user-context {
            font-size: 0.8em;
            color: var(--muted-text-color);
            background-color: #f1f3f4;
            padding: 8px 16px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
        }
        .summary-container-wrapper .user-context span { margin: 2px 8px; }
        .summary-container-wrapper .content { padding: 20px; flex-grow: 1; }
        .summary-container-wrapper .section {
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e8eaed;
        }
        .summary-container-wrapper .section:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .summary-container-wrapper .section h2 {
            margin-top: 0;
            margin-bottom: 12px;
            font-size: 1.2em;
            font-weight: 500;
            color: var(--text-color);
            display: flex;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--primary-color);
        }
        .summary-container-wrapper .section h2 .icon {
            margin-right: 8px;
            font-size: 1.1em;
            line-height: 1;
        }
        .summary-container-wrapper .summary-section h2 { border-bottom-color: var(--primary-color); }
        .summary-container-wrapper .keypoints-section h2 { border-bottom-color: var(--secondary-color); }
        .summary-container-wrapper .actions-section h2 { border-bottom-color: var(--action-color); }
        .summary-container-wrapper .html-content {
            font-size: 0.95em;
            line-height: 1.7;
        }
        .summary-container-wrapper .html-content p:first-child { margin-top: 0; }
        .summary-container-wrapper .html-content p:last-child { margin-bottom: 0; }
        .summary-container-wrapper .html-content ul {
            list-style: none;
            padding-left: 0;
            margin: 12px 0;
        }
        .summary-container-wrapper .html-content li {
            padding: 8px 0 8px 24px;
            position: relative;
            margin-bottom: 6px;
            line-height: 1.6;
        }
        .summary-container-wrapper .html-content li::before {
            position: absolute;
            left: 0;
            top: 8px;
            font-family: 'Arial';
            font-weight: bold;
            font-size: 1em;
        }
        .summary-container-wrapper .keypoints-section .html-content li::before { 
            content: '•'; 
            color: var(--secondary-color);
            font-size: 1.3em;
            top: 5px;
        }
        .summary-container-wrapper .actions-section .html-content li::before { 
            content: '▸'; 
            color: var(--action-color); 
        }
        .summary-container-wrapper .no-content { 
            color: var(--muted-text-color); 
            font-style: italic;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .summary-container-wrapper .footer {
            text-align: center;
            padding: 16px;
            font-size: 0.8em;
            color: #5f6368;
            background-color: #f8f9fa;
            border-top: 1px solid var(--border-color);
        }
"""

CONTENT_TEMPLATE_SUMMARY = """
        <div class="summary-container-wrapper">
            <div class="header">
                <h1>📖 精读：深度分析报告</h1>
            </div>
            <div class="user-context">
                <span><strong>用户:</strong> {user_name}</span>
                <span><strong>时间:</strong> {current_date_time_str}</span>
            </div>
            <div class="content">
                <div class="section summary-section">
                    <h2><span class="icon">📝</span>详细摘要</h2>
                    <div class="html-content">{summary_html}</div>
                </div>
                <div class="section keypoints-section">
                    <h2><span class="icon">💡</span>关键信息点</h2>
                    <div class="html-content">{keypoints_html}</div>
                </div>
                <div class="section actions-section">
                    <h2><span class="icon">🎯</span>行动建议</h2>
                    <div class="html-content">{actions_html}</div>
                </div>
            </div>
            <div class="footer">
                <p>&copy; {current_year} 精读 - 深度文本分析服务</p>
            </div>
        </div>
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True, description="是否在聊天界面显示操作状态更新。"
        )
        MODEL_ID: str = Field(
            default="",
            description="用于文本分析的内置LLM模型ID。如果为空，则使用当前对话的模型。",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=200,
            description="进行深度分析所需的最小文本长度(字符数)。建议200字符以上。",
        )
        RECOMMENDED_MIN_LENGTH: int = Field(
            default=500, description="建议的最小文本长度，以获得最佳分析效果。"
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="是否强制清除旧的插件结果（如果为 True，则不合并，直接覆盖）。",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="用于生成的最近消息数量。设置为1仅使用最后一条消息，更大值可包含更多上下文。",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.weekday_map = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日",
        }

    def _process_llm_output(self, llm_output: str) -> Dict[str, str]:
        """
        解析LLM的Markdown输出,将其转换为HTML片段。
        """
        summary_match = re.search(
            r"##\s*摘要\s*\n(.*?)(?=\n##|$)", llm_output, re.DOTALL
        )
        keypoints_match = re.search(
            r"##\s*关键信息点\s*\n(.*?)(?=\n##|$)", llm_output, re.DOTALL
        )
        actions_match = re.search(
            r"##\s*行动建议\s*\n(.*?)(?=\n##|$)", llm_output, re.DOTALL
        )

        summary_md = summary_match.group(1).strip() if summary_match else ""
        keypoints_md = keypoints_match.group(1).strip() if keypoints_match else ""
        actions_md = actions_match.group(1).strip() if actions_match else ""

        if not any([summary_md, keypoints_md, actions_md]):
            summary_md = llm_output.strip()
            logger.warning("LLM输出未遵循预期的Markdown格式。将整个输出视为摘要。")

        # 使用 'nl2br' 扩展将换行符 \n 转换为 <br>
        md_extensions = ["nl2br"]
        summary_html = (
            markdown.markdown(summary_md, extensions=md_extensions)
            if summary_md
            else '<p class="no-content">未能提取摘要信息。</p>'
        )
        keypoints_html = (
            markdown.markdown(keypoints_md, extensions=md_extensions)
            if keypoints_md
            else '<p class="no-content">未能提取关键信息点。</p>'
        )
        actions_html = (
            markdown.markdown(actions_md, extensions=md_extensions)
            if actions_md
            else '<p class="no-content">暂无明确的行动建议。</p>'
        )

        return {
            "summary_html": summary_html,
            "keypoints_html": keypoints_html,
            "actions_html": actions_html,
        }

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """发送状态更新事件。"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        """发送通知事件 (info/success/warning/error)。"""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    def _remove_existing_html(self, content: str) -> str:
        """移除内容中已有的插件生成 HTML 代码块 (通过标记识别)。"""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _extract_text_content(self, content) -> str:
        """从消息内容中提取文本，支持多模态消息格式"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # 多模态消息: [{"type": "text", "text": "..."}, {"type": "image_url", ...}]
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
        user_language: str = "zh-CN",
    ) -> str:
        """
        将新内容合并到现有的 HTML 容器中，或者创建一个新的容器。
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

    def _build_content_html(self, context: dict) -> str:
        """
        使用上下文数据构建内容 HTML。
        """
        return (
            CONTENT_TEMPLATE_SUMMARY.replace(
                "{user_name}", context.get("user_name", "用户")
            )
            .replace(
                "{current_date_time_str}", context.get("current_date_time_str", "")
            )
            .replace("{current_year}", context.get("current_year", ""))
            .replace("{summary_html}", context.get("summary_html", ""))
            .replace("{keypoints_html}", context.get("keypoints_html", ""))
            .replace("{actions_html}", context.get("actions_html", ""))
        )

    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Any] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info("Action: 精读启动 (v2.0.0 - Deep Reading)")

        if isinstance(__user__, (list, tuple)):
            user_language = (
                __user__[0].get("language", "zh-CN") if __user__ else "zh-CN"
            )
            user_name = __user__[0].get("name", "用户") if __user__[0] else "用户"
            user_id = (
                __user__[0]["id"]
                if __user__ and "id" in __user__[0]
                else "unknown_user"
            )
        elif isinstance(__user__, dict):
            user_language = __user__.get("language", "zh-CN")
            user_name = __user__.get("name", "用户")
            user_id = __user__.get("id", "unknown_user")

        now = datetime.now()
        current_date_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
        current_weekday_en = now.strftime("%A")
        current_weekday = self.weekday_map.get(current_weekday_en, current_weekday_en)
        current_year = now.strftime("%Y")
        current_timezone_str = "未知时区"

        original_content = ""
        try:
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("无法获取有效的用户消息内容。")

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
                        "用户"
                        if role == "user"
                        else "助手" if role == "assistant" else role
                    )
                    aggregated_parts.append(f"[{role_label} 消息 {i}]\n{text_content}")

            if not aggregated_parts:
                raise ValueError("无法获取有效的用户消息内容。")

            original_content = "\n\n---\n\n".join(aggregated_parts)

            if len(original_content) < self.valves.MIN_TEXT_LENGTH:
                short_text_message = f"文本内容过短({len(original_content)}字符)，建议至少{self.valves.MIN_TEXT_LENGTH}字符以获得有效的深度分析。\n\n💡 提示：对于短文本，建议使用'⚡ 闪记卡'进行快速提炼。"
                await self._emit_notification(
                    __event_emitter__, short_text_message, "warning"
                )
                return {
                    "messages": [
                        {"role": "assistant", "content": f"⚠️ {short_text_message}"}
                    ]
                }

            # Recommend for longer texts
            if len(original_content) < self.valves.RECOMMENDED_MIN_LENGTH:
                await self._emit_notification(
                    __event_emitter__,
                    f"文本长度为{len(original_content)}字符。建议{self.valves.RECOMMENDED_MIN_LENGTH}字符以上可获得更好的分析效果。",
                    "info",
                )

            await self._emit_notification(
                __event_emitter__, "📖 精读已启动，正在进行深度分析...", "info"
            )
            await self._emit_status(
                __event_emitter__, "📖 精读: 深入分析文本，提炼精华...", False
            )

            formatted_user_prompt = USER_PROMPT_GENERATE_SUMMARY.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                current_weekday=current_weekday,
                current_timezone_str=current_timezone_str,
                user_language=user_language,
                long_text_content=original_content,
            )

            # 确定使用的模型
            target_model = self.valves.MODEL_ID
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
                raise ValueError(f"无法获取用户对象, 用户ID: {user_id}")

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

            content_html = self._build_content_html(context)

            # Extract existing HTML if any
            existing_html_block = ""
            match = re.search(
                r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
                original_content,
            )
            if match:
                existing_html_block = match.group(1)

            if self.valves.CLEAR_PREVIOUS_HTML:
                original_content = self._remove_existing_html(original_content)
                final_html = self._merge_html(
                    "", content_html, CSS_TEMPLATE_SUMMARY, "", user_language
                )
            else:
                if existing_html_block:
                    original_content = self._remove_existing_html(original_content)
                    final_html = self._merge_html(
                        existing_html_block,
                        content_html,
                        CSS_TEMPLATE_SUMMARY,
                        "",
                        user_language,
                    )
                else:
                    final_html = self._merge_html(
                        "", content_html, CSS_TEMPLATE_SUMMARY, "", user_language
                    )

            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"

            await self._emit_status(__event_emitter__, "📖 精读: 分析完成!", True)
            await self._emit_notification(
                __event_emitter__,
                f"📖 精读完成，{user_name}！深度分析报告已生成。",
                "success",
            )

        except Exception as e:
            error_message = f"精读处理失败: {str(e)}"
            logger.error(f"精读错误: {error_message}", exc_info=True)
            user_facing_error = f"抱歉, 精读在处理时遇到错误: {str(e)}。\n请检查Open WebUI后端日志获取更多详情。"
            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n❌ **错误:** {user_facing_error}"

            await self._emit_status(__event_emitter__, "精读: 处理失败。", True)
            await self._emit_notification(
                __event_emitter__, f"精读处理失败, {user_name}!", "error"
            )

        return body
