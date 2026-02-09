"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
openwebui_id: ce96f7b4-12fc-4ac3-9a01-875713e69359
description: Integrate GitHub Copilot SDK. Supports dynamic models, multi-turn conversation, streaming, multimodal input, infinite sessions, and frontend debug logging.
version: 0.6.0
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
import contextlib
import traceback
from pathlib import Path
from typing import Optional, Union, AsyncGenerator, List, Any, Dict, Literal, Tuple
from types import SimpleNamespace
from pydantic import BaseModel, Field, create_model

# Database imports
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
from datetime import datetime, timezone

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

# Open WebUI internal database (re-use shared connection)
try:
    from open_webui.internal import db as owui_db
except ImportError:
    owui_db = None

# Setup logger
logger = logging.getLogger(__name__)


def _discover_owui_engine(db_module: Any) -> Optional[Engine]:
    """Discover the Open WebUI SQLAlchemy engine via provided db module helpers."""
    if db_module is None:
        return None

    db_context = getattr(db_module, "get_db_context", None) or getattr(
        db_module, "get_db", None
    )
    if callable(db_context):
        try:
            with db_context() as session:
                try:
                    return session.get_bind()
                except AttributeError:
                    return getattr(session, "bind", None) or getattr(
                        session, "engine", None
                    )
        except Exception as exc:
            logger.error(f"[DB Discover] get_db_context failed: {exc}")

    for attr in ("engine", "ENGINE", "bind", "BIND"):
        candidate = getattr(db_module, attr, None)
        if candidate is not None:
            return candidate

    return None


owui_engine = _discover_owui_engine(owui_db)
owui_Base = (
    getattr(owui_db, "Base", None) if owui_db is not None else declarative_base()
)


class ChatTodo(owui_Base):
    """Chat Todo Storage Table"""

    __tablename__ = "chat_todos"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    metrics = Column(JSON, nullable=True)  # {"total": 39, "completed": 0, "percent": 0}
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Base guidelines for all users
BASE_GUIDELINES = (
    "\n\n[Environment & Capabilities Context]\n"
    "You are an AI assistant operating within a high-capability Linux container environment (OpenWebUI).\n"
    "\n"
    "**System Environment & User Privileges:**\n"
    "- **Output Environment**: You are rendering in the **OpenWebUI Chat Page**, a modern, interactive web interface. Optimize your output format to leverage Markdown for the best UI experience.\n"
    "- **Root Access**: You are running as **root**. You have **READ access to the entire container file system** but you **MUST ONLY WRITE** to your designated persistent workspace directory (structured as `.../user_id/chat_id/`). All other system areas are strictly READ-ONLY.\n"
    "- **STRICT FILE CREATION RULE**: You are **PROHIBITED** from creating or editing files outside of your specific workspace path. Never place files in `/root`, `/tmp`, or `/app` (unless specifically instructed for analysis, but writing is banned). Every file operation (`create`, `edit`, `bash`) MUST use the absolute path provided in your `Session Context` below.\n"
    "- **Filesystem Layout (/app)**:\n"
    "  - `/app/backend`: Python backend source code. You can analyze core package logic here.\n"
    "  - `/app/build`: Compiled frontend assets (assets, static, pyodide, index.html).\n"
    "- **Rich Python Environment**: You can natively import and use any installed OpenWebUI dependencies. You have access to a wealth of libraries (e.g., for data processing, utility functions). However, you **MUST NOT** install new packages in the global environment. If you need additional dependencies, you must create a virtual environment within your designated workspace directory.\n"
    "- **Tool Availability**: You may have access to various tools (OpenWebUI Built-ins, Custom Tools, OpenAPI Servers, or MCP Servers) depending on the user's current configuration. If tools are visible in your session metadata, use them proactively to enhance your task execution.\n"
    "\n"
    "**Formatting & Presentation Directives:**\n"
    "1. **Markdown Excellence**: Leverage full **Markdown** capabilities (headers, bold, italics, tables, lists) to structure your response professionally for the chat interface.\n"
    "2. **Advanced Visualization**: Use **Mermaid** for flowcharts/diagrams and **LaTeX** for math. **IMPORTANT**: Always wrap Mermaid code within a standard ` ```mermaid ` code block to ensure it is rendered correctly by the UI.\n"
    "3. **Interactive Artifacts (HTML)**: Standalone HTML code blocks (HTML+CSS+JS) will be **AUTOMATICALLY RENDERED** as interactive web pages within the chat. **Dual Delivery Protocol**: For web applications, you MUST perform two actions:\n"
    "   - 1. **Persist**: Create the file in the workspace (e.g., `index.html`) for project structure.\n"
    "   - 2. **Render**: Immediately output the SAME code in a ` ```html ` block so the user can interact with it.\n"
    "   - **Result**: The user gets both a saved file AND a live app. Never force the user to choose one over the other.\n"
    "4. **Images & Files**: ALWAYS embed generated images/files directly using `![caption](url)`. Never provide plain text links.\n"
    "5. **TODO Visibility**: Every time you call the `update_todo` tool, you **MUST** immediately follow up with a beautifully formatted **Markdown summary** of the current TODO list. Use task checkboxes (`- [ ]`), progress indicators, and clear headings so the user can see the status directly in the chat.\n"
    "6. **Python Execution Standard**: For ANY task requiring Python logic (not just data analysis), you **MUST NOT** embed multi-line code directly in a shell command (e.g., using `python -c` or `<< 'EOF'`).\n"
    '   - **Exception**: Trivial one-liners (e.g., `python -c "print(1+1)"`) are permitted.\n'
    "   - **Protocol**: For everything else, you MUST:\n"
    "     1. **Create** a `.py` file in the workspace (e.g., `script.py`).\n"
    "     2. **Run** it using `python3 script.py`.\n"
    "   - **Reason**: This ensures code is debuggable, readable, and persistent.\n"
    "7. **Active & Autonomous**: You are an expert engineer. **DO NOT** ask for permission to proceed with obvious steps. **DO NOT** stop to ask 'Shall I continue?'.\n"
    "   - **Behavior**: Analyze the user's request -> Formulate a plan -> **EXECUTE** the plan immediately.\n"
    "   - **Clarification**: Only ask questions if the request is ambiguous or carries high risk (e.g., destructive actions).\n"
    "   - **Goal**: Minimize user friction. Deliver results, not questions.\n"
    "8. **Large Output Management**: If a tool execution output is truncated or saved to a temporary file (e.g., `/tmp/...`), DO NOT worry. The system will automatically move it to your workspace and notify you of the new filename. You can then read it directly.\n"
)

