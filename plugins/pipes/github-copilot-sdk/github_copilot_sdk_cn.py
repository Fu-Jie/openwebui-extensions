"""
title: GitHub Copilot 官方 SDK 管道 (动态模型版)
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
description: 集成 GitHub Copilot SDK。支持动态模型、多轮对话、流式输出、多模态输入及无限会话（上下文自动压缩）。
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

# Open WebUI internal database (re-use shared connection)
try:
    from open_webui.internal import db as owui_db
except ModuleNotFoundError:
    owui_db = None


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


def _discover_owui_schema(db_module: Any) -> Optional[str]:
    """Discover the Open WebUI database schema name if configured."""
    if db_module is None:
        return None

    try:
        base = getattr(db_module, "Base", None)
        metadata = getattr(base, "metadata", None) if base is not None else None
        candidate = getattr(metadata, "schema", None) if metadata is not None else None
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    except Exception as exc:
        logger.error(f"[DB Discover] Base metadata schema lookup failed: {exc}")

    try:
        metadata_obj = getattr(db_module, "metadata_obj", None)
        candidate = (
            getattr(metadata_obj, "schema", None) if metadata_obj is not None else None
        )
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    except Exception as exc:
        logger.error(f"[DB Discover] metadata_obj schema lookup failed: {exc}")

    try:
        from open_webui import env as owui_env

        candidate = getattr(owui_env, "DATABASE_SCHEMA", None)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    except Exception as exc:
        logger.error(f"[DB Discover] env schema lookup failed: {exc}")

    return None


owui_engine = _discover_owui_engine(owui_db)
owui_schema = _discover_owui_schema(owui_db)
owui_Base = getattr(owui_db, "Base", None) if owui_db is not None else None
if owui_Base is None:
    owui_Base = declarative_base()


class CopilotSessionMap(owui_Base):
    """Copilot Session Mapping Table"""

    __tablename__ = "copilot_session_map"
    __table_args__ = (
        {"extend_existing": True, "schema": owui_schema}
        if owui_schema
        else {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    copilot_session_id = Column(String(255), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# 全局客户端存储
_SHARED_CLIENT = None
_SHARED_TOKEN = ""
_CLIENT_LOCK = asyncio.Lock()


class Pipe:
    class Valves(BaseModel):
        GH_TOKEN: str = Field(
            default="", description="GitHub 细粒度令牌 (需开启 'Copilot Requests' 权限)"
        )
        MODEL_ID: str = Field(
            default="claude-sonnet-4.5",
            description="默认使用的 Copilot 模型名称 (当无法动态获取时使用)",
        )
        CLI_PATH: str = Field(
            default="/usr/local/bin/copilot",
            description="Copilot CLI 路径",
        )
        DEBUG: bool = Field(
            default=False,
            description="开启技术调试日志 (连接信息等)",
        )
        SHOW_THINKING: bool = Field(
            default=True,
            description="显示模型推理/思考过程",
        )
        EXCLUDE_KEYWORDS: str = Field(
            default="",
            description="排除包含这些关键词的模型 (逗号分隔，例如: codex, haiku)",
        )
        WORKSPACE_DIR: str = Field(
            default="",
            description="文件操作的受限工作目录。如果为空，允许访问当前进程目录。",
        )
        INFINITE_SESSION: bool = Field(
            default=True,
            description="启用无限会话 (自动上下文压缩)",
        )
        COMPACTION_THRESHOLD: float = Field(
            default=0.8,
            description="后台压缩阈值 (0.0-1.0)",
        )
        BUFFER_THRESHOLD: float = Field(
            default=0.95,
            description="背景压缩缓冲区阈值 (0.0-1.0)",
        )
        TIMEOUT: int = Field(
            default=300,
            description="流式数据块超时时间 (秒)",
        )

    def __init__(self):
        self.type = "pipe"
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
            self._emit_debug_log(f"提取到 ChatID: {chat_id} (来源: {source})")
        else:
            # 如果还是没找到，记录一下 body 的键，方便排查
            keys = list(body.keys()) if isinstance(body, dict) else "not a dict"
            self._emit_debug_log(f"警告: 未能提取到 ChatID。Body 键: {keys}")

        return {
            "chat_id": str(chat_id).strip(),
        }

    async def pipes(self) -> List[dict]:
        """动态获取模型列表"""
        # 如果有缓存，直接返回
        if self._model_cache:
            return self._model_cache

        self._emit_debug_log("正在动态获取模型列表...")
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

                self._emit_debug_log(
                    f"成功获取 {len(self._model_cache)} 个模型 (已过滤)"
                )
                return self._model_cache
            except Exception as e:
                self._emit_debug_log(f"获取模型列表失败: {e}")
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
            return "Error: 请在 Valves 中配置 GH_TOKEN。"

        # 解析用户选择的模型
        request_model = body.get("model", "")
        real_model_id = self.valves.MODEL_ID  # 默认值

        if request_model.startswith(f"{self.id}-"):
            real_model_id = request_model[len(f"{self.id}-") :]
            self._emit_debug_log(f"使用选择的模型: {real_model_id}")

        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        # 使用改进的助手获取 Chat ID
        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx.get("chat_id")

        is_streaming = body.get("stream", False)
        self._emit_debug_log(f"请求流式传输: {is_streaming}")

        last_text, attachments = self._process_images(messages)

        # 确定 Prompt 策略
        # 如果有 chat_id，尝试恢复会话。
        # 如果恢复成功，假设会话已有历史，只发送最后一条消息。
        # 如果是新会话，发送完整历史。

        prompt = ""
        is_new_session = True

        try:
            client = await self._get_client()
            session = None

            if chat_id:
                try:
                    # 尝试直接使用 chat_id 作为 session_id 恢复会话
                    session = await client.resume_session(chat_id)
                    self._emit_debug_log(f"已通过 ChatID 恢复会话: {chat_id}")
                    is_new_session = False
                except Exception:
                    # 恢复失败，磁盘上可能不存在该会话
                    self._emit_debug_log(
                        f"会话 {chat_id} 不存在或已过期，将创建新会话。"
                    )
                    session = None

            if session is None:
                # 创建新会话
                from copilot.types import SessionConfig, InfiniteSessionConfig

                # 无限会话配置
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
                    ),  # 使用 chat_id 作为 session_id
                    model=real_model_id,
                    streaming=body.get("stream", False),
                    infinite_sessions=infinite_session_config,
                )

                session = await client.create_session(config=session_config)

                # 获取新会话 ID
                new_sid = getattr(session, "session_id", getattr(session, "id", None))
                self._emit_debug_log(f"创建了新会话: {new_sid}")

            # 构建 Prompt
            if is_new_session:
                # 新会话，发送完整历史
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
                # 恢复的会话，只发送最后一条消息
                prompt = last_text

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

                return self.stream_response(client, session, send_payload, init_msg)
            else:
                try:
                    response = await session.send_and_wait(send_payload)
                    return response.data.content if response else "Empty response."
                finally:
                    # 销毁会话对象以释放内存，但保留磁盘数据
                    await session.destroy()

        except Exception as e:
            self._emit_debug_log(f"请求错误: {e}")
            return f"Error: {str(e)}"

    async def stream_response(
        self, client, session, send_payload, init_message: str = ""
    ) -> AsyncGenerator:
        queue = asyncio.Queue()
        done = asyncio.Event()
        self.thinking_started = False
        has_content = False  # 追踪是否已经输出了内容

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
                            # 尝试将 camelCase 转换为 snake_case
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

            # 记录工具事件的完整数据以辅助调试
            if "tool" in event_type:
                try:
                    data_str = str(event.data) if hasattr(event, "data") else "no data"
                    self._emit_debug_log(f"Tool Event [{event_type}]: {data_str}")
                except:
                    pass

            self._emit_debug_log(f"Event: {event_type}")

            # 处理消息内容 (增量或全量)
            if event_type in [
                "assistant.message_delta",
                "assistant.message.delta",
                "assistant.message",
            ]:
                # 记录全量消息事件的特殊日志，帮助排查为什么没有 delta
                if event_type == "assistant.message":
                    self._emit_debug_log(
                        f"收到全量消息事件 (非 Delta): {get_event_data(event, 'content')[:50]}..."
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
                # 尝试多个可能的字段来获取工具名称或描述
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
                    queue.put_nowait(f"\n正在运行工具: {tool_name}...\n")
                self._emit_debug_log(f"Tool Start: {tool_name}")

            elif event_type == "tool.execution_complete":
                if self.thinking_started:
                    queue.put_nowait("工具运行完成。\n")
                self._emit_debug_log("Tool Complete")

            elif event_type == "session.compaction_start":
                self._emit_debug_log("会话压缩开始")

            elif event_type == "session.compaction_complete":
                self._emit_debug_log("会话压缩完成")

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
            yield "> [Debug] 连接已建立，等待响应...\n"
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
                        yield f"> [Debug] 等待响应中 (已超过 {self.valves.TIMEOUT} 秒)...\n"
                    continue

            while not queue.empty():
                chunk = queue.get_nowait()
                if chunk:
                    has_content = True
                    yield chunk

            if self.thinking_started:
                yield "\n</think>\n"
                has_content = True

            # 核心修复：如果整个过程没有任何输出，返回一个提示，防止 OpenWebUI 报错
            if not has_content:
                yield "⚠️ Copilot 未返回任何内容。请检查模型 ID 是否正确，或尝试在 Valves 中开启 DEBUG 模式查看详细日志。"

        except Exception as e:
            yield f"\n[Stream Error: {str(e)}]"
        finally:
            unsubscribe()
            # 销毁会话对象以释放内存，但保留磁盘数据
            await session.destroy()
