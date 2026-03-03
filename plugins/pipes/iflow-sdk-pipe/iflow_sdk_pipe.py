"""
title: iFlow Official SDK Pipe
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
description: Integrate iFlow SDK. Supports dynamic models, multi-turn conversation, streaming, tool execution, and task planning.
version: 0.1.2
requirements: iflow-cli-sdk==0.1.11
"""

import shutil
import subprocess

import os
import json
import asyncio
import logging
from typing import Optional, Union, AsyncGenerator, List, Any, Dict, Literal
from pydantic import BaseModel, Field

# Setup logger
logger = logging.getLogger(__name__)

# Import iflow SDK modules with safety
IFlowClient = None
IFlowOptions = None
AssistantMessage = None
TaskFinishMessage = None
ToolCallMessage = None
PlanMessage = None
TaskStatusMessage = None
ApprovalMode = None
StopReason = None

try:
    from iflow_sdk import (
        IFlowClient,
        IFlowOptions,
        AssistantMessage,
        TaskFinishMessage,
        ToolCallMessage,
        PlanMessage,
        TaskStatusMessage,
        ApprovalMode,
        StopReason,
    )
except ImportError:
    logger.error(
        "iflow-cli-sdk not found. Please install it with 'pip install iflow-cli-sdk'."
    )

# Base guidelines for all users, adapted for iFlow
BASE_GUIDELINES = (
    "\n\n[Environment & Capabilities Context]\n"
    "You are an AI assistant operating within a high-capability Linux container environment (OpenWebUI) powered by **iFlow CLI**.\n"
    "\n"
    "**System Environment & User Privileges:**\n"
    "- **Output Environment**: You are rendering in the **OpenWebUI Chat Page**. Optimize your output format to leverage Markdown for the best UI experience.\n"
    "- **Root Access**: You are running as **root**. You have **READ access to the entire container file system**. You **MUST ONLY WRITE** to your designated persistent workspace directory.\n"
    "- **STRICT FILE CREATION RULE**: You are **PROHIBITED** from creating or editing files outside of your specific workspace path. Never place files in `/root`, `/tmp`, or `/app`. All operations must use the absolute path provided in your session context.\n"
    "- **iFlow Task Planning**: You possess **Task Planning** capabilities. When faced with complex requests, you SHOULD generate a structured plan. The iFlow SDK will visualize this plan as a task list for the user.\n"
    "- **Tool Execution (ACP)**: You interact with tools via the **Agent Control Protocol (ACP)**. Depending on the `ApprovalMode`, your tool calls may be executed automatically or require user confirmation.\n"
    "- **Rich Python Environment**: You can natively import and use any installed OpenWebUI dependencies.\n"
    "\n"
    "**Formatting & Presentation Directives:**\n"
    "1. **Markdown Excellence**: Leverage headers, tables, and lists to structure your response professionally.\n"
    "2. **Advanced Visualization**: Use **Mermaid** for diagrams and **LaTeX** for math. Always wrap Mermaid in standard ```mermaid blocks.\n"
    "3. **Interactive Artifacts (HTML)**: **Premium Delivery Protocol**: For web applications, you MUST:\n"
    "   - 1. **Persist**: Create the file in the workspace (e.g., `index.html`).\n"
    "   - 2. **Publish**: Call `publish_file_from_workspace(filename='your_file.html')` (via provided tools if available). This triggers the premium embedded experience.\n"
    "   - **CRITICAL**: Never output raw HTML source code directly in the chat. Persist and publish.\n"
    "4. **Media & Files**: ALWAYS embed generated media using `![caption](url)`. Never provide plain text links for images/videos.\n"
    "5. **Dual-Channel Delivery**: Always aim to provide both an instant visual Insight in the chat AND a persistent downloadable file.\n"
    "6. **Active & Autonomous**: Analyze the user's request -> Formulate a plan -> **EXECUTE** the plan immediately. Minimize user friction.\n"
)

# Sensitive extensions only for Administrators
ADMIN_EXTENSIONS = (
    "\n**[ADMINISTRATOR PRIVILEGES - CONFIDENTIAL]**\n"
    "Current user is an **ADMINISTRATOR**. Restricted access is lifted:\n"
    "- **Full OS Interaction**: You can use shell tools to analyze any container process or system configuration.\n"
    "- **Database Access**: You can connect to the **OpenWebUI Database** using credentials in environment variables.\n"
    "- **iFlow CLI Debugging**: You can inspect iFlow configuration and logs for diagnostic purposes.\n"
    "**SECURITY NOTE**: Protect sensitive internal details.\n"
)

