"""
title: Gemini 多模态过滤器（含字幕增强）
author: Gemini Adapter
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/openwebui-extensions

version: 0.3.2
description: >
    一个强大的过滤器，为 OpenWebUI 中的任何模型提供多模态能力：PDF、Office、图片、音频、视频等。
    默认智能路由至 Gemini 进行分析/直连；当检测到“视频+字幕”需求时，会自动启用字幕精修专家生成高质量 SRT 作为上下文。

功能特性:
- **多模态支持**: 处理 PDF, Word, Excel, PowerPoint, EPUB, MP3, MP4 和图片。
- **智能路由**:
    - **直连模式 (Direct Mode)**: 对于 Gemini 模型，文件直接传递（原生多模态）。
    - **分析器模式 (Analyzer Mode)**: 对于非 Gemini 模型（如 DeepSeek, Llama），文件由 Gemini 分析，结果注入为上下文。
- **持久上下文**: 利用 OpenWebUI 的 Chat ID 跨多轮对话维护会话历史。
- **数据库去重**: 自动记录已分析文件的哈希值，防止重复上传和分析，节省资源。
- **智能追问**: 支持针对已上传文档的纯文本追问，自动调用 Gemini 进行上下文分析。

配置项 (Valves):
- `gemini_adapter_url`: Gemini Adapter 服务的 URL。
- `target_model_keyword`: 用于识别 Gemini 模型的关键字（默认: "webgemini"）。
- `mode`: "auto" (推荐), "direct" (直连), 或 "analyzer" (分析器)。
- `analyzer_base_model_id`: 用于文档分析的基础 Gemini 模型（默认: "gemini-3.0-pro"）。
"""

import os
import asyncio
import requests
import base64
import mimetypes
import time
from typing import List, Union, Generator, Iterator, Optional
from pydantic import BaseModel, Field
import sqlalchemy
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

Base = declarative_base()


