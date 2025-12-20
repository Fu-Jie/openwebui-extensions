"""
title: [插件名称] (例如: 智能思维导图)
author: [作者姓名]
author_url: [作者主页链接]
funding_url: [赞助链接]
version: 0.1.0
icon_url: [图标 URL 或 Data URI]
description: [简短描述插件的功能]
requirements: [依赖列表, 例如: jinja2, markdown]
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Callable, Awaitable
import logging
import re
import json
from fastapi import Request
from datetime import datetime
import pytz

# 导入 OpenWebUI 工具函数
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================================================================
# 常量与提示词 (Constants & Prompts)
# =================================================================

SYSTEM_PROMPT = """
[在此处插入系统提示词]
你是一个有用的助手...
请以 [JSON/Markdown] 格式输出...
"""

USER_PROMPT_TEMPLATE = """
[在此处插入用户提示词模板]
用户上下文:
姓名: {user_name}
时间: {current_date_time_str}

待处理内容:
{content}
"""

# 用于在聊天中渲染结果的 HTML 模板
HTML_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[插件标题]</title>
    <style>
        /* 在此处添加 CSS 样式 */
        body { font-family: sans-serif; padding: 20px; }
        .container { border: 1px solid #ccc; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>[结果标题]</h1>
        <div id="content">{result_content}</div>
    </div>
</body>
</html>
"""


class Action:
    class Valves(BaseModel):
        show_status: bool = Field(
            default=True,
            description="是否在聊天界面显示操作状态更新。",
        )
        LLM_MODEL_ID: str = Field(
            default="",
            description="用于处理的内置 LLM 模型 ID。如果为空，则使用当前对话的模型。",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="处理所需的最小文本长度（字符数）。",
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="是否在追加新结果前清除消息中已有的插件生成 HTML 内容 (通过标记识别)。",
        )
        # 根据需要添加其他配置字段
        # MAX_TEXT_LENGTH: int = Field(default=2000, description="...")

    def __init__(self):
        self.valves = self.Valves()

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """提取用户上下文信息。"""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", "unknown_user"),
            "user_name": user_data.get("name", "用户"),
            "user_language": user_data.get("language", "zh-CN"),
        }

    def _get_current_time_context(self) -> Dict[str, str]:
        """获取当前时间上下文。"""
        try:
            # 默认为特定时区或系统时间
            tz = pytz.timezone("Asia/Shanghai")  # 根据需要修改
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
        处理 LLM 的原始输出。
        重写此方法以解析 JSON、提取 Markdown 等。
        """
        # 示例: 提取 JSON
        # try:
        #     start = llm_output.find('{')
        #     end = llm_output.rfind('}') + 1
        #     if start != -1 and end != -1:
        #         return json.loads(llm_output[start:end])
        # except Exception:
        #     pass
        return llm_output.strip()

    def _remove_existing_html(self, content: str) -> str:
        """移除内容中已有的插件生成 HTML 代码块 (通过标记识别)。"""
        # 匹配 ```html <!-- OPENWEBUI_PLUGIN_OUTPUT --> ... ``` 模式
        # 使用 [\s\S]*? 非贪婪匹配任意字符
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        """发送状态更新事件。"""
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
        """发送通知事件 (info, success, warning, error)。"""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": type, "content": content}}
            )

    async def _emit_message(
        self, emitter: Optional[Callable[[Any], Awaitable[None]]], content: str
    ):
        """发送消息追加事件 (追加到当前消息)。"""
        if emitter:
            await emitter({"type": "message", "data": {"content": content}})

    async def _emit_replace(
        self, emitter: Optional[Callable[[Any], Awaitable[None]]], content: str
    ):
        """发送消息替换事件 (替换当前消息)。"""
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

        # 1. 上下文设置
        user_context = self._get_user_context(__user__)
        time_context = self._get_current_time_context()

        # 2. 输入验证
        messages = body.get("messages", [])
        if not messages or not messages[-1].get("content"):
            return body  # 或者处理错误

        original_content = messages[-1]["content"]

        if len(original_content) < self.valves.MIN_TEXT_LENGTH:
            warning_msg = f"文本过短 ({len(original_content)} 字符)。最少需要: {self.valves.MIN_TEXT_LENGTH}。"
            await self._emit_notification(__event_emitter__, warning_msg, "warning")
            return body  # 或者返回失败消息

        # 3. 状态通知 (开始)
        await self._emit_status(__event_emitter__, "正在处理...", done=False)

        try:
            # 4. 准备提示词
            formatted_prompt = USER_PROMPT_TEMPLATE.format(
                user_name=user_context["user_name"],
                current_date_time_str=time_context["current_date_time_str"],
                content=original_content,
                # 添加其他上下文变量
            )

            # 5. 确定模型
            target_model = self.valves.LLM_MODEL_ID
            if not target_model:
                target_model = body.get("model")
                # 注意: 这里没有硬编码的回退，依赖于系统/用户上下文

            # 6. 调用 LLM
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
                raise ValueError("无效的 LLM 响应")

            assistant_content = llm_response["choices"][0]["message"]["content"]

            # 7. 处理输出
            processed_data = self._process_llm_output(assistant_content)

            # 8. 生成 HTML/结果
            # 示例: 简单的字符串替换
            final_html = HTML_TEMPLATE.replace("{result_content}", str(processed_data))
            final_html = final_html.replace(
                "{user_language}", user_context["user_language"]
            )

            # 9. 注入结果
            if self.valves.CLEAR_PREVIOUS_HTML:
                body["messages"][-1]["content"] = self._remove_existing_html(
                    body["messages"][-1]["content"]
                )

            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] += f"\n\n{html_embed_tag}"

            # 10. 状态通知 (成功)
            await self._emit_status(__event_emitter__, "处理完成！", done=True)
            await self._emit_notification(
                __event_emitter__, "操作成功完成。", "success"
            )

        except Exception as e:
            logger.error(f"Action failed: {e}", exc_info=True)
            error_msg = f"错误: {str(e)}"

            # 将错误附加到聊天中 (可选)
            body["messages"][-1]["content"] += f"\n\n❌ **错误**: {error_msg}"

            await self._emit_status(__event_emitter__, "处理失败。", done=True)
            await self._emit_notification(
                __event_emitter__, "操作失败，请检查日志。", "error"
            )

        return body
