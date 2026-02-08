"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
openwebui_id: ce96f7b4-12fc-4ac3-9a01-875713e69359
description: Integrate GitHub Copilot SDK. Supports dynamic models, multi-turn conversation, streaming, multimodal input, infinite sessions, and frontend debug logging.
version: 0.5.1
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

# Import copilot SDK modules
from copilot import CopilotClient, define_tool

# Import Tool Server Connections and Tool System from OpenWebUI Config
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
    "\n\n[Environment & Capabilities Context]\n"
    "You are an AI assistant operating within a specific, high-capability environment. Understanding your context is crucial for optimal decision-making.\n"
    "\n"
    "**System Environment:**\n"
    "- **Platform**: You are running inside a Linux containerized environment hosted within **OpenWebUI**.\n"
    "- **Core Engine**: You are powered by the **GitHub Copilot SDK** and interact via the **GitHub Copilot CLI**.\n"
    "- **Access**: You have direct access to the **OpenWebUI source code**. You can read, analyze, and reference the internal implementation of the platform you are running on via file operations or tools.\n"
    "- **FileSystem Access**: You are running as **root**. You have **READ access to the entire container file system** (including system files). However, you should **ONLY WRITE** to your designated persistent workspace directory.\n"
    "- **Native Python Environment**: You are running in a **rich Python environment** that already includes all OpenWebUI dependencies. You can natively import and use these installed libraries (e.g., for data processing, utility functions) without installing anything new.\n"
    "- **Package Management**: Only if you need **additional** libraries, you should **create a virtual environment** within your workspace and install them there. Do NOT mess with the global pip.\n"
    "- **Network**: You have internet access and can interact with external APIs if provided with the necessary tools (e.g., Web Search, MCP Servers).\n"
    "\n"
    "**Interface Capabilities (OpenWebUI):**\n"
    "- **Rich Web UI**: You are NOT limited to a simple terminal or text-only responses. You are rendering in a modern web browser.\n"
    "- **Visual Rendering**: You can and should use advanced visual elements to explain concepts clearly.\n"
    "- **Interactive Scripting**: You can often run Python scripts directly to perform calculations, data analysis, or automate tasks if the environment supports it/tools are available.\n"
    "- **Built-in Tools Integration**: OpenWebUI provides native tools for direct interaction with its internal services. For example, tools like `create_note`, `get_notes`, or `manage_memories` interact directly with the platform's database. Use these tools to persistently manage user data and system state.\n"
    "\n"
    "**Formatting & Presentation Directives:**\n"
    "1. **Markdown & Multimedia**:\n"
    "   - Use **bold**, *italics*, lists, and **Markdown tables** (standard format, never use HTML tables) liberally to structure your answer.\n"
    "   - **Mermaid Diagrams**: For flowcharts, sequence diagrams, or architecture logic, ALWAYS use the standard ```mermaid code block. Do NOT use other formats.\n"
    "   - **LaTeX Math**: Use standard LaTeX formatting for mathematical expressions.\n"
    "\n"
    "2. **Images & Files**:\n"
    "   - If a tool generated an image or file, you **MUST** embed it directly using `![caption](url)`.\n"
    "   - Do NOT simply provide a text link unless explicitly asked.\n"
    "\n"
    "3. **Interactive HTML/JS**:\n"
    "   - You can output standalone HTML/JS/CSS code blocks. OpenWebUI will render them as interactive widgets in an iframe.\n"
    "   - **IMPORTANT**: Combine all HTML, CSS (in `<style>`), and JavaScript (in `<script>`) into a **SINGLE** ` ```html ` code block.\n"
    "   - Use this for dynamic data visualizations (e.g., charts, graphs), interactive demos, or custom UI components.\n"
    "\n"
    "4. **Response Structure**:\n"
    "   - **Think First**: Before complex tasks, briefly outline your plan.\n"
    "   - **Be Concise but Complete**: specific answers are better than generic ones.\n"
    "   - **Premium Feel**: Format your output to look professional and polished, like a technical blog post or documentation.\n"
)


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (Requires 'Copilot Requests' permission)",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Tool Server Tools).",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="Enable Direct MCP Client connection (Recommended).",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="Cache OpenWebUI tools and MCP servers (performance optimization).",
        )
        REASONING_EFFORT: Literal["low", "medium", "high", "xhigh"] = Field(
            default="medium",
            description="Reasoning effort level (low, medium, high). Only affects standard Copilot models (not BYOK).",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="Show model reasoning/thinking process",
        )

        INFINITE_SESSION: bool = Field(
            default=True,
            description="Enable Infinite Sessions (automatic context compaction)",
        )
        DEBUG: bool = Field(
            default=False,
            description="Enable technical debug logs (connection info, etc.)",
        )
        LOG_LEVEL: str = Field(
            default="error",
            description="Copilot CLI log level: none, error, warning, info, debug, all",
        )
        TIMEOUT: int = Field(
            default=300,
            description="Timeout for each stream chunk (seconds)",
        )
        WORKSPACE_DIR: str = Field(
            default="",
            description="Restricted workspace directory for file operations. If empty, allows access to the current process directory.",
        )
        COPILOT_CLI_VERSION: str = Field(
            default="0.0.405",
            description="Specific Copilot CLI version to install/enforce (e.g. '0.0.405'). Leave empty for latest.",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="Exclude models containing these keywords (comma separated, e.g.: codex, haiku)",
        )
        COMPACTION_THRESHOLD: float = Field(
            default=0.8,
            description="Background compaction threshold (0.0-1.0)",
        )
        BUFFER_THRESHOLD: float = Field(
            default=0.95,
            description="Buffer exhaustion threshold (0.0-1.0)",
        )
        CUSTOM_ENV_VARS: str = Field(
            default="",
            description='Custom environment variables (JSON format, e.g., {"VAR": "value"})',
        )

        BYOK_TYPE: Literal["openai", "anthropic"] = Field(
            default="openai",
            description="BYOK Provider Type: openai, anthropic",
        )
        BYOK_BASE_URL: str = Field(
            default="",
            description="BYOK Base URL (e.g., https://api.openai.com/v1)",
        )
        BYOK_API_KEY: str = Field(
            default="",
            description="BYOK API Key (Global Setting)",
        )
        BYOK_BEARER_TOKEN: str = Field(
            default="",
            description="BYOK Bearer Token (Global, overrides API Key)",
        )
        BYOK_MODELS: str = Field(
            default="",
            description="BYOK Model List (comma separated). Leave empty to fetch from API.",
        )
        BYOK_WIRE_API: Literal["completions", "responses"] = Field(
            default="completions",
            description="BYOK Wire API: completions, responses",
        )

    class UserValves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="Personal GitHub Fine-grained Token (overrides global setting)",
        )
        REASONING_EFFORT: Literal["", "low", "medium", "high", "xhigh"] = Field(
            default="",
            description="Reasoning effort override. Only affects standard Copilot Models.",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="Show model reasoning/thinking process",
        )
        DEBUG: bool = Field(
            default=False,
            description="Enable technical debug logs (connection info, etc.)",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Tool Server Tools).",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="Enable dynamic MCP server loading (overrides global).",
        )
        ENABLE_TOOL_CACHE: bool = Field(
            default=True,
            description="Enable Tool/MCP configuration caching for this user.",
        )

        # BYOK User Overrides
        BYOK_API_KEY: str = Field(
            default="",
            description="BYOK API Key (User override)",
        )
        BYOK_TYPE: Literal["", "openai", "anthropic"] = Field(
            default="",
            description="BYOK Provider Type override.",
        )
        BYOK_BASE_URL: str = Field(
            default="",
            description="BYOK Base URL override.",
        )
        BYOK_BEARER_TOKEN: str = Field(
            default="",
            description="BYOK Bearer Token override.",
        )
        BYOK_MODELS: str = Field(
            default="",
            description="BYOK Model List override.",
        )
        BYOK_WIRE_API: Literal["", "completions", "responses"] = Field(
            default="",
            description="BYOK Wire API override.",
        )

    # ==================== Class-Level Caches ====================
    # These caches persist across requests since OpenWebUI may create
    # new Pipe instances for each request.
    # =============================================================
    _model_cache: List[dict] = []  # Model list cache
    _standard_model_ids: set = set()  # Track standard model IDs
    _tool_cache = None  # Cache for converted OpenWebUI tools
    _mcp_server_cache = None  # Cache for MCP server config
    _env_setup_done = False  # Track if env setup has been completed
    _last_update_check = 0  # Timestamp of last CLI update check

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

    # ==================== Fixed System Entry ====================
    # pipe() is the stable entry point used by OpenWebUI to handle requests.
    # Keep this section near the top for quick navigation and maintenance.
    # =============================================================
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

    # ==================== Functional Areas ====================
    # 1) Tool registration: define tools and register in _initialize_custom_tools
    # 2) Debug logging: _emit_debug_log / _emit_debug_log_sync
    # 3) Prompt/session: _extract_system_prompt / _build_session_config / _build_prompt
    # 4) Runtime flow: pipe() for request, stream_response() for streaming
    # ============================================================
    # ==================== Custom Tool Examples ====================
    # Tool registration: Add @define_tool decorated functions at module level,
    # then register them in _initialize_custom_tools() -> all_tools dict.
    async def _initialize_custom_tools(self, __user__=None, __event_call__=None):
        """Initialize custom tools based on configuration"""
        if not self.valves.ENABLE_OPENWEBUI_TOOLS:
            return []

        # Determine cache setting (user override > global)
        enable_cache = self.valves.ENABLE_TOOL_CACHE
        if __user__:
            try:
                # Attempt to get user valve, handling potential missing field or type issues gracefully
                # We need to construct UserValves to access defaults/overrides correctly if passed as dict
                raw_user_valves = __user__.get("valves", {})
                if isinstance(raw_user_valves, dict):
                    uv = self.UserValves(**raw_user_valves)
                    enable_cache = uv.ENABLE_TOOL_CACHE
                elif isinstance(raw_user_valves, self.UserValves):
                    enable_cache = raw_user_valves.ENABLE_TOOL_CACHE
            except:
                pass

        # Check Cache
        if enable_cache and self._tool_cache is not None:
            await self._emit_debug_log(
                "ℹ️ Using cached OpenWebUI tools.", __event_call__
            )
            return self._tool_cache

        # Load OpenWebUI tools dynamically
        openwebui_tools = await self._load_openwebui_tools(
            __user__=__user__, __event_call__=__event_call__
        )

        # Update Cache
        if enable_cache:
            self._tool_cache = openwebui_tools
            await self._emit_debug_log(
                "✅ OpenWebUI tools cached for subsequent requests.", __event_call__
            )

        # Log details only when cache is cold
        if openwebui_tools:
            tool_names = [t.name for t in openwebui_tools]
            await self._emit_debug_log(
                f"Loaded {len(openwebui_tools)} tools: {tool_names}",
                __event_call__,
            )
            if self.valves.DEBUG:
                for t in openwebui_tools:
                    await self._emit_debug_log(
                        f"📋 Tool Detail: {t.name} - {t.description[:100]}...",
                        __event_call__,
                    )

        return openwebui_tools

    def _json_schema_to_python_type(self, schema: dict) -> Any:
        """Convert JSON Schema type to Python type for Pydantic models."""
        if not isinstance(schema, dict):
            return Any

        # Check for Enum (Literal)
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
        """Convert OpenWebUI tool definition to Copilot SDK tool."""
        # Sanitize tool name to match pattern ^[a-zA-Z0-9_-]+$
        sanitized_tool_name = re.sub(r"[^a-zA-Z0-9_-]", "_", tool_name)

        # If sanitized name is empty or consists only of separators (e.g. pure Chinese name), generate a fallback name
        if not sanitized_tool_name or re.match(r"^[_.-]+$", sanitized_tool_name):
            hash_suffix = hashlib.md5(tool_name.encode("utf-8")).hexdigest()[:8]
            sanitized_tool_name = f"tool_{hash_suffix}"

        if sanitized_tool_name != tool_name:
            logger.debug(
                f"Sanitized tool name '{tool_name}' to '{sanitized_tool_name}'"
            )

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

            # Extract default value if present
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
                # If not required, wrap in Optional and use default_value
                optional_type = Optional[param_type]
                if description:
                    fields[param_name] = (
                        optional_type,
                        Field(default=default_value, description=description),
                    )
                else:
                    fields[param_name] = (optional_type, default_value)

        if fields:
            ParamsModel = create_model(f"{sanitized_tool_name}_Params", **fields)
        else:
            ParamsModel = create_model(f"{sanitized_tool_name}_Params")

        tool_callable = tool_dict.get("callable")
        tool_description = spec.get("description", "") if isinstance(spec, dict) else ""
        if not tool_description and isinstance(spec, dict):
            tool_description = spec.get("summary", "")

        # Determine tool source/group for description prefix
        tool_id = tool_dict.get("tool_id", "")
        tool_type = tool_dict.get(
            "type", ""
        )  # "builtin", "external", or empty (user-defined)

        if tool_type == "builtin":
            # OpenWebUI Built-in Tool (system tools like web search, memory, notes)
            group_prefix = "[OpenWebUI Built-in]"
        elif tool_type == "external" or tool_id.startswith("server:"):
            # OpenAPI Tool Server - use metadata if available
            tool_group_name = tool_dict.get("_tool_group_name")
            tool_group_desc = tool_dict.get("_tool_group_description")
            server_id = (
                tool_id.replace("server:", "").split("|")[0]
                if tool_id.startswith("server:")
                else tool_id
            )

            if tool_group_name:
                if tool_group_desc:
                    group_prefix = (
                        f"[Tool Server: {tool_group_name} - {tool_group_desc}]"
                    )
                else:
                    group_prefix = f"[Tool Server: {tool_group_name}]"
            else:
                group_prefix = f"[Tool Server: {server_id}]"
        else:
            # User-defined Python script tool - use metadata if available
            tool_group_name = tool_dict.get("_tool_group_name")
            tool_group_desc = tool_dict.get("_tool_group_description")

            if tool_group_name:
                # Use the tool's title from docstring, e.g., "Prefect API Tools"
                if tool_group_desc:
                    group_prefix = f"[User Tool: {tool_group_name} - {tool_group_desc}]"
                else:
                    group_prefix = f"[User Tool: {tool_group_name}]"
            else:
                group_prefix = f"[User Tool: {tool_id}]" if tool_id else "[User Tool]"

        # Build final description with group prefix
        if sanitized_tool_name != tool_name:
            # Include original name if it was sanitized
            tool_description = (
                f"{group_prefix} Function '{tool_name}': {tool_description}"
            )
        else:
            tool_description = f"{group_prefix} {tool_description}"

        async def _tool(params):
            # Crucial Fix: Use exclude_unset=True.
            # This ensures that parameters not explicitly provided by the LLM
            # (which default to None in the Pydantic model) are COMPLETELY OMITTED
            # from the function call. This allows the underlying Python function's
            # own default values to take effect, instead of receiving an explicit None.
            payload = (
                params.model_dump(exclude_unset=True)
                if hasattr(params, "model_dump")
                else {}
            )
            return await tool_callable(**payload)

        _tool.__name__ = sanitized_tool_name
        _tool.__doc__ = tool_description

        # Debug log for tool conversion
        logger.debug(
            f"Converting tool '{sanitized_tool_name}': {tool_description[:50]}..."
        )

        # Core Fix: Explicitly pass params_type and name
        return define_tool(
            name=sanitized_tool_name,
            description=tool_description,
            params_type=ParamsModel,
        )(_tool)

    def _build_openwebui_request(self, user: dict = None):
        """Build a more complete request-like object with dynamically loaded OpenWebUI configs."""
        # Dynamically build config from the official registry
        config = SimpleNamespace()
        for item in PERSISTENT_CONFIG_REGISTRY:
            # Special handling for TOOL_SERVER_CONNECTIONS which might be a list/dict object
            # rather than a simple primitive value, though .value handles the latest state
            val = item.value
            if hasattr(val, "value"):  # Handling nested structures if any
                val = val.value
            setattr(config, item.env_name, val)

        app_state = SimpleNamespace(
            config=config,
            TOOLS={},
            TOOL_CONTENTS={},
            FUNCTIONS={},
            FUNCTION_CONTENTS={},
            MODELS={},
        )

        def url_path_for(name: str, **path_params):
            """Mock url_path_for for tool compatibility."""
            if name == "get_file_content_by_id":
                return f"/api/v1/files/{path_params.get('id')}/content"
            return f"/mock/{name}"

        app = SimpleNamespace(
            state=app_state,
            url_path_for=url_path_for,
        )

        # Mocking generic request attributes
        request = SimpleNamespace(
            app=app,
            url=SimpleNamespace(
                path="/api/chat/completions",
                base_url="http://localhost:8080",
                __str__=lambda s: "http://localhost:8080/api/chat/completions",
            ),
            base_url="http://localhost:8080",
            headers={
                "user-agent": "Mozilla/5.0 (OpenWebUI Plugin/GitHub-Copilot-SDK)",
                "host": "localhost:8080",
                "accept": "*/*",
            },
            method="POST",
            cookies={},
            state=SimpleNamespace(
                token=SimpleNamespace(credentials=""), user=user if user else {}
            ),
        )
        return request

    async def _load_openwebui_tools(self, __user__=None, __event_call__=None):
        """Load OpenWebUI tools and convert them to Copilot SDK tools."""
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

        user = Users.get_user_by_id(user_id)
        if not user:
            return []

        # 1. Get User defined tools (Python scripts)
        tool_items = Tools.get_tools_by_user_id(user_id, permission="read")
        tool_ids = [tool.id for tool in tool_items] if tool_items else []

        # 2. Get OpenAPI Tool Server tools
        # We manually add enabled OpenAPI servers to the list because Tools.get_tools_by_user_id only checks the DB.
        # open_webui.utils.tools.get_tools handles the actual loading and access control.
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            for server in TOOL_SERVER_CONNECTIONS.value:
                # We only add 'openapi' servers here because get_tools currently only supports 'openapi' (or defaults to it).
                # MCP tools are handled separately via ENABLE_MCP_SERVER.
                if server.get("type") == "openapi":
                    # Format expected by get_tools: "server:<id>" implies types="openapi"
                    server_id = server.get("id")
                    if server_id:
                        tool_ids.append(f"server:{server_id}")

        if not tool_ids:
            return []

        request = self._build_openwebui_request(user_data)
        extra_params = {
            "__request__": request,
            "__user__": user_data,
            "__event_emitter__": None,
            "__event_call__": __event_call__,
            "__chat_id__": None,
            "__message_id__": None,
            "__model_knowledge__": [],
        }

        # Fetch User/Server Tools
        tools_dict = {}
        if tool_ids:
            try:
                tools_dict = await get_openwebui_tools(
                    request, tool_ids, user, extra_params
                )
            except Exception as e:
                await self._emit_debug_log(
                    f"Error fetching user/server tools: {e}", __event_call__
                )

        # Fetch Built-in Tools (Web Search, Memory, etc.)
        # Note: We pass minimal features/model dict as we want to expose all enabled built-ins
        # that are globally configured.
        try:
            # Get builtin tools
            builtin_tools = get_builtin_tools(
                self._build_openwebui_request(user_data),
                {
                    "__user__": user_data,
                    "__chat_id__": extra_params.get("__chat_id__"),
                    "__message_id__": extra_params.get("__message_id__"),
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
                },  # Mock capabilities to allow all globally enabled tools
            )
            if builtin_tools:
                tools_dict.update(builtin_tools)
        except Exception as e:
            await self._emit_debug_log(
                f"Error fetching built-in tools: {e}", __event_call__
            )

        if not tools_dict:
            return []

        # Enrich tools with metadata from their source
        # 1. User-defined tools: name, description from docstring
        # 2. OpenAPI Tool Server tools: name, description from server config info
        tool_metadata_cache = {}
        server_metadata_cache = {}

        # Pre-build server metadata cache from TOOL_SERVER_CONNECTIONS
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            for server in TOOL_SERVER_CONNECTIONS.value:
                server_id = server.get("id") or server.get("info", {}).get("id")
                if server_id:
                    info = server.get("info", {})
                    server_metadata_cache[server_id] = {
                        "name": info.get("name") or server_id,
                        "description": info.get("description", ""),
                    }

        for tool_name, tool_def in tools_dict.items():
            tool_id = tool_def.get("tool_id", "")
            tool_type = tool_def.get("type", "")

            if tool_type == "builtin":
                # Built-in tools don't need additional metadata
                continue
            elif tool_type == "external" or tool_id.startswith("server:"):
                # OpenAPI Tool Server - extract server ID and get metadata
                server_id = (
                    tool_id.replace("server:", "").split("|")[0]
                    if tool_id.startswith("server:")
                    else ""
                )
                if server_id and server_id in server_metadata_cache:
                    tool_def["_tool_group_name"] = server_metadata_cache[server_id].get(
                        "name"
                    )
                    tool_def["_tool_group_description"] = server_metadata_cache[
                        server_id
                    ].get("description")
            else:
                # User-defined Python script tool
                if tool_id and tool_id not in tool_metadata_cache:
                    try:
                        tool_model = Tools.get_tool_by_id(tool_id)
                        if tool_model:
                            tool_metadata_cache[tool_id] = {
                                "name": tool_model.name,
                                "description": (
                                    tool_model.meta.description
                                    if tool_model.meta
                                    else None
                                ),
                            }
                    except Exception:
                        pass

                if tool_id in tool_metadata_cache:
                    tool_def["_tool_group_name"] = tool_metadata_cache[tool_id].get(
                        "name"
                    )
                    tool_def["_tool_group_description"] = tool_metadata_cache[
                        tool_id
                    ].get("description")

        converted_tools = []
        for tool_name, tool_def in tools_dict.items():
            try:
                converted_tools.append(
                    self._convert_openwebui_tool(tool_name, tool_def)
                )
            except Exception as e:
                await self._emit_debug_log(
                    f"Failed to load OpenWebUI tool '{tool_name}': {e}",
                    __event_call__,
                )

        return converted_tools

    def _parse_mcp_servers(self) -> Optional[dict]:
        """
        Dynamically load MCP servers from OpenWebUI TOOL_SERVER_CONNECTIONS.
        Returns a dict of mcp_servers compatible with CopilotClient.
        """
        if not self.valves.ENABLE_MCP_SERVER:
            return None

        # Determine cache setting (no user context here usually, unless passed down, but for now use global as baseline + potentially stored user pref if we had access to user context easily in this method signature.
        # However, _parse_mcp_servers is called from _build_client_config which doesn't easily pass user context.
        # Wait, _parse_mcp_servers is called by _build_client_config(body) inside _pipe_impl.
        # But _pipe_impl has access to user.
        # Let's check where _parse_mcp_servers is called.
        # It is called in _build_client_config.
        # Actually _parse_mcp_servers is defined on 'self'.
        # To support user override here, we'd need to pass user settings down or store them temporarily.
        # Given the complexity, and that MCP servers are globally defined in OpenWebUI connection settings (usually),
        # maybe global cache setting is sufficient for MCP?
        # BUT, the user request implied "user can turn off".
        # Let's stick to global for MCP for now unless we refactor to pass user_valves into this method.
        # Refactoring to use self.valves.ENABLE_TOOL_CACHE is safe for now as baseline.
        # If we really need user override for MCP cache, we need to pass `enable_cache` boolean to this method.

        # Let's use the global valve for now as it matches the previous logic, but be aware of the limitation.
        # The user's request "run user close" (user can turn off) likely applies to the tools they use.

        # Check Cache
        if self.valves.ENABLE_TOOL_CACHE and self._mcp_server_cache is not None:
            return self._mcp_server_cache

        mcp_servers = {}

        # Iterate over OpenWebUI Tool Server Connections
        if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
            connections = TOOL_SERVER_CONNECTIONS.value
        else:
            connections = []

        for conn in connections:
            if conn.get("type") == "mcp":
                info = conn.get("info", {})
                # Use ID from info or generate one
                raw_id = info.get("id", f"mcp-server-{len(mcp_servers)}")

                # Sanitize server_id (using same logic as tools)
                server_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id)
                if not server_id or re.match(r"^[_.-]+$", server_id):
                    hash_suffix = hashlib.md5(raw_id.encode("utf-8")).hexdigest()[:8]
                    server_id = f"server_{hash_suffix}"

                url = conn.get("url")
                if not url:
                    continue

                # Build Headers (Handle Auth)
                headers = {}
                auth_type = conn.get("auth_type", "bearer")
                key = conn.get("key", "")

                if auth_type == "bearer" and key:
                    headers["Authorization"] = f"Bearer {key}"
                elif auth_type == "basic" and key:
                    headers["Authorization"] = f"Basic {key}"

                # Merge custom headers if any
                custom_headers = conn.get("headers", {})
                if isinstance(custom_headers, dict):
                    headers.update(custom_headers)

                # Get filtering configuration
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

        # Update Cache
        if self.valves.ENABLE_TOOL_CACHE:
            self._mcp_server_cache = mcp_servers

        return mcp_servers if mcp_servers else None

    async def _emit_debug_log(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        """Emit debug log to frontend (console) when DEBUG is enabled."""
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
            logger.debug(f"[Copilot Pipe] Frontend debug log failed: {e}")

    def _emit_debug_log_sync(
        self, message: str, __event_call__=None, debug_enabled: Optional[bool] = None
    ):
        """Sync wrapper for debug logging."""
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

    def _extract_text_from_content(self, content) -> str:
        """Extract text content from various message content formats."""
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
        """Return the prompt as-is (formatting hints removed)."""
        return prompt

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        """Deduplicate while preserving order."""
        seen = set()
        result = []
        for item in items:
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def _strip_model_prefix(self, model_id: str) -> str:
        """Sequential prefix stripping: OpenWebUI plugin ID then internal pipe prefix."""
        if not model_id:
            return ""

        res = model_id
        # 1. Strip OpenWebUI plugin prefix (e.g. 'github_copilot_sdk.copilot-gpt-4o' -> 'copilot-gpt-4o')
        if "." in res:
            res = res.split(".", 1)[-1]

        # 2. Strip our own internal prefix (e.g. 'copilot-gpt-4o' -> 'gpt-4o')
        internal_prefix = f"{self.id}-"
        if res.startswith(internal_prefix):
            res = res[len(internal_prefix) :]

        # 3. Handle legacy/variant dash-based prefix
        if res.startswith("copilot - "):
            res = res[10:]

        return res

    def _collect_model_ids(
        self, body: dict, request_model: str, real_model_id: str
    ) -> List[str]:
        """Collect possible model IDs from request/metadata/body params."""
        model_ids: List[str] = []
        if request_model:
            model_ids.append(request_model)
            stripped = self._strip_model_prefix(request_model)
            if stripped != request_model:
                model_ids.append(stripped)
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
        """Extract system prompt from metadata/model DB/body/messages."""
        system_prompt_content: Optional[str] = None
        system_prompt_source = ""

        # 0) body.get("system_prompt") - Explicit Override (Highest Priority)
        if hasattr(body, "get") and body.get("system_prompt"):
            system_prompt_content = body.get("system_prompt")
            system_prompt_source = "body_explicit_system_prompt"
            await self._emit_debug_log(
                f"Extracted system prompt from explicit body field (length: {len(system_prompt_content)})",
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
                            f"Extracted system prompt from metadata.model.params (length: {len(system_prompt_content)})",
                            __event_call__,
                            debug_enabled=debug_enabled,
                        )

        # 2) model DB lookup
        if not system_prompt_content:
            try:
                from open_webui.models.models import Models

                model_ids_to_try = self._collect_model_ids(
                    body, request_model, real_model_id
                )
                await self._emit_debug_log(
                    f"Checking system prompt for models: {model_ids_to_try}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                for mid in model_ids_to_try:
                    model_record = Models.get_model_by_id(mid)
                    if model_record:
                        await self._emit_debug_log(
                            f"Checking Model DB for: {mid} (Record found: {model_record.id if hasattr(model_record, 'id') else 'Yes'})",
                            __event_call__,
                            debug_enabled=debug_enabled,
                        )
                        if hasattr(model_record, "params"):
                            params = model_record.params
                            if isinstance(params, dict):
                                system_prompt_content = params.get("system")
                                if system_prompt_content:
                                    system_prompt_source = f"model_db:{mid}"
                                    await self._emit_debug_log(
                                        f"Success! Extracted system prompt from model DB using ID: {mid} (length: {len(system_prompt_content)})",
                                        __event_call__,
                                        debug_enabled=debug_enabled,
                                    )
                                    break
            except Exception as e:
                await self._emit_debug_log(
                    f"Failed to extract system prompt from model DB: {e}",
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
                        f"Extracted system prompt from body.params.system (length: {len(system_prompt_content)})",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )

        # 4) messages (role=system) - Last found wins or First found wins?
        # Typically OpenWebUI puts the active system prompt as the FIRST message.
        if not system_prompt_content:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt_content = self._extract_text_from_content(
                        msg.get("content", "")
                    )
                    if system_prompt_content:
                        system_prompt_source = "messages_system"
                        await self._emit_debug_log(
                            f"Extracted system prompt from messages (reverse search) (length: {len(system_prompt_content)})",
                            __event_call__,
                            debug_enabled=debug_enabled,
                        )
                    break

        return system_prompt_content, system_prompt_source

    def _get_workspace_dir(self) -> str:
        """Get the effective workspace directory with smart defaults."""
        if self.valves.WORKSPACE_DIR:
            return self.valves.WORKSPACE_DIR

        # Smart default for OpenWebUI container
        if os.path.exists("/app/backend/data"):
            cwd = "/app/backend/data/copilot_workspace"
        else:
            # Local fallback: subdirectory in current working directory
            cwd = os.path.join(os.getcwd(), "copilot_workspace")

        # Ensure directory exists
        if not os.path.exists(cwd):
            try:
                os.makedirs(cwd, exist_ok=True)
            except Exception as e:
                print(f"Error creating workspace {cwd}: {e}")
                return os.getcwd()  # Fallback to CWD if creation fails

        return cwd

    def _build_client_config(self, body: dict) -> dict:
        """Build CopilotClient config from valves and request body."""
        cwd = self._get_workspace_dir()
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
        provider_config: Optional[dict] = None,
    ):
        """Build SessionConfig for Copilot SDK."""
        from copilot.types import SessionConfig, InfiniteSessionConfig

        infinite_session_config = None
        if self.valves.INFINITE_SESSION:
            infinite_session_config = InfiniteSessionConfig(
                enabled=True,
                background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
                buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
            )

        # Prepare the combined system message content
        system_parts = []
        if system_prompt_content:
            system_parts.append(system_prompt_content.strip())
        system_parts.append(FORMATTING_GUIDELINES)
        final_system_msg = "\n".join(system_parts)

        # Design Choice: ALWAYS use 'replace' mode to ensure full control and avoid duplicates.
        # This replaces any default system prompt with our combined version.
        system_message_config = {
            "mode": "replace",
            "content": final_system_msg,
        }

        # Prepare session config parameters
        session_params = {
            "session_id": chat_id if chat_id else None,
            "model": real_model_id,
            "streaming": is_streaming,
            "tools": custom_tools,
            "available_tools": [t.name for t in custom_tools] if custom_tools else None,
            "system_message": system_message_config,
            "infinite_sessions": infinite_session_config,
        }

        if provider_config:
            session_params["provider"] = provider_config

        mcp_servers = self._parse_mcp_servers()
        if mcp_servers:
            session_params["mcp_servers"] = mcp_servers

        # Ensure working directory is set to allow the agent to perform file operations
        session_params["working_directory"] = self._get_workspace_dir()

        return SessionConfig(**session_params)

    def _get_user_context(self):
        """Helper to get user context (placeholder for future use)."""
        return {}

    def _get_chat_context(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __event_call__=None,
        debug_enabled: bool = False,
    ) -> Dict[str, str]:
        """
        Highly reliable chat context extraction logic.
        Priority: __metadata__ > body['chat_id'] > body['metadata']['chat_id']
        """
        chat_id = ""
        source = "none"

        # 1. Prioritize __metadata__ (most reliable source injected by OpenWebUI)
        if __metadata__ and isinstance(__metadata__, dict):
            chat_id = __metadata__.get("chat_id", "")
            if chat_id:
                source = "__metadata__"

        # 2. Then try body root
        if not chat_id and isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            if chat_id:
                source = "body_root"

        # 3. Finally try body.metadata
        if not chat_id and isinstance(body, dict):
            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                chat_id = body_metadata.get("chat_id", "")
                if chat_id:
                    source = "body_metadata"

        # Debug: Log ID source
        if chat_id:
            self._emit_debug_log_sync(
                f"Extracted ChatID: {chat_id} (Source: {source})",
                __event_call__,
                debug_enabled=debug_enabled,
            )
        else:
            # If still not found, log body keys for troubleshooting
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log_sync(
                f"Warning: Failed to extract ChatID. Body keys: {keys}",
                __event_call__,
                debug_enabled=debug_enabled,
            )

        return {
            "chat_id": str(chat_id).strip(),
        }

    async def _fetch_byok_models(self) -> List[dict]:
        """Fetch BYOK models from configured provider."""
        model_list = []
        if self.valves.BYOK_BASE_URL:
            try:
                base_url = self.valves.BYOK_BASE_URL.rstrip("/")
                url = f"{base_url}/models"
                headers = {}
                provider_type = self.valves.BYOK_TYPE.lower()

                if provider_type == "anthropic":
                    if self.valves.BYOK_API_KEY:
                        headers["x-api-key"] = self.valves.BYOK_API_KEY
                    headers["anthropic-version"] = "2023-06-01"
                else:
                    if self.valves.BYOK_BEARER_TOKEN:
                        headers["Authorization"] = (
                            f"Bearer {self.valves.BYOK_BEARER_TOKEN}"
                        )
                    elif self.valves.BYOK_API_KEY:
                        headers["Authorization"] = f"Bearer {self.valves.BYOK_API_KEY}"

                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
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
                            await self._emit_debug_log(
                                f"BYOK: Fetched {len(model_list)} models from {url}"
                            )
                        else:
                            await self._emit_debug_log(
                                f"BYOK: Failed to fetch models from {url}. Status: {resp.status}"
                            )
            except Exception as e:
                await self._emit_debug_log(f"BYOK: Model fetch error: {e}")

        # Fallback to configured list or defaults
        if not model_list:
            if self.valves.BYOK_MODELS.strip():
                model_list = [
                    m.strip() for m in self.valves.BYOK_MODELS.split(",") if m.strip()
                ]
                await self._emit_debug_log(
                    f"BYOK: Using user-configured BYOK_MODELS ({len(model_list)} models)."
                )
            else:
                defaults = {
                    "anthropic": [
                        "claude-3-5-sonnet-latest",
                        "claude-3-5-haiku-latest",
                        "claude-3-opus-latest",
                    ],
                }
                model_list = defaults.get(
                    self.valves.BYOK_TYPE.lower(),
                    ["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
                )
                await self._emit_debug_log(
                    f"BYOK: Using default fallback models for {self.valves.BYOK_TYPE} ({len(model_list)} models)."
                )

        return [
            {"id": m, "name": f"-{self._clean_model_id(m)}", "source": "byok"}
            for m in model_list
        ]

    def _clean_model_id(self, model_id: str) -> str:
        """Remove copilot prefixes from model ID."""
        if model_id.startswith("copilot-"):
            return model_id[8:]
        elif model_id.startswith("copilot - "):
            return model_id[10:]
        return model_id

    async def pipes(self) -> List[dict]:
        """Dynamically fetch model list"""
        if self._model_cache:
            return self._model_cache

        await self._emit_debug_log("Fetching model list dynamically...")
        try:
            self._setup_env()

            # Check for valid configuration
            byok_active = bool(
                self.valves.BYOK_BASE_URL
                and (self.valves.BYOK_API_KEY or self.valves.BYOK_BEARER_TOKEN)
            )
            if not self.valves.GH_TOKEN and not byok_active:
                self._standard_model_ids = set()
                return [
                    {"id": "error", "name": "Error: GH_TOKEN or BYOK not configured"}
                ]

            client_config = {}
            if os.environ.get("COPILOT_CLI_PATH"):
                client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

            # 1. Fetch BYOK Models if configured
            byok_models = []
            if byok_active:
                byok_models = await self._fetch_byok_models()
                # If GH_TOKEN is missing, return only BYOK models immediately
                if not self.valves.GH_TOKEN:
                    self._model_cache = byok_models
                    return self._model_cache

            # 2. Fetch Standard Copilot Models (if GH_TOKEN is present)
            standard_models = []
            client = CopilotClient(client_config)
            try:
                await client.start()
                raw_models = await client.list_models()

                exclude_list = [
                    k.strip().lower()
                    for k in self.valves.EXCLUDE_KEYWORDS.split(",")
                    if k.strip()
                ]
                processed_models = []

                for m in raw_models:
                    # Extract fields resiliently
                    m_id = (
                        m.get("id") if isinstance(m, dict) else getattr(m, "id", str(m))
                    )
                    m_billing = (
                        m.get("billing")
                        if isinstance(m, dict)
                        else getattr(m, "billing", {})
                    )
                    m_policy = (
                        m.get("policy")
                        if isinstance(m, dict)
                        else getattr(m, "policy", {})
                    )

                    # Skip disabled models
                    state = (
                        m_policy.get("state")
                        if isinstance(m_policy, dict)
                        else getattr(m_policy, "state", "enabled")
                    )
                    if state == "disabled":
                        continue

                    # Apply exclusion filter
                    if any(kw in m_id.lower() for kw in exclude_list):
                        continue

                    multiplier = (
                        m_billing.get("multiplier", 1)
                        if isinstance(m_billing, dict)
                        else getattr(m_billing, "multiplier", 1)
                    )

                    clean_id = self._clean_model_id(m_id)
                    # Use (0x) to indicate free/unlimited with a fire emoji
                    # User requested 'copilotsdk-🔥 model (0x)' format
                    if multiplier > 0:
                        display_name = f"-{clean_id} ({multiplier}x)"
                    else:
                        display_name = f"-🔥 {clean_id} (0x)"

                    processed_models.append(
                        {
                            "id": m_id,  # Keep raw ID
                            "name": display_name,
                            "multiplier": multiplier,
                            "raw_id": m_id,
                        }
                    )

                # Sort by multiplier (cheapest first), then name
                processed_models.sort(key=lambda x: (x["multiplier"], x["raw_id"]))
                standard_models = [
                    {
                        "id": f"{self.id}-{m['raw_id']}",
                        "name": m["name"],
                        "source": "copilot",
                    }
                    for m in processed_models
                ]
                self._standard_model_ids = {m["raw_id"] for m in processed_models}

            except Exception as e:
                await self._emit_debug_log(f"Failed to fetch standard model list: {e}")
                self._standard_model_ids = set()
                # If standard fetch fails but we have BYOK, use BYOK
                if byok_models:
                    self._model_cache = byok_models
                    return self._model_cache
                # Otherwise, soft fail with default model
                return [{"id": "gpt-5-mini", "name": "-gpt-5-mini"}]
            finally:
                await client.stop()

            # 3. Merge and Return
            self._model_cache = standard_models + byok_models

            await self._emit_debug_log(
                f"Successfully fetched {len(standard_models)} standard models and {len(byok_models)} BYOK models. Total: {len(self._model_cache)}"
            )
            return self._model_cache

        except Exception as e:
            await self._emit_debug_log(f"Pipes Error: {e}")
            return [{"id": "gpt-5-mini", "name": "-gpt-5-mini"}]

    async def _get_client(self):
        """Helper to get or create a CopilotClient instance."""
        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

        client = CopilotClient(client_config)
        await client.start()
        return client

    def _setup_env(self, __event_call__=None, debug_enabled: bool = False):
        """Setup environment variables and verify Copilot CLI."""
        if self._env_setup_done:
            return

        # 1. Environment Variables for Auth
        if self.valves.GH_TOKEN:
            os.environ["GH_TOKEN"] = self.valves.GH_TOKEN
            os.environ["GITHUB_TOKEN"] = self.valves.GH_TOKEN
        else:
            self._emit_debug_log_sync(
                "Warning: GH_TOKEN is not set.",
                __event_call__,
                debug_enabled=debug_enabled,
            )

        # Disable CLI auto-update to ensure version consistency
        os.environ["COPILOT_AUTO_UPDATE"] = "false"
        self._emit_debug_log_sync(
            "Disabled CLI auto-update (COPILOT_AUTO_UPDATE=false)",
            __event_call__,
            debug_enabled=debug_enabled,
        )

        # 2. CLI Path Discovery
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

        # Check existing version
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

        # 3. Installation/Update Logic
        should_install = not found
        install_reason = "CLI not found"
        if found and target_version:
            norm_target = target_version.lstrip("v")
            norm_current = current_version.lstrip("v") if current_version else ""

            # Only install if target version is GREATER than current version
            try:
                from packaging.version import parse as parse_version

                if parse_version(norm_target) > parse_version(norm_current):
                    should_install = True
                    install_reason = (
                        f"Upgrade needed ({current_version} -> {target_version})"
                    )
                elif parse_version(norm_target) < parse_version(norm_current):
                    self._emit_debug_log_sync(
                        f"Current version ({current_version}) is newer than specified ({target_version}). Skipping downgrade.",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
            except Exception as e:
                # Fallback to string comparison if packaging is not available
                if norm_target != norm_current:
                    should_install = True
                    install_reason = (
                        f"Version mismatch ({current_version} != {target_version})"
                    )

        if should_install:
            self._emit_debug_log_sync(
                f"Installing/Updating Copilot CLI: {install_reason}...",
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
                # Re-verify
                current_version = get_cli_version(cli_path)
            except Exception as e:
                self._emit_debug_log_sync(
                    f"CLI installation failed: {e}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

        # 4. Finalize
        os.environ["COPILOT_CLI_PATH"] = cli_path
        self._env_setup_done = True
        self._emit_debug_log_sync(
            f"Environment setup complete. CLI: {cli_path} (v{current_version})",
            __event_call__,
            debug_enabled=debug_enabled,
        )

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

    def _sync_copilot_config(
        self, reasoning_effort: str, __event_call__=None, debug_enabled: bool = False
    ):
        """
        Dynamically update ~/.copilot/config.json if REASONING_EFFORT is set.
        This provides a fallback if API injection is ignored by the server.
        """
        if not reasoning_effort:
            return

        effort = reasoning_effort

        # Check model support for xhigh
        # Only gpt-5.2-codex supports xhigh currently
        if effort == "xhigh":
            if (
                "gpt-5.2-codex"
                not in self._collect_model_ids(
                    body={},
                    request_model=self.id,
                    real_model_id=None,
                )[0].lower()
            ):
                # Fallback to high if not supported
                effort = "high"

        try:
            # Target standard path ~/.copilot/config.json
            config_path = os.path.expanduser("~/.copilot/config.json")
            config_dir = os.path.dirname(config_path)

            # Only proceed if directory exists (avoid creating trash types of files if path is wrong)
            if not os.path.exists(config_dir):
                return

            data = {}
            # Read existing config
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            # Update if changed
            current_val = data.get("reasoning_effort")
            if current_val != effort:
                data["reasoning_effort"] = effort
                try:
                    with open(config_path, "w") as f:
                        json.dump(data, f, indent=4)

                    self._emit_debug_log_sync(
                        f"Dynamically updated ~/.copilot/config.json: reasoning_effort='{effort}'",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"Failed to write config.json: {e}",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
        except Exception as e:
            self._emit_debug_log_sync(
                f"Config sync check failed: {e}",
                __event_call__,
                debug_enabled=debug_enabled,
            )

    # ==================== Internal Implementation ====================
    # _pipe_impl() contains the main request handling logic.
    # ================================================================
    async def _pipe_impl(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        # 1. Determine effective debug setting FIRST to capture all logs
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

        # 2. Setup environment with effective debug
        self._setup_env(__event_call__, debug_enabled=effective_debug)

        cwd = self._get_workspace_dir()
        await self._emit_debug_log(
            f"Agent working in: {cwd}", __event_call__, debug_enabled=effective_debug
        )

        # Determine effective BYOK settings
        byok_api_key = user_valves.BYOK_API_KEY or self.valves.BYOK_API_KEY
        byok_bearer_token = (
            user_valves.BYOK_BEARER_TOKEN or self.valves.BYOK_BEARER_TOKEN
        )
        byok_base_url = user_valves.BYOK_BASE_URL or self.valves.BYOK_BASE_URL
        byok_active = bool(byok_base_url and (byok_api_key or byok_bearer_token))

        # Check that either GH_TOKEN or BYOK is configured
        gh_token = user_valves.GH_TOKEN or self.valves.GH_TOKEN
        if not gh_token and not byok_active:
            return "Error: Please configure GH_TOKEN or BYOK settings in Valves."

        # Parse user selected model
        request_model = body.get("model", "")
        real_model_id = request_model

        # Determine effective reasoning effort
        effective_reasoning_effort = (
            user_valves.REASONING_EFFORT
            if user_valves.REASONING_EFFORT
            else self.valves.REASONING_EFFORT
        )

        # Apply SHOW_THINKING user setting (prefer user override when provided)
        show_thinking = (
            user_valves.SHOW_THINKING
            if user_valves.SHOW_THINKING is not None
            else self.valves.SHOW_THINKING
        )

        # 1. Determine the actual model ID to use
        # Priority: __metadata__.base_model_id (for custom models/characters) > request_model
        resolved_id = request_model
        model_source_type = "selected"

        if __metadata__ and __metadata__.get("base_model_id"):
            resolved_id = __metadata__.get("base_model_id", "")
            model_source_type = "base"

        # 2. Strip prefixes to get the clean model ID (e.g. 'gpt-4o')
        real_model_id = self._strip_model_prefix(resolved_id)

        # 3. Log the resolution result
        if real_model_id != request_model:
            log_msg = (
                f"Using {model_source_type} model: {real_model_id} "
                f"(Cleaned from '{resolved_id}')"
            )
            await self._emit_debug_log(
                log_msg,
                __event_call__,
                debug_enabled=effective_debug,
            )

        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        # Get Chat ID using improved helper
        chat_ctx = self._get_chat_context(
            body, __metadata__, __event_call__, debug_enabled=effective_debug
        )
        chat_id = chat_ctx.get("chat_id")

        # Extract system prompt from multiple sources
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
                f"Resolved system prompt source: {system_prompt_source} (length: {len(system_prompt_content) if system_prompt_content else 0})",
                __event_call__,
                debug_enabled=effective_debug,
            )

        is_streaming = body.get("stream", False)
        await self._emit_debug_log(
            f"Streaming request: {is_streaming}",
            __event_call__,
            debug_enabled=effective_debug,
        )

        last_text, attachments = self._process_images(
            messages, __event_call__, debug_enabled=effective_debug
        )

        # Determine prompt strategy
        # If we have a chat_id, we try to resume session.
        # If resumed, we assume the session has history, so we only send the last message.
        # If new session, we send full (accumulated) messages.

        # Ensure we have the latest config
        # Determine if the currently selected model is a BYOK model or a Standard model
        # Detection priority:
        # 1. Check body.metadata.model.name for multiplier info (most direct)
        # 2. Check model cache for explicit 'source' field
        # 3. Check if model name in cache contains multiplier info
        # 4. Fallback heuristics
        import re

        is_byok_model = False
        model_display_name = ""

        # Method 1: Get model name from various metadata sources
        body_metadata = body.get("metadata", {})
        if not isinstance(body_metadata, dict):
            body_metadata = {}

        # Priority: body.metadata.model.name > __metadata__.model.name > __metadata__.model_name
        meta_model = body_metadata.get("model", {})
        if isinstance(meta_model, dict):
            model_display_name = meta_model.get("name", "")

        if not model_display_name and __metadata__:
            # Check __metadata__['model'] which we saw in the logs
            model_obj = __metadata__.get("model", {})
            if isinstance(model_obj, dict):
                model_display_name = model_obj.get("name", "")
            elif isinstance(model_obj, str):
                model_display_name = model_obj

            # Further fallbacks
            if not model_display_name:
                model_display_name = __metadata__.get(
                    "model_name", ""
                ) or __metadata__.get("name", "")

        if not model_display_name:
            # Last resort: log keys and 'model' type for future debugging
            meta_keys = list(body_metadata.keys())
            extra_keys = list(__metadata__.keys()) if __metadata__ else []
            model_val = __metadata__.get("model") if __metadata__ else None
            await self._emit_debug_log(
                f"Debug: Name not found. body.meta keys: {meta_keys}, __meta__ keys: {extra_keys}, model_type: {type(model_val)}",
                __event_call__,
                debug_enabled=effective_debug,
            )

        if model_display_name:
            # Copilot models have multiplier info like "(0x)", "(1x)", "(0.5x)" or Chinese "（1x）"
            has_multiplier = bool(re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", model_display_name))
            
            # Logic: If Custom Model name lacks multiplier, check the Base Model's official name
            if not has_multiplier:
                # Ensure cache is populated
                if not self._model_cache:
                    try:
                        await self.pipes()
                    except:
                        pass
                
                # Lookup base model in cache to check its official name
                cached_model = next(
                    (m for m in self._model_cache if m.get("raw_id") == real_model_id or m.get("id") == real_model_id or m.get("id") == f"{self.id}-{real_model_id}"), 
                    None
                )
                
                if cached_model:
                    cached_name = cached_model.get("name", "")
                    if re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", cached_name):
                        has_multiplier = True
                        await self._emit_debug_log(
                            f"Correction: Found multiplier in Base Model name '{cached_name}' for Custom Model '{model_display_name}'. Treated as Standard Copilot.",
                            __event_call__,
                            debug_enabled=effective_debug,
                        )

            is_byok_model = not has_multiplier and byok_active

            await self._emit_debug_log(
                f"BYOK detection via display name: '{model_display_name}' -> multiplier={has_multiplier}, is_byok={is_byok_model}",
                __event_call__,
                debug_enabled=effective_debug,
            )
        else:
            # Fallback: lookup from cache
            if not self._model_cache:
                try:
                    await self.pipes()
                except:
                    pass

            # For custom models, use base_model_id to find the actual model info
            base_model_id_from_meta = (
                __metadata__.get("base_model_id", "") if __metadata__ else ""
            )
            lookup_model_id = (
                base_model_id_from_meta if base_model_id_from_meta else request_model
            )

            model_info = next(
                (m for m in (self._model_cache or []) if m["id"] == lookup_model_id),
                None,
            )

            if model_info:
                if "source" in model_info:
                    is_byok_model = model_info["source"] == "byok"
                    await self._emit_debug_log(
                        f"BYOK detection via cache source: '{model_info.get('id')}' source='{model_info['source']}' -> is_byok={is_byok_model}",
                        __event_call__,
                        debug_enabled=effective_debug,
                    )
                else:
                    model_name = model_info.get("name", "")
                    has_multiplier = bool(
                        re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", model_name)
                    )
                    is_byok_model = not has_multiplier and byok_active
                    await self._emit_debug_log(
                        f"BYOK detection via cache name: '{model_name}' -> multiplier={has_multiplier}, is_byok={is_byok_model}",
                        __event_call__,
                        debug_enabled=effective_debug,
                    )
            else:
                # Fallback to heuristics if model not in cache
                if byok_active:
                    if not gh_token:
                        is_byok_model = True
                    elif real_model_id.startswith("copilot-"):
                        # If ID starts with copilot-, assume it's NOT BYOK even if list is old
                        is_byok_model = False
                    elif real_model_id not in self._standard_model_ids:
                        is_byok_model = True
                await self._emit_debug_log(
                    f"BYOK detection via heuristics: model_id='{real_model_id}', byok_active={byok_active} -> is_byok={is_byok_model}",
                    __event_call__,
                    debug_enabled=effective_debug,
                )

        # Ensure we have the latest config (only for standard Copilot models)
        if not is_byok_model:
            self._sync_copilot_config(effective_reasoning_effort, __event_call__)

        # Initialize Client
        client = CopilotClient(self._build_client_config(body))
        should_stop_client = True
        try:
            await client.start()

            # Initialize custom tools (Handles caching internally)
            custom_tools = await self._initialize_custom_tools(
                __user__=__user__, __event_call__=__event_call__
            )
            if custom_tools:
                tool_names = [t.name for t in custom_tools]
                await self._emit_debug_log(
                    f"Enabled {len(custom_tools)} tools (Custom/Built-in)",
                    __event_call__,
                )

            # Check MCP Servers
            mcp_servers = self._parse_mcp_servers()
            mcp_server_names = list(mcp_servers.keys()) if mcp_servers else []
            if mcp_server_names:
                await self._emit_debug_log(
                    f"🔌 MCP Servers Configured: {mcp_server_names}",
                    __event_call__,
                )
            else:
                await self._emit_debug_log(
                    "ℹ️ No MCP tool servers found in OpenWebUI Connections.",
                    __event_call__,
                )

            # Create or Resume Session
            session = None
            is_new_session = True

            # Build BYOK Provider Config
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
                pass

            if chat_id:
                try:
                    # Prepare resume config (Requires github-copilot-sdk >= 0.1.23)
                    resume_params = {
                        "model": real_model_id,
                        "streaming": is_streaming,
                        "tools": custom_tools,
                        "available_tools": (
                            [t.name for t in custom_tools] if custom_tools else None
                        ),
                    }
                    if mcp_servers:
                        resume_params["mcp_servers"] = mcp_servers

                    # Always inject the latest system prompt in 'replace' mode
                    # This handles both custom models and user-defined system messages
                    system_parts = []
                    if system_prompt_content:
                        system_parts.append(system_prompt_content.strip())
                    system_parts.append(FORMATTING_GUIDELINES)
                    final_system_msg = "\n".join(system_parts)

                    resume_params["system_message"] = {
                        "mode": "replace",
                        "content": final_system_msg,
                    }

                    preview = final_system_msg[:100].replace("\n", " ")
                    await self._emit_debug_log(
                        f"Resuming session {chat_id}. Injecting System Prompt ({len(final_system_msg)} chars). Mode: REPLACE. Content Preview: {preview}...",
                        __event_call__,
                        debug_enabled=effective_debug,
                    )

                    # Update provider if needed (BYOK support during resume)
                    if provider_config:
                        resume_params["provider"] = provider_config
                        await self._emit_debug_log(
                            f"BYOK provider config included: type={provider_config.get('type')}, base_url={provider_config.get('base_url')}",
                            __event_call__,
                            debug_enabled=effective_debug,
                        )

                    # Debug: Log the full resume_params structure
                    await self._emit_debug_log(
                        f"resume_params keys: {list(resume_params.keys())}. system_message mode: {resume_params.get('system_message', {}).get('mode')}",
                        __event_call__,
                        debug_enabled=effective_debug,
                    )

                    session = await client.resume_session(chat_id, resume_params)
                    await self._emit_debug_log(
                        f"Successfully resumed session {chat_id} with model {real_model_id}",
                        __event_call__,
                    )
                    is_new_session = False
                except Exception as e:
                    await self._emit_debug_log(
                        f"Session {chat_id} not found or failed to resume ({str(e)}), creating new.",
                        __event_call__,
                    )

            if session is None:
                is_new_session = True
                session_config = self._build_session_config(
                    chat_id,
                    real_model_id,
                    custom_tools,
                    system_prompt_content,
                    is_streaming,
                    provider_config=provider_config,
                )

                await self._emit_debug_log(
                    f"Injecting system prompt into new session (len: {len(system_prompt_content or '') + len(FORMATTING_GUIDELINES)})",
                    __event_call__,
                )

                session = await client.create_session(config=session_config)

                model_type_label = "BYOK" if is_byok_model else "Copilot"
                await self._emit_debug_log(
                    f"New {model_type_label} session created. Selected: '{request_model}', Effective ID: '{real_model_id}'",
                    __event_call__,
                    debug_enabled=effective_debug,
                )

                # Show workspace info for new sessions
                if self.valves.DEBUG:
                    if session.workspace_path:
                        await self._emit_debug_log(
                            f"Session workspace: {session.workspace_path}",
                            __event_call__,
                        )

            # Construct Prompt (session-based: send only latest user input)
            # SDK testing confirmed session.resume correctly applies system_message updates,
            # so we simply use the user's input as the prompt.
            prompt = last_text

            await self._emit_debug_log(
                f"Sending prompt ({len(prompt)} chars) to Agent...",
                __event_call__,
            )

            send_payload = {"prompt": prompt, "mode": "immediate"}
            if attachments:
                send_payload["attachments"] = attachments

            # Note: temperature, top_p, max_tokens are not supported by the SDK's
            # session.send() method. These generation parameters would need to be
            # handled at a different level if the underlying provider supports them.

            if body.get("stream", False):
                init_msg = ""
                if effective_debug:
                    init_msg = (
                        f"> [Debug] Agent working in: {self._get_workspace_dir()}\n"
                    )
                    if mcp_server_names:
                        init_msg += f"> [Debug] 🔌 Connected MCP Servers: {', '.join(mcp_server_names)}\n"

                # Transfer client ownership to stream_response
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
                    return response.data.content if response else "Empty response."
                finally:
                    # Cleanup: destroy session if no chat_id (temporary session)
                    if not chat_id:
                        try:
                            await session.destroy()
                        except Exception as cleanup_error:
                            await self._emit_debug_log(
                                f"Session cleanup warning: {cleanup_error}",
                                __event_call__,
                            )
        except Exception as e:
            await self._emit_debug_log(
                f"Request Error: {e}", __event_call__, debug_enabled=effective_debug
            )
            return f"Error: {str(e)}"
        finally:
            # Cleanup client if not transferred to stream
            if should_stop_client:
                try:
                    await client.stop()
                except Exception as e:
                    await self._emit_debug_log(
                        f"Client cleanup warning: {e}",
                        __event_call__,
                        debug_enabled=effective_debug,
                    )

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
        Stream response from Copilot SDK, handling various event types.
        Follows official SDK patterns for event handling and streaming.
        """
        from copilot.generated.session_events import SessionEventType

        queue = asyncio.Queue()
        done = asyncio.Event()
        SENTINEL = object()
        # Use local state to handle concurrency and tracking
        state = {"thinking_started": False, "content_sent": False}
        has_content = False  # Track if any content has been yielded
        active_tools = {}  # Map tool_call_id to tool_name

        def get_event_type(event) -> str:
            """Extract event type as string, handling both enum and string types."""
            if hasattr(event, "type"):
                event_type = event.type
                # Handle SessionEventType enum
                if hasattr(event_type, "value"):
                    return event_type.value
                return str(event_type)
            return "unknown"

        def safe_get_data_attr(event, attr: str, default=None):
            """
            Safely extract attribute from event.data.
            Handles both dict access and object attribute access.
            """
            if not hasattr(event, "data") or event.data is None:
                return default

            data = event.data

            # Try as dict first
            if isinstance(data, dict):
                return data.get(attr, default)

            # Try as object attribute
            return getattr(data, attr, default)

        def handler(event):
            """
            Event handler following official SDK patterns.
            Processes streaming deltas, reasoning, tool events, and session state.
            """
            event_type = get_event_type(event)

            # === Message Delta Events (Primary streaming content) ===
            if event_type == "assistant.message_delta":
                # Official: event.data.delta_content for Python SDK
                delta = safe_get_data_attr(
                    event, "delta_content"
                ) or safe_get_data_attr(event, "deltaContent")
                if delta:
                    state["content_sent"] = True
                    if state["thinking_started"]:
                        queue.put_nowait("\n</think>\n")
                        state["thinking_started"] = False
                    queue.put_nowait(delta)

            # === Complete Message Event (Non-streaming response) ===
            elif event_type == "assistant.message":
                # Handle complete message (when SDK returns full content instead of deltas)
                # IMPORTANT: Skip if we already received delta content to avoid duplication.
                # The SDK may emit both delta and full message events.
                if state["content_sent"]:
                    return
                content = safe_get_data_attr(event, "content") or safe_get_data_attr(
                    event, "message"
                )
                if content:
                    state["content_sent"] = True
                    if state["thinking_started"]:
                        queue.put_nowait("\n</think>\n")
                        state["thinking_started"] = False
                    queue.put_nowait(content)

            # === Reasoning Delta Events (Chain-of-thought streaming) ===
            elif event_type == "assistant.reasoning_delta":
                delta = safe_get_data_attr(
                    event, "delta_content"
                ) or safe_get_data_attr(event, "deltaContent")
                if delta:
                    # Suppress late-arriving reasoning if content already started
                    if state["content_sent"]:
                        return

                    # Use UserValves or Global Valve for thinking visibility
                    if not state["thinking_started"] and show_thinking:
                        queue.put_nowait("<think>\n")
                        state["thinking_started"] = True
                    if state["thinking_started"]:
                        queue.put_nowait(delta)

            # === Complete Reasoning Event (Non-streaming reasoning) ===
            elif event_type == "assistant.reasoning":
                # Handle complete reasoning content
                reasoning = safe_get_data_attr(event, "content") or safe_get_data_attr(
                    event, "reasoning"
                )
                if reasoning:
                    # Suppress late-arriving reasoning if content already started
                    if state["content_sent"]:
                        return

                    if not state["thinking_started"] and show_thinking:
                        queue.put_nowait("<think>\n")
                        state["thinking_started"] = True
                    if state["thinking_started"]:
                        queue.put_nowait(reasoning)

            # === Tool Execution Events ===
            elif event_type == "tool.execution_start":
                tool_name = (
                    safe_get_data_attr(event, "name")
                    or safe_get_data_attr(event, "tool_name")
                    or "Unknown Tool"
                )
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")

                # Get tool arguments
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

                # Close thinking tag if open before showing tool
                if state["thinking_started"]:
                    queue.put_nowait("\n</think>\n")
                    state["thinking_started"] = False

                # Display tool call with improved formatting
                if tool_args:
                    tool_args_json = json.dumps(tool_args, indent=2, ensure_ascii=False)
                    tool_display = f"\n\n<details>\n<summary>🔧 Executing Tool: {tool_name}</summary>\n\n**Parameters:**\n\n```json\n{tool_args_json}\n```\n\n</details>\n\n"
                else:
                    tool_display = f"\n\n<details>\n<summary>🔧 Executing Tool: {tool_name}</summary>\n\n*No parameters*\n\n</details>\n\n"

                queue.put_nowait(tool_display)

                self._emit_debug_log_sync(f"Tool Start: {tool_name}", __event_call__)

            elif event_type == "tool.execution_complete":
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)

                # Handle both old string format and new dict format
                if isinstance(tool_info, str):
                    tool_name = tool_info
                elif isinstance(tool_info, dict):
                    tool_name = tool_info.get("name", "Unknown Tool")
                else:
                    tool_name = "Unknown Tool"

                # Try to get result content
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
                            # Try to serialize the entire dict if no content field
                            result_content = json.dumps(
                                result_obj, indent=2, ensure_ascii=False
                            )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"Error extracting result: {e}", __event_call__
                    )
                    result_type = "failure"
                    result_content = f"Error: {str(e)}"

                # Display tool result with improved formatting
                if result_content:
                    status_icon = "✅" if result_type == "success" else "❌"

                    # Try to detect content type for better formatting
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

                    # Format based on content type
                    if is_json:
                        # JSON content: use code block with syntax highlighting
                        result_display = f"\n<details>\n<summary>{status_icon} Tool Result: {tool_name}</summary>\n\n```json\n{result_content}\n```\n\n</details>\n\n"
                    else:
                        # Plain text: use text code block to preserve formatting and add line breaks
                        result_display = f"\n<details>\n<summary>{status_icon} Tool Result: {tool_name}</summary>\n\n```text\n{result_content}\n```\n\n</details>\n\n"

                    queue.put_nowait(result_display)

            elif event_type == "tool.execution_progress":
                # Tool execution progress update (for long-running tools)
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)
                tool_name = (
                    tool_info.get("name", "Unknown Tool")
                    if isinstance(tool_info, dict)
                    else "Unknown Tool"
                )

                progress = safe_get_data_attr(event, "progress", 0)
                message = safe_get_data_attr(event, "message", "")

                if message:
                    progress_display = f"\n> 🔄 **{tool_name}**: {message}\n"
                    queue.put_nowait(progress_display)

                self._emit_debug_log_sync(
                    f"Tool Progress: {tool_name} - {progress}%", __event_call__
                )

            elif event_type == "tool.execution_partial_result":
                # Streaming tool results (for tools that output incrementally)
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)
                tool_name = (
                    tool_info.get("name", "Unknown Tool")
                    if isinstance(tool_info, dict)
                    else "Unknown Tool"
                )

                partial_content = safe_get_data_attr(event, "content", "")
                if partial_content:
                    queue.put_nowait(partial_content)

                self._emit_debug_log_sync(
                    f"Tool Partial Result: {tool_name}", __event_call__
                )

            # === Usage Statistics Events ===
            elif event_type == "assistant.usage":
                # Token usage for current assistant turn
                if self.valves.DEBUG:
                    input_tokens = safe_get_data_attr(event, "input_tokens", 0)
                    output_tokens = safe_get_data_attr(event, "output_tokens", 0)
                    total_tokens = safe_get_data_attr(event, "total_tokens", 0)
                pass

            elif event_type == "session.usage_info":
                # Cumulative session usage information
                pass

            elif event_type == "session.compaction_complete":
                self._emit_debug_log_sync(
                    "Session Compaction Completed", __event_call__
                )

            elif event_type == "session.idle":
                # Session finished processing - signal completion
                done.set()
                try:
                    queue.put_nowait(SENTINEL)
                except:
                    pass

            elif event_type == "session.error":
                error_msg = safe_get_data_attr(event, "message", "Unknown Error")
                queue.put_nowait(f"\n[Error: {error_msg}]")
                done.set()
                try:
                    queue.put_nowait(SENTINEL)
                except:
                    pass

        unsubscribe = session.on(handler)

        self._emit_debug_log_sync(
            f"Subscribed to events. Sending request...", __event_call__
        )

        # Use asyncio.create_task used to prevent session.send from blocking the stream reading
        # if the SDK implementation waits for completion.
        send_task = asyncio.create_task(session.send(send_payload))
        self._emit_debug_log_sync(f"Prompt sent (async task started)", __event_call__)

        # Safe initial yield with error handling
        try:
            if self.valves.DEBUG and show_thinking:
                yield "<think>\n"
                if init_message:
                    yield init_message

                if reasoning_effort and reasoning_effort != "off":
                    yield f"> [Debug] Reasoning Effort injected: {reasoning_effort.upper()}\n"

                yield "> [Debug] Connection established, waiting for response...\n"
                state["thinking_started"] = True
        except Exception as e:
            # If initial yield fails, log but continue processing
            self._emit_debug_log_sync(f"Initial yield warning: {e}", __event_call__)

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
                            # Connection closed by client, stop gracefully
                            self._emit_debug_log_sync(
                                f"Yield error (client disconnected?): {yield_error}",
                                __event_call__,
                            )
                            break
                except asyncio.TimeoutError:
                    if done.is_set():
                        break
                    if state["thinking_started"]:
                        try:
                            yield f"> [Debug] Waiting for response ({self.valves.TIMEOUT}s exceeded)...\n"
                        except:
                            # If yield fails during timeout, connection is gone
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
                        # Connection closed, stop yielding
                        break

            if state["thinking_started"]:
                try:
                    yield "\n</think>\n"
                    has_content = True
                except:
                    pass  # Connection closed

            # Core fix: If no content was yielded, return a fallback message to prevent OpenWebUI error
            if not has_content:
                try:
                    yield "⚠️ Copilot returned no content. Please check if the Model ID is correct or enable DEBUG mode in Valves for details."
                except:
                    pass  # Connection already closed

        except Exception as e:
            try:
                yield f"\n[Stream Error: {str(e)}]"
            except:
                pass  # Connection already closed
        finally:
            unsubscribe()
            # Cleanup client and session
            try:
                # We do not destroy session here to allow persistence,
                # but we must stop the client.
                await client.stop()
            except Exception as e:
                pass