class GeminiAnalysisHistory(Base):
    """记录已分析文件的历史，用于去重"""

    __tablename__ = "gemini_analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(255), nullable=False, index=True)
    file_hash = Column(String(255), nullable=False, index=True)
    file_id = Column(String(255), nullable=True)  # 记录当时的 file_id 仅供参考
    filename = Column(String(255), nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class File(Base):
    """OpenWebUI 现有的 file 表映射 (只读)"""

    __tablename__ = "file"
    id = Column(String, primary_key=True)
    hash = Column(String)
    filename = Column(String)

    # 其他字段我们暂时不需要


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=8, description="Priority level for the filter operations."
        )
        gemini_adapter_url: str = Field(
            default="http://192.168.31.19:8197",
            description="URL of the Gemini Adapter",
        )
        openwebui_upload_path: str = Field(
            default="/app/backend/data/uploads",
            description="Path to OpenWebUI uploads directory (mapped in Docker)",
        )
        supported_extensions: str = Field(
            default=".pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .epub, .mp3, .wav, .mp4, .mov, .avi, .mkv, .webm",
            description="Comma-separated list of supported file extensions",
        )
        target_model_keyword: str = Field(
            default="webgemini",
            description="Keyword to identify Gemini models (e.g., 'webgemini')",
        )
        mode: str = Field(
            default="auto",
            description="Operation mode: 'auto' (decide based on model), 'direct' (pass file URL), or 'analyzer' (analyze first)",
        )
        analyzer_base_model_id: str = Field(
            default="gemini-3.0-pro",
            description="Base Model ID to use for document analysis (Brain)",
        )
        analyzer_custom_model_id: str = Field(
            default="gemini-analyzer",
            description="Custom model ID for general document analysis (Gem)",
        )
        subtitle_custom_model_id: str = Field(
            default="subtitle-master",
            description="Custom model ID for subtitle extraction / SRT polishing",
        )
        subtitle_keywords: str = Field(
            default="字幕,字幕精修,字幕提取,srt",
            description="Comma-separated keywords to trigger subtitle flow when paired with video uploads",
        )
        subtitle_video_extensions: str = Field(
            default=".mp4, .mov, .avi, .mkv, .webm",
            description="Video extensions that will trigger subtitle flow when keywords are present",
        )
        upload_timeout_seconds: int = Field(
            default=600, description="Timeout for adapter upload requests (seconds)"
        )
        analyze_timeout_seconds: int = Field(
            default=600, description="Timeout for adapter analysis requests (seconds)"
        )
        max_retries: int = Field(
            default=2, description="Max retry attempts for adapter calls"
        )
        retry_backoff_seconds: float = Field(
            default=60.0, description="Backoff seconds between retries"
        )
        circuit_failure_threshold: int = Field(
            default=3,
            description="Number of consecutive failures before opening circuit",
        )
        circuit_reset_seconds: int = Field(
            default=60, description="Cooldown seconds before closing circuit after trip"
        )

    def __init__(self):
        self.valves = self.Valves()
        self._db_engine = None
        self._SessionLocal = None
        self._init_database()
        self._failure_count = 0
        self._circuit_open_until = 0

    def _circuit_open(self) -> bool:
        now = time.time()
        if now < self._circuit_open_until:
            return True
        return False

    def _record_success(self):
        self._failure_count = 0
        self._circuit_open_until = 0

    def _record_failure(self):
        self._failure_count += 1
        if self._failure_count >= self.valves.circuit_failure_threshold:
            self._circuit_open_until = time.time() + self.valves.circuit_reset_seconds
            print(
                f"🚧 Circuit open for adapter calls ({self.valves.circuit_reset_seconds}s) after {self._failure_count} failures"
            )

    def _init_database(self):
        """初始化数据库连接和表"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                print(
                    "⚠️ DATABASE_URL not set. Deduplication will fall back to memory (unreliable)."
                )
                return

            # Handle postgres protocol
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)

            self._db_engine = create_engine(database_url, pool_pre_ping=True)
            self._SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self._db_engine
            )

            # Create our history table if it doesn't exist
            Base.metadata.create_all(bind=self._db_engine)
            print("✅ Gemini Filter: Database initialized and tables checked.")
        except Exception as e:
            print(f"❌ Gemini Filter: Database initialization failed: {e}")
            self._db_engine = None

    def get_db(self):
        if not self._SessionLocal:
            return None
        return self._SessionLocal()

    def get_file_hash(self, file_id: str) -> Optional[str]:
        """从 OpenWebUI 的 file 表获取文件哈希"""
        db = self.get_db()
        if not db:
            return None
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            return file_record.hash if file_record else None
        except Exception as e:
            print(f"⚠️ Failed to query file hash: {e}")
            return None
        finally:
            db.close()

    def is_file_analyzed(self, chat_id: str, file_hash: str) -> bool:
        """检查文件是否已在当前会话中分析过"""
        db = self.get_db()
        if not db:
            return False
        try:
            record = (
                db.query(GeminiAnalysisHistory)
                .filter(
                    GeminiAnalysisHistory.chat_id == chat_id,
                    GeminiAnalysisHistory.file_hash == file_hash,
                )
                .first()
            )
            return record is not None
        except Exception as e:
            print(f"⚠️ Failed to check analysis history: {e}")
            return False
        finally:
            db.close()

    def mark_file_analyzed(
        self, chat_id: str, file_hash: str, file_id: str, filename: str
    ):
        """标记文件为已分析"""
        db = self.get_db()
        if not db:
            return
        try:
            new_record = GeminiAnalysisHistory(
                chat_id=chat_id, file_hash=file_hash, file_id=file_id, filename=filename
            )
            db.add(new_record)
            db.commit()
            print(
                f"💾 Marked file {filename} (hash: {file_hash[:8]}...) as analyzed in chat {chat_id}"
            )
        except Exception as e:
            print(f"⚠️ Failed to mark file as analyzed: {e}")
            db.rollback()
        finally:
            db.close()

    def has_analyzed_files_in_chat(self, chat_id: str) -> bool:
        """检查当前会话是否有任何已分析的文件（用于追问判断）"""
        db = self.get_db()
        if not db:
            return False
        try:
            record = (
                db.query(GeminiAnalysisHistory)
                .filter(GeminiAnalysisHistory.chat_id == chat_id)
                .first()
            )
            return record is not None
        except Exception as e:
            return False
        finally:
            db.close()

    def upload_to_adapter(
        self, file_content: bytes, filename: str, content_type: str
    ) -> str:
        """
        Uploads file content to Gemini Adapter and returns the accessible URL.
        """
        if self._circuit_open():
            print("🚫 Upload circuit open, skipping upload")
            return None

        upload_url = f"{self.valves.gemini_adapter_url}/v1/files/upload"
        timeout = self.valves.upload_timeout_seconds
        retries = self.valves.max_retries
        backoff = self.valves.retry_backoff_seconds

        print(
            f"📤 Uploading {filename} to {upload_url} (timeout={timeout}s, retries={retries})..."
        )

        for attempt in range(retries + 1):
            try:
                files = {"file": (filename, file_content, content_type)}
                response = requests.post(upload_url, files=files, timeout=timeout)
                response.raise_for_status()

                result = response.json()
                file_url = result.get("url")
                print(f"✅ Upload success: {file_url}")
                self._record_success()
                return file_url
            except Exception as e:
                print(f"❌ Upload attempt {attempt+1} failed: {e}")
                self._record_failure()
                if attempt < retries:
                    time.sleep(backoff)
                else:
                    print("🚫 Upload exhausted retries")
        return None

    def analyze_document(
        self,
        file_url: Optional[str],
        user_message: str,
        openwebui_chat_id: Optional[str] = None,
        custom_model_id: Optional[str] = None,
        subtitle_mode: bool = False,
    ) -> Optional[str]:
        """
        Send file URL and user message to Gemini Adapter for analysis or subtitle extraction.
        Uses OpenWebUI's chat_id directly, relying on Adapter's database for context persistence.
        """
        print(
            f"🧠 Analyzing/Chatting with Gemini. File: {file_url}, ChatID: {openwebui_chat_id}, SubtitleMode: {subtitle_mode}"
        )

        headers = {
            "Content-Type": "application/json",
        }

        chat_url = f"{self.valves.gemini_adapter_url}/v1/chat/completions"
        timeout = self.valves.analyze_timeout_seconds
        retries = self.valves.max_retries
        backoff = self.valves.retry_backoff_seconds

        if self._circuit_open():
            print("🚫 Analyze circuit open, skipping analysis")
            return None

        # Construct Prompt
        # If file_url is present, it's likely the first turn or a new file.
        # If file_url is None, it's a follow-up question.
        if subtitle_mode:
            base_prompt = (
                "你是资深的字幕精修专家，负责将上传的音视频内容转写并打磨为高质量的 SRT 字幕。"
                "务必保留技术名词，删除口癖，保证双语混排空格规范。"
                "时间轴需要连续、准确，文本建议单行不超过 20 个中文字符。"
            )
            if file_url:
                prompt = (
                    f"{base_prompt}\n\n请聆听/阅读附件内容，并依据用户需求生成标准 SRT：\n"
                    f"用户问题：{user_message}"
                )
                content_list = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": file_url}},
                ]
            else:
                prompt = (
                    f"{base_prompt}\n\n基于前文上下文，继续回答用户的新需求：{user_message}\n"
                    "若需要补全或修订已有字幕，请保持时间轴连续。"
                )
                content_list = [{"type": "text", "text": prompt}]
        else:
            if file_url:
                prompt = f"请阅读附件文档，并针对以下问题进行详细分析和回答：\n\n用户问题：{user_message}\n\n请提供详尽的分析结果，这将作为上下文提供给另一个 AI 模型。"
                content_list = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": file_url}},
                ]
            else:
                # Follow-up question (no file needed, context is in session)
                prompt = f"基于之前的文档内容，回答用户的新问题：{user_message}\n\n请提供详尽的回答，这将作为上下文提供给另一个 AI 模型。"
                content_list = [{"type": "text", "text": prompt}]

        # Construct request payload
        payload = {
            "model": self.valves.analyzer_base_model_id,
            "custom_model_id": custom_model_id or self.valves.analyzer_custom_model_id,
            "chat_id": openwebui_chat_id,  # Pass OpenWebUI chat_id directly
            "messages": [
                {
                    "role": "user",
                    "content": content_list,
                }
            ],
            "stream": False,
        }

        persona = custom_model_id or self.valves.analyzer_custom_model_id
        print(
            f"🧠 Analyzing document with {self.valves.analyzer_base_model_id} (Persona: {persona})..."
        )
        for attempt in range(retries + 1):
            try:
                response = requests.post(chat_url, json=payload, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                print(f"✅ Analysis complete ({len(analysis)} chars)")
                self._record_success()
                return analysis
            except Exception as e:
                print(f"❌ Analysis attempt {attempt+1} failed: {e}")
                self._record_failure()
                if attempt < retries:
                    time.sleep(backoff)
                else:
                    print("🚫 Analysis exhausted retries")
        return None

    def process_url(self, url: str, should_process_images: bool = True) -> str:
        """
        Process a URL (Base64 or HTTP), upload to adapter if needed, and return new URL.
        """
        # 1. Handle Base64
        if url.startswith("data:"):
            try:
                header, encoded = url.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]

                # Check if it's an image and if we should process it
                is_image = "image" in mime_type
                if is_image and not should_process_images:
                    return url

                # Only process PDF, images, audio, or video (if allowed)
                if (
                    "pdf" not in mime_type
                    and not is_image
                    and "audio" not in mime_type
                    and "video" not in mime_type
                ):
                    return url

                # Decode
                file_content = base64.b64decode(encoded)
                extension = mimetypes.guess_extension(mime_type) or ".bin"
                filename = f"upload{extension}"

                # Upload
                new_url = self.upload_to_adapter(file_content, filename, mime_type)
                return new_url if new_url else url

            except Exception as e:
                print(f"❌ Error processing Base64: {e}")
                return url
        return url

    async def emit_status(
        self, __event_emitter__, description: str, done: bool = False
    ):
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

    async def inlet(
        self,
        body: dict,
        __event_emitter__=None,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        print(f"🔍 Gemini PDF Filter: Inlet triggered")

        # Extract Chat ID from metadata
        openwebui_chat_id = None
        if __metadata__:
            openwebui_chat_id = __metadata__.get("chat_id")
            print(f"🆔 OpenWebUI Chat ID: {openwebui_chat_id}")

        # 1. Determine the actual model ID (handling custom models)
        base_model_id = None
        if __model__:
            if "openai" in __model__:
                base_model_id = __model__["openai"].get("id")
            else:
                base_model_id = __model__.get("info", {}).get("base_model_id")

        # Fallback to body['model'] if base_model_id not found or __model__ is missing
        current_model = base_model_id if base_model_id else body.get("model", "")

        print(
            f"🤖 Checking model: {current_model} (Target: {self.valves.target_model_keyword})"
        )
        # 0. SKIP COPILOT MODELS
        # If the model is a Copilot Pipe model, we must NOT process files here.
        # Copilot Pipe has its own file handling logic (copy to workspace).
        if "copilot_sdk" in current_model.lower():
            print(f"⏩ Skipping Gemini Filter for Copilot model: {current_model}")
            return body


        # Check if model matches target keyword
        is_target_model = (
            self.valves.target_model_keyword.lower() in current_model.lower()
        )

        # Determine effective mode
        effective_mode = self.valves.mode
        if effective_mode == "auto":
            if is_target_model:
                effective_mode = "direct"
            else:
                effective_mode = "analyzer"

        print(f"⚙️ Effective Mode: {effective_mode}")

        # If not target model AND effective mode is NOT analyzer, skip.
        # This means if we are in 'direct' mode (forced or auto), we only run for target models.
        if not is_target_model and effective_mode != "analyzer":
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body

        # Extract plain text from the last user message for intent detection
        user_text_plain = last_message.get("content", "")
        if isinstance(user_text_plain, list):
            user_text_plain = " ".join(
                [
                    item.get("text", "")
                    for item in user_text_plain
                    if item.get("type") == "text"
                ]
            )

        subtitle_keywords = [
            kw.strip() for kw in self.valves.subtitle_keywords.split(",") if kw.strip()
        ]
        is_subtitle_query = any(kw in user_text_plain for kw in subtitle_keywords)
        video_exts = tuple(
            ext.strip().lower()
            for ext in self.valves.subtitle_video_extensions.split(",")
        )

        # 1. Process files list to bypass RAG
        processed_any = False
        if files := body.get("files"):
            files_to_keep = []

            # Parse supported extensions
            supported_exts = tuple(
                ext.strip().lower()
                for ext in self.valves.supported_extensions.split(",")
            )

            for file_item in files:
                # 尝试适配不同的 files 结构
                file_obj = file_item.get("file", file_item)

                # 获取文件名和 ID
                filename = file_obj.get("filename") or file_obj.get("name") or ""
                file_id = file_obj.get("id", "")

                print(f"📄 Checking file: {filename} (ID: {file_id})")

                # Database-backed deduplication
                file_hash = None
                if openwebui_chat_id and file_id:
                    file_hash = self.get_file_hash(file_id)
                    if file_hash:
                        if self.is_file_analyzed(openwebui_chat_id, file_hash):
                            print(
                                f"♻️ File {filename} (hash: {file_hash[:8]}...) already analyzed in chat {openwebui_chat_id}, skipping."
                            )
                            continue
                    else:
                        print(
                            f"⚠️ Could not find hash for file {file_id}, skipping deduplication check."
                        )

                # Check if extension is supported
                # IMPORTANT: If it's an image, only process if is_target_model is True
                is_image = any(
                    filename.lower().endswith(ext)
                    for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]
                )
                is_video = filename.lower().endswith(video_exts)
                should_process = False

                if filename.lower().endswith(supported_exts):
                    if is_image and not is_target_model:
                        print(f"⚠️ Skipping image for non-Gemini model: {filename}")
                        should_process = False
                    else:
                        should_process = True

                # Subtitle flow: only if video + subtitle intent
                use_subtitle_flow = should_process and is_video and is_subtitle_query

                if should_process:
                    print(f"📄 Detected supported file: {filename}")
                    await self.emit_status(
                        __event_emitter__,
                        f"🚀 发现新文件: {filename}，准备处理...",
                        done=False,
                    )

                    # Construct local path in OpenWebUI container
                    file_path = os.path.join(
                        self.valves.openwebui_upload_path, f"{file_id}_{filename}"
                    )

                    upload_success = False
                    try:
                        if os.path.exists(file_path):
                            print(f"📖 Reading local file: {file_path}")
                            with open(file_path, "rb") as f:
                                file_content = f.read()

                            # Determine mime type
                            mime_type, _ = mimetypes.guess_type(filename)
                            if not mime_type:
                                mime_type = "application/octet-stream"
                                if filename.lower().endswith(".pdf"):
                                    mime_type = "application/pdf"

                            # Upload to Adapter
                            # Upload is fast (local network), so we skip the status update for it to avoid flickering.

                            # Use run_in_executor to avoid blocking the event loop with synchronous requests
                            loop = asyncio.get_running_loop()
                            adapter_url = await loop.run_in_executor(
                                None,
                                self.upload_to_adapter,
                                file_content,
                                filename,
                                mime_type,
                            )

                            if adapter_url:
                                # Mark file as processed in DB
                                if openwebui_chat_id and file_hash:
                                    self.mark_file_analyzed(
                                        openwebui_chat_id, file_hash, file_id, filename
                                    )

                                # MODE SWITCH
                                if effective_mode == "analyzer":
                                    # Analyzer Mode: Analyze first, then inject context
                                    user_text = last_message.get("content", "")
                                    if isinstance(user_text, list):
                                        # Extract text from list content
                                        user_text = " ".join(
                                            [
                                                item["text"]
                                                for item in user_text
                                                if item["type"] == "text"
                                            ]
                                        )

                                    await self.emit_status(
                                        __event_emitter__,
                                        (
                                            "🧠 正在使用字幕精修专家生成高质量字幕..."
                                            if use_subtitle_flow
                                            else "🧠 正在使用 Gemini 深度分析文档内容 (这可能需要几十秒)..."
                                        ),
                                        done=False,
                                    )
                                    # Give a small yield to ensure status is sent
                                    await asyncio.sleep(0.1)

                                    # Pass openwebui_chat_id to analyze_document
                                    # Also run in executor to avoid blocking
                                    custom_model = (
                                        self.valves.subtitle_custom_model_id
                                        if use_subtitle_flow
                                        else self.valves.analyzer_custom_model_id
                                    )
                                    analysis_result = await loop.run_in_executor(
                                        None,
                                        self.analyze_document,
                                        adapter_url,
                                        user_text,
                                        openwebui_chat_id,
                                        custom_model,
                                        use_subtitle_flow,
                                    )

                                    if analysis_result:
                                        print(
                                            f"✅ Injecting analysis result into context"
                                        )
                                        # Inject as a system message or prepend to user message
                                        # Prepending to user message is usually safer for context retention
                                        context_title = (
                                            "【字幕精修结果（SRT 建议）】"
                                            if use_subtitle_flow
                                            else "【文档分析结果】"
                                        )
                                        context_message = f"{context_title}\n{analysis_result}\n\n【用户问题】\n"

                                        content = last_message.get("content", "")
                                        if isinstance(content, str):
                                            last_message["content"] = (
                                                context_message + content
                                            )
                                        elif isinstance(content, list):
                                            # Insert at the beginning of the list
                                            content.insert(
                                                0,
                                                {
                                                    "type": "text",
                                                    "text": context_message,
                                                },
                                            )
                                            last_message["content"] = content

                                        upload_success = True
                                        processed_any = True
                                        await self.emit_status(
                                            __event_emitter__,
                                            (
                                                "✅ 字幕生成完成，已注入上下文"
                                                if use_subtitle_flow
                                                else "✅ 文档分析完成，已注入上下文"
                                            ),
                                            done=True,
                                        )
                                    else:
                                        print("❌ Analysis failed, falling back to RAG")
                                        await self.emit_status(
                                            __event_emitter__,
                                            f"❌ 分析失败，回退到 RAG 模式",
                                            done=True,
                                        )
                                        # upload_success remains False, so it falls back to RAG
                                else:
                                    # Direct Mode: Pass URL to model
                                    print(f"✅ Adding file to messages: {adapter_url}")
                                    content = last_message.get("content", "")

                                    # Force Subtitle Gem if needed
                                    if use_subtitle_flow:
                                        if not body.get("custom_model_id"):
                                            body["custom_model_id"] = (
                                                self.valves.subtitle_custom_model_id
                                            )
                                        print(
                                            f"🎬 Subtitle flow detected. Binding custom_model_id -> {body['custom_model_id']}"
                                        )

                                    # Ensure content is a list
                                    if isinstance(content, str):
                                        content = [{"type": "text", "text": content}]

                                    content.append(
                                        {
                                            "type": "image_url",
                                            "image_url": {"url": adapter_url},
                                        }
                                    )
                                    last_message["content"] = content

                                    upload_success = True
                                    processed_any = True
                                    await self.emit_status(
                                        __event_emitter__,
                                        f"🔗 文件已连接到 Gemini 模型 (Direct Mode)",
                                        done=True,
                                    )
                            else:
                                print(f"❌ Failed to upload file to adapter")
                        else:
                            print(f"❌ Local file not found: {file_path}")

                    except Exception as e:
                        print(f"❌ Error processing file {filename}: {e}")
                        await self.emit_status(
                            __event_emitter__, f"❌ 处理文件失败: {e}", done=True
                        )

                    # RAG Fallback: If upload failed, keep the file in the list so OpenWebUI handles it
                    # If uploaded successfully, add to keep list (bypass RAG)
                    # OR if we skipped it because it was already processed (in Analyzer mode), we also bypass RAG?
                    # Actually, if we skip analysis, we usually want to bypass RAG too if we rely on Gemini context.
                    # But if we skip, we 'continue'd loop, so we didn't reach here.
                    # Wait, if we continue'd, we didn't add to files_to_keep.
                    # So it will be removed from files list?
                    # Let's check logic:
                    # files_to_keep = []
                    # for file in files:
                    #    if processed: continue
                    #    if success: files_to_keep.append(file)
                    # body['files'] = files_to_keep

                    # If we skip, it's NOT added to files_to_keep. So it's removed from body['files'].
                    # This is CORRECT for Analyzer mode (we don't want RAG).
                    # This is ALSO correct for Direct mode (we don't want RAG).

                    if upload_success:
                        # We processed it, so we remove it from RAG list (by NOT adding to files_to_keep? No wait)
                        # The logic below says:
                        # if upload_success: pass (don't add to files_to_keep) -> removed from RAG
                        # else: files_to_keep.append(file_item) -> kept for RAG
                        pass
                    else:
                        files_to_keep.append(file_item)
                else:
                    # Not a supported file type or image for non-Gemini model, keep it for RAG
                    files_to_keep.append(file_item)

            # Update files list
            # Always update if we have filtered anything, regardless of whether we processed new files
            if len(files_to_keep) != len(files):
                print(
                    f"🚫 Updating body['files']: {len(files)} -> {len(files_to_keep)}"
                )
                body["files"] = files_to_keep

        # Handle Analyzer Mode follow-up questions (No new files processed)
        # Only trigger if we are in analyzer mode AND we have processed files in this chat history
        has_processed_files = openwebui_chat_id and self.has_analyzed_files_in_chat(
            openwebui_chat_id
        )

        if effective_mode == "analyzer" and not processed_any and has_processed_files:
            # Check if we have a chat_id (meaning context might exist)
            if openwebui_chat_id:
                print(f"🤔 Analyzer Mode follow-up detected (has context).")

                user_text = last_message.get("content", "")
                if isinstance(user_text, list):
                    user_text = " ".join(
                        [item["text"] for item in user_text if item["type"] == "text"]
                    )

                # Only analyze if there is text content
                if user_text.strip():
                    await self.emit_status(
                        __event_emitter__,
                        (
                            "🧠 正在使用字幕精修专家处理追问..."
                            if is_subtitle_query
                            else "🧠 正在使用 Gemini 分析追问..."
                        ),
                        done=False,
                    )

                    loop = asyncio.get_running_loop()
                    followup_custom_model = (
                        self.valves.subtitle_custom_model_id
                        if is_subtitle_query
                        else self.valves.analyzer_custom_model_id
                    )
                    analysis_result = await loop.run_in_executor(
                        None,
                        self.analyze_document,
                        None,
                        user_text,
                        openwebui_chat_id,
                        followup_custom_model,
                        is_subtitle_query,
                    )

                    if analysis_result:
                        print(f"✅ Injecting follow-up analysis into context")
                        context_title = (
                            "【字幕精修专家回答】"
                            if is_subtitle_query
                            else "【文档分析助手回答】"
                        )
                        context_message = (
                            f"{context_title}\n{analysis_result}\n\n【用户新问题】\n"
                        )

                        content = last_message.get("content", "")
                        if isinstance(content, str):
                            last_message["content"] = context_message + content
                        elif isinstance(content, list):
                            content.insert(0, {"type": "text", "text": context_message})
                            last_message["content"] = content

                        await self.emit_status(
                            __event_emitter__,
                            f"✅ 追问分析完成，已注入上下文",
                            done=True,
                        )
                    else:
                        # If analysis fails or returns None (e.g. no session), we just let it pass.
                        # But wait, if analyze_document returns None, it might mean error.
                        # If it's a new chat with no files and no context, analyze_document might be confused?
                        # analyze_document handles file_url=None by using a specific prompt.
                        pass

        # 2. Process existing 'image_url' in content (Base64)
        # Only process if it's the target model (Gemini)
        if is_target_model:
            content = last_message.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        url = item.get("image_url", {}).get("url", "")
                        # Pass should_process_images=True because we already checked is_target_model
                        new_url = self.process_url(url, should_process_images=True)
                        if new_url != url:
                            item["image_url"]["url"] = new_url
                print("✅ Message content updated with adapter URLs")

        return body

    def outlet(self, body: dict, __user__: dict = None) -> dict:
        return body
