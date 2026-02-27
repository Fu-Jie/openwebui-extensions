"""
title: GitHub Copilot Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
openwebui_id: ce96f7b4-12fc-4ac3-9a01-875713e69359
description: Integrate GitHub Copilot SDK. Supports dynamic models, multi-turn conversation, streaming, multimodal input, infinite sessions, bidirectional OpenWebUI Skills bridge, and manage_skills tool.
version: 0.9.0
requirements: github-copilot-sdk==0.1.25
"""

import os
import re
import json
import base64
import tempfile
import asyncio
import logging
import shutil
import hashlib
import time
import subprocess
import tarfile
import zipfile
import urllib.parse
import urllib.request
import aiohttp
import contextlib
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
from open_webui.models.files import Files, FileForm
from open_webui.storage.provider import Storage
import mimetypes
import uuid

# Get OpenWebUI version for capability detection
try:
    from open_webui.env import VERSION as open_webui_version
except ImportError:
    open_webui_version = "0.0.0"

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
    "- **Skills vs Tools — CRITICAL DISTINCTION**:\n"
    "  - **Tools** (`bash`, `create_file`, `view_file`, custom functions, MCP tools, etc.) are **executable functions** you call directly. They take inputs, run code or API calls, and return results.\n"
    "  - **Skills** are **context-injected Markdown instructions** (from `SKILL.md` files in a skill directory). They are NOT callable functions and NOT shell commands. When the Copilot SDK detects intent, it reads the relevant `SKILL.md` and injects its content into your context automatically — you then follow those instructions using your standard tools.\n"
    "  - **Skill directory structure**: A skill lives in a subdirectory under the Skills Directory. **Only `SKILL.md` is required** — all other contents are optional resources that the skill may provide:\n"
    "    - `scripts/` — helper Python or shell scripts; invoke via `bash` / `python3` **only when SKILL.md instructs you to**.\n"
    "    - `references/` — supplementary Markdown documents (detailed workflows, examples); read with `view_file` as directed.\n"
    "    - `templates/` — file templates to copy or fill in as part of the skill workflow.\n"
    "    - Any other supporting files (data, configs, assets) — treat them as resources described in `SKILL.md`.\n"
    "  - **Rule**: Always start by reading `SKILL.md`. It is the authoritative entry point. Other files in the directory only matter if `SKILL.md` references them.\n"
    "  - **Deterministic skill management**: For install/list/create/edit/delete/show operations, MUST use the `manage_skills` tool (do not rely on skill auto-trigger).\n"
    "  - **NEVER run a skill name as a shell command** (e.g., do NOT run `docx` or any skill name via `bash`). The skill name is not a binary. Scripts inside `scripts/` are helpers to be called explicitly as instructed.\n"
    "  - **How to identify a skill**: Skills appear in your context as injected instruction blocks (usually with a heading matching the skill name). Tools appear in your available-tools list.\n"
    "\n"
    "**Formatting & Presentation Directives:**\n"
    "1. **Markdown Excellence**: Leverage full **Markdown** capabilities (headers, bold, italics, tables, lists) to structure your response professionally for the chat interface.\n"
    "2. **Advanced Visualization**: Use **Mermaid** for flowcharts/diagrams and **LaTeX** for math. **IMPORTANT**: Always wrap Mermaid code within a standard ` ```mermaid ` code block to ensure it is rendered correctly by the UI.\n"
    "3. **Interactive Artifacts (HTML)**: **Premium Delivery Protocol**: For web applications, you MUST perform two actions:\n"
    "   - 1. **Persist**: Create the file in the workspace (e.g., `index.html`) for project structure.\n"
    "   - 2. **Publish & Embed**: Call `publish_file_from_workspace(filename='your_file.html')`. This will automatically trigger the **Premium Experience** by directly embedding the interactive component using the action-style return.\n"
    "   - **CRITICAL**: When using this protocol in **Rich UI mode** (`embed_type='richui'`), **DO NOT** output the raw HTML code in a code block. Provide ONLY the **[Preview]** and **[Download]** links returned by the tool. The interactive embed will appear automatically after your message finishes.\n"
    "   - **Artifacts mode** (`embed_type='artifacts'`): You MUST provide the **[Preview]** and **[Download]** links, AND then you MUST output the provided `html_embed` (the iframe) wrapped within a ```html code block to enable the interactive preview.\n"
    "   - **Process Visibility**: While raw code is often replaced by links/frames, you SHOULD provide a **very brief Markdown summary** of the component's structure or key features (e.g., 'Generated login form with validation') before publishing. This keeps the user informed of the 'processing' progress.\n"
    "   - **Game/App Controls**: If your HTML includes keyboard controls (e.g., arrow keys, spacebar for games), you MUST include `event.preventDefault()` in your `keydown` listeners to prevent the parent browser page from scrolling.\n"
    "4. **Images & Files**: ALWAYS embed generated images/files directly using `![caption](url)`. Never provide plain text links.\n"
    "5. **File Delivery Protocol (Dual-Channel Delivery)**:\n"
    "     - **Definition**: **Artifacts** = content/code-block driven visual output in chat (typically with `html_embed`). **Rich UI** = tool/action returned embedded UI rendered by emitter in a persistent sandboxed iframe.\n"
    "     - **Philosophy**: Visual Artifacts (HTML/Mermaid) and Downloadable Files are **COMPLEMENTARY**. Always aim to provide BOTH: instant visual insight in the chat AND a persistent file for the user to keep.\n"
    "     - **The Rule**: When the user needs to *possess* data (download/export), you MUST publish it. Creating a local file alone is useless because the user cannot access your container.\n"
    "     - **Implicit Requests**: If asked to 'export', 'get link', or 'save', automatically trigger this sequence.\n"
    "     - **Execution Sequence**: 1. **Write Local**: Create file. 2. **Publish**: Call `publish_file_from_workspace`. 3. **Response Structure**:\n"
    "        - **For PDF files**: You MUST output ONLY Markdown links from the tool output (preview + download). **CRITICAL: NEVER output iframe/html_embed for PDF.**\n"
    "        - **For HTML files**: choose mode by complexity/environment. **Artifacts mode** (`embed_type='artifacts'`): output [Preview]/[Download], then MISSION-CRITICAL: output the provided `html_embed` value wrapped EXACTLY within a ```html code block. **Rich UI mode** (`embed_type='richui'`): output ONLY [Preview]/[Download]; do NOT output iframe/html block because Rich UI will render automatically via emitter.\n"
    "     - **URL Format**: You MUST use the **ABSOLUTE URLs** provided in the tool output. NEVER modify them.\n"
    "     - **Bypass RAG**: This protocol automatically handles S3 storage and bypasses RAG, ensuring 100% accurate data delivery.\n"
    "6. **TODO Visibility**: Every time you call the `update_todo` tool, you **MUST** immediately follow up with a beautifully formatted **Markdown summary** of the current TODO list. Use task checkboxes (`- [ ]`), progress indicators, and clear headings so the user can see the status directly in the chat.\n"
    "7. **Python Execution Standard**: For ANY task requiring Python logic (not just data analysis), you **MUST NOT** embed multi-line code directly in a shell command (e.g., using `python -c` or `<< 'EOF'`).\n"
    '   - **Exception**: Trivial one-liners (e.g., `python -c "print(1+1)"`) are permitted.\n'
    "   - **Protocol**: For everything else, you MUST:\n"
    "     1. **Create** a `.py` file in the workspace (e.g., `script.py`).\n"
    "     2. **Run** it using `python3 script.py`.\n"
    "   - **Reason**: This ensures code is debuggable, readable, and persistent.\n"
    "8. **Active & Autonomous**: You are an expert engineer. **DO NOT** ask for permission to proceed with obvious steps. **DO NOT** stop to ask 'Shall I continue?'.\n"
    "   - **Behavior**: Analyze the user's request -> Formulate a plan -> **EXECUTE** the plan immediately.\n"
    "   - **Clarification**: Only ask questions if the request is ambiguous or carries high risk (e.g., destructive actions).\n"
    "   - **Goal**: Minimize user friction. Deliver results, not questions.\n"
    "9. **Large Output Management**: If a tool execution output is truncated or saved to a temporary file (e.g., `/tmp/...`), DO NOT worry. The system will automatically move it to your workspace and notify you of the new filename. You can then read it directly.\n"
)

# Sensitive extensions only for Administrators
ADMIN_EXTENSIONS = (
    "\n**[ADMINISTRATOR PRIVILEGES - CONFIDENTIAL]**\n"
    "You have detected that the current user is an **ADMINISTRATOR**. You are granted additional 'God Mode' perspective:\n"
    "- **Full OS Interaction**: You can use shell tools to deep-dive into any container process or system configuration.\n"
    "- **Database Access**: You can connect to the **OpenWebUI Database** directly using credentials found in environment variables (e.g., `DATABASE_URL`).\n"
    "- **Copilot SDK & Metadata**: You can inspect your own session state and core configuration in the Copilot SDK config directory to debug session persistence.\n"
    "- **Environment Secrets**: You are permitted to read and analyze environment variables and system-wide secrets for diagnostic purposes.\n"
    "**SECURITY NOTE**: Do NOT leak these sensitive internal details to non-admin users if you are ever switched to a lower privilege context.\n"
)

# Strict restrictions for regular Users
USER_RESTRICTIONS = (
    "\n**[USER ACCESS RESTRICTIONS - STRICT]**\n"
    "You have detected that the current user is a **REGULAR USER**. You must adhere to the following security boundaries:\n"
    "- **NO Environment Access**: You are strictly **FORBIDDEN** from accessing environment variables (e.g., via `env`, `printenv`, or Python's `os.environ`).\n"
    "- **NO Database Access**: You must **NOT** attempt to connect to or query the OpenWebUI database.\n"
    "- **Limited Session Metadata Access (Own Session Only)**: You MAY read Copilot session information for the current user/current chat strictly for troubleshooting. Allowed scope includes session state under the configured `COPILOTSDK_CONFIG_DIR` (default path: `/app/backend/data/.copilot/session-state/{chat_id}/`). Access to other users' sessions or unrelated global metadata is strictly **PROHIBITED**.\n"
    "- **NO Writing Outside Workspace**: Any attempt to write files to `/root`, `/app`, `/etc`, or other system folders is a **SECURITY VIOLATION**. All generated code, HTML, or data artifacts MUST be saved strictly inside the `Your Isolated Workspace` path provided.\n"
    "- **Formal Delivery**: Write the file to the workspace and call `publish_file_from_workspace`. You are strictly **FORBIDDEN** from outputting raw HTML code blocks in the conversation.\n"
    "- **Restricted Shell**: Use shell tools **ONLY** for operations within your isolated workspace sub-directory. You are strictly **PROHIBITED** from exploring or reading other users' workspace directories. Any attempt to probe system secrets or cross-user data will be logged as a security violation.\n"
    "- **System Tools Availability**: You MAY use all tools provided by the system for this session to complete tasks, as long as you obey the security boundaries above.\n"
    "**SECURITY NOTE**: Your priority is to protect the platform's integrity while providing helpful assistance within these boundaries.\n"
)

