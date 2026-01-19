"""
title: Async Context Compression
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
description: Reduces token consumption in long conversations while maintaining coherence through intelligent summarization and message compression.
version: 1.2.0
openwebui_id: b1655bc8-6de9-4cad-8cb5-a6f7829a02ce
license: MIT

═══════════════════════════════════════════════════════════════════════════════
📌 What's new in 1.2.0
═══════════════════════════════════════════════════════════════════════════════

  ✅ Preflight Context Check: Validates context fit before sending to model.
  ✅ Structure-Aware Trimming: Collapses long AI responses while keeping H1-H6, intro, and conclusion.
  ✅ Native Tool Output Trimming: Cleaner context when using function calling. (Note: Non-native tool outputs are not fully injected into context)
  ✅ Context Usage Warning: Notification when usage exceeds 90%.
  ✅ Detailed Token Logging: Granular breakdown of System, Head, Summary, and Tail tokens.

═══════════════════════════════════════════════════════════════════════════════
📌 Overview
═══════════════════════════════════════════════════════════════════════════════

This filter significantly reduces token consumption in long conversations by using intelligent summarization and message compression, while maintaining conversational coherence.

Core Features:
  ✅ Automatic compression triggered by Token count threshold
  ✅ Asynchronous summary generation (does not block user response)
  ✅ Persistent storage with database support (PostgreSQL and SQLite)
  ✅ Flexible retention policy (configurable to keep first and last N messages)
  ✅ Smart summary injection to maintain context
  ✅ Structure-aware trimming to preserve document skeleton
  ✅ Native tool output trimming for function calling support

═══════════════════════════════════════════════════════════════════════════════
🔄 Workflow
═══════════════════════════════════════════════════════════════════════════════

Phase 1: Inlet (Pre-request processing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Receives all messages in the current conversation.
  2. Checks for a previously saved summary.
  3. If a summary exists and the message count exceeds the retention threshold:
     ├─ Extracts the first N messages to be kept.
     ├─ Injects the summary into the first message.
     ├─ Extracts the last N messages to be kept.
     └─ Combines them into a new message list: [Kept First Messages + Summary] + [Kept Last Messages].
  4. Sends the compressed message list to the LLM.

Phase 2: Outlet (Post-response processing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Triggered after the LLM response is complete.
  2. Checks if the Token count has reached the compression threshold.
  3. If the threshold is met, an asynchronous background task is started to generate a summary:
     ├─ Extracts messages to be summarized (excluding the kept first and last messages).
     ├─ Calls the LLM to generate a concise summary.
     └─ Saves the summary to the database.

═══════════════════════════════════════════════════════════════════════════════
💾 Storage
═══════════════════════════════════════════════════════════════════════════════

This filter uses Open WebUI's shared database connection for persistent storage.
It automatically reuses Open WebUI's internal SQLAlchemy engine and SessionLocal,
making the plugin database-agnostic and ensuring compatibility with any database
backend that Open WebUI supports (PostgreSQL, SQLite, etc.).

No additional database configuration is required - the plugin inherits
Open WebUI's database settings automatically.

  Table Structure (`chat_summary`):
    - id: Primary Key (auto-increment)
    - chat_id: Unique chat identifier (indexed)
    - summary: The summary content (TEXT)
    - compressed_message_count: The original number of messages
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update

═══════════════════════════════════════════════════════════════════════════════
📊 Compression Example
═══════════════════════════════════════════════════════════════════════════════

Scenario: A 20-message conversation (Default settings: keep first 1, keep last 6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Before Compression:
    Message 1: [Initial prompt + First question]
    Messages 2-14: [Historical conversation]
    Messages 15-20: [Recent conversation]
    Total: 20 full messages

  After Compression:
    Message 1: [Initial prompt + Historical summary + First question]
    Messages 15-20: [Last 6 full messages]
    Total: 7 messages

  Effect:
    ✓ Saves 13 messages (approx. 65%)
    ✓ Retains full context
    ✓ Protects important initial prompts

═══════════════════════════════════════════════════════════════════════════════
⚙️ Configuration
═══════════════════════════════════════════════════════════════════════════════

priority
  Default: 10
  Description: The execution order of the filter. Lower numbers run first.

compression_threshold_tokens
  Default: 64000
  Description: When the total context Token count exceeds this value, compression is triggered.
  Recommendation: Adjust based on your model's context window and cost.

max_context_tokens
  Default: 128000
  Description: Hard limit for context. Exceeding this value will force removal of the earliest messages.

model_thresholds
  Default: {}
  Description: Threshold override configuration for specific models.
  Example: {"gpt-4": {"compression_threshold_tokens": 8000, "max_context_tokens": 32000}}

enable_tool_output_trimming
  Default: false
  Description: When enabled and `function_calling: "native"` is active, trims verbose tool outputs to extract only the final answer.

keep_first
  Default: 1
  Description: Always keep the first N messages of the conversation. Set to 0 to disable. The first message often contains important system prompts.

keep_last
  Default: 6
  Description: Always keep the last N full messages of the conversation to ensure context coherence.

summary_model
  Default: None
  Description: The LLM used to generate the summary.
  Recommendation:
    - It is strongly recommended to configure a fast, economical, and compatible model, such as `deepseek-v3`, `gemini-2.5-flash`, `gpt-4.1`.
    - If left empty, the filter will attempt to use the model from the current conversation.
  Note:
    - If the current conversation uses a pipeline (Pipe) model or a model that does not support standard generation APIs, leaving this field empty may cause summary generation to fail. In this case, you must specify a valid model.

max_summary_tokens
  Default: 16384
  Description: The maximum number of tokens allowed for the generated summary.

summary_temperature
  Default: 0.3
  Description: Controls the randomness of the summary generation. Lower values produce more deterministic output.

debug_mode
  Default: true
  Description: Prints detailed debug information to the log. Recommended to set to `false` in production.

show_debug_log
  Default: false
  Description: Print debug logs to browser console (F12). Useful for frontend debugging.

🔧 Deployment
═══════════════════════════════════════════════════════

The plugin automatically uses Open WebUI's shared database connection.
No additional database configuration is required.

Suggested Filter Installation Order:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
It is recommended to set the priority of this filter relatively high (a smaller number) to ensure it runs before other filters that might modify message content. A typical order might be:

  1. Filters that need access to the full, uncompressed history (priority < 10)
     (e.g., a filter that injects a system-level prompt)
  2. This compression filter (priority = 10)
  3. Filters that run after compression (priority > 10)
     (e.g., a final output formatting filter)

═══════════════════════════════════════════════════════════════════════════════
📝 Database Query Examples
═══════════════════════════════════════════════════════════════════════════════

View all summaries:
  SELECT
    chat_id,
    LEFT(summary, 100) as summary_preview,
    compressed_message_count,
    updated_at
  FROM chat_summary
  ORDER BY updated_at DESC;

Query a specific conversation:
  SELECT *
  FROM chat_summary
  WHERE chat_id = 'your_chat_id';

Delete old summaries:
  DELETE FROM chat_summary
  WHERE updated_at < NOW() - INTERVAL '30 days';

Statistics:
  SELECT
    COUNT(*) as total_summaries,
    AVG(LENGTH(summary)) as avg_summary_length,
    AVG(compressed_message_count) as avg_msg_count
  FROM chat_summary;

═══════════════════════════════════════════════════════════════════════════════
⚠️ Important Notes
═══════════════════════════════════════════════════════════════════════════════

1. Database Connection
   ✓ The plugin uses Open WebUI's shared database connection automatically.
   ✓ No additional configuration is required.
   ✓ The `chat_summary` table will be created automatically on first run.

2. Retention Policy
   ⚠ The `keep_first` setting is crucial for preserving initial messages that contain system prompts. Configure it as needed.

3. Performance
   ⚠ Summary generation is asynchronous and will not block the user response.
   ⚠ There will be a brief background processing time when the threshold is first met.

4. Cost Optimization
   ⚠ The summary model is called once each time the threshold is met.
   ⚠ Set `compression_threshold_tokens` reasonably to avoid frequent calls.
   ⚠ It's recommended to use a fast and economical model (like `gemini-flash`) to generate summaries.

5. Multimodal Support
   ✓ This filter supports multimodal messages containing images.
   ✓ The summary is generated only from the text content.
   ✓ Non-text parts (like images) are preserved in their original messages during compression.

═══════════════════════════════════════════════════════════════════════════════
🐛 Troubleshooting
═══════════════════════════════════════════════════════════════════════════════

Problem: Database table not created
Solution:
  1. Ensure Open WebUI is properly configured with a database.
  2. Check the Open WebUI container logs for detailed error messages.
  3. Verify that Open WebUI's database connection is working correctly.

Problem: Summary not generated
Solution:
  1. Check if the `compression_threshold_tokens` has been met.
  2. Verify that the `summary_model` is configured correctly.
  3. Check the debug logs for any error messages.

Problem: Initial system prompt is lost
Solution:
  - Ensure `keep_first` is set to a value greater than 0 to preserve the initial messages containing this information.

Problem: Compression effect is not significant
Solution:
  1. Increase the `compression_threshold_tokens` appropriately.
  2. Decrease the number of `keep_last` or `keep_first`.
  3. Check if the conversation is actually long enough.


"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List, Union, Callable, Awaitable
import re
import asyncio
import json
import hashlib
import time
import contextlib

# Open WebUI built-in imports
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.models.models import Models
from fastapi.requests import Request
from open_webui.main import app as webui_app

# Open WebUI internal database (re-use shared connection)
try:
    from open_webui.internal import db as owui_db
except ModuleNotFoundError:  # pragma: no cover - filter runs inside Open WebUI
    owui_db = None

# Try to import tiktoken
try:
    import tiktoken
except ImportError:
    tiktoken = None

# Database imports
from sqlalchemy import Column, String, Text, DateTime, Integer, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
from datetime import datetime


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
            print(f"[DB Discover] get_db_context failed: {exc}")

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
        print(f"[DB Discover] Base metadata schema lookup failed: {exc}")

    try:
        metadata_obj = getattr(db_module, "metadata_obj", None)
        candidate = (
            getattr(metadata_obj, "schema", None) if metadata_obj is not None else None
        )
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    except Exception as exc:
        print(f"[DB Discover] metadata_obj schema lookup failed: {exc}")

    try:
        from open_webui import env as owui_env

        candidate = getattr(owui_env, "DATABASE_SCHEMA", None)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    except Exception as exc:
        print(f"[DB Discover] env schema lookup failed: {exc}")

    return None


owui_engine = _discover_owui_engine(owui_db)
owui_schema = _discover_owui_schema(owui_db)
owui_Base = getattr(owui_db, "Base", None) if owui_db is not None else None
if owui_Base is None:
    owui_Base = declarative_base()


class ChatSummary(owui_Base):
    """Chat Summary Storage Table"""

    __tablename__ = "chat_summary"
    __table_args__ = (
        {"extend_existing": True, "schema": owui_schema}
        if owui_schema
        else {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    compressed_message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Filter:
    def __init__(self):
        self.valves = self.Valves()
        self._owui_db = owui_db
        self._db_engine = owui_engine
        self._fallback_session_factory = (
            sessionmaker(bind=self._db_engine) if self._db_engine else None
        )
        self._init_database()

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
            raise RuntimeError(
                "Open WebUI database session is unavailable. Ensure Open WebUI's database layer is initialized."
            )

        session = self._fallback_session_factory()
        try:
            yield session
        finally:
            try:
                session.close()
            except Exception as exc:  # pragma: no cover - best-effort cleanup
                print(f"[Database] ⚠️ Failed to close fallback session: {exc}")

    def _init_database(self):
        """Initializes the database table using Open WebUI's shared connection."""
        try:
            if self._db_engine is None:
                raise RuntimeError(
                    "Open WebUI database engine is unavailable. Ensure Open WebUI is configured with a valid DATABASE_URL."
                )

            # Check if table exists using SQLAlchemy inspect
            inspector = inspect(self._db_engine)
            if not inspector.has_table("chat_summary"):
                # Create the chat_summary table if it doesn't exist
                ChatSummary.__table__.create(bind=self._db_engine, checkfirst=True)
                print(
                    "[Database] ✅ Successfully created chat_summary table using Open WebUI's shared database connection."
                )
            else:
                print(
                    "[Database] ✅ Using Open WebUI's shared database connection. chat_summary table already exists."
                )

        except Exception as e:
            print(f"[Database] ❌ Initialization failed: {str(e)}")

    class Valves(BaseModel):
        priority: int = Field(
            default=10, description="Priority level for the filter operations."
        )
        # Token related parameters
        compression_threshold_tokens: int = Field(
            default=64000,
            ge=0,
            description="When total context Token count exceeds this value, trigger compression (Global Default)",
        )
        max_context_tokens: int = Field(
            default=128000,
            ge=0,
            description="Hard limit for context. Exceeding this value will force removal of earliest messages (Global Default)",
        )
        model_thresholds: dict = Field(
            default={},
            description="Threshold override configuration for specific models. Only includes models requiring special configuration.",
        )

        keep_first: int = Field(
            default=1,
            ge=0,
            description="Always keep the first N messages. Set to 0 to disable.",
        )
        keep_last: int = Field(
            default=6, ge=0, description="Always keep the last N full messages."
        )
        summary_model: str = Field(
            default=None,
            description="The model ID used to generate the summary. If empty, uses the current conversation's model. Used to match configurations in model_thresholds.",
        )
        max_summary_tokens: int = Field(
            default=16384,
            ge=1,
            description="The maximum number of tokens for the summary.",
        )
        summary_temperature: float = Field(
            default=0.1,
            ge=0.0,
            le=2.0,
            description="The temperature for summary generation.",
        )
        debug_mode: bool = Field(
            default=True, description="Enable detailed logging for debugging."
        )
        show_debug_log: bool = Field(
            default=False, description="Show debug logs in the frontend console"
        )
        show_token_usage_status: bool = Field(
            default=True, description="Show token usage status notification"
        )
        enable_tool_output_trimming: bool = Field(
            default=False,
            description="Enable trimming of large tool outputs (only works with native function calling).",
        )

    def _save_summary(self, chat_id: str, summary: str, compressed_count: int):
        """Saves the summary to the database."""
        try:
            with self._db_session() as session:
                # Find existing record
                existing = session.query(ChatSummary).filter_by(chat_id=chat_id).first()

                if existing:
                    # [Optimization] Optimistic lock check: update only if progress moves forward
                    if compressed_count <= existing.compressed_message_count:
                        if self.valves.debug_mode:
                            print(
                                f"[Storage] Skipping update: New progress ({compressed_count}) is not greater than existing progress ({existing.compressed_message_count})"
                            )
                        return

                    # Update existing record
                    existing.summary = summary
                    existing.compressed_message_count = compressed_count
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    new_summary = ChatSummary(
                        chat_id=chat_id,
                        summary=summary,
                        compressed_message_count=compressed_count,
                    )
                    session.add(new_summary)

                session.commit()

                if self.valves.debug_mode:
                    action = "Updated" if existing else "Created"
                    print(
                        f"[Storage] Summary has been {action.lower()} in the database (Chat ID: {chat_id})"
                    )

        except Exception as e:
            print(f"[Storage] ❌ Database save failed: {str(e)}")

    def _load_summary_record(self, chat_id: str) -> Optional[ChatSummary]:
        """Loads the summary record object from the database."""
        try:
            with self._db_session() as session:
                record = session.query(ChatSummary).filter_by(chat_id=chat_id).first()
                if record:
                    # Detach the object from the session so it can be used after session close
                    session.expunge(record)
                    return record
        except Exception as e:
            print(f"[Load] ❌ Database read failed: {str(e)}")
        return None

    def _load_summary(self, chat_id: str, body: dict) -> Optional[str]:
        """Loads the summary text from the database (Compatible with old interface)."""
        record = self._load_summary_record(chat_id)
        if record:
            if self.valves.debug_mode:
                print(f"[Load] Loaded summary from database (Chat ID: {chat_id})")
                print(
                    f"[Load] Last updated: {record.updated_at}, Compressed message count: {record.compressed_message_count}"
                )
            return record.summary
        return None

    def _count_tokens(self, text: str) -> int:
        """Counts the number of tokens in the text."""
        if not text:
            return 0

        if tiktoken:
            try:
                # Uniformly use o200k_base encoding (adapted for latest models)
                encoding = tiktoken.get_encoding("o200k_base")
                return len(encoding.encode(text))
            except Exception as e:
                if self.valves.debug_mode:
                    print(
                        f"[Token Count] tiktoken error: {e}, falling back to character estimation"
                    )

        # Fallback strategy: Rough estimation (1 token ≈ 4 chars)
        return len(text) // 4

    def _calculate_messages_tokens(self, messages: List[Dict]) -> int:
        """Calculates the total tokens for a list of messages."""
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle multimodal content
                text_content = ""
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_content += part.get("text", "")
                total_tokens += self._count_tokens(text_content)
            else:
                total_tokens += self._count_tokens(str(content))
        return total_tokens

    def _get_model_thresholds(self, model_id: str) -> Dict[str, int]:
        """Gets threshold configuration for a specific model.

        Priority:
        1. If configuration exists for the model ID in model_thresholds, use it.
        2. Otherwise, use global parameters compression_threshold_tokens and max_context_tokens.
        """
        # Try to match from model-specific configuration
        if model_id in self.valves.model_thresholds:
            if self.valves.debug_mode:
                print(f"[Config] Using model-specific configuration: {model_id}")
            return self.valves.model_thresholds[model_id]

        # Use global default configuration
        if self.valves.debug_mode:
            print(
                f"[Config] Model {model_id} not in model_thresholds, using global parameters"
            )

        return {
            "compression_threshold_tokens": self.valves.compression_threshold_tokens,
            "max_context_tokens": self.valves.max_context_tokens,
        }

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        Unified extraction of chat context information (chat_id, message_id).
        Prioritizes extraction from body, then metadata.
        """
        chat_id = ""
        message_id = ""

        # 1. Try to get from body
        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")  # message_id is usually 'id' in body

            # Check body.metadata as fallback
            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        # 2. Try to get from __metadata__ (as supplement)
        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

    async def _emit_debug_log(
        self,
        __event_call__,
        chat_id: str,
        original_count: int,
        compressed_count: int,
        summary_length: int,
        kept_first: int,
        kept_last: int,
    ):
        """Emit debug log to browser console via JS execution"""
        if not self.valves.show_debug_log or not __event_call__:
            return

        try:
            # Prepare data for JS
            log_data = {
                "chatId": chat_id,
                "originalCount": original_count,
                "compressedCount": compressed_count,
                "summaryLength": summary_length,
                "keptFirst": kept_first,
                "keptLast": kept_last,
                "ratio": (
                    f"{(1 - compressed_count/original_count)*100:.1f}%"
                    if original_count > 0
                    else "0%"
                ),
            }

            # Construct JS code
            js_code = f"""
                (async function() {{
                    console.group("🗜️ Async Context Compression Debug");
                    console.log("Chat ID:", {json.dumps(chat_id)});
                    console.log("Messages:", {original_count} + " -> " + {compressed_count});
                    console.log("Compression Ratio:", {json.dumps(log_data['ratio'])});
                    console.log("Summary Length:", {summary_length} + " chars");
                    console.log("Configuration:", {{
                        "Keep First": {kept_first},
                        "Keep Last": {kept_last}
                    }});
                    console.groupEnd();
                }})();
            """

            await __event_call__(
                {
                    "type": "execute",
                    "data": {"code": js_code},
                }
            )
        except Exception as e:
            print(f"Error emitting debug log: {e}")

    async def _log(self, message: str, type: str = "info", event_call=None):
        """Unified logging to both backend (print) and frontend (console.log)"""
        # Backend logging
        if self.valves.debug_mode:
            print(message)

        # Frontend logging
        if self.valves.show_debug_log and event_call:
            try:
                css = "color: #3b82f6;"  # Blue default
                if type == "error":
                    css = "color: #ef4444; font-weight: bold;"  # Red
                elif type == "warning":
                    css = "color: #f59e0b;"  # Orange
                elif type == "success":
                    css = "color: #10b981; font-weight: bold;"  # Green

                # Clean message for frontend: remove separators and extra newlines
                lines = message.split("\n")
                # Keep lines that don't start with lots of equals or hyphens
                filtered_lines = [
                    line
                    for line in lines
                    if not line.strip().startswith("====")
                    and not line.strip().startswith("----")
                ]
                clean_message = "\n".join(filtered_lines).strip()

                if not clean_message:
                    return

                # Escape quotes in message for JS string
                safe_message = clean_message.replace('"', '\\"').replace("\n", "\\n")

                js_code = f"""
                    console.log("%c[Compression] {safe_message}", "{css}");
                """
                await event_call({"type": "execute", "data": {"code": js_code}})
            except Exception as e:
                print(f"Failed to emit log to frontend: {e}")

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: dict = None,
        __request__: Request = None,
        __model__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        Executed before sending to the LLM.
        Compression Strategy: Only responsible for injecting existing summaries, no Token calculation.
        """

        messages = body.get("messages", [])

        # --- Native Tool Output Trimming (Opt-in, only for native function calling) ---
        metadata = body.get("metadata", {})
        is_native_func_calling = metadata.get("function_calling") == "native"

        if self.valves.enable_tool_output_trimming and is_native_func_calling:
            trimmed_count = 0

            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str):
                    continue

                role = msg.get("role")

                # Only process assistant messages with native tool outputs
                if role == "assistant":
                    # Detect tool output markers in assistant content
                    if "tool_call_id:" in content or (
                        content.startswith('"') and "\\&quot;" in content
                    ):
                        # Always trim tool outputs when enabled

                        if self.valves.show_debug_log and __event_call__:
                            await self._log(
                                f"[Inlet] 🔍 Native tool output detected in assistant message.",
                                event_call=__event_call__,
                            )

                        # Extract the final answer (after last tool call metadata)
                        # Pattern: Matches escaped JSON strings like ""&quot;...&quot;"" followed by newlines
                        # We look for the last occurrence of such a pattern and take everything after it

                        # 1. Try matching the specific OpenWebUI tool output format: ""&quot;...&quot;""
                        # This regex finds the last end-quote of a tool output block
                        tool_output_pattern = r'""&quot;.*?&quot;""\s*'

                        # Find all matches
                        matches = list(
                            re.finditer(tool_output_pattern, content, re.DOTALL)
                        )

                        if matches:
                            # Get the end position of the last match
                            last_match_end = matches[-1].end()

                            # Everything after the last tool output is the final answer
                            final_answer = content[last_match_end:].strip()

                            if final_answer:
                                msg["content"] = (
                                    f"... [Tool outputs trimmed]\n{final_answer}"
                                )
                                trimmed_count += 1
                        else:
                            # Fallback: Try splitting on "Arguments:" if the new format isn't found
                            # (Preserving backward compatibility or different model behaviors)
                            parts = re.split(r"(?:Arguments:\s*\{[^}]+\})\n+", content)
                            if len(parts) > 1:
                                final_answer = parts[-1].strip()
                                if final_answer:
                                    msg["content"] = (
                                        f"... [Tool outputs trimmed]\n{final_answer}"
                                    )
                                    trimmed_count += 1

            if trimmed_count > 0 and self.valves.show_debug_log and __event_call__:
                await self._log(
                    f"[Inlet] ✂️ Trimmed {trimmed_count} tool output message(s).",
                    event_call=__event_call__,
                )

        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]

        # Extract system prompt for accurate token calculation
        # 1. For custom models: check DB (Models.get_model_by_id)
        # 2. For base models: check messages for role='system'
        system_prompt_content = None

        # Try to get from DB (custom model)
        try:
            model_id = body.get("model")
            if model_id:
                if self.valves.show_debug_log and __event_call__:
                    await self._log(
                        f"[Inlet] 🔍 Attempting DB lookup for model: {model_id}",
                        event_call=__event_call__,
                    )

                # Clean model ID if needed (though get_model_by_id usually expects the full ID)
                model_obj = Models.get_model_by_id(model_id)

                if model_obj:
                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] ✅ Model found in DB: {model_obj.name} (ID: {model_obj.id})",
                            event_call=__event_call__,
                        )

                    if model_obj.params:
                        try:
                            params = model_obj.params
                            # Handle case where params is a JSON string
                            if isinstance(params, str):
                                params = json.loads(params)

                            # Handle dict or Pydantic object
                            if isinstance(params, dict):
                                system_prompt_content = params.get("system")
                            else:
                                # Assume Pydantic model or object
                                system_prompt_content = getattr(params, "system", None)

                            if system_prompt_content:
                                if self.valves.show_debug_log and __event_call__:
                                    await self._log(
                                        f"[Inlet] 📝 System prompt found in DB params ({len(system_prompt_content)} chars)",
                                        event_call=__event_call__,
                                    )
                            else:
                                if self.valves.show_debug_log and __event_call__:
                                    await self._log(
                                        f"[Inlet] ⚠️ 'system' key missing in model params",
                                        event_call=__event_call__,
                                    )
                        except Exception as e:
                            if self.valves.show_debug_log and __event_call__:
                                await self._log(
                                    f"[Inlet] ❌ Failed to parse model params: {e}",
                                    type="error",
                                    event_call=__event_call__,
                                )

                    else:
                        if self.valves.show_debug_log and __event_call__:
                            await self._log(
                                f"[Inlet] ⚠️ Model params are empty",
                                event_call=__event_call__,
                            )
                else:
                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] ❌ Model NOT found in DB",
                            type="warning",
                            event_call=__event_call__,
                        )

        except Exception as e:
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    f"[Inlet] ❌ Error fetching system prompt from DB: {e}",
                    type="error",
                    event_call=__event_call__,
                )
            if self.valves.debug_mode:
                print(f"[Inlet] Error fetching system prompt from DB: {e}")

        # Fall back to checking messages (base model or already included)
        if not system_prompt_content:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt_content = msg.get("content", "")
                    break

        # Build system_prompt_msg for token calculation
        system_prompt_msg = None
        if system_prompt_content:
            system_prompt_msg = {"role": "system", "content": system_prompt_content}
            if self.valves.debug_mode:
                print(
                    f"[Inlet] Found system prompt ({len(system_prompt_content)} chars). Including in budget."
                )

        # Log message statistics (Moved here to include extracted system prompt)
        if self.valves.show_debug_log and __event_call__:
            try:
                msg_stats = {
                    "user": 0,
                    "assistant": 0,
                    "system": 0,
                    "total": len(messages),
                }
                for msg in messages:
                    role = msg.get("role", "unknown")
                    if role in msg_stats:
                        msg_stats[role] += 1

                # If system prompt was extracted from DB/Model but not in messages, count it
                if system_prompt_content:
                    # Check if it's already counted (i.e., was in messages)
                    is_in_messages = any(m.get("role") == "system" for m in messages)
                    if not is_in_messages:
                        msg_stats["system"] += 1
                        msg_stats["total"] += 1

                stats_str = f"Total: {msg_stats['total']} | User: {msg_stats['user']} | Assistant: {msg_stats['assistant']} | System: {msg_stats['system']}"
                await self._log(
                    f"[Inlet] Message Stats: {stats_str}", event_call=__event_call__
                )
            except Exception as e:
                print(f"[Inlet] Error logging message stats: {e}")

        if not chat_id:
            await self._log(
                "[Inlet] ❌ Missing chat_id in metadata, skipping compression",
                type="error",
                event_call=__event_call__,
            )
            return body

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Inlet] Chat ID: {chat_id}\n[Inlet] Received {len(messages)} messages",
                event_call=__event_call__,
            )

        # Record the target compression progress for the original messages, for use in outlet
        # Target is to compress up to the (total - keep_last) message
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        await self._log(
            f"[Inlet] Recorded target compression progress: {target_compressed_count}",
            event_call=__event_call__,
        )

        # Load summary record
        summary_record = await asyncio.to_thread(self._load_summary_record, chat_id)

        # Calculate effective_keep_first to ensure all system messages are protected
        last_system_index = -1
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                last_system_index = i

        effective_keep_first = max(self.valves.keep_first, last_system_index + 1)

        final_messages = []

        if summary_record:
            # Summary exists, build view: [Head] + [Summary Message] + [Tail]
            # Tail is all messages after the last compression point
            compressed_count = summary_record.compressed_message_count

            # Ensure compressed_count is reasonable
            if compressed_count > len(messages):
                compressed_count = max(0, len(messages) - self.valves.keep_last)

            # 1. Head messages (Keep First)
            head_messages = []
            if effective_keep_first > 0:
                head_messages = messages[:effective_keep_first]

            # 2. Summary message (Inserted as User message)
            summary_content = (
                f"【System Prompt: The following is a summary of the historical conversation, provided for context only. Do not reply to the summary content itself; answer the subsequent latest questions directly.】\n\n"
                f"{summary_record.summary}\n\n"
                f"---\n"
                f"Below is the recent conversation:"
            )
            summary_msg = {"role": "assistant", "content": summary_content}

            # 3. Tail messages (Tail) - All messages starting from the last compression point
            # Note: Must ensure head messages are not duplicated
            start_index = max(compressed_count, effective_keep_first)
            tail_messages = messages[start_index:]

            if self.valves.show_debug_log and __event_call__:
                tail_preview = [
                    f"{i + start_index}: [{m.get('role')}] {m.get('content', '')[:30]}..."
                    for i, m in enumerate(tail_messages)
                ]
                await self._log(
                    f"[Inlet] 📜 Tail Messages (Start Index: {start_index}): {tail_preview}",
                    event_call=__event_call__,
                )

            # --- Preflight Check & Budgeting (Simplified) ---

            # Assemble candidate messages (for output)
            candidate_messages = head_messages + [summary_msg] + tail_messages

            # Prepare messages for token calculation (include system prompt if missing)
            calc_messages = candidate_messages
            if system_prompt_msg:
                # Check if system prompt is already in head_messages
                is_in_head = any(m.get("role") == "system" for m in head_messages)
                if not is_in_head:
                    calc_messages = [system_prompt_msg] + candidate_messages

            # Get max context limit
            model = self._clean_model_id(body.get("model"))
            thresholds = self._get_model_thresholds(model)
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            # Calculate total tokens
            total_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, calc_messages
            )

            # Preflight Check Log
            await self._log(
                f"[Inlet] 🔎 Preflight Check: {total_tokens}t / {max_context_tokens}t ({(total_tokens/max_context_tokens*100):.1f}%)",
                event_call=__event_call__,
            )

            # If over budget, reduce history (Keep Last)
            if total_tokens > max_context_tokens:
                await self._log(
                    f"[Inlet] ⚠️ Candidate prompt ({total_tokens} Tokens) exceeds limit ({max_context_tokens}). Reducing history...",
                    type="warning",
                    event_call=__event_call__,
                )

                # Dynamically remove messages from the start of tail_messages
                # Always try to keep at least the last message (usually user input)
                while total_tokens > max_context_tokens and len(tail_messages) > 1:
                    # Strategy 1: Structure-Aware Assistant Trimming
                    # Retain: Headers (#), First Line, Last Line. Collapse the rest.
                    target_msg = None
                    target_idx = -1

                    # Find the oldest assistant message that is long and not yet trimmed
                    for i, msg in enumerate(tail_messages):
                        # Skip the last message (usually user input, protect it)
                        if i == len(tail_messages) - 1:
                            break

                        if msg.get("role") == "assistant":
                            content = str(msg.get("content", ""))
                            is_trimmed = msg.get("metadata", {}).get(
                                "is_trimmed", False
                            )
                            # Only target messages that are reasonably long (> 200 chars)
                            if len(content) > 200 and not is_trimmed:
                                target_msg = msg
                                target_idx = i
                                break

                    # If found a suitable assistant message, apply structure-aware trimming
                    if target_msg:
                        content = str(target_msg.get("content", ""))
                        lines = content.split("\n")
                        kept_lines = []

                        # Logic: Keep headers, first non-empty line, last non-empty line
                        first_line_found = False
                        last_line_idx = -1

                        # Find last non-empty line index
                        for idx in range(len(lines) - 1, -1, -1):
                            if lines[idx].strip():
                                last_line_idx = idx
                                break

                        for idx, line in enumerate(lines):
                            stripped = line.strip()
                            if not stripped:
                                continue

                            # Keep headers (H1-H6, requires space after #)
                            if re.match(r"^#{1,6}\s+", stripped):
                                kept_lines.append(line)
                                continue

                            # Keep first non-empty line
                            if not first_line_found:
                                kept_lines.append(line)
                                first_line_found = True
                                # Add placeholder if there's more content coming
                                if idx < last_line_idx:
                                    kept_lines.append("\n... [Content collapsed] ...\n")
                                continue

                            # Keep last non-empty line
                            if idx == last_line_idx:
                                kept_lines.append(line)
                                continue

                        # Update message content
                        new_content = "\n".join(kept_lines)

                        # Safety check: If trimming didn't save much (e.g. mostly headers), force drop
                        if len(new_content) > len(content) * 0.8:
                            # Fallback to drop if structure preservation is too verbose
                            pass
                        else:
                            target_msg["content"] = new_content
                            if "metadata" not in target_msg:
                                target_msg["metadata"] = {}
                            target_msg["metadata"]["is_trimmed"] = True

                            # Calculate token reduction
                            old_tokens = self._count_tokens(content)
                            new_tokens = self._count_tokens(target_msg["content"])
                            diff = old_tokens - new_tokens
                            total_tokens -= diff

                            if self.valves.show_debug_log and __event_call__:
                                await self._log(
                                    f"[Inlet] 📉 Structure-trimmed Assistant message. Saved: {diff} tokens.",
                                    event_call=__event_call__,
                                )
                            continue

                    # Strategy 2: Fallback - Drop Oldest Message Entirely (FIFO)
                    # (User requested to remove progressive trimming for other cases)
                    dropped = tail_messages.pop(0)
                    dropped_tokens = self._count_tokens(str(dropped.get("content", "")))
                    total_tokens -= dropped_tokens

                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] 🗑️ Dropped message from history to fit context. Role: {dropped.get('role')}, Tokens: {dropped_tokens}",
                            event_call=__event_call__,
                        )

                # Re-assemble
                candidate_messages = head_messages + [summary_msg] + tail_messages

                await self._log(
                    f"[Inlet] ✂️ History reduced. New total: {total_tokens} Tokens (Tail size: {len(tail_messages)})",
                    event_call=__event_call__,
                )

            final_messages = candidate_messages

            # Calculate detailed token stats for logging
            system_tokens = (
                self._count_tokens(system_prompt_msg.get("content", ""))
                if system_prompt_msg
                else 0
            )
            head_tokens = self._calculate_messages_tokens(head_messages)
            summary_tokens = self._count_tokens(summary_content)
            tail_tokens = self._calculate_messages_tokens(tail_messages)

            system_info = (
                f"System({system_tokens}t)" if system_prompt_msg else "System(0t)"
            )

            total_section_tokens = (
                system_tokens + head_tokens + summary_tokens + tail_tokens
            )

            await self._log(
                f"[Inlet] Applied summary: {system_info} + Head({len(head_messages)} msg, {head_tokens}t) + Summary({summary_tokens}t) + Tail({len(tail_messages)} msg, {tail_tokens}t) = Total({total_section_tokens}t)",
                type="success",
                event_call=__event_call__,
            )

            # Prepare status message (Context Usage format)
            if max_context_tokens > 0:
                usage_ratio = total_section_tokens / max_context_tokens
                status_msg = f"Context Usage (Estimated): {total_section_tokens} / {max_context_tokens} Tokens ({usage_ratio*100:.1f}%)"
                if usage_ratio > 0.9:
                    status_msg += " | ⚠️ High Usage"
            else:
                status_msg = f"Loaded historical summary (Hidden {compressed_count} historical messages)"

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": status_msg,
                            "done": True,
                        },
                    }
                )

            # Emit debug log to frontend (Keep the structured log as well)
            await self._emit_debug_log(
                __event_call__,
                chat_id,
                len(messages),
                len(final_messages),
                len(summary_record.summary),
                self.valves.keep_first,
                self.valves.keep_last,
            )
        else:
            # No summary, use original messages
            # But still need to check budget!
            final_messages = messages

            # Include system prompt in calculation
            calc_messages = final_messages
            if system_prompt_msg:
                is_in_messages = any(m.get("role") == "system" for m in final_messages)
                if not is_in_messages:
                    calc_messages = [system_prompt_msg] + final_messages

            # Get max context limit
            model = self._clean_model_id(body.get("model"))
            thresholds = self._get_model_thresholds(model)
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            total_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, calc_messages
            )

            if total_tokens > max_context_tokens:
                await self._log(
                    f"[Inlet] ⚠️ Original messages ({total_tokens} Tokens) exceed limit ({max_context_tokens}). Reducing history...",
                    type="warning",
                    event_call=__event_call__,
                )

                # Dynamically remove messages from the start
                # We'll respect effective_keep_first to protect system prompts

                start_trim_index = effective_keep_first

                while (
                    total_tokens > max_context_tokens
                    and len(final_messages)
                    > start_trim_index + 1  # Keep at least 1 message after keep_first
                ):
                    dropped = final_messages.pop(start_trim_index)
                    total_tokens -= self._count_tokens(str(dropped.get("content", "")))

                await self._log(
                    f"[Inlet] ✂️ Messages reduced. New total: {total_tokens} Tokens",
                    event_call=__event_call__,
                )

            # Send status notification (Context Usage format)
            if __event_emitter__:
                status_msg = f"Context Usage (Estimated): {total_tokens} / {max_context_tokens} Tokens"
                if max_context_tokens > 0:
                    usage_ratio = total_tokens / max_context_tokens
                    status_msg += f" ({usage_ratio*100:.1f}%)"
                    if usage_ratio > 0.9:
                        status_msg += " | ⚠️ High Usage"

                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": status_msg,
                            "done": True,
                        },
                    }
                )

        body["messages"] = final_messages

        await self._log(
            f"[Inlet] Final send: {len(body['messages'])} messages\n{'='*60}\n",
            event_call=__event_call__,
        )

        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        Executed after the LLM response is complete.
        Calculates Token count in the background and triggers summary generation (does not block current response, does not affect content output).
        """
        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]
        if not chat_id:
            await self._log(
                "[Outlet] ❌ Missing chat_id in metadata, skipping compression",
                type="error",
                event_call=__event_call__,
            )
            return body
        model = body.get("model") or ""

        # Calculate target compression progress directly
        # Assuming body['messages'] in outlet contains the full history (including new response)
        messages = body.get("messages", [])
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Outlet] Chat ID: {chat_id}\n[Outlet] Response complete\n[Outlet] Calculated target compression progress: {target_compressed_count} (Messages: {len(messages)})",
                event_call=__event_call__,
            )

        # Process Token calculation and summary generation asynchronously in the background (do not wait for completion, do not affect output)
        asyncio.create_task(
            self._check_and_generate_summary_async(
                chat_id,
                model,
                body,
                __user__,
                target_compressed_count,
                __event_emitter__,
                __event_call__,
            )
        )

        await self._log(
            f"[Outlet] Background processing started\n{'='*60}\n",
            event_call=__event_call__,
        )

        return body

    async def _check_and_generate_summary_async(
        self,
        chat_id: str,
        model: str,
        body: dict,
        user_data: Optional[dict],
        target_compressed_count: Optional[int],
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        Background processing: Calculates Token count and generates summary (does not block response).
        """
        try:
            messages = body.get("messages", [])

            # Get threshold configuration for current model
            thresholds = self._get_model_thresholds(model)
            compression_threshold_tokens = thresholds.get(
                "compression_threshold_tokens", self.valves.compression_threshold_tokens
            )

            await self._log(
                f"\n[🔍 Background Calculation] Starting Token count...",
                event_call=__event_call__,
            )

            # Calculate Token count in a background thread
            current_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, messages
            )

            await self._log(
                f"[🔍 Background Calculation] Token count: {current_tokens}",
                event_call=__event_call__,
            )

            # Check if compression is needed
            if current_tokens >= compression_threshold_tokens:
                await self._log(
                    f"[🔍 Background Calculation] ⚡ Compression threshold triggered (Token: {current_tokens} >= {compression_threshold_tokens})",
                    type="warning",
                    event_call=__event_call__,
                )

                # Proceed to generate summary
                await self._generate_summary_async(
                    messages,
                    chat_id,
                    body,
                    user_data,
                    target_compressed_count,
                    __event_emitter__,
                    __event_call__,
                )
            else:
                await self._log(
                    f"[🔍 Background Calculation] Compression threshold not reached (Token: {current_tokens} < {compression_threshold_tokens})",
                    event_call=__event_call__,
                )

        except Exception as e:
            await self._log(
                f"[🔍 Background Calculation] ❌ Error: {str(e)}",
                type="error",
                event_call=__event_call__,
            )

    def _clean_model_id(self, model_id: Optional[str]) -> Optional[str]:
        """Cleans the model ID by removing whitespace and quotes."""
        if not model_id:
            return None
        cleaned = model_id.strip().strip('"').strip("'")
        return cleaned if cleaned else None

    async def _generate_summary_async(
        self,
        messages: list,
        chat_id: str,
        body: dict,
        user_data: Optional[dict],
        target_compressed_count: Optional[int],
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        Generates summary asynchronously (runs in background, does not block response).
        Logic:
        1. Extract middle messages (remove keep_first and keep_last).
        2. Check Token limit, if exceeding max_context_tokens, remove from the head of middle messages.
        3. Generate summary for the remaining middle messages.
        """
        try:
            await self._log(
                f"\n[🤖 Async Summary Task] Starting...", event_call=__event_call__
            )

            # 1. Get target compression progress
            # If target_compressed_count is not passed (should not happen with new logic), estimate it
            if target_compressed_count is None:
                target_compressed_count = max(0, len(messages) - self.valves.keep_last)
                await self._log(
                    f"[🤖 Async Summary Task] ⚠️ target_compressed_count is None, estimating: {target_compressed_count}",
                    type="warning",
                    event_call=__event_call__,
                )

            # 2. Determine the range of messages to compress (Middle)
            start_index = self.valves.keep_first
            end_index = len(messages) - self.valves.keep_last
            if self.valves.keep_last == 0:
                end_index = len(messages)

            # Ensure indices are valid
            if start_index >= end_index:
                await self._log(
                    f"[🤖 Async Summary Task] Middle messages empty (Start: {start_index}, End: {end_index}), skipping",
                    event_call=__event_call__,
                )
                return

            middle_messages = messages[start_index:end_index]
            tail_preview_msgs = messages[end_index:]

            if self.valves.show_debug_log and __event_call__:
                middle_preview = [
                    f"{i + start_index}: [{m.get('role')}] {m.get('content', '')[:20]}..."
                    for i, m in enumerate(middle_messages[:3])
                ]
                tail_preview = [
                    f"{i + end_index}: [{m.get('role')}] {m.get('content', '')[:20]}..."
                    for i, m in enumerate(tail_preview_msgs)
                ]
                await self._log(
                    f"[🤖 Async Summary Task] 📊 Boundary Check:\n"
                    f"  - Middle (Compressing): {len(middle_messages)} msgs (Indices {start_index}-{end_index-1}) -> Preview: {middle_preview}\n"
                    f"  - Tail (Keeping): {len(tail_preview_msgs)} msgs (Indices {end_index}-End) -> Preview: {tail_preview}",
                    event_call=__event_call__,
                )

            # 3. Check Token limit and truncate (Max Context Truncation)
            # [Optimization] Use the summary model's (if any) threshold to decide how many middle messages can be processed
            # This allows using a long-window model (like gemini-flash) to compress history exceeding the current model's window
            summary_model_id = self._clean_model_id(
                self.valves.summary_model
            ) or self._clean_model_id(body.get("model"))

            if not summary_model_id:
                await self._log(
                    "[🤖 Async Summary Task] ⚠️ Summary model does not exist, skipping compression",
                    type="warning",
                    event_call=__event_call__,
                )
                return

            thresholds = self._get_model_thresholds(summary_model_id)
            # Note: Using the summary model's max context limit here
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            await self._log(
                f"[🤖 Async Summary Task] Using max limit for model {summary_model_id}: {max_context_tokens} Tokens",
                event_call=__event_call__,
            )

            # Calculate tokens for middle messages only (plus buffer for prompt)
            # We only send middle_messages to the summary model, so we shouldn't count the full history against its limit.
            middle_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, middle_messages
            )
            # Add buffer for prompt and output (approx 2000 tokens)
            estimated_input_tokens = middle_tokens + 2000

            if estimated_input_tokens > max_context_tokens:
                excess_tokens = estimated_input_tokens - max_context_tokens
                await self._log(
                    f"[🤖 Async Summary Task] ⚠️ Middle messages ({middle_tokens} Tokens) + Buffer exceed summary model limit ({max_context_tokens}), need to remove approx {excess_tokens} Tokens",
                    type="warning",
                    event_call=__event_call__,
                )

                # Remove from the head of middle_messages
                removed_tokens = 0
                removed_count = 0

                while removed_tokens < excess_tokens and middle_messages:
                    msg_to_remove = middle_messages.pop(0)
                    msg_tokens = self._count_tokens(
                        str(msg_to_remove.get("content", ""))
                    )
                    removed_tokens += msg_tokens
                    removed_count += 1

                await self._log(
                    f"[🤖 Async Summary Task] Removed {removed_count} messages, totaling {removed_tokens} Tokens",
                    event_call=__event_call__,
                )

            if not middle_messages:
                await self._log(
                    f"[🤖 Async Summary Task] Middle messages empty after truncation, skipping summary generation",
                    event_call=__event_call__,
                )
                return

            # 4. Build conversation text
            conversation_text = self._format_messages_for_summary(middle_messages)

            # 5. Call LLM to generate new summary
            # Note: previous_summary is not passed here because old summary (if any) is already included in middle_messages

            # Send status notification for starting summary generation
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Generating context summary in background...",
                            "done": False,
                        },
                    }
                )

            new_summary = await self._call_summary_llm(
                None,
                conversation_text,
                {**body, "model": summary_model_id},
                user_data,
                __event_call__,
            )

            if not new_summary:
                await self._log(
                    "[🤖 Async Summary Task] ⚠️ Summary generation returned empty result, skipping save",
                    type="warning",
                    event_call=__event_call__,
                )
                return

            # 6. Save new summary
            await self._log(
                "[Optimization] Saving summary in a background thread to avoid blocking the event loop.",
                event_call=__event_call__,
            )

            await asyncio.to_thread(
                self._save_summary, chat_id, new_summary, target_compressed_count
            )

            # Send completion status notification
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Context summary updated (Compressed {len(middle_messages)} messages)",
                            "done": True,
                        },
                    }
                )

            await self._log(
                f"[🤖 Async Summary Task] ✅ Complete! New summary length: {len(new_summary)} characters",
                type="success",
                event_call=__event_call__,
            )
            await self._log(
                f"[🤖 Async Summary Task] Progress update: Compressed up to original message {target_compressed_count}",
                event_call=__event_call__,
            )

            # --- Token Usage Status Notification ---
            if self.valves.show_token_usage_status and __event_emitter__:
                try:
                    # 1. Fetch System Prompt (DB fallback)
                    system_prompt_msg = None
                    model_id = body.get("model")
                    if model_id:
                        try:
                            model_obj = Models.get_model_by_id(model_id)
                            if model_obj and model_obj.params:
                                params = model_obj.params
                                if isinstance(params, str):
                                    params = json.loads(params)
                                if isinstance(params, dict):
                                    sys_content = params.get("system")
                                else:
                                    sys_content = getattr(params, "system", None)

                                if sys_content:
                                    system_prompt_msg = {
                                        "role": "system",
                                        "content": sys_content,
                                    }
                        except Exception:
                            pass  # Ignore DB errors here, best effort

                    # 2. Calculate Effective Keep First
                    last_system_index = -1
                    for i, msg in enumerate(messages):
                        if msg.get("role") == "system":
                            last_system_index = i
                    effective_keep_first = max(
                        self.valves.keep_first, last_system_index + 1
                    )

                    # 3. Construct Next Context
                    # Head
                    head_msgs = (
                        messages[:effective_keep_first]
                        if effective_keep_first > 0
                        else []
                    )

                    # Summary
                    summary_content = (
                        f"【System Prompt: The following is a summary of the historical conversation, provided for context only. Do not reply to the summary content itself; answer the subsequent latest questions directly.】\n\n"
                        f"{new_summary}\n\n"
                        f"---\n"
                        f"Below is the recent conversation:"
                    )
                    summary_msg = {"role": "assistant", "content": summary_content}

                    # Tail (using target_compressed_count which is what we just compressed up to)
                    # Note: target_compressed_count is the index *after* the last compressed message?
                    # In _generate_summary_async, target_compressed_count is passed in.
                    # It represents the number of messages to be covered by summary (excluding keep_last).
                    # So tail starts at max(target_compressed_count, effective_keep_first).
                    start_index = max(target_compressed_count, effective_keep_first)
                    tail_msgs = messages[start_index:]

                    # Assemble
                    next_context = head_msgs + [summary_msg] + tail_msgs

                    # Inject system prompt if needed
                    if system_prompt_msg:
                        is_in_head = any(m.get("role") == "system" for m in head_msgs)
                        if not is_in_head:
                            next_context = [system_prompt_msg] + next_context

                    # 4. Calculate Tokens
                    token_count = self._calculate_messages_tokens(next_context)

                    # 5. Get Thresholds & Calculate Ratio
                    model = self._clean_model_id(body.get("model"))
                    thresholds = self._get_model_thresholds(model)
                    max_context_tokens = thresholds.get(
                        "max_context_tokens", self.valves.max_context_tokens
                    )

                    # 6. Emit Status
                    status_msg = f"Context Summary Updated: {token_count} / {max_context_tokens} Tokens"
                    if max_context_tokens > 0:
                        ratio = (token_count / max_context_tokens) * 100
                        status_msg += f" ({ratio:.1f}%)"
                        if ratio > 90.0:
                            status_msg += " | ⚠️ High Usage"

                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": status_msg,
                                "done": True,
                            },
                        }
                    )
                except Exception as e:
                    await self._log(
                        f"[Status] Error calculating tokens: {e}",
                        type="error",
                        event_call=__event_call__,
                    )

        except Exception as e:
            await self._log(
                f"[🤖 Async Summary Task] ❌ Error: {str(e)}",
                type="error",
                event_call=__event_call__,
            )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Summary Error: {str(e)[:100]}...",
                            "done": True,
                        },
                    }
                )

            import traceback

            traceback.print_exc()

    def _format_messages_for_summary(self, messages: list) -> str:
        """Formats messages for summarization."""
        formatted = []
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Handle multimodal content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                content = " ".join(text_parts)

            # Handle role name
            role_name = {"user": "User", "assistant": "Assistant"}.get(role, role)

            # Limit length of each message to avoid excessive length
            if len(content) > 500:
                content = content[:500] + "..."

            formatted.append(f"[{i}] {role_name}: {content}")

        return "\n\n".join(formatted)

    async def _call_summary_llm(
        self,
        previous_summary: Optional[str],
        new_conversation_text: str,
        body: dict,
        user_data: dict,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> str:
        """
        Calls the LLM to generate a summary using Open WebUI's built-in method.
        """
        await self._log(
            f"[🤖 LLM Call] Using Open WebUI's built-in method",
            event_call=__event_call__,
        )

        # Build summary prompt (Optimized)
        summary_prompt = f"""
You are a professional conversation context compression expert. Your task is to create a high-fidelity summary of the following conversation content.
This conversation may contain previous summaries (as system messages or text) and subsequent conversation content.

### Core Objectives
1.  **Comprehensive Summary**: Concisely summarize key information, user intent, and assistant responses from the conversation.
2.  **De-noising**: Remove greetings, repetitions, confirmations, and other non-essential information.
3.  **Key Retention**:
    *   **Code snippets, commands, and technical parameters must be preserved verbatim. Do not modify or generalize them.**
    *   User intent, core requirements, decisions, and action items must be clearly preserved.
4.  **Coherence**: The generated summary should be a cohesive whole that can replace the original conversation as context.
5.  **Detailed Record**: Since length is permitted, please preserve details, reasoning processes, and nuances of multi-turn interactions as much as possible, rather than just high-level generalizations.

### Output Requirements
*   **Format**: Structured text, logically clear.
*   **Language**: Consistent with the conversation language (usually English).
*   **Length**: Strictly control within {self.valves.max_summary_tokens} Tokens.
*   **Strictly Forbidden**: Do not output "According to the conversation...", "The summary is as follows..." or similar filler. Output the summary content directly.

### Suggested Summary Structure
*   **Current Goal/Topic**: A one-sentence summary of the problem currently being solved.
*   **Key Information & Context**:
    *   Confirmed facts/parameters.
    *   **Code/Technical Details** (Wrap in code blocks).
*   **Progress & Conclusions**: Completed steps and reached consensus.
*   **Action Items/Next Steps**: Clear follow-up actions.

---
{new_conversation_text}
---

Based on the content above, generate the summary:
"""
        # Determine the model to use
        model = self._clean_model_id(self.valves.summary_model) or self._clean_model_id(
            body.get("model")
        )

        if not model:
            await self._log(
                "[🤖 LLM Call] ⚠️ Summary model does not exist, skipping summary generation",
                type="warning",
                event_call=__event_call__,
            )
            return ""

        await self._log(f"[🤖 LLM Call] Model: {model}", event_call=__event_call__)

        # Build payload
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": summary_prompt}],
            "stream": False,
            "max_tokens": self.valves.max_summary_tokens,
            "temperature": self.valves.summary_temperature,
        }

        try:
            # Get user object
            user_id = user_data.get("id") if user_data else None
            if not user_id:
                raise ValueError("Could not get user ID")

            # [Optimization] Get user object in a background thread to avoid blocking the event loop.
            await self._log(
                "[Optimization] Getting user object in a background thread to avoid blocking the event loop.",
                event_call=__event_call__,
            )
            user = await asyncio.to_thread(Users.get_user_by_id, user_id)

            if not user:
                raise ValueError(f"Could not find user: {user_id}")

            await self._log(
                f"[🤖 LLM Call] User: {user.email}\n[🤖 LLM Call] Sending request...",
                event_call=__event_call__,
            )

            # Create Request object
            request = Request(scope={"type": "http", "app": webui_app})

            # Call generate_chat_completion
            response = await generate_chat_completion(request, payload, user)

            if not response or "choices" not in response or not response["choices"]:
                raise ValueError("LLM response format incorrect or empty")

            summary = response["choices"][0]["message"]["content"].strip()

            await self._log(
                f"[🤖 LLM Call] ✅ Successfully received summary",
                type="success",
                event_call=__event_call__,
            )

            return summary

        except Exception as e:
            error_msg = str(e)
            # Handle specific error messages
            if "Model not found" in error_msg:
                error_message = f"Summary model '{model}' not found."
            else:
                error_message = f"Summary LLM Error ({model}): {error_msg}"
            if not self.valves.summary_model:
                error_message += (
                    "\n[Hint] You did not specify a summary_model, so the filter attempted to use the current conversation's model. "
                    "If this is a pipeline (Pipe) model or an incompatible model, please specify a compatible summary model (e.g., 'gemini-2.5-flash') in the configuration."
                )

            await self._log(
                f"[🤖 LLM Call] ❌ {error_message}",
                type="error",
                event_call=__event_call__,
            )

            raise Exception(error_message)
