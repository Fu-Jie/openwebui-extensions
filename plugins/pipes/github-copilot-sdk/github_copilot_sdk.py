"""
title: GitHub Copilot Official SDK Pipe (Dynamic Models)
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
description: Integrate GitHub Copilot SDK. Supports dynamic models, multi-turn conversation, streaming, multimodal input, and infinite sessions (context compaction).
version: 0.1.1
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

# Setup logger
logger = logging.getLogger(__name__)

# Global client storage
_SHARED_CLIENT = None
_SHARED_TOKEN = ""
_CLIENT_LOCK = asyncio.Lock()


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="",
            description="GitHub Fine-grained Token (Requires 'Copilot Requests' permission)",
        )
        MODEL_ID: str = Field(
            default="claude-sonnet-4.5",
            description="Default Copilot model name (used when dynamic fetching fails)",
        )
        CLI_PATH: str = Field(
            default="/usr/local/bin/copilot",
            description="Path to Copilot CLI",
        )
        DEBUG: bool = Field(
            default=False,
            description="Enable technical debug logs (connection info, etc.)",
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

    def __init__(self):
        self.type = "pipe"
        self.id = "copilotsdk"
        self.name = "copilotsdk"
        self.valves = self.Valves()
        self.temp_dir = tempfile.mkdtemp(prefix="copilot_images_")
        self.thinking_started = False
        self._model_cache = []  # Model list cache

    def __del__(self):
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass

    def _emit_debug_log(self, message: str):
        """Emit debug log to frontend if DEBUG valve is enabled."""
        if self.valves.DEBUG:
            print(f"[Copilot Pipe] {message}")

    def _get_user_context(self):
        """Helper to get user context (placeholder for future use)."""
        return {}

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
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
            self._emit_debug_log(f"Extracted ChatID: {chat_id} (Source: {source})")
        else:
            # If still not found, log body keys for troubleshooting
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log(
                f"Warning: Failed to extract ChatID. Body keys: {keys}"
            )

        return {
            "chat_id": str(chat_id).strip(),
        }

    async def pipes(self) -> List[dict]:
        """Dynamically fetch model list"""
        # Return cache if available
        if self._model_cache:
            return self._model_cache

        self._emit_debug_log("Fetching model list dynamically...")
        try:
            self._setup_env()
            if not self.valves.GH_TOKEN:
                return [{"id": f"{self.id}-error", "name": "Error: GH_TOKEN not set"}]

            from copilot import CopilotClient

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

                self._emit_debug_log(
                    f"Successfully fetched {len(self._model_cache)} models (filtered)"
                )
                return self._model_cache
            except Exception as e:
                self._emit_debug_log(f"Failed to fetch model list: {e}")
                # Return default model on failure
                return [
                    {
                        "id": f"{self.id}-{self.valves.MODEL_ID}",
                        "name": f"GitHub Copilot ({self.valves.MODEL_ID})",
                    }
                ]
            finally:
                await client.stop()
        except Exception as e:
            self._emit_debug_log(f"Pipes Error: {e}")
            return [
                {
                    "id": f"{self.id}-{self.valves.MODEL_ID}",
                    "name": f"GitHub Copilot ({self.valves.MODEL_ID})",
                }
            ]

    async def _get_client(self):
        """Helper to get or create a CopilotClient instance."""
        from copilot import CopilotClient

        client_config = {}
        if os.environ.get("COPILOT_CLI_PATH"):
            client_config["cli_path"] = os.environ["COPILOT_CLI_PATH"]

        client = CopilotClient(client_config)
        await client.start()
        return client

    def _setup_env(self):
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

        if self.valves.GH_TOKEN:
            os.environ["GH_TOKEN"] = self.valves.GH_TOKEN
            os.environ["GITHUB_TOKEN"] = self.valves.GH_TOKEN

    def _process_images(self, messages):
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
                            self._emit_debug_log(f"Image processed: {file_path}")
                        except Exception as e:
                            self._emit_debug_log(f"Image error: {e}")
        else:
            text_content = str(content)
        return text_content, attachments

    async def pipe(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Union[str, AsyncGenerator]:
        self._setup_env()
        if not self.valves.GH_TOKEN:
            return "Error: Please configure GH_TOKEN in Valves."

        # Parse user selected model
        request_model = body.get("model", "")
        real_model_id = self.valves.MODEL_ID  # Default value

        if request_model.startswith(f"{self.id}-"):
            real_model_id = request_model[len(f"{self.id}-") :]
            self._emit_debug_log(f"Using selected model: {real_model_id}")

        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        # Get Chat ID using improved helper
        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx.get("chat_id")

        is_streaming = body.get("stream", False)
        self._emit_debug_log(f"Request Streaming: {is_streaming}")

        last_text, attachments = self._process_images(messages)

        # Determine prompt strategy
        # If we have a chat_id, we try to resume session.
        # If resumed, we assume the session has history, so we only send the last message.
        # If new session, we send full history (or at least the last few turns if we want to be safe, but let's send full for now).

        # However, to be robust against history edits in OpenWebUI, we might want to always send full history?
        # Copilot SDK `create_session` doesn't take history. `session.send` appends.
        # If we resume, we append.
        # If user edited history, the session state is stale.
        # For now, we implement "Resume if possible, else Create".

        prompt = ""
        is_new_session = True

        try:
            client = await self._get_client()
            session = None

            if chat_id:
                try:
                    # Try to resume session using chat_id as session_id
                    session = await client.resume_session(chat_id)
                    self._emit_debug_log(f"Resumed session using ChatID: {chat_id}")
                    is_new_session = False
                except Exception:
                    # Resume failed, session might not exist on disk
                    self._emit_debug_log(
                        f"Session {chat_id} not found or expired, creating new."
                    )
                    session = None

            if session is None:
                # Create new session
                from copilot.types import SessionConfig, InfiniteSessionConfig

                # Infinite Session Config
                infinite_session_config = None
                if self.valves.INFINITE_SESSION:
                    infinite_session_config = InfiniteSessionConfig(
                        enabled=True,
                        background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
                        buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
                    )

                session_config = SessionConfig(
                    session_id=(
                        chat_id if chat_id else None
                    ),  # Use chat_id as session_id
                    model=real_model_id,
                    streaming=body.get("stream", False),
                    infinite_sessions=infinite_session_config,
                )

                session = await client.create_session(config=session_config)

                new_sid = getattr(session, "session_id", getattr(session, "id", None))
                self._emit_debug_log(f"Created new session: {new_sid}")

            # Construct prompt
            if is_new_session:
                # For new session, send full conversation history
                full_conversation = []
                for msg in messages[:-1]:
                    role = msg.get("role", "user").upper()
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            [
                                c.get("text", "")
                                for c in content
                                if c.get("type") == "text"
                            ]
                        )
                    full_conversation.append(f"{role}: {content}")
                full_conversation.append(f"User: {last_text}")
                prompt = "\n\n".join(full_conversation)
            else:
                # For resumed session, only send the last message
                prompt = last_text

            send_payload = {"prompt": prompt, "mode": "immediate"}
            if attachments:
                send_payload["attachments"] = attachments

            if body.get("stream", False):
                # Determine session status message for UI
                init_msg = ""
                if self.valves.DEBUG:
                    if is_new_session:
                        new_sid = getattr(
                            session, "session_id", getattr(session, "id", "unknown")
                        )
                        init_msg = f"> [Debug] Created new session: {new_sid}\n"
                    else:
                        init_msg = (
                            f"> [Debug] Resumed session using ChatID: {chat_id}\n"
                        )

                return self.stream_response(client, session, send_payload, init_msg)
            else:
                try:
                    response = await session.send_and_wait(send_payload)
                    return response.data.content if response else "Empty response."
                finally:
                    # Destroy session object to free memory, but KEEP data on disk
                    await session.destroy()

        except Exception as e:
            self._emit_debug_log(f"Request Error: {e}")
            return f"Error: {str(e)}"

    async def stream_response(
        self, client, session, send_payload, init_message: str = ""
    ) -> AsyncGenerator:
        queue = asyncio.Queue()
        done = asyncio.Event()
        self.thinking_started = False
        has_content = False  # Track if any content has been yielded

        def get_event_data(event, attr, default=""):
            if hasattr(event, "data"):
                data = event.data
                if data is None:
                    return default
                if isinstance(data, (str, int, float, bool)):
                    return str(data) if attr == "value" else default

                if isinstance(data, dict):
                    val = data.get(attr)
                    if val is None:
                        alt_attr = attr.replace("_", "") if "_" in attr else attr
                        val = data.get(alt_attr)
                        if val is None and "_" not in attr:
                            # Try snake_case if camelCase failed
                            import re

                            snake_attr = re.sub(r"(?<!^)(?=[A-Z])", "_", attr).lower()
                            val = data.get(snake_attr)
                else:
                    val = getattr(data, attr, None)
                    if val is None:
                        alt_attr = attr.replace("_", "") if "_" in attr else attr
                        val = getattr(data, alt_attr, None)
                        if val is None and "_" not in attr:
                            import re

                            snake_attr = re.sub(r"(?<!^)(?=[A-Z])", "_", attr).lower()
                            val = getattr(data, snake_attr, None)

                return val if val is not None else default
            return default

        def handler(event):
            event_type = (
                getattr(event.type, "value", None)
                if hasattr(event, "type")
                else str(event.type)
            )

            # Log full event data for tool events to help debugging
            if "tool" in event_type:
                try:
                    data_str = str(event.data) if hasattr(event, "data") else "no data"
                    self._emit_debug_log(f"Tool Event [{event_type}]: {data_str}")
                except:
                    pass

            self._emit_debug_log(f"Event: {event_type}")

            # Handle message content (delta or full)
            if event_type in [
                "assistant.message_delta",
                "assistant.message.delta",
                "assistant.message",
            ]:
                # Log full message event for troubleshooting why there's no delta
                if event_type == "assistant.message":
                    self._emit_debug_log(
                        f"Received full message event (non-Delta): {get_event_data(event, 'content')[:50]}..."
                    )

                delta = (
                    get_event_data(event, "delta_content")
                    or get_event_data(event, "deltaContent")
                    or get_event_data(event, "content")
                    or get_event_data(event, "text")
                )
                if delta:
                    if self.thinking_started:
                        queue.put_nowait("\n</think>\n")
                        self.thinking_started = False
                    queue.put_nowait(delta)

            elif event_type in [
                "assistant.reasoning_delta",
                "assistant.reasoning.delta",
                "assistant.reasoning",
            ]:
                delta = (
                    get_event_data(event, "delta_content")
                    or get_event_data(event, "deltaContent")
                    or get_event_data(event, "content")
                    or get_event_data(event, "text")
                )
                if delta:
                    if not self.thinking_started and self.valves.SHOW_THINKING:
                        queue.put_nowait("<think>\n")
                        self.thinking_started = True
                    if self.thinking_started:
                        queue.put_nowait(delta)

            elif event_type == "tool.execution_start":
                # Try multiple possible fields for tool name/description
                tool_name = (
                    get_event_data(event, "toolName")
                    or get_event_data(event, "name")
                    or get_event_data(event, "description")
                    or get_event_data(event, "tool_name")
                    or "Unknown Tool"
                )
                if not self.thinking_started and self.valves.SHOW_THINKING:
                    queue.put_nowait("<think>\n")
                    self.thinking_started = True
                if self.thinking_started:
                    queue.put_nowait(f"\nRunning Tool: {tool_name}...\n")
                self._emit_debug_log(f"Tool Start: {tool_name}")

            elif event_type == "tool.execution_complete":
                if self.thinking_started:
                    queue.put_nowait("Tool Completed.\n")
                self._emit_debug_log("Tool Complete")

            elif event_type == "session.compaction_start":
                self._emit_debug_log("Session Compaction Started")

            elif event_type == "session.compaction_complete":
                self._emit_debug_log("Session Compaction Completed")

            elif event_type == "session.idle":
                done.set()
            elif event_type == "session.error":
                msg = get_event_data(event, "message", "Unknown Error")
                queue.put_nowait(f"\n[Error: {msg}]")
                done.set()

        unsubscribe = session.on(handler)
        await session.send(send_payload)

        if self.valves.DEBUG:
            yield "<think>\n"
            if init_message:
                yield init_message
            yield "> [Debug] Connection established, waiting for response...\n"
            self.thinking_started = True

        try:
            while not done.is_set():
                try:
                    chunk = await asyncio.wait_for(
                        queue.get(), timeout=float(self.valves.TIMEOUT)
                    )
                    if chunk:
                        has_content = True
                        yield chunk
                except asyncio.TimeoutError:
                    if done.is_set():
                        break
                    if self.thinking_started:
                        yield f"> [Debug] Waiting for response ({self.valves.TIMEOUT}s exceeded)...\n"
                    continue

            while not queue.empty():
                chunk = queue.get_nowait()
                if chunk:
                    has_content = True
                    yield chunk

            if self.thinking_started:
                yield "\n</think>\n"
                has_content = True

            # Core fix: If no content was yielded, return a fallback message to prevent OpenWebUI error
            if not has_content:
                yield "⚠️ Copilot returned no content. Please check if the Model ID is correct or enable DEBUG mode in Valves for details."

        except Exception as e:
            yield f"\n[Stream Error: {str(e)}]"
        finally:
            unsubscribe()
            # Only destroy session if it's not cached
            # We can't easily check chat_id here without passing it,
            # but stream_response is called within the scope where we decide persistence.
            # Wait, stream_response takes session as arg.
            # We need to know if we should destroy it.
            # Let's assume if it's in _SESSIONS, we don't destroy it.
            # But checking _SESSIONS here is race-prone or complex.
            # Simplified: The caller (pipe) handles destruction logic?
            # No, stream_response is a generator, pipe returns it.
            # So pipe function exits before stream finishes.
            # We need to handle destruction here.
            pass

            # TODO: Proper session cleanup for streaming
            # For now, we rely on the fact that if we mapped it, we keep it.
            # If we didn't map it (no chat_id), we should destroy it.
            # But we don't have chat_id here.
            # Let's modify stream_response signature or just leave it open for GC?
            # CopilotSession doesn't auto-close.
            # Let's add a flag to stream_response.
            pass
