"""
title: 精读 (Deep Reading)
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNDI4NWY0Ii8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMWU4OGU1Ii8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHBhdGggZD0iTTYgMmg4bDYgNnYxMmEyIDIgMCAwIDEtMiAySDZhMiAyIDAgMCAxLTItMlY0YTIgMiAwIDAgMSAyLTJ6IiBmaWxsPSJ1cmwoI2cpIi8+PHBhdGggZD0iTTE0IDJsNiA2aC02eiIgZmlsbD0iIzFlODhlNSIgb3BhY2l0eT0iMC42Ii8+PGxpbmUgeDE9IjgiIHkxPSIxMyIgeDI9IjE2IiB5Mj0iMTMiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48bGluZSB4MT0iOCIgeTE9IjE3IiB4Mj0iMTQiIHkyPSIxNyIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEuNSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTgiIHI9IjMiIGZpbGw9IiNmZmQ3MDAiLz48cGF0aCBkPSJNMTYgMTZsMS41IDEuNSIgc3Ryb2tlPSIjNDI4NWY0IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==
version: 2.0.0
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

HTML_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{{ user_language }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>精读:深度分析报告</title>
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
            <h1>📖 精读：深度分析报告</h1>
        </div>
        <div class="user-context">
            <span><strong>用户:</strong> {{ user_name }}</span>
            <span><strong>分析时间:</strong> {{ current_date_time_str }}</span>
            <span><strong>星期:</strong> {{ current_weekday }}</span>
        </div>
        <div class="content">
            <div class="section summary-section">
                <h2><span class="icon">📝</span>详细摘要</h2>
                <div class="html-content">{{ summary_html | safe }}</div>
            </div>
            <div class="section keypoints-section">
                <h2><span class="icon">💡</span>关键信息点</h2>
                <div class="html-content">{{ keypoints_html | safe }}</div>
            </div>
            <div class="section actions-section">
                <h2><span class="icon">🎯</span>行动建议</h2>
                <div class="html-content">{{ actions_html | safe }}</div>
            </div>
        </div>
        <div class="footer">
            <p>&copy; {{ current_year }} 精读 - 深度文本分析服务</p>
        </div>
    </div>
</body>
</html>"""


class Action:
    class Valves(BaseModel):
        show_status: bool = Field(
            default=True, description="是否在聊天界面显示操作状态更新。"
        )
        LLM_MODEL_ID: str = Field(
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
            description="是否在追加新结果前清除消息中已有的插件生成 HTML 内容 (通过标记识别)。",
        )

    def __init__(self):
        self.valves = self.Valves()

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

    def _remove_existing_html(self, content: str) -> str:
        """移除内容中已有的插件生成 HTML 代码块 (通过标记识别)。"""
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _build_html(self, context: dict) -> str:
        """
        使用 Jinja2 模板和上下文数据构建最终的HTML内容。
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
        current_date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        current_weekday = now.strftime("%A")
        current_year = now.strftime("%Y")
        current_timezone_str = "未知时区"

        original_content = ""
        try:
            messages = body.get("messages", [])
            if not messages or not messages[-1].get("content"):
                raise ValueError("无法获取有效的用户消息内容。")

            original_content = messages[-1]["content"]

            if len(original_content) < self.valves.MIN_TEXT_LENGTH:
                short_text_message = f"文本内容过短({len(original_content)}字符)，建议至少{self.valves.MIN_TEXT_LENGTH}字符以获得有效的深度分析。\n\n💡 提示：对于短文本，建议使用'⚡ 闪记卡'进行快速提炼。"
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
                                "content": f"文本长度为{len(original_content)}字符。建议{self.valves.RECOMMENDED_MIN_LENGTH}字符以上可获得更好的分析效果。",
                            },
                        }
                    )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "info",
                            "content": "📖 精读已启动，正在进行深度分析...",
                        },
                    }
                )
                if self.valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "📖 精读: 深入分析文本，提炼精华...",
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

            # 确定使用的模型
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

            final_html_content = self._build_html(context)

            if self.valves.CLEAR_PREVIOUS_HTML:
                original_content = self._remove_existing_html(original_content)

            html_embed_tag = f"```html\n{final_html_content}\n```"
            body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"

            if self.valves.show_status and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "📖 精读: 分析完成!", "done": True},
                    }
                )
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "success",
                            "content": f"📖 精读完成，{user_name}！深度分析报告已生成。",
                        },
                    }
                )

        except Exception as e:
            error_message = f"精读处理失败: {str(e)}"
            logger.error(f"精读错误: {error_message}", exc_info=True)
            user_facing_error = f"抱歉, 精读在处理时遇到错误: {str(e)}。\n请检查Open WebUI后端日志获取更多详情。"
            body["messages"][-1][
                "content"
            ] = f"{original_content}\n\n❌ **错误:** {user_facing_error}"

            if __event_emitter__:
                if self.valves.show_status:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "精读: 处理失败。",
                                "done": True,
                            },
                        }
                    )
                await __event_emitter__(
                    {
                        "type": "notification",
                        "data": {
                            "type": "error",
                            "content": f"精读处理失败, {user_name}!",
                        },
                    }
                )

        return body
