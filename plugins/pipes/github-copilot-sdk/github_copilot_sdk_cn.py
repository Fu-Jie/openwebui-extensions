"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
openwebui_id: ce96f7b4-12fc-4ac3-9a01-875713e69359
description: 集成 GitHub Copilot SDK。支持动态模型、多轮对话、流式输出、多模态输入、无限会话及前端调试日志。
version: 0.2.3
requirements: github-copilot-sdk
"""

import os
import time
import json
import base64
import tempfile
import asyncio
import logging
import shutil
import subprocess
import sys
from typing import Optional, Union, AsyncGenerator, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import contextlib

# 导入 Copilot SDK 模块
from copilot import CopilotClient, define_tool

# Setup logger
logger = logging.getLogger(__name__)


class RandomNumberParams(BaseModel):
    min: int = Field(description="最小值（包含）")
    max: int = Field(description="最大值（包含）")


@define_tool(description="在指定范围内生成随机整数。")
async def generate_random_number(params: RandomNumberParams) -> str:
    import random

    if params.min >= params.max:
        raise ValueError("min 必须小于 max")
    number = random.randint(params.min, params.max)
    return f"生成的随机数: {number}"


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub 细粒度 Token（需要 Copilot Requests 权限）",
        )
        MODEL_ID: str = Field(
            default="gpt-5-mini",
            description="默认 Copilot 模型名（动态获取失败时使用）",
        )
        CLI_PATH: str = Field(
            default="/usr/local/bin/copilot",
            description="Copilot CLI 路径",
        )
        DEBUG: bool = Field(
            default=False,
            description="启用技术调试日志（连接信息等）",
        )
        LOG_LEVEL: str = Field(
            default="error",
            description="Copilot CLI 日志级别：none, error, warning, info, debug, all",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )
        SHOW_WORKSPACE_INFO: bool = Field(
            default=True,
            description="调试模式下显示会话工作空间路径与摘要",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="排除包含这些关键词的模型（逗号分隔，如：codex, haiku）",
        )
        WORKSPACE_DIR: str = Field(
            default="",
            description="文件操作的受限工作区目录；为空则使用当前进程目录",
        )
        INFINITE_SESSION: bool = Field(
            default=True,
            description="启用无限会话（自动上下文压缩）",
        )
        COMPACTION_THRESHOLD: float = Field(
            default=0.8,
            description="后台压缩阈值 (0.0-1.0)",
        )
        BUFFER_THRESHOLD: float = Field(
            default=0.95,
            description="缓冲区耗尽阈值 (0.0-1.0)",
        )
        TIMEOUT: int = Field(
            default=300,
            description="每个流式分块超时（秒）",
        )
        CUSTOM_ENV_VARS: str = Field(
            default="",
            description='自定义环境变量（JSON 格式，例如 {"VAR": "value"}）',
        )
        ENABLE_TOOLS: bool = Field(
            default=False,
            description="启用自定义工具（例如：随机数）",
        )
        AVAILABLE_TOOLS: str = Field(
            default="all",
            description="可用工具：'all' 或逗号分隔列表（例如：'generate_random_number'）",
        )
        REASONING_EFFORT: str = Field(
            default="medium",
            description="推理强度级别: low, medium, high. (gpt-5.2-codex 额外支持 xhigh)",
        )
        ENFORCE_FORMATTING: bool = Field(
            default=True,
            description="在系统提示词中添加格式化指导，以提高输出的可读性（段落、换行、结构）。",
        )

    class UserValves(BaseModel):
        REASONING_EFFORT: str = Field(
            default="",
            description="推理强度级别 (low, medium, high, xhigh)。留空以使用全局设置。",
        )
        CLI_PATH: str = Field(
            default="",
            description="自定义 Copilot CLI 路径。留空以使用全局设置。",
        )
        DEBUG: bool = Field(
            default=False,
            description="启用技术调试日志（连接信息等）",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )
        MODEL_ID: str = Field(
            default="",
            description="自定义模型 ID (例如 gpt-4o)。留空以使用全局默认值。",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "copilotsdk"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")
        self.thinking_started = False
        self._model_cache = []  # 模型列表缓存

    def __del__(self):
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

    # ==================== 系统固定入口 ====================
    # pipe() 是 OpenWebUI 调用的稳定入口。
    # 将该部分放在前面，便于快速定位与维护。
    # ======================================================
    async def pipe(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        return await self._pipe_impl(
            body,
            __metadata__=__metadata__,
            __user__=__user__,
            __event_emitter__=__event_emitter__,
            __event_call__=__event_call__,
        )

    # ==================== 功能性分区说明 ====================
    # 1) 工具注册：定义工具并在 _initialize_custom_tools 中注册
    # 2) 调试日志：_emit_debug_log / _emit_debug_log_sync
    # 3) 提示词/会话：_extract_system_prompt / _build_session_config / _build_prompt
    # 4) 运行流程：pipe() 负责请求，stream_response() 负责流式输出
    # ======================================================
    # ==================== 自定义工具示例 ====================
    # 工具注册：在模块级别添加 @define_tool 装饰的函数，
    # 然后在 _initialize_custom_tools() 的 all_tools 字典中注册。

    def _extract_text_from_content(self, content) -> str:
        """从各种消息内容格式中提取文本内容"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        return ""

    def _apply_formatting_hint(self, prompt: str) -> str:
        """在启用格式化时，向用户提示词追加轻量格式化要求。"""
        if not self.valves.ENFORCE_FORMATTING:
            return prompt

        if not prompt:
            return prompt

        if "[格式化指南]" in prompt or "[格式化要求]" in prompt:
            return prompt

        formatting_hint = (
            "\n\n[格式化要求]\n" "请使用清晰的段落与换行，必要时使用项目符号列表。"
        )
        return f"{prompt}{formatting_hint}"

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        """去重保序"""
        seen = set()
        result = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def _collect_model_ids(
        self, body: dict, request_model: str, real_model_id: str
    ) -> List[str]:
        """收集可能的模型 ID（来自请求/metadata/body params）"""
        model_ids: List[str] = []
        if request_model:
            model_ids.append(request_model)
        if request_model.startswith(f"{self.id}-"):
            model_ids.append(request_model[len(f"{self.id}-") :])
        if real_model_id:
            model_ids.append(real_model_id)

        metadata = body.get("metadata", {})
        if isinstance(metadata, dict):
            meta_model = metadata.get("model")
            meta_model_id = metadata.get("model_id")
            if isinstance(meta_model, str):
                model_ids.append(meta_model)
            if isinstance(meta_model_id, str):
                model_ids.append(meta_model_id)

        body_params = body.get("params", {})
        if isinstance(body_params, dict):
            for key in ("model", "model_id", "modelId"):
                val = body_params.get(key)
                if isinstance(val, str):
                    model_ids.append(val)

        return self._dedupe_preserve_order(model_ids)

    async def _extract_system_prompt(
        self,
        body: dict,
        messages: List[dict],
        request_model: str,
        real_model_id: str,
        __event_call__=None,
    ) -> tuple[Optional[str], str]:
        """从 metadata/模型 DB/body/messages 提取系统提示词"""
        system_prompt_content: Optional[str] = None
        system_prompt_source = ""

        # 1) metadata.model.params.system
        metadata = body.get("metadata", {})
        if isinstance(metadata, dict):
            meta_model = metadata.get("model")
            if isinstance(meta_model, dict):
                meta_params = meta_model.get("params")
                if isinstance(meta_params, dict) and meta_params.get("system"):
                    system_prompt_content = meta_params.get("system")
                    system_prompt_source = "metadata.model.params"
                    await self._emit_debug_log(
                        f"从 metadata.model.params 提取系统提示词（长度: {len(system_prompt_content)}）",
                        __event_call__,
                    )

        # 2) 模型 DB
        if not system_prompt_content:
            try:
                from open_webui.models.models import Models

                model_ids_to_try = self._collect_model_ids(
                    body, request_model, real_model_id
                )
                for mid in model_ids_to_try:
                    model_record = Models.get_model_by_id(mid)
                    if model_record and hasattr(model_record, "params"):
                        params = model_record.params
                        if isinstance(params, dict):
                            system_prompt_content = params.get("system")
                            if system_prompt_content:
                                system_prompt_source = f"model_db:{mid}"
                                await self._emit_debug_log(
                                    f"从模型数据库提取系统提示词（长度: {len(system_prompt_content)}）",
                                    __event_call__,
                                )
                                break
            except Exception as e:
                await self._emit_debug_log(
                    f"从模型数据库提取系统提示词失败: {e}",
                    __event_call__,
                )

        # 3) body.params.system
        if not system_prompt_content:
            body_params = body.get("params", {})
            if isinstance(body_params, dict):
                system_prompt_content = body_params.get("system")
                if system_prompt_content:
                    system_prompt_source = "body_params"
                    await self._emit_debug_log(
                        f"从 body.params 提取系统提示词（长度: {len(system_prompt_content)}）",
                        __event_call__,
                    )

        # 4) messages (role=system)
        if not system_prompt_content:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt_content = self._extract_text_from_content(
                        msg.get("content", "")
                    )
                    if system_prompt_content:
                        system_prompt_source = "messages_system"
                        await self._emit_debug_log(
                            f"从消息中提取系统提示词（长度: {len(system_prompt_content)}）",
                            __event_call__,
                        )
                    break

        return system_prompt_content, system_prompt_source

    def _build_client_config(self, body: dict) -> dict:
        """根据 Valves 和请求构建 CopilotClient 配置"""
        cwd = self.valves.WORKSPACE_DIR if self.valves.WORKSPACE_DIR else os.getcwd()
        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]
        client_config["cwd"] = cwd

        if self.valves.LOG_LEVEL:
            client_config["log_level"] = self.valves.LOG_LEVEL

        if self.valves.CUSTOM_ENV_VARS:
            try:
                custom_env = json.loads(self.valves.CUSTOM_ENV_VARS)
                if isinstance(custom_env, dict):
                    client_config["env"] = custom_env
            except:
                pass

        return client_config

    def _build_session_config(
        self,
        chat_id: Optional[str],
        real_model_id: str,
        custom_tools: List[Any],
        system_prompt_content: Optional[str],
        is_streaming: bool,
        reasoning_effort: str = "",
    ):
        """构建 Copilot SDK 的 SessionConfig"""
        from copilot.types import SessionConfig, InfiniteSessionConfig

        infinite_session_config = None
        if self.valves.INFINITE_SESSION:
            infinite_session_config = InfiniteSessionConfig(
                enabled=True,
                background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
                buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
            )

        system_message_config = None
        if system_prompt_content or self.valves.ENFORCE_FORMATTING:
            # 构建系统消息内容
            system_parts = []

            if system_prompt_content:
                system_parts.append(system_prompt_content)

            if self.valves.ENFORCE_FORMATTING:
                formatting_instruction = (
                    "\n\n[格式化指南]\n"
                    "在提供解释或描述时：\n"
                    "- 使用清晰的段落分隔（双换行）\n"
                    "- 将长句拆分为多个短句\n"
                    "- 对多个要点使用项目符号或编号列表\n"
                    "- 为主要部分添加标题（##、###）\n"
                    "- 确保不同主题之间有适当的间距"
                )
                system_parts.append(formatting_instruction)
                logger.info(f"[ENFORCE_FORMATTING] 已添加格式化指导到系统提示词")

            if system_parts:
                system_message_config = {
                    "mode": "append",
                    "content": "\n".join(system_parts),
                }

        # 准备会话配置参数
        session_params = {
            "session_id": chat_id if chat_id else None,
            "model": real_model_id,
            "streaming": is_streaming,
            "tools": custom_tools,
            "system_message": system_message_config,
            "infinite_sessions": infinite_session_config,
        }

        # 如果不是默认值（medium），添加 reasoning_effort
        if reasoning_effort and reasoning_effort.lower() != "medium":
            session_params["reasoning_effort"] = reasoning_effort.lower()

        return SessionConfig(**session_params)

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        """去重保序"""
        seen = set()
        result = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def _collect_model_ids(
        self, body: dict, request_model: str, real_model_id: str
    ) -> List[str]:
        """收集可能的模型 ID（来自请求/metadata/body params）"""
        model_ids: List[str] = []
        if request_model:
            model_ids.append(request_model)
        if request_model.startswith(f"{self.id}-"):
            model_ids.append(request_model[len(f"{self.id}-") :])
        if real_model_id:
            model_ids.append(real_model_id)

        metadata = body.get("metadata", {})
        if isinstance(metadata, dict):
            meta_model = metadata.get("model")
            meta_model_id = metadata.get("model_id")
            if isinstance(meta_model, str):
                model_ids.append(meta_model)
            if isinstance(meta_model_id, str):
                model_ids.append(meta_model_id)

        body_params = body.get("params", {})
        if isinstance(body_params, dict):
            for key in ("model", "model_id", "modelId"):
                val = body_params.get(key)
                if isinstance(val, str):
                    model_ids.append(val)

        return self._dedupe_preserve_order(model_ids)

    async def _extract_system_prompt(
        self,
        body: dict,
        messages: List[dict],
        request_model: str,
        real_model_id: str,
        __event_call__=None,
    ) -> tuple[Optional[str], str]:
        """从 metadata/模型 DB/body/messages 提取系统提示词"""
        system_prompt_content: Optional[str] = None
        system_prompt_source = ""

        # 1) metadata.model.params.system
        metadata = body.get("metadata", {})
        if isinstance(metadata, dict):
            meta_model = metadata.get("model")
            if isinstance(meta_model, dict):
                meta_params = meta_model.get("params")
                if isinstance(meta_params, dict) and meta_params.get("system"):
                    system_prompt_content = meta_params.get("system")
                    system_prompt_source = "metadata.model.params"
                    await self._emit_debug_log(
                        f"从 metadata.model.params 提取系统提示词（长度: {len(system_prompt_content)}）",
                        __event_call__,
                    )

        # 2) 模型 DB
        if not system_prompt_content:
            try:
                from open_webui.models.models import Models

                model_ids_to_try = self._collect_model_ids(
                    body, request_model, real_model_id
                )
                for mid in model_ids_to_try:
                    model_record = Models.get_model_by_id(mid)
                    if model_record and hasattr(model_record, "params"):
                        params = model_record.params
                        if isinstance(params, dict):
                            system_prompt_content = params.get("system")
                            if system_prompt_content:
                                system_prompt_source = f"model_db:{mid}"
                                await self._emit_debug_log(
                                    f"从模型数据库提取系统提示词（长度: {len(system_prompt_content)}）",
                                    __event_call__,
                                )
                                break
            except Exception as e:
                await self._emit_debug_log(
                    f"从模型数据库提取系统提示词失败: {e}",
                    __event_call__,
                )

        # 3) body.params.system
        if not system_prompt_content:
            body_params = body.get("params", {})
            if isinstance(body_params, dict):
                system_prompt_content = body_params.get("system")
                if system_prompt_content:
                    system_prompt_source = "body_params"
                    await self._emit_debug_log(
                        f"从 body.params 提取系统提示词（长度: {len(system_prompt_content)}）",
                        __event_call__,
                    )

        # 4) messages (role=system)
        if not system_prompt_content:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt_content = self._extract_text_from_content(
                        msg.get("content", "")
                    )
                    if system_prompt_content:
                        system_prompt_source = "messages_system"
                        await self._emit_debug_log(
                            f"从消息中提取系统提示词（长度: {len(system_prompt_content)}）",
                            __event_call__,
                        )
                    break

        return system_prompt_content, system_prompt_source

    def _initialize_custom_tools(self):
        """根据配置初始化自定义工具"""
        if not self.valves.ENABLE_TOOLS:
            return []

        # 定义所有可用工具（在此注册新工具）
        all_tools = {
            "generate_random_number": generate_random_number,
        }

        # 根据配置过滤
        if self.valves.AVAILABLE_TOOLS == "all":
            return list(all_tools.values())

        # 仅启用指定的工具
        enabled = [t.strip() for t in self.valves.AVAILABLE_TOOLS.split(",")]
        return [all_tools[name] for name in enabled if name in all_tools]

    async def _emit_debug_log(self, message: str, __event_call__=None):
        """在 DEBUG 开启时将日志输出到前端控制台。"""
        if not self.valves.DEBUG:
            return

        logger.debug(f"[Copilot Pipe] {message}")

        if not __event_call__:
            return

        try:
            js_code = f"""
                (async function() {{
                    console.debug("%c[Copilot Pipe] " + {json.dumps(message, ensure_ascii=False)}, "color: #3b82f6;");
                }})();
            """
            await __event_call__({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            logger.debug(f"[Copilot Pipe] 前端调试日志失败: {e}")

    def _emit_debug_log_sync(self, message: str, __event_call__=None):
        """在非异步上下文中输出调试日志。"""
        if not self.valves.DEBUG:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug(f"[Copilot Pipe] {message}")
            return

        loop.create_task(self._emit_debug_log(message, __event_call__))

    async def _emit_native_message(self, message_data: dict, __event_call__=None):
        """发送原生 OpenAI 格式消息事件用于工具调用/结果。"""
        if not __event_call__:
            return

        try:
            await __event_call__({"type": "message", "data": message_data})
            await self._emit_debug_log(
                f"已发送原生消息: {message_data.get('role')} - {list(message_data.keys())}",
                __event_call__,
            )
        except Exception as e:
            logger.warning(f"发送原生消息失败: {e}")
            await self._emit_debug_log(
                f"原生消息发送失败: {e}。回退到文本显示。", __event_call__
            )

    def _get_user_context(self):
        """获取用户上下文（占位，预留）。"""
        return {}

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None, __event_call__=None
    ) -> Dict[str, str]:
        """
        高度可靠的聊天上下文提取逻辑。
        优先级：__metadata__ > body['chat_id'] > body['metadata']['chat_id']
        """
        chat_id = ""
        source = "none"

        # 1. 优先从 __metadata__ 获取 (OpenWebUI 注入的最可靠来源)
        if __metadata__ and isinstance(__metadata__, dict):
            chat_id = __metadata__.get("chat_id", "")
            if chat_id:
                source = "__metadata__"

        # 2. 其次从 body 顶层获取
        if not chat_id and isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            if chat_id:
                source = "body_root"

        # 3. 最后从 body.metadata 获取
        if not chat_id and isinstance(body, dict):
            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                chat_id = body_metadata.get("chat_id", "")
                if chat_id:
                    source = "body_metadata"

        # 调试：记录 ID 来源
        if chat_id:
            self._emit_debug_log_sync(
                f"提取到 ChatID: {chat_id} (来源: {source})", __event_call__
            )
        else:
            # 如果还是没找到，记录一下 body 的键，方便排查
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log_sync(
                f"警告: 未能提取到 ChatID。Body 键: {keys}", __event_call__
            )

        return {
            "chat_id": str(chat_id).strip(),
        }

    async def pipes(self) -> List[dict]:
        """动态获取模型列表"""
        # 如果有缓存，直接返回
        if self._model_cache:
            return self._model_cache

        await self._emit_debug_log("正在动态获取模型列表...")
        try:
            self._setup_env()
            if not self.valves.GH_TOKEN:
                return [{"id": f"{self.id}-error", "name": "Error: GH_TOKEN not set"}]

            client_config = {}
            if os.environ.get("COPILOT_CLI_PATH"):
                client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

            client = CopilotClient(client_config)
            try:
                await client.start()
                models = await client.list_models()

                # 更新缓存
                self._model_cache = []
                exclude_list = [
                    k.strip().lower()
                    for k in self.valves.EXCLUDE_KEYWORDS.split(",")
                    if k.strip()
                ]

                models_with_info = []
                for m in models:
                    # 兼容字典和对象访问方式
                    m_id = (
                        m.get("id") if isinstance(m, dict) else getattr(m, "id", str(m))
                    )
                    m_name = (
                        m.get("name")
                        if isinstance(m, dict)
                        else getattr(m, "name", m_id)
                    )
                    m_policy = (
                        m.get("policy")
                        if isinstance(m, dict)
                        else getattr(m, "policy", {})
                    )
                    m_billing = (
                        m.get("billing")
                        if isinstance(m, dict)
                        else getattr(m, "billing", {})
                    )

                    # 检查策略状态
                    state = (
                        m_policy.get("state")
                        if isinstance(m_policy, dict)
                        else getattr(m_policy, "state", "enabled")
                    )
                    if state == "disabled":
                        continue

                    # 过滤逻辑
                    if any(kw in m_id.lower() for kw in exclude_list):
                        continue

                    # 获取倍率
                    multiplier = (
                        m_billing.get("multiplier", 1)
                        if isinstance(m_billing, dict)
                        else getattr(m_billing, "multiplier", 1)
                    )

                    # 格式化显示名称
                    if multiplier == 0:
                        display_name = f"-🔥 {m_id} (unlimited)"
                    else:
                        display_name = f"-{m_id} ({multiplier}x)"

                    models_with_info.append(
                        {
                            "id": f"{self.id}-{m_id}",
                            "name": display_name,
                            "multiplier": multiplier,
                            "raw_id": m_id,
                        }
                    )

                # 排序：倍率升序，然后是原始ID升序
                models_with_info.sort(key=lambda x: (x["multiplier"], x["raw_id"]))
                self._model_cache = [
                    {"id": m["id"], "name": m["name"]} for m in models_with_info
                ]

                await self._emit_debug_log(
                    f"成功获取 {len(self._model_cache)} 个模型 (已过滤)"
                )
                return self._model_cache
            except Exception as e:
                await self._emit_debug_log(f"获取模型列表失败: {e}")
                # 失败时返回默认模型
                return [
                    {
                        "id": f"{self.id}-{self.valves.MODEL_ID}",
                        "name": f"GitHub Copilot ({self.valves.MODEL_ID})",
                    }
                ]
            finally:
                await client.stop()
        except Exception as e:
            await self._emit_debug_log(f"Pipes Error: {e}")
            return [
                {
                    "id": f"{self.id}-{self.valves.MODEL_ID}",
                    "name": f"GitHub Copilot ({self.valves.MODEL_ID})",
                }
            ]

    async def _get_client(self):
        """Helper to get or create a CopilotClient instance."""
        # 确定工作空间目录
        cwd = self.valves.WORKSPACE_DIR if self.valves.WORKSPACE_DIR else os.getcwd()

        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]
        client_config["cwd"] = cwd

        # 设置日志级别
        if self.valves.LOG_LEVEL:
            client_config["log_level"] = self.valves.LOG_LEVEL

        # 添加自定义环境变量
        if self.valves.CUSTOM_ENV_VARS:
            try:
                custom_env = json.loads(self.valves.CUSTOM_ENV_VARS)
                if isinstance(custom_env, dict):
                    client_config["env"] = custom_env
            except:
                pass  # 静默失败，因为这是同步方法且不应影响主流程

        client = CopilotClient(client_config)
        await client.start()
        return client

    def _setup_env(self, __event_call__=None):
        cli_path = self.valves.CLI_PATH
        found = False

        if os.path.exists(cli_path):
            found = True

        if not found:
            sys_path = shutil.which("copilot")
            if sys_path:
                cli_path = sys_path
                found = True

        if not found:
            try:
                subprocess.run(
                    "curl -fsSL https://gh.io/copilot-install | bash",
                    shell=True,
                    check=True,
                )
                if os.path.exists(self.valves.CLI_PATH):
                    cli_path = self.valves.CLI_PATH
                    found = True
            except:
                pass

        if found:
            os.environ["COPILOT_CLI_PATH"] = cli_path
            cli_dir = os.path.dirname(cli_path)
            if cli_dir not in os.environ["PATH"]:
                os.environ["PATH"] = f"{cli_dir}:{os.environ['PATH']}"

            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    f"Copilot CLI 已定位: {cli_path}", __event_call__
                )

        if self.valves.GH_TOKEN:
            os.environ["GH_TOKEN"] = self.valves.GH_TOKEN
            os.environ["GITHUB_TOKEN"] = self.valves.GH_TOKEN
        else:
            if self.valves.DEBUG:
                self._emit_debug_log_sync("Warning: GH_TOKEN 未设置。", __event_call__)

    def _process_images(self, messages, __event_call__=None):
        attachments = []
        text_content = ""
        if not messages:
            return "", []
        last_msg = messages[-1]
        content = last_msg.get("content", "")

        if isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    text_content += item.get("text", "")
                elif item.get("type") == "image_url":
                    image_url = item.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:image"):
                        try:
                            header, encoded = image_url.split(",", 1)
                            ext = header.split(";")[0].split("/")[-1]
                            file_name = f"image_{len(attachments)}.{ext}"
                            file_path = os.path.join(self.temp_dir, file_name)
                            with open(file_path, "wb") as f:
                                f.write(base64.b64decode(encoded))
                            attachments.append(
                                {
                                    "type": "file",
                                    "path": file_path,
                                    "display_name": file_name,
                                }
                            )
                            self._emit_debug_log_sync(
                                f"Image processed: {file_path}", __event_call__
                            )
                        except Exception as e:
                            self._emit_debug_log_sync(
                                f"Image error: {e}", __event_call__
                            )
        else:
            text_content = str(content)
        return text_content, attachments

    def _sync_copilot_config(self, reasoning_effort: str, __event_call__=None):
        """
        动态更新 ~/.copilot/config.json 中的 reasoning_effort 设置。
        如果 API 注入被忽略，这提供了最后的保障。
        """
        if not reasoning_effort:
            return

        effort = reasoning_effort

        # 检查模型对 xhigh 的支持
        # 目前仅 gpt-5.2-codex 支持 xhigh
        # 在 _sync_copilot_config 中很难获得准确的当前模型 ID，
        # 因此这里我们放宽限制，允许写入 xhigh。
        # 如果模型不支持，Copilot CLI 可能会忽略或降级处理，但这比在这里硬编码判断更安全，
        # 因为获取当前请求的 body 需要修改函数签名。

        try:
            # 目标标准路径 ~/.copilot/config.json
            config_path = os.path.expanduser("~/.copilot/config.json")
            config_dir = os.path.dirname(config_path)

            # 仅在目录存在时执行（避免在错误环境创建垃圾文件）
            if not os.path.exists(config_dir):
                return

            data = {}
            # 读取现有配置
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            # 如果值有变化则更新
            current_val = data.get("reasoning_effort")
            if current_val != effort:
                data["reasoning_effort"] = effort
                try:
                    with open(config_path, "w") as f:
                        json.dump(data, f, indent=4)

                    self._emit_debug_log_sync(
                        f"已动态更新 ~/.copilot/config.json: reasoning_effort='{effort}'",
                        __event_call__,
                    )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"写入 config.json 失败: {e}", __event_call__
                    )
        except Exception as e:
            self._emit_debug_log_sync(f"配置同步检查失败: {e}", __event_call__)

    # ==================== 内部实现 ====================
    # _pipe_impl() 包含主请求处理逻辑。
    # ================================================
    async def _pipe_impl(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        self._setup_env(__event_call__)
        if not self.valves.GH_TOKEN:
            return "Error: 请在 Valves 中配置 GH_TOKEN。"

        # 解析用户选择的模型
        request_model = body.get("model", "")
        real_model_id = self.valves.MODEL_ID  # 默认值

        # 确定有效的推理强度和调试设置
        if __user__:
            raw_valves = __user__.get("valves", {})
            if isinstance(raw_valves, self.UserValves):
                user_valves = raw_valves
            elif isinstance(raw_valves, dict):
                user_valves = self.UserValves(**raw_valves)
            else:
                user_valves = self.UserValves()
        else:
            user_valves = self.UserValves()
        effective_reasoning_effort = (
            user_valves.REASONING_EFFORT
            if user_valves.REASONING_EFFORT
            else self.valves.REASONING_EFFORT
        )
        # 如果用户启用了 DEBUG，则覆盖全局设置
        if user_valves.DEBUG:
            self.valves.DEBUG = True

        # 处理 SHOW_THINKING（优先使用用户设置）
        show_thinking = (
            user_valves.SHOW_THINKING
            if user_valves.SHOW_THINKING is not None
            else self.valves.SHOW_THINKING
        )

        if request_model.startswith(f"{self.id}-"):
            real_model_id = request_model[len(f"{self.id}-") :]
            await self._emit_debug_log(
                f"使用选择的模型: {real_model_id}", __event_call__
            )

        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        # 使用改进的助手获取 Chat ID
        chat_ctx = self._get_chat_context(body, __metadata__, __event_call__)
        chat_id = chat_ctx.get("chat_id")

        # 从多个来源提取系统提示词
        system_prompt_content, system_prompt_source = await self._extract_system_prompt(
            body, messages, request_model, real_model_id, __event_call__
        )

        if system_prompt_content:
            preview = system_prompt_content[:60].replace("\n", " ")
            await self._emit_debug_log(
                f"系统提示词已确认（来源: {system_prompt_source}, 长度: {len(system_prompt_content)}, 预览: {preview}）",
                __event_call__,
            )

        is_streaming = body.get("stream", False)
        await self._emit_debug_log(f"请求流式传输: {is_streaming}", __event_call__)

        client = CopilotClient(self._build_client_config(body))
        should_stop_client = True
        try:
            await client.start()

            # 初始化自定义工具
            custom_tools = self._initialize_custom_tools()
            if custom_tools:
                tool_names = [t.name for t in custom_tools]
                await self._emit_debug_log(
                    f"已启用 {len(custom_tools)} 个自定义工具: {tool_names}",
                    __event_call__,
                )

            session = None

            if chat_id:
                try:
                    # 尝试直接使用 chat_id 作为 session_id 恢复会话
                    session = await client.resume_session(chat_id)
                    await self._emit_debug_log(
                        f"已通过 ChatID 恢复会话: {chat_id}", __event_call__
                    )

                    # 显示工作空间信息（如果可用）
                    if self.valves.DEBUG and self.valves.SHOW_WORKSPACE_INFO:
                        if session.workspace_path:
                            await self._emit_debug_log(
                                f"会话工作空间: {session.workspace_path}",
                                __event_call__,
                            )

                    is_new_session = False
                except Exception as e:
                    # 恢复失败，磁盘上可能不存在该会话
                    reasoning_effort = (effective_reasoning_effort,)
                    await self._emit_debug_log(
                        f"会话 {chat_id} 不存在或已过期 ({str(e)})，将创建新会话。",
                        __event_call__,
                    )
                    session = None

            if session is None:
                session_config = self._build_session_config(
                    chat_id,
                    real_model_id,
                    custom_tools,
                    system_prompt_content,
                    is_streaming,
                )
                if system_prompt_content:
                    await self._emit_debug_log(
                        f"配置系统消息（模式: append）",
                        __event_call__,
                    )

                # 显示系统配置预览
                if system_prompt_content or self.valves.ENFORCE_FORMATTING:
                    preview_parts = []
                    if system_prompt_content:
                        preview_parts.append(
                            f"自定义提示词: {system_prompt_content[:100]}..."
                        )
                    if self.valves.ENFORCE_FORMATTING:
                        preview_parts.append("格式化指导: 已启用")

                    if isinstance(session_config, dict):
                        system_config = session_config.get("system_message", {})
                    else:
                        system_config = getattr(session_config, "system_message", None)

                    if isinstance(system_config, dict):
                        full_content = system_config.get("content", "")
                    else:
                        full_content = ""

                    await self._emit_debug_log(
                        f"系统消息配置 - {', '.join(preview_parts)} (总长度: {len(full_content)} 字符)",
                        __event_call__,
                    )

                session = await client.create_session(config=session_config)

                # 获取新会话 ID
                new_sid = getattr(session, "session_id", getattr(session, "id", None))
                await self._emit_debug_log(f"创建了新会话: {new_sid}", __event_call__)

                # 显示新会话的工作空间信息
                if self.valves.DEBUG and self.valves.SHOW_WORKSPACE_INFO:
                    if session.workspace_path:
                        await self._emit_debug_log(
                            f"会话工作空间: {session.workspace_path}",
                            __event_call__,
                        )

            # 构建 Prompt（基于会话：仅发送最新用户输入）
            prompt = self._apply_formatting_hint(last_text)

            send_payload = {"prompt": prompt, "mode": "immediate"}
            if attachments:
                send_payload["attachments"] = attachments

            if body.get("stream", False):
                # 确定 UI 显示的会话状态消息
                init_msg = ""
                if self.valves.DEBUG:
                    if is_new_session:
                        new_sid = getattr(
                            session, "session_id", getattr(session, "id", "unknown")
                        )
                        init_msg = f"> [Debug] 创建了新会话: {new_sid}\n"
                    else:
                        init_msg = f"> [Debug] 已通过 ChatID 恢复会话: {chat_id}\n"

                return self.stream_response(
                    client,
                    session,
                    send_payload,
                    init_msg,
                    __event_call__,
                    reasoning_effort=effective_reasoning_effort,
                    show_thinking=show_thinking,
                )
            else:
                try:
                    response = await session.send_and_wait(send_payload)
                    return response.data.content if response else "Empty response."
                finally:
                    # 清理：如果没有 chat_id（临时会话），销毁会话
                    if not chat_id:
                        try:
                            await session.destroy()
                        except Exception as cleanup_error:
                            await self._emit_debug_log(
                                f"会话清理警告: {cleanup_error}",
                                __event_call__,
                            )
        except Exception as e:
            await self._emit_debug_log(f"请求错误: {e}", __event_call__)
            return f"Error: {str(e)}"
        finally:
            if should_stop_client:
                try:
                    await client.stop()
                except:
                    pass

    async def stream_response(
        self,
        client,
        session,
        send_payload,
        init_message: str = "",
        __event_call__=None,
        reasoning_effort: str = "",
        show_thinking: bool = True,
    ) -> AsyncGenerator:
        """
        从 Copilot SDK 流式传输响应，处理各种事件类型。
        遵循官方 SDK 模式进行事件处理和流式传输。
        """
        from copilot.generated.session_events import SessionEventType

        queue = asyncio.Queue()
        done = asyncio.Event()
        SENTINEL = object()
        # 使用本地状态来处理并发和跟踪
        state = {"thinking_started": False, "content_sent": False}
        has_content = False  # 追踪是否已经输出了内容
        active_tools = {}  # 映射 tool_call_id 到工具名称

        def get_event_type(event) -> str:
            """提取事件类型为字符串，处理枚举和字符串类型。"""
            if hasattr(event, "type"):
                event_type = event.type
                # 处理 SessionEventType 枚举
                if hasattr(event_type, "value"):
                    return event_type.value
                return str(event_type)
            return "unknown"

        def safe_get_data_attr(event, attr: str, default=None):
            """
            安全地从 event.data 提取属性。
            同时处理字典访问和对象属性访问。
            """
            if not hasattr(event, "data") or event.data is None:
                return default

            data = event.data

            # 首先尝试作为字典
            if isinstance(data, dict):
                return data.get(attr, default)

            # 尝试作为对象属性
            return getattr(data, attr, default)

        def handler(event):
            """
            事件处理器，遵循官方 SDK 模式。
            处理流式增量、推理、工具事件和会话状态。
            """
            event_type = get_event_type(event)

            # === 消息增量事件（主要流式内容）===
            if event_type == "assistant.message_delta":
                # 官方：Python SDK 使用 event.data.delta_content
                delta = safe_get_data_attr(
                    event, "delta_content"
                ) or safe_get_data_attr(event, "deltaContent")
                if delta:
                    state["content_sent"] = True
                    if state["thinking_started"]:
                        queue.put_nowait("\n</think>\n")
                        state["thinking_started"] = False
                    queue.put_nowait(delta)

            # === 完整消息事件（非流式响应） ===
            elif event_type == "assistant.message":
                # 处理完整消息（当 SDK 返回完整内容而不是增量时）
                content = safe_get_data_attr(event, "content") or safe_get_data_attr(
                    event, "message"
                )
                if content:
                    state["content_sent"] = True
                    if state["thinking_started"]:
                        queue.put_nowait("\n</think>\n")
                        state["thinking_started"] = False
                    queue.put_nowait(content)

            # === 推理增量事件（思维链流式传输）===
            elif event_type == "assistant.reasoning_delta":
                delta = safe_get_data_attr(
                    event, "delta_content"
                ) or safe_get_data_attr(event, "deltaContent")
                if delta:
                    # 如果内容已经开始，抑制迟到的推理
                    if state["content_sent"]:
                        return

                    if not state["thinking_started"] and show_thinking:
                        queue.put_nowait("<think>\n")
                        state["thinking_started"] = True
                    if state["thinking_started"]:
                        queue.put_nowait(delta)

            # === 完整推理事件（非流式推理） ===
            elif event_type == "assistant.reasoning":
                # 处理完整推理内容
                reasoning = safe_get_data_attr(event, "content") or safe_get_data_attr(
                    event, "reasoning"
                )
                if reasoning:
                    # 如果内容已经开始，抑制延迟到达的推理
                    if state["content_sent"]:
                        return

                    if not state["thinking_started"] and show_thinking:
                        queue.put_nowait("<think>\n")
                        state["thinking_started"] = True
                    if state["thinking_started"]:
                        queue.put_nowait(reasoning)

            # === 工具执行事件 ===
            elif event_type == "tool.execution_start":
                tool_name = (
                    safe_get_data_attr(event, "name")
                    or safe_get_data_attr(event, "tool_name")
                    or "未知工具"
                )
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")

                # 获取工具参数
                tool_args = {}
                try:
                    args_obj = safe_get_data_attr(event, "arguments")
                    if isinstance(args_obj, dict):
                        tool_args = args_obj
                    elif isinstance(args_obj, str):
                        tool_args = json.loads(args_obj)
                except:
                    pass

                if tool_call_id:
                    active_tools[tool_call_id] = {
                        "name": tool_name,
                        "arguments": tool_args,
                    }

                # 在显示工具前关闭思考标签
                if state["thinking_started"]:
                    queue.put_nowait("\n</think>\n")
                    state["thinking_started"] = False

                # 使用改进的格式展示工具调用
                if tool_args:
                    tool_args_json = json.dumps(tool_args, indent=2, ensure_ascii=False)
                    tool_display = f"\n\n<details>\n<summary>🔧 执行工具: {tool_name}</summary>\n\n**参数:**\n\n```json\n{tool_args_json}\n```\n\n</details>\n\n"
                else:
                    tool_display = f"\n\n<details>\n<summary>🔧 执行工具: {tool_name}</summary>\n\n*无参数*\n\n</details>\n\n"

                queue.put_nowait(tool_display)

                self._emit_debug_log_sync(f"工具开始: {tool_name}", __event_call__)

            elif event_type == "tool.execution_complete":
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)

                # 处理旧的字符串格式和新的字典格式
                if isinstance(tool_info, str):
                    tool_name = tool_info
                elif isinstance(tool_info, dict):
                    tool_name = tool_info.get("name", "未知工具")
                else:
                    tool_name = "未知工具"

                # 尝试获取结果内容
                result_content = ""
                result_type = "success"
                try:
                    result_obj = safe_get_data_attr(event, "result")
                    if hasattr(result_obj, "content"):
                        result_content = result_obj.content
                    elif isinstance(result_obj, dict):
                        result_content = result_obj.get("content", "")
                        result_type = result_obj.get("result_type", "success")
                        if not result_content:
                            # 如果没有 content 字段，尝试序列化整个字典
                            result_content = json.dumps(
                                result_obj, indent=2, ensure_ascii=False
                            )
                except Exception as e:
                    self._emit_debug_log_sync(f"提取结果时出错: {e}", __event_call__)
                    result_type = "failure"
                    result_content = f"错误: {str(e)}"

                # 使用改进的格式展示工具结果
                if result_content:
                    status_icon = "✅" if result_type == "success" else "❌"

                    # 尝试检测内容类型以便更好地格式化
                    is_json = False
                    try:
                        json_obj = (
                            json.loads(result_content)
                            if isinstance(result_content, str)
                            else result_content
                        )
                        if isinstance(json_obj, (dict, list)):
                            result_content = json.dumps(
                                json_obj, indent=2, ensure_ascii=False
                            )
                            is_json = True
                    except:
                        pass

                    # 根据内容类型格式化
                    if is_json:
                        # JSON 内容：使用代码块和语法高亮
                        result_display = f"\n<details>\n<summary>{status_icon} 执行结果: {tool_name}</summary>\n\n```json\n{result_content}\n```\n\n</details>\n\n"
                    else:
                        # 纯文本：保留格式，不使用代码块
                        result_display = f"\n<details>\n<summary>{status_icon} 执行结果: {tool_name}</summary>\n\n{result_content}\n\n</details>\n\n"

                    queue.put_nowait(result_display)

            elif event_type == "tool.execution_progress":
                # 工具执行进度更新（用于长时间运行的工具）
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)
                tool_name = (
                    tool_info.get("name", "未知工具")
                    if isinstance(tool_info, dict)
                    else "未知工具"
                )

                progress = safe_get_data_attr(event, "progress", 0)
                message = safe_get_data_attr(event, "message", "")

                if message:
                    progress_display = f"\n> 🔄 **{tool_name}**: {message}\n"
                    queue.put_nowait(progress_display)

                self._emit_debug_log_sync(
                    f"工具进度: {tool_name} - {progress}%", __event_call__
                )

            elif event_type == "tool.execution_partial_result":
                # 流式工具结果（用于增量输出的工具）
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)
                tool_name = (
                    tool_info.get("name", "未知工具")
                    if isinstance(tool_info, dict)
                    else "未知工具"
                )

                partial_content = safe_get_data_attr(event, "content", "")
                if partial_content:
                    queue.put_nowait(partial_content)

                self._emit_debug_log_sync(f"工具部分结果: {tool_name}", __event_call__)

            # === 使用统计事件 ===
            elif event_type == "assistant.usage":
                # 当前助手回合的 token 使用量
                if self.valves.DEBUG:
                    input_tokens = safe_get_data_attr(event, "input_tokens", 0)
                    output_tokens = safe_get_data_attr(event, "output_tokens", 0)
                    total_tokens = safe_get_data_attr(event, "total_tokens", 0)
                pass

            elif event_type == "session.usage_info":
                # 会话累计使用信息
                pass

            # === 会话状态事件 ===
            elif event_type == "session.compaction_start":
                self._emit_debug_log_sync("会话压缩已开始", __event_call__)

            elif event_type == "session.compaction_complete":
                self._emit_debug_log_sync("会话压缩已完成", __event_call__)

            elif event_type == "session.idle":
                # 会话处理完成 - 发出完成信号
                done.set()
                try:
                    queue.put_nowait(SENTINEL)
                except:
                    pass

            elif event_type == "session.error":
                error_msg = safe_get_data_attr(event, "message", "未知错误")
                queue.put_nowait(f"\n[错误: {error_msg}]")
                done.set()
                try:
                    queue.put_nowait(SENTINEL)
                except:
                    pass

        unsubscribe = session.on(handler)

        self._emit_debug_log_sync(f"已订阅事件。正在发送请求...", __event_call__)

        # 使用 asyncio.create_task 防止 session.send 阻塞流读取
        # 如果 SDK 实现等待完成。
        send_task = asyncio.create_task(session.send(send_payload))
        self._emit_debug_log_sync(f"Prompt 已发送 (异步任务已启动)", __event_call__)

        # 安全的初始 yield，带错误处理
        try:
            if self.valves.DEBUG:
                yield "<think>\n"
                if init_message:
                    yield init_message

                if reasoning_effort and reasoning_effort != "off":
                    yield f"> [Debug] 已注入推理强度 (Reasoning Effort): {reasoning_effort.upper()}\n"

                yield "> [Debug] 连接已建立，等待响应...\n"
                self.thinking_started = True
        except Exception as e:
            # 如果初始 yield 失败，记录但继续处理
            self._emit_debug_log_sync(f"初始 yield 警告: {e}", __event_call__)

        try:
            while not done.is_set():
                try:
                    chunk = await asyncio.wait_for(
                        queue.get(), timeout=float(self.valves.TIMEOUT)
                    )
                    if chunk is SENTINEL:
                        break
                    if chunk:
                        has_content = True
                        try:
                            yield chunk
                        except Exception as yield_error:
                            # 客户端关闭连接，优雅停止
                            self._emit_debug_log_sync(
                                f"Yield 错误（客户端断开连接？）: {yield_error}",
                                __event_call__,
                            )
                            break
                except asyncio.TimeoutError:
                    if done.is_set():
                        break
                    if self.thinking_started:
                        try:
                            yield f"> [Debug] 等待响应中 (已超过 {self.valves.TIMEOUT} 秒)...\n"
                        except:
                            # 如果超时期间 yield 失败，连接已断开
                            break
                    continue

            while not queue.empty():
                chunk = queue.get_nowait()
                if chunk is SENTINEL:
                    break
                if chunk:
                    has_content = True
                    try:
                        yield chunk
                    except:
                        # 连接关闭，停止 yielding
                        break

            if self.thinking_started:
                try:
                    yield "\n</think>\n"
                    has_content = True
                except:
                    pass  # 连接已关闭

            # 核心修复：如果整个过程没有任何输出，返回一个提示，防止 OpenWebUI 报错
            if not has_content:
                try:
                    yield "⚠️ Copilot 未返回任何内容。请检查模型 ID 是否正确，或尝试在 Valves 中开启 DEBUG 模式查看详细日志。"
                except:
                    pass  # 连接已关闭

        except Exception as e:
            try:
                yield f"\n[Stream Error: {str(e)}]"
            except:
                pass  # 连接已关闭
        finally:
            unsubscribe()
            # 销毁会话对象以释放内存，但保留磁盘数据
            await session.destroy()
