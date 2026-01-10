"""
title: Context & Model Enhancement Filter
version: 0.3

description:
    一个专注于增强请求上下文和优化模型功能的 Filter 插件。提供三大核心功能：

    1. 环境变量注入：在每条用户消息前自动注入用户环境变量（用户名、时间、时区、语言等）
       - 支持纯文本、图片、多模态消息
       - 幂等性设计，避免重复注入
       - 注入成功时发送前端状态提示

    2. Web Search 功能改进：为特定模型优化 Web 搜索功能
       - 为阿里云通义千问系列、DeepSeek、Gemini 等模型添加搜索能力
       - 自动识别模型并追加 "-search" 后缀
       - 管理功能开关，防止冲突
       - 启用时发送搜索能力状态提示

    3. 模型适配与上下文注入：为特定模型注入 chat_id 等上下文信息
       - 支持 cfchatqwen、webgemini 等模型的特殊处理
       - 动态模型重定向
       - 智能化的模型识别和适配

features:
    - 自动化环境变量管理
    - 智能模型功能适配
    - 异步状态反馈
    - 幂等性保证
    - 多模型支持
"""

from pydantic import BaseModel, Field
from typing import Optional
import re
import logging
import asyncio


# 配置日志
logger = logging.getLogger(__name__)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )

    def __init__(self):
        # Indicates custom file handling logic. This flag helps disengage default routines in favor of custom
        # implementations, informing the WebUI to defer file-related operations to designated methods within this class.
        # Alternatively, you can remove the files directly from the body in from the inlet hook
        # self.file_handler = True

        # Initialize 'valves' with specific configurations. Using 'Valves' instance helps encapsulate settings,
        # which ensures settings are managed cohesively and not confused with operational flags like 'file_handler'.
        self.valves = self.Valves()
        pass

    def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __event_emitter__=None,
    ) -> dict:
        # Modify the request body or validate it before processing by the chat completion API.
        # This function is the pre-processor for the API where various checks on the input can be performed.
        # It can also modify the request before sending it to the API.
        messages = body.get("messages", [])
        self.insert_user_env_info(__metadata__, messages, __event_emitter__)
        # if "测试系统提示词" in str(messages):
        #     messages.insert(0, {"role": "system", "content": "你是一个大数学家"})
        #     print("XXXXX" * 100)
        #     print(body)
        self.change_web_search(body, __user__, __event_emitter__)
        body = self.inlet_chat_id(__model__, __metadata__, body)

        return body

    def inlet_chat_id(self, model: dict, metadata: dict, body: dict):
        if "openai" in model:
            base_model_id = model["openai"]["id"]

        else:
            base_model_id = model["info"]["base_model_id"]

        base_model = model["id"] if base_model_id is None else base_model_id
        if base_model.startswith("cfchatqwen"):
            # pass
            body["chat_id"] = metadata["chat_id"]

        if base_model.startswith("webgemini"):
            body["chat_id"] = metadata["chat_id"]
            if not model["id"].startswith("webgemini"):
                body["custom_model_id"] = model["id"]

        # print("我是 body *******************", body)
        return body

    def change_web_search(self, body, __user__, __event_emitter__=None):
        """
        优化特定模型的 Web 搜索功能。

        功能：
        - 检测是否启用了 Web 搜索
        - 为支持搜索的模型启用模型本身的搜索能力
        - 禁用默认的 web_search 开关以避免冲突
        - 当使用模型本身的搜索能力时发送状态提示

        参数：
            body: 请求体字典
            __user__: 用户信息
            __event_emitter__: 用于发送前端事件的发射器函数
        """
        features = body.get("features", {})
        web_search_enabled = (
            features.get("web_search", False) if isinstance(features, dict) else False
        )
        if isinstance(__user__, (list, tuple)):
            user_email = __user__[0].get("email", "用户") if __user__[0] else "用户"
        elif isinstance(__user__, dict):
            user_email = __user__.get("email", "用户")
        model_name = body.get("model")

        search_enabled_for_model = False
        if web_search_enabled:
            if model_name in ["qwen-max-latest", "qwen-max", "qwen-plus-latest"]:
                body.setdefault("enable_search", True)
                features["web_search"] = False
                search_enabled_for_model = True
            if "search" in model_name or "搜索" in model_name:
                features["web_search"] = False
            if model_name.startswith("cfdeepseek-deepseek") and not model_name.endswith(
                "search"
            ):
                body["model"] = body["model"] + "-search"
                features["web_search"] = False
                search_enabled_for_model = True
            if model_name.startswith("cfchatqwen") and not model_name.endswith(
                "search"
            ):
                body["model"] = body["model"] + "-search"
                features["web_search"] = False
                search_enabled_for_model = True
            if model_name.startswith("gemini-2.5") and "search" not in model_name:
                body["model"] = body["model"] + "-search"
                features["web_search"] = False
                search_enabled_for_model = True

        # 如果启用了模型本身的搜索能力，发送状态提示
        if search_enabled_for_model and __event_emitter__:
            try:
                asyncio.create_task(
                    self._emit_search_status(__event_emitter__, model_name)
                )
            except RuntimeError:
                pass

    def insert_user_env_info(
        self, __metadata__, messages, __event_emitter__=None, model_match_tags=None
    ):
        """
        在第一条用户消息中注入环境变量信息。

        功能特性：
        - 始终在用户消息内容前注入环境变量的 Markdown 说明
        - 支持多种消息类型：纯文本、图片、图文混合消息
        - 幂等性设计：若环境变量信息已存在则更新为最新数据，不会重复添加
        - 注入成功后通过事件发射器向前端发送"注入成功"的状态提示

        参数：
            __metadata__: 包含环境变量的元数据字典
            messages: 消息列表
            __event_emitter__: 用于发送前端事件的发射器函数
            model_match_tags: 模型匹配标签（保留参数，当前未使用）
        """
        variables = __metadata__.get("variables", {})
        if not messages or messages[0]["role"] != "user":
            return

        env_injected = False
        if variables:
            # 构建环境变量的Markdown文本
            variable_markdown = (
                "## 用户环境变量\n"
                "以下信息为用户的环境变量，可用于为用户提供更个性化的服务或满足特定需求时作为参考：\n"
                f"- **用户姓名**：{variables.get('{{USER_NAME}}', '')}\n"
                f"- **当前日期时间**：{variables.get('{{CURRENT_DATETIME}}', '')}\n"
                f"- **当前星期**：{variables.get('{{CURRENT_WEEKDAY}}', '')}\n"
                f"- **当前时区**：{variables.get('{{CURRENT_TIMEZONE}}', '')}\n"
                f"- **用户语言**：{variables.get('{{USER_LANGUAGE}}', '')}\n"
            )

            content = messages[0]["content"]
            # 环境变量部分的匹配模式
            env_var_pattern = r"(## 用户环境变量\n以下信息为用户的环境变量，可用于为用户提供更个性化的服务或满足特定需求时作为参考：\n.*?用户语言.*?\n)"
            # 处理不同内容类型
            if isinstance(content, list):  # 多模态内容(可能包含图片和文本)
                # 查找第一个文本类型的内容
                text_index = -1
                for i, part in enumerate(content):
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_index = i
                        break

                if text_index >= 0:
                    # 存在文本内容，检查是否已存在环境变量信息
                    text_part = content[text_index]
                    text_content = text_part.get("text", "")

                    if re.search(env_var_pattern, text_content, flags=re.DOTALL):
                        # 已存在环境变量信息，更新为最新数据
                        text_part["text"] = re.sub(
                            env_var_pattern,
                            variable_markdown,
                            text_content,
                            flags=re.DOTALL,
                        )
                    else:
                        # 不存在环境变量信息，添加到开头
                        text_part["text"] = f"{variable_markdown}\n{text_content}"

                    content[text_index] = text_part
                else:
                    # 没有文本内容(例如只有图片)，添加新的文本项
                    content.insert(
                        0, {"type": "text", "text": f"{variable_markdown}\n"}
                    )

                messages[0]["content"] = content

            elif isinstance(content, str):  # 纯文本内容
                # 检查是否已存在环境变量信息
                if re.search(env_var_pattern, content, flags=re.DOTALL):
                    # 已存在，更新为最新数据
                    messages[0]["content"] = re.sub(
                        env_var_pattern, variable_markdown, content, flags=re.DOTALL
                    )
                else:
                    # 不存在，添加到开头
                    messages[0]["content"] = f"{variable_markdown}\n{content}"
                env_injected = True

            else:  # 其他类型内容
                # 转换为字符串并处理
                str_content = str(content)
                # 检查是否已存在环境变量信息
                if re.search(env_var_pattern, str_content, flags=re.DOTALL):
                    # 已存在，更新为最新数据
                    messages[0]["content"] = re.sub(
                        env_var_pattern, variable_markdown, str_content, flags=re.DOTALL
                    )
                else:
                    # 不存在，添加到开头
                    messages[0]["content"] = f"{variable_markdown}\n{str_content}"
                env_injected = True

            # 环境变量注入成功后，发送状态提示给用户
            if env_injected and __event_emitter__:
                try:
                    # 如果在异步环境中，使用 await
                    asyncio.create_task(self._emit_env_status(__event_emitter__))
                except RuntimeError:
                    # 如果不在异步环境中，直接调用
                    pass

    async def _emit_env_status(self, __event_emitter__):
        """
        发送环境变量注入成功的状态提示给前端用户
        """
        try:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "✓ 用户环境变量已注入成功",
                        "done": True,
                    },
                }
            )
        except Exception as e:
            print(f"发送状态提示时出错: {e}")

    async def _emit_search_status(self, __event_emitter__, model_name):
        """
        发送模型搜索功能启用的状态提示给前端用户
        """
        try:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"🔍 已为 {model_name} 启用搜索能力",
                        "done": True,
                    },
                }
            )
        except Exception as e:
            print(f"发送搜索状态提示时出错: {e}")
