"""
title: 异步上下文压缩
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
description: 通过智能摘要和消息压缩，降低长对话的 token 消耗，同时保持对话连贯性。
version: 1.1.1
openwebui_id: 5c0617cb-a9e4-4bd6-a440-d276534ebd18
license: MIT

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
import asyncio
import json
import hashlib
import time

# Open WebUI 内置导入
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from fastapi.requests import Request
from open_webui.main import app as webui_app

# Open WebUI 内部数据库 (复用共享连接)
from open_webui.internal.db import engine as owui_engine
from open_webui.internal.db import Session as owui_Session
from open_webui.internal.db import Base as owui_Base

# 尝试导入 tiktoken
try:
    import tiktoken
except ImportError:
    tiktoken = None

# 数据库导入
from sqlalchemy import Column, String, Text, DateTime, Integer, inspect
from datetime import datetime


class ChatSummary(owui_Base):
    """对话摘要存储表"""

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
        self.temp_state = {}  # 用于在 inlet 和 outlet 之间传递临时数据
        self._init_database()

    def _init_database(self):
        """使用 Open WebUI 的共享连接初始化数据库表"""
        try:
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
        model_thresholds: dict = Field(
            default={},
            description="针对特定模型的阈值覆盖配置。仅包含需要特殊配置的模型。",
        )

        keep_first: int = Field(
            default=1, ge=0, description="始终保留最初的 N 条消息。设置为 0 则不保留。"
        )
        keep_last: int = Field(
            default=6, ge=0, description="始终保留最近的 N 条完整消息。"
        )
        summary_model: str = Field(
            default=None,
            description="用于生成摘要的模型 ID。留空则使用当前对话的模型。用于匹配 model_thresholds 中的配置。",
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

    def _save_summary(self, chat_id: str, summary: str, compressed_count: int):
        """保存摘要到数据库"""
        try:
            with self._SessionLocal() as session:
                # 查找现有记录
                existing = session.query(ChatSummary).filter_by(chat_id=chat_id).first()

                if existing:
                    # [优化] 乐观锁检查：只有进度向前推进时才更新
                    if compressed_count <= existing.compressed_message_count:
                        if self.valves.debug_mode:
                            print(
                                f"[存储] 跳过更新：新进度 ({compressed_count}) 不大于现有进度 ({existing.compressed_message_count})"
                            )
                        return

                    # 更新现有记录
                    existing.summary = summary
                    existing.compressed_message_count = compressed_count
                    existing.updated_at = datetime.utcnow()
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
                    print(f"[存储] 摘要已{action}到数据库 (Chat ID: {chat_id})")

        except Exception as e:
            print(f"[存储] ❌ 数据库保存失败: {str(e)}")

    def _load_summary_record(self, chat_id: str) -> Optional[ChatSummary]:
        """从数据库加载摘要记录对象"""
        try:
            with self._SessionLocal() as session:
                record = session.query(ChatSummary).filter_by(chat_id=chat_id).first()
                if record:
                    # Detach the object from the session so it can be used after session close
                    session.expunge(record)
                    return record
        except Exception as e:
            print(f"[加载] ❌ 数据库读取失败: {str(e)}")
        return None

    def _load_summary(self, chat_id: str, body: dict) -> Optional[str]:
        """从数据库加载摘要文本 (兼容旧接口)"""
        record = self._load_summary_record(chat_id)
        if record:
            if self.valves.debug_mode:
                print(f"[加载] 从数据库加载摘要 (Chat ID: {chat_id})")
                print(
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
        1. 如果 model_thresholds 中存在该模型ID的配置，使用该配置
        2. 否则使用全局参数 compression_threshold_tokens 和 max_context_tokens
        """
        # 尝试从模型特定配置中匹配
        if model_id in self.valves.model_thresholds:
            if self.valves.debug_mode:
                print(f"[配置] 使用模型特定配置: {model_id}")
            return self.valves.model_thresholds[model_id]

        # 使用全局默认配置
        if self.valves.debug_mode:
            print(f"[配置] 模型 {model_id} 未在 model_thresholds 中，使用全局参数")

        return {
            "compression_threshold_tokens": self.valves.compression_threshold_tokens,
            "max_context_tokens": self.valves.max_context_tokens,
        }

    def _inject_summary_to_first_message(self, message: dict, summary: str) -> dict:
        """将摘要注入到第一条消息中（追加到内容前面）"""
        content = message.get("content", "")
        summary_block = f"【历史对话摘要】\n{summary}\n\n---\n以下是最近的对话：\n\n"

        # 处理不同内容类型
        if isinstance(content, list):  # 多模态内容
            # 查找第一个文本部分并在其前面插入摘要
            new_content = []
            summary_inserted = False

            for part in content:
                if (
                    isinstance(part, dict)
                    and part.get("type") == "text"
                    and not summary_inserted
                ):
                    # 在第一个文本部分前插入摘要
                    new_content.append(
                        {"type": "text", "text": summary_block + part.get("text", "")}
                    )
                    summary_inserted = True
                else:
                    new_content.append(part)

            # 如果没有文本部分，在开头插入
            if not summary_inserted:
                new_content.insert(0, {"type": "text", "text": summary_block})

            message["content"] = new_content

        elif isinstance(content, str):  # 纯文本
            message["content"] = summary_block + content

        return message

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
        """统一日志输出到后端 (print) 和前端 (console.log)"""
        # 后端日志
        if self.valves.debug_mode:
            print(message)

        # 前端日志
        if self.valves.show_debug_log and event_call:
            try:
                css = "color: #3b82f6;"  # 默认蓝色
                if type == "error":
                    css = "color: #ef4444; font-weight: bold;"  # 红色
                elif type == "warning":
                    css = "color: #f59e0b;"  # 橙色
                elif type == "success":
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
                print(f"发送前端日志失败: {e}")

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: dict = None,
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        在发送到 LLM 之前执行
        压缩策略：只负责注入已有的摘要，不进行 Token 计算
        """
        messages = body.get("messages", [])
        chat_id = __metadata__["chat_id"]

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Inlet] Chat ID: {chat_id}\n[Inlet] 收到 {len(messages)} 条消息",
                event_call=__event_call__,
            )

        # 记录原始消息的目标压缩进度，供 outlet 使用
        # 目标是压缩到倒数第 keep_last 条之前
        target_compressed_count = max(0, len(messages) - self.valves.keep_last)

        # [优化] 简单的状态清理检查
        if chat_id in self.temp_state:
            await self._log(
                f"[Inlet] ⚠️ 覆盖未消费的旧状态 (Chat ID: {chat_id})",
                type="warning",
                event_call=__event_call__,
            )

        self.temp_state[chat_id] = target_compressed_count

        await self._log(
            f"[Inlet] 记录目标压缩进度: {target_compressed_count}",
            event_call=__event_call__,
        )

        # 加载摘要记录
        summary_record = await asyncio.to_thread(self._load_summary_record, chat_id)

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
            if self.valves.keep_first > 0:
                head_messages = messages[: self.valves.keep_first]

            # 2. 摘要消息 (作为 User 消息插入)
            summary_content = (
                f"【系统提示：以下是历史对话的摘要，仅供参考上下文，请勿对摘要内容进行回复，直接回答后续的最新问题】\n\n"
                f"{summary_record.summary}\n\n"
                f"---\n"
                f"以下是最近的对话："
            )
            summary_msg = {"role": "user", "content": summary_content}

            # 3. 尾部消息 (Tail) - 从上次压缩点开始的所有消息
            # 注意：这里必须确保不重复包含头部消息
            start_index = max(compressed_count, self.valves.keep_first)
            tail_messages = messages[start_index:]

            final_messages = head_messages + [summary_msg] + tail_messages

            # 发送状态通知
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"已加载历史摘要 (隐藏 {compressed_count} 条历史消息)",
                            "done": True,
                        },
                    }
                )

            await self._log(
                f"[Inlet] 应用摘要: Head({len(head_messages)}) + Summary + Tail({len(tail_messages)})",
                type="success",
                event_call=__event_call__,
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
            final_messages = messages

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
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ) -> dict:
        """
        在 LLM 响应完成后执行
        在后台计算 Token 数并触发摘要生成（不阻塞当前响应，不影响内容输出）
        """
        chat_id = __metadata__["chat_id"]
        model = body.get("model", "gpt-3.5-turbo")

        if self.valves.debug_mode or self.valves.show_debug_log:
            await self._log(
                f"\n{'='*60}\n[Outlet] Chat ID: {chat_id}\n[Outlet] 响应完成",
                event_call=__event_call__,
            )

        # 在后台异步处理 Token 计算和摘要生成（不等待完成，不影响输出）
        asyncio.create_task(
            self._check_and_generate_summary_async(
                chat_id, model, body, __user__, __event_emitter__, __event_call__
            )
        )

        await self._log(
            f"[Outlet] 后台处理已启动\n{'='*60}\n",
            event_call=__event_call__,
        )

        return body

    async def _check_and_generate_summary_async(
        self,
        chat_id: str,
        model: str,
        body: dict,
        user_data: Optional[dict],
        __event_emitter__: Callable[[Any], Awaitable[None]] = None,
        __event_call__: Callable[[Any], Awaitable[None]] = None,
    ):
        """
        后台处理：计算 Token 数并生成摘要（不阻塞响应）
        """
        try:
            messages = body.get("messages", [])

            # 获取当前模型的阈值配置
            thresholds = self._get_model_thresholds(model)
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

            # 检查是否需要压缩
            if current_tokens >= compression_threshold_tokens:
                await self._log(
                    f"[🔍 后台计算] ⚡ 触发压缩阈值 (Token: {current_tokens} >= {compression_threshold_tokens})",
                    type="warning",
                    event_call=__event_call__,
                )

                # 继续生成摘要
                await self._generate_summary_async(
                    messages,
                    chat_id,
                    body,
                    user_data,
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
                type="error",
                event_call=__event_call__,
            )

    async def _generate_summary_async(
        self,
        messages: list,
        chat_id: str,
        body: dict,
        user_data: Optional[dict],
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
            # 优先从 temp_state 获取（由 inlet 计算），如果获取不到（例如重启后），则假设当前是完整历史
            target_compressed_count = self.temp_state.pop(chat_id, None)
            if target_compressed_count is None:
                target_compressed_count = max(0, len(messages) - self.valves.keep_last)
                await self._log(
                    f"[🤖 异步摘要任务] ⚠️ 无法获取 inlet 状态，使用当前消息数估算进度: {target_compressed_count}",
                    type="warning",
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

            await self._log(
                f"[🤖 异步摘要任务] 待处理中间消息: {len(middle_messages)} 条",
                event_call=__event_call__,
            )

            # 3. 检查 Token 上限并截断 (Max Context Truncation)
            # [优化] 使用摘要模型(如果有)的阈值来决定能处理多少中间消息
            # 这样可以用长窗口模型(如 gemini-flash)来压缩超过当前模型窗口的历史记录
            summary_model_id = self.valves.summary_model or body.get("model")

            thresholds = self._get_model_thresholds(summary_model_id)
            # 注意：这里使用的是摘要模型的最大上下文限制
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
                    type="warning",
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
                None, conversation_text, body, user_data, __event_call__
            )

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
                type="success",
                event_call=__event_call__,
            )
            await self._log(
                f"[🤖 异步摘要任务] 进度更新: 已压缩至原始消息 {target_compressed_count}",
                event_call=__event_call__,
            )

        except Exception as e:
            await self._log(
                f"[🤖 异步摘要任务] ❌ 错误: {str(e)}",
                type="error",
                event_call=__event_call__,
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
        model = self.valves.summary_model or body.get("model", "")

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

            if not response or "choices" not in response or not response["choices"]:
                raise ValueError("LLM 响应格式不正确或为空")

            summary = response["choices"][0]["message"]["content"].strip()

            await self._log(
                f"[🤖 LLM 调用] ✅ 成功接收摘要",
                type="success",
                event_call=__event_call__,
            )

            return summary

        except Exception as e:
            error_message = f"调用 LLM ({model}) 生成摘要时发生错误: {str(e)}"
            if not self.valves.summary_model:
                error_message += (
                    "\n[提示] 您未指定 summary_model，因此过滤器尝试使用当前对话的模型。"
                    "如果这是流水线 (Pipe) 模型或不兼容的模型，请在配置中指定兼容的摘要模型 (例如 'gemini-2.5-flash')。"
                )

            await self._log(
                f"[🤖 LLM 调用] ❌ {error_message}",
                type="error",
                event_call=__event_call__,
            )

            raise Exception(error_message)