# Strict restrictions for regular Users
USER_RESTRICTIONS = (
    "\n**[USER ACCESS RESTRICTIONS - STRICT]**\n"
    "Current user is a **REGULAR USER**. Adhere to boundaries:\n"
    "- **NO Environment Access**: FORBIDDEN from accessing environment variables (e.g., via `env` or `os.environ`).\n"
    "- **NO Database Access**: MUST NOT attempt to connect to OpenWebUI database.\n"
    "- **NO Writing Outside Workspace**: All artifacts MUST be saved strictly inside the isolated workspace path provided.\n"
    "- **Restricted Shell**: Use shell tools ONLY for operations within your isolated workspace. Do NOT explore system secrets.\n"
)


class Pipe:
    class Valves(BaseModel):
        IFLOW_PORT: int = Field(
            default=8090,
            description="Port for iFlow CLI process.",
        )
        IFLOW_URL: str = Field(
            default="ws://localhost:8090/acp",
            description="WebSocket URL for iFlow ACP.",
        )
        AUTO_START: bool = Field(
            default=True,
            description="Whether to automatically start the iFlow process.",
        )
        TIMEOUT: float = Field(
            default=300.0,
            description="Timeout for the message request (seconds).",
        )
        LOG_LEVEL: str = Field(
            default="INFO",
            description="Log level for iFlow SDK (DEBUG, INFO, WARNING, ERROR).",
        )
        CWD: str = Field(
            default="",
            description="CLI operation working directory. Empty for default.",
        )
        APPROVAL_MODE: Literal["DEFAULT", "AUTO_EDIT", "YOLO", "PLAN"] = Field(
            default="YOLO",
            description="Tool execution permission mode.",
        )
        FILE_ACCESS: bool = Field(
            default=False,
            description="Enable file system access (disabled by default for security).",
        )
        AUTO_INSTALL_CLI: bool = Field(
            default=True,
            description="Automatically install iFlow CLI if not found in PATH.",
        )
        IFLOW_BIN_DIR: str = Field(
            default="/app/backend/data/bin",
            description="Fixed path for iFlow CLI binary (recommended for persistence in Docker).",
        )

        # Auth Config
        SELECTED_AUTH_TYPE: Literal["iflow", "openai-compatible"] = Field(
            default="iflow",
            description="Authentication type. 'iflow' for native, 'openai-compatible' for others.",
        )
        AUTH_API_KEY: str = Field(
            default="",
            description="API Key for the model provider.",
        )
        AUTH_BASE_URL: str = Field(
            default="",
            description="Base URL for the model provider.",
        )
        AUTH_MODEL: str = Field(
            default="",
            description="Model name to use.",
        )
        SYSTEM_PROMPT: str = Field(
            default="",
            description="System prompt to guide the AI's behavior.",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "iflow_sdk"
        self.name = "iflow"
        self.valves = self.Valves()

    def _get_user_role(self, __user__: dict) -> str:
        """Determine if the user is an admin."""
        return __user__.get("role", "user")

    def _get_system_prompt(self, role: str) -> str:
        """Construct the dynamic system prompt based on user role."""
        prompt = self.valves.SYSTEM_PROMPT if self.valves.SYSTEM_PROMPT else ""
        prompt += BASE_GUIDELINES
        if role == "admin":
            prompt += ADMIN_EXTENSIONS
        else:
            prompt += USER_RESTRICTIONS
        return prompt

    async def _ensure_cli(self, _emit_status) -> bool:
        """Check for iFlow CLI and attempt installation if missing."""

        async def _check_binary(name: str) -> Optional[str]:
            # 1. Check in system PATH
            path = shutil.which(name)
            if path:
                return path

            # 2. Compile potential search paths
            search_paths = []

            # Try to resolve NPM global prefix
            try:
                proc = await asyncio.create_subprocess_exec(
                    "npm",
                    "config",
                    "get",
                    "prefix",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await proc.communicate()
                if proc.returncode == 0:
                    prefix = stdout.decode().strip()
                    search_paths.extend(
                        [
                            os.path.join(prefix, "bin"),
                            os.path.join(prefix, "node_modules", ".bin"),
                            prefix,
                        ]
                    )
            except:
                pass

            if self.valves.IFLOW_BIN_DIR:
                search_paths.extend(
                    [
                        self.valves.IFLOW_BIN_DIR,
                        os.path.join(self.valves.IFLOW_BIN_DIR, "bin"),
                    ]
                )

            # Common/default locations
            search_paths.extend(
                [
                    os.path.expanduser("~/.iflow/bin"),
                    os.path.expanduser("~/.npm-global/bin"),
                    os.path.expanduser("~/.local/bin"),
                    "/usr/local/bin",
                    "/usr/bin",
                    "/bin",
                    os.path.expanduser("~/bin"),
                ]
            )

            for p in search_paths:
                full_path = os.path.join(p, name)
                if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                    return full_path
            return None

        # Initial check
        binary_path = await _check_binary("iflow")
        if binary_path:
            logger.info(f"iFlow CLI found at: {binary_path}")
            bin_dir = os.path.dirname(binary_path)
            if bin_dir not in os.environ["PATH"]:
                os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"
            return True

        if not self.valves.AUTO_INSTALL_CLI:
            return False

        try:
            install_loc_msg = (
                self.valves.IFLOW_BIN_DIR
                if self.valves.IFLOW_BIN_DIR
                else "default location"
            )
            await _emit_status(
                f"iFlow CLI not found. Attempting auto-installation to {install_loc_msg}..."
            )

            # Detection for package managers and official script
            env = os.environ.copy()
            has_npm = shutil.which("npm") is not None
            has_curl = shutil.which("curl") is not None

            if has_npm:
                if self.valves.IFLOW_BIN_DIR:
                    os.makedirs(self.valves.IFLOW_BIN_DIR, exist_ok=True)
                    install_cmd = f"npm i -g --prefix {self.valves.IFLOW_BIN_DIR} @iflow-ai/iflow-cli@latest"
                else:
                    install_cmd = "npm i -g @iflow-ai/iflow-cli@latest"
            elif has_curl:
                await _emit_status(
                    "npm not found. Attempting to use official shell installer via curl..."
                )
                # Official installer script from gitee/github as fallback
                # We try gitee first as it's more reliable in some environments
                install_cmd = 'bash -c "$(curl -fsSL https://gitee.com/iflow-ai/iflow-cli/raw/main/install.sh)"'
                # If we have a custom bin dir, try to tell the installer (though it might not support it)
                if self.valves.IFLOW_BIN_DIR:
                    env["IFLOW_BIN_DIR"] = self.valves.IFLOW_BIN_DIR
            else:
                await _emit_status(
                    "Error: Neither 'npm' nor 'curl' found. Cannot proceed with auto-installation."
                )
                return False

            process = await asyncio.create_subprocess_shell(
                install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout_data, stderr_data = await process.communicate()

            # Even if the script returns non-zero (which it might if it tries to
            # start an interactive shell at the end), we check if the binary exists.
            await _emit_status(
                "Installation script finished. Finalizing verification..."
            )
            binary_path = await _check_binary("iflow")

            if binary_path:
                try:
                    os.chmod(binary_path, 0o755)
                except:
                    pass
                await _emit_status(f"iFlow CLI confirmed at {binary_path}.")
                bin_dir = os.path.dirname(binary_path)
                if bin_dir not in os.environ["PATH"]:
                    os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"
                return True
            else:
                # Script failed and no binary
                error_msg = (
                    stderr_data.decode().strip() or "Binary not found in search paths"
                )
                logger.error(
                    f"Installation failed with code {process.returncode}: {error_msg}"
                )
                await _emit_status(f"Installation failed: {error_msg}")
                return False
        except Exception as e:
            logger.error(f"Error during installation: {str(e)}")
            await _emit_status(f"Installation error: {str(e)}")
            return False

    async def _ensure_sdk(self, _emit_status) -> bool:
        """Check for iflow-cli-sdk Python package and attempt installation if missing."""
        global IFlowClient, IFlowOptions, AssistantMessage, TaskFinishMessage, ToolCallMessage, PlanMessage, TaskStatusMessage, ApprovalMode, StopReason

        if IFlowClient is not None:
            return True

        await _emit_status("iflow-cli-sdk not found. Attempting auto-installation...")
        try:
            # Use sys.executable to ensure we use the same Python environment
            import sys

            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                "iflow-cli-sdk",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                await _emit_status("iflow-cli-sdk installed successfully. Loading...")
                # Try to import again
                from iflow_sdk import (
                    IFlowClient as C,
                    IFlowOptions as O,
                    AssistantMessage as AM,
                    TaskFinishMessage as TM,
                    ToolCallMessage as TC,
                    PlanMessage as P,
                    TaskStatusMessage as TS,
                    ApprovalMode as AP,
                    StopReason as SR,
                )

                # Update global pointers
                IFlowClient, IFlowOptions = C, O
                AssistantMessage, TaskFinishMessage = AM, TM
                ToolCallMessage, PlanMessage = TC, P
                TaskStatusMessage, ApprovalMode, StopReason = TS, AP, SR
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"SDK installation failed: {error_msg}")
                await _emit_status(f"SDK installation failed: {error_msg}")
                return False
        except Exception as e:
            logger.error(f"Error during SDK installation: {str(e)}")
            await _emit_status(f"SDK installation error: {str(e)}")
            return False

    async def pipe(
        self, body: dict, __user__: dict, __event_emitter__=None
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Main entry point for the pipe."""

        async def _emit_status(description: str, done: bool = False):
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": description,
                            "done": done,
                        },
                    }
                )

        # 0. Ensure SDK and CLI are available
        if not await self._ensure_sdk(_emit_status):
            return "Error: iflow-cli-sdk (Python package) missing and auto-installation failed. Please install it with `pip install iflow-cli-sdk` manually."

        # 1. Update PATH to include custom bin dir
        if self.valves.IFLOW_BIN_DIR not in os.environ["PATH"]:
            os.environ["PATH"] = f"{self.valves.IFLOW_BIN_DIR}:{os.environ['PATH']}"

        # 2. Ensure CLI is installed and path is updated
        if not await self._ensure_cli(_emit_status):
            return f"Error: iFlow CLI not found and auto-installation failed. Please install it to {self.valves.IFLOW_BIN_DIR} manually."

        messages = body.get("messages", [])
        if not messages:
            return "No messages provided."

        # Get the last user message
        last_message = messages[-1]
        content = last_message.get("content", "")

        # Determine user role and construct prompt
        role = self._get_user_role(__user__)
        dynamic_prompt = self._get_system_prompt(role)

        # Prepare Auth Info
        auth_info = None
        if self.valves.AUTH_API_KEY:
            auth_info = {
                "api_key": self.valves.AUTH_API_KEY,
                "base_url": self.valves.AUTH_BASE_URL,
                "model_name": self.valves.AUTH_MODEL,
            }

        # Prepare Session Settings
        session_settings = None
        try:
            from iflow_sdk import SessionSettings

            session_settings = SessionSettings(system_prompt=dynamic_prompt)
        except ImportError:
            session_settings = {"system_prompt": dynamic_prompt}

        # 2. Configure iFlow Options
        # Use local references to ensure we're using the freshly imported SDK components
        from iflow_sdk import (
            IFlowOptions as SDKOptions,
            ApprovalMode as SDKApprovalMode,
        )

        # Get approval mode with a safe fallback
        try:
            target_mode = getattr(SDKApprovalMode, self.valves.APPROVAL_MODE)
        except (AttributeError, TypeError):
            target_mode = (
                SDKApprovalMode.YOLO if hasattr(SDKApprovalMode, "YOLO") else None
            )

        options = SDKOptions(
            url=self.valves.IFLOW_URL,
            auto_start_process=self.valves.AUTO_START,
            process_start_port=self.valves.IFLOW_PORT,
            timeout=self.valves.TIMEOUT,
            log_level=self.valves.LOG_LEVEL,
            cwd=self.valves.CWD or None,
            approval_mode=target_mode,
            file_access=self.valves.FILE_ACCESS,
            auth_method_id=self.valves.SELECTED_AUTH_TYPE if auth_info else None,
            auth_method_info=auth_info,
            session_settings=session_settings,
        )

        async def _emit_status(description: str, done: bool = False):
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": description,
                            "done": done,
                        },
                    }
                )

        # 3. Stream from iFlow
        async def stream_generator():
            try:
                await _emit_status("Initializing iFlow connection...")

                async with IFlowClient(options) as client:
                    await client.send_message(content)

                    await _emit_status("iFlow is processing...")

                    async for message in client.receive_messages():
                        if isinstance(message, AssistantMessage):
                            yield message.chunk.text
                            if message.agent_info and message.agent_info.agent_id:
                                logger.debug(
                                    f"Message from agent: {message.agent_info.agent_id}"
                                )

                        elif isinstance(message, PlanMessage):
                            plan_str = "\n".join(
                                [
                                    f"{'✅' if e.status == 'completed' else '⏳'} [{e.priority}] {e.content}"
                                    for e in message.entries
                                ]
                            )
                            await _emit_status(f"Execution Plan updated:\n{plan_str}")

                        elif isinstance(message, TaskStatusMessage):
                            await _emit_status(f"iFlow: {message.status}")

                        elif isinstance(message, ToolCallMessage):
                            tool_desc = (
                                f"Calling tool: {message.tool_name}"
                                if message.tool_name
                                else "Invoking tool"
                            )
                            await _emit_status(
                                f"{tool_desc}... (Status: {message.status})"
                            )

                        elif isinstance(message, TaskFinishMessage):
                            reason_msg = "Task completed."
                            if message.stop_reason == StopReason.MAX_TOKENS:
                                reason_msg = "Task stopped: Max tokens reached."
                            elif message.stop_reason == StopReason.END_TURN:
                                reason_msg = "Task completed successfully."

                            await _emit_status(reason_msg, done=True)
                            break

            except Exception as e:
                logger.error(f"Error in iFlow pipe: {str(e)}", exc_info=True)
                error_msg = f"iFlow Error: {str(e)}"
                yield error_msg
                await _emit_status(error_msg, done=True)

        return stream_generator()
