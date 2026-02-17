"""
title: 异步上下文压缩
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
description: 通过智能摘要和消息压缩，降低长对话的 token 消耗，同时保持对话连贯性。
version: 1.3.0
openwebui_id: 5c0617cb-a9e4-4bd6-a440-d276534ebd18
license: MIT

═══════════════════════════════════════════════════════════════════════════════
📌 1.3.0 版本更新
═══════════════════════════════════════════════════════════════════════════════

  ✅ 智能状态显示：新增 `token_usage_status_threshold` 阀门（默认 80%），用于控制 Token 使用状态的显示时机，减少不必要的通知。
  ✅ Copilot SDK 集成：自动检测并跳过基于 copilot_sdk 的模型压缩，防止冲突。
  ✅ 用户体验改进：状态消息仅在 Token 使用率超过配置阈值时显示，保持界面更清爽。

═══════════════════════════════════════════════════════════════════════════════
📌 功能概述
═══════════════════════════════════════════════════════════════════════════════

本过滤器通过智能摘要和消息压缩技术，显著降低长对话的 token 消耗，同时保持对话连贯性。

核心特性：
  ✅ 自动触发压缩（基于 Token 数量阈值）
  ✅ 异步生成摘要（不阻塞用户响应）
  ✅ 数据库持久化存储（支持 PostgreSQL 和 SQLite）
  ✅ 灵活的保留策略（可配置保留对话的头部和尾部）
  ✅ 智能注入摘要，保持上下文连贯性

═══════════════════════════════════════════════════════════════════════════════
🔄 工作流程
═══════════════════════════════════════════════════════════════════════════════

阶段 1: inlet（请求前处理）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 接收当前对话的所有消息。
  2. 检查是否存在已保存的摘要。
  3. 如果有摘要且消息数超过保留阈值：
     ├─ 提取要保留的头部消息（例如，第一条消息）。
     ├─ 将摘要注入到头部消息中。
     ├─ 提取要保留的尾部消息。
     └─ 组合成新的消息列表：[头部消息+摘要] + [尾部消息]。
  4. 发送压缩后的消息到 LLM。

阶段 2: outlet（响应后处理）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. LLM 响应完成后触发。
  2. 检查 Token 数是否达到压缩阈值。
  3. 如果达到 Token 阈值，则在后台异步生成摘要：
     ├─ 提取需要摘要的消息（排除保留的头部和尾部）。
     ├─ 调用 LLM 生成简洁摘要。
     └─ 将摘要保存到数据库。

═══════════════════════════════════════════════════════════════════════════════
💾 存储方案
═══════════════════════════════════════════════════════════════════════════════

本过滤器使用 Open WebUI 的共享数据库连接进行持久化存储。
它自动复用 Open WebUI 内部的 SQLAlchemy 引擎和 SessionLocal，
使插件与数据库类型无关，并确保与 Open WebUI 支持的任何数据库后端
（PostgreSQL、SQLite 等）兼容。

无需额外的数据库配置 - 插件自动继承 Open WebUI 的数据库设置。

  表结构：
    - id: 主键（自增）
    - chat_id: 对话唯一标识（唯一索引）
    - summary: 摘要内容（TEXT）
    - compressed_message_count: 原始消息数
    - created_at: 创建时间
    - updated_at: 更新时间

═══════════════════════════════════════════════════════════════════════════════
📊 压缩效果示例
═══════════════════════════════════════════════════════════════════════════════

场景：20 条消息的对话 (默认设置: 保留前 1 条, 后 6 条)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  压缩前：
    消息 1: [初始设定 + 初始问题]
    消息 2-14: [历史对话内容]
    消息 15-20: [最近对话]
    总计: 20 条完整消息

  压缩后：
    消息 1: [初始设定 + 历史摘要 + 初始问题]
    消息 15-20: [最近 6 条完整消息]
    总计: 7 条消息

  效果：
    ✓ 节省 13 条消息（约 65%）
    ✓ 保留完整上下文信息
    ✓ 保护重要的初始设定

═══════════════════════════════════════════════════════════════════════════════
⚙️ 配置参数说明
═══════════════════════════════════════════════════════════════════════════════

priority (优先级)
  默认: 10
  说明: 过滤器执行顺序，数值越小越先执行。

compression_threshold_tokens (压缩阈值 Token)
  默认: 64000
  说明: 当上下文总 Token 数超过此值时，触发压缩。
  建议: 根据模型上下文窗口和成本调整。

max_context_tokens (最大上下文 Token)
  默认: 128000
  说明: 上下文的硬性上限。超过此值将强制移除最早的消息。

model_thresholds (模型特定阈值)
  默认: {}
  说明: 针对特定模型的阈值覆盖配置。
  示例: {"gpt-4": {"compression_threshold_tokens": 8000, "max_context_tokens": 32000}}

keep_first (保留初始消息数)
  默认: 1
  说明: 始终保留对话开始的 N 条消息。设置为 0 则不保留。第一条消息通常包含重要的提示或环境变量。

keep_last (保留最近消息数)
  默认: 6
  说明: 始终保留对话末尾的 N 条完整消息，以确保上下文的连贯性。

summary_model (摘要模型)
  默认: None
  说明: 用于生成摘要的 LLM 模型。
  建议:
    - 强烈建议配置一个快速且经济的兼容模型，如 `deepseek-v3`、`gemini-2.5-flash`、`gpt-4.1`。
    - 如果留空，过滤器将尝试使用当前对话的模型。
  注意:
    - 如果当前对话使用的是流水线（Pipe）模型或不直接支持标准生成API的模型，留空此项可能会导致摘要生成失败。在这种情况下，必须指定一个有效的模型。

max_summary_tokens (摘要长度)
  默认: 16384
  说明: 生成摘要时允许的最大 token 数。

summary_temperature (摘要温度)
  默认: 0.3
  说明: 控制摘要生成的随机性，较低的值会产生更确定性的输出。

debug_mode (调试模式)
  默认: true
  说明: 在日志中打印详细的调试信息。生产环境建议设为 `false`。

show_debug_log (前端调试日志)
  默认: false
  说明: 在浏览器控制台打印调试日志 (F12)。便于前端调试。

🔧 部署配置
═══════════════════════════════════════════════════════

插件自动使用 Open WebUI 的共享数据库连接。
无需额外的数据库配置。

过滤器安装顺序建议：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
建议将此过滤器的优先级设置得相对较高（数值较小），以确保它在其他可能修改消息内容的过滤器之前运行。一个典型的顺序可能是：

  1. 需要访问完整、未压缩历史记录的过滤器 (priority < 10)
     (例如: 注入系统级提示的过滤器)
  2. 本压缩过滤器 (priority = 10)
  3. 在压缩后运行的过滤器 (priority > 10)
     (例如: 最终输出格式化过滤器)

═══════════════════════════════════════════════════════════════════════════════
📝 数据库查询示例
═══════════════════════════════════════════════════════════════════════════════

查看所有摘要：
  SELECT
    chat_id,
    LEFT(summary, 100) as summary_preview,
    compressed_message_count,
    updated_at
  FROM chat_summary
  ORDER BY updated_at DESC;

查询特定对话：
  SELECT *
  FROM chat_summary
  WHERE chat_id = 'your_chat_id';

删除过期摘要：
  DELETE FROM chat_summary
  WHERE updated_at < NOW() - INTERVAL '30 days';

统计信息：
  SELECT
    COUNT(*) as total_summaries,
    AVG(LENGTH(summary)) as avg_summary_length,
    AVG(compressed_message_count) as avg_msg_count
  FROM chat_summary;

═══════════════════════════════════════════════════════════════════════════════
⚠️ 注意事项
═══════════════════════════════════════════════════════════════════════════════

1. 数据库连接
   ✓ 插件自动使用 Open WebUI 的共享数据库连接。
   ✓ 无需额外配置。
   ✓ 首次运行会自动创建 `chat_summary` 表。

2. 保留策略
   ⚠ `keep_first` 配置对于保留包含提示或环境变量的初始消息非常重要。请根据需要进行配置。

3. 性能考虑
   ⚠ 摘要生成是异步的，不会阻塞用户响应。
   ⚠ 首次达到阈值时会有短暂的后台处理时间。

4. 成本优化
   ⚠ 每次达到阈值会调用一次摘要模型。
   ⚠ 合理设置 `compression_threshold_tokens` 避免频繁调用。
   ⚠ 建议使用快速且经济的模型（如 `gemini-flash`）生成摘要。

5. 多模态支持
   ✓ 本过滤器支持包含图片的多模态消息。
   ✓ 摘要仅针对文本内容生成。
   ✓ 在压缩过程中，非文本部分（如图片）会被保留在原始消息中。

═══════════════════════════════════════════════════════════════════════════════
🐛 故障排除
═══════════════════════════════════════════════════════════════════════════════

问题：数据库表未创建
解决：
  1. 确保 Open WebUI 已正确配置数据库。
  2. 查看 Open WebUI 的容器日志以获取详细的错误信息。
  3. 验证 Open WebUI 的数据库连接是否正常工作。

问题：摘要未生成
解决：
  1. 检查是否达到 `compression_threshold_tokens`。
  2. 查看 `summary_model` 是否配置正确。
  3. 检查调试日志中的错误信息。

问题：初始的提示或环境变量丢失
解决：
  - 确保 `keep_first` 设置为大于 0 的值，以保留包含这些信息的初始消息。

问题：压缩效果不明显
解决：
  1. 适当提高 `compression_threshold_tokens`。
  2. 减少 `keep_last` 或 `keep_first` 的数量。
  3. 检查对话是否真的很长。


"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List, Union, Callable, Awaitable
import re
import asyncio
import json
import hashlib
import contextlib
import logging

# 配置日志记录
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Open WebUI 内置导入
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.models.models import Models
from fastapi.requests import Request
from open_webui.main import app as webui_app

# Open WebUI 内部数据库 (复用共享连接)
try:
    from open_webui.internal import db as owui_db
except ModuleNotFoundError:  # pragma: no cover - filter runs inside Open WebUI
    owui_db = None

# 尝试导入 tiktoken
try:
    import tiktoken
except ImportError:
    tiktoken = None

# 数据库导入
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
    """对话摘要存储表"""

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


class Filter:
    def __init__(self):
        self.valves = self.Valves()
        self._owui_db = owui_db
        self._db_engine = owui_engine
        self._fallback_session_factory = (
            sessionmaker(bind=self._db_engine) if self._db_engine else None
        )
        self._threshold_cache = {}
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
        """使用 Open WebUI 的共享连接初始化数据库表"""
        try:
            if self._db_engine is None:
                raise RuntimeError(
                    "Open WebUI database engine is unavailable. Ensure Open WebUI is configured with a valid DATABASE_URL."
                )

            # 使用 SQLAlchemy inspect 检查表是否存在
            inspector = inspect(self._db_engine)
            if not inspector.has_table("chat_summary"):
                # 如果表不存在则创建
                ChatSummary.__table__.create(bind=self._db_engine, checkfirst=True)
                print(
                    "[数据库] ✅ 使用 Open WebUI 的共享数据库连接成功创建 chat_summary 表。"
                )
            else:
                print(
                    "[数据库] ✅ 使用 Open WebUI 的共享数据库连接。chat_summary 表已存在。"
                )

        except Exception as e:
            print(f"[数据库] ❌ 初始化失败: {str(e)}")

    class Valves(BaseModel):
        priority: int = Field(
            default=10, description="Priority level for the filter operations."
        )
        # Token 相关参数
        compression_threshold_tokens: int = Field(
            default=64000,
            ge=0,
            description="当上下文总 Token 数超过此值时，触发压缩 (全局默认值)",
        )
        max_context_tokens: int = Field(
            default=128000,
            ge=0,
            description="上下文的硬性上限。超过此值将强制移除最早的消息 (全局默认值)",
        )
        model_thresholds: Union[str, dict] = Field(
            default={},
            description="针对特定模型的阈值覆盖配置。可以是 JSON 字符串或字典。",
        )

        @model_validator(mode="before")
        @classmethod
        def parse_model_thresholds(cls, data: Any) -> Any:
            if isinstance(data, dict):
                thresholds = data.get("model_thresholds")
                if isinstance(thresholds, str) and thresholds.strip():
                    try:
                        data["model_thresholds"] = json.loads(thresholds)
                    except Exception as e:
                        logger.error(f"Failed to parse model_thresholds JSON: {e}")
            return data

        keep_first: int = Field(
            default=1, ge=0, description="始终保留最初的 N 条消息。设置为 0 则不保留。"
        )
        keep_last: int = Field(
            default=6, ge=0, description="始终保留最近的 N 条完整消息。"
        )
        summary_model: Optional[str] = Field(
            default=None,
            description="用于生成摘要的模型 ID。留空则使用当前对话的模型。用于匹配 model_thresholds 中的配置。",
        )
        summary_model_max_context: int = Field(
            default=0,
            ge=0,
            description="摘要模型的最大上下文 Token 数。如果为 0，则回退到 model_thresholds 或全局 max_context_tokens。",
        )
        max_summary_tokens: int = Field(
            default=16384, ge=1, description="摘要的最大 token 数"
        )
        summary_temperature: float = Field(
            default=0.1, ge=0.0, le=2.0, description="摘要生成的温度参数"
        )
        debug_mode: bool = Field(default=True, description="调试模式，打印详细日志")
        show_debug_log: bool = Field(
            default=False, description="在浏览器控制台打印调试日志 (F12)"
        )
        show_token_usage_status: bool = Field(
            default=True, description="在对话结束时显示 Token 使用情况的状态通知"
        )
        token_usage_status_threshold: int = Field(
            default=80,
            ge=0,
            le=100,
            description="仅当 Token 使用率超过此百分比（0-100）时才显示状态。设为 0 表示始终显示。",
        )
        enable_tool_output_trimming: bool = Field(
            default=False,
            description="启用原生工具输出裁剪 (仅适用于 native function calling)，裁剪过长的工具输出以节省 Token。",
        )

    def _save_summary(self, chat_id: str, summary: str, compressed_count: int):
        """保存摘要到数据库"""
        try:
            with self._db_session() as session:
                # 查找现有记录
                existing = session.query(ChatSummary).filter_by(chat_id=chat_id).first()

                if existing:
                    # [优化] 乐观锁检查：只有进度向前推进时才更新
                    if compressed_count <= existing.compressed_message_count:
                        if self.valves.debug_mode:
                            logger.debug(
                                f"[存储] 跳过更新：新进度 ({compressed_count}) 不大于现有进度 ({existing.compressed_message_count})"
                            )
                        return

                    # 更新现有记录
                    existing.summary = summary
                    existing.compressed_message_count = compressed_count
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # 创建新记录
                    new_summary = ChatSummary(
                        chat_id=chat_id,
                        summary=summary,
                        compressed_message_count=compressed_count,
                    )
                    session.add(new_summary)

                session.commit()

                if self.valves.debug_mode:
                    action = "更新" if existing else "创建"
                    logger.info(f"[存储] 摘要已{action}到数据库 (Chat ID: {chat_id})")

        except Exception as e:
            logger.error(f"[存储] ❌ 数据库保存失败: {str(e)}")

    def _load_summary_record(self, chat_id: str) -> Optional[ChatSummary]:
        """从数据库加载摘要记录对象"""
        try:
            with self._db_session() as session:
                record = session.query(ChatSummary).filter_by(chat_id=chat_id).first()
                if record:
                    # Detach the object from the session so it can be used after session close
                    session.expunge(record)
                    return record
        except Exception as e:
            logger.error(f"[加载] ❌ 数据库读取失败: {str(e)}")
        return None

    def _load_summary(self, chat_id: str, body: dict) -> Optional[str]:
        """从数据库加载摘要文本 (兼容旧接口)"""
        record = self._load_summary_record(chat_id)
        if record:
            if self.valves.debug_mode:
                logger.debug(f"[加载] 从数据库加载摘要 (Chat ID: {chat_id})")
                logger.debug(
                    f"[加载] 更新时间: {record.updated_at}, 已压缩消息数: {record.compressed_message_count}"
                )
            return record.summary
        return None

    def _count_tokens(self, text: str) -> int:
        """计算文本的 Token 数量"""
        if not text:
            return 0

        if tiktoken:
            try:
                # 统一使用 o200k_base 编码 (适配最新模型)
                encoding = tiktoken.get_encoding("o200k_base")
                return len(encoding.encode(text))
            except Exception as e:
                if self.valves.debug_mode:
                    print(f"[Token计数] tiktoken 错误: {e}，回退到字符估算")

        # 回退策略：粗略估算 (1 token ≈ 4 chars)
        return len(text) // 4

    def _calculate_messages_tokens(self, messages: List[Dict]) -> int:
        """计算消息列表的总 Token 数"""
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                # 多模态内容处理
                text_content = ""
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_content += part.get("text", "")
                total_tokens += self._count_tokens(text_content)
            else:
                total_tokens += self._count_tokens(str(content))
        return total_tokens

    def _get_model_thresholds(self, model_id: str) -> Dict[str, int]:
        """获取特定模型的阈值配置

        优先级：
        1. 缓存匹配
        2. model_thresholds 直接匹配
        3. 基础模型 (base_model_id) 匹配
        4. 全局默认配置
        """
        if not model_id:
            return {
                "compression_threshold_tokens": self.valves.compression_threshold_tokens,
                "max_context_tokens": self.valves.max_context_tokens,
            }

        # 1. 检查缓存
        if model_id in self._threshold_cache:
            return self._threshold_cache[model_id]

        # 获取解析后的阈值配置
        parsed = self.valves.model_thresholds
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except Exception:
                parsed = {}

        # 2. 尝试直接匹配
        if model_id in parsed:
            res = parsed[model_id]
            self._threshold_cache[model_id] = res
            if self.valves.debug_mode:
                logger.debug(f"[配置] 模型 {model_id} 命中直接配置")
            return res

        # 3. 尝试匹配基础模型 (base_model_id)
        try:
            model_obj = Models.get_model_by_id(model_id)
            if model_obj:
                # 某些模型可能有多个基础模型 ID
                base_ids = []
                if hasattr(model_obj, "base_model_id") and model_obj.base_model_id:
                    base_ids.append(model_obj.base_model_id)
                if hasattr(model_obj, "base_model_ids") and model_obj.base_model_ids:
                    if isinstance(model_obj.base_model_ids, list):
                        base_ids.extend(model_obj.base_model_ids)

                for b_id in base_ids:
                    if b_id in parsed:
                        res = parsed[b_id]
                        self._threshold_cache[model_id] = res
                        if self.valves.debug_mode:
                            logger.info(
                                f"[配置] 模型 {model_id} 匹配到基础模型 {b_id} 的配置"
                            )
                        return res
        except Exception as e:
            logger.error(f"[配置] 查找基础模型失败: {e}")

        # 4. 使用全局默认配置
        res = {
            "compression_threshold_tokens": self.valves.compression_threshold_tokens,
            "max_context_tokens": self.valves.max_context_tokens,
        }
        self._threshold_cache[model_id] = res
        return res

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        统一提取聊天上下文信息 (chat_id, message_id)。
        优先从 body 中提取，其次从 metadata 中提取。
        """
        chat_id = ""
        message_id = ""

        # 1. 尝试从 body 获取
        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")  # message_id 在 body 中通常是 id

            # 再次检查 body.metadata
            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        # 2. 尝试从 __metadata__ 获取 (作为补充)
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

    async def _log(self, message: str, log_type: str = "info", event_call=None):
        """统一日志输出到后端 (print) 和前端 (console.log)"""
        # 后端日志
        if self.valves.debug_mode:
            print(message)

        # 前端日志
        if self.valves.show_debug_log and event_call:
            try:
                css = "color: #3b82f6;"  # 默认蓝色
                if log_type == "error":
                    css = "color: #ef4444; font-weight: bold;"  # 红色
                elif log_type == "warning":
                    css = "color: #f59e0b;"  # 橙色
                elif log_type == "success":
                    css = "color: #10b981; font-weight: bold;"  # 绿色

                # 清理前端消息：移除分隔符和多余换行
                lines = message.split("\n")
                # 保留不以大量等号或连字符开头的行
                filtered_lines = [
                    line
                    for line in lines
                    if not line.strip().startswith("====")
                    and not line.strip().startswith("----")
                ]
                clean_message = "\n".join(filtered_lines).strip()

                if not clean_message:
                    return

                # 转义消息中的引号和换行符
                safe_message = clean_message.replace('"', '\\"').replace("\n", "\\n")

                js_code = f"""
                    console.log("%c[压缩] {safe_message}", "{css}");
                """
                await event_call({"type": "execute", "data": {"code": js_code}})
            except Exception as e:
                logger.error(f"发送前端日志失败: {e}")

    def _should_show_status(self, usage_ratio: float) -> bool:
        """
        根据阈值检查是否应该显示 Token 使用状态。
        
        Args:
            usage_ratio: 当前使用率（0.0 到 1.0）
            
        Returns:
            如果应该显示状态则返回 True，否则返回 False
        """
        if not self.valves.show_token_usage_status:
            return False
        
        # 如果阈值为 0，则始终显示
        if self.valves.token_usage_status_threshold == 0:
            return True
        
        # 检查使用率是否超过阈值
        threshold_ratio = self.valves.token_usage_status_threshold / 100.0
        return usage_ratio >= threshold_ratio

    def _should_skip_compression(self, body: dict, __model__: Optional[dict] = None) -> bool:
        """
        检查是否应该跳过压缩。
        返回 True 如果：
        1. 基础模型包含 'copilot_sdk'
        """
        # 检查基础模型是否包含 copilot_sdk
        if __model__:
            base_model_id = __model__.get("base_model_id", "")
            if "copilot_sdk" in base_model_id.lower():
                return True
        
        # 同时检查 body 中的模型
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
        在发送到 LLM 之前执行
        压缩策略：
        1. 注入已有摘要
        2. 预检 Token 预算
        3. 如果超限，执行结构化裁剪（Structure-Aware Trimming）或丢弃旧消息
        """
        
        # 检查是否应该跳过压缩（例如，copilot_sdk）
        if self._should_skip_compression(body, __model__):
            if self.valves.debug_mode:
                logger.info("[Inlet] 跳过压缩：检测到 copilot_sdk 基础模型")
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    "[Inlet] ⏭️ 跳过压缩：检测到 copilot_sdk",
                    event_call=__event_call__,
                )
            return body
        
        messages = body.get("messages", [])

        # --- 原生工具输出裁剪 (Native Tool Output Trimming) ---
        metadata = body.get("metadata", {})
        is_native_func_calling = metadata.get("function_calling") == "native"

        if self.valves.enable_tool_output_trimming and is_native_func_calling:
            trimmed_count = 0
            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str):
                    continue

                role = msg.get("role")

                # 仅处理带有原生工具输出的助手消息
                if role == "assistant":
                    # 检测助手内容中的工具输出标记
                    if "tool_call_id:" in content or (
                        content.startswith('"') and "\\&quot;" in content
                    ):
                        if self.valves.show_debug_log and __event_call__:
                            await self._log(
                                f"[Inlet] 🔍 检测到助手消息中的原生工具输出。",
                                event_call=__event_call__,
                            )

                        # 提取最终答案（在最后一个工具调用元数据之后）
                        # 模式：匹配转义的 JSON 字符串，如 ""&quot;...&quot;"" 后跟换行符
                        # 我们寻找该模式的最后一次出现，并获取其后的所有内容

                        # 1. 尝试匹配特定的 OpenWebUI 工具输出格式：""&quot;...&quot;""
                        tool_output_pattern = r'""&quot;.*?&quot;""\s*'

                        # 查找所有匹配项
                        matches = list(
                            re.finditer(tool_output_pattern, content, re.DOTALL)
                        )

                        if matches:
                            # 获取最后一个匹配项的结束位置
                            last_match_end = matches[-1].end()

                            # 最后一个工具输出之后的所有内容即为最终答案
                            final_answer = content[last_match_end:].strip()

                            if final_answer:
                                msg["content"] = (
                                    f"... [Tool outputs trimmed]\n{final_answer}"
                                )
                                trimmed_count += 1
                        else:
                            # 回退：如果找不到新格式，尝试按 "Arguments:" 分割
                            # (保留向后兼容性或适应不同模型行为)
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
                    f"[Inlet] ✂️ 已裁剪 {trimmed_count} 条工具输出消息。",
                    event_call=__event_call__,
                )

        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]

        # 提取系统提示词以进行准确的 Token 计算
        # 1. 对于自定义模型：检查数据库 (Models.get_model_by_id)
        # 2. 对于基础模型：检查消息中的 role='system'
        system_prompt_content = None

        # 尝试从数据库获取 (自定义模型)
        try:
            model_id = body.get("model")
            if model_id:
                if self.valves.show_debug_log and __event_call__:
                    await self._log(
                        f"[Inlet] 🔍 尝试从数据库查找模型: {model_id}",
                        event_call=__event_call__,
                    )

                # 清理模型 ID
                model_obj = Models.get_model_by_id(model_id)

                if model_obj:
                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] ✅ 数据库中找到模型: {model_obj.name} (ID: {model_obj.id})",
                            event_call=__event_call__,
                        )

                    if model_obj.params:
                        try:
                            params = model_obj.params
                            # 处理 params 是 JSON 字符串的情况
                            if isinstance(params, str):
                                params = json.loads(params)
                            # 转换 Pydantic 模型为字典
                            elif hasattr(params, "model_dump"):
                                params = params.model_dump()
                            elif hasattr(params, "dict"):
                                params = params.dict()

                            # 处理字典
                            if isinstance(params, dict):
                                system_prompt_content = params.get("system")
                            else:
                                # 回退：尝试 getattr
                                system_prompt_content = getattr(params, "system", None)

                            if system_prompt_content:
                                if self.valves.show_debug_log and __event_call__:
                                    await self._log(
                                        f"[Inlet] 📝 在数据库参数中找到系统提示词 ({len(system_prompt_content)} 字符)",
                                        event_call=__event_call__,
                                    )
                            else:
                                if self.valves.show_debug_log and __event_call__:
                                    await self._log(
                                        f"[Inlet] ⚠️ 模型参数中缺少 'system' 键",
                                        event_call=__event_call__,
                                    )
                        except Exception as e:
                            if self.valves.show_debug_log and __event_call__:
                                await self._log(
                                    f"[Inlet] ❌ 解析模型参数失败: {e}",
                                    log_type="error",
                                    event_call=__event_call__,
                                )

                    else:
                        if self.valves.show_debug_log and __event_call__:
                            await self._log(
                                f"[Inlet] ⚠️ 模型参数为空",
                                event_call=__event_call__,
                            )
                else:
                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] ❌ 数据库中未找到模型",
                            log_type="warning",
                            event_call=__event_call__,
                        )

        except Exception as e:
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    f"[Inlet] ❌ 从数据库获取系统提示词错误: {e}",
                    log_type="error",
                    event_call=__event_call__,
                )
            if self.valves.debug_mode:
                logger.error(f"[Inlet] 从数据库获取系统提示词错误: {e}")

        # 回退：检查消息列表 (基础模型或已包含)
        if not system_prompt_content:
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt_content = msg.get("content", "")
                    break

        # 构建 system_prompt_msg 用于 Token 计算
        system_prompt_msg = None
        if system_prompt_content:
            system_prompt_msg = {"role": "system", "content": system_prompt_content}
            if self.valves.debug_mode:
                logger.debug(
                    f"[Inlet] 找到系统提示词 ({len(system_prompt_content)} 字符)。计入预算。"
                )

        # 记录消息统计信息 (移至此处以包含提取的系统提示词)
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

                # 如果系统提示词是从 DB/Model 提取的但不在消息中，则计数
                if system_prompt_content:
                    # 检查是否已计数 (即是否在消息中)
                    is_in_messages = any(m.get("role") == "system" for m in messages)
                    if not is_in_messages:
                        msg_stats["system"] += 1
                        msg_stats["total"] += 1

                stats_str = f"Total: {msg_stats['total']} | User: {msg_stats['user']} | Assistant: {msg_stats['assistant']} | System: {msg_stats['system']}"
                await self._log(
                    f"[Inlet] 消息统计: {stats_str}", event_call=__event_call__
                )
            except Exception as e:
                logger.error(f"[Inlet] 记录消息统计错误: {e}")

        if not chat_id:
            await self._log(
                "[Inlet] ❌ metadata 中缺少 chat_id，跳过压缩",
                log_type="error",
                event_call=__event_call__,
            )
            return body

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Inlet] Chat ID: {chat_id}\n[Inlet] 收到 {len(messages)} 条消息",
                event_call=__event_call__,
            )

        # 记录原始消息的目标压缩进度，供 outlet 使用
        # 目标是压缩到倒数第 keep_last 条之前
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        await self._log(
            f"[Inlet] 记录目标压缩进度: {target_compressed_count}",
            event_call=__event_call__,
        )

        # 加载摘要记录
        summary_record = await asyncio.to_thread(self._load_summary_record, chat_id)

        # 计算 effective_keep_first 以确保所有系统消息都被保护
        last_system_index = -1
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                last_system_index = i

        effective_keep_first = max(self.valves.keep_first, last_system_index + 1)

        final_messages = []

        if summary_record:
            # 存在摘要，构建视图：[Head] + [Summary Message] + [Tail]
            # Tail 是从上次压缩点之后的所有消息
            compressed_count = summary_record.compressed_message_count

            # 确保 compressed_count 合理
            if compressed_count > len(messages):
                compressed_count = max(0, len(messages) - self.valves.keep_last)

            # 1. 头部消息 (Keep First)
            head_messages = []
            if effective_keep_first > 0:
                head_messages = messages[:effective_keep_first]

            # 2. 摘要消息 (作为 User 消息插入)
            summary_content = (
                f"【系统提示：以下是历史对话的摘要，仅供参考上下文，请勿对摘要内容进行回复，直接回答后续的最新问题】\n\n"
                f"{summary_record.summary}\n\n"
                f"---\n"
                f"以下是最近的对话："
            )
            summary_msg = {"role": "assistant", "content": summary_content}

            # 3. 尾部消息 (Tail) - 从上次压缩点开始的所有消息
            # 注意：这里必须确保不重复包含头部消息
            start_index = max(compressed_count, effective_keep_first)
            tail_messages = messages[start_index:]

            if self.valves.show_debug_log and __event_call__:
                tail_preview = [
                    f"{i + start_index}: [{m.get('role')}] {m.get('content', '')[:30]}..."
                    for i, m in enumerate(tail_messages)
                ]
                await self._log(
                    f"[Inlet] 📜 尾部消息 (起始索引: {start_index}): {tail_preview}",
                    event_call=__event_call__,
                )

            # --- 预检检查与预算 (Preflight Check & Budgeting) ---

            # 组装候选消息 (用于输出)
            candidate_messages = head_messages + [summary_msg] + tail_messages

            # 准备用于 Token 计算的消息 (如果缺少则包含系统提示词)
            calc_messages = candidate_messages
            if system_prompt_msg:
                # 检查系统提示词是否已在 head_messages 中
                is_in_head = any(m.get("role") == "system" for m in head_messages)
                if not is_in_head:
                    calc_messages = [system_prompt_msg] + candidate_messages

            # 获取最大上下文限制
            model = self._clean_model_id(body.get("model"))
            thresholds = self._get_model_thresholds(model) or {}
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            # 计算总 Token
            total_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, calc_messages
            )

            # 预检检查日志
            await self._log(
                f"[Inlet] 🔎 预检检查: {total_tokens}t / {max_context_tokens}t ({(total_tokens/max_context_tokens*100):.1f}%)",
                event_call=__event_call__,
            )

            # 如果超出预算，缩减历史记录 (Keep Last)
            if total_tokens > max_context_tokens:
                await self._log(
                    f"[Inlet] ⚠️ 候选提示词 ({total_tokens} Tokens) 超过上限 ({max_context_tokens})。正在缩减历史记录...",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # 动态从 tail_messages 的开头移除消息
                # 始终尝试保留至少最后一条消息 (通常是用户输入)
                while total_tokens > max_context_tokens and len(tail_messages) > 1:
                    # 策略 1: 结构化助手消息裁剪 (Structure-Aware Assistant Trimming)
                    # 保留: 标题 (#), 第一行, 最后一行。折叠其余部分。
                    target_msg = None
                    target_idx = -1

                    # 查找最旧的、较长且尚未裁剪的助手消息
                    for i, msg in enumerate(tail_messages):
                        # 跳过最后一条消息 (通常是用户输入，保护它)
                        if i == len(tail_messages) - 1:
                            break

                        if msg.get("role") == "assistant":
                            content = str(msg.get("content", ""))
                            is_trimmed = msg.get("metadata", {}).get(
                                "is_trimmed", False
                            )
                            # 仅针对相当长 (> 200 字符) 的消息
                            if len(content) > 200 and not is_trimmed:
                                target_msg = msg
                                target_idx = i
                                break

                    # 如果找到合适的助手消息，应用结构化裁剪
                    if target_msg:
                        content = str(target_msg.get("content", ""))
                        lines = content.split("\n")
                        kept_lines = []

                        # 逻辑: 保留标题, 第一行非空行, 最后一行非空行
                        first_line_found = False
                        last_line_idx = -1

                        # 查找最后一行非空行的索引
                        for idx in range(len(lines) - 1, -1, -1):
                            if lines[idx].strip():
                                last_line_idx = idx
                                break

                        for idx, line in enumerate(lines):
                            stripped = line.strip()
                            if not stripped:
                                continue

                            # 保留标题 (H1-H6, 需要 # 后有空格)
                            if re.match(r"^#{1,6}\s+", stripped):
                                kept_lines.append(line)
                                continue

                            # 保留第一行非空行
                            if not first_line_found:
                                kept_lines.append(line)
                                first_line_found = True
                                # 如果后面还有内容，添加占位符
                                if idx < last_line_idx:
                                    kept_lines.append("\n... [Content collapsed] ...\n")
                                continue

                            # 保留最后一行非空行
                            if idx == last_line_idx:
                                kept_lines.append(line)
                                continue

                        # 更新消息内容
                        new_content = "\n".join(kept_lines)

                        # 安全检查: 如果裁剪没有节省太多 (例如主要是标题)，则强制丢弃
                        if len(new_content) > len(content) * 0.8:
                            # 如果结构保留过于冗长，回退到丢弃
                            pass
                        else:
                            target_msg["content"] = new_content
                            if "metadata" not in target_msg:
                                target_msg["metadata"] = {}
                            target_msg["metadata"]["is_trimmed"] = True

                            # 计算 Token 减少量
                            old_tokens = self._count_tokens(content)
                            new_tokens = self._count_tokens(target_msg["content"])
                            diff = old_tokens - new_tokens
                            total_tokens -= diff

                            if self.valves.show_debug_log and __event_call__:
                                await self._log(
                                    f"[Inlet] 📉 结构化裁剪助手消息。节省: {diff} tokens。",
                                    event_call=__event_call__,
                                )
                            continue

                    # 策略 2: 回退 - 完全丢弃最旧的消息 (FIFO)
                    dropped = tail_messages.pop(0)
                    dropped_tokens = self._count_tokens(str(dropped.get("content", "")))
                    total_tokens -= dropped_tokens

                    if self.valves.show_debug_log and __event_call__:
                        await self._log(
                            f"[Inlet] 🗑️ 从历史记录中丢弃消息以适应上下文。角色: {dropped.get('role')}, Tokens: {dropped_tokens}",
                            event_call=__event_call__,
                        )

                # 重新组装
                candidate_messages = head_messages + [summary_msg] + tail_messages

                await self._log(
                    f"[Inlet] ✂️ 历史记录已缩减。新总数: {total_tokens} Tokens (尾部大小: {len(tail_messages)})",
                    event_call=__event_call__,
                )

            final_messages = candidate_messages

            # 计算详细 Token 统计以用于日志
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
                f"[Inlet] 应用摘要: {system_info} + Head({len(head_messages)} 条, {head_tokens}t) + Summary({summary_tokens}t) + Tail({len(tail_messages)} 条, {tail_tokens}t) = Total({total_section_tokens}t)",
                log_type="success",
                event_call=__event_call__,
            )

            # 准备状态消息 (上下文使用量格式)
            if max_context_tokens > 0:
                usage_ratio = total_section_tokens / max_context_tokens
                # 仅在超过阈值时显示状态
                if self._should_show_status(usage_ratio):
                    status_msg = f"上下文使用量 (预估): {total_section_tokens} / {max_context_tokens} Tokens ({usage_ratio*100:.1f}%)"
                    if usage_ratio > 0.9:
                        status_msg += " | ⚠️ 高负载"
                    
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
                # 对于 max_context_tokens 为 0 的情况，显示摘要信息而不检查阈值
                if self.valves.show_token_usage_status and __event_emitter__:
                    status_msg = f"已加载历史摘要 (隐藏 {compressed_count} 条历史消息)"
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
            # 没有摘要，使用原始消息
            # 但仍然需要检查预算！
            final_messages = messages

            # 包含系统提示词进行计算
            calc_messages = final_messages
            if system_prompt_msg:
                is_in_messages = any(m.get("role") == "system" for m in final_messages)
                if not is_in_messages:
                    calc_messages = [system_prompt_msg] + final_messages

            # 获取最大上下文限制
            model = self._clean_model_id(body.get("model"))
            thresholds = self._get_model_thresholds(model) or {}
            max_context_tokens = thresholds.get(
                "max_context_tokens", self.valves.max_context_tokens
            )

            total_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, calc_messages
            )

            if total_tokens > max_context_tokens:
                await self._log(
                    f"[Inlet] ⚠️ 原始消息 ({total_tokens} Tokens) 超过上限 ({max_context_tokens})。正在缩减历史记录...",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # 动态从开头移除消息
                # 我们将遵守 effective_keep_first 以保护系统提示词

                start_trim_index = effective_keep_first

                while (
                    total_tokens > max_context_tokens
                    and len(final_messages)
                    > start_trim_index + 1  # 保留 keep_first 之后至少 1 条消息
                ):
                    dropped = final_messages.pop(start_trim_index)
                    dropped_tokens = self._count_tokens(str(dropped.get("content", "")))
                    total_tokens -= dropped_tokens

                await self._log(
                    f"[Inlet] ✂️ 消息已缩减。新总数: {total_tokens} Tokens",
                    event_call=__event_call__,
                )

            # 发送状态通知 (上下文使用量格式)
            # 发送状态通知 (上下文使用量格式)
            if max_context_tokens > 0:
                usage_ratio = total_tokens / max_context_tokens
                # 仅在超过阈值时显示状态
                if self._should_show_status(usage_ratio):
                    status_msg = f"上下文使用量 (预估): {total_tokens} / {max_context_tokens} Tokens ({usage_ratio*100:.1f}%)"
                    if usage_ratio > 0.9:
                        status_msg += " | ⚠️ 高负载"
                    
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
            f"[Inlet] 最终发送: {len(body['messages'])} 条消息\n{'='*60}\n",
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
        在 LLM 响应完成后执行
        在后台计算 Token 数并触发摘要生成（不阻塞当前响应，不影响内容输出）
        """
        # 检查是否应该跳过压缩（例如，copilot_sdk）
        if self._should_skip_compression(body, __model__):
            if self.valves.debug_mode:
                logger.info("[Outlet] 跳过压缩：检测到 copilot_sdk 基础模型")
            if self.valves.show_debug_log and __event_call__:
                await self._log(
                    "[Outlet] ⏭️ 跳过压缩：检测到 copilot_sdk",
                    event_call=__event_call__,
                )
            return body
        
        chat_ctx = self._get_chat_context(body, __metadata__)
        chat_id = chat_ctx["chat_id"]
        if not chat_id:
            await self._log(
                "[Outlet] ❌ metadata 中缺少 chat_id，跳过压缩",
                log_type="error",
                event_call=__event_call__,
            )
            return body
        model = body.get("model") or ""
        messages = body.get("messages", [])

        # 直接计算目标压缩进度
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        # 在后台异步处理 Token 计算和摘要生成（不等待完成，不影响输出）
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
        后台处理：计算 Token 数并生成摘要（不阻塞响应）
        """
        try:
            messages = body.get("messages", [])

            # 获取当前模型的阈值配置
            thresholds = self._get_model_thresholds(model) or {}
            compression_threshold_tokens = thresholds.get(
                "compression_threshold_tokens", self.valves.compression_threshold_tokens
            )

            await self._log(
                f"\n[🔍 后台计算] 开始 Token 计数...",
                event_call=__event_call__,
            )

            # 在后台线程中计算 Token 数
            current_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, messages
            )

            await self._log(
                f"[🔍 后台计算] Token 数: {current_tokens}",
                event_call=__event_call__,
            )

            # 发送状态通知 (上下文使用量格式)
            if __event_emitter__:
                max_context_tokens = thresholds.get(
                    "max_context_tokens", self.valves.max_context_tokens
                )
                if max_context_tokens > 0:
                    usage_ratio = current_tokens / max_context_tokens
                    # 仅在超过阈值时显示状态
                    if self._should_show_status(usage_ratio):
                        status_msg = f"上下文使用量 (预估): {current_tokens} / {max_context_tokens} Tokens ({usage_ratio*100:.1f}%)"
                        if usage_ratio > 0.9:
                            status_msg += " | ⚠️ 高负载"
                        
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": status_msg,
                                    "done": True,
                                },
                            }
                        )

            # 检查是否需要压缩
            if current_tokens >= compression_threshold_tokens:
                await self._log(
                    f"[🔍 后台计算] ⚡ 触发压缩阈值 (Token: {current_tokens} >= {compression_threshold_tokens})",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # 继续生成摘要
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
                    f"[🔍 后台计算] 未触发压缩阈值 (Token: {current_tokens} < {compression_threshold_tokens})",
                    event_call=__event_call__,
                )

        except Exception as e:
            await self._log(
                f"[🔍 后台计算] ❌ 错误: {str(e)}",
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
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        异步生成摘要（后台执行，不阻塞响应）
        逻辑：
        1. 提取中间消息（去除 keep_first 和 keep_last）。
        2. 检查 Token 上限，如果超过 max_context_tokens，从中间消息头部移除。
        3. 对剩余的中间消息生成摘要。
        """
        try:
            await self._log(f"\n[🤖 异步摘要任务] 开始...", event_call=__event_call__)

            # 1. 获取目标压缩进度
            # 如果未传递 target_compressed_count（新逻辑下不应发生），则进行估算
            if target_compressed_count is None:
                target_compressed_count = max(0, len(messages) - self.valves.keep_last)
                await self._log(
                    f"[🤖 异步摘要任务] ⚠️ target_compressed_count 为 None，进行估算: {target_compressed_count}",
                    log_type="warning",
                    event_call=__event_call__,
                )

            # 2. 确定待压缩的消息范围 (Middle)
            start_index = self.valves.keep_first
            end_index = len(messages) - self.valves.keep_last
            if self.valves.keep_last == 0:
                end_index = len(messages)

            # 确保索引有效
            if start_index >= end_index:
                await self._log(
                    f"[🤖 异步摘要任务] 中间消息为空 (Start: {start_index}, End: {end_index})，跳过",
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
                    f"[🤖 异步摘要任务] 📊 边界检查:\n"
                    f"  - 中间 (压缩): {len(middle_messages)} 条 (索引 {start_index}-{end_index-1}) -> 预览: {middle_preview}\n"
                    f"  - 尾部 (保留): {len(tail_preview_msgs)} 条 (索引 {end_index}-End) -> 预览: {tail_preview}",
                    event_call=__event_call__,
                )

            # 3. 检查 Token 上限并截断 (Max Context Truncation)
            # [优化] 使用摘要模型(如果有)的阈值来决定能处理多少中间消息
            # 这样可以用长窗口模型(如 gemini-flash)来压缩超过当前模型窗口的历史记录
            summary_model_id = self._clean_model_id(
                self.valves.summary_model
            ) or self._clean_model_id(body.get("model"))

            if not summary_model_id:
                await self._log(
                    "[🤖 异步摘要任务] ⚠️ 摘要模型不存在，跳过压缩",
                    log_type="warning",
                    event_call=__event_call__,
                )
                return

            thresholds = self._get_model_thresholds(summary_model_id) or {}
            # Priority: 1. summary_model_max_context (if > 0) -> 2. model_thresholds -> 3. global max_context_tokens
            if self.valves.summary_model_max_context > 0:
                max_context_tokens = self.valves.summary_model_max_context
            else:
                max_context_tokens = thresholds.get(
                    "max_context_tokens", self.valves.max_context_tokens
                )

            await self._log(
                f"[🤖 异步摘要任务] 使用模型 {summary_model_id} 的上限: {max_context_tokens} Tokens",
                event_call=__event_call__,
            )

            # 计算中间消息的 Token (加上提示词的缓冲)
            # 我们只把 middle_messages 发送给摘要模型，所以不应该把完整历史计入限制
            middle_tokens = await asyncio.to_thread(
                self._calculate_messages_tokens, middle_messages
            )
            # 增加提示词和输出的缓冲 (约 2000 Tokens)
            estimated_input_tokens = middle_tokens + 2000

            if estimated_input_tokens > max_context_tokens:
                excess_tokens = estimated_input_tokens - max_context_tokens
                await self._log(
                    f"[🤖 异步摘要任务] ⚠️ 中间消息 ({middle_tokens} Tokens) + 缓冲超过摘要模型上限 ({max_context_tokens})，需要移除约 {excess_tokens} Token",
                    log_type="warning",
                    event_call=__event_call__,
                )

                # 从 middle_messages 头部开始移除
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
                    f"[🤖 异步摘要任务] 已移除 {removed_count} 条消息，共 {removed_tokens} Token",
                    event_call=__event_call__,
                )

            if not middle_messages:
                await self._log(
                    f"[🤖 异步摘要任务] 截断后中间消息为空，跳过摘要生成",
                    event_call=__event_call__,
                )
                return

            # 4. 构建对话文本
            conversation_text = self._format_messages_for_summary(middle_messages)

            # 5. 调用 LLM 生成新摘要
            # 注意：这里不再传入 previous_summary，因为旧摘要（如果有）已经包含在 middle_messages 里了

            # 发送开始生成摘要的状态通知
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "正在后台生成上下文摘要...",
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
                    "[🤖 异步摘要任务] ⚠️ 摘要生成返回空结果，跳过保存",
                    log_type="warning",
                    event_call=__event_call__,
                )
                return

            # 6. 保存新摘要
            await self._log(
                "[优化] 在后台线程中保存摘要以避免阻塞事件循环。",
                event_call=__event_call__,
            )

            await asyncio.to_thread(
                self._save_summary, chat_id, new_summary, target_compressed_count
            )

            # 发送完成状态通知
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"上下文摘要已更新 (压缩了 {len(middle_messages)} 条消息)",
                            "done": True,
                        },
                    }
                )

            await self._log(
                f"[🤖 异步摘要任务] ✅ 完成！新摘要长度: {len(new_summary)} 字符",
                log_type="success",
                event_call=__event_call__,
            )
            await self._log(
                f"[🤖 异步摘要任务] 进度更新: 已压缩至原始消息 {target_compressed_count}",
                event_call=__event_call__,
            )

            # --- Token 使用情况状态通知 ---
            if self.valves.show_token_usage_status and __event_emitter__:
                try:
                    # 1. 获取系统提示词 (DB 回退)
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
                            pass  # 忽略 DB 错误，尽力而为

                    # 2. 计算 Effective Keep First
                    last_system_index = -1
                    for i, msg in enumerate(messages):
                        if msg.get("role") == "system":
                            last_system_index = i
                    effective_keep_first = max(
                        self.valves.keep_first, last_system_index + 1
                    )

                    # 3. 构建下一个上下文 (Next Context)
                    # Head
                    head_msgs = (
                        messages[:effective_keep_first]
                        if effective_keep_first > 0
                        else []
                    )

                    # Summary
                    summary_content = (
                        f"【系统提示：以下是历史对话的摘要，仅供参考上下文，请勿对摘要内容进行回复，直接回答后续的最新问题】\n\n"
                        f"{new_summary}\n\n"
                        f"---\n"
                        f"以下是最近的对话："
                    )
                    summary_msg = {"role": "assistant", "content": summary_content}

                    # Tail (使用 target_compressed_count，这是我们刚刚压缩到的位置)
                    # 注意：target_compressed_count 是要被摘要覆盖的消息数（不包括 keep_last）
                    # 所以 tail 从 max(target_compressed_count, effective_keep_first) 开始
                    start_index = max(target_compressed_count, effective_keep_first)
                    tail_msgs = messages[start_index:]

                    # 组装
                    next_context = head_msgs + [summary_msg] + tail_msgs

                    # 如果需要，注入系统提示词
                    if system_prompt_msg:
                        is_in_head = any(m.get("role") == "system" for m in head_msgs)
                        if not is_in_head:
                            next_context = [system_prompt_msg] + next_context

                    # 4. 计算 Token
                    token_count = self._calculate_messages_tokens(next_context)

                    # 5. 获取阈值并计算比例
                    model = self._clean_model_id(body.get("model"))
                    thresholds = self._get_model_thresholds(model) or {}
                    # Priority: 1. summary_model_max_context (if > 0) -> 2. model_thresholds -> 3. global max_context_tokens
                    if self.valves.summary_model_max_context > 0:
                        max_context_tokens = self.valves.summary_model_max_context
                    else:
                        max_context_tokens = thresholds.get(
                            "max_context_tokens", self.valves.max_context_tokens
                        )

                    # 6. 发送状态 (仅在超过阈值时)
                    if max_context_tokens > 0:
                        usage_ratio = token_count / max_context_tokens
                        # 仅在超过阈值时显示状态
                        if self._should_show_status(usage_ratio):
                            status_msg = f"上下文摘要已更新: {token_count} / {max_context_tokens} Tokens ({usage_ratio*100:.1f}%)"
                            if usage_ratio > 0.9:
                                status_msg += " | ⚠️ 高负载"
                            
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
                        f"[Status] 计算 Token 错误: {e}",
                        log_type="error",
                        event_call=__event_call__,
                    )

        except Exception as e:
            await self._log(
                f"[🤖 异步摘要任务] ❌ 错误: {str(e)}",
                log_type="error",
                event_call=__event_call__,
            )

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"摘要生成错误: {str(e)[:100]}...",
                            "done": True,
                        },
                    }
                )

            logger.exception("[🤖 异步摘要任务] ❌ 发生异常")

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

            # User requested to remove truncation to allow full context for summary
            # unless it exceeds model limits (which is handled by the LLM call itself or max_tokens)

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
        调用 LLM 生成摘要，使用 Open Web UI 的内置方法。
        """
        await self._log(
            f"[🤖 LLM 调用] 使用 Open Web UI 内置方法",
            event_call=__event_call__,
        )

        # 构建摘要提示词 (优化版)
        summary_prompt = f"""