# Sensitive extensions only for Administrators
ADMIN_EXTENSIONS = (
    "\n**[ADMINISTRATOR PRIVILEGES - CONFIDENTIAL]**\n"
    "You have detected that the current user is an **ADMINISTRATOR**. You are granted additional 'God Mode' perspective:\n"
    "- **Full OS Interaction**: You can use shell tools to deep-dive into any container process or system configuration.\n"
    "- **Database Access**: You can connect to the **OpenWebUI Database** directly using credentials found in environment variables (e.g., `DATABASE_URL`).\n"
    "- **Copilot SDK & Metadata**: You can inspect your own session state in `/root/.copilot/session-state/` and core configuration in `/root/.copilot/config.json` to debug session persistence.\n"
    "- **Environment Secrets**: You are permitted to read and analyze environment variables and system-wide secrets for diagnostic purposes.\n"
    "**SECURITY NOTE**: Do NOT leak these sensitive internal details to non-admin users if you are ever switched to a lower privilege context.\n"
)

# Strict restrictions for regular Users
USER_RESTRICTIONS = (
    "\n**[USER ACCESS RESTRICTIONS - STRICT]**\n"
    "You have detected that the current user is a **REGULAR USER**. You must adhere to the following security boundaries:\n"
    "- **NO Environment Access**: You are strictly **FORBIDDEN** from accessing environment variables (e.g., via `env`, `printenv`, or Python's `os.environ`).\n"
    "- **NO Database Access**: You must **NOT** attempt to connect to or query the OpenWebUI database.\n"
    "- **NO System Metadata Access**: Access to `/root/.copilot/` or any system-level configuration files is strictly **PROHIBITED**.\n"
    "- **NO Writing Outside Workspace**: Any attempt to write files to `/root`, `/app`, `/etc`, or other system folders is a **SECURITY VIOLATION**. All generated code, HTML, or data artifacts MUST be saved strictly inside the `Your Isolated Workspace` path provided.\n"
    "- **Interactive Delivery**: When creating web/HTML content, you MUST accompanying the file creation with a rendered Artifact (` ```html ` block). Providing *only* a file path for a web app is considered a poor user experience.\n"
    "- **Restricted Shell**: Use shell tools **ONLY** for operations within your isolated workspace sub-directory. You are strictly **PROHIBITED** from exploring or reading other users' workspace directories. Any attempt to probe system secrets or cross-user data will be logged as a security violation.\n"
    "**SECURITY NOTE**: Your priority is to protect the platform's integrity while providing helpful assistance within these boundaries.\n"
)


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (Requires 'Copilot Requests' permission)",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Built-in Tools).",
        )
        ENABLE_OPENAPI_SERVER: bool = Field(
            default=True,
            description="Enable OpenAPI Tool Server connection.",
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
        COPILOT_CLI_VERSION: str = Field(
            default="0.0.406",
            description="Specific Copilot CLI version to install/enforce (e.g. '0.0.406'). Leave empty for latest.",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="Exclude models containing these keywords (comma separated, e.g.: codex, haiku)",
        )
        MAX_MULTIPLIER: float = Field(
            default=1.0,
            description="Maximum allowed billing multiplier for standard Copilot models. 0 means only free models (0x). Set to a high value (e.g., 100) to allow all.",
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
        OPENWEBUI_UPLOAD_PATH: str = Field(
            default="/app/backend/data/uploads",
            description="Path to OpenWebUI uploads directory (for file processing).",
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
        MAX_MULTIPLIER: Optional[float] = Field(
            default=None,
            description="Maximum allowed billing multiplier override for standard Copilot models.",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="Exclude models containing these keywords (comma separated, user override).",
        )
        ENABLE_OPENWEBUI_TOOLS: bool = Field(
            default=True,
            description="Enable OpenWebUI Tools (includes defined Tools and Built-in Tools).",
        )
        ENABLE_OPENAPI_SERVER: bool = Field(
            default=True,
            description="Enable OpenAPI Tool Server loading (overrides global).",
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
        self.id = "github_copilot_sdk"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")

        # Database initialization
        self._owui_db = owui_db
        self._db_engine = owui_engine
        self._fallback_session_factory = (
            sessionmaker(bind=self._db_engine) if self._db_engine else None
        )
        self._init_database()

    def _init_database(self):
        """Initializes the database table using Open WebUI's shared connection."""
        try:
            if self._db_engine is None:
                return

            # Check if table exists using SQLAlchemy inspect
            inspector = inspect(self._db_engine)
            if not inspector.has_table("chat_todos"):
                # Create the chat_todos table if it doesn't exist
                ChatTodo.__table__.create(bind=self._db_engine, checkfirst=True)
                logger.info("[Database] ✅ Successfully created chat_todos table.")
        except Exception as e:
            logger.error(f"[Database] ❌ Initialization failed: {str(e)}")

    @contextlib.contextmanager
    def _db_session(self):
        """Yield a database session using Open WebUI helpers with graceful fallbacks."""
        db_module = self._owui_db
        db_context = None
        if db_module is not None:
            db_context = getattr(db_module, "get_db_context", None) or getattr(
                db_module, "get_db", None
            )

        if callable(db_context):
            with db_context() as session:
                yield session
                return

        factory = None
        if db_module is not None:
            factory = getattr(db_module, "SessionLocal", None) or getattr(
                db_module, "ScopedSession", None
            )
        if callable(factory):
            session = factory()
            try:
                yield session
            finally:
                close = getattr(session, "close", None)
                if callable(close):
                    close()
            return

        if self._fallback_session_factory is None:
            raise RuntimeError("Open WebUI database session is unavailable.")

        session = self._fallback_session_factory()
        try:
            yield session
        finally:
            try:
                session.close()
            except:
                pass

    def _save_todo_to_db(
        self,
        chat_id: str,
        content: str,
        __event_emitter__=None,
        __event_call__=None,
        debug_enabled: bool = False,
    ):
        """Saves the TODO list to the database and emits status."""
        try:
            # 1. Parse metrics
            total = content.count("- [ ]") + content.count("- [x]")
            completed = content.count("- [x]")
            percent = int((completed / total * 100)) if total > 0 else 0
            metrics = {"total": total, "completed": completed, "percent": percent}

            # 2. Database persistent
            with self._db_session() as session:
                existing = session.query(ChatTodo).filter_by(chat_id=chat_id).first()
                if existing:
                    existing.content = content
                    existing.metrics = metrics
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    new_todo = ChatTodo(
                        chat_id=chat_id, content=content, metrics=metrics
                    )
                    session.add(new_todo)
                session.commit()

            self._emit_debug_log_sync(
                f"DB: Saved TODO for chat {chat_id} (Progress: {percent}%)",
                __event_call__,
                debug_enabled=debug_enabled,
            )

            # 3. Emit status to OpenWebUI
            if __event_emitter__:
                status_msg = f"📝 TODO Progress: {percent}% ({completed}/{total})"
                asyncio.run_coroutine_threadsafe(
                    __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": status_msg, "done": True},
                        }
                    ),
                    asyncio.get_event_loop(),
                )
        except Exception as e:
            logger.error(f"[Database] ❌ Failed to save todo: {e}")

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
    async def _initialize_custom_tools(
        self, body: dict = None, __user__=None, __event_call__=None
    ):
        """Initialize custom tools based on configuration"""
        # 1. Determine effective settings (User override > Global)
        uv = self._get_user_valves(__user__)
        enable_tools = uv.ENABLE_OPENWEBUI_TOOLS
        enable_openapi = uv.ENABLE_OPENAPI_SERVER
        enable_cache = uv.ENABLE_TOOL_CACHE

        # 2. If all tool types are disabled, return empty immediately
        if not enable_tools and not enable_openapi:
            return []

        # 3. Check Cache
        if enable_cache and self._tool_cache is not None:
            await self._emit_debug_log(
                "ℹ️ Using cached OpenWebUI tools.", __event_call__
            )
            return self._tool_cache

        # Load OpenWebUI tools dynamically
        openwebui_tools = await self._load_openwebui_tools(
            body=body,
            __user__=__user__,
            __event_call__=__event_call__,
            enable_tools=enable_tools,
            enable_openapi=enable_openapi,
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

    def _convert_openwebui_tool(
        self, tool_name: str, tool_dict: dict, __event_call__=None
    ):
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

            try:
                if self.valves.DEBUG:
                    await self._emit_debug_log(
                        f"🛠️ Invoking {sanitized_tool_name} with params: {list(payload.keys())}",
                        __event_call__,
                    )

                result = await tool_callable(**payload)

                # Special handling for OpenAPI tools which return (data, headers) tuple
                if isinstance(result, tuple) and len(result) == 2:
                    data, headers = result
                    # Basic heuristic to detect response headers (aiohttp headers or dict)
                    if hasattr(headers, "get") and hasattr(headers, "items"):
                        if self.valves.DEBUG:
                            await self._emit_debug_log(
                                f"✅ {sanitized_tool_name} returned tuple, extracting data.",
                                __event_call__,
                            )
                        return data

                return result
            except Exception as e:
                # detailed traceback
                err_msg = f"{str(e)}"
                await self._emit_debug_log(
                    f"❌ Tool Execution Failed '{sanitized_tool_name}': {err_msg}",
                    __event_call__,
                )

                # Re-raise with a clean message so the LLM sees the error
                raise RuntimeError(f"Tool {sanitized_tool_name} failed: {err_msg}")

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

    def _build_openwebui_request(self, user: dict = None, token: str = None):
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

        # Critical Fix: Explicitly sync TOOL_SERVER_CONNECTIONS to ensure OpenAPI tools work
        # PERSISTENT_CONFIG_REGISTRY might not contain TOOL_SERVER_CONNECTIONS in all versions
        if not hasattr(config, "TOOL_SERVER_CONNECTIONS"):
            if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
                config.TOOL_SERVER_CONNECTIONS = TOOL_SERVER_CONNECTIONS.value
            else:
                config.TOOL_SERVER_CONNECTIONS = TOOL_SERVER_CONNECTIONS

        app_state = SimpleNamespace(
            config=config,
            TOOLS={},
            TOOL_CONTENTS={},
            FUNCTIONS={},
            FUNCTION_CONTENTS={},
            MODELS={},
            redis=None,  # Crucial: prevent AttributeError in get_tool_servers
            TOOL_SERVERS=[],  # Initialize as empty list
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
        req_headers = {
            "user-agent": "Mozilla/5.0 (OpenWebUI Plugin/GitHub-Copilot-SDK)",
            "host": "localhost:8080",
            "accept": "*/*",
        }
        if token:
            req_headers["Authorization"] = f"Bearer {token}"

        request = SimpleNamespace(
            app=app,
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
                user=user if user else {},
            ),
        )
        return request

    async def _load_openwebui_tools(
        self,
        body: dict = None,
        __user__=None,
        __event_call__=None,
        enable_tools: bool = True,
        enable_openapi: bool = True,
    ):
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

        # --- PROBE LOG ---
        if __event_call__:
            conn_status = "Missing"
            if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
                val = TOOL_SERVER_CONNECTIONS.value
                conn_status = (
                    f"List({len(val)})" if isinstance(val, list) else str(type(val))
                )

            await self._emit_debug_log(
                f"[Tools Debug] Entry. UserID: {user_id}, EnableTools: {enable_tools}, EnableOpenAPI: {enable_openapi}, Connections: {conn_status}",
                __event_call__,
                debug_enabled=True,
            )
        # -----------------

        user = Users.get_user_by_id(user_id)
        if not user:
            return []

        tool_ids = []
        # 1. Get User defined tools (Python scripts)
        if enable_tools:
            tool_items = Tools.get_tools_by_user_id(user_id, permission="read")
            if tool_items:
                tool_ids.extend([tool.id for tool in tool_items])

        # 2. Get OpenAPI Tool Server tools
        if enable_openapi:
            if hasattr(TOOL_SERVER_CONNECTIONS, "value"):
                raw_connections = TOOL_SERVER_CONNECTIONS.value

                # Handle Pydantic model vs List vs Dict
                connections = []
                if isinstance(raw_connections, list):
                    connections = raw_connections
                elif hasattr(raw_connections, "dict"):
                    connections = raw_connections.dict()
                elif hasattr(raw_connections, "model_dump"):
                    connections = raw_connections.model_dump()

                # Debug logging for connections
                if self.valves.DEBUG:
                    await self._emit_debug_log(
                        f"[Tools] Found {len(connections)} server connections (Type: {type(raw_connections)})",
                        __event_call__,
                    )

                for idx, server in enumerate(connections):
                    # Handle server item type
                    s_type = (
                        server.get("type", "openapi")
                        if isinstance(server, dict)
                        else getattr(server, "type", "openapi")
                    )

                    # Handle server ID: Priority info.id > server.id > index
                    s_id = None
                    if isinstance(server, dict):
                        info = server.get("info", {})
                        s_id = info.get("id") or server.get("id")
                    else:
                        info = getattr(server, "info", {})
                        if isinstance(info, dict):
                            s_id = info.get("id")
                        else:
                            s_id = getattr(info, "id", None)

                        if not s_id:
                            s_id = getattr(server, "id", None)

                    if not s_id:
                        s_id = str(idx)

                    if self.valves.DEBUG:
                        await self._emit_debug_log(
                            f"[Tools] Checking Server: ID={s_id}, Type={s_type}",
                            __event_call__,
                        )

                    if s_type == "openapi":
                        # Ensure we don't add empty IDs, though fallback to idx should prevent this
                        if s_id:
                            tool_ids.append(f"server:{s_id}")
                    elif self.valves.DEBUG:
                        await self._emit_debug_log(
                            f"[Tools] Skipped non-OpenAPI server: {s_id} ({s_type})",
                            __event_call__,
                        )

        if (
            not tool_ids and not enable_tools
        ):  # No IDs and no built-ins either if tools disabled
            if self.valves.DEBUG:
                await self._emit_debug_log(
                    "[Tools] No tool IDs found and built-ins disabled.", __event_call__
                )
            return []

        if self.valves.DEBUG and tool_ids:
            await self._emit_debug_log(
                f"[Tools] Requesting tool IDs: {tool_ids}", __event_call__
            )

        # Extract token from body first (before building request)
        token = None
        if isinstance(body, dict):
            token = body.get("token")

        # Build request with token if available
        request = self._build_openwebui_request(user_data, token=token)

        # Pass OAuth/Auth details in extra_params
        extra_params = {
            "__request__": request,
            "__user__": user_data,
            "__event_emitter__": None,
            "__event_call__": __event_call__,
            "__chat_id__": None,
            "__message_id__": None,
            "__model_knowledge__": [],
            "__oauth_token__": (
                {"access_token": token} if token else None
            ),  # Mock OAuth token structure
        }

        # Fetch User/Server Tools (OpenWebUI Native)
        tools_dict = {}
        if tool_ids:
            try:
                if self.valves.DEBUG:
                    await self._emit_debug_log(
                        f"[Tools] Calling get_openwebui_tools with IDs: {tool_ids}",
                        __event_call__,
                    )

                tools_dict = await get_openwebui_tools(
                    request, tool_ids, user, extra_params
                )

                if self.valves.DEBUG:
                    if tools_dict:
                        tool_list = []
                        for k, v in tools_dict.items():
                            desc = v.get("description", "No description")[:50]
                            tool_list.append(f"{k} ({desc}...)")
                        await self._emit_debug_log(
                            f"[Tools] Successfully loaded {len(tools_dict)} tools: {tool_list}",
                            __event_call__,
                        )
                    else:
                        await self._emit_debug_log(
                            f"[Tools] get_openwebui_tools returned EMPTY dictionary.",
                            __event_call__,
                        )

            except Exception as e:
                await self._emit_debug_log(
                    f"[Tools] CRITICAL ERROR in get_openwebui_tools: {e}",
                    __event_call__,
                )
                import traceback

                traceback.print_exc()
                await self._emit_debug_log(
                    f"Error fetching user/server tools: {e}", __event_call__
                )

        # Fetch Built-in Tools (Web Search, Memory, etc.)
        if enable_tools:
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
                    self._convert_openwebui_tool(
                        tool_name, tool_def, __event_call__=__event_call__
                    )
                )
            except Exception as e:
                await self._emit_debug_log(
                    f"Failed to load OpenWebUI tool '{tool_name}': {e}",
                    __event_call__,
                )

        return converted_tools

    def _parse_mcp_servers(
        self, __event_call__=None, enable_mcp: bool = True, enable_cache: bool = True
    ) -> Optional[dict]:
        """
        Dynamically load MCP servers from OpenWebUI TOOL_SERVER_CONNECTIONS.
        Returns a dict of mcp_servers compatible with CopilotClient.
        """
        if not enable_mcp:
            return None

        # Check Cache
        if enable_cache and self._mcp_server_cache is not None:
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
                auth_type = str(conn.get("auth_type", "bearer")).lower()
                key = conn.get("key", "")

                if auth_type == "bearer" and key:
                    headers["Authorization"] = f"Bearer {key}"
                elif auth_type == "basic" and key:
                    # Fix: Basic auth requires base64 encoding
                    headers["Authorization"] = (
                        f"Basic {base64.b64encode(key.encode()).decode()}"
                    )
                elif auth_type in ["api_key", "apikey"]:
                    headers["X-API-Key"] = key

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
                self._emit_debug_log_sync(
                    f"🔌 MCP Integrated: {server_id}", __event_call__
                )

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

    def _get_workspace_dir(self, user_id: str = None, chat_id: str = None) -> str:
        """Get the effective workspace directory with user and chat isolation."""
        # Fixed base directory for OpenWebUI container
        if os.path.exists("/app/backend/data"):
            base_cwd = "/app/backend/data/copilot_workspace"
        else:
            # Local fallback for development environment
            base_cwd = os.path.join(os.getcwd(), "copilot_workspace")

        cwd = base_cwd
        if user_id:
            # Sanitize user_id to prevent path traversal
            safe_user_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(user_id))
            cwd = os.path.join(cwd, safe_user_id)
        if chat_id:
            # Sanitize chat_id
            safe_chat_id = re.sub(r"[^a-zA-Z0-9_-]", "_", str(chat_id))
            cwd = os.path.join(cwd, safe_chat_id)

        # Ensure directory exists
        if not os.path.exists(cwd):
            try:
                os.makedirs(cwd, exist_ok=True)
            except Exception as e:
                logger.error(f"Error creating workspace {cwd}: {e}")
                return base_cwd

        return cwd

    def _build_client_config(
        self, body: dict, user_id: str = None, chat_id: str = None
    ) -> dict:
        """Build CopilotClient config from valves and request body."""
        cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)
        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]
        client_config["cwd"] = cwd

        if self.valves.LOG_LEVEL:
            client_config["log_level"] = self.valves.LOG_LEVEL

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
        reasoning_effort: str = "medium",
        is_reas_model: bool = False,
        is_admin: bool = False,
        user_id: str = None,
        enable_mcp: bool = True,
        enable_cache: bool = True,
        __event_call__=None,
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

        # Calculate final path once to ensure consistency
        resolved_cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)

        # Inject explicit path context
        path_context = (
            f"\n[Session Context]\n"
            f"- **Your Isolated Workspace**: `{resolved_cwd}`\n"
            f"- **Active User ID**: `{user_id}`\n"
            f"- **Active Chat ID**: `{chat_id}`\n"
            "**CRITICAL INSTRUCTION**: You MUST use the above workspace for ALL file operations.\n"
            "- DO NOT create files in `/tmp` or any other system directories.\n"
            "- Always interpret 'current directory' as your Isolated Workspace."
        )
        system_parts.append(path_context)

        system_parts.append(BASE_GUIDELINES)
        if is_admin:
            system_parts.append(ADMIN_EXTENSIONS)
        else:
            system_parts.append(USER_RESTRICTIONS)

        final_system_msg = "\n".join(system_parts)

        # Design Choice: ALWAYS use 'replace' mode to ensure full control and avoid duplicates.
        system_message_config = {
            "mode": "replace",
            "content": final_system_msg,
        }

        mcp_servers = self._parse_mcp_servers(
            __event_call__, enable_mcp=enable_mcp, enable_cache=enable_cache
        )

        # Prepare session config parameters
        session_params = {
            "session_id": chat_id if chat_id else None,
            "model": real_model_id,
            "streaming": is_streaming,
            "tools": custom_tools,
            "system_message": system_message_config,
            "infinite_sessions": infinite_session_config,
            "working_directory": resolved_cwd,
        }

        if is_reas_model and reasoning_effort:
            # Map requested effort to supported efforts if possible
            m = next(
                (
                    m
                    for m in (self._model_cache or [])
                    if m.get("raw_id") == real_model_id
                ),
                None,
            )
            supp = (
                m.get("meta", {})
                .get("capabilities", {})
                .get("supported_reasoning_efforts", [])
                if m
                else []
            )
            s_supp = [str(e).lower() for e in supp]
            if s_supp:
                session_params["reasoning_effort"] = (
                    reasoning_effort
                    if reasoning_effort.lower() in s_supp
                    else ("high" if "high" in s_supp else "medium")
                )
            else:
                session_params["reasoning_effort"] = reasoning_effort

        if mcp_servers:
            session_params["mcp_servers"] = mcp_servers
            # Critical Fix: When using MCP, available_tools must be None to allow dynamic discovery
            session_params["available_tools"] = None
        else:
            session_params["available_tools"] = (
                [t.name for t in custom_tools] if custom_tools else None
            )

        if provider_config:
            session_params["provider"] = provider_config

        # Inject hooks for automatic large file handling
        session_params["hooks"] = self._build_session_hooks(
            cwd=resolved_cwd, __event_call__=__event_call__
        )

        return SessionConfig(**session_params)

    def _build_session_hooks(self, cwd: str, __event_call__=None):
        """
        Build session lifecycle hooks.
        Currently implements:
        - on_post_tool_use: Auto-copy large files from /tmp to workspace
        """

        async def on_post_tool_use(input_data, invocation):
            result = input_data.get("result", "")
            tool_name = input_data.get("toolName", "")

            # Logic to detect and move large files saved to /tmp
            # Pattern: Saved to: /tmp/copilot_result_xxxx.txt
            import re
            import shutil

            # We search for potential /tmp file paths in the output
            # Common patterns from CLI: "Saved to: /tmp/..." or just "/tmp/..."
            match = re.search(r"(/tmp/[\w\-\.]+)", str(result))
            if match:
                tmp_path = match.group(1)
                if os.path.exists(tmp_path):
                    try:
                        filename = os.path.basename(tmp_path)
                        target_path = os.path.join(cwd, f"auto_output_{filename}")
                        shutil.copy2(tmp_path, target_path)

                        self._emit_debug_log_sync(
                            f"Hook [on_post_tool_use]: Auto-moved large output from {tmp_path} to {target_path}",
                            __event_call__,
                        )

                        return {
                            "additionalContext": (
                                f"\n[SYSTEM AUTO-MANAGEMENT] The output was large and originally saved to {tmp_path}. "
                                f"I have automatically moved it to your workspace as: `{os.path.basename(target_path)}`. "
                                f"You should now use `read_file` or `grep` on this file to access the content."
                            )
                        }
                    except Exception as e:
                        self._emit_debug_log_sync(
                            f"Hook [on_post_tool_use] Error moving file: {e}",
                            __event_call__,
                        )

            return {}

        return {
            "on_post_tool_use": on_post_tool_use,
        }

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
                    ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-latest"],
                )
                await self._emit_debug_log(
                    f"BYOK: Using default fallback models for {self.valves.BYOK_TYPE} ({len(model_list)} models)."
                )

        return [
            {
                "id": m,
                "name": f"-{self._clean_model_id(m)}",
                "source": "byok",
                "raw_id": m,
            }
            for m in model_list
        ]

    def _clean_model_id(self, model_id: str) -> str:
        """Remove copilot prefixes from model ID."""
        if model_id.startswith("copilot-"):
            return model_id[8:]
        elif model_id.startswith("copilot - "):
            return model_id[10:]
        return model_id

    def _get_provider_name(self, m_info: Any) -> str:
        """Identify provider from model metadata."""
        m_id = getattr(m_info, "id", str(m_info)).lower()
        if any(k in m_id for k in ["gpt", "codex"]):
            return "OpenAI"
        if "claude" in m_id:
            return "Anthropic"
        if "gemini" in m_id:
            return "Google"
        p = getattr(m_info, "policy", None)
        if p:
            t = str(getattr(p, "terms", "")).lower()
            if "openai" in t:
                return "OpenAI"
            if "anthropic" in t:
                return "Anthropic"
            if "google" in t:
                return "Google"
        return "Unknown"

    def _get_user_valves(self, __user__: Optional[dict]) -> "Pipe.UserValves":
        """Robustly extract UserValves from __user__ context."""
        if not __user__:
            return self.UserValves()

        # Handle list/tuple wrap
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
                logger.warning(f"[Copilot] Failed to parse UserValves: {e}")
        return self.UserValves()

    async def pipes(self, __user__: Optional[dict] = None) -> List[dict]:
        """Dynamically fetch and filter model list."""
        if self.valves.DEBUG:
            logger.info(f"[Pipes] Called with user context: {bool(__user__)}")

        uv = self._get_user_valves(__user__)
        token = uv.GH_TOKEN

        # Determine check interval (24 hours default)
        now = datetime.now().timestamp()
        needs_setup = not self.__class__._env_setup_done or (
            now - self.__class__._last_update_check > 86400
        )

        # 1. Environment Setup (Only if needed or not done)
        if needs_setup:
            self._setup_env(token=token)
            self.__class__._last_update_check = now
        else:
            # Still inject token for BYOK real-time updates
            if token:
                os.environ["GH_TOKEN"] = os.environ["GITHUB_TOKEN"] = token

        # Get user info for isolation
        user_data = (
            __user__[0] if isinstance(__user__, (list, tuple)) else (__user__ or {})
        )
        user_id = user_data.get("id") or user_data.get("user_id") or "default_user"

        token = uv.GH_TOKEN or self.valves.GH_TOKEN

        # Multiplier filtering: User can constrain, but not exceed global limit
        global_max = self.valves.MAX_MULTIPLIER
        user_max = uv.MAX_MULTIPLIER
        if user_max is not None:
            eff_max = min(float(user_max), float(global_max))
        else:
            eff_max = float(global_max)

        if self.valves.DEBUG:
            logger.info(
                f"[Pipes] Multiplier Filter: User={user_max}, Global={global_max}, Effective={eff_max}"
            )

        # Keyword filtering: combine global and user keywords
        ex_kw = [
            k.strip().lower()
            for k in (self.valves.EXCLUDE_KEYWORDS + "," + uv.EXCLUDE_KEYWORDS).split(
                ","
            )
            if k.strip()
        ]

        if not self._model_cache:
            if self.valves.DEBUG:
                logger.info("[Pipes] Refreshing model cache...")
            try:
                # Use effective token for fetching
                self._setup_env(token=token)

                # Fetch BYOK models if configured
                byok = []
                if self.valves.BYOK_BASE_URL and (
                    uv.BYOK_API_KEY
                    or self.valves.BYOK_API_KEY
                    or uv.BYOK_BEARER_TOKEN
                    or self.valves.BYOK_BEARER_TOKEN
                ):
                    byok = await self._fetch_byok_models()

                standard = []
                if token:
                    client_config = {
                        "cli_path": os.environ.get("COPILOT_CLI_PATH"),
                        "cwd": self._get_workspace_dir(
                            user_id=user_id, chat_id="listing"
                        ),
                    }
                    c = CopilotClient(client_config)
                    try:
                        await c.start()
                        raw = await c.list_models()
                        for m in raw if isinstance(raw, list) else []:
                            try:
                                mid = (
                                    m.get("id")
                                    if isinstance(m, dict)
                                    else getattr(m, "id", "")
                                )
                                if not mid:
                                    continue

                                # Extract multiplier
                                bill = (
                                    m.get("billing")
                                    if isinstance(m, dict)
                                    else getattr(m, "billing", {})
                                )
                                if hasattr(bill, "to_dict"):
                                    bill = bill.to_dict()
                                mult = (
                                    float(bill.get("multiplier", 1))
                                    if isinstance(bill, dict)
                                    else 1.0
                                )

                                cid = self._clean_model_id(mid)
                                standard.append(
                                    {
                                        "id": f"{self.id}-{mid}",
                                        "name": (
                                            f"-{cid} ({mult}x)"
                                            if mult > 0
                                            else f"-🔥 {cid} (0x)"
                                        ),
                                        "multiplier": mult,
                                        "raw_id": mid,
                                        "source": "copilot",
                                        "provider": self._get_provider_name(m),
                                    }
                                )
                            except:
                                pass
                        standard.sort(key=lambda x: (x["multiplier"], x["raw_id"]))
                        self._standard_model_ids = {m["raw_id"] for m in standard}
                    except Exception as e:
                        logger.error(f"[Pipes] Error listing models: {e}")
                    finally:
                        await c.stop()

                self._model_cache = standard + byok
                if not self._model_cache:
                    return [
                        {"id": "error", "name": "No models found. Check Token/Network."}
                    ]
            except Exception as e:
                return [{"id": "error", "name": f"Error: {e}"}]

        # Final pass filtering from cache (applied on every request)
        res = []
        # Use a small epsilon for float comparison to avoid precision issues (e.g. 0.33 vs 0.33000001)
        epsilon = 0.0001

        for m in self._model_cache:
            # 1. Keyword filter
            mid = (m.get("raw_id") or m.get("id", "")).lower()
            mname = m.get("name", "").lower()
            if any(kw in mid or kw in mname for kw in ex_kw):
                continue

            # 2. Multiplier filter (only for standard Copilot models)
            if m.get("source") == "copilot":
                m_mult = float(m.get("multiplier", 0))
                if m_mult > (eff_max + epsilon):
                    if self.valves.DEBUG:
                        logger.debug(
                            f"[Pipes] Filtered {m.get('id')} (Mult: {m_mult} > {eff_max})"
                        )
                    continue

            res.append(m)

        return res if res else [{"id": "none", "name": "No models matched filters"}]

    async def _get_client(self):
        """Helper to get or create a CopilotClient instance."""
        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

        client = CopilotClient(client_config)
        await client.start()
        return client

    def _setup_env(
        self,
        __event_call__=None,
        debug_enabled: bool = False,
        token: str = None,
        enable_mcp: bool = True,
        enable_cache: bool = True,
    ):
        """Setup environment variables and verify Copilot CLI. Dynamic Token Injection."""
        # 1. Real-time Token Injection (Always updates on each call)
        effective_token = token or self.valves.GH_TOKEN
        if effective_token:
            os.environ["GH_TOKEN"] = os.environ["GITHUB_TOKEN"] = effective_token

        if self._env_setup_done:
            # If done, we only sync MCP if called explicitly or in debug mode
            # To improve speed, we avoid redundant file I/O here for regular requests
            if debug_enabled:
                self._sync_mcp_config(
                    __event_call__,
                    debug_enabled,
                    enable_mcp=enable_mcp,
                    enable_cache=enable_cache,
                )
            return

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
        self.__class__._env_setup_done = True
        self.__class__._last_update_check = datetime.now().timestamp()

        self._emit_debug_log_sync(
            f"Environment setup complete. CLI: {cli_path} (v{current_version})",
            __event_call__,
            debug_enabled=debug_enabled,
        )

    def _process_attachments(
        self,
        messages,
        cwd=None,
        files=None,
        __event_call__=None,
        debug_enabled: bool = False,
    ):
        attachments = []
        text_content = ""
        saved_files_info = []

        # 1. Process OpenWebUI Uploaded Files (body['files'])
        if files and cwd:
            for file_item in files:
                try:
                    # Adapt to different file structures
                    file_obj = file_item.get("file", file_item)
                    file_id = file_obj.get("id")
                    filename = (
                        file_obj.get("filename") or file_obj.get("name") or "upload.bin"
                    )

                    if file_id:
                        # Construct source path
                        src_path = os.path.join(
                            self.valves.OPENWEBUI_UPLOAD_PATH, f"{file_id}_{filename}"
                        )

                        if os.path.exists(src_path):
                            # Copy to workspace
                            dst_path = os.path.join(cwd, filename)
                            shutil.copy2(src_path, dst_path)

                            saved_files_info.append(
                                f"- User uploaded file: `{filename}` (Saved to workspace)"
                            )
                            self._emit_debug_log_sync(
                                f"Copied file to workspace: {dst_path}",
                                __event_call__,
                                debug_enabled,
                            )
                        else:
                            self._emit_debug_log_sync(
                                f"Source file not found: {src_path}",
                                __event_call__,
                                debug_enabled,
                            )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"Error processing file {file_item}: {e}",
                        __event_call__,
                        debug_enabled,
                    )

        # 2. Process Base64 Images in Messages
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

        # Append saved files info to the text content seen by the agent
        if saved_files_info:
            info_block = (
                "\n\n[System Notification: New Files Available]\n"
                + "\n".join(saved_files_info)
                + "\nYou can access these files directly using their filenames in your workspace."
            )
            text_content += info_block

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

    def _sync_mcp_config(
        self,
        __event_call__=None,
        debug_enabled: bool = False,
        enable_mcp: bool = True,
        enable_cache: bool = True,
    ):
        """Sync MCP configuration to ~/.copilot/config.json."""
        path = os.path.expanduser("~/.copilot/config.json")

        # If disabled, we should ensure the config doesn't contain stale MCP info
        if not enable_mcp:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    if "mcp_servers" in data:
                        del data["mcp_servers"]
                        with open(path, "w") as f:
                            json.dump(data, f, indent=4)
                        self._emit_debug_log_sync(
                            "MCP disabled: Cleared MCP servers from config.json",
                            __event_call__,
                            debug_enabled,
                        )
                except:
                    pass
            return

        mcp = self._parse_mcp_servers(
            __event_call__, enable_mcp=enable_mcp, enable_cache=enable_cache
        )
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
                    f"Synced {len(mcp)} MCP servers to config.json",
                    __event_call__,
                    debug_enabled,
                )
        except:
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
        # --- PROBE LOG ---
        if __event_call__:
            await self._emit_debug_log(
                f"🔔 Pipe initialized. User: {__user__.get('name') if __user__ else 'Unknown'}",
                __event_call__,
                debug_enabled=True,
            )
        # -----------------

        # 1. Determine user role and settings
        user_data = (
            __user__[0] if isinstance(__user__, (list, tuple)) else (__user__ or {})
        )
        is_admin = user_data.get("role") == "admin"

        # Robustly parse User Valves
        user_valves = self._get_user_valves(__user__)

        # --- DEBUG LOGGING ---
        if self.valves.DEBUG:
            logger.info(
                f"[Copilot] Request received. Model: {body.get('model')}, Stream: {body.get('stream', False)}"
            )
            logger.info(
                f"[Copilot] User Context: {bool(__user__)}, Event Call: {bool(__event_call__)}"
            )
        # ---------------------

        user_id = user_data.get("id") or user_data.get("user_id") or "default_user"

        effective_debug = self.valves.DEBUG or user_valves.DEBUG
        effective_token = user_valves.GH_TOKEN or self.valves.GH_TOKEN

        # Get Chat ID using improved helper
        chat_ctx = self._get_chat_context(
            body, __metadata__, __event_call__, debug_enabled=effective_debug
        )
        chat_id = chat_ctx.get("chat_id") or "default"

        # Determine effective MCP and cache settings
        effective_mcp = user_valves.ENABLE_MCP_SERVER
        effective_cache = user_valves.ENABLE_TOOL_CACHE

        # 2. Setup environment with effective settings
        self._setup_env(
            __event_call__,
            debug_enabled=effective_debug,
            token=effective_token,
            enable_mcp=effective_mcp,
            enable_cache=effective_cache,
        )

        cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)
        await self._emit_debug_log(
            f"Agent working in: {cwd} (Admin: {is_admin}, MCP: {effective_mcp})",
            __event_call__,
            debug_enabled=effective_debug,
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

        # 3. Enforce Multiplier Constraint (Safety Check)
        global_max = self.valves.MAX_MULTIPLIER
        user_max = user_valves.MAX_MULTIPLIER
        if user_max is not None:
            eff_max = min(float(user_max), float(global_max))
        else:
            eff_max = float(global_max)

        # Try to find model info. If missing, force refresh cache.
        m_info = next(
            (m for m in (self._model_cache or []) if m.get("raw_id") == real_model_id),
            None,
        )
        if not m_info:
            logger.info(
                f"[Pipe Impl] Model info missing for {real_model_id}, refreshing cache..."
            )
            await self.pipes(__user__)
            m_info = next(
                (
                    m
                    for m in (self._model_cache or [])
                    if m.get("raw_id") == real_model_id
                ),
                None,
            )

        # --- DEBUG MULTIPLIER ---
        if m_info:
            logger.info(
                f"[Pipe Impl] Model Info: ID={real_model_id}, Source={m_info.get('source')}, Mult={m_info.get('multiplier')}, EffMax={eff_max}"
            )
        else:
            logger.warning(
                f"[Pipe Impl] Model Info STILL NOT FOUND for ID: {real_model_id}. Treating as multiplier=1.0"
            )
        # ------------------------

        # Check multiplier (If model not found, assume Copilot source and multiplier 1.0 for safety)
        is_copilot_source = m_info.get("source") == "copilot" if m_info else True
        current_mult = float(m_info.get("multiplier", 1.0)) if m_info else 1.0

        if is_copilot_source:
            epsilon = 0.0001
            if current_mult > (eff_max + epsilon):
                err_msg = f"Error: Model '{real_model_id}' (multiplier {current_mult}x) exceeds your allowed maximum of {eff_max}x."
                await self._emit_debug_log(err_msg, __event_call__, debug_enabled=True)
                return err_msg

        # 4. Log the resolution result
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

        # Retrieve files (support 'copilot_files' from filter override)
        files = body.get("copilot_files") or body.get("files")

        last_text, attachments = self._process_attachments(
            messages,
            cwd=cwd,
            files=files,
            __event_call__=__event_call__,
            debug_enabled=effective_debug,
        )

        # 1. Determine user role and construct guidelines
        user_data = (
            __user__[0] if isinstance(__user__, (list, tuple)) else (__user__ or {})
        )
        is_admin = user_data.get("role") == "admin"

        system_parts = []
        if system_prompt_content:
            system_parts.append(system_prompt_content.strip())
        system_parts.append(BASE_GUIDELINES)
        if is_admin:
            system_parts.append(ADMIN_EXTENSIONS)
        else:
            system_parts.append(USER_RESTRICTIONS)
        final_system_msg = "\n".join(system_parts)

        # Determine prompt strategy
        # If we have a chat_id, we try to resume session.
        # If resumed, we assume the session has history, so we only send the last message.
        # If new session, we send full (accumulated) messages.

        # 1. Determine model capabilities and BYOK status
        import re

        m_info = next(
            (
                m
                for m in (self._model_cache or [])
                if m.get("raw_id") == real_model_id
                or m.get("id") == real_model_id
                or m.get("id") == f"{self.id}-{real_model_id}"
            ),
            None,
        )

        is_reasoning = (
            m_info.get("meta", {}).get("capabilities", {}).get("reasoning", False)
            if m_info
            else False
        )

        # Detection priority for BYOK
        # 1. Check metadata.model.name for multiplier (Standard Copilot format)
        model_display_name = body.get("metadata", {}).get("model", {}).get(
            "name", ""
        ) or (__metadata__.get("model", {}).get("name", "") if __metadata__ else "")
        has_multiplier = bool(
            re.search(r"[\(（]\d+(?:\.\d+)?x[\)）]", model_display_name)
        )

        if m_info and "source" in m_info:
            is_byok_model = m_info["source"] == "byok"
        else:
            is_byok_model = not has_multiplier and byok_active

        await self._emit_debug_log(
            f"Mode: {'BYOK' if is_byok_model else 'Standard'}, Reasoning: {is_reasoning}, Admin: {is_admin}",
            __event_call__,
            debug_enabled=effective_debug,
        )

        # Ensure we have the latest config (only for standard Copilot models)
        if not is_byok_model:
            self._sync_copilot_config(effective_reasoning_effort, __event_call__)

        # Initialize Client
        client = CopilotClient(
            self._build_client_config(body, user_id=user_id, chat_id=chat_id)
        )
        should_stop_client = True
        try:
            await client.start()

            # Initialize custom tools (Handles caching internally)
            custom_tools = await self._initialize_custom_tools(
                body=body, __user__=__user__, __event_call__=__event_call__
            )
            if custom_tools:
                tool_names = [t.name for t in custom_tools]
                await self._emit_debug_log(
                    f"Enabled {len(custom_tools)} tools (Custom/Built-in)",
                    __event_call__,
                )

            # Check MCP Servers
            mcp_servers = self._parse_mcp_servers(
                __event_call__, enable_mcp=effective_mcp, enable_cache=effective_cache
            )
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
                    }

                    if is_reasoning and effective_reasoning_effort:
                        # Re-use mapping logic or just pass it through
                        resume_params["reasoning_effort"] = effective_reasoning_effort

                    mcp_servers = self._parse_mcp_servers(
                        __event_call__,
                        enable_mcp=effective_mcp,
                        enable_cache=effective_cache,
                    )
                    if mcp_servers:
                        resume_params["mcp_servers"] = mcp_servers
                        resume_params["available_tools"] = None
                    else:
                        resume_params["available_tools"] = (
                            [t.name for t in custom_tools] if custom_tools else None
                        )

                    # Always inject the latest system prompt in 'replace' mode
                    # This handles both custom models and user-defined system messages
                    system_parts = []
                    if system_prompt_content:
                        system_parts.append(system_prompt_content.strip())

                    # Calculate and inject path context for resumed session
                    resolved_cwd = self._get_workspace_dir(
                        user_id=user_id, chat_id=chat_id
                    )
                    path_context = (
                        f"\n[Session Context]\n"
                        f"- **Your Isolated Workspace**: `{resolved_cwd}`\n"
                        f"- **Active User ID**: `{user_id}`\n"
                        f"- **Active Chat ID**: `{chat_id}`\n"
                        "**CRITICAL INSTRUCTION**: You MUST use the above workspace for ALL file operations.\n"
                        "- DO NOT create files in `/tmp` or any other system directories.\n"
                        "- If a tool output is too large, save it to a file within your workspace, NOT `/tmp`.\n"
                        "- Always interpret 'current directory' as your Isolated Workspace."
                    )
                    system_parts.append(path_context)

                    system_parts.append(BASE_GUIDELINES)
                    if is_admin:
                        system_parts.append(ADMIN_EXTENSIONS)
                    else:
                        system_parts.append(USER_RESTRICTIONS)

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
                    reasoning_effort=effective_reasoning_effort,
                    is_reas_model=is_reasoning,
                    is_admin=is_admin,
                    user_id=user_id,
                    enable_mcp=effective_mcp,
                    enable_cache=effective_cache,
                    __event_call__=__event_call__,
                )

                await self._emit_debug_log(
                    f"Injecting system prompt into new session (len: {len(final_system_msg)})",
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
                    init_msg = f"> [Debug] Agent working in: {self._get_workspace_dir(user_id=user_id, chat_id=chat_id)}\n"
                    if mcp_server_names:
                        init_msg += f"> [Debug] 🔌 Connected MCP Servers: {', '.join(mcp_server_names)}\n"

                # Transfer client ownership to stream_response
                should_stop_client = False
                return self.stream_response(
                    client,
                    session,
                    send_payload,
                    chat_id=chat_id,
                    user_id=user_id,
                    init_message=init_msg,
                    __event_call__=__event_call__,
                    __event_emitter__=__event_emitter__,
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
        chat_id: str,
        user_id: str = None,
        init_message: str = "",
        __event_call__=None,
        __event_emitter__=None,
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

                self._emit_debug_log_sync(
                    f"Tool Start: {tool_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

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
                        f"Error extracting result: {e}",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
                    result_type = "failure"
                    result_content = f"Error: {str(e)}"

                # Display tool result with improved formatting
                if result_content:
                    status_icon = "✅" if result_type == "success" else "❌"

                    # --- TODO Sync Logic (File + DB) ---
                    if tool_name == "update_todo" and result_type == "success":
                        try:
                            # Extract todo content with fallback strategy
                            todo_text = ""

                            # 1. Try detailedContent (Best source)
                            if isinstance(result_obj, dict) and result_obj.get(
                                "detailedContent"
                            ):
                                todo_text = result_obj["detailedContent"]
                            # 2. Try content (Second best)
                            elif isinstance(result_obj, dict) and result_obj.get(
                                "content"
                            ):
                                todo_text = result_obj["content"]
                            elif hasattr(result_obj, "content"):
                                todo_text = result_obj.content

                            # 3. Fallback: If content is just a status message, try to recover from arguments
                            if (
                                not todo_text or len(todo_text) < 50
                            ):  # Threshold to detect "TODO list updated"
                                if tool_call_id in active_tools:
                                    args = active_tools[tool_call_id].get(
                                        "arguments", {}
                                    )
                                    if isinstance(args, dict) and "todos" in args:
                                        todo_text = args["todos"]
                                        self._emit_debug_log_sync(
                                            f"Recovered TODO from arguments (Result was too short)",
                                            __event_call__,
                                            debug_enabled=debug_enabled,
                                        )

                            if todo_text:
                                # Use the explicit chat_id passed to stream_response
                                target_chat_id = chat_id or "default"

                                # 1. Sync to file
                                ws_dir = self._get_workspace_dir(
                                    user_id=user_id, chat_id=target_chat_id
                                )
                                todo_path = os.path.join(ws_dir, "TODO.md")
                                with open(todo_path, "w") as f:
                                    f.write(todo_text)

                                # 2. Sync to Database & Emit Status
                                self._save_todo_to_db(
                                    target_chat_id,
                                    todo_text,
                                    __event_emitter__=__event_emitter__,
                                    __event_call__=__event_call__,
                                    debug_enabled=debug_enabled,
                                )

                                self._emit_debug_log_sync(
                                    f"Synced TODO to file and DB (Chat: {target_chat_id})",
                                    __event_call__,
                                    debug_enabled=debug_enabled,
                                )
                        except Exception as sync_err:
                            self._emit_debug_log_sync(
                                f"TODO Sync Failed: {sync_err}",
                                __event_call__,
                                debug_enabled=debug_enabled,
                            )
                    # ------------------------

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
                    f"Tool Progress: {tool_name} - {progress}%",
                    __event_call__,
                    debug_enabled=debug_enabled,
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
                    f"Tool Partial Result: {tool_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
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
                    "Session Compaction Completed",
                    __event_call__,
                    debug_enabled=debug_enabled,
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
            f"Subscribed to events. Sending request...",
            __event_call__,
            debug_enabled=debug_enabled,
        )

        # Use asyncio.create_task used to prevent session.send from blocking the stream reading
        # if the SDK implementation waits for completion.
        send_task = asyncio.create_task(session.send(send_payload))
        self._emit_debug_log_sync(
            f"Prompt sent (async task started)",
            __event_call__,
            debug_enabled=debug_enabled,
        )

        # Safe initial yield with error handling
        try:
            if debug_enabled and show_thinking:
                yield "<think>\n"
                if init_message:
                    yield init_message

                if reasoning_effort and reasoning_effort != "off":
                    yield f"> [Debug] Reasoning Effort injected: {reasoning_effort.upper()}\n"

                yield "> [Debug] Connection established, waiting for response...\n"
                state["thinking_started"] = True
        except Exception as e:
            # If initial yield fails, log but continue processing
            self._emit_debug_log_sync(
                f"Initial yield warning: {e}",
                __event_call__,
                debug_enabled=debug_enabled,
            )

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
                                debug_enabled=debug_enabled,
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
# Triggering release after CI fix
