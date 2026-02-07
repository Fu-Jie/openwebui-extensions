"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
openwebui_id: ce96f7b4-12fc-4ac3-9a01-875713e69359
description: Integrate GitHub Copilot SDK. Supports dynamic models, multi-turn conversation, streaming, multimodal input, infinite sessions, and frontend debug logging.
version: 0.3.1
requirements: github-copilot-sdk==0.1.22
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
from pathlib import Path
from typing import Optional, Union, AsyncGenerator, List, Any, Dict
from types import SimpleNamespace
from pydantic import BaseModel, Field, create_model

# Import copilot SDK modules
from copilot import CopilotClient, define_tool

# Import Tool Server Connections and Tool System from OpenWebUI Config
from open_webui.config import TOOL_SERVER_CONNECTIONS
from open_webui.utils.tools import get_tools as get_openwebui_tools
from open_webui.models.tools import Tools
from open_webui.models.users import Users

# Setup logger
logger = logging.getLogger(__name__)


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (Requires 'Copilot Requests' permission)",
        )
        COPILOT_CLI_VERSION: str = Field(
            default="0.0.405",
            description="Specific Copilot CLI version to install/enforce (e.g. '0.0.405'). Leave empty for latest.",
        )
        DEBUG: bool = Field(
            default=False,
            description="Enable technical debug logs (connection info, etc.)",
        )
        LOG_LEVEL: str = Field(
            default="error",
            description="Copilot CLI log level: none, error, warning, info, debug, all",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="Show model reasoning/thinking process",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="Exclude models containing these keywords (comma separated, e.g.: codex, haiku)",
        )
        WORKSPACE_DIR: str = Field(
            default="",
            description="Restricted workspace directory for file operations. If empty, allows access to the current process directory.",
        )
        INFINITE_SESSION: bool = Field(
            default=True,
            description="Enable Infinite Sessions (automatic context compaction)",
        )
        COMPACTION_THRESHOLD: float = Field(
            default=0.8,
            description="Background compaction threshold (0.0-1.0)",
        )
        BUFFER_THRESHOLD: float = Field(
            default=0.95,
            description="Buffer exhaustion threshold (0.0-1.0)",
        )
        TIMEOUT: int = Field(
            default=300,
            description="Timeout for each stream chunk (seconds)",
        )
        CUSTOM_ENV_VARS: str = Field(
            default="",
            description='Custom environment variables (JSON format, e.g., {"VAR": "value"})',
        )

        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Tool Server Tools).",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="Enable Direct MCP Client connection (Recommended).",
        )
        REASONING_EFFORT: str = Field(
            default="medium",
            description="Reasoning effort level: low, medium, high. (gpt-5.2-codex also supports xhigh)",
        )
        ENFORCE_FORMATTING: bool = Field(
            default=True,
            description="Add formatting instructions to system prompt for better readability (paragraphs, line breaks, structure).",
        )
        ALLOWED_AGENT_MODELS: str = Field(
            default="",
            description="Comma-separated allowlist of models that can be used to spawn agents. If empty, no server-side restriction is enforced.",
        )
        FALLBACK_AGENT_MODEL: str = Field(
            default="",
            description="Optional fallback model to use if requested model is not in the allowlist. If empty, disallowed models will be rejected.",
        )

    class UserValves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="Personal GitHub Fine-grained Token (overrides global setting)",
        )
        REASONING_EFFORT: str = Field(
            default="",
            description="Reasoning effort level (low, medium, high, xhigh). Leave empty to use global setting.",
        )
        DEBUG: bool = Field(
            default=False,
            description="Enable technical debug logs (connection info, etc.)",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="Show model reasoning/thinking process",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Tool Server Tools).",
        )
        ENABLE_MCP_SERVER: bool = Field(
            default=True,
            description="Enable dynamic MCP server loading (overrides global).",
        )

        ENFORCE_FORMATTING: bool = Field(
            default=True,
            description="Enforce formatting guidelines (overrides global)",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "copilotsdk"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")
        self.thinking_started = False
        self._model_cache = []  # Model list cache
        self._last_update_check = 0  # Timestamp of last CLI update check

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

        # Load OpenWebUI tools dynamically
        openwebui_tools = await self._load_openwebui_tools(
            __user__=__user__, __event_call__=__event_call__
        )

        return openwebui_tools

    def _json_schema_to_python_type(self, schema: dict) -> Any:
        """Convert JSON Schema type to Python type for Pydantic models."""
        if not isinstance(schema, dict):
            return Any

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
                        Field(default=None, description=description),
                    )
                else:
                    fields[param_name] = (optional_type, None)

        if fields:
            ParamsModel = create_model(f"{sanitized_tool_name}_Params", **fields)
        else:
            ParamsModel = create_model(f"{sanitized_tool_name}_Params")

        tool_callable = tool_dict.get("callable")
        tool_description = spec.get("description", "") if isinstance(spec, dict) else ""
        if not tool_description and isinstance(spec, dict):
            tool_description = spec.get("summary", "")

        # Critical: If the tool name was sanitized (e.g. Chinese -> Hash), instructions are lost.
        # We must inject the original name into the description so the model knows what it is.
        if sanitized_tool_name != tool_name:
            tool_description = f"Function '{tool_name}': {tool_description}"

        async def _tool(params):
            payload = params.model_dump() if hasattr(params, "model_dump") else {}
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

    def _build_openwebui_request(self):
        """Build a minimal request-like object for OpenWebUI tool loading."""
        app_state = SimpleNamespace(
            config=SimpleNamespace(
                TOOL_SERVER_CONNECTIONS=TOOL_SERVER_CONNECTIONS.value
            ),
            TOOLS={},
        )
        app = SimpleNamespace(state=app_state)
        request = SimpleNamespace(
            app=app,
            cookies={},
            state=SimpleNamespace(token=SimpleNamespace(credentials="")),
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

        request = self._build_openwebui_request()
        extra_params = {
            "__request__": request,
            "__user__": user_data,
            "__event_emitter__": None,
            "__event_call__": __event_call__,
            "__chat_id__": None,
            "__message_id__": None,
            "__model_knowledge__": [],
        }

        tools_dict = await get_openwebui_tools(request, tool_ids, user, extra_params)
        if not tools_dict:
            return []

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

                mcp_servers[server_id] = {
                    "type": "http",
                    "url": url,
                    "headers": headers,
                    "tools": ["*"],  # Enable all tools by default
                }

        return mcp_servers if mcp_servers else None

    async def _emit_debug_log(self, message: str, __event_call__=None):
        """Emit debug log to frontend (console) when DEBUG is enabled."""
        # Check user config first if available (will need to be passed down or stored)
        # For now we only check global valves in this helper, but in pipe implementation we respect user setting.
        # This helper might need refactoring to accept user_debug_setting
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
            logger.debug(f"[Copilot Pipe] Frontend debug log failed: {e}")

    def _emit_debug_log_sync(self, message: str, __event_call__=None):
        """Sync wrapper for debug logging in non-async contexts."""
        if not self.valves.DEBUG:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug(f"[Copilot Pipe] {message}")
            return

        loop.create_task(self._emit_debug_log(message, __event_call__))

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
        """Append a lightweight formatting hint to the user prompt when enabled."""
        if not self.valves.ENFORCE_FORMATTING:
            return prompt

        if not prompt:
            return prompt

        if "[Formatting Guidelines]" in prompt or "[Formatting Request]" in prompt:
            return prompt

        formatting_hint = (
            "\n\n[Formatting Request]\n"
            "Please format your response with clear paragraph breaks, short sentences, "
            "and bullet lists when appropriate."
        )
        return f"{prompt}{formatting_hint}"

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

    def _collect_model_ids(
        self, body: dict, request_model: str, real_model_id: str
    ) -> List[str]:
        """Collect possible model IDs from request/metadata/body params."""
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
        """Extract system prompt from metadata/model DB/body/messages."""
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
                        f"Extracted system prompt from metadata.model.params (length: {len(system_prompt_content)})",
                        __event_call__,
                    )

        # 2) model DB lookup
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
                                    f"Extracted system prompt from model DB (length: {len(system_prompt_content)})",
                                    __event_call__,
                                )
                                break
            except Exception as e:
                await self._emit_debug_log(
                    f"Failed to extract system prompt from model DB: {e}",
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
                        f"Extracted system prompt from body.params (length: {len(system_prompt_content)})",
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
                            f"Extracted system prompt from messages (length: {len(system_prompt_content)})",
                            __event_call__,
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

    def _parse_allowed_models(self) -> list:
        """Parse ALLOWED_AGENT_MODELS valve into a list of model IDs."""
        if not self.valves.ALLOWED_AGENT_MODELS:
            return []
        return [
            model.strip()
            for model in self.valves.ALLOWED_AGENT_MODELS.split(",")
            if model.strip()
        ]

    def _sanitize_model(self, requested_model: str) -> str:
        """
        Enforce model allowlist and fallback logic.
        
        Returns the validated or fallback model ID.
        Raises ValueError if the model is disallowed and no fallback is available.
        """
        allowed_models = self._parse_allowed_models()
        
        # If no allowlist is configured, allow any model (backward compatible)
        if not allowed_models:
            return requested_model
        
        # Check if requested model is in allowlist
        if requested_model in allowed_models:
            return requested_model
        
        # Model is not allowed - check for fallback
        fallback_model = self.valves.FALLBACK_AGENT_MODEL.strip()
        
        if fallback_model:
            # Verify fallback is in allowlist
            if fallback_model in allowed_models:
                logger.info(
                    f"Model '{requested_model}' not in allowlist. Using fallback: {fallback_model}"
                )
                return fallback_model
            else:
                raise ValueError(
                    f"Model '{requested_model}' not in allowlist, and fallback model '{fallback_model}' is also not in allowlist."
                )
        else:
            raise ValueError(
                f"Model '{requested_model}' is not in the allowed models list: {', '.join(allowed_models)}"
            )

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

        system_message_config = None
        if system_prompt_content or self.valves.ENFORCE_FORMATTING:
            # Build system message content
            system_parts = []

            if system_prompt_content:
                system_parts.append(system_prompt_content)

            if self.valves.ENFORCE_FORMATTING:
                formatting_instruction = (
                    "\n\n[Formatting Guidelines]\n"
                    "When providing explanations or descriptions:\n"
                    "- Use clear paragraph breaks (double line breaks)\n"
                    "- Break long sentences into multiple shorter ones\n"
                    "- Use bullet points or numbered lists for multiple items\n"
                    "- Add headings (##, ###) for major sections\n"
                    "- Ensure proper spacing between different topics"
                )
                system_parts.append(formatting_instruction)
                logger.info(
                    f"[ENFORCE_FORMATTING] Added formatting instructions to system prompt"
                )

            if system_parts:
                system_message_config = {
                    "mode": "append",
                    "content": "\n".join(system_parts),
                }

        # Prepare session config parameters
        session_params = {
            "session_id": chat_id if chat_id else None,
            "model": real_model_id,
            "streaming": is_streaming,
            "tools": custom_tools,
            "system_message": system_message_config,
            "infinite_sessions": infinite_session_config,
        }

        mcp_servers = self._parse_mcp_servers()
        if mcp_servers:
            session_params["mcp_servers"] = mcp_servers

        return SessionConfig(**session_params)

    def _get_user_context(self):
        """Helper to get user context (placeholder for future use)."""
        return {}

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None, __event_call__=None
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
                f"Extracted ChatID: {chat_id} (Source: {source})", __event_call__
            )
        else:
            # If still not found, log body keys for troubleshooting
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log_sync(
                f"Warning: Failed to extract ChatID. Body keys: {keys}",
                __event_call__,
            )

        return {
            "chat_id": str(chat_id).strip(),
        }

    async def pipes(self) -> List[dict]:
        """Dynamically fetch model list"""
        # Return cache if available
        if self._model_cache:
            return self._model_cache

        await self._emit_debug_log("Fetching model list dynamically...")
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

                # Update cache
                self._model_cache = []
                exclude_list = [
                    k.strip().lower()
                    for k in self.valves.EXCLUDE_KEYWORDS.split(",")
                    if k.strip()
                ]

                models_with_info = []
                for m in models:
                    # Compatible with dict and object access
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

                    # Check policy state
                    state = (
                        m_policy.get("state")
                        if isinstance(m_policy, dict)
                        else getattr(m_policy, "state", "enabled")
                    )
                    if state == "disabled":
                        continue

                    # Filtering logic
                    if any(kw in m_id.lower() for kw in exclude_list):
                        continue

                    # Get multiplier
                    multiplier = (
                        m_billing.get("multiplier", 1)
                        if isinstance(m_billing, dict)
                        else getattr(m_billing, "multiplier", 1)
                    )

                    # Format display name
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

                # Sort: multiplier ascending, then raw_id ascending
                models_with_info.sort(key=lambda x: (x["multiplier"], x["raw_id"]))
                self._model_cache = [
                    {"id": m["id"], "name": m["name"]} for m in models_with_info
                ]

                await self._emit_debug_log(
                    f"Successfully fetched {len(self._model_cache)} models (filtered)"
                )
                return self._model_cache
            except Exception as e:
                await self._emit_debug_log(f"Failed to fetch model list: {e}")
                # Return default model on failure
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
        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

        client = CopilotClient(client_config)
        await client.start()
        return client

    def _setup_env(self, __event_call__=None):
        # Default CLI path logic
        cli_path = "/usr/local/bin/copilot"
        if os.environ.get("COPILOT_CLI_PATH"):
            cli_path = os.environ["COPILOT_CLI_PATH"]

        target_version = self.valves.COPILOT_CLI_VERSION.strip()
        found = False
        current_version = None

        # internal helper to get version
        def get_cli_version(path):
            try:
                output = (
                    subprocess.check_output(
                        [path, "--version"], stderr=subprocess.STDOUT
                    )
                    .decode()
                    .strip()
                )
                # Copilot CLI version output format is usually just the version number or "copilot version X.Y.Z"
                # We try to extract X.Y.Z
                match = re.search(r"(\d+\.\d+\.\d+)", output)
                return match.group(1) if match else output
            except Exception:
                return None

        # Check default path
        if os.path.exists(cli_path):
            found = True
            current_version = get_cli_version(cli_path)

        # Check system path if not found
        if not found:
            sys_path = shutil.which("copilot")
            if sys_path:
                cli_path = sys_path
                found = True
                current_version = get_cli_version(cli_path)

        # Determine if we need to install or update
        should_install = False
        install_reason = ""

        if not found:
            should_install = True
            install_reason = "CLI not found"
        elif target_version:
            # Normalize versions for comparison (remove 'v' prefix)
            norm_target = target_version.lstrip("v")
            norm_current = current_version.lstrip("v") if current_version else ""

            if norm_target != norm_current:
                should_install = True
                install_reason = f"Version mismatch (Current: {current_version}, Target: {target_version})"

        if should_install:
            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    f"Installing Copilot CLI: {install_reason}...", __event_call__
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

                # Check default install location first, then system path
                if os.path.exists("/usr/local/bin/copilot"):
                    cli_path = "/usr/local/bin/copilot"
                    found = True
                elif shutil.which("copilot"):
                    cli_path = shutil.which("copilot")
                    found = True

                if found:
                    current_version = get_cli_version(cli_path)
            except Exception as e:
                if self.valves.DEBUG:
                    self._emit_debug_log_sync(
                        f"Failed to install Copilot CLI: {e}", __event_call__
                    )

        if found:
            os.environ["COPILOT_CLI_PATH"] = cli_path
            cli_dir = os.path.dirname(cli_path)
            if cli_dir not in os.environ["PATH"]:
                os.environ["PATH"] = f"{cli_dir}:{os.environ['PATH']}"

            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    f"Copilot CLI found at: {cli_path} (Version: {current_version})",
                    __event_call__,
                )
        else:
            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    "Error: Copilot CLI NOT found. Agent capabilities will be disabled.",
                    __event_call__,
                )

        if self.valves.GH_TOKEN:
            os.environ["GH_TOKEN"] = self.valves.GH_TOKEN
            os.environ["GITHUB_TOKEN"] = self.valves.GH_TOKEN
        else:
            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    "Warning: GH_TOKEN is not set.", __event_call__
                )

        self._sync_mcp_config(__event_call__)

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
                    )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"Failed to write config.json: {e}", __event_call__
                    )
        except Exception as e:
            self._emit_debug_log_sync(f"Config sync check failed: {e}", __event_call__)

    async def _update_copilot_cli(self, cli_path: str, __event_call__=None):
        """Async task to update Copilot CLI if needed."""
        import time

        try:
            # Check frequency (e.g., once every hour)
            now = time.time()
            if now - self._last_update_check < 3600:
                return

            self._last_update_check = now

            # Simple check if "update" command is available or if we should just run it
            # The user requested "async attempt to update copilot cli"

            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    "Triggering async Copilot CLI update check...", __event_call__
                )

            # We create a subprocess to run the update
            process = await asyncio.create_subprocess_exec(
                cli_path,
                "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if self.valves.DEBUG:
                output = stdout.decode().strip() or stderr.decode().strip()
                if output:
                    self._emit_debug_log_sync(
                        f"Async CLI Update result: {output}", __event_call__
                    )

        except Exception as e:
            if self.valves.DEBUG:
                self._emit_debug_log_sync(
                    f"Async CLI Update failed: {e}", __event_call__
                )

    def _sync_mcp_config(self, __event_call__=None):
        """Deprecated: MCP config is now handled dynamically via session config."""
        pass

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
        self._setup_env(__event_call__)

        cwd = self._get_workspace_dir()
        if self.valves.DEBUG:
            await self._emit_debug_log(f"Agent working in: {cwd}", __event_call__)

        if not self.valves.GH_TOKEN:
            return "Error: Please configure GH_TOKEN in Valves."

        # Trigger async CLI update if configured
        cli_path = os.environ.get("COPILOT_CLI_PATH")
        if cli_path:
            asyncio.create_task(self._update_copilot_cli(cli_path, __event_call__))

        # Parse user selected model
        request_model = body.get("model", "")
        real_model_id = request_model

        # Determine effective reasoning effort and debug setting
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
        # Apply DEBUG user setting override if set to True (if False, respect global)
        # Actually user setting should probably override strictly.
        # But boolean fields in UserValves default to False, so we can't distinguish "not set" from "off" easily without Optional[bool]
        # Let's assume if user sets DEBUG=True, it wins.
        if user_valves.DEBUG:
            self.valves.DEBUG = True

        # Apply SHOW_THINKING user setting (prefer user override when provided)
        show_thinking = (
            user_valves.SHOW_THINKING
            if user_valves.SHOW_THINKING is not None
            else self.valves.SHOW_THINKING
        )

        if request_model.startswith(f"{self.id}-"):
            real_model_id = request_model[len(f"{self.id}-") :]
            await self._emit_debug_log(
                f"Using selected model: {real_model_id}", __event_call__
            )
        elif __metadata__ and __metadata__.get("base_model_id"):
            base_model_id = __metadata__.get("base_model_id", "")
            if base_model_id.startswith(f"{self.id}-"):
                real_model_id = base_model_id[len(f"{self.id}-") :]
                await self._emit_debug_log(
                    f"Using base model: {real_model_id} (derived from custom model {request_model})",
                    __event_call__,
                )

        # Enforce model allowlist and fallback (if configured)
        try:
            real_model_id = self._sanitize_model(real_model_id)
        except ValueError as e:
            await self._emit_debug_log(
                f"Blocked agent spawn attempt: {e}", __event_call__
            )
            return f"Error: {str(e)}"

        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        # Get Chat ID using improved helper
        chat_ctx = self._get_chat_context(body, __metadata__, __event_call__)
        chat_id = chat_ctx.get("chat_id")

        # Extract system prompt from multiple sources
        system_prompt_content, system_prompt_source = await self._extract_system_prompt(
            body, messages, request_model, real_model_id, __event_call__
        )

        if system_prompt_content:
            preview = system_prompt_content[:60].replace("\n", " ")
            await self._emit_debug_log(
                f"System prompt confirmed (source: {system_prompt_source}, length: {len(system_prompt_content)}, preview: {preview})",
                __event_call__,
            )

        is_streaming = body.get("stream", False)
        await self._emit_debug_log(f"Request Streaming: {is_streaming}", __event_call__)

        last_text, attachments = self._process_images(messages, __event_call__)

        # Determine prompt strategy
        # If we have a chat_id, we try to resume session.
        # If resumed, we assume the session has history, so we only send the last message.
        # If new session, we send full (accumulated) messages.

        # Ensure we have the latest config
        self._sync_copilot_config(effective_reasoning_effort, __event_call__)

        # Initialize Client
        client = CopilotClient(self._build_client_config(body))
        should_stop_client = True
        try:
            await client.start()

            # Initialize custom tools
            custom_tools = await self._initialize_custom_tools(
                __user__=__user__, __event_call__=__event_call__
            )
            if custom_tools:
                tool_names = [t.name for t in custom_tools]
                await self._emit_debug_log(
                    f"Enabled {len(custom_tools)} custom tools: {tool_names}",
                    __event_call__,
                )
                if self.valves.DEBUG:
                    for t in custom_tools:
                        await self._emit_debug_log(
                            f"📋 Tool Detail: {t.name} - {t.description[:100]}...",
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
            if chat_id:
                try:
                    # Prepare resume config
                    resume_params = {}
                    if mcp_servers:
                        resume_params["mcp_servers"] = mcp_servers

                    session = (
                        await client.resume_session(chat_id, resume_params)
                        if resume_params
                        else await client.resume_session(chat_id)
                    )
                    await self._emit_debug_log(
                        f"Resumed session: {chat_id} (Reasoning: {effective_reasoning_effort or 'default'})",
                        __event_call__,
                    )

                    # Show workspace info of available
                    if self.valves.DEBUG:
                        if session.workspace_path:
                            await self._emit_debug_log(
                                f"Session workspace: {session.workspace_path}",
                                __event_call__,
                            )

                    is_new_session = False
                except Exception as e:
                    await self._emit_debug_log(
                        f"Session {chat_id} not found ({str(e)}), creating new.",
                        __event_call__,
                    )

            if session is None:
                session_config = self._build_session_config(
                    chat_id,
                    real_model_id,
                    custom_tools,
                    system_prompt_content,
                    is_streaming,
                )
                if system_prompt_content or self.valves.ENFORCE_FORMATTING:
                    # Build preview of what's being sent
                    preview_parts = []
                    if system_prompt_content:
                        preview_parts.append(
                            f"custom_prompt: {system_prompt_content[:100]}..."
                        )
                    if self.valves.ENFORCE_FORMATTING:
                        preview_parts.append("formatting_guidelines: enabled")

                    if isinstance(session_config, dict):
                        system_config = session_config.get("system_message", {})
                    else:
                        system_config = getattr(session_config, "system_message", None)

                    if isinstance(system_config, dict):
                        full_content = system_config.get("content", "")
                    else:
                        full_content = ""

                    await self._emit_debug_log(
                        f"System message config - {', '.join(preview_parts)} (total length: {len(full_content)} chars)",
                        __event_call__,
                    )
                session = await client.create_session(config=session_config)
                await self._emit_debug_log(
                    f"Created new session with model: {real_model_id}",
                    __event_call__,
                )

                # Show workspace info for new sessions
                if self.valves.DEBUG:
                    if session.workspace_path:
                        await self._emit_debug_log(
                            f"Session workspace: {session.workspace_path}",
                            __event_call__,
                        )

            # Construct Prompt (session-based: send only latest user input)
            prompt = self._apply_formatting_hint(last_text)

            await self._emit_debug_log(
                f"Sending prompt ({len(prompt)} chars) to Agent...",
                __event_call__,
            )

            send_payload = {"prompt": prompt, "mode": "immediate"}
            if attachments:
                send_payload["attachments"] = attachments

            if body.get("stream", False):
                init_msg = ""
                if self.valves.DEBUG:
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
            await self._emit_debug_log(f"Request Error: {e}", __event_call__)
            return f"Error: {str(e)}"
        finally:
            # Cleanup client if not transferred to stream
            if should_stop_client:
                try:
                    await client.stop()
                except Exception as e:
                    await self._emit_debug_log(
                        f"Client cleanup warning: {e}", __event_call__
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
            if self.valves.DEBUG:
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
