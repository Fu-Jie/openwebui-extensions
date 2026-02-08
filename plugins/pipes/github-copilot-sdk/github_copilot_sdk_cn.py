"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
description: 集成 GitHub Copilot SDK。支持动态模型、多轮对话、流式输出、多模态输入、无限会话及前端调试日志。
version: 0.5.1
requirements: github-copilot-sdk==0.1.23
"""

import os
import re
import time
import json
import base64
import tempfile
import asyncio
import logging
import shutil
import subprocess
import sys
import hashlib
from pathlib import Path
from typing import Optional, Union, AsyncGenerator, List, Any, Dict, Callable, Tuple, Literal
from types import SimpleNamespace
from pydantic import BaseModel, Field, create_model
from datetime import datetime, timezone
import contextlib

# 导入 Copilot SDK 模块
from copilot import CopilotClient, define_tool

# 导入 Tool Server Connections 和 Tool System (从 OpenWebUI 配置)
from open_webui.config import (
    PERSISTENT_CONFIG_REGISTRY,
    TOOL_SERVER_CONNECTIONS,
)
from open_webui.utils.tools import get_tools as get_openwebui_tools, get_builtin_tools
from open_webui.models.tools import Tools
from open_webui.models.users import Users

# Setup logger
logger = logging.getLogger(__name__)

FORMATTING_GUIDELINES = (
    "\n\n[环境与能力上下文]\n"
    "你是一个在特定高性能环境中运行的 AI 助手。了解你的上下文对于做出最佳决策至关重要。\n"
    "\n"
    "**系统环境：**\n"
    "- **平台**：你在 **OpenWebUI** 托管的 Linux 容器化环境中运行。\n"
    "- **核心引擎**：你由 **GitHub Copilot SDK** 驱动，并通过 **GitHub Copilot CLI** 进行交互。\n"
    "- **访问权限**：你可以直接访问 **OpenWebUI 源代码**。你可以通过文件操作或工具读取、分析和参考你正在运行的平台的内部实现。\n"
    "- **文件系统访问**：你以 **root** 身份运行。你对 **整个容器文件系统** 拥有 **读取权限**（包括系统文件）。但是，你应 **仅写入** 你指定的持久化工作区目录。\n"
    "- **原生 Python 环境**：你运行在一个 **丰富的 Python 环境** 中，已经包含了 OpenWebUI 的所有依赖库。你可以直接导入并使用这些已安装的库（例如用于数据处理、工具函数等），而无需安装任何新东西。\n"
    "- **包管理**：仅当你需要 **额外** 的库时，才应在你的工作区内 **创建一个虚拟环境** 并在那里安装它们。不要搞乱全局 pip。\n"
    "- **网络**：你有互联网访问权限，并且可以在提供相应工具（例如 Web 搜索、MCP 服务器）的情况下与外部 API 进行交互。\n"
    "\n"
    "**界面能力 (OpenWebUI)：**\n"
    "- **丰富的 Web UI**：你不受简单终端或纯文本响应的限制。你在现代 Web 浏览器中进行渲染。\n"
    "- **视觉渲染**：你可以并且应该使用高级视觉元素来清晰地解释概念。\n"
    "- **交互式脚本**：如果环境支持/工具有效，你通常可以直接运行 Python 脚本来执行计算、数据分析或自动化任务。\n"
    "- **内置工具集成**：OpenWebUI 提供了与内部服务直接交互的原生工具。例如，`create_note`、`get_notes` 或 `manage_memories` 等工具直接操作平台的数据库。利用这些工具来持久化地管理用户数据和系统状态。\n"
    "\n"
    "**格式化与呈现指令：**\n"
    "1. **Markdown & 多媒体**：\n"
    "   - 自由使用 **粗体**、*斜体*、列表和 **Markdown 表格**（标准格式，严禁使用 HTML 表格）来构建你的答案。\n"
    "   - **Mermaid 图表**：对于流程图、序列图或架构逻辑，请务必使用标准的 ```mermaid 代码块。不要使用其他格式。\n"
    "   - **LaTeX 数学**：使用标准 LaTeX 格式表示数学表达式。\n"
    "\n"
    "2. **图像与文件**：\n"
    "   - 如果工具生成了图像或文件，你 **必须** 使用 `![caption](url)` 直接嵌入。\n"
    "   - 除非明确要求，否则不要仅提供文本链接。\n"
    "\n"
    "3. **交互式 HTML/JS**：\n"
    "   - 你可以输出独立的 HTML/JS/CSS 代码块。OpenWebUI 将在 iframe 中将其渲染为交互式小部件。\n"
    "   - **重要**：请将所有 HTML、CSS（在 `<style>` 中）和 JavaScript（在 `<script>` 中）合并到一个 **单一的** ` ```html ` 代码块中。\n"
    "   - 将此用于动态数据可视化（例如图表）、交互式演示或自定义 UI 组件。\n"
    "\n"
    "4. **响应结构**：\n"
    "   - **先思考**：在执行复杂任务之前，简要概述你的计划。\n"
    "   - **简洁但完整**：具体的答案优于通用的答案。\n"
    "   - **高级质感**：格式化你的输出，使其看起来专业且经过打磨，就像技术博客文章或文档一样。\n"
)


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (需要 'Copilot Requests' 权限)",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="启用 OpenWebUI 工具 (包括自定义工具和工具服务器工具)。",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="启用直接 MCP 客户端连接 (推荐)。",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="缓存 OpenWebUI 工具和 MCP 服务器配置 (性能优化)。",
        )
        REASONING_EFFORT: Literal["low", "medium", "high", "xhigh"] = Field(
            default="medium",
            description="推理强度级别 (low, medium, high)。仅影响标准 Copilot 模型 (非 BYOK)。",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )

        INFINITE_SESSION: bool = Field(
            default=True,
            description="启用无限会话（自动上下文压缩）",
        )
        DEBUG: bool = Field(
            default=False,
            description="启用技术调试日志（连接信息等）",
        )
        LOG_LEVEL: str = Field(
            default="error",
            description="Copilot CLI 日志级别：none, error, warning, info, debug, all",
        )
        TIMEOUT: int = Field(
            default=300,
            description="每个流式分块超时（秒）",
        )
        WORKSPACE_DIR: str = Field(
            default="",
            description="文件操作的受限工作区目录。为空则使用当前进程目录。",
        )
        COPILOT_CLI_VERSION: str = Field(
            default="0.0.405",
            description="指定安装/强制使用的 Copilot CLI 版本 (例如 '0.0.405')。留空则表示使用最新版。",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="排除包含这些关键词的模型（逗号分隔，如：codex, haiku）",
        )
        COMPACTION_THRESHOLD: float = Field(
            default=0.8,
            description="后台压缩阈值 (0.0-1.0)",
        )
        BUFFER_THRESHOLD: float = Field(
            default=0.95,
            description="缓冲区耗尽阈值 (0.0-1.0)",
        )
        CUSTOM_ENV_VARS: str = Field(
            default="",
            description='自定义环境变量（JSON 格式，例如 {"VAR": "value"}）',
        )

        BYOK_TYPE: Literal["openai", "anthropic"] = Field(
            default="openai",
            description="BYOK 提供商类型：openai, anthropic",
        )
        BYOK_BASE_URL: str = Field(
            default="",
            description="BYOK 基础 URL (例如 https://api.openai.com/v1)",
        )
        BYOK_API_KEY: str = Field(
            default="",
            description="BYOK API 密钥 (全局设置)",
        )
        BYOK_BEARER_TOKEN: str = Field(
            default="",
            description="BYOK Bearer 令牌 (全局，优先级高于 API Key)",
        )
        BYOK_MODELS: str = Field(
            default="",
            description="BYOK 模型列表 (逗号分隔)。留空则尝试从 API 获取。",
        )
        BYOK_WIRE_API: Literal["completions", "responses"] = Field(
            default="completions",
            description="BYOK 传输 API 类型：completions, responses",
        )

    class UserValves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="个人 GitHub Fine-grained Token (覆盖全局设置)",
        )
        REASONING_EFFORT: Literal["", "low", "medium", "high", "xhigh"] = Field(
            default="",
            description="推理强度级别覆盖。仅影响标准 Copilot 模型。",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )
        DEBUG: bool = Field(
            default=False,
            description="启用技术调试日志（连接信息等）",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="启用 OpenWebUI 工具 (包括自定义工具和工具服务器工具)。",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="启用动态 MCP 服务器加载 (覆盖全局设置)。",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="为此用户启用工具/MCP 配置缓存。",
        )

        # BYOK 用户覆盖
        BYOK_API_KEY: str = Field(
            default="",
            description="BYOK API 密钥 (用户覆盖)",
        )
        BYOK_TYPE: Literal["", "openai", "anthropic"] = Field(
            default="",
            description="BYOK 提供商类型覆盖。",
        )
        BYOK_BASE_URL: str = Field(
            default="",
            description="BYOK 基础 URL 覆盖。",
        )
        BYOK_BEARER_TOKEN: str = Field(
            default="",
            description="BYOK Bearer 令牌 覆盖。",
        )
        BYOK_MODELS: str = Field(
            default="",
            description="BYOK 模型列表覆盖。",
        )
        BYOK_WIRE_API: Literal["", "completions", "responses"] = Field(
            default="",
            description="BYOK 传输 API 覆盖。",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "copilotsdk"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")
        self._model_cache = []  # 模型列表缓存
        self._standard_model_ids = set()  # 追踪标准模型 ID，以区分 BYOK 模型
        self._env_setup_done = False  # 是否已完成环境初始化环境检查
        self._tool_cache = None  # 已转换的 OpenWebUI 工具缓存
        self._mcp_server_cache = None  # MCP 服务器配置缓存
        self._last_update_check = 0  # Timestamp of last CLI update check

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

    # ==================== 功能性分区 ====================
    # 1) 工具加载与转换
    # 2) 提示词提取与处理
    # 3) 环境配置与工作区
    # ======================================================

    async def _initialize_custom_tools(self, __user__=None, __event_call__=None):
        """根据配置初始化自定义工具"""
        if not self.valves.ENABLE_OPENWEBUI_TOOLS:
            return []

        # 确定缓存设置 (用户覆盖 > 全局)
        enable_cache = self.valves.ENABLE_TOOL_CACHE
        if __user__:
            try:
                raw_user_valves = __user__.get("valves", {})
                if isinstance(raw_user_valves, dict):
                    uv = self.UserValves(**raw_user_valves)
                    enable_cache = uv.ENABLE_TOOL_CACHE
            except:
                pass

        # 检查缓存
        if enable_cache and self._tool_cache is not None:
            await self._emit_debug_log("ℹ️ 使用缓存的 OpenWebUI 工具。", __event_call__)
            return self._tool_cache

        # 动态加载 OpenWebUI 工具
        openwebui_tools = await self._load_openwebui_tools(
            __user__=__user__, __event_call__=__event_call__
        )

        # 更新缓存
        if enable_cache:
            self._tool_cache = openwebui_tools
            await self._emit_debug_log(
                "✅ OpenWebUI 工具已缓存，供后续请求使用。", __event_call__
            )

        return openwebui_tools

    def _json_schema_to_python_type(self, schema: dict) -> Any:
        """将 JSON Schema 类型转换为 Pydantic 模型的 Python 类型。"""
        if not isinstance(schema, dict):
            return Any

        # 检查枚举 (Literal)
        enum_values = schema.get("enum")
        if enum_values and isinstance(enum_values, list):
            from typing import Literal

            return Literal[tuple(enum_values)]

        schema_type = schema.get("type")
        if isinstance(schema_type, list):
            schema_type = next((t for t in schema_type if t != "null"), schema_type[0])

        if schema_type == "string":
            return str
        if schema_type == "integer":
            return int
        if schema_type == "number":
            return float
        if schema_type == "boolean":
            return bool
        if schema_type == "object":
            return Dict[str, Any]
        if schema_type == "array":
            items_schema = schema.get("items", {})
            item_type = self._json_schema_to_python_type(items_schema)
            return List[item_type]

        return Any

    def _convert_openwebui_tool(self, tool_name: str, tool_dict: dict):
        """将 OpenWebUI 工具定义转换为 Copilot SDK 工具。"""
        # 净化工具名称以匹配模式 ^[a-zA-Z0-9_-]+$
        sanitized_tool_name = re.sub(r"[^a-zA-Z0-9_-]", "_", tool_name)

        if not sanitized_tool_name or re.match(r"^[_.-]+$", sanitized_tool_name):
            hash_suffix = hashlib.md5(tool_name.encode("utf-8")).hexdigest()[:8]
            sanitized_tool_name = f"tool_{hash_suffix}"

        spec = tool_dict.get("spec", {}) if isinstance(tool_dict, dict) else {}
        params_schema = spec.get("parameters", {}) if isinstance(spec, dict) else {}
        properties = params_schema.get("properties", {})
        required = params_schema.get("required", [])

        if not isinstance(properties, dict):
            properties = {}
        if not isinstance(required, list):
            required = []

        required_set = set(required)
        fields = {}
        for param_name, param_schema in properties.items():
            param_type = self._json_schema_to_python_type(param_schema)
            description = ""
            if isinstance(param_schema, dict):
                description = param_schema.get("description", "")

            # 提取默认值
            default_value = None
            if isinstance(param_schema, dict) and "default" in param_schema:
                default_value = param_schema.get("default")

            if param_name in required_set:
                if description:
                    fields[param_name] = (
                        param_type,
                        Field(..., description=description),
                    )
                else:
                    fields[param_name] = (param_type, ...)
            else:
                optional_type = Optional[param_type]
                if description:
                    fields[param_name] = (
                        optional_type,
                        Field(default=default_value, description=description),
                    )
                else:
                    fields[param_name] = (optional_type, default_value)

        ParamsModel = (
            create_model(f"{sanitized_tool_name}_Params", **fields)
            if fields
            else create_model(f"{sanitized_tool_name}_Params")
        )

        tool_callable = tool_dict.get("callable")
        tool_description = spec.get("description", "") if isinstance(spec, dict) else ""
        if not tool_description and isinstance(spec, dict):
            tool_description = spec.get("summary", "")

        # 确定工具来源/组以添加描述前缀
        tool_id = tool_dict.get("tool_id", "")
        tool_type = tool_dict.get("type", "")

        if tool_type == "builtin":
            group_prefix = "[OpenWebUI 内置]"
        elif tool_type == "external" or tool_id.startswith("server:"):
            tool_group_name = tool_dict.get("_tool_group_name")
            tool_group_desc = tool_dict.get("_tool_group_description")
            server_id = (
                tool_id.replace("server:", "").split("|")[0]
                if tool_id.startswith("server:")
                else tool_id
            )

            if tool_group_name:
                group_prefix = (
                    f"[工具服务器: {tool_group_name} - {tool_group_desc}]"
                    if tool_group_desc
                    else f"[工具服务器: {tool_group_name}]"
                )
            else:
                group_prefix = f"[工具服务器: {server_id}]"
        else:
            tool_group_name = tool_dict.get("_tool_group_name")
            tool_group_desc = tool_dict.get("_tool_group_description")

            if tool_group_name:
                group_prefix = (
                    f"[用户工具: {tool_group_name} - {tool_group_desc}]"
                    if tool_group_desc
                    else f"[用户工具: {tool_group_name}]"
                )
            else:
                group_prefix = f"[用户工具: {tool_id}]" if tool_id else "[用户工具]"

        if sanitized_tool_name != tool_name:
            tool_description = f"{group_prefix} 函数 '{tool_name}': {tool_description}"
        else:
            tool_description = f"{group_prefix} {tool_description}"

        async def _tool(params):
            payload = (
                params.model_dump(exclude_unset=True)
                if hasattr(params, "model_dump")
                else {}
            )
            return await tool_callable(**payload)

        _tool.__name__ = sanitized_tool_name
        _tool.__doc__ = tool_description

        return define_tool(
            name=sanitized_tool_name,
            description=tool_description,
            params_type=ParamsModel,
        )(_tool)

    def _build_openwebui_request(self, user_data: Optional[dict] = None):
        """构建一个最小的 request 模拟对象用于 OpenWebUI 工具加载。"""
        app_state = SimpleNamespace(
            config=SimpleNamespace(
                TOOL_SERVER_CONNECTIONS=(
                    TOOL_SERVER_CONNECTIONS.value
                    if hasattr(TOOL_SERVER_CONNECTIONS, "value")
                    else []
                )
            ),
            TOOLS={},
        )
        app = SimpleNamespace(state=app_state)

        def url_path_for(name: str, **path_params):
            return f"/mock/path/{name}"

        app.url_path_for = url_path_for

        request = SimpleNamespace(
            app=app,
            cookies={},
            state=SimpleNamespace(token=SimpleNamespace(credentials="")),
        )
        if user_data and user_data.get("token"):
            request.state.token.credentials = user_data["token"]
        return request

    async def _load_openwebui_tools(self, __user__=None, __event_call__=None):
        """加载 OpenWebUI 工具并转换为 Copilot SDK 工具。"""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        if not user_data:
            return []

        user_id = user_data.get("id") or user_data.get("user_id")
        if not user_id:
            return []

        try:
            from open_webui.models.users import Users

            user = Users.get_user_by_id(user_id)
            if not user:
                return []
        except:
            return []

        # 1. 用户自定义工具
        tool_items = Tools.get_tools_by_user_id(user_id, permission="read")
        tool_ids = [tool.id for tool in tool_items] if tool_items else []

        # 2. 工具服务器工具
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            for server in TOOL_SERVER_CONNECTIONS.value:
                if server.get("type") == "openapi":
                    server_id = server.get("id")
                    if server_id:
                        tool_ids.append(f"server:{server_id}")

        request = self._build_openwebui_request(user_data)
        extra_params = {
            "__request__": request,
            "__user__": user_data,
            "__event_call__": __event_call__,
        }

        tools_dict = {}
        if tool_ids:
            try:
                tools_dict = await get_openwebui_tools(
                    request, tool_ids, user, extra_params
                )
            except Exception as e:
                await self._emit_debug_log(f"获取自定义工具出错: {e}", __event_call__)

        # 内置工具
        try:
            builtin_tools = get_builtin_tools(
                request,
                {"__user__": user_data},
                model={
                    "info": {
                        "meta": {
                            "capabilities": {
                                "web_search": True,
                                "image_generation": True,
                            }
                        }
                    }
                },
            )
            if builtin_tools:
                tools_dict.update(builtin_tools)
        except Exception as e:
            await self._emit_debug_log(f"获取内置工具出错: {e}", __event_call__)

        if not tools_dict:
            return []

        server_metadata_cache = {}
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            for server in TOOL_SERVER_CONNECTIONS.value:
                sid = server.get("id") or server.get("info", {}).get("id")
                if sid:
                    info = server.get("info", {})
                    server_metadata_cache[sid] = {
                        "name": info.get("name") or sid,
                        "description": info.get("description", ""),
                    }

        converted_tools = []
        for tool_name, tool_def in tools_dict.items():
            try:
                # 尝试丰富元数据
                tool_id = tool_def.get("tool_id", "")
                if tool_id.startswith("server:"):
                    sid = tool_id.replace("server:", "").split("|")[0]
                    if sid in server_metadata_cache:
                        tool_def["_tool_group_name"] = server_metadata_cache[sid].get(
                            "name"
                        )
                        tool_def["_tool_group_description"] = server_metadata_cache[
                            sid
                        ].get("description")

                converted_tools.append(
                    self._convert_openwebui_tool(tool_name, tool_def)
                )
            except Exception as e:
                await self._emit_debug_log(
                    f"转换 OpenWebUI 工具 '{tool_name}' 失败: {e}",
                    __event_call__,
                )

        return converted_tools

    def _parse_mcp_servers(self) -> Optional[dict]:
        """
        从 OpenWebUI TOOL_SERVER_CONNECTIONS 动态加载 MCP 服务器配置。
        返回兼容 CopilotClient 的 mcp_servers 字典。
        """
        if not self.valves.ENABLE_MCP_SERVER:
            return None

        # 检查缓存
        if self.valves.ENABLE_TOOL_CACHE and self._mcp_server_cache is not None:
            return self._mcp_server_cache

        mcp_servers = {}

        # 遍历 OpenWebUI 工具服务器连接
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            connections = TOOL_SERVER_CONNECTIONS.value
        else:
            connections = []

        for conn in connections:
            if conn.get("type") == "mcp":
                info = conn.get("info", {})
                # 使用 info 中的 ID 或自动生成
                raw_id = info.get("id", f"mcp-server-{len(mcp_servers)}")

                # 净化 server_id (使用与工具相同的逻辑)
                server_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id)
                if not server_id or re.match(r"^[_.-]+$", server_id):
                    hash_suffix = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:8]
                    server_id = f"server_{hash_suffix}"

                url = conn.get("url")
                if not url:
                    continue

                # 构建 Header (处理认证)
                headers = {}
                auth_type = conn.get("auth_type", "bearer")
                key = conn.get("key", "")

                if auth_type == "bearer" and key:
                    headers["Authorization"] = f"Bearer {key}"
                elif auth_type == "basic" and key:
                    headers["Authorization"] = f"Basic {key}"

                # 合并自定义 headers
                custom_headers = conn.get("headers", {})
                if isinstance(custom_headers, dict):
                    headers.update(custom_headers)

                # 获取过滤配置
                mcp_config = conn.get("config", {})
                function_filter = mcp_config.get("function_name_filter_list", "")

                allowed_tools = ["*"]
                if function_filter:
                    if isinstance(function_filter, str):
                        allowed_tools = [
                            f.strip() for f in function_filter.split(",") if f.strip()
                        ]
                    elif isinstance(function_filter, list):
                        allowed_tools = function_filter

                mcp_servers[server_id] = {
                    "type": "http",
                    "url": url,
                    "headers": headers,
                    "tools": allowed_tools,
                }

        # 更新缓存
        if self.valves.ENABLE_TOOL_CACHE:
            self._mcp_server_cache = mcp_servers

        return mcp_servers if mcp_servers else None

    def _build_session_config(
        self,
        chat_id: Optional[str],
        real_model_id: str,
        custom_tools: List[Any],
        system_prompt_content: Optional[str],
        is_streaming: bool,
    ):
        """构建 Copilot SDK 的 SessionConfig"""
        # 处理无限会话配置
        from copilot.types import SessionConfig, InfiniteSessionConfig

        infinite_session_config = None
        if self.valves.INFINITE_SESSION:
            infinite_session_config = InfiniteSessionConfig(
                enabled=True,
                background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
                buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
            )

        # 始终包含格式化指南（默认开启）
        system_parts = []
        if system_prompt_content:
            system_parts.append(system_prompt_content)
        system_parts.append(FORMATTING_GUIDELINES)

        # 始终使用 'replace' 模式以确保完全控制并避免重复
        system_message_config = {
            "mode": "replace",
            "content": "\n".join(system_parts),
        }

        # 准备基础参数
        session_params = {
            "session_id": chat_id if chat_id else None,
            "model": real_model_id,
            "streaming": is_streaming,
            "tools": custom_tools,
            "system_message": system_message_config,
            "infinite_sessions": infinite_session_config,
        }

        # 注入 MCP 转换器
        mcp_servers = self._parse_mcp_servers()
        if mcp_servers:
            session_params["mcp_servers"] = mcp_servers

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

    def _apply_formatting_hint(self, prompt: str) -> str:
        """返回原始提示词（已移除格式化提示）"""
        return prompt

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
        debug_enabled: bool = False,
    ) -> Tuple[Optional[str], str]:
        """从 metadata/模型 DB/body/messages 提取系统提示词"""
        system_prompt_content: Optional[str] = None
        system_prompt_source = ""

        # 0) body.get("system_prompt") - Explicit Override (Highest Priority)
        if hasattr(body, "get") and body.get("system_prompt"):
            system_prompt_content = body.get("system_prompt")
            system_prompt_source = "body_explicit_system_prompt"
            await self._emit_debug_log(
                f"从显式 body 字段提取了系统提示词（长度: {len(system_prompt_content)}）",
                __event_call__,
                debug_enabled=debug_enabled,
            )

        # 1) metadata.model.params.system
        if not system_prompt_content:
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
                            debug_enabled=debug_enabled,
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
                                    f"成功！使用 ID 从模型数据库中提取了系统提示词: {mid}（长度: {len(system_prompt_content)}）",
                                    __event_call__,
                                    debug_enabled=debug_enabled,
                                )
                                break
            except Exception as e:
                await self._emit_debug_log(
                    f"从模型数据库提取系统提示词失败: {e}",
                    __event_call__,
                    debug_enabled=debug_enabled,
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

    async def _emit_debug_log(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        """在 DEBUG 开启时将日志输出到前端控制台。"""
        should_log = (
            debug_enabled
            if debug_enabled is not None
            else getattr(self.valves, "DEBUG", False)
        )
        if not should_log:
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

    def _emit_debug_log_sync(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        """在非异步上下文中输出调试日志。"""
        should_log = (
            debug_enabled
            if debug_enabled is not None
            else getattr(self.valves, "DEBUG", False)
        )
        if not should_log:
            return

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                self._emit_debug_log(message, __event_call__, debug_enabled=True)
            )
        except RuntimeError:
            logger.debug(f"[Copilot Pipe] {message}")

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
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __event_call__=None,
        debug_enabled: bool = False,
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
                f"提取到 ChatID: {chat_id} (来源: {source})",
                __event_call__,
                debug_enabled=debug_enabled,
            )
        else:
            # 如果还是没找到，记录一下 body 的键，方便排查
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log_sync(
                f"警告: 未能提取到 ChatID。Body 键: {keys}",
                __event_call__,
                debug_enabled=debug_enabled,
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
                    # 格式化显示名称
                    clean_id = self._clean_model_id(m_id)
                    if multiplier == 0:
                        display_name = f"-🔥 {clean_id} (0x)"
                    else:
                        display_name = f"-{clean_id} ({multiplier}x)"

                    models_with_info.append(
                        {
                            "id": f"{self.id}-{m_id}",  # Keep original prefix logic for ID
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
                        "id": f"{self.id}-gpt-5-mini",
                        "name": f"GitHub Copilot (gpt-5-mini)",
                    }
                ]
            finally:
                await client.stop()
        except Exception as e:
            await self._emit_debug_log(f"Pipes Error: {e}")
            return [
                {
                    "id": f"{self.id}-gpt-5-mini",
                    "name": f"GitHub Copilot (gpt-5-mini)",
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

    async def _update_copilot_cli(
        self, cli_path, __event_call__=None, debug_enabled: bool = False
    ):
        """如果已配置，则异步检查 Copilot CLI 更新。"""
        if not self.valves.AUTO_UPDATE:
            return

        # 检查更新频率（每 24 小时一次）
        now = time.time()
        if now - self._last_update_check < 86400:
            return

        self._last_update_check = now

        try:
            self._emit_debug_log_sync(
                "正在检查 Copilot CLI 更新...",
                __event_call__,
                debug_enabled=debug_enabled,
            )

            # 我们创建一个子进程来运行更新
            process = await asyncio.create_subprocess_exec(
                cli_path,
                "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._emit_debug_log_sync(
                    "Copilot CLI 更新检查完成",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
            else:
                self._emit_debug_log_sync(
                    f"Copilot CLI 更新失败: {stderr.decode()}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

        except Exception as e:
            self._emit_debug_log_sync(
                f"CLI 更新任务异常: {e}", __event_call__, debug_enabled=debug_enabled
            )

    def _setup_env(self, __event_call__=None, debug_enabled: bool = False):
        """初始化环境变量并验证 Copilot CLI。"""
        if self._env_setup_done:
            return

        # 1. 认证相关的环境变量
        if self.valves.GH_TOKEN:
            os.environ["GH_TOKEN"] = self.valves.GH_TOKEN
            os.environ["GITHUB_TOKEN"] = self.valves.GH_TOKEN
        else:
            self._emit_debug_log_sync(
                "警告: 未设置 GH_TOKEN。", __event_call__, debug_enabled=debug_enabled
            )

        # 禁用 CLI 自动更新以确保版本一致性
        os.environ["COPILOT_AUTO_UPDATE"] = "false"
        self._emit_debug_log_sync(
            "已禁用 CLI 自动更新 (COPILOT_AUTO_UPDATE=false)",
            __event_call__,
            debug_enabled=debug_enabled,
        )

        # 2. CLI 路径发现
        cli_path = "/usr/local/bin/copilot"
        if os.environ.get("COPILOT_CLI_PATH"):
            cli_path = os.environ["COPILOT_CLI_PATH"]

        target_version = self.valves.COPILOT_CLI_VERSION.strip()
        found = False
        current_version = None

        def get_cli_version(path):
            try:
                output = (
                    subprocess.check_output(
                        [path, "--version"], stderr=subprocess.STDOUT
                    )
                    .decode()
                    .strip()
                )
                import re

                match = re.search(r"(\d+\.\d+\.\d+)", output)
                return match.group(1) if match else output
            except Exception:
                return None

        # 检查现有版本
        if os.path.exists(cli_path):
            found = True
            current_version = get_cli_version(cli_path)

        if not found:
            sys_path = shutil.which("copilot")
            if sys_path:
                cli_path = sys_path
                found = True
                current_version = get_cli_version(cli_path)

        if not found:
            pkg_path = os.path.join(os.path.dirname(__file__), "bin", "copilot")
            if os.path.exists(pkg_path):
                cli_path = pkg_path
                found = True
                current_version = get_cli_version(cli_path)

        # 3. 安装/更新逻辑
        should_install = not found
        install_reason = "CLI 未找到"
        if found and target_version:
            norm_target = target_version.lstrip("v")
            norm_current = current_version.lstrip("v") if current_version else ""

            # 只有当目标版本大于当前版本时才安装
            try:
                from packaging.version import parse as parse_version

                if parse_version(norm_target) > parse_version(norm_current):
                    should_install = True
                    install_reason = f"需要升级 ({current_version} -> {target_version})"
                elif parse_version(norm_target) < parse_version(norm_current):
                    self._emit_debug_log_sync(
                        f"当前版本 ({current_version}) 比指定版本 ({target_version}) 更新。跳过降级。",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
            except Exception as e:
                # 如果 packaging 不可用，回退到字符串比较
                if norm_target != norm_current:
                    should_install = True
                    install_reason = (
                        f"版本不匹配 ({current_version} != {target_version})"
                    )

        if should_install:
            self._emit_debug_log_sync(
                f"正在安装/更新 Copilot CLI: {install_reason}...",
                __event_call__,
                debug_enabled=debug_enabled,
            )
            try:
                env = os.environ.copy()
                if target_version:
                    env["VERSION"] = target_version
                subprocess.run(
                    "curl -fsSL https://gh.io/copilot-install | bash",
                    shell=True,
                    check=True,
                    env=env,
                )
                # 重新验证
                current_version = get_cli_version(cli_path)
            except Exception as e:
                self._emit_debug_log_sync(
                    f"CLI 安装失败: {e}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

        # 4. 完成初始化
        os.environ["COPILOT_CLI_PATH"] = cli_path
        self._env_setup_done = True
        self._emit_debug_log_sync(
            f"环境设置完成。CLI 路径: {cli_path} (版本: {current_version})",
            __event_call__,
            debug_enabled=debug_enabled,
        )
        self._sync_mcp_config(__event_call__, debug_enabled=debug_enabled)

    def _process_images(
        self, messages, __event_call__=None, debug_enabled: bool = False
    ):
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
                                f"Image processed: {file_path}",
                                __event_call__,
                                debug_enabled=debug_enabled,
                            )
                        except Exception as e:
                            self._emit_debug_log_sync(
                                f"Image error: {e}",
                                __event_call__,
                                debug_enabled=debug_enabled,
                            )
        else:
            text_content = str(content)
        return text_content, attachments

    # ==================== 内部实现 ====================
    # _pipe_impl() 包含主请求处理逻辑。
    # ================================================
    def _sync_copilot_config(self, reasoning_effort: str, __event_call__=None):
        """
        如果设置了 REASONING_EFFORT，则动态更新 ~/.copilot/config.json。
        这提供了一个回退机制，以防 API 注入被服务器忽略。
        """
        if not reasoning_effort:
            return

        effort = reasoning_effort

        # 检查模型是否支持 xhigh
        # 目前只有 gpt-5.2-codex 支持 xhigh
        if effort == "xhigh":
            # 简单检查，使用默认模型 ID
            if (
                "gpt-5.2-codex"
                not in self._collect_model_ids(
                    body={},
                    request_model=self.id,
                    real_model_id=None,
                )[0].lower()
            ):
                # 如果不支持则回退到 high
                effort = "high"

        try:
            # 目标标准路径 ~/.copilot/config.json
            config_path = os.path.expanduser("~/.copilot/config.json")
            config_dir = os.path.dirname(config_path)

            # 仅当目录存在时才继续（避免在路径错误时创建垃圾文件）
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

            # 如果有变化则更新
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

    async def _update_copilot_cli(
        self, cli_path, __event_call__=None, debug_enabled: bool = False
    ):
        """如果已配置，则异步检查 Copilot CLI 更新。"""
        import time

        if not self.valves.AUTO_UPDATE:
            return

        # 检查更新频率（每 24 小时一次）
        now = time.time()
        if now - self._last_update_check < 86400:
            return

        self._last_update_check = now

        try:
            self._emit_debug_log_sync(
                "正在检查 Copilot CLI 更新...",
                __event_call__,
                debug_enabled=debug_enabled,
            )

            # 我们创建一个子进程来运行更新
            process = await asyncio.create_subprocess_exec(
                cli_path,
                "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self._emit_debug_log_sync(
                    "Copilot CLI 更新检查完成",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
            else:
                self._emit_debug_log_sync(
                    f"Copilot CLI 更新失败: {stderr.decode()}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

        except Exception as e:
            self._emit_debug_log_sync(
                f"CLI 更新任务异常: {e}", __event_call__, debug_enabled=debug_enabled
            )

    async def _pipe_impl(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        # 1. 首先确定有效的调试设置
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

        effective_debug = self.valves.DEBUG or user_valves.DEBUG

        # 2. 初始化环境
        self._setup_env(__event_call__, debug_enabled=effective_debug)

        cwd = self._get_workspace_dir()
        await self._emit_debug_log(
            f"Agent 工作目录: {cwd}", __event_call__, debug_enabled=effective_debug
        )

        # 确定有效的 BYOK 设置
        byok_api_key = user_valves.BYOK_API_KEY or self.valves.BYOK_API_KEY
        byok_bearer_token = (
            user_valves.BYOK_BEARER_TOKEN or self.valves.BYOK_BEARER_TOKEN
        )
        byok_base_url = user_valves.BYOK_BASE_URL or self.valves.BYOK_BASE_URL
        byok_active = bool(byok_base_url and (byok_api_key or byok_bearer_token))

        # 检查 GH_TOKEN 或 BYOK 配置
        gh_token = user_valves.GH_TOKEN or self.valves.GH_TOKEN
        if not gh_token and not byok_active:
            return "Error: 请在 Valves 中配置 GH_TOKEN 或 BYOK 设置。"

        # 解析模型
        request_model = body.get("model", "")
        real_model_id = request_model

        # 确定推理强度
        effective_reasoning_effort = (
            user_valves.REASONING_EFFORT
            if user_valves.REASONING_EFFORT
            else self.valves.REASONING_EFFORT
        )

        # 确定显示思考过程
        show_thinking = (
            user_valves.SHOW_THINKING
            if user_valves.SHOW_THINKING is not None
            else self.valves.SHOW_THINKING
        )

        # 1. 确定实际使用的模型 ID
        resolved_id = request_model
        model_source_type = "selected"

        if __metadata__ and __metadata__.get("base_model_id"):
            resolved_id = __metadata__.get("base_model_id", "")
            model_source_type = "base"

        # 2. 去除前缀 (内联逻辑)
        real_model_id = resolved_id
        if "." in real_model_id:
            real_model_id = real_model_id.split(".", 1)[-1]
        if real_model_id.startswith(f"{self.id}-"):
            real_model_id = real_model_id[len(f"{self.id}-") :]
        if real_model_id.startswith("copilot - "):
            real_model_id = real_model_id[10:]

        # 3. 记录解析结果
        if real_model_id != request_model:
            log_msg = (
                f"使用 {model_source_type} 模型: {real_model_id} "
                f"(清洗自 '{resolved_id}')"
            )
            await self._emit_debug_log(
                log_msg,
                __event_call__,
                debug_enabled=effective_debug,
            )

        messages = body.get("messages", [])
        if not messages:
            return "没有消息。"

        # 获取 Chat ID
        chat_ctx = self._get_chat_context(
            body, __metadata__, __event_call__, debug_enabled=effective_debug
        )
        chat_id = chat_ctx.get("chat_id")

        # 提取系统提示词
        system_prompt_content, system_prompt_source = await self._extract_system_prompt(
            body,
            messages,
            request_model,
            real_model_id,
            __event_call__,
            debug_enabled=effective_debug,
        )

        if system_prompt_content:
            preview = system_prompt_content[:60].replace("\n", " ")
            await self._emit_debug_log(
                f"系统提示词来源: {system_prompt_source} (长度: {len(system_prompt_content)})",
                __event_call__,
                debug_enabled=effective_debug,
            )

        is_streaming = body.get("stream", False)
        await self._emit_debug_log(
            f"流式请求: {is_streaming}",
            __event_call__,
            debug_enabled=effective_debug,
        )

        last_text, attachments = self._process_images(
            messages, __event_call__, debug_enabled=effective_debug
        )

        # 判断 BYOK 模型逻辑
        import re

        is_byok_model = False
        model_display_name = ""

        # 获取模型名称
        body_metadata = body.get("metadata", {})
        if not isinstance(body_metadata, dict):
            body_metadata = {}

        meta_model = body_metadata.get("model", {})
        if isinstance(meta_model, dict):
            model_display_name = meta_model.get("name", "")

        if not model_display_name and __metadata__:
            model_obj = __metadata__.get("model", {})
            if isinstance(model_obj, dict):
                model_display_name = model_obj.get("name", "")
            elif isinstance(model_obj, str):
                model_display_name = model_obj
            
            if not model_display_name:
                model_display_name = __metadata__.get("model_name", "") or __metadata__.get("name", "")

        if model_display_name:
            # 这里的正则已更新支持中文括号
            has_multiplier = bool(re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", model_display_name))
            
            # 逻辑：如果自定义模型名称没有倍率，检查 Base Model 的官方名称
            if not has_multiplier:
                # 确保缓存已填充
                if not self._model_cache:
                    try:
                        await self.pipes()
                    except:
                        pass
                
                # 在缓存中查找 base model 以检查其官方名称
                cached_model = next(
                    (m for m in self._model_cache if m.get("raw_id") == real_model_id or m.get("id") == real_model_id or m.get("id") == f"{self.id}-{real_model_id}"), 
                    None
                )
                
                if cached_model:
                    cached_name = cached_model.get("name", "")
                    # 这里的正则也已更新支持中文括号
                    if re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", cached_name):
                        has_multiplier = True
                        await self._emit_debug_log(
                            f"修正：在 Base Model 名称 '{cached_name}' 中发现倍率信息 (自定义模型: '{model_display_name}')。视为标准 Copilot 模型。",
                            __event_call__,
                            debug_enabled=effective_debug,
                        )

            is_byok_model = not has_multiplier and byok_active
            await self._emit_debug_log(
                f"BYOK 检测 (通过显示名称): '{model_display_name}' -> 有倍率={has_multiplier}, 是BYOK={is_byok_model}",
                __event_call__,
                debug_enabled=effective_debug,
            )
        else:
            # 缓存回退逻辑
            if not self._model_cache:
                try:
                    await self.pipes()
                except:
                    pass

            base_model_id_from_meta = __metadata__.get("base_model_id", "") if __metadata__ else ""
            lookup_model_id = base_model_id_from_meta if base_model_id_from_meta else request_model

            model_info = next(
                (m for m in (self._model_cache or []) if m["id"] == lookup_model_id),
                None,
            )

            if model_info:
                if "source" in model_info:
                    is_byok_model = model_info["source"] == "byok"
                else:
                    model_name = model_info.get("name", "")
                    has_multiplier = bool(re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", model_name))
                    is_byok_model = not has_multiplier and byok_active
            else:
                if byok_active:
                    if not gh_token:
                        is_byok_model = True
                    elif real_model_id.startswith("copilot-"):
                        is_byok_model = False
                    elif real_model_id not in self._standard_model_ids:
                        is_byok_model = True
            
            await self._emit_debug_log(
                f"BYOK 检测 (通过启发式): model_id='{real_model_id}', byok_active={byok_active} -> is_byok={is_byok_model}",
                __event_call__,
                debug_enabled=effective_debug,
            )

        # 仅针对标准 Copilot 模型同步配置
        if not is_byok_model:
            self._sync_copilot_config(effective_reasoning_effort, __event_call__)

        # 初始化客户端
        client = CopilotClient(self._build_client_config(body))
        should_stop_client = True
        try:
            await client.start()

            custom_tools = await self._initialize_custom_tools(
                __user__=__user__, __event_call__=__event_call__
            )
            if custom_tools:
                tool_names = [t.name for t in custom_tools]
                await self._emit_debug_log(
                    f"启用 {len(custom_tools)} 个工具 (自定义/内置)",
                    __event_call__,
                )

            mcp_servers = self._parse_mcp_servers()
            mcp_server_names = list(mcp_servers.keys()) if mcp_servers else []
            if mcp_server_names:
                await self._emit_debug_log(
                    f"🔌 MCP 服务器已配置: {mcp_server_names}",
                    __event_call__,
                )
            else:
                await self._emit_debug_log(
                    "ℹ️ 未发现 MCP 工具服务器。",
                    __event_call__,
                )

            session = None
            is_new_session = True

            provider_config = None
            if is_byok_model:
                byok_type = (user_valves.BYOK_TYPE or self.valves.BYOK_TYPE).lower()
                if byok_type not in ["openai", "anthropic"]:
                    byok_type = "openai"
                
                byok_wire_api = user_valves.BYOK_WIRE_API or self.valves.BYOK_WIRE_API

                provider_config = {
                    "type": byok_type,
                    "wire_api": byok_wire_api,
                    "base_url": byok_base_url,
                }
                if byok_api_key:
                    provider_config["api_key"] = byok_api_key
                if byok_bearer_token:
                    provider_config["bearer_token"] = byok_bearer_token

            if chat_id:
                try:
                    resume_params = {
                        "model": real_model_id,
                        "streaming": is_streaming,
                        "tools": custom_tools,
                        "available_tools": ([t.name for t in custom_tools] if custom_tools else None),
                    }
                    if mcp_servers:
                        resume_params["mcp_servers"] = mcp_servers

                    system_parts = []
                    if system_prompt_content:
                        system_parts.append(system_prompt_content.strip())
                    system_parts.append(FORMATTING_GUIDELINES)
                    final_system_msg = "\n".join(system_parts)

                    resume_params["system_message"] = {
                        "mode": "replace",
                        "content": final_system_msg,
                    }

                    if provider_config:
                        resume_params["provider"] = provider_config
                        await self._emit_debug_log(
                            f"包含 BYOK 提供商配置: type={provider_config.get('type')}",
                            __event_call__,
                            debug_enabled=effective_debug,
                        )

                    session = await client.resume_session(chat_id, resume_params)
                    await self._emit_debug_log(
                        f"成功恢复会话 {chat_id}，模型: {real_model_id}",
                        __event_call__,
                    )
                    is_new_session = False
                except Exception as e:
                    await self._emit_debug_log(
                        f"会话 {chat_id} 未找到或恢复失败 ({str(e)})，正在创建新会话。",
                        __event_call__,
                    )

            if session is None:
                is_new_session = True
                
                from copilot.types import SessionConfig, InfiniteSessionConfig
                
                infinite_session_config = None
                if self.valves.INFINITE_SESSION:
                    infinite_session_config = InfiniteSessionConfig(
                        enabled=True,
                        background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
                        buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
                    )

                system_parts = []
                if system_prompt_content:
                    system_parts.append(system_prompt_content.strip())
                system_parts.append(FORMATTING_GUIDELINES)
                final_system_msg = "\n".join(system_parts)

                session_params = {
                    "session_id": chat_id if chat_id else None,
                    "model": real_model_id,
                    "streaming": is_streaming,
                    "tools": custom_tools,
                    "available_tools": [t.name for t in custom_tools] if custom_tools else None,
                    "system_message": {
                        "mode": "replace",
                        "content": final_system_msg,
                    },
                    "infinite_sessions": infinite_session_config,
                    "working_directory": self._get_workspace_dir(),
                }

                if provider_config:
                    session_params["provider"] = provider_config
                
                if mcp_servers:
                    session_params["mcp_servers"] = mcp_servers

                session_config = SessionConfig(**session_params)

                await self._emit_debug_log(
                    f"注入系统提示词到新会话 (长度: {len(final_system_msg)})",
                    __event_call__,
                )

                session = await client.create_session(config=session_config)

                model_type_label = "BYOK" if is_byok_model else "Copilot"
                await self._emit_debug_log(
                    f"新 {model_type_label} 会话已创建。选择: '{request_model}', 有效 ID: '{real_model_id}'",
                    __event_call__,
                    debug_enabled=effective_debug,
                )

            prompt = last_text
            await self._emit_debug_log(
                f"发送提示词 ({len(prompt)} 字符) 给 Agent...",
                __event_call__,
            )

            send_payload = {"prompt": prompt, "mode": "immediate"}
            if attachments:
                send_payload["attachments"] = attachments

            if body.get("stream", False):
                init_msg = ""
                if effective_debug:
                    init_msg = (
                        f"> [Debug] Agent 工作目录: {self._get_workspace_dir()}\n"
                    )
                    if mcp_server_names:
                        init_msg += f"> [Debug] 🔌 已连接 MCP 服务器: {', '.join(mcp_server_names)}\n"

                should_stop_client = False
                return self.stream_response(
                    client,
                    session,
                    send_payload,
                    init_msg,
                    __event_call__,
                    reasoning_effort=effective_reasoning_effort,
                    show_thinking=show_thinking,
                    debug_enabled=effective_debug,
                )
            else:
                try:
                    response = await session.send_and_wait(send_payload)
                    return response.data.content if response else "无响应。"
                finally:
                    if not chat_id:
                        try:
                            await session.destroy()
                        except:
                            pass
        except Exception as e:
            await self._emit_debug_log(
                f"请求错误: {e}", __event_call__, debug_enabled=effective_debug
            )
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
        debug_enabled: bool = False,
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
