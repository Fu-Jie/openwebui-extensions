"""
title: Async Context Compression
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
description: Reduces token consumption in long conversations while maintaining coherence through intelligent summarization and message compression.
version: 1.1.0
openwebui_id: b1655bc8-6de9-4cad-8cb5-a6f7829a02ce
license: MIT

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
import asyncio
import json
import hashlib
import time

# Open WebUI built-in imports
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from fastapi.requests import Request
from open_webui.main import app as webui_app

# Open WebUI internal database (re-use shared connection)
from open_webui.internal.db import engine as owui_engine
from open_webui.internal.db import Session as owui_Session
from open_webui.internal.db import Base as owui_Base

# Try to import tiktoken
try:
    import tiktoken
except ImportError:
    tiktoken = None

# Database imports
from sqlalchemy import Column, String, Text, DateTime, Integer, inspect
from datetime import datetime


class ChatSummary(owui_Base):
    """Chat Summary Storage Table"""

    __tablename__ = "chat_summary"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    compressed_message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Filter:
    def __init__(self):
        self.valves = self.Valves()
        self._db_engine = owui_engine
        self._SessionLocal = owui_Session
        self.temp_state = {}  # Used to pass temporary data between inlet and outlet
        self._init_database()

    def _init_database(self):
        """Initializes the database table using Open WebUI's shared connection."""
        try:
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

    def _save_summary(self, chat_id: str, summary: str, compressed_count: int):
        """Saves the summary to the database."""
        try:
            with self._SessionLocal() as session:
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
            with self._SessionLocal() as session:
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

    def _inject_summary_to_first_message(self, message: dict, summary: str) -> dict:
        """Injects the summary into the first message (prepended to content)."""
        content = message.get("content", "")
        summary_block = f"【Historical Conversation Summary】\n{summary}\n\n---\nBelow is the recent conversation:\n\n"

        # Handle different content types
        if isinstance(content, list):  # Multimodal content
            # Find the first text part and insert the summary before it
            new_content = []
            summary_inserted = False

            for part in content:
                if (
                    isinstance(part, dict)
                    and part.get("type") == "text"
                    and not summary_inserted
                ):
                    # Prepend summary to the first text part
                    new_content.append(
                        {"type": "text", "text": summary_block + part.get("text", "")}
                    )
                    summary_inserted = True
                else:
                    new_content.append(part)

            # If no text part, insert at the beginning
            if not summary_inserted:
                new_content.insert(0, {"type": "text", "text": summary_block})

            message["content"] = new_content

        elif isinstance(content, str):  # Plain text
            message["content"] = summary_block + content

        return message

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        Executed before sending to the LLM.
        Compression Strategy: Only responsible for injecting existing summaries, no Token calculation.
        """
        messages = body.get("messages", [])
        chat_id = __metadata__["chat_id"]

        if self.valves.debug_mode:
            print(f"\n{'='*60}")
            print(f"[Inlet] Chat ID: {chat_id}")
            print(f"[Inlet] Received {len(messages)} messages")

        # Record the target compression progress for the original messages, for use in outlet
        # Target is to compress up to the (total - keep_last) message
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        # [Optimization] Simple state cleanup check
        if chat_id in self.temp_state:
            if self.valves.debug_mode:
                print(
                    f"[Inlet] ⚠️ Overwriting unconsumed old state (Chat ID: {chat_id})"
                )

        self.temp_state[chat_id] = target_compressed_count

        if self.valves.debug_mode:
            print(
                f"[Inlet] Recorded target compression progress: {target_compressed_count}"
            )

        # Load summary record
        summary_record = await asyncio.to_thread(self._load_summary_record, chat_id)

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
            if self.valves.keep_first > 0:
                head_messages = messages[: self.valves.keep_first]

            # 2. Summary message (Inserted as User message)
            summary_content = (
                f"【System Prompt: The following is a summary of the historical conversation, provided for context only. Do not reply to the summary content itself; answer the subsequent latest questions directly.】\n\n"
                f"{summary_record.summary}\n\n"
                f"---\n"
                f"Below is the recent conversation:"
            )
            summary_msg = {"role": "user", "content": summary_content}

            # 3. Tail messages (Tail) - All messages starting from the last compression point
            # Note: Must ensure head messages are not duplicated
            start_index = max(compressed_count, self.valves.keep_first)
            tail_messages = messages[start_index:]

            final_messages = head_messages + [summary_msg] + tail_messages

            # Send status notification
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Loaded historical summary (Hidden {compressed_count} historical messages)",
                            "done": True,
                        },
                    }
                )

            if self.valves.debug_mode:
                print(
                    f"[Inlet] Applied summary: Head({len(head_messages)}) + Summary + Tail({len(tail_messages)})"
                )
        else:
            # No summary, use original messages
            final_messages = messages

        body["messages"] = final_messages

        if self.valves.debug_mode:
            print(f"[Inlet] Final send: {len(body['messages'])} messages")
            print(f"{'='*60}\n")

        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        Executed after the LLM response is complete.
        Calculates Token count in the background and triggers summary generation (does not block current response, does not affect content output).
        """
        chat_id = __metadata__["chat_id"]
        model = body.get("model", "gpt-3.5-turbo")

        if self.valves.debug_mode:
            print(f"\n{'='*60}")
            print(f"[Outlet] Chat ID: {chat_id}")
            print(f"[Outlet] Response complete")

        # Process Token calculation and summary generation asynchronously in the background (do not wait for completion, do not affect output)
        asyncio.create_task(
            self._check_and_generate_summary_async(
                chat_id, model, body, __user__, __event_emitter__
            )
        )

        if self.valves.debug_mode:
            print(f"[Outlet] Background processing started")
            print(f"{'='*60}\n")

        return body

    async def _check_and_generate_summary_async(
        self,
        chat_id: str,
        model: str,
        body: dict,
        user_data: Optional[dict],
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
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

            if self.valves.debug_mode:
                print(f"\n[🔍 Background Calculation] Starting Token count...")

            # Calculate Token count in a background thread
            current_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, messages
            )

            if self.valves.debug_mode:
                print(f"[🔍 Background Calculation] Token count: {current_tokens}")

            # Check if compression is needed
            if current_tokens >= compression_threshold_tokens:
                if self.valves.debug_mode:
                    print(
                        f"[🔍 Background Calculation] ⚡ Compression threshold triggered (Token: {current_tokens} >= {compression_threshold_tokens})"
                    )

                # Proceed to generate summary
                await self._generate_summary_async(
                    messages, chat_id, body, user_data, __event_emitter__
                )
            else:
                if self.valves.debug_mode:
                    print(
                        f"[🔍 Background Calculation] Compression threshold not reached (Token: {current_tokens} < {compression_threshold_tokens})"
                    )

        except Exception as e:
            print(f"[🔍 Background Calculation] ❌ Error: {str(e)}")

    async def _generate_summary_async(
        self,
        messages: list,
        chat_id: str,
        body: dict,
        user_data: Optional[dict],
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        Generates summary asynchronously (runs in background, does not block response).
        Logic:
        1. Extract middle messages (remove keep_first and keep_last).
        2. Check Token limit, if exceeding max_context_tokens, remove from the head of middle messages.
        3. Generate summary for the remaining middle messages.
        """
        try:
            if self.valves.debug_mode:
                print(f"\n[🤖 Async Summary Task] Starting...")

            # 1. Get target compression progress
            # Prioritize getting from temp_state (calculated by inlet). If unavailable (e.g., after restart), assume current is full history.
            target_compressed_count = self.temp_state.pop(chat_id, None)
            if target_compressed_count is None:
                target_compressed_count = max(0, len(messages) - self.valves.keep_last)
                if self.valves.debug_mode:
                    print(
                        f"[🤖 Async Summary Task] ⚠️ Could not get inlet state, estimating progress using current message count: {target_compressed_count}"
                    )

            # 2. Determine the range of messages to compress (Middle)
            start_index = self.valves.keep_first
            end_index = len(messages) - self.valves.keep_last
            if self.valves.keep_last == 0:
                end_index = len(messages)

            # Ensure indices are valid
            if start_index >= end_index:
                if self.valves.debug_mode:
                    print(
                        f"[🤖 Async Summary Task] Middle messages empty (Start: {start_index}, End: {end_index}), skipping"
                    )
                return

            middle_messages = messages[start_index:end_index]

            if self.valves.debug_mode:
                print(
                    f"[🤖 Async Summary Task] Middle messages to process: {len(middle_messages)}"
                )

            # 3. Check Token limit and truncate (Max Context Truncation)
            # [Optimization] Use the summary model's (if any) threshold to decide how many middle messages can be processed
            # This allows using a long-window model (like gemini-flash) to compress history exceeding the current model's window
            summary_model_id = self.valves.summary_model or body.get(
                "model", "gpt-3.5-turbo"
            )

            thresholds = self._get_model_thresholds(summary_model_id)
            # Note: Using the summary model's max context limit here
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            if self.valves.debug_mode:
                print(
                    f"[🤖 Async Summary Task] Using max limit for model {summary_model_id}: {max_context_tokens} Tokens"
                )

            # Calculate current total Tokens (using summary model for counting)
            total_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, messages
            )

            if total_tokens > max_context_tokens:
                excess_tokens = total_tokens - max_context_tokens
                if self.valves.debug_mode:
                    print(
                        f"[🤖 Async Summary Task] ⚠️ Total Tokens ({total_tokens}) exceed summary model limit ({max_context_tokens}), need to remove approx {excess_tokens} Tokens"
                    )

                # Remove from the head of middle_messages
                removed_tokens = 0
                removed_count = 0

                while removed_tokens < excess_tokens and middle_messages:
                    msg_to_remove = middle_messages.pop(0)
                    msg_tokens = self._count_tokens(str(msg_to_remove.get("content", "")))
                    removed_tokens += msg_tokens
                    removed_count += 1

                if self.valves.debug_mode:
                    print(
                        f"[🤖 Async Summary Task] Removed {removed_count} messages, totaling {removed_tokens} Tokens"
                    )

            if not middle_messages:
                if self.valves.debug_mode:
                    print(
                        f"[🤖 Async Summary Task] Middle messages empty after truncation, skipping summary generation"
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
                None, conversation_text, body, user_data
            )

            # 6. Save new summary
            if self.valves.debug_mode:
                print(
                    "[Optimization] Saving summary in a background thread to avoid blocking the event loop."
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

            if self.valves.debug_mode:
                print(
                    f"[🤖 Async Summary Task] ✅ Complete! New summary length: {len(new_summary)} characters"
                )
                print(
                    f"[🤖 Async Summary Task] Progress update: Compressed up to original message {target_compressed_count}"
                )

        except Exception as e:
            print(f"[🤖 Async Summary Task] ❌ Error: {str(e)}")
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
    ) -> str:
        """
        Calls the LLM to generate a summary using Open WebUI's built-in method.
        """
        if self.valves.debug_mode:
            print(f"[🤖 LLM Call] Using Open WebUI's built-in method")

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
        model = self.valves.summary_model or body.get("model", "")

        if self.valves.debug_mode:
            print(f"[🤖 LLM Call] Model: {model}")

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
            if self.valves.debug_mode:
                print(
                    "[Optimization] Getting user object in a background thread to avoid blocking the event loop."
                )
            user = await asyncio.to_thread(Users.get_user_by_id, user_id)

            if not user:
                raise ValueError(f"Could not find user: {user_id}")

            if self.valves.debug_mode:
                print(f"[🤖 LLM Call] User: {user.email}")
                print(f"[🤖 LLM Call] Sending request...")

            # Create Request object
            request = Request(scope={"type": "http", "app": webui_app})

            # Call generate_chat_completion
            response = await generate_chat_completion(request, payload, user)

            if not response or "choices" not in response or not response["choices"]:
                raise ValueError("LLM response format incorrect or empty")

            summary = response["choices"][0]["message"]["content"].strip()

            if self.valves.debug_mode:
                print(f"[🤖 LLM Call] ✅ Successfully received summary")

            return summary

        except Exception as e:
            error_message = f"Error occurred while calling LLM ({model}) to generate summary: {str(e)}"
            if not self.valves.summary_model:
                error_message += (
                    "\n[Hint] You did not specify a summary_model, so the filter attempted to use the current conversation's model. "
                    "If this is a pipeline (Pipe) model or an incompatible model, please specify a compatible summary model (e.g., 'gemini-2.5-flash') in the configuration."
                )

            if self.valves.debug_mode:
                print(f"[🤖 LLM Call] ❌ {error_message}")

            raise Exception(error_message)