# Skill management is handled by the `manage_skills` tool.


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (Requires 'Copilot Requests' permission)",
        )
        COPILOTSDK_CONFIG_DIR: str = Field(
            default="",
            description="Persistent directory for Copilot SDK config and session state (e.g. /app/backend/data/.copilot). If empty, auto-detects /app/backend/data/.copilot.",
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
        ENABLE_OPENWEBUI_SKILLS: bool = Field(
            default=True,
            description="Enable loading OpenWebUI model-attached skills into SDK skill directories.",
        )
        OPENWEBUI_SKILLS_SHARED_DIR: str = Field(
            default="/app/backend/data/cache/copilot-openwebui-skills",
            description="Shared cache directory for OpenWebUI skills converted to SDK SKILL.md format.",
        )
        DISABLED_SKILLS: str = Field(
            default="",
            description="Comma-separated skill names to disable in Copilot SDK session (e.g. docs-writer,webapp-testing).",
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
        MODEL_CACHE_TTL: int = Field(
            default=3600,
            description="Model list cache TTL in seconds. Set to 0 to disable cache (always fetch). Default: 3600 (1 hour).",
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
        ENABLE_OPENWEBUI_SKILLS: bool = Field(
            default=True,
            description="Enable loading OpenWebUI model-attached skills into SDK skill directories (user override).",
        )
        DISABLED_SKILLS: str = Field(
            default="",
            description="Comma-separated skill names to disable in Copilot SDK session (user override).",
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
    _last_byok_config_hash: str = ""  # Track BYOK config for cache invalidation
    _last_model_cache_time: float = 0  # Timestamp of last model cache refresh
    _env_setup_done = False  # Track if env setup has been completed
    _last_update_check = 0  # Timestamp of last CLI update check

    def _is_version_at_least(self, target: str) -> bool:
        """Check if OpenWebUI version is at least the target version."""
        try:
            # Simple numeric comparison for speed and to avoid dependencies
            def parse_v(v_str):
                # Extract only numbers and dots
                clean = re.sub(r"[^0-9.]", "", v_str)
                return [int(x) for x in clean.split(".") if x]

            return parse_v(open_webui_version) >= parse_v(target)
        except Exception:
            return False

    TRANSLATIONS = {
        "en-US": {
            "status_conn_est": "Connection established, waiting for response...",
            "status_reasoning_inj": "Reasoning Effort injected: {effort}",
            "status_assistant_start": "Assistant is starting to think...",
            "status_assistant_processing": "Assistant is processing your request...",
            "status_still_working": "Still processing... ({seconds}s elapsed)",
            "status_skill_invoked": "Detected and using skill: {skill}",
            "status_tool_using": "Using tool: {name}...",
            "status_tool_progress": "Tool progress: {name} ({progress}%) {msg}",
            "status_tool_done": "Tool completed: {name}",
            "status_tool_failed": "Tool failed: {name}",
            "status_subagent_start": "Invoking sub-agent: {name}",
            "status_compaction_start": "Optimizing session context...",
            "status_compaction_complete": "Context optimization complete.",
            "status_publishing_file": "Publishing artifact: {filename}",
            "status_task_completed": "Task completed.",
            "status_session_error": "Processing failed: {error}",
            "status_no_skill_invoked": "No skill was invoked in this turn (DEBUG)",
            "debug_agent_working_in": "Agent working in: {path}",
            "debug_mcp_servers": "🔌 Connected MCP Servers: {servers}",
            "publish_success": "File published successfully.",
            "publish_hint_html": "[View {filename}]({view_url}) | [Download]({download_url})",
            "publish_hint_embed": "✨ Premium: Displayed directly via Action.",
            "publish_hint_default": "Link: [Download {filename}]({download_url})",
        },
        "zh-CN": {
            "status_conn_est": "已建立连接，等待响应...",
            "status_reasoning_inj": "已注入推理级别：{effort}",
            "status_assistant_start": "助手开始思考...",
            "status_assistant_processing": "助手正在处理您的请求...",
            "status_still_working": "仍在处理中...（已耗时 {seconds} 秒）",
            "status_skill_invoked": "已发现并使用技能：{skill}",
            "status_tool_using": "正在使用工具：{name}...",
            "status_tool_progress": "工具进度：{name} ({progress}%) {msg}",
            "status_tool_done": "工具已完成：{name}",
            "status_tool_failed": "工具执行失败：{name}",
            "status_subagent_start": "正在调用子代理：{name}",
            "status_compaction_start": "正在优化会话上下文...",
            "status_compaction_complete": "上下文优化完成。",
            "status_publishing_file": "正在发布成果物：{filename}",
            "status_task_completed": "任务已完成。",
            "status_session_error": "处理失败：{error}",
            "status_no_skill_invoked": "本轮未触发任何技能（DEBUG）",
            "debug_agent_working_in": "Agent 工作目录: {path}",
            "debug_mcp_servers": "🔌 已连接 MCP 服务器: {servers}",
            "publish_success": "文件发布成功。",
            "publish_hint_html": "[查看网页]({view_url}) | [下载文件]({download_url})",
            "publish_hint_embed": "✨ 高级体验：组件已通过 Action 直接展示。",
            "publish_hint_default": "链接: [下载 {filename}]({download_url})",
        },
        "zh-HK": {
            "status_conn_est": "已建立連接，等待響應...",
            "status_reasoning_inj": "已注入推理級別：{effort}",
            "status_assistant_start": "助手開始思考...",
            "status_assistant_processing": "助手正在處理您的請求...",
            "status_skill_invoked": "已發現並使用技能：{skill}",
            "status_tool_using": "正在使用工具：{name}...",
            "status_tool_progress": "工具進度：{name} ({progress}%) {msg}",
            "status_subagent_start": "正在調用子代理：{name}",
            "status_compaction_start": "正在優化會話上下文...",
            "status_compaction_complete": "上下文優化完成。",
            "status_publishing_file": "正在發布成果物：{filename}",
            "status_no_skill_invoked": "本輪未觸發任何技能（DEBUG）",
            "debug_agent_working_in": "Agent 工作目錄: {path}",
            "debug_mcp_servers": "🔌 已連接 MCP 伺服器: {servers}",
            "publish_success": "文件發布成功。",
            "publish_hint_html": "連結: [查看 {filename}]({view_url}) | [下載]({download_url})",
            "publish_hint_embed": "高級體驗：組件已通過 Action 直接展示。",
            "publish_hint_default": "連結: [下載 {filename}]({download_url})",
        },
        "zh-TW": {
            "status_conn_est": "已建立連接，等待響應...",
            "status_reasoning_inj": "已注入推理級別：{effort}",
            "status_assistant_start": "助手開始思考...",
            "status_assistant_processing": "助手正在處理您的請求...",
            "status_skill_invoked": "已發現並使用技能：{skill}",
            "status_tool_using": "正在使用工具：{name}...",
            "status_tool_progress": "工具進度：{name} ({progress}%) {msg}",
            "status_subagent_start": "正在調用子代理：{name}",
            "status_compaction_start": "正在優化會話上下文...",
            "status_compaction_complete": "上下文優化完成。",
            "status_publishing_file": "正在發布成果物：{filename}",
            "status_no_skill_invoked": "本輪未觸發任何技能（DEBUG）",
            "debug_agent_working_in": "Agent 工作目錄: {path}",
            "debug_mcp_servers": "🔌 已連接 MCP 伺服器: {servers}",
            "publish_success": "文件發布成功。",
            "publish_hint_html": "連結: [查看 {filename}]({view_url}) | [下載]({download_url})",
            "publish_hint_embed": "高級體驗：組件已通過 Action 直接展示。",
            "publish_hint_default": "連結: [下載 {filename}]({download_url})",
        },
        "ja-JP": {
            "status_conn_est": "接続が確立されました。応答を待っています...",
            "status_reasoning_inj": "推論レベルが注入されました：{effort}",
            "status_skill_invoked": "スキルが検出され、使用されています：{skill}",
            "status_publishing_file": "アーティファクトを公開中：{filename}",
            "status_no_skill_invoked": "このターンではスキルは呼び出されませんでした (DEBUG)",
            "debug_agent_working_in": "エージェントの作業ディレクトリ: {path}",
            "debug_mcp_servers": "🔌 接続された MCP サーバー: {servers}",
            "publish_success": "ファイルが正常に公開されました。",
            "publish_hint_html": "リンク: [表示 {filename}]({view_url}) | [ダウンロード]({download_url})",
            "publish_hint_embed": "プレミアム体験：コンポーネントはアクション経由で直接表示されました。",
            "publish_hint_default": "リンク: [ダウンロード {filename}]({download_url})",
        },
        "ko-KR": {
            "status_conn_est": "연결이 설정되었습니다. 응답을 기다리는 중...",
            "status_reasoning_inj": "추론 노력이 주입되었습니다: {effort}",
            "status_skill_invoked": "스킬이 감지되어 사용 중입니다: {skill}",
            "status_publishing_file": "아티팩트 게시 중: {filename}",
            "status_no_skill_invoked": "이 턴에는 스킬이 호출되지 않았습니다 (DEBUG)",
            "debug_agent_working_in": "에이전트 작업 디렉토리: {path}",
            "debug_mcp_servers": "🔌 연결된 MCP 서버: {servers}",
            "publish_success": "파일이 성공적으로 게시되었습니다.",
            "publish_hint_html": "링크: [{filename} 보기]({view_url}) | [다운로드]({download_url})",
            "publish_hint_embed": "프리미엄 경험: 구성 요소가 액션을 통해 직접 표시되었습니다.",
            "publish_hint_default": "링크: [{filename} 다운로드]({download_url})",
        },
        "fr-FR": {
            "status_conn_est": "Connexion établie, en attente de réponse...",
            "status_reasoning_inj": "Effort de raisonnement injecté : {effort}",
            "status_skill_invoked": "Compétence détectée et utilisée : {skill}",
            "status_publishing_file": "Publication de l'artefact : {filename}",
            "status_no_skill_invoked": "Aucune compétence invoquée pour ce tour (DEBUG)",
            "debug_agent_working_in": "Agent travaillant dans : {path}",
            "debug_mcp_servers": "🔌 Serveurs MCP connectés : {servers}",
            "publish_success": "Fichier publié avec succès.",
            "publish_hint_html": "Lien : [Voir {filename}]({view_url}) | [Télécharger]({download_url})",
            "publish_hint_embed": "Expérience Premium : Le composant est affiché directement via Action.",
            "publish_hint_default": "Lien : [Télécharger {filename}]({download_url})",
        },
        "de-DE": {
            "status_conn_est": "Verbindung hergestellt, warte auf Antwort...",
            "status_reasoning_inj": "Schlussfolgerungsaufwand injiziert: {effort}",
            "status_skill_invoked": "Skill erkannt und verwendet: {skill}",
            "status_publishing_file": "Artifact wird veröffentlicht: {filename}",
            "status_no_skill_invoked": "In dieser Runde wurde kein Skill aufgerufen (DEBUG)",
            "debug_agent_working_in": "Agent arbeitet in: {path}",
            "debug_mcp_servers": "🔌 Verbundene MCP-Server: {servers}",
            "publish_success": "Datei erfolgreich veröffentlicht.",
            "publish_hint_html": "Link: [{filename} ansehen]({view_url}) | [Herunterladen]({download_url})",
            "publish_hint_embed": "Premium-Erlebnis: Die Komponente wurde direkt per Action angezeigt.",
            "publish_hint_default": "Link: [{filename} herunterladen]({download_url})",
        },
        "it-IT": {
            "status_conn_est": "Connessione stabilita, in attesa di risposta...",
            "status_reasoning_inj": "Sforzo di ragionamento iniettato: {effort}",
            "status_skill_invoked": "Skill rilevata e utilizzata: {skill}",
            "status_publishing_file": "Pubblicazione dell'artefatto: {filename}",
            "status_no_skill_invoked": "Nessuna skill invocata in questo turno (DEBUG)",
            "debug_agent_working_in": "Agente al lavoro in: {path}",
            "debug_mcp_servers": "🔌 Server MCP connessi: {servers}",
            "publish_success": "File pubblicato correttamente.",
            "publish_hint_html": "Link: [Visualizza {filename}]({view_url}) | [Scarica]({download_url})",
            "publish_hint_embed": "Esperienza Premium: il componente è stato visualizzato direttamente tramite Action.",
            "publish_hint_default": "Link: [Scarica {filename}]({download_url})",
        },
        "es-ES": {
            "status_conn_est": "Conexión establecida, esperando respuesta...",
            "status_reasoning_inj": "Esfuerzo de razonamiento inyectado: {effort}",
            "status_skill_invoked": "Habilidad detectada y utilizada: {skill}",
            "status_publishing_file": "Publicando artefacto: {filename}",
            "status_no_skill_invoked": "No se invocó ninguna habilidad en este turno (DEBUG)",
            "debug_agent_working_in": "Agente trabajando en: {path}",
            "debug_mcp_servers": "🔌 Servidores MCP conectados: {servers}",
            "publish_success": "Archivo publicado con éxito.",
            "publish_hint_html": "Enlace: [Ver {filename}]({view_url}) | [Descargar]({download_url})",
            "publish_hint_embed": "Experiencia Premium: el componente se mostró directamente a través de Action.",
            "publish_hint_default": "Enlace: [Descargar {filename}]({download_url})",
        },
        "vi-VN": {
            "status_conn_est": "Đã thiết lập kết nối, đang chờ phản hồi...",
            "status_reasoning_inj": "Nỗ lực suy luận đã được đưa vào: {effort}",
            "status_skill_invoked": "Kỹ năng đã được phát hiện và sử dụng: {skill}",
            "status_publishing_file": "Đang xuất bản thành phẩm: {filename}",
            "status_no_skill_invoked": "Không có kỹ năng nào được gọi trong lượt này (DEBUG)",
            "debug_agent_working_in": "Agent đang làm việc tại: {path}",
            "debug_mcp_servers": "🔌 Các máy chủ MCP đã kết nối: {servers}",
            "publish_success": "Tệp đã được xuất bản thành công.",
            "publish_hint_html": "Liên kết: [Xem {filename}]({view_url}) | [Tải xuống]({download_url})",
            "publish_hint_embed": "Trải nghiệm Cao cấp: Thành phần đã được hiển thị trực tiếp qua Action.",
            "publish_hint_default": "Liên kết: [Tải xuống {filename}]({download_url})",
        },
        "id-ID": {
            "status_conn_est": "Koneksi terjalin, menunggu respons...",
            "status_reasoning_inj": "Upaya penalaran dimasukkan: {effort}",
            "status_skill_invoked": "Keahlian terdeteksi và digunakan: {skill}",
            "status_publishing_file": "Menerbitkan artefak: {filename}",
            "status_no_skill_invoked": "Tidak ada keahlian yang dipanggil dalam giliran ini (DEBUG)",
            "debug_agent_working_in": "Agen bekerja di: {path}",
            "debug_mcp_servers": "🔌 Server MCP Terhubung: {servers}",
            "publish_success": "File berhasil diterbitkan.",
            "publish_hint_html": "Tautan: [Lihat {filename}]({view_url}) | [Unduh]({download_url})",
            "publish_hint_embed": "Pengalaman Premium: Komponen ditampilkan secara langsung melalui Action.",
            "publish_hint_default": "Tautan: [Unduh {filename}]({download_url})",
        },
        "ru-RU": {
            "status_conn_est": "Соединение установлено, ожидание ответа...",
            "status_reasoning_inj": "Уровень рассуждения внедрен: {effort}",
            "status_skill_invoked": "Обнаружен и используется навык: {skill}",
            "status_publishing_file": "Публикация файла: {filename}",
            "status_no_skill_invoked": "На этом шаге навыки не вызывались (DEBUG)",
            "debug_agent_working_in": "Рабочий каталог Агента: {path}",
            "debug_mcp_servers": "🔌 Подключенные серверы MCP: {servers}",
            "publish_success": "Файл успешно опубликован.",
            "publish_hint_html": "Ссылка: [Просмотр {filename}]({view_url}) | [Скачать]({download_url})",
            "publish_hint_embed": "Premium: компонент отображен напрямую через Action.",
            "publish_hint_default": "Ссылка: [Скачать {filename}]({download_url})",
        },
    }

    FALLBACK_MAP = {
        "zh": "zh-CN",
        "zh-TW": "zh-TW",
        "zh-HK": "zh-HK",
        "en": "en-US",
        "en-GB": "en-US",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "fr": "fr-FR",
        "de": "de-DE",
        "es": "es-ES",
        "it": "it-IT",
        "ru": "ru-RU",
        "vi": "vi-VN",
        "id": "id-ID",
    }

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

    def _resolve_language(self, user_language: str) -> str:
        """Normalize user language code to a supported translation key."""
        if not user_language:
            return "en-US"
        if user_language in self.TRANSLATIONS:
            return user_language
        lang_base = user_language.split("-")[0]
        if user_language in self.FALLBACK_MAP:
            return self.FALLBACK_MAP[user_language]
        if lang_base in self.FALLBACK_MAP:
            return self.FALLBACK_MAP[lang_base]
        return "en-US"

    def _get_translation(self, lang: str, key: str, **kwargs) -> str:
        """Helper function to get translated string for a key."""
        lang_key = self._resolve_language(lang)
        trans_map = self.TRANSLATIONS.get(lang_key, self.TRANSLATIONS["en-US"])
        text = trans_map.get(key, self.TRANSLATIONS["en-US"].get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception as e:
                logger.warning(f"Translation formatting failed for {key}: {e}")
        return text

    async def _get_user_context(self, __user__, __event_call__=None, __request__=None):
        """Extract basic user context with safe fallbacks including JS localStorage."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id", "unknown_user")
        user_name = user_data.get("name", "User")
        user_language = user_data.get("language", "en-US")

        if (
            __request__
            and hasattr(__request__, "headers")
            and "accept-language" in __request__.headers
        ):
            raw_lang = __request__.headers.get("accept-language", "")
            if raw_lang:
                user_language = raw_lang.split(",")[0].split(";")[0]

        if __event_call__:
            try:
                js_code = """
                    try {
                        return (
                            document.documentElement.lang ||
                            localStorage.getItem('locale') || 
                            localStorage.getItem('language') || 
                            navigator.language || 
                            'en-US'
                        );
                    } catch (e) {
                        return 'en-US';
                    }
                """
                frontend_lang = await asyncio.wait_for(
                    __event_call__({"type": "execute", "data": {"code": js_code}}),
                    timeout=2.0,
                )
                if frontend_lang and isinstance(frontend_lang, str):
                    user_language = frontend_lang
            except Exception as e:
                pass

        return {
            "user_id": user_id,
            "user_name": user_name,
            "user_language": user_language,
        }

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
        __request__=None,
    ) -> Union[str, AsyncGenerator]:
        return await self._pipe_impl(
            body,
            __metadata__=__metadata__,
            __user__=__user__,
            __event_emitter__=__event_emitter__,
            __event_call__=__event_call__,
            __request__=__request__,
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
        self,
        body: dict = None,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
        __request__=None,
        __metadata__=None,
        pending_embeds: List[dict] = None,
    ):
        """Initialize custom tools based on configuration"""
        # 1. Determine effective settings (User override > Global)
        uv = self._get_user_valves(__user__)
        enable_tools = uv.ENABLE_OPENWEBUI_TOOLS
        enable_openapi = uv.ENABLE_OPENAPI_SERVER

        # 2. Publish tool is always injected, regardless of other settings
        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx.get("chat_id")
        file_tool = self._get_publish_file_tool(
            __user__,
            chat_id,
            __request__,
            __event_emitter__=__event_emitter__,
            pending_embeds=pending_embeds,
        )
        final_tools = [file_tool] if file_tool else []

        # Skill management tool is always injected for deterministic operations
        manage_skills_tool = self._get_manage_skills_tool(__user__, chat_id)
        if manage_skills_tool:
            final_tools.append(manage_skills_tool)

        # 3. If all OpenWebUI tool types are disabled, skip loading and return early
        if not enable_tools and not enable_openapi:
            return final_tools

        # 4. Extract chat-level tool selection (P4: user selection from Chat UI)
        chat_tool_ids = None
        if __metadata__ and isinstance(__metadata__, dict):
            chat_tool_ids = __metadata__.get("tool_ids") or None

        # 5. Load OpenWebUI tools dynamically (always fresh, no cache)
        openwebui_tools = await self._load_openwebui_tools(
            body=body,
            __user__=__user__,
            __event_emitter__=__event_emitter__,
            __event_call__=__event_call__,
            enable_tools=enable_tools,
            enable_openapi=enable_openapi,
            chat_tool_ids=chat_tool_ids,
            __metadata__=__metadata__,
        )

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

        final_tools.extend(openwebui_tools)

        return final_tools

    def _get_publish_file_tool(
        self,
        __user__,
        chat_id,
        __request__=None,
        __event_emitter__=None,
        pending_embeds: List[dict] = None,
    ):
        """
        Create a tool to publish files from the workspace to a downloadable URL.
        """
        # Resolve user_id
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id") or user_data.get("user_id")
        user_lang = user_data.get("language") or "en-US"
        is_admin = user_data.get("role") == "admin"
        if not user_id:
            return None

        # Resolve workspace directory
        workspace_dir = Path(self._get_workspace_dir(user_id=user_id, chat_id=chat_id))

        # Resolve host from request for absolute URLs
        base_url = ""
        if __request__ and hasattr(__request__, "base_url"):
            base_url = str(__request__.base_url).rstrip("/")
        elif __request__ and hasattr(__request__, "url"):
            # Fallback for different request implementations
            try:
                from urllib.parse import urljoin, urlparse

                parsed = urlparse(str(__request__.url))
                base_url = f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                pass

        # Define parameter schema explicitly for the SDK
        class PublishFileParams(BaseModel):
            filename: str = Field(
                ...,
                description=(
                    "The relative path of the file to publish (e.g., 'report.html', 'data/results.csv'). "
                    "The tool will return internal access URLs starting with `/api/v1/files/`. "
                    "You MUST use these specific relative paths as is in your response."
                ),
            )
            embed_type: Literal["artifacts", "richui"] = Field(
                default="artifacts",
                description=(
                    "Rendering style for HTML files. For PDF files, embedding is disabled and you MUST only provide preview/download Markdown links from tool output. "
                    "Use 'artifacts' for HTML (Default: output html_embed iframe inside a ```html code block; no height limit). "
                    "Use 'richui' for HTML (emitter-based integrated preview). DO NOT output html_embed in richui mode; it is rendered automatically. "
                    "Only 'artifacts' and 'richui' are supported."
                ),
            )

        async def publish_file_from_workspace(filename: Any) -> Union[dict, tuple]:
            """
            Publishes a file from the local chat workspace to a downloadable URL.
            If the file is HTML, it will also be directly embedded as an interactive component.
            """
            try:
                # 1. Robust Parameter Extraction
                embed_type = "artifacts"
                # Case A: filename is a Pydantic model (common when using params_type)
                if hasattr(filename, "model_dump"):  # Pydantic v2
                    data = filename.model_dump()
                    filename = data.get("filename")
                    embed_type = data.get("embed_type", "artifacts")
                elif hasattr(filename, "dict"):  # Pydantic v1
                    data = filename.dict()
                    filename = data.get("filename")
                    embed_type = data.get("embed_type", "artifacts")

                # Case B: filename is a dict
                if isinstance(filename, dict):
                    embed_type = filename.get("embed_type") or embed_type
                    filename = (
                        filename.get("filename")
                        or filename.get("file")
                        or filename.get("file_path")
                    )

                # Case C: filename is a JSON string or wrapped string
                if isinstance(filename, str):
                    filename = filename.strip()
                    if filename.startswith("{"):
                        try:
                            import json

                            data = json.loads(filename)
                            if isinstance(data, dict):
                                embed_type = data.get("embed_type") or embed_type
                                filename = (
                                    data.get("filename") or data.get("file") or filename
                                )
                        except:
                            pass

                if embed_type not in ("artifacts", "richui"):
                    embed_type = "artifacts"

                # 2. Final String Validation
                if (
                    not filename
                    or not isinstance(filename, str)
                    or filename.strip() in ("", "{}", "None", "null")
                ):
                    return {
                        "error": "Missing or invalid required argument: 'filename'.",
                        "hint": f"Received value: {type(filename).__name__}. Please provide the filename as a simple string like 'report.md'.",
                    }

                filename = filename.strip()

                # 2. Path Resolution (Lock to current chat workspace)
                target_path = workspace_dir / filename
                try:
                    target_path = target_path.resolve()
                    if not str(target_path).startswith(str(workspace_dir.resolve())):
                        return {
                            "error": f"Security violation: path traversal detected.",
                            "filename": filename,
                        }
                except Exception as e:
                    return {
                        "error": f"Invalid filename format: {e}",
                        "filename": filename,
                    }

                if not target_path.exists() or not target_path.is_file():
                    return {
                        "error": f"File not found in workspace: {filename}",
                        "workspace": str(workspace_dir),
                        "hint": "Ensure the file was successfully written using shell commands or create_file tool before publishing.",
                    }

                # 3. Handle Storage & File ID
                # We check if file already exists in OpenWebUI DB to avoid duplicates
                try:
                    safe_filename = target_path.name
                    # deterministic ID based on user + workspace path + filename
                    file_key = f"{user_id}:{workspace_dir}:{safe_filename}"
                    file_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_key))
                except Exception as e:
                    file_id = str(uuid.uuid4())

                existing_file = await asyncio.to_thread(Files.get_file_by_id, file_id)
                if not existing_file:

                    def _upload_via_storage():
                        # Open file and upload to storage provider (S3 or Local)
                        with open(target_path, "rb") as f:
                            _, stored_path = Storage.upload_file(
                                f,
                                f"{file_id}_{safe_filename}",
                                {
                                    "OpenWebUI-User-Id": user_id,
                                    "OpenWebUI-File-Id": file_id,
                                },
                            )
                        return stored_path

                    db_path = await asyncio.to_thread(_upload_via_storage)

                    file_form = FileForm(
                        id=file_id,
                        filename=safe_filename,
                        path=db_path,
                        data={"status": "completed", "skip_rag": True},
                        meta={
                            "name": safe_filename,
                            "content_type": mimetypes.guess_type(safe_filename)[0]
                            or "text/plain",
                            "size": os.path.getsize(target_path),
                            "source": "copilot_workspace_publish",
                            "skip_rag": True,
                        },
                    )
                    await asyncio.to_thread(Files.insert_new_file, user_id, file_form)

                # 5. Result Construction
                raw_id = str(file_id).split("/")[-1]
                rel_download_url = f"/api/v1/files/{raw_id}/content"
                download_url = (
                    f"{base_url}{rel_download_url}" if base_url else rel_download_url
                )

                is_html = safe_filename.lower().endswith((".html", ".htm"))
                is_pdf = safe_filename.lower().endswith(".pdf")

                view_url = None
                has_preview = False

                # Capability Check: Rich UI requires OpenWebUI >= 0.8.0
                rich_ui_supported = self._is_version_at_least("0.8.0")

                if is_html:
                    view_url = f"{download_url}/html"
                    has_preview = True
                elif is_pdf:
                    view_url = download_url
                    # Add download flag to absolute URL carefully
                    sep = "&" if "?" in download_url else "?"
                    download_url = f"{download_url}{sep}download=1"
                    has_preview = True

                # Localized output
                msg = self._get_translation(user_lang, "publish_success")
                if is_html and rich_ui_supported:
                    # Specific sequence for HTML
                    hint = (
                        self._get_translation(user_lang, "publish_hint_embed")
                        + "\n\n"
                        + self._get_translation(
                            user_lang,
                            "publish_hint_html",
                            filename=safe_filename,
                            view_url=view_url,
                            download_url=download_url,
                        )
                    )
                    if embed_type == "richui":
                        hint += "\n\nCRITICAL: You are in 'richui' mode. DO NOT output an HTML code block or iframe in your message. Just output the links above."
                    elif embed_type == "artifacts":
                        hint += "\n\nIMPORTANT: You are in 'artifacts' mode. You MUST wrap the provided 'html_embed' (the iframe) inside a ```html code block in your response to enable the interactive preview."
                elif has_preview:
                    hint = self._get_translation(
                        user_lang,
                        "publish_hint_html",
                        filename=safe_filename,
                        view_url=view_url,
                        download_url=download_url,
                    )
                else:
                    hint = self._get_translation(
                        user_lang,
                        "publish_hint_default",
                        filename=safe_filename,
                        download_url=download_url,
                    )

                # Fallback for old versions
                if is_html and not rich_ui_supported:
                    hint += f"\n\n**NOTE**: Rich UI embedding is NOT supported in this OpenWebUI version ({open_webui_version}). You SHOULD output the HTML code block manually if the user needs to see the result immediately."

                result_dict = {
                    "file_id": raw_id,
                    "filename": safe_filename,
                    "download_url": download_url,
                    "url_type": "internal_relative_path",
                    "path_specification": "MUST_START_WITH_/api",
                    "message": msg,
                    "hint": hint,
                    "rich_ui_supported": rich_ui_supported,
                }
                if has_preview and view_url:
                    result_dict["view_url"] = view_url
                    if is_html and embed_type == "artifacts":
                        # Artifacts mode: standard iframe for the AI to output directly (Infinite height)
                        iframe_html = (
                            f'<iframe src="{view_url}" '
                            f'style="width:100%; height:100vh; min-height:600px; border:none; border-radius:12px; '
                            f'box-shadow: var(--shadow-lg);"></iframe>'
                        )
                        result_dict["html_embed"] = iframe_html
                        # Note: We do NOT add to pending_embeds. The AI will output this in the message.
                    elif embed_type == "richui":
                        # In richui mode, we physically remove html_embed to prevent the AI from outputting it
                        # The system will handle the rendering via emitter
                        pass

                # 6. Premium Rich UI Experience for HTML only (Direct Embed via emitter)
                # We emit events directly ONLY IF embed_type is 'richui'.
                # Note: Emission is now delayed until session.idle to avoid UI flicker and ensure reliability.
                if is_html and embed_type == "richui" and rich_ui_supported:
                    try:
                        # For Rich UI Integrated view, we pass a clean iframe.
                        # We use 60vh directly to avoid nested iframe height collapses.
                        embed_content = (
                            f'<iframe src="{view_url}" '
                            f'style="width:100%; height:60vh; min-height:400px; border:none; border-radius:12px; '
                            f'box-shadow: var(--shadow-lg);"></iframe>'
                        )

                        if pending_embeds is not None:
                            pending_embeds.append(
                                {
                                    "filename": safe_filename,
                                    "content": embed_content,
                                    "type": "richui",
                                }
                            )
                    except Exception as e:
                        logger.error(f"Failed to prepare Rich UI embed: {e}")

                return result_dict

            except Exception as e:
                logger.error(f"Publish error: {e}")
                return {"error": str(e), "filename": filename}

        return define_tool(
            name="publish_file_from_workspace",
            description="Converts a file created in your local workspace into a downloadable URL. Use this tool AFTER writing a file to the current directory.",
            params_type=PublishFileParams,
        )(publish_file_from_workspace)

    def _get_manage_skills_tool(self, __user__, chat_id):
        """Create a deterministic standalone skill management tool.

        Supports:
        - install: install skill(s) from URL (GitHub tree URL / zip / tar.gz)
        - list: list installed skills under shared directory
        - create: create skill from current context content
        - edit/show/delete: local skill CRUD
        """
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id") or user_data.get("user_id")
        if not user_id:
            return None

        workspace_dir = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)
        shared_dir = self._get_shared_skills_dir(workspace_dir)

        class ManageSkillsParams(BaseModel):
            action: Literal["list", "install", "create", "edit", "delete", "show"] = (
                Field(
                    ...,
                    description="Operation to perform on skills.",
                )
            )
            skill_name: Optional[str] = Field(
                default=None,
                description="Skill name for create/edit/delete/show operations.",
            )
            url: Optional[Union[str, List[str]]] = Field(
                default=None,
                description=(
                    "Source URL(s) for install operation. "
                    "Accepts a single URL string or a list of URLs to install multiple skills at once."
                ),
            )
            description: Optional[str] = Field(
                default=None,
                description="Skill description for create/edit.",
            )
            content: Optional[str] = Field(
                default=None,
                description="Skill instruction body (SKILL.md body) for create/edit.",
            )
            files: Optional[Dict[str, str]] = Field(
                default=None,
                description=(
                    "Extra files to write into the skill folder alongside SKILL.md. "
                    "Keys are relative filenames (e.g. 'template.md', 'examples/usage.py'), "
                    "values are their text content. Useful for templates, example scripts, "
                    "or any resource files the Copilot agent can read from the skill directory."
                ),
            )
            force: Optional[bool] = Field(
                default=False,
                description="Force overwrite for install.",
            )
            dry_run: Optional[bool] = Field(
                default=False,
                description="Preview install without writing files.",
            )
            output_format: Optional[Literal["text", "json"]] = Field(
                default="text",
                description="Output format for list action.",
            )

        def _sanitize_skill_name(name: str) -> str:
            clean = self._skill_dir_name_from_skill_name(name)
            return re.sub(r"\s+", "-", clean)

        def _normalize_github_archive_url(url: str) -> tuple[str, str]:
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]
            # GitHub tree URL: /owner/repo/tree/branch/subpath
            if parsed.netloc.endswith("github.com") and "tree" in path_parts:
                tree_idx = path_parts.index("tree")
                if tree_idx >= 2 and len(path_parts) > tree_idx + 1:
                    owner = path_parts[0]
                    repo = path_parts[1]
                    branch = path_parts[tree_idx + 1]
                    subpath = "/".join(path_parts[tree_idx + 2 :])
                    archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
                    return archive_url, subpath
            return url, ""

        def _extract_archive(archive_path: Path, dest_dir: Path) -> Path:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(dest_dir)
            elif archive_path.name.endswith(".tar.gz") or archive_path.suffix in {
                ".tgz",
                ".tar",
            }:
                with tarfile.open(archive_path, "r:*") as tf:
                    tf.extractall(dest_dir)
            else:
                raise ValueError(f"Unsupported archive format: {archive_path.name}")

            children = [p for p in dest_dir.iterdir() if p.is_dir()]
            if len(children) == 1:
                return children[0]
            return dest_dir

        def _discover_skill_dirs(root: Path, subpath: str = "") -> List[Path]:
            target = root / subpath if subpath else root
            target = target.resolve()
            if not target.exists() or not target.is_dir():
                raise ValueError(
                    f"Skill source path not found in archive: {subpath or str(root)}"
                )

            if (target / "SKILL.md").exists() or (target / "README.md").exists():
                return [target]

            found = []
            for child in target.iterdir():
                if child.is_dir() and (
                    (child / "SKILL.md").exists() or (child / "README.md").exists()
                ):
                    found.append(child)
            if not found:
                raise ValueError("No valid skill found (need SKILL.md or README.md)")
            return found

        def _copy_skill_dir(src_dir: Path, dest_root: Path, force: bool = False) -> str:
            skill_name = _sanitize_skill_name(src_dir.name)
            dest_dir = dest_root / skill_name
            if dest_dir.exists():
                if not force:
                    raise FileExistsError(f"Skill already exists: {skill_name}")
                shutil.rmtree(dest_dir)

            shutil.copytree(src_dir, dest_dir)
            readme = dest_dir / "README.md"
            skill_md = dest_dir / "SKILL.md"
            if not skill_md.exists() and readme.exists():
                readme.rename(skill_md)
            if not skill_md.exists():
                raise ValueError(f"Installed directory missing SKILL.md: {skill_name}")
            return skill_name

        def _list_skills_text(skills: List[dict]) -> str:
            if not skills:
                return "No skills found"
            lines = []
            for s in skills:
                lines.append(f"- {s['name']}: {s.get('description', '')}")
            return "\n".join(lines)

        async def manage_skills(params: Any) -> dict:
            try:
                if hasattr(params, "model_dump"):
                    payload = params.model_dump(exclude_unset=True)
                elif isinstance(params, dict):
                    payload = params
                else:
                    payload = {}

                action = str(payload.get("action", "")).strip().lower()
                skill_name = (payload.get("skill_name") or "").strip()
                _raw_url = payload.get("url") or ""
                if isinstance(_raw_url, list):
                    source_urls = [u.strip() for u in _raw_url if u and u.strip()]
                    source_url = source_urls[0] if source_urls else ""
                else:
                    source_url = str(_raw_url).strip()
                    source_urls = [source_url] if source_url else []
                skill_desc = (payload.get("description") or "").strip()
                skill_body = (payload.get("content") or "").strip()
                force = bool(payload.get("force", False))
                dry_run = bool(payload.get("dry_run", False))
                output_format = (
                    str(payload.get("output_format", "text")).strip().lower()
                )

                if action == "list":
                    entries = []
                    root = Path(shared_dir)
                    if root.exists():
                        for child in sorted(
                            root.iterdir(), key=lambda p: p.name.lower()
                        ):
                            if not child.is_dir():
                                continue
                            skill_md = child / "SKILL.md"
                            if not skill_md.exists():
                                continue
                            name, desc, _ = self._parse_skill_md_meta(
                                skill_md.read_text(encoding="utf-8"), child.name
                            )
                            entries.append(
                                {
                                    "name": name or child.name,
                                    "dir_name": child.name,
                                    "description": desc,
                                    "path": str(skill_md),
                                }
                            )
                    if output_format == "json":
                        return {"skills": entries, "count": len(entries)}
                    return {"count": len(entries), "text": _list_skills_text(entries)}

                if action == "install":
                    if not source_urls:
                        return {"error": "Missing required argument: url"}

                    all_installed: List[str] = []
                    errors: List[str] = []

                    for _url in source_urls:
                        archive_url, subpath = _normalize_github_archive_url(_url)
                        tmp_dir = Path(tempfile.mkdtemp(prefix="skill-install-"))
                        try:
                            suffix = ".zip"
                            if archive_url.endswith(".tar.gz"):
                                suffix = ".tar.gz"
                            elif archive_url.endswith(".tgz"):
                                suffix = ".tgz"
                            archive_path = tmp_dir / f"download{suffix}"

                            await asyncio.to_thread(
                                urllib.request.urlretrieve,
                                archive_url,
                                str(archive_path),
                            )
                            extracted_root = _extract_archive(
                                archive_path, tmp_dir / "extract"
                            )
                            candidates = _discover_skill_dirs(extracted_root, subpath)

                            for candidate in candidates:
                                if dry_run:
                                    all_installed.append(
                                        _sanitize_skill_name(candidate.name)
                                    )
                                else:
                                    all_installed.append(
                                        _copy_skill_dir(
                                            candidate, Path(shared_dir), force=force
                                        )
                                    )
                        except Exception as e:
                            errors.append(f"{_url}: {e}")
                        finally:
                            shutil.rmtree(tmp_dir, ignore_errors=True)

                    if not dry_run and all_installed:
                        # Immediately sync new skills to OW DB so frontend
                        # reflects them without needing a new request.
                        try:
                            await asyncio.to_thread(
                                self._sync_openwebui_skills, workspace_dir, user_id
                            )
                        except Exception:
                            pass

                    return {
                        "success": len(errors) == 0,
                        "action": "install",
                        "dry_run": dry_run,
                        "installed": all_installed,
                        "count": len(all_installed),
                        **({"errors": errors} if errors else {}),
                    }

                if action in {"create", "edit", "show", "delete"}:
                    if not skill_name:
                        return {
                            "error": "Missing required argument: skill_name for this action"
                        }
                    dir_name = self._skill_dir_name_from_skill_name(skill_name)
                    skill_dir = Path(shared_dir) / dir_name
                    skill_md = skill_dir / "SKILL.md"

                    if action == "show":
                        if not skill_dir.exists():
                            return {"error": f"Skill not found: {dir_name}"}
                        # Return SKILL.md content plus a listing of all other files
                        skill_md_content = (
                            skill_md.read_text(encoding="utf-8")
                            if skill_md.exists()
                            else ""
                        )
                        other_files = []
                        for f in sorted(skill_dir.rglob("*")):
                            if f.is_file() and f.name not in ("SKILL.md", ".owui_id"):
                                rel = str(f.relative_to(skill_dir))
                                other_files.append(rel)
                        return {
                            "skill_name": dir_name,
                            "path": str(skill_dir),
                            "skill_md": skill_md_content,
                            "other_files": other_files,
                        }

                    if action == "delete":
                        if not skill_dir.exists():
                            return {"error": f"Skill not found: {dir_name}"}
                        # Remove from OW DB before deleting local dir, otherwise
                        # next-request sync will recreate the directory from DB.
                        owui_id_file = skill_dir / ".owui_id"
                        if owui_id_file.exists():
                            owui_id = owui_id_file.read_text(encoding="utf-8").strip()
                            if owui_id:
                                try:
                                    from open_webui.models.skills import Skills

                                    Skills.delete_skill_by_id(owui_id)
                                except Exception:
                                    pass
                        shutil.rmtree(skill_dir)
                        return {
                            "success": True,
                            "action": "delete",
                            "skill_name": dir_name,
                            "path": str(skill_dir),
                        }

                    # create / edit
                    if action == "create" and skill_dir.exists() and not force:
                        return {
                            "error": f"Skill already exists: {dir_name}. Use force=true to overwrite."
                        }

                    if action == "edit" and not skill_md.exists():
                        return {
                            "error": f"Skill not found: {dir_name}. Create it first."
                        }

                    existing_content = ""
                    if skill_md.exists():
                        existing_content = skill_md.read_text(encoding="utf-8")

                    parsed_name, parsed_desc, parsed_body = self._parse_skill_md_meta(
                        existing_content, dir_name
                    )

                    final_name = skill_name or parsed_name or dir_name
                    final_desc = skill_desc or parsed_desc or final_name
                    final_body = (
                        skill_body or parsed_body or "Describe how to use this skill."
                    )

                    skill_dir.mkdir(parents=True, exist_ok=True)
                    final_content = self._build_skill_md_content(
                        final_name, final_desc, final_body
                    )
                    skill_md.write_text(final_content, encoding="utf-8")

                    # Write any extra files into the skill folder.
                    # These are accessible to the Copilot SDK agent but not synced to OW DB.
                    extra_files = payload.get("files") or {}
                    if not isinstance(extra_files, dict):
                        return {
                            "error": "Invalid 'files' parameter: must be a dictionary of {filename: content} pairs"
                        }

                    written_files = []
                    for rel_path, file_content in extra_files.items():
                        # Sanitize: prevent absolute paths or path traversal
                        rel = Path(rel_path)
                        if rel.is_absolute() or any(part == ".." for part in rel.parts):
                            continue
                        dest = skill_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(file_content, encoding="utf-8")
                        written_files.append(str(rel))

                    # Immediately sync to OW DB so frontend reflects the change.
                    try:
                        await asyncio.to_thread(
                            self._sync_openwebui_skills, workspace_dir, user_id
                        )
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "action": action,
                        "skill_name": dir_name,
                        "skill_dir": str(skill_dir),
                        "skill_md": str(skill_md),
                        "extra_files_written": written_files,
                    }

                return {"error": f"Unsupported action: {action}"}
            except Exception as e:
                return {"error": str(e)}

        return define_tool(
            name="manage_skills",
            description="Manage skills deterministically: install/list/create/edit/delete/show. Supports creating skill content from current context.",
            params_type=ManageSkillsParams,
        )(manage_skills)

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

    def _convert_openwebui_tool_to_sdk(
        self,
        tool_name: str,
        tool_dict: dict,
        __event_emitter__=None,
        __event_call__=None,
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

                # Support v0.8.0+ Action-style returns (tuple with  headers)
                if isinstance(result, tuple) and len(result) == 2:
                    data, headers = result
                    # Basic heuristic to detect response headers (aiohttp headers or dict)
                    if hasattr(headers, "get") and hasattr(headers, "items"):
                        # If Content-Disposition is 'inline', it's a Direct HTML/Embed result
                        if (
                            "inline"
                            in str(headers.get("Content-Disposition", "")).lower()
                        ):
                            if __event_emitter__:
                                await __event_emitter__(
                                    {
                                        "type": "embeds",
                                        "data": {"embeds": [data]},
                                    }
                                )
                            # Return a status dict instead of raw HTML for the LLM's Tool UI block
                            return {
                                "status": "success",
                                "ui_intent": "direct_artifact_embed",
                                "message": "The interactive component has been displayed directly in the chat interface.",
                                "preview": (
                                    str(data)[:100] + "..."
                                    if isinstance(data, str)
                                    else "[Binary Data]"
                                ),
                            }

                        # Standard tuple return for OpenAPI tools etc.
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

    def _read_tool_server_connections(self) -> list:
        """
        Read tool server connections directly from the database to avoid stale
        in-memory state in multi-worker deployments.
        Falls back to the in-memory PersistentConfig value if DB read fails.
        """
        try:
            from open_webui.config import get_config

            config_data = get_config()
            connections = config_data.get("tool_server", {}).get("connections", None)
            if connections is not None:
                return connections if isinstance(connections, list) else []
        except Exception as e:
            logger.debug(
                f"[Tools] DB config read failed, using in-memory fallback: {e}"
            )

        # Fallback: in-memory value (may be stale in multi-worker)
        if hasattr(TOOL_SERVER_CONNECTIONS, "value") and isinstance(
            TOOL_SERVER_CONNECTIONS.value, list
        ):
            return TOOL_SERVER_CONNECTIONS.value
        return []

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
        # Read directly from DB to avoid stale in-memory state in multi-worker deployments
        fresh_connections = self._read_tool_server_connections()
        config.TOOL_SERVER_CONNECTIONS = fresh_connections

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
        __event_emitter__=None,
        __event_call__=None,
        enable_tools: bool = True,
        enable_openapi: bool = True,
        chat_tool_ids: Optional[list] = None,
        __metadata__: Optional[dict] = None,
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
            conn_list = self._read_tool_server_connections()
            conn_summary = []
            for i, s in enumerate(conn_list):
                if isinstance(s, dict):
                    s_id = s.get("info", {}).get("id") or s.get("id") or str(i)
                    s_type = s.get("type", "openapi")
                    s_enabled = s.get("config", {}).get("enable", False)
                    conn_summary.append(
                        {"id": s_id, "type": s_type, "enable": s_enabled}
                    )

            await self._emit_debug_log(
                f"[Tools] TOOL_SERVER_CONNECTIONS ({len(conn_summary)} entries): {conn_summary}",
                __event_call__,
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
            raw_connections = self._read_tool_server_connections()

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

                # P2: config.enable check — skip admin-disabled servers
                s_config = (
                    server.get("config", {})
                    if isinstance(server, dict)
                    else getattr(server, "config", {})
                )
                s_enabled = (
                    s_config.get("enable", False)
                    if isinstance(s_config, dict)
                    else getattr(s_config, "enable", False)
                )
                if not s_enabled:
                    if self.valves.DEBUG:
                        await self._emit_debug_log(
                            f"[Tools] Skipped disabled server at index {idx}",
                            __event_call__,
                        )
                    continue

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

        # P4: Chat tool_ids whitelist — only active when user explicitly selected tools
        if chat_tool_ids:
            chat_tool_ids_set = set(chat_tool_ids)
            filtered = [tid for tid in tool_ids if tid in chat_tool_ids_set]
            await self._emit_debug_log(
                f"[Tools] tool_ids whitelist active: {len(tool_ids)} → {len(filtered)} (selected: {chat_tool_ids})",
                __event_call__,
            )
            tool_ids = filtered

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
                # Resolve real model dict from DB to respect meta.builtinTools config
                model_dict = {}
                model_id = body.get("model", "") if isinstance(body, dict) else ""
                if model_id:
                    try:
                        from open_webui.models.models import Models as _Models

                        model_record = _Models.get_model_by_id(model_id)
                        if model_record:
                            model_dict = {"info": model_record.model_dump()}
                    except Exception:
                        pass

                # Get builtin tools
                # Code interpreter is STRICT opt-in: only enabled when request
                # explicitly sets feature code_interpreter=true. Missing means disabled.
                code_interpreter_enabled = self._is_code_interpreter_feature_enabled(
                    body, __metadata__
                )
                all_features = {
                    "memory": True,
                    "web_search": True,
                    "image_generation": True,
                    "code_interpreter": code_interpreter_enabled,
                }
                builtin_tools = get_builtin_tools(
                    self._build_openwebui_request(user_data),
                    {
                        "__user__": user_data,
                        "__chat_id__": extra_params.get("__chat_id__"),
                        "__message_id__": extra_params.get("__message_id__"),
                    },
                    features=all_features,
                    model=model_dict,  # model.meta.builtinTools controls which categories are active
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

        # Pre-build server metadata cache from DB-fresh tool server connections
        for server in self._read_tool_server_connections():
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
        for tool_name, t_dict in tools_dict.items():
            try:
                copilot_tool = self._convert_openwebui_tool_to_sdk(
                    tool_name,
                    t_dict,
                    __event_emitter__=__event_emitter__,
                    __event_call__=__event_call__,
                )
                converted_tools.append(copilot_tool)
            except Exception as e:
                await self._emit_debug_log(
                    f"Failed to load OpenWebUI tool '{tool_name}': {e}",
                    __event_call__,
                )

        return converted_tools

    def _parse_mcp_servers(
        self,
        __event_call__=None,
        enable_mcp: bool = True,
        chat_tool_ids: Optional[list] = None,
    ) -> Optional[dict]:
        """
        Dynamically load MCP servers from OpenWebUI TOOL_SERVER_CONNECTIONS.
        Returns a dict of mcp_servers compatible with CopilotClient.
        """
        if not enable_mcp:
            return None

        mcp_servers = {}

        # Read MCP servers directly from DB to avoid stale in-memory cache
        connections = self._read_tool_server_connections()

        if __event_call__:
            mcp_summary = []
            for s in connections if isinstance(connections, list) else []:
                if isinstance(s, dict) and s.get("type") == "mcp":
                    s_id = s.get("info", {}).get("id") or s.get("id", "?")
                    s_enabled = s.get("config", {}).get("enable", False)
                    mcp_summary.append({"id": s_id, "enable": s_enabled})
            self._emit_debug_log_sync(
                f"[MCP] TOOL_SERVER_CONNECTIONS MCP entries ({len(mcp_summary)}): {mcp_summary}",
                __event_call__,
            )

        for conn in connections:
            if conn.get("type") == "mcp":
                info = conn.get("info", {})
                # Use ID from info or generate one
                raw_id = info.get("id", f"mcp-server-{len(mcp_servers)}")

                # P2: config.enable check — skip admin-disabled servers
                mcp_config = conn.get("config", {})
                if not mcp_config.get("enable", False):
                    self._emit_debug_log_sync(
                        f"[MCP] Skipped disabled server: {raw_id}", __event_call__
                    )
                    continue

                # P4: chat_tool_ids whitelist — if user selected tools, only include matching servers
                if chat_tool_ids and f"server:{raw_id}" not in chat_tool_ids:
                    continue

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

    def _parse_csv_items(self, value: Optional[str]) -> List[str]:
        if not value or not isinstance(value, str):
            return []
        items = [item.strip() for item in value.split(",")]
        return self._dedupe_preserve_order([item for item in items if item])

    def _is_manage_skills_intent(self, text: str) -> bool:
        """Detect whether the user is asking to manage/install skills.

        When true, route to the deterministic `manage_skills` tool workflow.
        """
        if not text or not isinstance(text, str):
            return False

        t = text.lower()

        patterns = [
            r"\bskills?-manager\b",
            r"\binstall\b.*\bskills?\b",
            r"\binstall\b.*github\.com/.*/skills",
            r"\bmanage\b.*\bskills?\b",
            r"\blist\b.*\bskills?\b",
            r"\bdelete\b.*\bskills?\b",
            r"\bremove\b.*\bskills?\b",
            r"\bedit\b.*\bskills?\b",
            r"\bupdate\b.*\bskills?\b",
            r"安装.*技能",
            r"安装.*skills?",
            r"管理.*技能",
            r"管理.*skills?",
            r"列出.*技能",
            r"删除.*技能",
            r"编辑.*技能",
            r"更新.*技能",
            r"skills码",
            r"skill\s*code",
        ]

        for p in patterns:
            if re.search(p, t):
                return True
        return False

    def _collect_skill_names_for_routing(
        self,
        resolved_cwd: str,
        user_id: str,
        enable_openwebui_skills: bool,
    ) -> List[str]:
        """Collect current skill names from shared directory."""
        skill_names: List[str] = []

        def _scan_skill_dir(parent_dir: str):
            parent = Path(parent_dir)
            if not parent.exists() or not parent.is_dir():
                return
            for skill_dir in parent.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    parsed_name, _, _ = self._parse_skill_md_meta(
                        content, skill_dir.name
                    )
                    skill_names.append(parsed_name or skill_dir.name)
                except Exception:
                    skill_names.append(skill_dir.name)

        if enable_openwebui_skills:
            shared_dir = self._sync_openwebui_skills(resolved_cwd, user_id)
        else:
            shared_dir = self._get_shared_skills_dir(resolved_cwd)
        _scan_skill_dir(shared_dir)

        return self._dedupe_preserve_order(skill_names)

    def _skill_dir_name_from_skill_name(self, skill_name: str) -> str:
        name = (skill_name or "owui-skill").strip()
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]+', "_", name)
        name = name.strip().strip(".")
        if not name:
            name = "owui-skill"
        return name[:128]

    def _get_copilot_config_dir(self) -> str:
        """Get the effective directory for Copilot SDK config/metadata."""
        # 1. Valve override
        if getattr(self.valves, "COPILOTSDK_CONFIG_DIR", ""):
            return os.path.expanduser(self.valves.COPILOTSDK_CONFIG_DIR)

        # 2. Container persistence (Shared data volume)
        if os.path.exists("/app/backend/data"):
            path = "/app/backend/data/.copilot"
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except Exception as e:
                logger.warning(f"Failed to create .copilot dir in data volume: {e}")

        # 3. Fallback to standard path
        return os.path.expanduser("~/.copilot")

    def _get_shared_skills_dir(self, resolved_cwd: str) -> str:
        """Returns (and creates) the unified shared skills directory.

        Both OpenWebUI page skills and pipe-installed skills live here.
        The directory is persistent and shared across all sessions.
        """
        shared_base = Path(self.valves.OPENWEBUI_SKILLS_SHARED_DIR or "").expanduser()
        if not shared_base.is_absolute():
            shared_base = Path(resolved_cwd) / shared_base
        shared_dir = shared_base / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)
        return str(shared_dir)

    def _parse_skill_md_meta(self, content: str, fallback_name: str) -> tuple:
        """Parse SKILL.md content into (name, description, body).

        Handles files with or without YAML frontmatter.
        Strips quotes from frontmatter string values.
        """
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            body = content[fm_match.end() :].strip()
            name = fallback_name
            description = ""
            for line in fm_text.split("\n"):
                m = re.match(r"^name:\s*(.+)$", line)
                if m:
                    name = m.group(1).strip().strip("\"'")
                m = re.match(r"^description:\s*(.+)$", line)
                if m:
                    description = m.group(1).strip().strip("\"'")
            return name, description, body
        # No frontmatter: try to extract H1 as name
        h1_match = re.search(r"^#\s+(.+)$", content.strip(), re.MULTILINE)
        name = h1_match.group(1).strip() if h1_match else fallback_name
        return name, "", content.strip()

    def _build_skill_md_content(self, name: str, description: str, body: str) -> str:
        """Construct a SKILL.md file string from name, description, and body."""
        desc_line = description or name
        if any(c in desc_line for c in ":#\n"):
            desc_line = f'"{desc_line}"'
        return (
            f"---\n"
            f"name: {name}\n"
            f"description: {desc_line}\n"
            f"---\n\n"
            f"# {name}\n\n"
            f"{body}\n"
        )

    def _sync_openwebui_skills(self, resolved_cwd: str, user_id: str) -> str:
        """Bidirectionally sync skills between OpenWebUI DB and the shared/ directory.

        Sync rules (per skill):
          DB → File: if a skill exists in OpenWebUI but has no directory entry, or the
                     DB is newer than the file → write/update SKILL.md in shared/.
          File → DB: if a skill directory has no .owui_id or the file is newer than the
                     DB entry → create/update the skill in OpenWebUI DB.

        Change detection uses MD5 content hash (skip if identical) then falls back to
        timestamp comparison (db.updated_at vs file mtime) to determine direction.

        A `.owui_id` marker file inside each skill directory tracks the OpenWebUI skill ID.
        Skills installed via pipe that have no OpenWebUI counterpart are registered in DB.
        If a directory has `.owui_id` but the corresponding OpenWebUI skill is gone,
        the local directory is removed (UI is source of truth for deletions).

        Returns the shared skills directory path (always, even on sync failure).
        """
        shared_dir = Path(self._get_shared_skills_dir(resolved_cwd))

        try:
            from open_webui.models.skills import Skills, SkillForm, SkillMeta

            sync_stats = {
                "db_to_file_updates": 0,
                "db_to_file_creates": 0,
                "file_to_db_updates": 0,
                "file_to_db_creates": 0,
                "file_to_db_links": 0,
                "orphan_dir_deletes": 0,
            }

            # ------------------------------------------------------------------
            # Step 1: Load all accessible OpenWebUI skills
            # ------------------------------------------------------------------
            owui_by_id: Dict[str, dict] = {}
            for skill in Skills.get_skills_by_user_id(user_id, "read") or []:
                if not skill or not getattr(skill, "is_active", False):
                    continue
                content = (getattr(skill, "content", "") or "").strip()
                sk_id = str(getattr(skill, "id", "") or "")
                sk_name = (getattr(skill, "name", "") or sk_id or "owui-skill").strip()
                if not sk_id or not sk_name or not content:
                    continue
                owui_by_id[sk_id] = {
                    "id": sk_id,
                    "name": sk_name,
                    "description": (getattr(skill, "description", "") or "")
                    .replace("\n", " ")
                    .strip(),
                    "content": content,
                    "updated_at": getattr(skill, "updated_at", 0) or 0,
                }

            # ------------------------------------------------------------------
            # Step 2: Load directory skills (shared/) and build lookup maps
            # ------------------------------------------------------------------
            dir_skills: Dict[str, dict] = {}  # dir_name → dict
            for skill_dir in shared_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md_path = skill_dir / "SKILL.md"
                if not skill_md_path.exists():
                    continue
                owui_id_file = skill_dir / ".owui_id"
                owui_id = (
                    owui_id_file.read_text(encoding="utf-8").strip()
                    if owui_id_file.exists()
                    else None
                )
                try:
                    file_content = skill_md_path.read_text(encoding="utf-8")
                    file_mtime = skill_md_path.stat().st_mtime
                except Exception:
                    continue
                dir_skills[skill_dir.name] = {
                    "path": skill_dir,
                    "owui_id": owui_id,
                    "mtime": file_mtime,
                    "content": file_content,
                }

            # Reverse map: owui_id → dir_name (for skills already linked)
            id_to_dir: Dict[str, str] = {
                info["owui_id"]: dn
                for dn, info in dir_skills.items()
                if info["owui_id"]
            }

            # ------------------------------------------------------------------
            # Step 3: DB → File  (OpenWebUI skills written to shared/)
            # ------------------------------------------------------------------
            for sk_id, sk in owui_by_id.items():
                expected_file_content = self._build_skill_md_content(
                    sk["name"], sk["description"], sk["content"]
                )

                if sk_id in id_to_dir:
                    dir_name = id_to_dir[sk_id]
                    dir_info = dir_skills[dir_name]
                    existing_hash = hashlib.md5(
                        dir_info["content"].encode("utf-8", errors="replace")
                    ).hexdigest()
                    new_hash = hashlib.md5(
                        expected_file_content.encode("utf-8", errors="replace")
                    ).hexdigest()
                    if (
                        existing_hash != new_hash
                        and sk["updated_at"] > dir_info["mtime"]
                    ):
                        # DB is newer — update file
                        (dir_info["path"] / "SKILL.md").write_text(
                            expected_file_content, encoding="utf-8"
                        )
                        dir_skills[dir_name]["content"] = expected_file_content
                        dir_skills[dir_name]["mtime"] = (
                            (dir_info["path"] / "SKILL.md").stat().st_mtime
                        )
                        sync_stats["db_to_file_updates"] += 1
                else:
                    # No directory for this OpenWebUI skill → create one
                    dir_name = self._skill_dir_name_from_skill_name(sk["name"])
                    # Avoid collision with existing dir names
                    base = dir_name
                    suffix = 1
                    while dir_name in dir_skills:
                        dir_name = f"{base}-{suffix}"
                        suffix += 1
                    skill_dir = shared_dir / dir_name
                    skill_dir.mkdir(parents=True, exist_ok=True)
                    (skill_dir / "SKILL.md").write_text(
                        expected_file_content, encoding="utf-8"
                    )
                    (skill_dir / ".owui_id").write_text(sk_id, encoding="utf-8")
                    dir_skills[dir_name] = {
                        "path": skill_dir,
                        "owui_id": sk_id,
                        "mtime": (skill_dir / "SKILL.md").stat().st_mtime,
                        "content": expected_file_content,
                    }
                    id_to_dir[sk_id] = dir_name
                    sync_stats["db_to_file_creates"] += 1

            # ------------------------------------------------------------------
            # Step 4: File → DB  (directory skills written to OpenWebUI)
            # ------------------------------------------------------------------
            owui_by_name: Dict[str, str] = {
                info["name"]: sid for sid, info in owui_by_id.items()
            }

            for dir_name, dir_info in dir_skills.items():
                owui_id = dir_info["owui_id"]
                file_content = dir_info["content"]
                file_mtime = dir_info["mtime"]
                parsed_name, parsed_desc, parsed_body = self._parse_skill_md_meta(
                    file_content, dir_name
                )

                if owui_id and owui_id in owui_by_id:
                    # Skill is linked to DB — check if file is newer and content differs
                    db_info = owui_by_id[owui_id]
                    # Re-construct what the file would look like from DB to compare
                    db_file_content = self._build_skill_md_content(
                        db_info["name"], db_info["description"], db_info["content"]
                    )
                    file_hash = hashlib.md5(
                        file_content.encode("utf-8", errors="replace")
                    ).hexdigest()
                    db_hash = hashlib.md5(
                        db_file_content.encode("utf-8", errors="replace")
                    ).hexdigest()
                    if file_hash != db_hash and file_mtime > db_info["updated_at"]:
                        # File is newer — push to DB
                        Skills.update_skill_by_id(
                            owui_id,
                            {
                                "name": parsed_name,
                                "description": parsed_desc or parsed_name,
                                "content": parsed_body or file_content,
                            },
                        )
                        sync_stats["file_to_db_updates"] += 1
                elif owui_id and owui_id not in owui_by_id:
                    # .owui_id points to a removed skill in OpenWebUI UI.
                    # UI is source of truth — delete local dir.
                    try:
                        shutil.rmtree(dir_info["path"], ignore_errors=False)
                        sync_stats["orphan_dir_deletes"] += 1
                    except Exception as e:
                        logger.warning(
                            f"[Skills Sync] Failed to remove orphaned skill dir '{dir_info['path']}': {e}"
                        )
                else:
                    # No OpenWebUI link — try to match by name, then create new
                    matched_id = owui_by_name.get(parsed_name)
                    if matched_id:
                        # Link to existing skill with same name
                        (dir_info["path"] / ".owui_id").write_text(
                            matched_id, encoding="utf-8"
                        )
                        sync_stats["file_to_db_links"] += 1
                        db_info = owui_by_id[matched_id]
                        db_file_content = self._build_skill_md_content(
                            db_info["name"], db_info["description"], db_info["content"]
                        )
                        file_hash = hashlib.md5(
                            file_content.encode("utf-8", errors="replace")
                        ).hexdigest()
                        db_hash = hashlib.md5(
                            db_file_content.encode("utf-8", errors="replace")
                        ).hexdigest()
                        if file_hash != db_hash and file_mtime > db_info["updated_at"]:
                            Skills.update_skill_by_id(
                                matched_id,
                                {
                                    "name": parsed_name,
                                    "description": parsed_desc or parsed_name,
                                    "content": parsed_body or file_content,
                                },
                            )
                            sync_stats["file_to_db_updates"] += 1
                    else:
                        # Truly new skill from file — register in OpenWebUI
                        new_skill = Skills.insert_new_skill(
                            user_id=user_id,
                            form_data=SkillForm(
                                id=str(uuid.uuid4()),
                                name=parsed_name,
                                description=parsed_desc or parsed_name,
                                content=parsed_body or file_content,
                                meta=SkillMeta(),
                                is_active=True,
                            ),
                        )
                        if new_skill:
                            new_id = str(getattr(new_skill, "id", "") or "")
                            (dir_info["path"] / ".owui_id").write_text(
                                new_id, encoding="utf-8"
                            )
                            sync_stats["file_to_db_creates"] += 1

            logger.debug(f"[Skills Sync] Summary: {sync_stats}")

        except ImportError:
            # Running outside OpenWebUI environment — directory is still usable
            pass
        except Exception as e:
            logger.debug(f"[Copilot] Skills sync failed: {e}", exc_info=True)

        return str(shared_dir)

    def _resolve_session_skill_config(
        self,
        resolved_cwd: str,
        user_id: str,
        enable_openwebui_skills: bool,
        disabled_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        skill_directories: List[str] = []

        # Unified shared directory — always included.
        # When enable_openwebui_skills is True, run bidirectional sync first so
        # OpenWebUI page skills and directory skills are kept in sync.
        if enable_openwebui_skills:
            shared_dir = self._sync_openwebui_skills(resolved_cwd, user_id)
        else:
            shared_dir = self._get_shared_skills_dir(resolved_cwd)
        skill_directories.append(shared_dir)

        config: Dict[str, Any] = {}
        if skill_directories:
            config["skill_directories"] = self._dedupe_preserve_order(skill_directories)

        if disabled_skills:
            normalized_disabled = self._dedupe_preserve_order(disabled_skills)
            if normalized_disabled:
                config["disabled_skills"] = normalized_disabled

        return config

    def _is_code_interpreter_feature_enabled(
        self, body: Optional[dict], __metadata__: Optional[dict] = None
    ) -> bool:
        """Code interpreter must be explicitly enabled by request feature flags."""

        def _extract_flag(container: Any) -> Optional[bool]:
            if not isinstance(container, dict):
                return None
            features = container.get("features")
            if isinstance(features, dict) and "code_interpreter" in features:
                return bool(features.get("code_interpreter"))
            return None

        # 1) top-level body.features
        flag = _extract_flag(body)
        if flag is not None:
            return flag

        # 2) body.metadata.features
        if isinstance(body, dict):
            flag = _extract_flag(body.get("metadata"))
            if flag is not None:
                return flag

        # 3) injected __metadata__.features
        flag = _extract_flag(__metadata__)
        if flag is not None:
            return flag

        return False

    async def _extract_system_prompt(
        self,
        body: dict,
        messages: List[dict],
        request_model: str,
        real_model_id: str,
        code_interpreter_enabled: bool = False,
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

        # Append Code Interpreter Warning only when feature is explicitly enabled
        if code_interpreter_enabled:
            code_interpreter_warning = (
                "\n\n[System Note]\n"
                "The `execute_code` tool (builtin category: `code_interpreter`) executes code in a remote, ephemeral environment. "
                "It cannot access files in your local workspace or persist changes. "
                "Use it only for calculation or logic verification, not for file manipulation."
                "\n"
                "always use relative paths that start with `/api/v1/files/`. "
                "Do not output `api/...` and do not prepend any domain or protocol (e.g., NEVER use `https://same.ai/api/...`)."
            )
            if system_prompt_content:
                system_prompt_content += code_interpreter_warning
            else:
                system_prompt_content = code_interpreter_warning.strip()

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

    def _build_client_config(self, user_id: str = None, chat_id: str = None) -> dict:
        """Build CopilotClient config from valves and request body."""
        cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)
        config_dir = self._get_copilot_config_dir()

        # Set environment variable for SDK/CLI to pick up the new config location
        os.environ["COPILOTSDK_CONFIG_DIR"] = config_dir

        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]
        client_config["cwd"] = cwd
        client_config["config_dir"] = config_dir

        if self.valves.LOG_LEVEL:
            client_config["log_level"] = self.valves.LOG_LEVEL

        if self.valves.LOG_LEVEL:
            client_config["log_level"] = self.valves.LOG_LEVEL

        # Setup persistent CLI tool installation directories
        agent_env = dict(os.environ)
        if os.path.exists("/app/backend/data"):
            tools_dir = "/app/backend/data/.copilot_tools"
            npm_dir = f"{tools_dir}/npm"
            venv_dir = f"{tools_dir}/venv"

            try:
                os.makedirs(f"{npm_dir}/bin", exist_ok=True)

                # Setup Python Virtual Environment to strictly protect system python
                if not os.path.exists(f"{venv_dir}/bin/activate"):
                    import subprocess
                    import sys

                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "venv",
                            "--system-site-packages",
                            venv_dir,
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )

                agent_env["NPM_CONFIG_PREFIX"] = npm_dir
                agent_env["VIRTUAL_ENV"] = venv_dir
                agent_env.pop("PYTHONUSERBASE", None)
                agent_env.pop("PIP_USER", None)

                agent_env["PATH"] = (
                    f"{npm_dir}/bin:{venv_dir}/bin:{agent_env.get('PATH', '')}"
                )
            except Exception as e:
                logger.warning(f"Failed to setup Python venv or tool dirs: {e}")

        if self.valves.CUSTOM_ENV_VARS:
            try:
                custom_env = json.loads(self.valves.CUSTOM_ENV_VARS)
                if isinstance(custom_env, dict):
                    agent_env.update(custom_env)
            except:
                pass

        client_config["env"] = agent_env

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
        enable_openwebui_skills: bool = True,
        disabled_skills: Optional[List[str]] = None,
        chat_tool_ids: Optional[list] = None,
        __event_call__=None,
        manage_skills_intent: bool = False,
    ):
        """Build SessionConfig for Copilot SDK."""
        from copilot.types import SessionConfig, InfiniteSessionConfig
        import time

        try:
            # -time.timezone is offset in seconds. UTC+8 is 28800.
            is_china_tz = (-time.timezone / 3600) == 8.0
        except Exception:
            is_china_tz = False

        if is_china_tz:
            pkg_mirror_hint = " (Note: Server is in UTC+8. You MUST append `-i https://pypi.tuna.tsinghua.edu.cn/simple` for pip/uv and `--registry=https://registry.npmmirror.com` for npm to prevent network timeouts.)"
        else:
            pkg_mirror_hint = " (Note: If network is slow or times out, proactively use a fast regional mirror suitable for the current timezone.)"

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

        if manage_skills_intent:
            system_parts.append(
                "[Skill Management]\n"
                "If the user wants to install, create, delete, edit, or list skills, use the `manage_skills` tool.\n"
                "Supported operations: list, install, create, edit, delete, show.\n"
                "When installing skills that require CLI tools, you MAY run installation commands.\n"
                f"To avoid hanging the session, ALWAYS append `-q` or `--silent` to package managers, and confirm unattended installations (e.g., `npm install -g -q <pkg>` or `pip install -q <pkg>`).{pkg_mirror_hint}\n"
                "When running `npm install -g`, it will automatically use prefix `/app/backend/data/.copilot_tools/npm`. No need to set the prefix manually, but you MUST be aware this is the installation target.\n"
                "When running `pip install`, it operates within an isolated Python Virtual Environment (`VIRTUAL_ENV=/app/backend/data/.copilot_tools/venv`) that has access to system packages (`--system-site-packages`). This protects the system Python while allowing you to use pre-installed generic libraries. DO NOT attempt to bypass this isolation."
            )

        # Calculate final path once to ensure consistency
        resolved_cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)

        # Inject explicit path context
        config_dir = self._get_copilot_config_dir()
        path_context = (
            f"\n[Session Context]\n"
            f"- **Your Isolated Workspace**: `{resolved_cwd}`\n"
            f"- **Active User ID**: `{user_id}`\n"
            f"- **Active Chat ID**: `{chat_id}`\n"
            f"- **Skills Directory**: `{self.valves.OPENWEBUI_SKILLS_SHARED_DIR}/shared/` — contains user-installed skills.\n"
            f"- **Config Directory**: `{config_dir}` — system configuration (Restricted).\n"
            f"- **CLI Tools Path**: `/app/backend/data/.copilot_tools/` — Global tools installed via npm or pip will automatically go here and be in your $PATH. Python tools are strictly isolated in a venv here.\n"
            "**CRITICAL INSTRUCTION**: You MUST use the above workspace for ALL file operations.\n"
            "- DO NOT create files in `/tmp` or any other system directories.\n"
            "- Always interpret 'current directory' as your Isolated Workspace."
        )
        system_parts.append(path_context)

        # Available Native Tools Context
        native_tools_context = (
            "\n[Available Native System Tools]\n"
            "The host environment is rich. Based on the official OpenWebUI Docker deployment baseline (backend image), the following CLI tools are expected to be preinstalled and globally available in $PATH:\n"
            "- **Network/Data**: `curl`, `jq`, `netcat-openbsd`\n"
            "- **Media/Doc**: `pandoc` (format conversion), `ffmpeg` (audio/video)\n"
            "- **Build/System**: `git`, `gcc`, `make`, `build-essential`, `zstd`, `bash`\n"
            "- **Python/Runtime**: `python3`, `pip3`, `uv`\n"
            f"- **Package Mgr Guidance**: Prefer `uv pip install <pkg>` over plain `pip install` for speed and stability.{pkg_mirror_hint}\n"
            "- **Verification Rule**: Before installing any CLI/tool dependency, first check availability with `which <tool>` or a lightweight version probe (e.g. `<tool> --version`).\n"
            "- **Python Libs**: The active virtual environment inherits `--system-site-packages`. Advanced libraries like `pandas`, `numpy`, `pillow`, `opencv-python-headless`, `pypdf`, `langchain`, `playwright`, `httpx`, and `beautifulsoup4` are ALREADY installed. Try importing them before attempting to install.\n"
        )
        system_parts.append(native_tools_context)

        system_parts.append(BASE_GUIDELINES)

        # Dynamic Capability Note: Rich UI (HTML Emitters/Iframes) requires OpenWebUI >= 0.8.0
        if not self._is_version_at_least("0.8.0"):
            version_note = (
                f"\n**[CRITICAL VERSION NOTE]**\n"
                f"The host OpenWebUI version is `{open_webui_version}`, which is older than 0.8.0.\n"
                "- **Rich UI Disabled**: Integration features like `type: embeds` or automated iframe overlays are NOT supported.\n"
                "- **Protocol Fallback**: You MUST NOT rely on the 'Premium Delivery Protocol' for visuals. Instead, you SHOULD output the HTML code block manually in your message if you want the user to see the result."
            )
            system_parts.append(version_note)

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
            __event_call__, enable_mcp=enable_mcp, chat_tool_ids=chat_tool_ids
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

        # Always set available_tools=None so the Copilot CLI's built-in tools
        # (e.g. bash, create_file) remain accessible alongside our custom tools.
        # Custom tools are registered via the 'tools' param; whitelist filtering
        # via available_tools would silently block CLI built-ins.
        session_params["available_tools"] = None

        if provider_config:
            session_params["provider"] = provider_config

        # Inject hooks for automatic large file handling
        session_params["hooks"] = self._build_session_hooks(
            cwd=resolved_cwd, __event_call__=__event_call__
        )

        session_params.update(
            self._resolve_session_skill_config(
                resolved_cwd=resolved_cwd,
                user_id=user_id,
                enable_openwebui_skills=enable_openwebui_skills,
                disabled_skills=disabled_skills,
            )
        )

        try:
            skill_dirs_dbg = session_params.get("skill_directories") or []
            if skill_dirs_dbg:
                logger.info(f"[Copilot] skill_directories={skill_dirs_dbg}")
                for sd in skill_dirs_dbg:
                    path = Path(sd)
                    skill_md_count = sum(
                        1 for p in path.glob("*/SKILL.md") if p.is_file()
                    )
                    logger.info(
                        f"[Copilot] skill_dir check: {sd} exists={path.exists()} skill_md_count={skill_md_count}"
                    )
        except Exception as e:
            logger.debug(f"[Copilot] skill directory debug check failed: {e}")

        return SessionConfig(**session_params)

    def _build_session_hooks(self, cwd: str, __event_call__=None):
        """
        Build session lifecycle hooks.
        Currently implements:
        - on_post_tool_use: Auto-copy large files from /tmp to workspace
        """

        async def on_post_tool_use(input_data, invocation):
            result = input_data.get("result", "")

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

    async def _fetch_byok_models(self, uv: "Pipe.UserValves" = None) -> List[dict]:
        """Fetch BYOK models from configured provider."""
        model_list = []

        # Resolve effective settings (User > Global)
        # Note: We handle the case where uv might be None
        effective_base_url = (
            uv.BYOK_BASE_URL if uv else ""
        ) or self.valves.BYOK_BASE_URL
        effective_type = (uv.BYOK_TYPE if uv else "") or self.valves.BYOK_TYPE
        effective_api_key = (uv.BYOK_API_KEY if uv else "") or self.valves.BYOK_API_KEY
        effective_bearer_token = (
            uv.BYOK_BEARER_TOKEN if uv else ""
        ) or self.valves.BYOK_BEARER_TOKEN
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
                        headers["Authorization"] = f"Bearer {effective_bearer_token}"
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
                                        f"BYOK: Fetched {len(model_list)} models from {url}"
                                    )
                                    break
                                else:
                                    await self._emit_debug_log(
                                        f"BYOK: Failed to fetch models from {url} (Attempt {attempt+1}/3). Status: {resp.status}"
                                    )
                        except Exception as e:
                            await self._emit_debug_log(
                                f"BYOK: Model fetch error (Attempt {attempt+1}/3): {e}"
                            )

                        if attempt < 2:
                            await asyncio.sleep(1)
            except Exception as e:
                await self._emit_debug_log(f"BYOK: Setup error: {e}")

        # Fallback to configured list or defaults
        if not model_list:
            if effective_models.strip():
                model_list = [
                    m.strip() for m in effective_models.split(",") if m.strip()
                ]
                await self._emit_debug_log(
                    f"BYOK: Using user-configured BYOK_MODELS ({len(model_list)} models)."
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

        # --- NEW: CONFIG-AWARE CACHE INVALIDATION ---
        # Calculate current config fingerprint to detect changes
        current_config_str = f"{token}|{uv.BYOK_BASE_URL or self.valves.BYOK_BASE_URL}|{uv.BYOK_API_KEY or self.valves.BYOK_API_KEY}|{self.valves.BYOK_BEARER_TOKEN}"
        current_config_hash = hashlib.md5(current_config_str.encode()).hexdigest()

        # TTL-based cache expiry
        cache_ttl = self.valves.MODEL_CACHE_TTL
        if (
            self._model_cache
            and cache_ttl > 0
            and (now - self.__class__._last_model_cache_time) > cache_ttl
        ):
            if self.valves.DEBUG:
                logger.info(
                    f"[Pipes] Model cache expired (TTL={cache_ttl}s). Invalidating."
                )
            self.__class__._model_cache = []

        if (
            self._model_cache
            and self.__class__._last_byok_config_hash != current_config_hash
        ):
            if self.valves.DEBUG:
                logger.info(
                    f"[Pipes] Configuration change detected. Invalidating model cache."
                )
            self.__class__._model_cache = []
            self.__class__._last_byok_config_hash = current_config_hash

        if not self._model_cache:
            # Update the hash when we refresh the cache
            self.__class__._last_byok_config_hash = current_config_hash
            if self.valves.DEBUG:
                logger.info("[Pipes] Refreshing model cache...")
            try:
                # Use effective token for fetching.
                # If COPILOT_CLI_PATH is missing (e.g. env cleared after worker restart),
                # force a full re-discovery by resetting _env_setup_done first.
                if not os.environ.get("COPILOT_CLI_PATH"):
                    self.__class__._env_setup_done = False
                self._setup_env(token=token)

                # Fetch BYOK models if configured
                byok = []
                effective_base_url = uv.BYOK_BASE_URL or self.valves.BYOK_BASE_URL
                if effective_base_url and (
                    uv.BYOK_API_KEY
                    or self.valves.BYOK_API_KEY
                    or uv.BYOK_BEARER_TOKEN
                    or self.valves.BYOK_BEARER_TOKEN
                ):
                    byok = await self._fetch_byok_models(uv=uv)

                standard = []
                cli_path = os.environ.get("COPILOT_CLI_PATH", "")
                cli_ready = bool(cli_path and os.path.exists(cli_path))
                if token and cli_ready:
                    client_config = {
                        "cli_path": cli_path,
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
                elif token and self.valves.DEBUG:
                    logger.info(
                        "[Pipes] Copilot CLI not ready during listing. Skip standard model probe to avoid blocking startup."
                    )

                self._model_cache = standard + byok
                self.__class__._last_model_cache_time = now
                if not self._model_cache:
                    has_byok = bool(
                        (uv.BYOK_BASE_URL or self.valves.BYOK_BASE_URL)
                        and (
                            uv.BYOK_API_KEY
                            or self.valves.BYOK_API_KEY
                            or uv.BYOK_BEARER_TOKEN
                            or self.valves.BYOK_BEARER_TOKEN
                        )
                    )
                    if not token and not has_byok:
                        return [
                            {
                                "id": "no_token",
                                "name": "⚠️ No credentials configured. Please set GH_TOKEN or BYOK settings in Valves.",
                            }
                        ]
                    return [
                        {
                            "id": "warming_up",
                            "name": "Copilot CLI is preparing in background. Please retry in a moment.",
                        }
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
    ):
        """Setup environment variables and resolve Copilot CLI path from SDK bundle."""

        # 1. Real-time Token Injection (Always updates on each call)
        effective_token = token or self.valves.GH_TOKEN
        if effective_token:
            os.environ["GH_TOKEN"] = os.environ["GITHUB_TOKEN"] = effective_token

        if self._env_setup_done:
            if debug_enabled:
                self._sync_mcp_config(
                    __event_call__,
                    debug_enabled,
                    enable_mcp=enable_mcp,
                )
            return

        os.environ["COPILOT_AUTO_UPDATE"] = "false"

        # 2. CLI Path Discovery (priority: env var > PATH > SDK bundle)
        cli_path = os.environ.get("COPILOT_CLI_PATH", "")
        found = bool(cli_path and os.path.exists(cli_path))

        if not found:
            sys_path = shutil.which("copilot")
            if sys_path:
                cli_path = sys_path
                found = True

        if not found:
            try:
                from copilot.client import _get_bundled_cli_path

                bundled_path = _get_bundled_cli_path()
                if bundled_path and os.path.exists(bundled_path):
                    cli_path = bundled_path
                    found = True
            except ImportError:
                pass

        # 3. Finalize
        cli_ready = found
        if cli_ready:
            os.environ["COPILOT_CLI_PATH"] = cli_path
            # Add the CLI's parent directory to PATH so subprocesses can invoke `copilot` directly
            cli_bin_dir = os.path.dirname(cli_path)
            current_path = os.environ.get("PATH", "")
            if cli_bin_dir and cli_bin_dir not in current_path.split(os.pathsep):
                os.environ["PATH"] = cli_bin_dir + os.pathsep + current_path

        self.__class__._env_setup_done = cli_ready
        self.__class__._last_update_check = datetime.now().timestamp()

        self._emit_debug_log_sync(
            f"Environment setup complete. CLI ready={cli_ready}. Path: {cli_path}",
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
        Dynamically update config.json if REASONING_EFFORT is set.
        This provides a fallback if API injection is ignored by the server.
        """
        if not reasoning_effort:
            return

        effort = reasoning_effort

        try:
            # Target dynamic config path
            config_path = os.path.join(self._get_copilot_config_dir(), "config.json")
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
                        f"Dynamically updated config.json: reasoning_effort='{effort}'",
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
    ):
        """Sync MCP configuration to dynamic config.json."""
        path = os.path.join(self._get_copilot_config_dir(), "config.json")

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

        mcp = self._parse_mcp_servers(__event_call__, enable_mcp=enable_mcp)
        if not mcp:
            return
        try:
            path = os.path.join(self._get_copilot_config_dir(), "config.json")
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
        __request__=None,
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

        # Determine effective MCP settings
        effective_mcp = user_valves.ENABLE_MCP_SERVER
        effective_openwebui_skills = user_valves.ENABLE_OPENWEBUI_SKILLS
        effective_disabled_skills = self._parse_csv_items(
            user_valves.DISABLED_SKILLS or self.valves.DISABLED_SKILLS
        )

        # P4: Chat tool_ids whitelist — extract once, reuse for both OpenAPI and MCP
        chat_tool_ids = None
        if __metadata__ and isinstance(__metadata__, dict):
            chat_tool_ids = __metadata__.get("tool_ids") or None

        user_ctx = await self._get_user_context(__user__, __event_call__, __request__)
        user_lang = user_ctx["user_language"]

        # 2. Setup environment with effective settings
        self._setup_env(
            __event_call__,
            debug_enabled=effective_debug,
            token=effective_token,
            enable_mcp=effective_mcp,
        )

        cwd = self._get_workspace_dir(user_id=user_id, chat_id=chat_id)
        await self._emit_debug_log(
            f"{self._get_translation(user_lang, 'debug_agent_working_in', path=cwd)} (Admin: {is_admin}, MCP: {effective_mcp})",
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
        code_interpreter_enabled = self._is_code_interpreter_feature_enabled(
            body, __metadata__
        )

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
            code_interpreter_enabled=code_interpreter_enabled,
            __event_call__=__event_call__,
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

        # Skill-manager intent diagnostics/routing hint (without disabling other skills).
        manage_skills_intent = self._is_manage_skills_intent(last_text)
        if manage_skills_intent:
            try:
                await self._emit_debug_log(
                    "[Skills] Skill management intent detected. `manage_skills` tool routing enabled.",
                    __event_call__,
                    debug_enabled=effective_debug,
                )
            except Exception as e:
                await self._emit_debug_log(
                    f"[Skills] Skill-manager intent diagnostics failed: {e}",
                    __event_call__,
                    debug_enabled=effective_debug,
                )

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

        # Shared state for delayed HTML embeds (Premium Experience)
        pending_embeds = []

        # Initialize Client
        client = CopilotClient(
            self._build_client_config(user_id=user_id, chat_id=chat_id)
        )
        should_stop_client = True
        try:
            await client.start()

            # Initialize custom tools (Handles caching internally)
            custom_tools = await self._initialize_custom_tools(
                body=body,
                __user__=__user__,
                __event_emitter__=__event_emitter__,
                __event_call__=__event_call__,
                __request__=__request__,
                __metadata__=__metadata__,
                pending_embeds=pending_embeds,
            )
            if custom_tools:
                await self._emit_debug_log(
                    f"Enabled {len(custom_tools)} tools (Custom/Built-in)",
                    __event_call__,
                )

            # Check MCP Servers
            mcp_servers = self._parse_mcp_servers(
                __event_call__, enable_mcp=effective_mcp, chat_tool_ids=chat_tool_ids
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
                    resolved_cwd = self._get_workspace_dir(
                        user_id=user_id, chat_id=chat_id
                    )
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
                        chat_tool_ids=chat_tool_ids,
                    )
                    if mcp_servers:
                        resume_params["mcp_servers"] = mcp_servers

                    # Always None: let CLI built-ins (bash etc.) remain available.
                    resume_params["available_tools"] = None

                    resume_params.update(
                        self._resolve_session_skill_config(
                            resolved_cwd=resolved_cwd,
                            user_id=user_id,
                            enable_openwebui_skills=effective_openwebui_skills,
                            disabled_skills=effective_disabled_skills,
                        )
                    )
                    try:
                        skill_dirs_dbg = resume_params.get("skill_directories") or []
                        if skill_dirs_dbg:
                            logger.info(
                                f"[Copilot] resume skill_directories={skill_dirs_dbg}"
                            )
                            for sd in skill_dirs_dbg:
                                path = Path(sd)
                                skill_md_count = sum(
                                    1 for p in path.glob("*/SKILL.md") if p.is_file()
                                )
                                logger.info(
                                    f"[Copilot] resume skill_dir check: {sd} exists={path.exists()} skill_md_count={skill_md_count}"
                                )
                    except Exception as e:
                        logger.debug(
                            f"[Copilot] resume skill directory debug check failed: {e}"
                        )

                    # Always inject the latest system prompt in 'replace' mode
                    # This handles both custom models and user-defined system messages
                    system_parts = []
                    if system_prompt_content:
                        system_parts.append(system_prompt_content.strip())

                    if manage_skills_intent:
                        system_parts.append(
                            "[Skill Routing Hint]\n"
                            "The user is asking to install/manage skills. Use the `manage_skills` tool first for deterministic operations "
                            "(list/install/create/edit/delete/show). Do not run skill names as shell commands."
                        )

                    # Calculate and inject path context for resumed session
                    path_context = (
                        f"\n[Session Context]\n"
                        f"- **Your Isolated Workspace**: `{resolved_cwd}`\n"
                        f"- **Active User ID**: `{user_id}`\n"
                        f"- **Active Chat ID**: `{chat_id}`\n"
                        f"- **Skills Directory**: `{self.valves.OPENWEBUI_SKILLS_SHARED_DIR}/shared/` — contains user skills (`SKILL.md`-based). For management operations, use the `manage_skills` tool.\n"
                        "**CRITICAL INSTRUCTION**: You MUST use the above workspace for ALL file operations.\n"
                        "- DO NOT create files in `/tmp` or any other system directories.\n"
                        "- Use the `manage_skills` tool for skill install/list/create/edit/delete/show operations.\n"
                        "- If a tool output is too large, save it to a file within your workspace, NOT `/tmp`.\n"
                        "- Always interpret 'current directory' as your Isolated Workspace."
                    )
                    system_parts.append(path_context)

                    system_parts.append(BASE_GUIDELINES)

                    # Dynamic Capability Note: Rich UI (HTML Emitters/Iframes) requires OpenWebUI >= 0.8.0
                    if not self._is_version_at_least("0.8.0"):
                        version_note = (
                            f"\n**[CRITICAL VERSION NOTE]**\n"
                            f"The host OpenWebUI version is `{open_webui_version}`, which is older than 0.8.0.\n"
                            "- **Rich UI Disabled**: Integration features like `type: embeds` or automated iframe overlays are NOT supported.\n"
                            "- **Protocol Fallback**: You MUST NOT rely on the 'Premium Delivery Protocol' for visuals. Instead, you SHOULD output the HTML code block manually in your message if you want the user to see the result."
                        )
                        system_parts.append(version_note)

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
                except Exception as e:
                    await self._emit_debug_log(
                        f"Session {chat_id} not found or failed to resume ({str(e)}), creating new.",
                        __event_call__,
                    )

            if session is None:
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
                    enable_openwebui_skills=effective_openwebui_skills,
                    disabled_skills=effective_disabled_skills,
                    manage_skills_intent=manage_skills_intent,
                    chat_tool_ids=chat_tool_ids,
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
                    init_msg = f"> [Debug] {self._get_translation(user_lang, 'debug_agent_working_in', path=self._get_workspace_dir(user_id=user_id, chat_id=chat_id))}\n"
                    if mcp_server_names:
                        init_msg += f"> [Debug] {self._get_translation(user_lang, 'debug_mcp_servers', servers=', '.join(mcp_server_names))}\n"

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
                    reasoning_effort=(
                        effective_reasoning_effort
                        if (is_reasoning and not is_byok_model)
                        else "off"
                    ),
                    show_thinking=show_thinking,
                    debug_enabled=effective_debug,
                    user_lang=user_lang,
                    pending_embeds=pending_embeds,
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
        user_lang: str = "en-US",
        pending_embeds: List[dict] = None,
    ) -> AsyncGenerator:
        """
        Stream response from Copilot SDK, handling various event types.
        Follows official SDK patterns for event handling and streaming.
        """
        queue = asyncio.Queue()
        done = asyncio.Event()
        SENTINEL = object()
        # Use local state to handle concurrency and tracking
        state = {
            "thinking_started": False,
            "content_sent": False,
            "last_status_desc": None,
            "idle_reached": False,
            "session_finalized": False,
        }
        has_content = False  # Track if any content has been yielded
        active_tools = {}  # Map tool_call_id to tool_name
        skill_invoked_in_turn = False
        stream_start_ts = time.monotonic()
        last_wait_status_ts = 0.0
        wait_status_interval = 15.0

        IDLE_SENTINEL = object()
        ERROR_SENTINEL = object()
        SENTINEL = object()

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

            # --- Status Emission Helper ---
            async def _emit_status_helper(description: str, is_done: bool = False):
                if not __event_emitter__:
                    return
                try:
                    # BLOCKING LOCK: If we are in the safe-haven of turn completion,
                    # discard any stray async status updates from earlier pending tasks.
                    if state.get(
                        "session_finalized"
                    ) and description != self._get_translation(
                        user_lang, "status_task_completed"
                    ):
                        return

                    # Optimized emission: we try to minimize context switches

                    # 1. Close the OLD one if it's different
                    if (
                        state.get("last_status_desc")
                        and state["last_status_desc"] != description
                    ):
                        try:
                            await __event_emitter__(
                                {
                                    "type": "status",
                                    "data": {
                                        "description": state["last_status_desc"],
                                        "done": True,
                                    },
                                }
                            )
                        except:
                            pass

                    # CRITICAL: Re-check session_finalized after the inner await above.
                    # The coroutine may have been suspended at await point #1 while the
                    # main loop set session_finalized=True and emitted the final done=True.
                    # Without this re-check, the done=False emission below would fire
                    # AFTER all finalization, becoming the last statusHistory entry
                    # and leaving a permanent shimmer on the UI.
                    if state.get(
                        "session_finalized"
                    ) and description != self._get_translation(
                        user_lang, "status_task_completed"
                    ):
                        return

                    # 2. Emit the requested status
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": description, "done": is_done},
                        }
                    )

                    # 3. Track the active status
                    if not is_done:
                        state["last_status_desc"] = description
                    elif state.get("last_status_desc") == description:
                        state["last_status_desc"] = None
                except:
                    pass

            def emit_status(desc: str, is_done: bool = False):
                """Sync wrapper to schedule the async status emission."""
                if __event_emitter__ and desc:
                    # We use a task because this is often called from sync tool handlers
                    asyncio.create_task(_emit_status_helper(desc, is_done))

            # === Turn Management Events ===
            if event_type == "assistant.turn_start":
                self._emit_debug_log_sync(
                    "Assistant Turn Started",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

                initial_status = self._get_translation(
                    user_lang, "status_assistant_processing"
                )
                # Route through emit_status → _emit_status_helper so the session_finalized
                # guard is respected. Direct create_task(__event_emitter__) bypasses the guard
                # and can fire AFTER finalization, leaving a stale done=False spinner.
                emit_status(initial_status)

            elif event_type == "assistant.intent":
                intent = safe_get_data_attr(event, "intent")
                if intent:
                    self._emit_debug_log_sync(
                        f"Assistant Intent: {intent}",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
                    emit_status(f"{intent}...")

            # === Message Delta Events (Primary streaming content) ===
            elif event_type == "assistant.message_delta":
                # Close any pending thinking status when content starts
                if not state["content_sent"]:
                    state["content_sent"] = True
                    if state.get("last_status_desc"):
                        emit_status(state["last_status_desc"], is_done=True)

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
                    # Close current status
                    if state.get("last_status_desc"):
                        emit_status(state["last_status_desc"], is_done=True)

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

            # === Skill Invocation Events ===
            elif event_type == "skill.invoked":
                nonlocal skill_invoked_in_turn
                skill_invoked_in_turn = True
                skill_name = (
                    safe_get_data_attr(event, "name")
                    or safe_get_data_attr(event, "skill_name")
                    or safe_get_data_attr(event, "skill")
                    or safe_get_data_attr(event, "id")
                    or "unknown-skill"
                )
                skill_status_text = self._get_translation(
                    user_lang, "status_skill_invoked", skill=skill_name
                )

                self._emit_debug_log_sync(
                    f"Skill Invoked: {skill_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

                # Make invocation visible in chat stream to avoid "skills loaded but feels unknown" confusion.
                queue.put_nowait(f"\n> 🧩 **{skill_status_text}**\n")

                # Also send status bubble when possible.
                emit_status(skill_status_text, is_done=True)

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

                # Try to detect filename in arguments for better status (e.g., create_file, bash)
                tool_status_text = self._get_translation(
                    user_lang,
                    "status_tool_using",
                    name=tool_name,
                )

                # Enhanced filenames detection for common tools
                filename_hint = (
                    tool_args.get("filename")
                    or tool_args.get("file")
                    or tool_args.get("path")
                )
                if not filename_hint and tool_name == "bash":
                    command = tool_args.get("command", "")
                    # Detect output file from common bash redirect patterns (>>, >, tee, cat >)
                    # Use alternation group (not char class) to avoid matching '|' pipe symbols
                    match = re.search(r"(?:>>|>|tee|cat\s*>)\s*([^\s;&|<>]+)", command)
                    if match:
                        candidate = match.group(1).strip().split("/")[-1]
                        # Only use as hint if it looks like a filename (has extension or is not a flag)
                        if (
                            candidate
                            and not candidate.startswith("-")
                            and "." in candidate
                        ):
                            filename_hint = candidate

                if filename_hint:
                    tool_status_text += f" ({filename_hint})"

                if tool_call_id:
                    active_tools[tool_call_id] = {
                        "name": tool_name,
                        "arguments": tool_args,
                        "status_text": tool_status_text if __event_emitter__ else None,
                    }

                # Close thinking tag if open before showing tool
                if state["thinking_started"]:
                    queue.put_nowait("\n</think>\n")
                    state["thinking_started"] = False

                # Show status bubble for tool usage
                emit_status(tool_status_text)

                self._emit_debug_log_sync(
                    f"Tool Start: {tool_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

            elif event_type == "tool.execution_complete":
                tool_call_id = safe_get_data_attr(event, "tool_call_id", "")
                tool_info = active_tools.get(tool_call_id)

                tool_name = "tool"
                status_text = None
                if isinstance(tool_info, dict):
                    tool_name = tool_info.get("name", "tool")
                    status_text = tool_info.get("status_text")
                elif isinstance(tool_info, str):
                    tool_name = tool_info

                # Mark tool status as done if it was the last one
                if status_text:
                    emit_status(status_text, is_done=True)

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
                    elif isinstance(result_obj, str):
                        result_content = result_obj
                    result_type = (
                        safe_get_data_attr(event, "type", "success") or "success"
                    )
                except Exception as e:
                    self._emit_debug_log_sync(
                        f"Error extracting result: {e}",
                        __event_call__,
                        debug_enabled=debug_enabled,
                    )
                    result_type = "failure"
                    result_content = f"Error: {str(e)}"

                # User-friendly completion status (success/failure) after the tool finishes.
                # We emit this as done=True so it cleanly replaces transient "Using tool..." states.
                if str(result_type).lower() in {"success", "ok", "completed"}:
                    emit_status(
                        self._get_translation(
                            user_lang, "status_tool_done", name=tool_name
                        ),
                        is_done=True,
                    )
                else:
                    emit_status(
                        self._get_translation(
                            user_lang, "status_tool_failed", name=tool_name
                        ),
                        is_done=True,
                    )

                # Display tool result with improved formatting
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
                        elif isinstance(result_obj, dict) and result_obj.get("content"):
                            todo_text = result_obj["content"]
                        elif hasattr(result_obj, "content"):
                            todo_text = result_obj.content

                        # 3. Fallback: If content is just a status message, try to recover from arguments
                        if (
                            not todo_text or len(todo_text) < 50
                        ):  # Threshold to detect "TODO list updated"
                            if tool_call_id in active_tools:
                                args = active_tools[tool_call_id].get("arguments", {})
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

                # --- Build native OpenWebUI 0.8.3 tool_calls block ---
                # Serialize input args (from execution_start)
                tool_args_for_block = {}
                if tool_call_id and tool_call_id in active_tools:
                    tool_args_for_block = active_tools[tool_call_id].get(
                        "arguments", {}
                    )
                    tool_name = active_tools[tool_call_id].get("name", tool_name)

                try:
                    args_json_str = json.dumps(tool_args_for_block, ensure_ascii=False)
                except Exception:
                    args_json_str = "{}"

                def escape_html_attr(s: str) -> str:
                    if not isinstance(s, str):
                        return ""
                    return (
                        str(s)
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace('"', "&quot;")
                        .replace("\n", "&#10;")
                        .replace("\r", "&#13;")
                    )

                # MUST escape both arguments and result with &quot; and &#10; to satisfy OpenWebUI's strict regex /="([^"]*)"/
                args_for_attr = (
                    escape_html_attr(args_json_str) if args_json_str else "{}"
                )
                # Use "Success" if result_content is empty to ensure card renders
                result_for_attr = escape_html_attr(result_content or "Success")

                # Emit the unified native tool_calls block:
                # OpenWebUI 0.8.3 frontend regex explicitly expects: name="xxx" arguments="..." result="..." done="true"
                tool_block = (
                    f'\n<details type="tool_calls"'
                    f' id="{tool_call_id}"'
                    f' name="{tool_name}"'
                    f' arguments="{args_for_attr}"'
                    f' result="{result_for_attr}"'
                    f' done="true">\n'
                    f"<summary>Tool Executed</summary>\n"
                    f"</details>\n\n"
                )
                state["content_sent"] = True
                queue.put_nowait(tool_block)

                self._emit_debug_log_sync(
                    f"Tool Complete: {tool_name} - {result_type}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

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

                status_text = self._get_translation(
                    user_lang,
                    "status_tool_progress",
                    name=tool_name,
                    progress=progress,
                    msg=message,
                )

                # Route through emit_status to respect session_finalized guard
                emit_status(status_text)

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

            # === Sub-agent Events ===
            elif event_type == "subagent.started":
                agent_name = safe_get_data_attr(event, "name") or "Agent"
                self._emit_debug_log_sync(
                    f"Sub-agent Started: {agent_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                emit_status(
                    self._get_translation(
                        user_lang, "status_subagent_start", name=agent_name
                    )
                )

            elif event_type == "subagent.completed":
                agent_name = safe_get_data_attr(event, "name") or "Agent"
                self._emit_debug_log_sync(
                    f"Sub-agent Completed: {agent_name}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                emit_status(
                    self._get_translation(
                        user_lang, "status_subagent_start", name=agent_name
                    ),
                    is_done=True,
                )

            elif event_type == "subagent.failed":
                agent_name = safe_get_data_attr(event, "name") or "Agent"
                error = safe_get_data_attr(event, "error") or "Unknown error"
                self._emit_debug_log_sync(
                    f"Sub-agent Failed: {agent_name} - {error}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                emit_status(
                    self._get_translation(
                        user_lang, "status_subagent_start", name=agent_name
                    ),
                    is_done=True,
                )
                self._emit_debug_log_sync(
                    f"Sub-agent Failed: {agent_name} - {error}",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )

            elif event_type == "assistant.turn_end":
                self._emit_debug_log_sync(
                    "Assistant Turn Ended",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                if state.get("last_status_desc"):
                    emit_status(state["last_status_desc"], is_done=True)

                # Send the clean Task Completed status
                emit_status(
                    self._get_translation(user_lang, "status_task_completed"),
                    is_done=True,
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

            elif event_type == "session.compaction_start":
                self._emit_debug_log_sync(
                    "Session Compaction Started",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                emit_status(self._get_translation(user_lang, "status_compaction_start"))

            elif event_type == "session.compaction_complete":
                self._emit_debug_log_sync(
                    "Session Compaction Completed",
                    __event_call__,
                    debug_enabled=debug_enabled,
                )
                emit_status(
                    self._get_translation(user_lang, "status_compaction_complete"),
                    is_done=True,
                )

            elif event_type == "session.idle":
                # Session finished processing - signal to the generator loop to finalize
                state["idle_reached"] = True
                try:
                    queue.put_nowait(IDLE_SENTINEL)
                except:
                    pass

            elif event_type == "session.error":
                error_msg = safe_get_data_attr(event, "message", "Unknown Error")
                emit_status(
                    self._get_translation(
                        user_lang, "status_session_error", error=error_msg
                    ),
                    is_done=True,
                )
                queue.put_nowait(f"\n[Error: {error_msg}]")
                try:
                    queue.put_nowait(ERROR_SENTINEL)
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
            if debug_enabled and __event_emitter__:
                # Emit debug info as UI status rather than reasoning block
                async def _emit_status(key: str, desc: str = None, **kwargs):
                    try:
                        final_desc = (
                            desc
                            if desc
                            else self._get_translation(user_lang, key, **kwargs)
                        )
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {"description": final_desc, "done": True},
                            }
                        )
                    except:
                        pass

                if init_message:
                    for line in init_message.split("\n"):
                        if line.strip():
                            clean_msg = line.replace("> [Debug] ", "").strip()
                            asyncio.create_task(_emit_status("custom", desc=clean_msg))

                if reasoning_effort and reasoning_effort != "off":
                    asyncio.create_task(
                        _emit_status(
                            "status_reasoning_inj", effort=reasoning_effort.upper()
                        )
                    )

                asyncio.create_task(_emit_status("status_conn_est"))
        except Exception as e:
            # If initial yield fails, log but continue processing
            self._emit_debug_log_sync(
                f"Initial status warning: {e}",
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
                        done.set()
                        break

                    if chunk is IDLE_SENTINEL:
                        # --- [FINAL STEP] Emit Rich UI Integrated View & Task Completion ---
                        if __event_emitter__:
                            try:
                                # 1b. Clear any tracked last tool/intent status
                                if state.get("last_status_desc"):
                                    await __event_emitter__(
                                        {
                                            "type": "status",
                                            "data": {
                                                "description": state[
                                                    "last_status_desc"
                                                ],
                                                "done": True,
                                            },
                                        }
                                    )
                                    state["last_status_desc"] = None

                                # 1c. CRITICAL: Close all tool statuses and REWRITE their description
                                # In some versions of OpenWebUI, just marking as done doesn't update the summary.
                                # We explicitly change the text to 'Completed' to force UI refresh.
                                for _tool_id, _tool_info in active_tools.items():
                                    if isinstance(_tool_info, dict) and _tool_info.get(
                                        "status_text"
                                    ):
                                        try:
                                            # Append a checkmark to the tool status to force a string change
                                            final_tool_status = f"✅ {_tool_info['status_text'].replace('...', '')}"
                                            await __event_emitter__(
                                                {
                                                    "type": "status",
                                                    "data": {
                                                        "description": final_tool_status,
                                                        "done": True,
                                                    },
                                                }
                                            )
                                        except Exception:
                                            pass

                                # 2. Emit Rich UI components (richui type)
                                if pending_embeds:
                                    for embed in pending_embeds:
                                        if embed.get("type") == "richui":
                                            # Status update
                                            await __event_emitter__(
                                                {
                                                    "type": "status",
                                                    "data": {
                                                        "description": self._get_translation(
                                                            user_lang,
                                                            "status_publishing_file",
                                                            filename=embed["filename"],
                                                        ),
                                                        "done": True,
                                                    },
                                                }
                                            )
                                            # Success notification
                                            await __event_emitter__(
                                                {
                                                    "type": "notification",
                                                    "data": {
                                                        "type": "success",
                                                        "content": self._get_translation(
                                                            user_lang, "publish_success"
                                                        ),
                                                    },
                                                }
                                            )
                                            # Standard OpenWebUI Embed Structure: type: "embeds", data: {"embeds": [content]}
                                            await __event_emitter__(
                                                {
                                                    "type": "embeds",
                                                    "data": {
                                                        "embeds": [embed["content"]]
                                                    },
                                                }
                                            )

                                # 3. LOCK internal status emission for background tasks
                                # (Stray Task A from tool.execution_complete will now be discarded)
                                state["session_finalized"] = True

                                # 4. [PULSE LOCK] Trigger a UI refresh by pulsing a non-done status
                                # This forces OpenWebUI's summary line to re-evaluate the description.
                                # 4. [PULSE LOCK] Trigger a UI refresh by pulsing a non-done status
                                finalized_msg = "✔️ " + self._get_translation(
                                    user_lang, "status_task_completed"
                                )

                                await __event_emitter__(
                                    {
                                        "type": "status",
                                        "data": {
                                            "description": finalized_msg,
                                            "done": False,
                                        },
                                    }
                                )

                                # Increased window to ensure the 'done: False' is processed before the pipe closes
                                await asyncio.sleep(0.2)

                                # 5. FINAL emit
                                await __event_emitter__(
                                    {
                                        "type": "status",
                                        "data": {
                                            "description": finalized_msg,
                                            "done": True,
                                            "hidden": False,
                                        },
                                    }
                                )
                            except Exception as emit_error:
                                self._emit_debug_log_sync(
                                    f"Final emission error: {emit_error}",
                                    __event_call__,
                                    debug_enabled=debug_enabled,
                                )

                        done.set()
                        break

                    if chunk is ERROR_SENTINEL:
                        # Extract error message if possible or use default
                        if __event_emitter__:
                            try:
                                await __event_emitter__(
                                    {
                                        "type": "status",
                                        "data": {
                                            "description": "Error during processing",
                                            "done": True,
                                        },
                                    }
                                )
                            except:
                                pass
                        done.set()
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

                    now_ts = time.monotonic()
                    if __event_emitter__ and (
                        now_ts - last_wait_status_ts >= wait_status_interval
                    ):
                        elapsed = int(now_ts - stream_start_ts)
                        try:
                            asyncio.create_task(
                                __event_emitter__(
                                    {
                                        "type": "status",
                                        "data": {
                                            "description": self._get_translation(
                                                user_lang,
                                                "status_still_working",
                                                seconds=elapsed,
                                            ),
                                            "done": False,
                                        },
                                    }
                                )
                            )
                        except Exception:
                            pass
                        last_wait_status_ts = now_ts
                    continue

            while not queue.empty():
                chunk = queue.get_nowait()
                if chunk in (SENTINEL, IDLE_SENTINEL, ERROR_SENTINEL):
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
            # Final Status Cleanup: Emergency mark all as done if not already
            if __event_emitter__:
                try:
                    # Clear any specific tool/intent statuses tracked
                    if state.get("last_status_desc"):
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": state["last_status_desc"],
                                    "done": True,
                                },
                            }
                        )

                    # Clear all active tool statuses before final completion status,
                    # so Task completed remains the last visible summary in OpenWebUI.
                    for tool_id, tool_info in active_tools.items():
                        if isinstance(tool_info, dict) and tool_info.get("status_text"):
                            try:
                                await __event_emitter__(
                                    {
                                        "type": "status",
                                        "data": {
                                            "description": tool_info["status_text"],
                                            "done": True,
                                        },
                                    }
                                )
                            except:
                                pass

                    # Final final confirmation to prevent any stuck status bubbles
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": self._get_translation(
                                    user_lang, "status_task_completed"
                                ),
                                "done": True,
                                "hidden": False,
                            },
                        }
                    )
                except:
                    pass

            unsubscribe()
            # Cleanup client and session
            try:
                # We do not destroy session here to allow persistence,
                # but we must stop the client.
                await client.stop()
            except Exception as e:
                pass


# Triggering release after CI fix