你是一个专业的对话上下文压缩专家。你的任务是对以下对话内容进行高保真摘要。
这段对话可能包含之前的摘要（作为系统消息或文本）以及后续的对话内容。

### 核心目标
1.  **全面总结**：将对话中的关键信息、用户意图、助手回复进行精炼总结。
2.  **去噪提纯**：移除寒暄、重复、确认性回复等无用信息。
3.  **关键保留**：
    *   **代码片段、命令、技术参数必须逐字保留，严禁修改或概括。**
    *   用户意图、核心需求、决策结论、待办事项必须清晰保留。
4.  **连贯性**：生成的摘要应作为一个整体，能够替代原始对话作为上下文。
5.  **详尽记录**：由于允许的篇幅较长，请尽可能保留对话中的细节、论证过程和多轮交互的细微差别，而不仅仅是宏观概括。

### 输出要求
*   **格式**：结构化文本，逻辑清晰。
*   **语言**：与对话语言保持一致（通常为中文）。
*   **长度**：严格控制在 {self.valves.max_summary_tokens} Token 以内。
*   **严禁**：不要输出"根据对话..."、"摘要如下..."等废话。直接输出摘要内容。

### 摘要结构建议
*   **当前目标/主题**：一句话概括当前正在解决的问题。
*   **关键信息与上下文**：
    *   已确认的事实/参数。
    *   **代码/技术细节** (使用代码块包裹)。
