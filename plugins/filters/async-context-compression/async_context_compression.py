"""
title: Async Context Compression
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
description: Reduces token consumption in long conversations while maintaining coherence through intelligent summarization and message compression.
version: 1.4.1
openwebui_id: b1655bc8-6de9-4cad-8cb5-a6f7829a02ce
license: MIT

═══════════════════════════════════════════════════════════════════════════════
📌 What's new in 1.4.1
═══════════════════════════════════════════════════════════════════════════════

  ✅ Reverse-Unfolding Mechanism: Accurately reconstructs the expanded native tool-calling sequence during the outlet phase to permanently fix coordinate drift and missing summaries for long tool-based conversations.
  ✅ Safer Tool Trimming: Refactored `enable_tool_output_trimming` to strictly use atomic block groups for safe trimming, completely preventing JSON payload corruption.

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
  Description: When enabled and `function_calling: "native"` is active, collapses oversized native tool outputs (role="tool" messages exceeding ~1200 chars) to a short placeholder, reducing context size while preserving tool-call chain structure.

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
  Default: false
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
   ⚠ Image tokens are NOT calculated. Different models have vastly different image token costs
     (GPT-4o: 85-1105, Claude: ~1300, Gemini: ~258 per image). Plan your thresholds accordingly.

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

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union, Callable, Awaitable
import re
import asyncio
import json
import hashlib
import time
import contextlib
import logging
from copy import deepcopy
from functools import lru_cache

# Setup logger
logger = logging.getLogger(__name__)

SUMMARY_METADATA_SOURCE = "async_context_compression"

# Open WebUI built-in imports
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.models.models import Models
from fastapi.requests import Request
from open_webui.main import app as webui_app

try:
    from open_webui.models.chats import Chats
except ModuleNotFoundError:  # pragma: no cover - filter runs inside OpenWebUI
    Chats = None

try:
    from open_webui.models.chat_messages import ChatMessages
except ModuleNotFoundError:  # pragma: no cover - filter runs inside OpenWebUI
    ChatMessages = None

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
from datetime import datetime, timezone


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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


TRANSLATIONS = {
    "en-US": {
        "status_context_usage": "Context Usage (Estimated): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ High Usage",
        "status_loaded_summary": "Loaded historical summary (Hidden {count} historical messages)",
        "status_context_summary_updated": "Context Summary Updated: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "Generating context summary in background...",
        "status_summary_error": "Summary Error: {error}",
        "summary_prompt_prefix": "【Previous Summary: The following is a summary of the historical conversation, provided for context only. Do not reply to the summary content itself; answer the subsequent latest questions directly.】\n\n",
        "summary_prompt_suffix": "\n\n---\nBelow is the recent conversation:",
        "tool_trimmed": "... [Tool outputs trimmed]\n{content}",
        "content_collapsed": "\n... [Content collapsed] ...\n",
    },
    "zh-CN": {
        "status_context_usage": "上下文用量 (预估): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ 用量较高",
        "status_loaded_summary": "已加载历史总结 (隐藏了 {count} 条历史消息)",
        "status_context_summary_updated": "上下文总结已更新: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "正在后台生成上下文总结...",
        "status_summary_error": "总结生成错误: {error}",
        "summary_prompt_prefix": "【前情提要：以下是历史对话的总结，仅供上下文参考。请不要回复总结内容本身，直接回答之后最新的问题。】\n\n",
        "summary_prompt_suffix": "\n\n---\n以下是最近的对话：",
        "tool_trimmed": "... [工具输出已裁剪]\n{content}",
        "content_collapsed": "\n... [内容已折叠] ...\n",
    },
    "zh-HK": {
        "status_context_usage": "上下文用量 (預估): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ 用量較高",
        "status_loaded_summary": "已載入歷史總結 (隱藏了 {count} 條歷史訊息)",
        "status_context_summary_updated": "上下文總結已更新: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "正在後台生成上下文總結...",
        "status_summary_error": "總結生成錯誤: {error}",
        "summary_prompt_prefix": "【前情提要：以下是歷史對話的總結，僅供上下文參考。請不要回覆總結內容本身，直接回答之後最新的問題。】\n\n",
        "summary_prompt_suffix": "\n\n---\n以下是最近的對話：",
        "tool_trimmed": "... [工具輸出已裁剪]\n{content}",
        "content_collapsed": "\n... [內容已折疊] ...\n",
    },
    "zh-TW": {
        "status_context_usage": "上下文用量 (預估): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ 用量較高",
        "status_loaded_summary": "已載入歷史總結 (隱藏了 {count} 條歷史訊息)",
        "status_context_summary_updated": "上下文總結已更新: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "正在後台生成上下文總結...",
        "status_summary_error": "總結生成錯誤: {error}",
        "summary_prompt_prefix": "【前情提要：以下是歷史對話的總結，僅供上下文参考。請不要回覆總結內容本身，直接回答之後最新的問題。】\n\n",
        "summary_prompt_suffix": "\n\n---\n以下是最近的對話：",
        "tool_trimmed": "... [工具輸出已裁剪]\n{content}",
        "content_collapsed": "\n... [內容已折疊] ...\n",
    },
    "ja-JP": {
        "status_context_usage": "コンテキスト使用量 (推定): {tokens} / {max_tokens} トークン ({ratio}%)",
        "status_high_usage": " | ⚠️ 使用量高",
        "status_loaded_summary": "履歴の要約を読み込みました ({count} 件の履歴メッセージを非表示)",
        "status_context_summary_updated": "コンテキストの要約が更新されました: {tokens} / {max_tokens} トークン ({ratio}%)",
        "status_generating_summary": "バックグラウンドでコンテキスト要約を生成しています...",
        "status_summary_error": "要約エラー: {error}",
        "summary_prompt_prefix": "【これまでのあらすじ：以下は過去の会話の要約であり、コンテキストの参考としてのみ提供されます。要約の内容自体には返答せず、その後の最新の質問に直接答えてください。】\n\n",
        "summary_prompt_suffix": "\n\n---\n以下は最近の会話です：",
        "tool_trimmed": "... [ツールの出力をトリミングしました]\n{content}",
        "content_collapsed": "\n... [コンテンツが折りたたまれました] ...\n",
    },
    "ko-KR": {
        "status_context_usage": "컨텍스트 사용량 (예상): {tokens} / {max_tokens} 토큰 ({ratio}%)",
        "status_high_usage": " | ⚠️ 사용량 높음",
        "status_loaded_summary": "이전 요약 불러옴 ({count}개의 이전 메시지 숨김)",
        "status_context_summary_updated": "컨텍스트 요약 업데이트됨: {tokens} / {max_tokens} 토큰 ({ratio}%)",
        "status_generating_summary": "백그라운드에서 컨텍스트 요약 생성 중...",
        "status_summary_error": "요약 오류: {error}",
        "summary_prompt_prefix": "【이전 요약: 다음은 이전 대화의 요약이며 문맥 참고용으로만 제공됩니다. 요약 내용 자체에 답하지 말고 최신 질문에 직접 답하세요.】\n\n",
        "summary_prompt_suffix": "\n\n---\n다음은 최근 대화입니다:",
        "tool_trimmed": "... [도구 출력 잘림]\n{content}",
        "content_collapsed": "\n... [내용 접힘] ...\n",
    },
    "fr-FR": {
        "status_context_usage": "Utilisation du contexte (estimée) : {tokens} / {max_tokens} jetons ({ratio}%)",
        "status_high_usage": " | ⚠️ Utilisation élevée",
        "status_loaded_summary": "Résumé historique chargé ({count} messages d'historique masqués)",
        "status_context_summary_updated": "Résumé du contexte mis à jour : {tokens} / {max_tokens} jetons ({ratio}%)",
        "status_generating_summary": "Génération du résumé du contexte en arrière-plan...",
        "status_summary_error": "Erreur de résumé : {error}",
        "summary_prompt_prefix": "【Résumé précédent : Ce qui suit est un résumé de la conversation historique, fourni uniquement pour le contexte. Ne répondez pas au contenu du résumé lui-même ; répondez directement aux dernières questions.】\n\n",
        "summary_prompt_suffix": "\n\n---\nVoici la conversation récente :",
        "tool_trimmed": "... [Sorties d'outils coupées]\n{content}",
        "content_collapsed": "\n... [Contenu réduit] ...\n",
    },
    "de-DE": {
        "status_context_usage": "Kontextnutzung (geschätzt): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ Hohe Nutzung",
        "status_loaded_summary": "Historische Zusammenfassung geladen ({count} historische Nachrichten ausgeblendet)",
        "status_context_summary_updated": "Kontextzusammenfassung aktualisiert: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "Kontextzusammenfassung wird im Hintergrund generiert...",
        "status_summary_error": "Zusammenfassungsfehler: {error}",
        "summary_prompt_prefix": "【Vorherige Zusammenfassung: Das Folgende ist eine Zusammenfassung der historischen Konversation, die nur als Kontext dient. Antworten Sie nicht auf den Inhalt der Zusammenfassung selbst, sondern direkt auf die nachfolgenden neuesten Fragen.】\n\n",
        "summary_prompt_suffix": "\n\n---\nHier ist die jüngste Konversation:",
        "tool_trimmed": "... [Werkzeugausgaben gekürzt]\n{content}",
        "content_collapsed": "\n... [Inhalt ausgeblendet] ...\n",
    },
    "es-ES": {
        "status_context_usage": "Uso del contexto (estimado): {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_high_usage": " | ⚠️ Uso elevado",
        "status_loaded_summary": "Resumen histórico cargado ({count} mensajes históricos ocultos)",
        "status_context_summary_updated": "Resumen del contexto actualizado: {tokens} / {max_tokens} Tokens ({ratio}%)",
        "status_generating_summary": "Generando resumen del contexto en segundo plano...",
        "status_summary_error": "Error de resumen: {error}",
        "summary_prompt_prefix": "【Resumen anterior: El siguiente es un resumen de la conversación histórica, proporcionado solo como contexto. No responda al contenido del resumen en sí; responda directamente a las preguntas más recientes.】\n\n",
        "summary_prompt_suffix": "\n\n---\nA continuación se muestra la conversación reciente:",
        "tool_trimmed": "... [Salidas de herramientas recortadas]\n{content}",
        "content_collapsed": "\n... [Contenido contraído] ...\n",
    },
    "it-IT": {
        "status_context_usage": "Utilizzo contesto (stimato): {tokens} / {max_tokens} Token ({ratio}%)",
        "status_high_usage": " | ⚠️ Utilizzo elevato",
        "status_loaded_summary": "Riepilogo storico caricato ({count} messaggi storici nascosti)",
        "status_context_summary_updated": "Riepilogo contesto aggiornato: {tokens} / {max_tokens} Token ({ratio}%)",
        "status_generating_summary": "Generazione riepilogo contesto in background...",
        "status_summary_error": "Errore riepilogo: {error}",
        "summary_prompt_prefix": "【Riepilogo precedente: Il seguente è un riepilogo della conversazione storica, fornito solo per contesto. Non rispondere al contenuto del riepilogo stesso; rispondi direttamente alle domande più recenti.】\n\n",
        "summary_prompt_suffix": "\n\n---\nDi seguito è riportata la conversazione recente:",
        "tool_trimmed": "... [Output degli strumenti tagliati]\n{content}",
        "content_collapsed": "\n... [Contenuto compresso] ...\n",
    },
}


# Global cache for tiktoken encoding
TIKTOKEN_ENCODING = None
if tiktoken:
    try:
        TIKTOKEN_ENCODING = tiktoken.get_encoding("o200k_base")
    except Exception as e:
        logger.error(f"[Init] Failed to load tiktoken encoding: {e}")


@lru_cache(maxsize=1024)
def _get_cached_tokens(text: str) -> int:
    """Calculates tokens with LRU caching for exact string matches."""
    if not text:
        return 0
    if TIKTOKEN_ENCODING:
        try:
            # tiktoken logic is relatively fast, but caching it based on exact string match
            # turns O(N) encoding time to O(1) dictionary lookup for historical messages.
            return len(TIKTOKEN_ENCODING.encode(text))
        except Exception as e:
            logger.warning(
                f"[Token Count] tiktoken error: {e}, falling back to character estimation"
            )
            pass

    # Fallback strategy: Rough estimation (1 token ≈ 4 chars)
    return len(text) // 4


class Filter:
    def __init__(self):
        self.valves = self.Valves()
        self._owui_db = owui_db
        self._db_engine = owui_engine
        self._fallback_session_factory = (
            sessionmaker(bind=self._db_engine) if self._db_engine else None
        )
        self._model_thresholds_cache: Optional[Dict[str, Any]] = None

        # Fallback mapping for variants not in TRANSLATIONS keys
        self.fallback_map = {
            "es-AR": "es-ES",
            "es-MX": "es-ES",
            "fr-CA": "fr-FR",
            "en-CA": "en-US",
            "en-GB": "en-US",
            "en-AU": "en-US",
            "de-AT": "de-DE",
        }

        # Concurrency control: Lock per chat session
        self._chat_locks = {}
        self._init_database()

    def _resolve_language(self, lang: str) -> str:
        """Resolve the best matching language code from the TRANSLATIONS dict."""
        target_lang = lang

        # 1. Direct match
        if target_lang in TRANSLATIONS:
            return target_lang

        # 2. Variant fallback (explicit mapping)
        if target_lang in self.fallback_map:
            target_lang = self.fallback_map[target_lang]
            if target_lang in TRANSLATIONS:
                return target_lang

        # 3. Base language fallback (e.g. fr-BE -> fr-FR)
        if "-" in lang:
            base_lang = lang.split("-")[0]
            for supported_lang in TRANSLATIONS:
                if supported_lang.startswith(base_lang + "-"):
                    return supported_lang

        # 4. Final Fallback to en-US
        return "en-US"

    def _get_translation(self, lang: str, key: str, **kwargs) -> str:
        """Get translated string for the given language and key."""
        target_lang = self._resolve_language(lang)
        lang_dict = TRANSLATIONS.get(target_lang, TRANSLATIONS["en-US"])
        text = lang_dict.get(key, TRANSLATIONS["en-US"].get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception as e:
                logger.warning(f"Translation formatting failed for {key}: {e}")
        return text

    def _get_chat_lock(self, chat_id: str) -> asyncio.Lock:
        """Get or create an asyncio lock for a specific chat ID."""
        if chat_id not in self._chat_locks:
            self._chat_locks[chat_id] = asyncio.Lock()
        return self._chat_locks[chat_id]

    def _is_summary_message(self, message: Dict[str, Any]) -> bool:
        """Return True when the message is this filter's injected summary marker."""
        metadata = message.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        return bool(
            metadata.get("is_summary")
            and metadata.get("source") == SUMMARY_METADATA_SOURCE
        )

    def _build_summary_message(
        self, summary_text: str, lang: str, covered_until: int
    ) -> Dict[str, Any]:
        """Create a summary marker message with original-history progress metadata."""
        summary_content = (
            self._get_translation(lang, "summary_prompt_prefix")
            + f"{summary_text}"
            + self._get_translation(lang, "summary_prompt_suffix")
        )
        return {
            "role": "assistant",
            "content": summary_content,
            "metadata": {
                "is_summary": True,
                "source": SUMMARY_METADATA_SOURCE,
                "covered_until": max(0, int(covered_until)),
            },
        }

    def _get_summary_view_state(self, messages: List[Dict]) -> Dict[str, Optional[int]]:
        """Inspect the current message view and recover summary marker metadata."""
        for index, message in enumerate(messages):
            if not self._is_summary_message(message):
                continue

            metadata = message.get("metadata", {})
            covered_until = metadata.get("covered_until", 0)
            if not isinstance(covered_until, int) or covered_until < 0:
                covered_until = 0

            return {
                "summary_index": index,
                "base_progress": covered_until,
            }

        return {"summary_index": None, "base_progress": 0}

    def _get_original_history_count(self, messages: List[Dict]) -> int:
        """Map the current visible message list back to original-history size."""
        summary_state = self._get_summary_view_state(messages)
        summary_index = summary_state["summary_index"]
        base_progress = summary_state["base_progress"] or 0

        if summary_index is None:
            return len(messages)

        return base_progress + max(0, len(messages) - summary_index - 1)

    def _calculate_target_compressed_count(self, messages: List[Dict]) -> int:
        """Calculate the next summary boundary in original-history coordinates."""
        summary_state = self._get_summary_view_state(messages)
        summary_index = summary_state["summary_index"]
        base_progress = summary_state["base_progress"] or 0

        original_count = self._get_original_history_count(messages)
        raw_target = max(base_progress, original_count - self.valves.keep_last)

        if summary_index is None:
            protected_prefix = self._get_effective_keep_first(messages)
            return self._align_tail_start_to_atomic_boundary(
                messages, raw_target, protected_prefix
            )

        if raw_target <= base_progress:
            return base_progress

        tail_messages = messages[summary_index + 1 :]
        local_target = raw_target - base_progress
        aligned_local_target = self._align_tail_start_to_atomic_boundary(
            tail_messages, local_target, 0
        )
        return base_progress + aligned_local_target

    def _reconstruct_active_history_branch(
        self, history_messages: Any, current_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Rebuild the active chat branch from OpenWebUI `history.messages` data."""
        if not isinstance(history_messages, dict) or not history_messages:
            return []

        if isinstance(current_id, str) and current_id in history_messages:
            ordered_messages: List[Dict[str, Any]] = []
            visited = set()
            cursor = current_id

            while isinstance(cursor, str) and cursor and cursor not in visited:
                visited.add(cursor)
                node = history_messages.get(cursor)
                if not isinstance(node, dict):
                    break

                ordered_messages.append(deepcopy(node))
                cursor = node.get("parentId") or node.get("parent_id")

            if ordered_messages:
                ordered_messages.reverse()
                return ordered_messages

        sortable_messages = []
        for index, node in enumerate(history_messages.values()):
            if not isinstance(node, dict):
                continue

            timestamp = node.get("timestamp")
            if not isinstance(timestamp, (int, float)):
                timestamp = node.get("created_at")
            if not isinstance(timestamp, (int, float)):
                timestamp = index

            sortable_messages.append((float(timestamp), index, deepcopy(node)))

        sortable_messages.sort(key=lambda item: (item[0], item[1]))
        return [message for _, _, message in sortable_messages]

    def _load_full_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """Load the full persisted chat history for summary decisions when available."""
        if not chat_id or Chats is None:
            return []

        try:
            chat_record = Chats.get_chat_by_id(chat_id)
        except Exception as exc:
            logger.warning(f"[Chat Load] Failed to fetch chat {chat_id}: {exc}")
            return []

        chat_payload = getattr(chat_record, "chat", None)
        if not isinstance(chat_payload, dict):
            return []

        direct_messages = chat_payload.get("messages")
        if isinstance(direct_messages, list) and direct_messages:
            return deepcopy(direct_messages)

        history = chat_payload.get("history")
        if not isinstance(history, dict):
            return []

        history_messages = history.get("messages")
        if not isinstance(history_messages, dict) or not history_messages:
            return []

        current_id = history.get("currentId") or history.get("current_id")
        return self._reconstruct_active_history_branch(history_messages, current_id)

    def _shorten_tool_call_id(self, tool_call_id: str, max_length: int = 40) -> str:
        """Keep tool call IDs within provider limits while staying deterministic."""
        if not isinstance(tool_call_id, str):
            return tool_call_id

        cleaned_id = tool_call_id.strip()
        if len(cleaned_id) <= max_length:
            return cleaned_id

        hash_suffix = hashlib.sha1(cleaned_id.encode("utf-8")).hexdigest()[:8]
        prefix_length = max(0, max_length - len(hash_suffix) - 1)
        return f"{cleaned_id[:prefix_length]}_{hash_suffix}"

    def _normalize_native_tool_call_ids(self, messages: List[Dict]) -> int:
        """Normalize overlong native tool-call IDs and keep assistant/tool links aligned."""
        rewritten_ids: Dict[str, str] = {}

        for message in messages:
            tool_calls = message.get("tool_calls")
            if not isinstance(tool_calls, list):
                continue

            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue

                original_id = tool_call.get("id")
                if not isinstance(original_id, str) or not original_id.strip():
                    continue

                normalized_id = rewritten_ids.get(original_id)
                if normalized_id is None:
                    normalized_id = self._shorten_tool_call_id(original_id)
                    rewritten_ids[original_id] = normalized_id

                tool_call["id"] = normalized_id

        if not rewritten_ids:
            return 0

        normalized_count = 0
        for message in messages:
            tool_call_id = message.get("tool_call_id")
            if not isinstance(tool_call_id, str):
                continue

            normalized_id = rewritten_ids.get(tool_call_id)
            if normalized_id and normalized_id != tool_call_id:
                message["tool_call_id"] = normalized_id
                normalized_count += 1

        return sum(1 for old_id, new_id in rewritten_ids.items() if old_id != new_id)

    def _trim_native_tool_outputs(self, messages: List[Dict], lang: str) -> int:
        """Collapse verbose native tool outputs while preserving tool-call structure."""
        trimmed_count = 0
        tool_trim_threshold_chars = 1200
        collapsed_text = self._get_translation(lang, "content_collapsed").strip()

        for group in self._get_atomic_groups(messages):
            if len(group) < 2:
                continue

            grouped_messages = [messages[index] for index in group]
            first_message = grouped_messages[0]
            trailing_messages = grouped_messages[1:]

            if not (
                first_message.get("role") == "assistant"
                and first_message.get("tool_calls")
                and trailing_messages
            ):
                continue

            last_message = grouped_messages[-1]
            assistant_followup = None
            tool_messages = trailing_messages

            if (
                len(grouped_messages) >= 3
                and last_message.get("role") == "assistant"
                and all(msg.get("role") == "tool" for msg in grouped_messages[1:-1])
            ):
                assistant_followup = last_message
                tool_messages = grouped_messages[1:-1]
            elif not all(msg.get("role") == "tool" for msg in trailing_messages):
                continue

            tool_chars = sum(len(str(msg.get("content", ""))) for msg in tool_messages)
            if tool_chars < tool_trim_threshold_chars:
                continue

            for tool_message in tool_messages:
                metadata = tool_message.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                metadata["is_trimmed"] = True
                metadata["trimmed_by"] = SUMMARY_METADATA_SOURCE
                tool_message["metadata"] = metadata
                tool_message["content"] = collapsed_text
                trimmed_count += 1

            if assistant_followup is not None:
                final_content = assistant_followup.get("content", "")
                if isinstance(final_content, str) and final_content.strip():
                    assistant_metadata = assistant_followup.get("metadata", {})
                    if not isinstance(assistant_metadata, dict):
                        assistant_metadata = {}
                    if not assistant_metadata.get("tool_outputs_trimmed"):
                        assistant_followup["content"] = self._get_translation(
                            lang, "tool_trimmed", content=final_content
                        )
                        assistant_metadata["tool_outputs_trimmed"] = True
                        assistant_metadata["trimmed_by"] = SUMMARY_METADATA_SOURCE
                        assistant_followup["metadata"] = assistant_metadata

        for message in messages:
            content = message.get("content", "")
            if (
                not isinstance(content, str)
                or '<details type="tool_calls"' not in content
            ):
                continue

            trimmed_blocks = 0

            def _replace_tool_block(match: re.Match) -> str:
                nonlocal trimmed_blocks
                block = match.group(0)
                result_match = re.search(r'result="([^"]*)"', block)

                if not result_match:
                    return block

                if len(result_match.group(1)) < tool_trim_threshold_chars:
                    return block

                trimmed_blocks += 1
                return re.sub(
                    r'result="([^"]*)"',
                    f'result="&quot;{collapsed_text}&quot;"',
                    block,
                    count=1,
                )

            new_content = re.sub(
                r'<details type="tool_calls"[\s\S]*?</details>',
                _replace_tool_block,
                content,
            )

            if trimmed_blocks <= 0:
                continue

            metadata = message.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["tool_outputs_trimmed"] = True
            metadata["trimmed_by"] = SUMMARY_METADATA_SOURCE
            message["metadata"] = metadata
            message["content"] = new_content
            trimmed_count += trimmed_blocks

        return trimmed_count

    def _get_atomic_groups(self, messages: List[Dict]) -> List[List[int]]:
        """
        Groups message indices into atomic units that must be kept or dropped together.
        Specifically handles native tool-calling sequences:
        - assistant(tool_calls)
        - tool(s)
        - assistant(final response)
        """
        groups = []
        current_group = []

        for i, msg in enumerate(messages):
            role = msg.get("role")
            has_tool_calls = bool(msg.get("tool_calls"))

            # Logic:
            # 1. If assistant message has tool_calls, it starts a potential block.
            # 2. If message is 'tool' role, it MUST belong to the preceding assistant group.
            # 3. If message is 'assistant' and follows a 'tool' group, it's the final answer.

            if role == "assistant" and has_tool_calls:
                # Close previous group if any
                if current_group:
                    groups.append(current_group)
                current_group = [i]
            elif role == "tool":
                # Force tool results into the current group
                if not current_group:
                    # An orphaned tool result? Group it alone but warn
                    groups.append([i])
                else:
                    current_group.append(i)
            elif (
                role == "assistant"
                and current_group
                and messages[current_group[-1]].get("role") == "tool"
            ):
                # This is likely the assistant follow-up consuming tool results
                current_group.append(i)
                groups.append(current_group)
                current_group = []
            else:
                # Regular message (user, or assistant without tool calls)
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([i])

        if current_group:
            groups.append(current_group)

        return groups

    def _get_effective_keep_first(self, messages: List[Dict]) -> int:
        """Protect configured head messages and all leading system messages."""
        last_system_index = -1
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                last_system_index = i

        return max(self.valves.keep_first, last_system_index + 1)

    def _align_tail_start_to_atomic_boundary(
        self, messages: List[Dict], raw_start_index: int, protected_prefix: int
    ) -> int:
        """
        Align the retained tail to an atomic-group boundary.

        If the raw tail start falls in the middle of an assistant/tool/assistant
        chain, move it backward to the start of that chain so the next request
        never begins with an orphaned tool result or assistant follow-up.
        """
        aligned_start = max(raw_start_index, protected_prefix)

        if aligned_start <= protected_prefix or aligned_start >= len(messages):
            return aligned_start

        trimmable = messages[protected_prefix:]
        local_start = aligned_start - protected_prefix

        for group in self._get_atomic_groups(trimmable):
            group_start = group[0]
            group_end = group[-1] + 1

            if local_start == group_start:
                return aligned_start

            if group_start < local_start < group_end:
                return protected_prefix + group_start

        return aligned_start

    async def _get_user_context(
        self,
        __user__: Optional[Dict[str, Any]],
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> Dict[str, str]:
        """Extract basic user context with safe fallbacks."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        user_id = user_data.get("id", "unknown_user")
        user_name = user_data.get("name", "User")
        user_language = user_data.get("language", "en-US")

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
            except asyncio.TimeoutError:
                logger.warning(
                    "Failed to retrieve frontend language: Timeout (using fallback)"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve frontend language: {type(e).__name__}: {e}"
                )

        return {
            "user_id": user_id,
            "user_name": user_name,
            "user_language": user_language,
        }

    def _parse_model_thresholds(self) -> Dict[str, Any]:
        """Parse model_thresholds string into a dictionary.

        Format: model_id:compression_threshold:max_context, model_id2:threshold2:max2
        Example: gpt-4:8000:32000, claude-3:100000:200000

        Returns cached result if already parsed.
        """
        if self._model_thresholds_cache is not None:
            return self._model_thresholds_cache

        self._model_thresholds_cache = {}
        raw_config = self.valves.model_thresholds
        if not raw_config:
            return self._model_thresholds_cache

        for entry in raw_config.split(","):
            entry = entry.strip()
            if not entry:
                continue

            parts = entry.split(":")
            if len(parts) != 3:
                continue

            try:
                model_id = parts[0].strip()
                compression_threshold = int(parts[1].strip())
                max_context = int(parts[2].strip())

                self._model_thresholds_cache[model_id] = {
                    "compression_threshold_tokens": compression_threshold,
                    "max_context_tokens": max_context,
                }
            except ValueError:
                continue

        return self._model_thresholds_cache

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
                logger.warning(f"[Database] ⚠️ Failed to close fallback session: {exc}")

    def _init_database(self):
        """Initializes the database table using Open WebUI's shared connection."""
        try:
            if self._db_engine is None:
                raise RuntimeError(
                    "Open WebUI database engine is unavailable. Ensure Open WebUI is configured with a valid DATABASE_URL."
                )

            # Check if table exists using SQLAlchemy inspect
            inspector = inspect(self._db_engine)
            # Support schema if configured
            has_table = (
                inspector.has_table("chat_summary", schema=owui_schema)
                if owui_schema
                else inspector.has_table("chat_summary")
            )

            if not has_table:
                # Create the chat_summary table if it doesn't exist
                ChatSummary.__table__.create(bind=self._db_engine, checkfirst=True)
                logger.info(
                    "[Database] ✅ Successfully created chat_summary table using Open WebUI's shared database connection."
                )
            else:
                logger.info(
                    "[Database] ✅ Using Open WebUI's shared database connection. chat_summary table already exists."
                )

        except Exception as e:
            logger.error(f"[Database] ❌ Initialization failed: {str(e)}")

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
        model_thresholds: str = Field(
            default="",
            description="Per-model threshold overrides. Format: model_id:compression_threshold:max_context (comma-separated). Example: gpt-4:8000:32000, claude-3:100000:200000",
        )

        keep_first: int = Field(
            default=1,
            ge=0,
            description="Always keep the first N messages. Set to 0 to disable.",
        )
        keep_last: int = Field(
            default=6, ge=0, description="Always keep the last N full messages."
        )
        summary_model: Optional[str] = Field(
            default=None,
            description="The model ID used to generate the summary. If empty, uses the current conversation's model. Used to match configurations in model_thresholds.",
        )
        summary_model_max_context: int = Field(
            default=0,
            ge=0,
            description="Max context tokens for the summary model. If 0, falls back to model_thresholds or global max_context_tokens. Example: gemini-flash=1000000, gpt-4o-mini=128000.",
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
            default=False, description="Enable detailed logging for debugging."
        )
        show_debug_log: bool = Field(
            default=False, description="Show debug logs in the frontend console"
        )
        show_token_usage_status: bool = Field(
            default=True, description="Show token usage status notification"
        )
        token_usage_status_threshold: int = Field(
            default=80,
            ge=0,
            le=100,
            description="Only show token usage status when usage exceeds this percentage (0-100). Set to 0 to always show.",
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
                            logger.info(
                                f"[Storage] Skipping update: New progress ({compressed_count}) is not greater than existing progress ({existing.compressed_message_count})"
                            )
                        return

                    # Update existing record
                    existing.summary = summary
                    existing.compressed_message_count = compressed_count
                    existing.updated_at = datetime.now(timezone.utc)
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
                    logger.info(
                        f"[Storage] Summary has been {action.lower()} in the database (Chat ID: {chat_id})"
                    )

        except Exception as e:
            logger.error(f"[Storage] ❌ Database save failed: {str(e)}")

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
            logger.error(f"[Load] ❌ Database read failed: {str(e)}")
        return None

    def _load_summary(self, chat_id: str, body: dict) -> Optional[str]:
        """Loads the summary text from the database (Compatible with old interface)."""
        record = self._load_summary_record(chat_id)
        if record:
            if self.valves.debug_mode:
                logger.info(f"[Load] Loaded summary from database (Chat ID: {chat_id})")
                logger.info(
                    f"[Load] Last updated: {record.updated_at}, Compressed message count: {record.compressed_message_count}"
                )
            return record.summary
        return None

    def _count_tokens(self, text: str) -> int:
        """Counts the number of tokens in the text."""
        return _get_cached_tokens(text)

    def _calculate_messages_tokens(self, messages: List[Dict]) -> int:
        """Calculates the total tokens for a list of messages."""
        start_time = time.time()
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

        duration = (time.time() - start_time) * 1000
        if self.valves.debug_mode:
            logger.info(
                f"[Token Calc] Calculated {total_tokens} tokens for {len(messages)} messages in {duration:.2f}ms"
            )

        return total_tokens

    def _estimate_messages_tokens(self, messages: List[Dict]) -> int:
        """Fast estimation of tokens based on character count (1/4 ratio)."""
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total_chars += len(part.get("text", ""))
            else:
                total_chars += len(str(content))

        return total_chars // 4

    def _get_model_thresholds(self, model_id: str) -> Dict[str, int]:
        """Gets threshold configuration for a specific model.

        Priority:
        1. If configuration exists for the model ID in model_thresholds, use it.
        2. If model is a custom model, try to match its base_model_id.
        3. Otherwise, use global parameters compression_threshold_tokens and max_context_tokens.
        """
        parsed = self._parse_model_thresholds()

        # 1. Direct match with model_id
        if model_id in parsed:
            if self.valves.debug_mode:
                logger.info(f"[Config] Using model-specific configuration: {model_id}")
            return parsed[model_id]

        # 2. Try to find base_model_id for custom models
        try:
            model_obj = Models.get_model_by_id(model_id)
            if model_obj:
                # Check for base_model_id (custom model)
                base_model_id = getattr(model_obj, "base_model_id", None)
                if not base_model_id:
                    # Try base_model_ids (array) - take first one
                    base_model_ids = getattr(model_obj, "base_model_ids", None)
                    if (
                        base_model_ids
                        and isinstance(base_model_ids, list)
                        and len(base_model_ids) > 0
                    ):
                        base_model_id = base_model_ids[0]

                if base_model_id and base_model_id in parsed:
                    if self.valves.debug_mode:
                        logger.info(
                            f"[Config] Custom model '{model_id}' -> base_model '{base_model_id}': using base model configuration"
                        )
                    return parsed[base_model_id]
        except Exception as e:
            if self.valves.debug_mode:
                logger.warning(
                    f"[Config] Failed to lookup base_model for '{model_id}': {e}"
                )

        # 3. Use global default configuration
        if self.valves.debug_mode:
            logger.info(
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

    def _infer_native_function_calling_from_messages(self, messages: Any) -> bool:
        """Infer native function-calling mode from tool-shaped messages."""
        if not isinstance(messages, list):
            return False

        for message in messages:
            if not isinstance(message, dict):
                continue

            tool_calls = message.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                return True

            if message.get("role") == "tool":
                return True

            content = message.get("content", "")
            if isinstance(content, str) and '<details type="tool_calls"' in content:
                return True

        return False

    def _summarize_message_shape(
        self, messages: Any, limit: int = 12
    ) -> List[Dict[str, Any]]:
        """Build a compact structural summary of recent messages for debugging."""
        if not isinstance(messages, list):
            return []

        summary = []
        for index, message in enumerate(messages[:limit]):
            if not isinstance(message, dict):
                summary.append(
                    {
                        "index": index,
                        "type": type(message).__name__,
                    }
                )
                continue

            content = message.get("content", "")
            tool_calls = message.get("tool_calls")
            metadata = message.get("metadata", {})

            entry = {
                "index": index,
                "role": message.get("role", "unknown"),
                "has_tool_calls": bool(isinstance(tool_calls, list) and tool_calls),
                "tool_call_count": len(tool_calls)
                if isinstance(tool_calls, list)
                else 0,
                "tool_call_id_lengths": [
                    len(str(tc.get("id", "")))
                    for tc in tool_calls[:3]
                    if isinstance(tc, dict)
                ]
                if isinstance(tool_calls, list)
                else [],
                "has_tool_call_id": isinstance(message.get("tool_call_id"), str),
                "tool_call_id_length": len(str(message.get("tool_call_id", "")))
                if isinstance(message.get("tool_call_id"), str)
                else 0,
                "content_type": type(content).__name__,
                "content_length": len(content) if isinstance(content, str) else 0,
                "has_tool_details_block": isinstance(content, str)
                and '<details type="tool_calls"' in content,
                "metadata_keys": sorted(metadata.keys())[:8]
                if isinstance(metadata, dict)
                else [],
            }

            if isinstance(content, list):
                entry["content_part_types"] = [
                    part.get("type", type(part).__name__)
                    for part in content[:5]
                    if isinstance(part, dict)
                ]

            summary.append(entry)

        return summary

    def _build_native_tool_debug_snapshot(self, body: Any) -> Dict[str, Any]:
        """Collect a structural snapshot of the request for tool-calling diagnosis."""
        if not isinstance(body, dict):
            return {"body_type": type(body).__name__}

        messages = body.get("messages", [])
        metadata = body.get("metadata", {})
        params = body.get("params", {})

        role_counts: Dict[str, int] = {}
        tool_detail_blocks = 0
        tool_role_indices = []
        assistant_tool_call_indices = []

        if isinstance(messages, list):
            for index, message in enumerate(messages):
                if not isinstance(message, dict):
                    continue

                role = str(message.get("role", "unknown"))
                role_counts[role] = role_counts.get(role, 0) + 1

                if role == "tool":
                    tool_role_indices.append(index)

                tool_calls = message.get("tool_calls")
                if isinstance(tool_calls, list) and tool_calls:
                    assistant_tool_call_indices.append(index)

                content = message.get("content", "")
                if isinstance(content, str) and '<details type="tool_calls"' in content:
                    tool_detail_blocks += content.count('<details type="tool_calls"')

        return {
            "body_keys": sorted(body.keys()),
            "metadata_keys": sorted(metadata.keys()) if isinstance(metadata, dict) else [],
            "params_keys": sorted(params.keys()) if isinstance(params, dict) else [],
            "metadata_function_calling": metadata.get("function_calling")
            if isinstance(metadata, dict)
            else None,
            "params_function_calling": params.get("function_calling")
            if isinstance(params, dict)
            else None,
            "message_count": len(messages) if isinstance(messages, list) else 0,
            "role_counts": role_counts,
            "assistant_tool_call_indices": assistant_tool_call_indices[:8],
            "tool_role_indices": tool_role_indices[:8],
            "tool_detail_blocks": tool_detail_blocks,
            "inferred_native": self._infer_native_function_calling_from_messages(
                messages
            ),
            "message_shape": self._summarize_message_shape(messages),
        }

    def _build_summary_progress_snapshot(self, messages: Any) -> Dict[str, Any]:
        """Collect compact summary-boundary diagnostics for a message list."""
        if not isinstance(messages, list):
            return {"messages_type": type(messages).__name__}

        summary_state = self._get_summary_view_state(messages)
        sample = []
        for index, message in enumerate(messages[:4]):
            if not isinstance(message, dict):
                sample.append({"index": index, "type": type(message).__name__})
                continue

            content = message.get("content", "")
            sample.append(
                {
                    "index": index,
                    "role": message.get("role", "unknown"),
                    "id": message.get("id", ""),
                    "parentId": message.get("parentId") or message.get("parent_id"),
                    "tool_call_id": message.get("tool_call_id", ""),
                    "tool_call_count": len(message.get("tool_calls", []))
                    if isinstance(message.get("tool_calls"), list)
                    else 0,
                    "is_summary": self._is_summary_message(message),
                    "content_length": len(content) if isinstance(content, str) else 0,
                }
            )

        tail_sample = []
        start_index = max(0, len(messages) - 3)
        for index, message in enumerate(messages[start_index:], start=start_index):
            if not isinstance(message, dict):
                tail_sample.append({"index": index, "type": type(message).__name__})
                continue

            content = message.get("content", "")
            tail_sample.append(
                {
                    "index": index,
                    "role": message.get("role", "unknown"),
                    "id": message.get("id", ""),
                    "parentId": message.get("parentId") or message.get("parent_id"),
                    "tool_call_id": message.get("tool_call_id", ""),
                    "tool_call_count": len(message.get("tool_calls", []))
                    if isinstance(message.get("tool_calls"), list)
                    else 0,
                    "is_summary": self._is_summary_message(message),
                    "content_length": len(content) if isinstance(content, str) else 0,
                }
            )

        return {
            "message_count": len(messages),
            "summary_state": summary_state,
            "original_history_count": self._get_original_history_count(messages),
            "target_compressed_count": self._calculate_target_compressed_count(messages),
            "effective_keep_first": self._get_effective_keep_first(messages),
            "head_sample": sample,
            "tail_sample": tail_sample,
        }

    def _unfold_messages(self, messages: Any) -> List[Dict[str, Any]]:
        """
        Reverse-expand compact UI messages back into their native tool-calling sequence
        by parsing the hidden 'output' dictionary, identical to what OpenWebUI does
        in the inlet phase (middleware.py:process_messages_with_output).
        """
        if not isinstance(messages, list):
            return messages

        unfolded = []
        for msg in messages:
            if not isinstance(msg, dict):
                unfolded.append(msg)
                continue

            # If it's an assistant message with the hidden 'output' field, unfold it
            if msg.get("role") == "assistant" and isinstance(msg.get("output"), list) and msg.get("output"):
                try:
                    from open_webui.utils.misc import convert_output_to_messages
                    expanded = convert_output_to_messages(msg["output"], raw=True)
                    if expanded:
                        unfolded.extend(expanded)
                        continue
                except ImportError:
                    pass # Fallback if for some reason the internal import fails

            # Clean message (strip 'output' field just like inlet does)
            clean_msg = {k: v for k, v in msg.items() if k != "output"}
            unfolded.append(clean_msg)
            
        return unfolded

    def _get_function_calling_mode(self, body: dict) -> str:
        """Read function-calling mode from all known OpenWebUI payload locations."""
        metadata = body.get("metadata", {}) if isinstance(body, dict) else {}
        params = body.get("params", {}) if isinstance(body, dict) else {}
        messages = body.get("messages", []) if isinstance(body, dict) else []

        if isinstance(metadata, dict):
            mode = metadata.get("function_calling")
            if isinstance(mode, str) and mode.strip():
                return mode.strip()

        if isinstance(params, dict):
            mode = params.get("function_calling")
            if isinstance(mode, str) and mode.strip():
                return mode.strip()

        if self._infer_native_function_calling_from_messages(messages):
            return "native"

        return ""

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
                    try {{
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
                        return true;
                    }} catch (e) {{
                        console.error("[Compression] Failed to emit summary debug log", e);
                        return false;
                    }}
                }})();
            """

            await asyncio.wait_for(
                __event_call__(
                    {
                        "type": "execute",
                        "data": {"code": js_code},
                    }
                ),
                timeout=2.0,
            )
        except Exception as e:
            logger.error(f"Error emitting debug log: {e}")

    async def _log(self, message: str, log_type: str = "info", event_call=None):
        """Unified logging to both backend (print) and frontend (console.log)"""
        # Backend logging
        if self.valves.debug_mode:
            logger.info(message)

        # Frontend logging
        if self.valves.show_debug_log and event_call:
            try:
                css = "color: #3b82f6;"  # Blue default
                if log_type == "error":
                    css = "color: #ef4444; font-weight: bold;"  # Red
                elif log_type == "warning":
                    css = "color: #f59e0b;"  # Orange
                elif log_type == "success":
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
                    try {{
                        console.log("%c[Compression] {safe_message}", "{css}");
                        return true;
                    }} catch (e) {{
                        console.error("[Compression] Failed to emit console log", e);
                        return false;
                    }}
                """
                await asyncio.wait_for(
                    event_call({"type": "execute", "data": {"code": js_code}}),
                    timeout=2.0,
                )
            except ValueError as ve:
                if "broadcast" in str(ve).lower():
                    logger.debug("Cannot broadcast to frontend without explicit room; suppressing further frontend logs in this session.")
                    self.valves.show_debug_log = False
                else:
                    logger.error(f"Failed to process log to frontend: ValueError: {ve}")
            except Exception as e:
                logger.error(
                    f"Failed to process log to frontend: {type(e).__name__}: {e}"
                )

    def _should_show_status(self, usage_ratio: float) -> bool:
        """
        Check if token usage status should be shown based on threshold.

        Args:
            usage_ratio: Current usage ratio (0.0 to 1.0)

        Returns:
            True if status should be shown, False otherwise
        """
        if not self.valves.show_token_usage_status:
            return False

        # If threshold is 0, always show
        if self.valves.token_usage_status_threshold == 0:
            return True

        # Check if usage exceeds threshold
        threshold_ratio = self.valves.token_usage_status_threshold / 100.0
        return usage_ratio >= threshold_ratio

    def _should_skip_compression(
        self, body: dict, __model__: Optional[dict] = None
    ) -> bool:
        """
        Check if compression should be skipped.
        Returns True if:
        1. The base model includes 'copilot_sdk'
        """
        # Check if base model includes copilot_sdk
        if __model__:
            base_model_id = __model__.get("base_model_id", "")
            if "copilot_sdk" in base_model_id.lower():
                return True

        # Also check model in body
        model_id = body.get("model", "")
        if "copilot_sdk" in model_id.lower():
            return True

        return False

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

        if self._should_skip_compression(body, __model__):
            if self.valves.debug_mode:
                logger.info(
                    "[Inlet] Skipping compression: copilot_sdk detected in base model"
                )
            return body

        messages = body.get("messages", [])
        user_ctx = await self._get_user_context(__user__, __event_call__)
        lang = user_ctx["user_language"]

        if self.valves.show_debug_log and __event_call__:
            debug_snapshot = self._build_native_tool_debug_snapshot(body)
            await self._log(
                "[Inlet] 🧩 Request structure snapshot: "
                + json.dumps(debug_snapshot, ensure_ascii=False),
                event_call=__event_call__,
            )

        normalized_tool_call_count = self._normalize_native_tool_call_ids(messages)
        if (
            normalized_tool_call_count > 0
            and self.valves.show_debug_log
            and __event_call__
        ):
            await self._log(
                f"[Inlet] 🪪 Normalized {normalized_tool_call_count} overlong tool call ID(s).",
                event_call=__event_call__,
            )

        # --- Native Tool Output Trimming (Opt-in, only for native function calling) ---
        function_calling_mode = self._get_function_calling_mode(body)
        is_native_func_calling = function_calling_mode == "native"

        if self.valves.show_debug_log and __event_call__:
            trimming_state = (
                "enabled" if self.valves.enable_tool_output_trimming else "disabled"
            )
            await self._log(
                "[Inlet] ✂️ Tool trimming check: "
                f"state={trimming_state}, function_calling={function_calling_mode or 'unset'}, "
                f"message_count={len(messages)}",
                event_call=__event_call__,
            )

        if self.valves.enable_tool_output_trimming and is_native_func_calling:
            trimmed_count = self._trim_native_tool_outputs(messages, lang)
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    (
                        f"[Inlet] ✂️ Trimmed {trimmed_count} tool output message(s)."
                        if trimmed_count > 0
                        else "[Inlet] ✂️ Tool trimming checked, but no oversized native tool outputs were found."
                    ),
                    event_call=__event_call__,
                )
        elif self.valves.show_debug_log and __event_call__:
            skip_reason = (
                "tool trimming disabled"
                if not self.valves.enable_tool_output_trimming
                else f"function_calling={function_calling_mode or 'unset'}"
            )
            await self._log(
                f"[Inlet] ✂️ Tool trimming skipped: {skip_reason}.",
                event_call=__event_call__,
            )

        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]

        # Extract system prompt for accurate token calculation
        # 1. For custom models: check DB (Models.get_model_by_id)
        # 2. For base models: check messages for role='system'
        system_prompt_content = None

        # Try to get from DB (custom model)
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
                # Run in thread to avoid blocking event loop on slow DB queries
                model_obj = await asyncio.to_thread(Models.get_model_by_id, model_id)

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
                            # Convert Pydantic model to dict if needed
                            elif hasattr(params, "model_dump"):
                                params = params.model_dump()
                            elif hasattr(params, "dict"):
                                params = params.dict()

                            # Now params should be a dict
                            if isinstance(params, dict):
                                system_prompt_content = params.get("system")
                            else:
                                # Fallback: try getattr
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
                                    log_type="error",
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
                            f"[Inlet] ℹ️ Not a custom model, skipping custom system prompt check",
                            event_call=__event_call__,
                        )

        except Exception as e:
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    f"[Inlet] ❌ Error fetching system prompt from DB: {e}",
                    log_type="error",
                    event_call=__event_call__,
                )
            if self.valves.debug_mode:
                logger.error(f"[Inlet] Error fetching system prompt from DB: {e}")

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
                logger.info(
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
                logger.error(f"[Inlet] Error logging message stats: {e}")

        if not chat_id:
            await self._log(
                "[Inlet] ❌ Missing chat_id in metadata, skipping compression",
                log_type="error",
                event_call=__event_call__,
            )
            return body

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Inlet] Chat ID: {chat_id}\n[Inlet] Received {len(messages)} messages",
                event_call=__event_call__,
            )

            # Log custom model configurations
            raw_config = self.valves.model_thresholds
            parsed_configs = self._parse_model_thresholds()

            if raw_config:
                config_list = [
                    f"{model}: {cfg['compression_threshold_tokens']}t/{cfg['max_context_tokens']}t"
                    for model, cfg in parsed_configs.items()
                ]

                if config_list:
                    await self._log(
                        f"[Inlet] 📋 Model Configs (Raw: '{raw_config}'): {', '.join(config_list)}",
                        event_call=__event_call__,
                    )
                else:
                    await self._log(
                        f"[Inlet] ⚠️ Invalid Model Configs (Raw: '{raw_config}'): No valid configs parsed. Expected format: 'model_id:threshold:max_context'",
                        log_type="warning",
                        event_call=__event_call__,
                    )
            else:
                await self._log(
                    f"[Inlet] 📋 Model Configs: No custom configuration (Global defaults only)",
                    event_call=__event_call__,
                )

        # Log the aligned compression boundary using the same original-history
        # coordinate mapping as outlet/async summary generation.
        target_compressed_count = self._calculate_target_compressed_count(messages)

        await self._log(
            f"[Inlet] Recorded target compression progress: {target_compressed_count}",
            event_call=__event_call__,
        )

        # Load summary record
        summary_record = await asyncio.to_thread(self._load_summary_record, chat_id)

        # Calculate effective_keep_first to ensure all system messages are protected
        effective_keep_first = self._get_effective_keep_first(messages)

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

            # 2. Tail messages (Tail) - All messages starting from the last compression point.
            # Align legacy/raw progress to an atomic boundary so old summary rows do not
            # reintroduce orphaned tool messages into the retained tail.
            raw_start_index = max(compressed_count, effective_keep_first)
            start_index = self._align_tail_start_to_atomic_boundary(
                messages, raw_start_index, effective_keep_first
            )

            # 3. Summary message (Inserted as Assistant message)
            summary_msg = self._build_summary_message(
                summary_record.summary,
                lang,
                start_index,
            )

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

            # --- Fast Estimation Check ---
            estimated_tokens = self._estimate_messages_tokens(calc_messages)

            # Since this is a hard limit check, only skip precise calculation if we are far below it (margin of 15%)
            # max_context_tokens == 0 means "no limit", skip reduction entirely
            if max_context_tokens <= 0:
                total_tokens = estimated_tokens
                await self._log(
                    f"[Inlet] 🔎 No max_context_tokens limit set (0). Skipping reduction. Est: {total_tokens}t",
                    event_call=__event_call__,
                )
            elif estimated_tokens < max_context_tokens * 0.85:
                total_tokens = estimated_tokens
                await self._log(
                    f"[Inlet] 🔎 Fast Preflight Check (Est): {total_tokens}t / {max_context_tokens}t (Well within limit)",
                    event_call=__event_call__,
                )
            else:
                # Calculate exact total tokens via tiktoken
                total_tokens = await asyncio.to_thread(
                    self._calculate_messages_tokens, calc_messages
                )

                # Preflight Check Log
                await self._log(
                    f"[Inlet] 🔎 Precise Preflight Check: {total_tokens}t / {max_context_tokens}t ({(total_tokens/max_context_tokens*100):.1f}%)",
                    event_call=__event_call__,
                )

                # Identify atomic groups to avoid breaking tool-calling context
                atomic_groups = self._get_atomic_groups(tail_messages)

                while total_tokens > max_context_tokens and len(atomic_groups) > 1:
                    # Strategy 1: Structure-Aware Assistant Trimming (Optional, only for non-tool messages)
                    # For simplicity and reliability in this fix, we prioritize Group-Drop over partial trim
                    # if a group contains tool calls.

                    # Strategy 2: Drop Oldest Atomic Group Entirely
                    dropped_group_indices = atomic_groups.pop(0)
                    # Note: indices in dropped_group_indices are relative to ORIGINAL tail_messages
                    # But since we are popping from tail_messages itself, we need to be careful.

                    # Extract and drop messages in this group from the actual list
                    # Since we always pop group 0, we pop len(dropped_group_indices) times from front
                    dropped_tokens = 0
                    for _ in range(len(dropped_group_indices)):
                        dropped = tail_messages.pop(0)
                        if total_tokens == estimated_tokens:
                            dropped_tokens += len(str(dropped.get("content", ""))) // 4
                        else:
                            dropped_tokens += self._count_tokens(
                                str(dropped.get("content", ""))
                            )

                    total_tokens -= dropped_tokens

                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] 🗑️ Dropped atomic group ({len(dropped_group_indices)} msgs) to fit context. Tokens: {dropped_tokens}",
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
            summary_content = summary_msg.get("content", "")
            if total_tokens == estimated_tokens:
                system_tokens = (
                    len(system_prompt_msg.get("content", "")) // 4
                    if system_prompt_msg
                    else 0
                )
                head_tokens = self._estimate_messages_tokens(head_messages)
                summary_tokens = len(summary_content) // 4
                tail_tokens = self._estimate_messages_tokens(tail_messages)
            else:
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
                log_type="success",
                event_call=__event_call__,
            )

            # Prepare status message (Context Usage format)
            if max_context_tokens > 0:
                usage_ratio = total_section_tokens / max_context_tokens
                # Only show status if threshold is met
                if self._should_show_status(usage_ratio):
                    status_msg = self._get_translation(
                        lang,
                        "status_context_usage",
                        tokens=total_section_tokens,
                        max_tokens=max_context_tokens,
                        ratio=f"{usage_ratio*100:.1f}",
                    )
                    if usage_ratio > 0.9:
                        status_msg += self._get_translation(lang, "status_high_usage")

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
            else:
                # For the case where max_context_tokens is 0, show summary info without threshold check
                if self.valves.show_token_usage_status and __event_emitter__:
                    status_msg = self._get_translation(
                        lang, "status_loaded_summary", count=compressed_count
                    )
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
            thresholds = self._get_model_thresholds(model) or {}
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            # --- Fast Estimation Check ---
            estimated_tokens = self._estimate_messages_tokens(calc_messages)

            # Only skip precise calculation if we are clearly below the limit
            # max_context_tokens == 0 means "no limit", skip reduction entirely
            if max_context_tokens <= 0:
                total_tokens = estimated_tokens
                await self._log(
                    f"[Inlet] 🔎 No max_context_tokens limit set (0). Skipping reduction. Est: {total_tokens}t",
                    event_call=__event_call__,
                )
            elif estimated_tokens < max_context_tokens * 0.85:
                total_tokens = estimated_tokens
                await self._log(
                    f"[Inlet] 🔎 Fast limit check (Est): {total_tokens}t / {max_context_tokens}t",
                    event_call=__event_call__,
                )
            else:
                total_tokens = await asyncio.to_thread(
                    self._calculate_messages_tokens, calc_messages
                )

            if total_tokens > max_context_tokens and max_context_tokens > 0:
                await self._log(
                    f"[Inlet] ⚠️ Original messages ({total_tokens} Tokens) exceed limit ({max_context_tokens}). Reducing history...",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # Use atomic grouping to preserve tool-calling integrity
                trimmable = final_messages[effective_keep_first:]
                atomic_groups = self._get_atomic_groups(trimmable)

                while total_tokens > max_context_tokens and len(atomic_groups) > 1:
                    dropped_group_indices = atomic_groups.pop(0)
                    dropped_tokens = 0
                    for _ in range(len(dropped_group_indices)):
                        dropped = trimmable.pop(0)
                        if total_tokens == estimated_tokens:
                            dropped_tokens += len(str(dropped.get("content", ""))) // 4
                        else:
                            dropped_tokens += self._count_tokens(
                                str(dropped.get("content", ""))
                            )
                    total_tokens -= dropped_tokens

                final_messages = final_messages[:effective_keep_first] + trimmable

                await self._log(
                    f"[Inlet] ✂️ Messages reduced (atomic). New total: {total_tokens} Tokens",
                    event_call=__event_call__,
                )

            # Send status notification (Context Usage format)
            if max_context_tokens > 0:
                usage_ratio = total_tokens / max_context_tokens
                # Only show status if threshold is met
                if self._should_show_status(usage_ratio):
                    status_msg = self._get_translation(
                        lang,
                        "status_context_usage",
                        tokens=total_tokens,
                        max_tokens=max_context_tokens,
                        ratio=f"{usage_ratio*100:.1f}",
                    )
                    if usage_ratio > 0.9:
                        status_msg += self._get_translation(lang, "status_high_usage")

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
        __model__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        Executed after the LLM response is complete.
        Calculates Token count in the background and triggers summary generation (does not block current response, does not affect content output).
        """
        # Check if compression should be skipped (e.g., for copilot_sdk)
        if self._should_skip_compression(body, __model__):
            if self.valves.debug_mode:
                logger.info(
                    "[Outlet] Skipping compression: copilot_sdk detected in base model"
                )
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    "[Outlet] ⏭️ Skipping compression: copilot_sdk detected",
                    event_call=__event_call__,
                )
            return body

        # Get user context for i18n
        user_ctx = await self._get_user_context(__user__, __event_call__)
        lang = user_ctx["user_language"]

        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]
        if not chat_id:
            await self._log(
                "[Outlet] ❌ Missing chat_id in metadata, skipping compression",
                log_type="error",
                event_call=__event_call__,
            )
            return body
        model = body.get("model") or ""
        messages = body.get("messages", [])

        if self.valves.show_debug_log and __event_call__:
            outlet_snapshot = self._build_native_tool_debug_snapshot(body)
            outlet_progress = self._build_summary_progress_snapshot(messages)
            await self._log(
                "[Outlet] 🧩 Body structure snapshot: "
                + json.dumps(outlet_snapshot, ensure_ascii=False),
                event_call=__event_call__,
            )
            await self._log(
                "[Outlet] 📐 Body summary-progress snapshot: "
                + json.dumps(outlet_progress, ensure_ascii=False),
                event_call=__event_call__,
            )

        # Unfold compact tool messages to align with inlet's exact coordinate system
        # In the outlet phase, the frontend payload often lacks the hidden 'output' field.
        # We try to load the full, raw history from the database first.
        db_messages = self._load_full_chat_messages(chat_id)
        messages_to_unfold = db_messages if (db_messages and len(db_messages) >= len(messages)) else messages
        
        summary_messages = self._unfold_messages(messages_to_unfold)
        message_source = "outlet-db-unfolded" if db_messages and len(summary_messages) != len(messages) else "outlet-body-unfolded" if len(summary_messages) != len(messages) else "outlet-body"

        if self.valves.show_debug_log and __event_call__:
            source_progress = self._build_summary_progress_snapshot(summary_messages)
            await self._log(
                f"[Outlet] 📚 Summary source messages: {message_source} ({len(summary_messages)} msgs, body carried {len(messages)})",
                event_call=__event_call__,
            )
            await self._log(
                "[Outlet] 📐 Summary source progress snapshot: "
                + json.dumps(source_progress, ensure_ascii=False),
                event_call=__event_call__,
            )

        # Calculate target compression progress directly, then align it to an atomic
        # boundary so the saved summary never cuts through a tool-calling block.
        target_compressed_count = self._calculate_target_compressed_count(
            summary_messages
        )

        summary_body = dict(body)
        summary_body["messages"] = summary_messages

        # Process Token calculation and summary generation asynchronously in the background
        # Use a lock to prevent multiple concurrent summary tasks for the same chat
        chat_lock = self._get_chat_lock(chat_id)

        if chat_lock.locked():
            if self.valves.debug_mode:
                logger.info(
                    f"[Outlet] Skipping summary task for {chat_id}: Task already in progress"
                )
            return body

        asyncio.create_task(
            self._locked_summary_task(
                chat_lock,
                chat_id,
                model,
                summary_body,
                __user__,
                target_compressed_count,
                lang,
                __event_emitter__,
                __event_call__,
            )
        )

        return body

    async def _locked_summary_task(
        self,
        lock: asyncio.Lock,
        chat_id: str,
        model: str,
        body: dict,
        user_data: Optional[dict],
        target_compressed_count: Optional[int],
        lang: str,
        __event_emitter__: Callable,
        __event_call__: Callable,
    ):
        """Wrapper to run summary generation with an async lock."""
        async with lock:
            await self._check_and_generate_summary_async(
                chat_id,
                model,
                body,
                user_data,
                target_compressed_count,
                lang,
                __event_emitter__,
                __event_call__,
            )

    async def _check_and_generate_summary_async(
        self,
        chat_id: str,
        model: str,
        body: dict,
        user_data: Optional[dict],
        target_compressed_count: Optional[int],
        lang: str = "en-US",
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        Background processing: Calculates Token count and generates summary (does not block response).
        """

        try:
            messages = body.get("messages", [])

            # Clean model ID
            model = self._clean_model_id(model)

            if self.valves.debug_mode or self.valves.show_debug_log:
                await self._log(
                    f"\n{'='*60}\n[Outlet] Chat ID: {chat_id}\n[Outlet] Response complete\n[Outlet] Calculated target compression progress: {target_compressed_count} (Messages: {len(messages)})",
                    event_call=__event_call__,
                )
                await self._log(
                    f"[Outlet] Background processing started\n{'='*60}\n",
                    event_call=__event_call__,
                )

            # Get threshold configuration for current model
            thresholds = self._get_model_thresholds(model) or {}
            compression_threshold_tokens = thresholds.get(
                "compression_threshold_tokens", self.valves.compression_threshold_tokens
            )

            await self._log(
                f"\n[🔍 Background Calculation] Starting Token count...",
                event_call=__event_call__,
            )

            # --- Fast Estimation Check ---
            estimated_tokens = self._estimate_messages_tokens(messages)

            # For triggering summary generation, we need to be more precise if we are in the grey zone
            # Margin is 15% (skip tiktoken if estimated is < 85% of threshold)
            # Note: We still use tiktoken if we exceed threshold, because we want an accurate usage status report
            if estimated_tokens < compression_threshold_tokens * 0.85:
                current_tokens = estimated_tokens
                await self._log(
                    f"[🔍 Background Calculation] Fast estimate ({current_tokens}) is well below threshold ({compression_threshold_tokens}). Skipping tiktoken.",
                    event_call=__event_call__,
                )
            else:
                # Calculate Token count precisely in a background thread
                current_tokens = await asyncio.to_thread(
                    self._calculate_messages_tokens, messages
                )
                await self._log(
                    f"[🔍 Background Calculation] Precise token count: {current_tokens}",
                    event_call=__event_call__,
                )

            # Send status notification (Context Usage format)
            if __event_emitter__:
                max_context_tokens = thresholds.get(
                    "max_context_tokens", self.valves.max_context_tokens
                )
                if max_context_tokens > 0:
                    usage_ratio = current_tokens / max_context_tokens
                    # Only show status if threshold is met
                    if self._should_show_status(usage_ratio):
                        status_msg = self._get_translation(
                            lang,
                            "status_context_usage",
                            tokens=current_tokens,
                            max_tokens=max_context_tokens,
                            ratio=f"{usage_ratio*100:.1f}",
                        )
                        if usage_ratio > 0.9:
                            status_msg += self._get_translation(
                                lang, "status_high_usage"
                            )

                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": status_msg,
                                    "done": True,
                                },
                            }
                        )

            # Check if compression is needed
            if current_tokens >= compression_threshold_tokens:
                await self._log(
                    f"[🔍 Background Calculation] ⚡ Compression threshold triggered (Token: {current_tokens} >= {compression_threshold_tokens})",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # Proceed to generate summary
                await self._generate_summary_async(
                    messages,
                    chat_id,
                    body,
                    user_data,
                    target_compressed_count,
                    lang,
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
                log_type="error",
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
        lang: str = "en-US",
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        Generates summary asynchronously (runs in background, does not block response).
        Logic:
        1. Extract the visible message slice that maps to the next original-history boundary.
        2. If the summary model window is smaller than that slice, keep the oldest slice and trim the newest atomic groups.
        3. Generate summary for the remaining messages and save the exact covered boundary.
        """
        try:
            await self._log(
                f"\n[🤖 Async Summary Task] Starting...", event_call=__event_call__
            )

            # 1. Get target compression progress in original-history coordinates.
            if target_compressed_count is None:
                target_compressed_count = self._calculate_target_compressed_count(
                    messages
                )
                await self._log(
                    f"[🤖 Async Summary Task] ⚠️ target_compressed_count is None, estimating: {target_compressed_count}",
                    log_type="warning",
                    event_call=__event_call__,
                )

            # 2. Determine the visible message range that maps to the target original
            # compression progress.
            summary_state = self._get_summary_view_state(messages)
            summary_index = summary_state["summary_index"]
            base_progress = summary_state["base_progress"] or 0

            if summary_index is None:
                start_index = self._get_effective_keep_first(messages)
                end_index = min(len(messages), target_compressed_count)
                protected_prefix = 0
            else:
                start_index = summary_index
                end_index = min(
                    len(messages),
                    summary_index + 1 + max(0, target_compressed_count - base_progress),
                )
                protected_prefix = 1

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
                    log_type="warning",
                    event_call=__event_call__,
                )
                return

            thresholds = self._get_model_thresholds(summary_model_id)
            # Priority: 1. summary_model_max_context (if > 0) -> 2. model_thresholds -> 3. global max_context_tokens
            if self.valves.summary_model_max_context > 0:
                max_context_tokens = self.valves.summary_model_max_context
            else:
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

            if max_context_tokens <= 0:
                await self._log(
                    "[🤖 Async Summary Task] No max_context_tokens limit set (0). Skipping middle-message truncation.",
                    event_call=__event_call__,
                )
            elif estimated_input_tokens > max_context_tokens:
                excess_tokens = estimated_input_tokens - max_context_tokens
                await self._log(
                    f"[🤖 Async Summary Task] ⚠️ Middle messages ({middle_tokens} Tokens) + Buffer exceed summary model limit ({max_context_tokens}), need to remove approx {excess_tokens} Tokens",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # Trim newest messages first so saved progress still reflects the exact
                # original-history boundary actually covered by the summary.
                removed_tokens = 0
                removed_count = 0

                trimmable_middle = middle_messages[protected_prefix:]
                summary_atomic_groups = self._get_atomic_groups(trimmable_middle)
                while removed_tokens < excess_tokens and len(summary_atomic_groups) > 1:
                    group_indices = summary_atomic_groups.pop()
                    for _ in range(len(group_indices)):
                        msg_to_remove = trimmable_middle.pop()
                        msg_tokens = self._count_tokens(
                            str(msg_to_remove.get("content", ""))
                        )
                        removed_tokens += msg_tokens
                        removed_count += 1

                middle_messages = middle_messages[:protected_prefix] + trimmable_middle

                await self._log(
                    f"[🤖 Async Summary Task] Removed {removed_count} messages (atomic), totaling {removed_tokens} Tokens",
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
                            "description": self._get_translation(
                                lang, "status_generating_summary"
                            ),
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
                    log_type="warning",
                    event_call=__event_call__,
                )
                return

            if summary_index is None:
                saved_compressed_count = start_index + len(middle_messages)
            else:
                saved_compressed_count = base_progress + max(
                    0, len(middle_messages) - protected_prefix
                )

            # 6. Save new summary
            await self._log(
                "[Optimization] Saving summary in a background thread to avoid blocking the event loop.",
                event_call=__event_call__,
            )

            await asyncio.to_thread(
                self._save_summary, chat_id, new_summary, saved_compressed_count
            )

            # Send completion status notification
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": self._get_translation(
                                lang,
                                "status_loaded_summary",
                                count=len(middle_messages),
                            ),
                            "done": True,
                        },
                    }
                )

            await self._log(
                f"[🤖 Async Summary Task] ✅ Complete! New summary length: {len(new_summary)} characters",
                log_type="success",
                event_call=__event_call__,
            )
            await self._log(
                f"[🤖 Async Summary Task] Progress update: Compressed up to original message {saved_compressed_count}",
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

                    # 2. Construct Next Context using the saved original-history boundary.
                    next_summary_msg = self._build_summary_message(
                        new_summary, lang, saved_compressed_count
                    )
                    if summary_index is None:
                        effective_keep_first = self._get_effective_keep_first(messages)
                        head_msgs = (
                            messages[:effective_keep_first]
                            if effective_keep_first > 0
                            else []
                        )
                        visible_tail_start = max(
                            saved_compressed_count, effective_keep_first
                        )
                    else:
                        head_msgs = messages[:summary_index]
                        visible_tail_start = (
                            summary_index
                            + 1
                            + max(0, saved_compressed_count - base_progress)
                        )

                    tail_msgs = messages[visible_tail_start:]

                    # Assemble
                    next_context = head_msgs + [next_summary_msg] + tail_msgs

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
                    # 6. Emit Status (only if threshold is met)
                    if max_context_tokens > 0:
                        usage_ratio = token_count / max_context_tokens
                        # Only show status if threshold is met
                        if self._should_show_status(usage_ratio):
                            status_msg = self._get_translation(
                                lang,
                                "status_context_usage",
                                tokens=token_count,
                                max_tokens=max_context_tokens,
                                ratio=f"{usage_ratio*100:.1f}",
                            )
                            if usage_ratio > 0.9:
                                status_msg += self._get_translation(
                                    lang, "status_high_usage"
                                )

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
                        log_type="error",
                        event_call=__event_call__,
                    )

        except Exception as e:
            await self._log(
                f"[🤖 Async Summary Task] ❌ Error: {str(e)}",
                log_type="error",
                event_call=__event_call__,
            )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": self._get_translation(
                                lang, "status_summary_error", error=str(e)[:100]
                            ),
                            "done": True,
                        },
                    }
                )

            import traceback

            logger.exception("[🤖 Async Summary Task] Unhandled exception")

    def _format_messages_for_summary(self, messages: list) -> str:
        """
        Formats messages for summarization with metadata awareness.
        Preserves IDs, names, and key metadata fragments to ensure traceability.
        """
        formatted = []
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Extract Identity Metadata
            msg_id = msg.get("id", "N/A")
            msg_name = msg.get("name", "")
            # Only pick non-system, interesting metadata keys
            metadata = msg.get("metadata", {})
            safe_meta = {
                k: v
                for k, v in metadata.items()
                if k not in ["is_trimmed", "is_summary"]
            }

            # Handle multimodal content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                content = " ".join(text_parts)

            # Handle role name
            role_name = {"user": "User", "assistant": "Assistant"}.get(role, role)

            meta_str = f" [ID: {msg_id}]"
            if msg_name:
                meta_str += f" [Name: {msg_name}]"
            if safe_meta:
                meta_str += f" [Meta: {safe_meta}]"

            formatted.append(f"[{i}] {role_name}{meta_str}: {content}")

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

### Identity Traceability
The input dialogue contains message IDs (e.g., [ID: ...]) and optional names. 
If a specific message contributes a critical decision, a unique code snippet, or a tool-calling result, please reference its ID or Name in your summary to maintain traceability.

---
{new_conversation_text}
---

Based on the content above, generate the summary (including key message identities where relevant):
"""
        # Determine the model to use
        model = self._clean_model_id(self.valves.summary_model) or self._clean_model_id(
            body.get("model")
        )

        if not model:
            await self._log(
                "[🤖 LLM Call] ⚠️ Summary model does not exist, skipping summary generation",
                log_type="warning",
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

            # Handle JSONResponse (some backends return JSONResponse instead of dict)
            if hasattr(response, "body"):
                # It's a Response object, extract the body
                import json as json_module

                try:
                    response = json_module.loads(response.body.decode("utf-8"))
                except Exception:
                    raise ValueError(f"Failed to parse JSONResponse body: {response}")

            if (
                not response
                or not isinstance(response, dict)
                or "choices" not in response
                or not response["choices"]
            ):
                raise ValueError(
                    f"LLM response format incorrect or empty: {type(response).__name__}"
                )

            summary = response["choices"][0]["message"]["content"].strip()

            await self._log(
                f"[🤖 LLM Call] ✅ Successfully received summary",
                log_type="success",
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
                log_type="error",
                event_call=__event_call__,
            )

            raise Exception(error_message)
