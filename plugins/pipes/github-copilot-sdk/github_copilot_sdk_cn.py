"""
title: GitHub Copilot SDK 官方管道
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
description: 集成 GitHub Copilot SDK。支持动态模型、多选提供商、流式输出、多模态 input、无限会话及前端调试日志。
version: 0.6.1
requirements: github-copilot-sdk==0.1.23
"""

import os
import re
import json
import base64
import tempfile
import asyncio
import logging
import shutil
import subprocess
import hashlib
import aiohttp
from pathlib import Path
from typing import Optional, Union, AsyncGenerator, List, Any, Dict, Literal, Tuple
from types import SimpleNamespace
from pydantic import BaseModel, Field, create_model

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
    "- **文件系统访问**：你以 **root** 身份运行。你对 **整个容器文件系统** 拥有读取权限。但是，你应仅写入工作区目录。\n"
    "- **原生 Python 环境**：你运行在一个丰富的 Python 环境中，已经包含了 OpenWebUI 的所有依赖库。\n"
    "\n"
    "**界面能力 (OpenWebUI)：**\n"
    "- **视觉渲染**：你可以并且应该使用高级视觉元素（如 Mermaid 图表、交互式 HTML）来清晰地解释概念。\n"
    "- **内置工具**：OpenWebUI 提供了与内部服务直接交互的原生工具（如笔记、记忆管理）。\n"
    "\n"
    "**格式化与呈现指令：**\n"
    "1. **Markdown & 多媒体**：自由使用粗体、斜体、表格和列表。\n"
    "2. **Mermaid 图表**：请务必使用标准的 ```mermaid 代码块。\n"
    "3. **交互式 HTML/JS**：你可以输出完整的 ```html 代码块（含 CSS/JS），将在 iframe 中渲染。\n"
    "7. **主动与自主**: 你是专家工程师。对于显而易见的步骤，**不要**请求许可。**不要**停下来问“我通过吗？”或“是否继续？”。\n"
    "   - **行为模式**: 分析用户请求 -> 制定计划 -> **立即执行**计划。\n"
    "   - **澄清**: 仅当请求模棱两可或具有高风险（例如破坏性操作）时才提出问题。\n"
    "   - **目标**: 最小化用户摩擦。交付结果，而不是问题。\n"
    "8. **大文件输出管理**: 如果工具执行输出被截断或保存到临时文件 (例如 `/tmp/...`)，**不要**担心。系统会自动将其移动到你的工作区并通知你新的文件名。然后你可以直接读取它。\n"
)


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Access Token (PAT 或 OAuth Token)。用于聊天。",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="启用 OpenWebUI 工具 (包括自定义工具和工具服务器工具)。",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="启用直接 MCP 客户端连接 (建议)。",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="缓存配置以优化性能。",
        )
        REASONING_EFFORT: Literal["low", "medium", "high", "xhigh"] = Field(
            default="medium",
            description="推理强度级别 (low, medium, high, xhigh)。仅影响标准模型。",
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
            description="启用技术调试日志（输出到浏览器控制台）",
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
            description="文件操作受限目录。为空则使用默认路径。",
        )
        COPILOT_CLI_VERSION: str = Field(
            default="0.0.406",
            description="指定强制使用的 Copilot CLI 版本 (例如 '0.0.406')。",
        )
        PROVIDERS: str = Field(
            default="OpenAI, Anthropic, Google",
            description="允许使用的模型提供商 (逗号分隔)。留空则显示所有。",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="排除包含这些关键词的模型（逗号分隔，如：codex, haiku）",
        )
        MAX_MULTIPLIER: float = Field(
            default=1.0,
            description="标准模型允许的最大计费倍率。0 表示仅显示免费模型。",
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
            description="自定义环境变量（JSON 格式）",
        )

        BYOK_TYPE: Literal["openai", "anthropic"] = Field(
            default="openai",
            description="BYOK 供应商类型：openai, anthropic",
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
            description="BYOK Bearer 令牌 (优先级高于 API Key)",
        )
        BYOK_MODELS: str = Field(
            default="",
            description="BYOK 模型列表 (逗号分隔)。",
        )
        BYOK_WIRE_API: Literal["completions", "responses"] = Field(
            default="completions",
            description="BYOK 通信协议：completions, responses",
        )

    class UserValves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="个人 GitHub Token (覆盖全局设置)",
        )
        REASONING_EFFORT: Literal["", "low", "medium", "high", "xhigh"] = Field(
            default="",
            description="推理强度级别覆盖。",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )
        DEBUG: bool = Field(
            default=False,
            description="启用技术调试日志",
        )
        MAX_MULTIPLIER: Optional[float] = Field(
            default=None,
            description="计费倍率覆盖。",
        )
        PROVIDERS: str = Field(
            default="",
            description="允许的提供商覆盖 (逗号分隔)。",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="排除关键词 (支持个人覆盖)。",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="启用 OpenWebUI 工具。",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="启用动态 MCP 服务器加载。",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="启用配置缓存。",
        )
        COMPACTION_THRESHOLD: Optional[float] = Field(
            default=None,
            description="压缩阈值覆盖。",
        )
        BUFFER_THRESHOLD: Optional[float] = Field(
            default=None,
            description="缓冲区阈值覆盖。",
        )

        # BYOK 覆盖
        BYOK_API_KEY: str = Field(default="", description="BYOK API 密钥覆盖")
        BYOK_TYPE: Literal["", "openai", "anthropic"] = Field(
            default="", description="BYOK 类型覆盖"
        )
        BYOK_BASE_URL: str = Field(default="", description="BYOK URL 覆盖")
        BYOK_BEARER_TOKEN: str = Field(default="", description="BYOK Token 覆盖")
        BYOK_MODELS: str = Field(default="", description="BYOK 模型列表覆盖")
        BYOK_WIRE_API: Literal["", "completions", "responses"] = Field(
            default="", description="协议覆盖"
        )

    _model_cache: List[dict] = []
    _standard_model_ids: set = set()
    _tool_cache = None
    _mcp_server_cache = None
    _env_setup_done = False
    _last_update_check = 0

    def __init__(self):
        self.type = "pipe"
        self.id = "copilot"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")

    def __del__(self):
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

    async def pipe(
        self,
        body: dict,
        __metadata__=None,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        return await self._pipe_impl(
            body, __metadata__, __user__, __event_emitter__, __event_call__
        )

    async def _initialize_custom_tools(
        self, __user__=None, __event_call__=None, body: dict = None
    ):
        """基于配置初始化自定义工具"""
        # 1. 确定有效设置 (用户覆盖 > 全局)
        uv = self._get_user_valves(__user__)
        enable_tools = uv.ENABLE_OPENWEBUI_TOOLS
        enable_openapi = uv.ENABLE_OPENAPI_SERVER
        enable_cache = uv.ENABLE_TOOL_CACHE

        # 2. 如果所有工具类型都已禁用，立即返回空
        if not enable_tools and not enable_openapi:
            return []

        # 3. 检查缓存
        if enable_cache and self._tool_cache is not None:
            await self._emit_debug_log("ℹ️ 使用缓存的 OpenWebUI 工具。", __event_call__)
            return self._tool_cache

        # 动态加载 OpenWebUI 工具
        tools = await self._load_openwebui_tools(
            __user__=__user__,
            __event_call__=__event_call__,
            body=body,
            enable_tools=enable_tools,
            enable_openapi=enable_openapi,
        )

        # 更新缓存
        if enable_cache:
            self._tool_cache = tools
            await self._emit_debug_log(
                "✅ OpenWebUI 工具已缓存，供后续请求使用。", __event_call__
            )

        return tools

    def _json_schema_to_python_type(self, schema: dict) -> Any:
        if not isinstance(schema, dict):
            return Any
        e = schema.get("enum")
        if e and isinstance(e, list):
            return Literal[tuple(e)]
        t = schema.get("type")
        if isinstance(t, list):
            t = next((x for x in t if x != "null"), t[0])
        if t == "string":
            return str
        if t == "integer":
            return int
        if t == "number":
            return float
        if t == "boolean":
            return bool
        if t == "object":
            return Dict[str, Any]
        if t == "array":
            return List[self._json_schema_to_python_type(schema.get("items", {}))]
        return Any

    def _convert_openwebui_tool(self, n, d, __event_call__=None):
        sn = re.sub(r"[^a-zA-Z0-9_-]", "_", n)
        if not sn or re.match(r"^[_.-]+$", sn):
            sn = f"tool_{hashlib.md5(n.encode()).hexdigest()[:8]}"
        spec = d.get("spec", {})
        props = spec.get("parameters", {}).get("properties", {})
        req = spec.get("parameters", {}).get("required", [])
        fields = {}
        for pn, ps in props.items():
            pt = self._json_schema_to_python_type(ps)
            fields[pn] = (
                pt if pn in req else Optional[pt],
                Field(
                    default=ps.get("default") if pn not in req else ...,
                    description=ps.get("description", ""),
                ),
            )

        async def _tool(p):
            payload = (
                p.model_dump(exclude_unset=True) if hasattr(p, "model_dump") else {}
            )
            return await d.get("callable")(**payload)

        _tool.__name__, _tool.__doc__ = sn, spec.get("description", "") or spec.get(
            "summary", ""
        )
        return define_tool(
            name=sn,
            description=_tool.__doc__,
            params_type=create_model(f"{sn}_Params", **fields),
        )(_tool)

    def _build_openwebui_request(self, user=None, token: str = None):
        cfg = SimpleNamespace()
        for i in PERSISTENT_CONFIG_REGISTRY:
            val = i.value
            if hasattr(val, "value"):
                val = val.value
            setattr(cfg, i.env_name, val)

        if not hasattr(cfg, "TOOL_SERVER_CONNECTIONS"):
            if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
                cfg.TOOL_SERVER_CONNECTIONS = TOOL_SERVER_CONNECTIONS.value
            else:
                cfg.TOOL_SERVER_CONNECTIONS = TOOL_SERVER_CONNECTIONS

        app_state = SimpleNamespace(
            config=cfg,
            TOOLS={},
            TOOL_CONTENTS={},
            FUNCTIONS={},
            FUNCTION_CONTENTS={},
            MODELS={},
            redis=None,
            TOOL_SERVERS=[],
        )

        def url_path_for(name: str, **path_params):
            if name == "get_file_content_by_id":
                return f"/api/v1/files/{path_params.get('id')}/content"
            return f"/mock/{name}"

        req_headers = {
            "user-agent": "Copilot-Pipe",
            "host": "localhost:8080",
            "accept": "*/*",
        }
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        return SimpleNamespace(
            app=SimpleNamespace(state=app_state, url_path_for=url_path_for),
            url=SimpleNamespace(
                path="/api/chat/completions",
                base_url="http://localhost:8080",
                __str__=lambda s: "http://localhost:8080/api/chat/completions",
            ),
            base_url="http://localhost:8080",
            headers=req_headers,
            method="POST",
            cookies={},
            state=SimpleNamespace(
                token=SimpleNamespace(credentials=token if token else ""),
                user=user or {},
            ),
        )

    async def _load_openwebui_tools(
        self,
        __user__=None,
        __event_call__=None,
        body: dict = None,
        enable_tools: bool = True,
        enable_openapi: bool = True,
    ):
        ud = __user__[0] if isinstance(__user__, (list, tuple)) else (__user__ or {})
        uid = ud.get("id") or ud.get("user_id")
        if not uid:
            return []
        u = Users.get_user_by_id(uid)
        if not u:
            return []
        tids = []
        # 1. 获取用户自定义工具 (Python 脚本)
        if enable_tools:
            tool_items = Tools.get_tools_by_user_id(uid, permission="read")
            if tool_items:
                tids.extend([tool.id for tool in tool_items])

        # 2. 获取 OpenAPI 工具服务器工具
        if enable_openapi:
            if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
                tids.extend(
                    [
                        f"server:{s.get('id')}"
                        for s in TOOL_SERVER_CONNECTIONS.value
                        if (
                            s.get("type", "openapi") == "openapi"
                            or s.get("type") is None
                        )
                        and s.get("id")
                    ]
                )

        token = None
        if isinstance(body, dict):
            token = body.get("token")

        req = self._build_openwebui_request(ud, token)
        td = {}

        if tids:
            td = await get_openwebui_tools(
                req,
                tids,
                u,
                {
                    "__request__": req,
                    "__user__": ud,
                    "__event_emitter__": None,
                    "__event_call__": __event_call__,
                    "__chat_id__": None,
                    "__message_id__": None,
                    "__model_knowledge__": [],
                    "__oauth_token__": {"access_token": token} if token else None,
                },
            )

        # 3. 获取内建工具 (网页搜索、内存等)
        if enable_tools:
            try:
                bi = get_builtin_tools(
                    req,
                    {
                        "__user__": ud,
                        "__chat_id__": None,
                        "__message_id__": None,
                    },
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
                if bi:
                    td.update(bi)
            except:
                pass
        return [
            self._convert_openwebui_tool(n, d, __event_call__=__event_call__)
            for n, d in td.items()
        ]

    def _get_user_valves(self, __user__: Optional[dict]) -> "Pipe.UserValves":
        """从 __user__ 上下文中稳健地提取 UserValves。"""
        if not __user__:
            return self.UserValves()

        # 处理列表/元组包装
        user_data = __user__[0] if isinstance(__user__, (list, tuple)) else __user__
        if not isinstance(user_data, dict):
            return self.UserValves()

        raw_valves = user_data.get("valves")
        if isinstance(raw_valves, self.UserValves):
            return raw_valves
        if isinstance(raw_valves, dict):
            try:
                return self.UserValves(**raw_valves)
            except Exception as e:
                logger.warning(f"[Copilot] 解析 UserValves 失败: {e}")
        return self.UserValves()

    def _parse_mcp_servers(self, __event_call__=None) -> Optional[dict]:
        if not self.valves.ENABLE_MCP_SERVER:
            return None
        if self.valves.ENABLE_TOOL_CACHE and self._mcp_server_cache is not None:
            return self._mcp_server_cache
        mcp = {}
        conns = (
            getattr(TOOL_SERVER_CONNECTIONS, "value", [])
            if hasattr(TOOL_SERVER_CONNECTIONS, "value")
            else (
                TOOL_SERVER_CONNECTIONS
                if isinstance(TOOL_SERVER_CONNECTIONS, list)
                else []
            )
        )
        for c in conns:
            if not isinstance(c, dict) or c.get("type") != "mcp":
                continue
            info = c.get("info", {})
            rid = info.get("id") or c.get("id") or f"mcp-{len(mcp)}"
            sid = re.sub(r"[^a-zA-Z0-9-]", "-", str(rid)).lower().strip("-")
            url = c.get("url")
            if not url:
                continue
            mtype = "http"
            if "/sse" in url.lower() or "sse" in str(c.get("config", {})).lower():
                mtype = "sse"
            h = c.get("headers", {})
            at, key = str(c.get("auth_type", "bearer")).lower(), c.get("key", "")
            if key and "Authorization" not in h:
                if at == "bearer":
                    h["Authorization"] = f"Bearer {key}"
                elif at == "basic":
                    h["Authorization"] = (
                        f"Basic {base64.b64encode(key.encode()).decode()}"
                    )
                elif at in ["api_key", "apikey"]:
                    h["X-API-Key"] = key
            ff = c.get("config", {}).get("function_name_filter_list", "")
            allowed = [f.strip() for f in ff.split(",") if f.strip()] if ff else ["*"]
            self._emit_debug_log_sync(
                f"🔌 发现 MCP 节点: {sid} ({mtype.upper()}) | URL: {url}"
            )
            mcp[sid] = {"type": mtype, "url": url, "headers": h, "tools": allowed}
        if self.valves.ENABLE_TOOL_CACHE:
            self._mcp_server_cache = mcp
        return mcp if mcp else None

    async def _emit_debug_log(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        is_debug = (
            debug_enabled
            if debug_enabled is not None
            else getattr(self.valves, "DEBUG", False)
        )
        log_msg = f"[Copilot SDK] {message}"
        if is_debug:
            logger.info(log_msg)
        else:
            logger.debug(log_msg)
        if is_debug and __event_call__:
            try:
                js = f"console.debug('%c[Copilot SDK] ' + {json.dumps(message, ensure_ascii=False)}, 'color: #3b82f6;');"
                await __event_call__({"type": "execute", "data": {"code": js}})
            except:
                pass

    def _emit_debug_log_sync(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        is_debug = (
            debug_enabled
            if debug_enabled is not None
            else getattr(self.valves, "DEBUG", False)
        )
        log_msg = f"[Copilot SDK] {message}"
        if is_debug:
            logger.info(log_msg)
        else:
            logger.debug(log_msg)
        if is_debug and __event_call__:
            try:
                asyncio.get_running_loop().create_task(
                    self._emit_debug_log(message, __event_call__, True)
                )
            except:
                pass

    def _get_provider_name(self, mi: Any) -> str:
        mid = getattr(mi, "id", str(mi)).lower()
        if any(k in mid for k in ["gpt", "codex"]):
            return "OpenAI"
        if "claude" in mid:
            return "Anthropic"
        if "gemini" in mid:
            return "Google"
        p = getattr(mi, "policy", None)
        if p:
            t = str(getattr(p, "terms", "")).lower()
            if "openai" in t:
                return "OpenAI"
            if "anthropic" in t:
                return "Anthropic"
            if "google" in t:
                return "Google"
        return "Unknown"

    def _clean_model_id(self, mid: str) -> str:
        if "." in mid:
            mid = mid.split(".", 1)[-1]
        for p in ["copilot-", "copilot - "]:
            if mid.startswith(p):
                mid = mid[len(p) :]
        return mid

    def _setup_env(self, __event_call__=None, debug_enabled: bool = False):
        if self.__class__._env_setup_done:
            # 即使已完成环境配置，在调试模式下仍同步一次 MCP。
            if debug_enabled:
                self._sync_mcp_config(__event_call__, debug_enabled)
            return

        os.environ["COPILOT_AUTO_UPDATE"] = "false"
        cp = os.environ.get("COPILOT_CLI_PATH", "/usr/local/bin/copilot")
        target = self.valves.COPILOT_CLI_VERSION.strip()

        # 记录检查时间
        from datetime import datetime

        self.__class__._last_update_check = datetime.now().timestamp()

        def gv(p):
            try:
                return re.search(
                    r"(\d+\.\d+\.\d+)",
                    subprocess.check_output(
                        [p, "--version"], stderr=subprocess.STDOUT
                    ).decode(),
                ).group(1)
            except:
                return None

        cv = gv(cp)
        if not cv:
            cp = shutil.which("copilot") or os.path.join(
                os.path.dirname(__file__), "bin", "copilot"
            )
        cv = gv(cp)
        if not cv or (target and target.lstrip("v") > (cv or "")):
            self._emit_debug_log_sync(
                f"正在更新 Copilot CLI 至 {target}...", __event_call__, debug_enabled
            )
            try:
                ev = os.environ.copy()
                if target:
                    ev["VERSION"] = target
                subprocess.run(
                    "curl -fsSL https://gh.io/copilot-install | bash",
                    shell=True,
                    check=True,
                    env=ev,
                )
                cp, cv = "/usr/local/bin/copilot", gv("/usr/local/bin/copilot")
            except:
                pass
        os.environ["COPILOT_CLI_PATH"] = cp
        self.__class__._env_setup_done = True
        self._sync_mcp_config(__event_call__, debug_enabled)

    def _sync_mcp_config(self, __event_call__=None, debug_enabled: bool = False):
        if not self.valves.ENABLE_MCP_SERVER:
            return
        mcp = self._parse_mcp_servers(__event_call__)
        if not mcp:
            return
        try:
            path = os.path.expanduser("~/.copilot/config.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {}
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                except:
                    pass
            if json.dumps(data.get("mcp_servers"), sort_keys=True) != json.dumps(
                mcp, sort_keys=True
            ):
                data["mcp_servers"] = mcp
                with open(path, "w") as f:
                    json.dump(data, f, indent=4)
                self._emit_debug_log_sync(
                    f"已将 {len(mcp)} 个 MCP 节点同步至配置文件",
                    __event_call__,
                    debug_enabled,
                )
        except:
            pass

    def _get_workspace_dir(self, user_id: str = None, chat_id: str = None) -> str:
        """获取具有用户和聊天隔离的有效工作区目录"""
        d = self.valves.WORKSPACE_DIR
        base_cwd = (
            d
            if d
            else (
                "/app/backend/data/copilot_workspace"
                if os.path.exists("/app/backend/data")
                else os.path.join(os.getcwd(), "copilot_workspace")
            )
        )

        cwd = base_cwd
        if user_id:
            safe_user_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))
            cwd = os.path.join(cwd, safe_user_id)
        if chat_id:
            safe_chat_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(chat_id))
            cwd = os.path.join(cwd, safe_chat_id)

        try:
            os.makedirs(cwd, exist_ok=True)
            return cwd
        except Exception as e:
            return base_cwd

    def _process_images(
        self, messages, __event_call__=None, debug_enabled: bool = False
    ):
        if not messages:
            return "", []
        last = messages[-1].get("content", "")
        if not isinstance(last, list):
            return str(last), []
        text, att = "", []
        for item in last:
            if item.get("type") == "text":
                text += item.get("text", "")
            elif item.get("type") == "image_url":
                url = item.get("image_url", {}).get("url", "")
                if url.startswith("data:image"):
                    try:
                        h, e = url.split(",", 1)
                        ext = h.split(";")[0].split("/")[-1]
                        path = os.path.join(self.temp_dir, f"img_{len(att)}.{ext}")
                        with open(path, "wb") as f:
                            f.write(base64.b64decode(e))
                        att.append(
                            {
                                "type": "file",
                                "path": path,
                                "display_name": f"img_{len(att)}",
                            }
                        )
                    except:
                        pass
        return text, att

    async def _fetch_byok_models(self, uv: "Pipe.UserValves" = None) -> List[dict]:
        """从配置的提供商获取 BYOK 模型。"""
        model_list = []
        
        # 确定有效配置 (用户 > 全局)
        effective_base_url = (uv.BYOK_BASE_URL if uv else "") or self.valves.BYOK_BASE_URL
        effective_type = (uv.BYOK_TYPE if uv else "") or self.valves.BYOK_TYPE
        effective_api_key = (uv.BYOK_API_KEY if uv else "") or self.valves.BYOK_API_KEY
        effective_bearer_token = (uv.BYOK_BEARER_TOKEN if uv else "") or self.valves.BYOK_BEARER_TOKEN
        effective_models = (uv.BYOK_MODELS if uv else "") or self.valves.BYOK_MODELS

        if effective_base_url:
            try:
                base_url = effective_base_url.rstrip("/")
                url = f"{base_url}/models"
                headers = {}
                provider_type = effective_type.lower()

                if provider_type == "anthropic":
                    if effective_api_key:
                        headers["x-api-key"] = effective_api_key
                    headers["anthropic-version"] = "2023-06-01"
                else:
                    if effective_bearer_token:
                        headers["Authorization"] = (
                            f"Bearer {effective_bearer_token}"
                        )
                    elif effective_api_key:
                        headers["Authorization"] = f"Bearer {effective_api_key}"

                timeout = aiohttp.ClientTimeout(total=60)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    for attempt in range(3):
                        try:
                            async with session.get(url, headers=headers) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    if (
                                        isinstance(data, dict)
                                        and "data" in data
                                        and isinstance(data["data"], list)
                                    ):
                                        for item in data["data"]:
                                            if isinstance(item, dict) and "id" in item:
                                                model_list.append(item["id"])
                                    elif isinstance(data, list):
                                        for item in data:
                                            if isinstance(item, dict) and "id" in item:
                                                model_list.append(item["id"])
                                    
                                    await self._emit_debug_log(
                                        f"BYOK: 从 {url} 获取了 {len(model_list)} 个模型"
                                    )
                                    break
                                else:
                                    await self._emit_debug_log(
                                        f"BYOK: 获取模型失败 {url} (尝试 {attempt+1}/3). 状态码: {resp.status}"
                                    )
                        except Exception as e:
                            await self._emit_debug_log(f"BYOK: 模型获取错误 (尝试 {attempt+1}/3): {e}")
                        
                        if attempt < 2:
                            await asyncio.sleep(1)

            except Exception as e:
                await self._emit_debug_log(f"BYOK: 设置错误: {e}")

        # 如果自动获取失败，回退到手动配置列表
        if not model_list:
            if effective_models.strip():
                model_list = [
                    m.strip() for m in effective_models.split(",") if m.strip()
                ]
                await self._emit_debug_log(
                    f"BYOK: 使用用户手动配置的 BYOK_MODELS ({len(model_list)} 个模型)."
                )

        return [
            {
                "id": m,
                "name": f"-{self._clean_model_id(m)}",
                "source": "byok",
                "provider": effective_type.capitalize(),
                "raw_id": m,
            }
            for m in model_list
        ]

    def _build_session_config(
        self,
        cid,
        rmid,
        tools,
        sysp,
        ist,
        prov=None,
        eff="medium",
        isr=False,
        cthr=None,
        bthr=None,
        ec=None,
        uid=None,
    ):
        from copilot.types import SessionConfig, InfiniteSessionConfig

        inf = (
            InfiniteSessionConfig(
                enabled=True,
                background_compaction_threshold=cthr
                or self.valves.COMPACTION_THRESHOLD,
                buffer_exhaustion_threshold=bthr or self.valves.BUFFER_THRESHOLD,
            )
            if self.valves.INFINITE_SESSION
            else None
        )
        p = {
            "session_id": cid,
            "model": rmid,
            "streaming": ist,
            "tools": tools,
            "system_message": {
                "content": (sysp.strip() + "\n" if sysp else "")
                + FORMATTING_GUIDELINES
                + (
                    f"\n[会话上下文]\n"
                    f"- **您的隔离工作区**: `{self._get_workspace_dir(uid, cid)}`\n"
                    f"- **活跃会话 ID**: `{cid}`\n"
                    "**关键指令**: 所有文件操作必须在这个上述工作区进行。\n"
                    "- **不要**在 `/tmp` 或其他系统目录创建文件。\n"
                    "- 始终将“当前目录”理解为您的隔离工作区。"
                ),
                "mode": "replace",
            },
            "infinite_sessions": inf,
            "working_directory": self._get_workspace_dir(uid, cid),
        }
        if isr and eff:
            m = next((x for x in self._model_cache if x.get("raw_id") == rmid), None)
            supp = (
                m.get("meta", {})
                .get("capabilities", {})
                .get("supported_reasoning_efforts", [])
                if m
                else []
            )
            p["reasoning_effort"] = (
                (eff if eff in supp else ("high" if "high" in supp else "medium"))
                if supp
                else eff
            )
        if self.valves.ENABLE_MCP_SERVER:
            mcp = self._parse_mcp_servers(ec)
            if mcp:
                p["mcp_servers"], p["available_tools"] = mcp, None
        else:
            p["available_tools"] = [t.name for t in tools] if tools else None
        if prov:
            p["provider"] = prov

        # 注入自动大文件处理钩子
        wd = p.get("working_directory", "")
        p["hooks"] = self._build_session_hooks(cwd=wd, __event_call__=ec)

        return SessionConfig(**p)

    def _build_session_hooks(self, cwd: str, __event_call__=None):
        """
        构建会话生命周期钩子。
        当前实现：
        - on_post_tool_use: 自动将 /tmp 中的大文件复制到工作区
        """

        async def on_post_tool_use(input_data, invocation):
            result = input_data.get("result", "")

            # 检测并移动 /tmp 中保存的大文件
            # 模式: Saved to: /tmp/copilot_result_xxxx.txt
            import re
            import shutil

            # 搜索输出中潜在的 /tmp 文件路径
            # 常见 CLI 模式: "Saved to: /tmp/..." 或仅 "/tmp/..."
            match = re.search(r"(/tmp/[\w\-\.]+)", str(result))
            if match:
                tmp_path = match.group(1)
                if os.path.exists(tmp_path):
                    try:
                        filename = os.path.basename(tmp_path)
                        target_path = os.path.join(cwd, f"auto_output_{filename}")
                        shutil.copy2(tmp_path, target_path)

                        self._emit_debug_log_sync(
                            f"Hook [on_post_tool_use]: 自动将大文件输出从 {tmp_path} 移动到 {target_path}",
                            __event_call__,
                        )

                        return {
                            "additionalContext": (
                                f"\n[系统自动管理] 输出内容过大，最初保存在 {tmp_path}。\n"
                                f"我已经自动将其移动到您的工作区，文件名为: `{os.path.basename(target_path)}`。\n"
                                f"您现在应该对该文件使用 `read_file` 或 `grep` 来访问内容。"
                            )
                        }
                    except Exception as e:
                        self._emit_debug_log_sync(
                            f"Hook [on_post_tool_use] 移动文件错误: {e}",
                            __event_call__,
                        )

            return {}

        return {
            "on_post_tool_use": on_post_tool_use,
        }

    async def _pipe_impl(
        self,
        body,
        __metadata__=None,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        ud = __user__[0] if isinstance(__user__, (list, tuple)) else (__user__ or {})
        uid = ud.get("id") or ud.get("user_id") or "default_user"
        uv = self.UserValves(**(__user__.get("valves", {}) if __user__ else {}))
        debug = self.valves.DEBUG or uv.DEBUG
        self._setup_env(__event_call__, debug)
        byok_active = bool(
            self.valves.BYOK_BASE_URL
            and (
                uv.BYOK_API_KEY
                or self.valves.BYOK_API_KEY
                or self.valves.BYOK_BEARER_TOKEN
            )
        )
        if not self.valves.GH_TOKEN and not byok_active:
            return "Error: 配置缺失。"
        rid = (
            __metadata__.get("base_model_id")
            if __metadata__ and __metadata__.get("base_model_id")
            else body.get("model", "")
        )
        rmid = self._clean_model_id(rid)
        mi = next(
            (x for x in (self._model_cache or []) if x.get("raw_id") == rmid), None
        )
        isr = (
            mi.get("meta", {}).get("capabilities", {}).get("reasoning", False)
            if mi
            else any(k in rmid.lower() for k in ["gpt", "codex"])
        )
        isb = (
            mi.get("source") == "byok"
            if mi
            else (
                not bool(re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", rid)) and byok_active
            )
        )
        cid = str(
            (__metadata__ or {}).get("chat_id")
            or body.get("chat_id")
            or body.get("metadata", {}).get("chat_id", "")
        ).strip()
        sysp, _ = await self._extract_system_prompt(
            body,
            body.get("messages", []),
            body.get("model", ""),
            rmid,
            __event_call__,
            debug,
        )
        text, att = self._process_images(
            body.get("messages", []), __event_call__, debug
        )
        client = CopilotClient(self._build_client_config(body, uid, cid))
        try:
            await client.start()
            tools = await self._initialize_custom_tools(__user__, __event_call__, body)
            prov = (
                {
                    "type": (uv.BYOK_TYPE or self.valves.BYOK_TYPE).lower() or "openai",
                    "wire_api": (uv.BYOK_WIRE_API or self.valves.BYOK_WIRE_API),
                    "base_url": uv.BYOK_BASE_URL or self.valves.BYOK_BASE_URL,
                }
                if isb
                else None
            )
            if prov:
                if uv.BYOK_API_KEY or self.valves.BYOK_API_KEY:
                    prov["api_key"] = uv.BYOK_API_KEY or self.valves.BYOK_API_KEY
                if self.valves.BYOK_BEARER_TOKEN:
                    prov["bearer_token"] = self.valves.BYOK_BEARER_TOKEN
            session = None
            if cid:
                try:
                    rp = {
                        "model": rmid,
                        "streaming": body.get("stream", False),
                        "tools": tools,
                        "system_message": {
                            "mode": "replace",
                            "content": (sysp.strip() + "\n" if sysp else "")
                            + FORMATTING_GUIDELINES,
                        },
                    }
                    if self.valves.ENABLE_MCP_SERVER:
                        mcp = self._parse_mcp_servers(__event_call__)
                        if mcp:
                            rp["mcp_servers"], rp["available_tools"] = mcp, None
                    else:
                        rp["available_tools"] = (
                            [t.name for t in tools] if tools else None
                        )
                    if isr:
                        eff = uv.REASONING_EFFORT or self.valves.REASONING_EFFORT
                        supp = (
                            mi.get("meta", {})
                            .get("capabilities", {})
                            .get("supported_reasoning_efforts", [])
                            if mi
                            else []
                        )
                        rp["reasoning_effort"] = (
                            (
                                eff
                                if eff in supp
                                else ("high" if "high" in supp else "medium")
                            )
                            if supp
                            else eff
                        )
                    if prov:
                        rp["provider"] = prov
                    session = await client.resume_session(cid, rp)
                except:
                    pass
            if not session:
                session = await client.create_session(
                    config=self._build_session_config(
                        cid,
                        rmid,
                        tools,
                        sysp,
                        body.get("stream", False),
                        prov,
                        uv.REASONING_EFFORT or self.valves.REASONING_EFFORT,
                        isr,
                        uv.COMPACTION_THRESHOLD,
                        uv.BUFFER_THRESHOLD,
                        __event_call__,
                        uid,
                    )
                )
            if body.get("stream", False):
                return self.stream_response(
                    client,
                    session,
                    {"prompt": text, "mode": "immediate", "attachments": att},
                    "",
                    __event_call__,
                    uv.REASONING_EFFORT or self.valves.REASONING_EFFORT,
                    uv.SHOW_THINKING,
                    debug,
                )
            else:
                r = await session.send_and_wait(
                    {"prompt": text, "mode": "immediate", "attachments": att}
                )
                return r.data.content if r else "空响应。"
        except Exception as e:
            return f"错误: {e}"
        finally:
            if not body.get("stream"):
                await client.stop()

    async def pipes(self, __user__: Optional[dict] = None) -> List[dict]:
        # 获取用户配置
        uv = self._get_user_valves(__user__)
        token = uv.GH_TOKEN or self.valves.GH_TOKEN

        # 环境初始化 (带有 24 小时冷却时间)
        from datetime import datetime
        now = datetime.now().timestamp()
        if not self.__class__._env_setup_done or (now - self.__class__._last_update_check > 86400):
            self._setup_env(debug_enabled=uv.DEBUG or self.valves.DEBUG, token=token)
        elif token:
            os.environ["GH_TOKEN"] = os.environ["GITHUB_TOKEN"] = token

        # 确定倍率限制
        eff_max = self.valves.MAX_MULTIPLIER
        if uv.MAX_MULTIPLIER is not None:
            eff_max = uv.MAX_MULTIPLIER

        # 确定关键词和提供商过滤
        ex_kw = [k.strip().lower() for k in (self.valves.EXCLUDE_KEYWORDS + "," + uv.EXCLUDE_KEYWORDS).split(",") if k.strip()]
        allowed_p = [p.strip().lower() for p in (uv.PROVIDERS if uv.PROVIDERS else self.valves.PROVIDERS).split(",") if p.strip()]

        # 如果缓存为空，刷新模型列表
        if not self._model_cache:
            byok_models = []
            standard_models = []

            # 1. 获取 BYOK 模型 (优先使用个人设置)
            if ((uv.BYOK_BASE_URL if uv else "") or self.valves.BYOK_BASE_URL) and \
               ((uv.BYOK_API_KEY if uv else "") or self.valves.BYOK_API_KEY or (uv.BYOK_BEARER_TOKEN if uv else "") or self.valves.BYOK_BEARER_TOKEN):
                byok_models = await self._fetch_byok_models(uv=uv)

            # 2. 获取标准 Copilot 模型
            if token:
                c = await self._get_client()
                try:
                    raw_models = await c.list_models()
                    raw = raw_models if isinstance(raw_models, list) else []
                    processed = []
                    
                    for m in raw:
                        try:
                            m_is_dict = isinstance(m, dict)
                            mid = m.get("id") if m_is_dict else getattr(m, "id", str(m))
                            bill = m.get("billing") if m_is_dict else getattr(m, "billing", None)
                            if bill and not isinstance(bill, dict):
                                bill = bill.to_dict() if hasattr(bill, "to_dict") else vars(bill)
                            
                            pol = m.get("policy") if m_is_dict else getattr(m, "policy", None)
                            if pol and not isinstance(pol, dict):
                                pol = pol.to_dict() if hasattr(pol, "to_dict") else vars(pol)
                            
                            if (pol or {}).get("state") == "disabled":
                                continue
                                
                            cap = m.get("capabilities") if m_is_dict else getattr(m, "capabilities", None)
                            vis, reas, ctx, supp = False, False, None, []
                            if cap:
                                if not isinstance(cap, dict):
                                    cap = cap.to_dict() if hasattr(cap, "to_dict") else vars(cap)
                                s = cap.get("supports", {})
                                vis, reas = s.get("vision", False), s.get("reasoning_effort", False)
                                l = cap.get("limits", {})
                                ctx = l.get("max_context_window_tokens")
                            
                            raw_eff = (m.get("supported_reasoning_efforts") if m_is_dict else getattr(m, "supported_reasoning_efforts", [])) or []
                            supp = [str(e).lower() for e in raw_eff if e]
                            mult = (bill or {}).get("multiplier", 1)
                            cid = self._clean_model_id(mid)
                            processed.append({
                                "id": f"{self.id}-{mid}",
                                "name": f"-{cid} ({mult}x)" if mult > 0 else f"-🔥 {cid} (0x)",
                                "multiplier": mult,
                                "raw_id": mid,
                                "source": "copilot",
                                "provider": self._get_provider_name(m),
                                "meta": {
                                    "capabilities": {
                                        "vision": vis,
                                        "reasoning": reas,
                                        "supported_reasoning_efforts": supp,
                                    },
                                    "context_length": ctx,
                                },
                            })
                        except:
                            continue
                            
                    processed.sort(key=lambda x: (x["multiplier"], x["raw_id"]))
                    standard_models = processed
                    self._standard_model_ids = {m["raw_id"] for m in processed}
                except:
                    pass
                finally:
                    await c.stop()

            self._model_cache = standard_models + byok_models

        if not self._model_cache:
            return [{"id": "error", "name": "未找到任何模型。请检查 Token 或 BYOK 配置。"}]

        # 3. 实时过滤结果
        res = []
        for m in self._model_cache:
            # 提供商过滤
            if allowed_p and m.get("provider", "Unknown").lower() not in allowed_p:
                continue
            
            mid, mname = (m.get("raw_id") or m.get("id", "")).lower(), m.get("name", "").lower()
            # 关键词过滤
            if any(kw in mid or kw in mname for kw in ex_kw):
                continue
            
            # 倍率限制 (仅限 Copilot 官方模型)
            if m.get("source") == "copilot":
                if float(m.get("multiplier", 1)) > (float(eff_max) + 0.0001):
                    continue
            
            res.append(m)
            
        return res if res else [{"id": "none", "name": "没有匹配当前过滤条件的模型"}]

    async def stream_response(
        self,
        client,
        session,
        payload,
        init_msg,
        __event_call__,
        effort="",
        show_thinking=True,
        debug=False,
    ) -> AsyncGenerator:
        queue, done, sentinel = asyncio.Queue(), asyncio.Event(), object()
        state = {"thinking_started": False, "content_sent": False}
        has_content = False

        def handler(event):
            etype = (
                event.type.value if hasattr(event.type, "value") else str(event.type)
            )

            def get_attr(a):
                if not hasattr(event, "data") or event.data is None:
                    return None
                return (
                    event.data.get(a)
                    if isinstance(event.data, dict)
                    else getattr(event.data, a, None)
                )

            if etype == "assistant.message_delta":
                delta = (
                    get_attr("delta_content")
                    or get_attr("deltaContent")
                    or get_attr("content")
                )
                if delta:
                    state["content_sent"] = True
                    if state["thinking_started"]:
                        queue.put_nowait("\n</think>\n")
                        state["thinking_started"] = False
                    queue.put_nowait(delta)
            elif etype == "assistant.reasoning_delta":
                delta = (
                    get_attr("reasoning_text")
                    or get_attr("reasoningText")
                    or get_attr("delta_content")
                )
                if delta and not state["content_sent"] and show_thinking:
                    if not state["thinking_started"]:
                        queue.put_nowait("<think>\n")
                        state["thinking_started"] = True
                    queue.put_nowait(delta)
            elif etype == "assistant.usage":
                queue.put_nowait(
                    {
                        "choices": [{"delta": {}, "finish_reason": "stop", "index": 0}],
                        "usage": {
                            "prompt_tokens": get_attr("input_tokens") or 0,
                            "completion_tokens": get_attr("output_tokens") or 0,
                            "total_tokens": get_attr("total_tokens") or 0,
                        },
                    }
                )
            elif etype == "session.idle":
                done.set()
                queue.put_nowait(sentinel)
            elif etype == "session.error":
                queue.put_nowait(f"\n[错误: {get_attr('message')}]")
                done.set()
                queue.put_nowait(sentinel)

        unsubscribe = session.on(handler)
        asyncio.create_task(session.send(payload))
        try:
            while not done.is_set() or not queue.empty():
                try:
                    chunk = await asyncio.wait_for(
                        queue.get(), timeout=float(self.valves.TIMEOUT)
                    )
                    if chunk is sentinel:
                        break
                    if chunk:
                        has_content = True
                        yield chunk
                except asyncio.TimeoutError:
                    if done.is_set():
                        break
                    continue
            if state["thinking_started"]:
                yield "\n</think>\n"
            if not has_content:
                yield "⚠️ 未返回内容。"
        except Exception as e:
            yield f"\n[流错误: {e}]"
        finally:
            unsubscribe()
            await client.stop()

    async def _extract_system_prompt(
        self,
        body,
        messages,
        request_model,
        real_model_id,
        __event_call__=None,
        debug_enabled=False,
    ):
        sysp, src = None, ""
        if body.get("system_prompt"):
            sysp, src = body.get("system_prompt"), "body_explicit"
        if not sysp:
            meta = body.get("metadata", {}).get("model", {}).get("params", {})
            if meta.get("system"):
                sysp, src = meta.get("system"), "metadata_params"
        if not sysp:
            try:
                from open_webui.models.models import Models

                for mid in [request_model, real_model_id]:
                    m_rec = Models.get_model_by_id(mid)
                    if (
                        m_rec
                        and hasattr(m_rec, "params")
                        and isinstance(m_rec.params, dict)
                        and m_rec.params.get("system")
                    ):
                        sysp, src = m_rec.params.get("system"), f"模型库:{mid}"
                        break
            except:
                pass
        if not sysp:
            for msg in messages:
                if msg.get("role") == "system":
                    sysp, src = msg.get("content", ""), "消息历史"
                    break
        if sysp:
            await self._emit_debug_log(
                f"系统提示词来源: {src} ({len(sysp)} 字符)",
                __event_call__,
                debug_enabled,
            )
        return sysp, src

    def _build_client_config(self, body, user_id=None, chat_id=None):
        c = {
            "cli_path": os.environ.get("COPILOT_CLI_PATH"),
            "cwd": self._get_workspace_dir(user_id, chat_id),
        }
        if self.valves.LOG_LEVEL:
            c["log_level"] = self.valves.LOG_LEVEL
        if self.valves.CUSTOM_ENV_VARS:
            try:
                e = json.loads(self.valves.CUSTOM_ENV_VARS)
                c.update({"env": e}) if isinstance(e, dict) else None
            except:
                pass
        return c