*   **进展与结论**：已完成的步骤和达成的共识。
*   **待办/下一步**：明确的后续行动。

---
{new_conversation_text}
---

请根据上述内容，生成摘要：
"""
        # 确定使用的模型
        model = self._clean_model_id(self.valves.summary_model) or self._clean_model_id(
            body.get("model")
        )

        if not model:
            await self._log(
                "[🤖 LLM 调用] ⚠️ 摘要模型不存在，跳过摘要生成",
                log_type="warning",
                event_call=__event_call__,
            )
            return ""

        await self._log(f"[🤖 LLM 调用] 模型: {model}", event_call=__event_call__)

        # 构建 payload
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": summary_prompt}],
            "stream": False,
            "max_tokens": self.valves.max_summary_tokens,
            "temperature": self.valves.summary_temperature,
        }

        try:
            # 获取用户对象
            user_id = user_data.get("id") if user_data else None
            if not user_id:
                raise ValueError("无法获取用户 ID")

            # [优化] 在后台线程中获取用户对象以避免阻塞事件循环
            await self._log(
                "[优化] 在后台线程中获取用户对象以避免阻塞事件循环。",
                event_call=__event_call__,
            )
            user = await asyncio.to_thread(Users.get_user_by_id, user_id)

            if not user:
                raise ValueError(f"无法找到用户: {user_id}")

            await self._log(
                f"[🤖 LLM 调用] 用户: {user.email}\n[🤖 LLM 调用] 发送请求...",
                event_call=__event_call__,
            )

            # 创建 Request 对象
            request = Request(scope={"type": "http", "app": webui_app})

            # 调用 generate_chat_completion
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
                f"[🤖 LLM 调用] ✅ 成功接收摘要",
                log_type="success",
                event_call=__event_call__,
            )

            return summary

        except Exception as e:
            error_msg = str(e)
            # Handle specific error messages
            if "Model not found" in error_msg:
                error_message = f"摘要模型 '{model}' 不存在。"
            else:
                error_message = f"摘要 LLM 错误 ({model}): {error_msg}"
            if not self.valves.summary_model:
                error_message += (
                    "\n[提示] 您未指定 summary_model，因此过滤器尝试使用当前对话的模型。"
                    "如果这是流水线 (Pipe) 模型或不兼容的模型，请在配置中指定兼容的摘要模型 (例如 'gemini-2.5-flash')。"
                )

            await self._log(
                f"[🤖 LLM 调用] ❌ {error_message}",
                log_type="error",
                event_call=__event_call__,
            )

            raise Exception(error_message)
