"""
title: 导出为 Excel
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.3.7
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xNSAySDZhMiAyIDAgMCAwLTIgMnYxNmEyIDIgMCAwIDAgMiAyaDEyYTIgMiAwIDAgMCAyLTJWN1oiLz48cGF0aCBkPSJNMTQgMnY0YTIgMiAwIDAgMCAyIDJoNCIvPjxwYXRoIGQ9Ik04IDEzaDIiLz48cGF0aCBkPSJNMTQgMTNoMiIvPjxwYXRoIGQ9Ik04IDE3aDIiLz48cGF0aCBkPSJNMTQgMTdoMiIvPjwvc3ZnPg==
description: 从聊天消息中提取表格并导出为 Excel (.xlsx) 文件，支持智能格式化。
"""

import os
import pandas as pd
import re
import base64
from fastapi import FastAPI, HTTPException
from typing import Optional, Callable, Awaitable, Any, List, Dict
import datetime
import asyncio
from open_webui.models.chats import Chats
from open_webui.models.users import Users
from open_webui.utils.chat import generate_chat_completion
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI()


class Action:
    class Valves(BaseModel):
        TITLE_SOURCE: Literal["chat_title", "ai_generated", "markdown_title"] = Field(
            default="chat_title",
            description="标题来源: 'chat_title' (对话标题), 'ai_generated' (AI生成), 'markdown_title' (Markdown标题)",
        )
        SHOW_STATUS: bool = Field(
            default=True,
            description="是否显示操作状态更新。",
        )
        EXPORT_SCOPE: Literal["last_message", "all_messages"] = Field(
            default="last_message",
            description="导出范围: 'last_message' (仅最后一条消息), 'all_messages' (所有消息)",
        )
        MODEL_ID: str = Field(
            default="",
            description="AI 标题生成模型 ID。留空则使用当前对话模型。",
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="是否在浏览器控制台打印调试日志。",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def _emit_status(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        description: str,
        done: bool = False,
    ):
        """Emits a status update event."""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    async def _emit_notification(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        content: str,
        ntype: str = "info",
    ):
        """Emits a notification event (info, success, warning, error)."""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    async def _emit_debug_log(self, emitter, title: str, data: dict):
        """在浏览器控制台打印结构化调试日志"""
        if not self.valves.SHOW_DEBUG_LOG or not emitter:
            return

        try:
            import json

            js_code = f"""
                (async function() {{
                    console.group("🛠️ {title}");
                    console.log({json.dumps(data, ensure_ascii=False)});
                    console.groupEnd();
                }})();
            """

            await emitter({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            print(f"Error emitting debug log: {e}")

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __request__: Optional[Any] = None,
    ):
        print(f"action:{__name__}")
        if isinstance(__user__, (list, tuple)):
            user_language = (
                __user__[0].get("language", "en-US") if __user__ else "en-US"
            )
            user_name = __user__[0].get("name", "User") if __user__[0] else "User"
            user_id = (
                __user__[0]["id"]
                if __user__ and "id" in __user__[0]
                else "unknown_user"
            )
        elif isinstance(__user__, dict):
            user_language = __user__.get("language", "en-US")
            user_name = __user__.get("name", "User")
            user_id = __user__.get("id", "unknown_user")

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "正在保存文件...", "done": False},
                }
            )

            try:
                messages = body.get("messages", [])
                if not messages:
                    raise HTTPException(status_code=400, detail="未找到消息。")

                # Determine messages to process based on scope
                target_messages = []
                if self.valves.EXPORT_SCOPE == "all_messages":
                    target_messages = messages
                else:
                    target_messages = [messages[-1]]

                all_tables = []
                all_sheet_names = []

                # Process messages
                for msg_index, msg in enumerate(target_messages):
                    content = msg.get("content", "")
                    tables = self.extract_tables_from_message(content)

                    if not tables:
                        continue

                    # Generate sheet names for this message's tables

                    # Extract headers for this message
                    headers = []
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if re.match(r"^#{1,6}\s+", line):
                            headers.append(
                                {
                                    "text": re.sub(r"^#{1,6}\s+", "", line).strip(),
                                    "line_num": i,
                                }
                            )

                    for table_index, table in enumerate(tables):
                        sheet_name = ""

                        # 1. Try Markdown Header (closest above)
                        table_start_line = table["start_line"] - 1
                        closest_header_text = None
                        candidate_headers = [
                            h for h in headers if h["line_num"] < table_start_line
                        ]
                        if candidate_headers:
                            closest_header = max(
                                candidate_headers, key=lambda x: x["line_num"]
                            )
                            closest_header_text = closest_header["text"]

                        if closest_header_text:
                            sheet_name = self.clean_sheet_name(closest_header_text)

                        # 2. AI Generated (Only if explicitly enabled and we have a request object)
                        if (
                            not sheet_name
                            and self.valves.TITLE_SOURCE == "ai_generated"
                            and len(target_messages) == 1
                        ):
                            pass

                        # 3. Fallback: Message Index
                        if not sheet_name:
                            if len(target_messages) > 1:
                                if len(tables) > 1:
                                    sheet_name = f"消息{msg_index+1}-表{table_index+1}"
                                else:
                                    sheet_name = f"消息{msg_index+1}"
                            else:
                                # Single message (last_message scope)
                                if len(tables) > 1:
                                    sheet_name = f"表{table_index+1}"
                                else:
                                    sheet_name = "Sheet1"

                        all_tables.append(table)
                        all_sheet_names.append(sheet_name)

                if not all_tables:
                    raise HTTPException(
                        status_code=400, detail="在选定范围内未找到表格。"
                    )

                # Deduplicate sheet names
                final_sheet_names = []
                seen_names = {}
                for name in all_sheet_names:
                    base_name = name
                    counter = 1
                    while name in seen_names:
                        name = f"{base_name} ({counter})"
                        counter += 1
                    seen_names[name] = True
                    final_sheet_names.append(name)

                # 通知用户提取到的表格数量
                table_count = len(all_tables)
                if self.valves.EXPORT_SCOPE == "all_messages":
                    await self._emit_notification(
                        __event_emitter__,
                        f"从所有消息中提取到 {table_count} 个表格。",
                        "info",
                    )
                    # 等待片刻让用户看到通知，再触发下载
                    await asyncio.sleep(1.5)

                # Generate Workbook Title (Filename)
                title = ""
                chat_ctx = self._get_chat_context(body, None)
                chat_id = chat_ctx["chat_id"]
                chat_title = ""
                if chat_id:
                    chat_title = await self.fetch_chat_title(chat_id, user_id)

                if (
                    self.valves.TITLE_SOURCE == "chat_title"
                    or not self.valves.TITLE_SOURCE
                ):
                    title = chat_title
                elif self.valves.TITLE_SOURCE == "ai_generated":
                    # 使用 AI 根据消息内容生成标题
                    if target_messages and __request__:
                        # 获取第一条有表格的消息内容
                        content_for_title = ""
                        for msg in target_messages:
                            msg_content = msg.get("content", "")
                            if msg_content:
                                content_for_title = msg_content
                                break
                        if content_for_title:
                            title = await self.generate_title_using_ai(
                                body,
                                content_for_title,
                                user_id,
                                __request__,
                                __event_emitter__,
                            )
                elif self.valves.TITLE_SOURCE == "markdown_title":
                    for msg in target_messages:
                        extracted = self.extract_title(msg.get("content", ""))
                        if extracted:
                            title = extracted
                            break

                # Fallback for filename
                if not title:
                    if chat_title:
                        title = chat_title
                    else:
                        if self.valves.TITLE_SOURCE != "markdown_title":
                            for msg in target_messages:
                                extracted = self.extract_title(msg.get("content", ""))
                                if extracted:
                                    title = extracted
                                    break

                current_datetime = datetime.datetime.now()
                formatted_date = current_datetime.strftime("%Y%m%d")

                if not title:
                    workbook_name = f"{user_name}_{formatted_date}"
                else:
                    workbook_name = self.clean_filename(title)

                filename = f"{workbook_name}.xlsx"
                excel_file_path = os.path.join(
                    "app", "backend", "data", "temp", filename
                )

                os.makedirs(os.path.dirname(excel_file_path), exist_ok=True)

                # Save tables to Excel
                self.save_tables_to_excel_enhanced(
                    all_tables, excel_file_path, final_sheet_names
                )

                # Trigger file download
                if __event_call__:
                    with open(excel_file_path, "rb") as file:
                        file_content = file.read()
                        base64_blob = base64.b64encode(file_content).decode("utf-8")

                    await __event_call__(
                        {
                            "type": "execute",
                            "data": {
                                "code": f"""
                                try {{
                                    const base64Data = "{base64_blob}";
                                    const binaryData = atob(base64Data);
                                    const arrayBuffer = new Uint8Array(binaryData.length);
                                    for (let i = 0; i < binaryData.length; i++) {{
                                        arrayBuffer[i] = binaryData.charCodeAt(i);
                                    }}
                                    const blob = new Blob([arrayBuffer], {{ type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }});
                                    const filename = "{filename}";

                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement("a");
                                    a.style.display = "none";
                                    a.href = url;
                                    a.download = filename;
                                    document.body.appendChild(a);
                                    a.click();
                                    URL.revokeObjectURL(url);
                                    document.body.removeChild(a);
                                }} catch (error) {{
                                    console.error('Error triggering download:', error);
                                }}
                                """
                            },
                        }
                    )
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "文件已保存", "done": True},
                    }
                )

                # Clean up temp file
                if os.path.exists(excel_file_path):
                    os.remove(excel_file_path)

                return {"message": "下载已触发"}

            except HTTPException as e:
                print(f"Error processing tables: {str(e.detail)}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"保存文件错误: {e.detail}",
                            "done": True,
                        },
                    }
                )
                await self._emit_notification(
                    __event_emitter__, "未找到可导出的表格！", "error"
                )
                raise e
            except Exception as e:
                print(f"Error processing tables: {str(e)}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"保存文件错误: {str(e)}",
                            "done": True,
                        },
                    }
                )
                await self._emit_notification(
                    __event_emitter__, "未找到可导出的表格！", "error"
                )

    async def generate_title_using_ai(
        self,
        body: dict,
        content: str,
        user_id: str,
        request: Any,
        event_emitter: Callable = None,
    ) -> str:
        if not request:
            return ""

        try:
            user_obj = Users.get_user_by_id(user_id)
            # 使用配置的 MODEL_ID 或回退到当前对话模型
            model = (
                self.valves.MODEL_ID.strip()
                if self.valves.MODEL_ID
                else body.get("model")
            )

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个乐于助人的助手。请根据以下内容为 Excel 导出文件生成一个简短、简洁的文件名（最多10个字）。不要使用引号或文件扩展名。避免使用文件名中无效的特殊字符。只输出文件名。",
                    },
                    {"role": "user", "content": content[:2000]},  # 限制内容长度
                ],
                "stream": False,
            }

            # 定义生成任务
            async def generate_task():
                return await generate_chat_completion(request, payload, user_obj)

            # 定义通知任务
            async def notification_task():
                # 立即发送首次通知
                if event_emitter:
                    await self._emit_notification(
                        event_emitter,
                        "AI 正在为您生成文件名，请稍候...",
                        "info",
                    )

                # 之后每5秒通知一次
                while True:
                    await asyncio.sleep(5)
                    if event_emitter:
                        await self._emit_notification(
                            event_emitter,
                            "文件名生成中，请耐心等待...",
                            "info",
                        )

            # 并发运行任务
            gen_future = asyncio.ensure_future(generate_task())
            notify_future = asyncio.ensure_future(notification_task())

            done, pending = await asyncio.wait(
                [gen_future, notify_future], return_when=asyncio.FIRST_COMPLETED
            )

            # 如果生成完成，取消通知任务
            if not notify_future.done():
                notify_future.cancel()

            # 获取结果
            if gen_future in done:
                response = gen_future.result()
                if response and "choices" in response:
                    return response["choices"][0]["message"]["content"].strip()
            else:
                # 理论上不会发生，因为是 FIRST_COMPLETED 且我们取消了 notify
                await gen_future
                response = gen_future.result()
                if response and "choices" in response:
                    return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"生成标题时出错: {e}")
            if event_emitter:
                await self._emit_notification(
                    event_emitter,
                    f"AI 文件名生成失败，将使用默认名称。错误: {str(e)}",
                    "warning",
                )

        return ""

    def extract_title(self, content: str) -> str:
        """从 Markdown h1/h2 中提取标题"""
        lines = content.split("\n")
        for line in lines:
            # 仅匹配 h1-h2 标题
            match = re.match(r"^#{1,2}\s+(.+)$", line.strip())
            if match:
                return match.group(1).strip()
        return ""

    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """安全提取用户上下文信息。"""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", "unknown_user"),
            "user_name": user_data.get("name", "用户"),
            "user_language": user_data.get("language", "zh-CN"),
        }

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

    async def fetch_chat_title(self, chat_id: str, user_id: str = "") -> str:
        """通过 chat_id 从数据库获取对话标题"""
        if not chat_id:
            return ""

        def _load_chat():
            if user_id:
                return Chats.get_chat_by_id_and_user_id(id=chat_id, user_id=user_id)
            return Chats.get_chat_by_id(chat_id)

        try:
            chat = await asyncio.to_thread(_load_chat)
        except Exception as exc:
            print(f"加载对话 {chat_id} 失败: {exc}")
            return ""

        if not chat:
            return ""

        data = getattr(chat, "chat", {}) or {}
        title = data.get("title") or getattr(chat, "title", "")
        return title.strip() if isinstance(title, str) else ""

    def extract_tables_from_message(self, message: str) -> List[Dict]:
        """
        从消息文本中提取Markdown表格及位置信息
        返回结构: [{
            "data": 表格数据,
            "start_line": 起始行号,
            "end_line": 结束行号
        }]
        """
        table_row_pattern = r"^\s*\|.*\|.*\s*$"
        rows = message.split("\n")
        tables = []
        current_table = []
        start_line = None
        current_line = 0

        for row in rows:
            current_line += 1
            if re.search(table_row_pattern, row):
                if start_line is None:
                    start_line = current_line  # 记录表格起始行

                # 处理表格行
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]

                # 跳过分隔行
                is_separator_row = all(re.fullmatch(r"[:\-]+", cell) for cell in cells)
                if not is_separator_row:
                    current_table.append(cells)
            elif current_table:
                # 表格结束
                tables.append(
                    {
                        "data": current_table,
                        "start_line": start_line,
                        "end_line": current_line - 1,
                    }
                )
                current_table = []
                start_line = None

        # 处理最后一个表格
        if current_table:
            tables.append(
                {
                    "data": current_table,
                    "start_line": start_line,
                    "end_line": current_line,
                }
            )

        return tables

    def generate_names_from_content(self, content: str, tables: List[Dict]) -> tuple:
        """
        根据内容生成工作簿名称和sheet名称
        - 忽略非空段落，只使用 markdown 标题 (h1-h6)。
        - 单表格: 使用最近的标题作为工作簿和工作表名。
        - 多表格: 使用文档第一个标题作为工作簿名，各表格最近的标题作为工作表名。
        - 默认命名:
            - 工作簿: 在主流程中处理 (user_yyyymmdd.xlsx)。
            - 工作表: 表1, 表2, ...
        """
        lines = content.split("\n")
        workbook_name = ""
        sheet_names = []
        all_headers = []

        # 1. 查找文档中所有 h1-h6 标题及其位置
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                all_headers.append(
                    {"text": re.sub(r"^#{1,6}\s+", "", line).strip(), "line_num": i}
                )

        # 2. 为每个表格生成 sheet 名称
        for i, table in enumerate(tables):
            table_start_line = table["start_line"] - 1  # 转换为 0-based 索引
            closest_header_text = None

            # 查找当前表格上方最近的标题
            candidate_headers = [
                h for h in all_headers if h["line_num"] < table_start_line
            ]
            if candidate_headers:
                # 找到候选标题中行号最大的，即为最接近的
                closest_header = max(candidate_headers, key=lambda x: x["line_num"])
                closest_header_text = closest_header["text"]

            if closest_header_text:
                # 清理并添加找到的标题
                sheet_names.append(self.clean_sheet_name(closest_header_text))
            else:
                # 如果找不到标题，使用默认名称 "表{i+1}"
                sheet_names.append(f"表{i+1}")

        # 3. 根据表格数量确定工作簿名称
        if len(tables) == 1:
            # 单个表格: 使用其工作表名作为工作簿名 (前提是该名称不是默认的 "表1")
            if sheet_names[0] != "表1":
                workbook_name = sheet_names[0]
        elif len(tables) > 1:
            # 多个表格: 使用文档中的第一个标题作为工作簿名
            if all_headers:
                # 找到所有标题中行号最小的，即为第一个标题
                first_header = min(all_headers, key=lambda x: x["line_num"])
                workbook_name = first_header["text"]

        # 4. 清理工作簿名称 (如果为空，主流程会使用默认名称)
        workbook_name = self.clean_filename(workbook_name) if workbook_name else ""

        return workbook_name, sheet_names

    def clean_filename(self, name: str) -> str:
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def clean_sheet_name(self, name: str) -> str:
        """清理sheet名称(限制31字符,去除非法字符)"""
        name = re.sub(r"[\\/*?[\]:]", "", name).strip()
        return name[:31] if len(name) > 31 else name

    # ======================== 符合中国规范的格式化功能 ========================

    def calculate_text_width(self, text: str) -> float:
        """
        计算文本显示宽度，考虑中英文字符差异
        中文字符按2个单位计算，英文字符按1个单位计算
        """
        if not text:
            return 0

        width = 0
        for char in str(text):
            # 判断是否为中文字符（包括中文标点）
            if "\u4e00" <= char <= "\u9fff" or "\u3000" <= char <= "\u303f":
                width += 2  # 中文字符占2个单位宽度
            else:
                width += 1  # 英文字符占1个单位宽度

        return width

    def calculate_text_height(self, text: str, max_width: int = 50) -> int:
        """
        计算文本显示所需的行数
        根据换行符和文本长度计算
        """
        if not text:
            return 1

        text = str(text)
        # 计算换行符导致的行数
        explicit_lines = text.count("\n") + 1

        # 计算因文本长度超出而需要的额外行数
        text_width = self.calculate_text_width(text.replace("\n", ""))
        wrapped_lines = max(
            1, int(text_width / max_width) + (1 if text_width % max_width > 0 else 0)
        )

        return max(explicit_lines, wrapped_lines)

    def get_column_letter(self, col_index: int) -> str:
        """
        将列索引转换为Excel列字母 (A, B, C, ..., AA, AB, ...)
        """
        result = ""
        while col_index >= 0:
            result = chr(65 + col_index % 26) + result
            col_index = col_index // 26 - 1
        return result

    def determine_content_type(self, header: str, values: list) -> str:
        """
        根据表头和内容智能判断数据类型，符合中国官方表格规范
        返回: 'number', 'date', 'sequence', 'text'
        """
        header_lower = str(header).lower().strip()

        # 检查表头关键词
        number_keywords = [
            "数量",
            "金额",
            "价格",
            "费用",
            "成本",
            "收入",
            "支出",
            "总计",
            "小计",
            "百分比",
            "%",
            "比例",
            "率",
            "数值",
            "分数",
            "成绩",
            "得分",
        ]
        date_keywords = ["日期", "时间", "年份", "月份", "时刻", "date", "time"]
        sequence_keywords = [
            "序号",
            "编号",
            "号码",
            "排序",
            "次序",
            "顺序",
            "id",
            "编码",
        ]

        # 检查表头
        for keyword in number_keywords:
            if keyword in header_lower:
                return "number"

        for keyword in date_keywords:
            if keyword in header_lower:
                return "date"

        for keyword in sequence_keywords:
            if keyword in header_lower:
                return "sequence"

        # 检查数据内容
        if not values:
            return "text"

        sample_values = [
            str(v).strip() for v in values[:10] if str(v).strip()
        ]  # 取前10个非空值作为样本
        if not sample_values:
            return "text"

        numeric_count = 0
        date_count = 0
        sequence_count = 0

        for value in sample_values:
            # 检查是否为数字
            try:
                float(
                    value.replace(",", "")
                    .replace("，", "")
                    .replace("%", "")
                    .replace("％", "")
                )
                numeric_count += 1
                continue
            except ValueError:
                pass

            # 检查是否为日期格式
            date_patterns = [
                r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?",
                r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
                r"\d{4}\d{2}\d{2}",
            ]
            for pattern in date_patterns:
                if re.match(pattern, value):
                    date_count += 1
                    break

            # 检查是否为序号格式
            if (
                re.match(r"^\d+$", value) and len(value) <= 4
            ):  # 纯数字且不超过4位，可能是序号
                sequence_count += 1

        total_count = len(sample_values)

        # 根据比例判断类型
        if numeric_count / total_count >= 0.7:
            return "number"
        elif date_count / total_count >= 0.7:
            return "date"
        elif sequence_count / total_count >= 0.8 and sequence_count > 2:
            return "sequence"
        else:
            return "text"

    def get_column_letter(self, col_index: int) -> str:
        """
        将列索引转换为Excel列字母 (A, B, C, ..., AA, AB, ...)
        """
        result = ""
        while col_index >= 0:
            result = chr(65 + col_index % 26) + result
            col_index = col_index // 26 - 1
        return result

    def save_tables_to_excel_enhanced(
        self, tables: List[Dict], file_path: str, sheet_names: List[str]
    ):
        """
        符合中国官方表格规范的Excel保存功能
        """
        try:
            with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
                workbook = writer.book

                # OpenWebUI 风格主题配色
                HEADER_BG = "#1f2937"  # 深灰色 (匹配 OpenWebUI 侧边栏)
                HEADER_FG = "#ffffff"  # 白色文字
                ROW_ODD_BG = "#ffffff"  # 奇数行白色
                ROW_EVEN_BG = "#f3f4f6"  # 偶数行浅灰 (斑马纹)
                BORDER_COLOR = "#e5e7eb"  # 浅色边框

                # 表头样式 - 居中对齐
                header_format = workbook.add_format(
                    {
                        "bold": True,
                        "font_size": 11,
                        "font_name": "Arial",
                        "font_color": HEADER_FG,
                        "bg_color": HEADER_BG,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "align": "center",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                # 文本单元格样式 - 左对齐 (奇数行)
                text_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                # 文本单元格样式 - 左对齐 (偶数行 - 斑马纹)
                text_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                # 数值单元格样式 - 右对齐
                number_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                number_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                # 整数格式 - 右对齐
                integer_format = workbook.add_format(
                    {
                        "num_format": "0",
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                integer_format_alt = workbook.add_format(
                    {
                        "num_format": "0",
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                # 小数格式 - 右对齐
                decimal_format = workbook.add_format(
                    {
                        "num_format": "0.00",
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                decimal_format_alt = workbook.add_format(
                    {
                        "num_format": "0.00",
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "right",
                        "valign": "vcenter",
                    }
                )

                # 日期格式 - 居中对齐
                date_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "center",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                date_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "center",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                # 序号格式 - 居中对齐
                sequence_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "center",
                        "valign": "vcenter",
                    }
                )

                sequence_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "center",
                        "valign": "vcenter",
                    }
                )

                # 粗体单元格样式 (用于全单元格加粗)
                text_bold_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                        "bold": True,
                    }
                )

                text_bold_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                        "bold": True,
                    }
                )

                # 斜体单元格样式 (用于全单元格斜体)
                text_italic_format = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_ODD_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                        "italic": True,
                    }
                )

                text_italic_format_alt = workbook.add_format(
                    {
                        "font_name": "Arial",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": ROW_EVEN_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                        "italic": True,
                    }
                )

                # 代码单元格样式 (用于行内代码高亮显示)
                CODE_BG = "#f0f0f0"  # 代码浅灰背景
                text_code_format = workbook.add_format(
                    {
                        "font_name": "Consolas",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": CODE_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                text_code_format_alt = workbook.add_format(
                    {
                        "font_name": "Consolas",
                        "font_size": 10,
                        "border": 1,
                        "border_color": BORDER_COLOR,
                        "bg_color": CODE_BG,
                        "align": "left",
                        "valign": "vcenter",
                        "text_wrap": True,
                    }
                )

                for i, table in enumerate(tables):
                    try:
                        table_data = table["data"]
                        if not table_data or len(table_data) < 1:
                            print(f"Skipping empty table at index {i}")
                            continue

                        print(f"Processing table {i+1} with {len(table_data)} rows")

                        # 获取sheet名称
                        sheet_name = (
                            sheet_names[i] if i < len(sheet_names) else f"表{i+1}"
                        )

                        # 创建DataFrame
                        headers = [
                            str(cell).strip()
                            for cell in table_data[0]
                            if str(cell).strip()
                        ]
                        if not headers:
                            print(f"Warning: No valid headers found for table {i+1}")
                            headers = [f"列{j+1}" for j in range(len(table_data[0]))]

                        data_rows = []
                        if len(table_data) > 1:
                            max_cols = len(headers)
                            for row in table_data[1:]:
                                processed_row = []
                                for j in range(max_cols):
                                    if j < len(row):
                                        processed_row.append(str(row[j]))
                                    else:
                                        processed_row.append("")
                                data_rows.append(processed_row)
                            df = pd.DataFrame(data_rows, columns=headers)
                        else:
                            df = pd.DataFrame(columns=headers)

                        print(f"DataFrame created with columns: {list(df.columns)}")

                        # 智能数据类型转换
                        for col in df.columns:
                            # 先尝试数字转换
                            try:
                                df[col] = pd.to_numeric(df[col])
                            except (ValueError, TypeError):
                                # 尝试日期转换
                                try:
                                    df[col] = pd.to_datetime(df[col], errors="raise")
                                except (ValueError, TypeError):
                                    # 保持为字符串，使用 infer_objects 优化
                                    df[col] = df[col].infer_objects()

                        # 先写入数据（不包含表头）
                        df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False,
                            header=False,
                            startrow=1,
                        )
                        worksheet = writer.sheets[sheet_name]

                        # 应用符合中国规范的格式化 (带斑马纹)
                        formats = {
                            "header": header_format,
                            "text": [text_format, text_format_alt],
                            "number": [number_format, number_format_alt],
                            "integer": [integer_format, integer_format_alt],
                            "decimal": [decimal_format, decimal_format_alt],
                            "date": [date_format, date_format_alt],
                            "sequence": [sequence_format, sequence_format_alt],
                            "bold": [text_bold_format, text_bold_format_alt],
                            "italic": [text_italic_format, text_italic_format_alt],
                            "code": [text_code_format, text_code_format_alt],
                        }
                        self.apply_chinese_standard_formatting(
                            worksheet,
                            df,
                            headers,
                            workbook,
                            formats,
                        )

                    except Exception as e:
                        print(f"Error processing table {i+1}: {str(e)}")
                        continue

        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            raise

    def apply_chinese_standard_formatting(
        self,
        worksheet,
        df,
        headers,
        workbook,
        formats,
    ):
        """
        应用符合中国官方表格规范的格式化 (带斑马纹)
        - 表头: 居中对齐 (深色背景)
        - 数值: 右对齐
        - 文本: 左对齐
        - 日期: 居中对齐
        - 序号: 居中对齐
        - 斑马纹: 隔行变色
        - 支持全单元格 Markdown 粗体 (**text**) 和斜体 (*text*)
        """
        try:
            # 从 formats 字典提取格式
            header_format = formats["header"]

            # 1. 写入表头（居中对齐）
            print(f"Writing headers with Chinese standard alignment: {headers}")
            for col_idx, header in enumerate(headers):
                if header and str(header).strip():
                    worksheet.write(0, col_idx, str(header).strip(), header_format)
                else:
                    default_header = f"列{col_idx+1}"
                    worksheet.write(0, col_idx, default_header, header_format)

            # 2. 分析每列的数据类型并应用相应格式
            column_types = {}
            for col_idx, column in enumerate(headers):
                if col_idx < len(df.columns):
                    column_values = df.iloc[:, col_idx].tolist()
                    column_types[col_idx] = self.determine_content_type(
                        column, column_values
                    )
                    print(
                        f"Column '{column}' determined as type: {column_types[col_idx]}"
                    )
                else:
                    column_types[col_idx] = "text"

            # 3. 写入并格式化数据（带斑马纹）
            for row_idx, row in df.iterrows():
                # 确定奇偶行 (0-indexed, 所以 row 0 视觉上是第 1 行)
                is_alt_row = row_idx % 2 == 1  # 偶数索引 = 奇数行, 使用 alt 格式

                for col_idx, value in enumerate(row):
                    content_type = column_types.get(col_idx, "text")

                    # 根据内容类型和斑马纹选择格式
                    fmt_idx = 1 if is_alt_row else 0

                    if content_type == "number":
                        # 数值类型 - 右对齐
                        if pd.api.types.is_numeric_dtype(df.iloc[:, col_idx]):
                            if pd.api.types.is_integer_dtype(df.iloc[:, col_idx]):
                                current_format = formats["integer"][fmt_idx]
                            else:
                                try:
                                    numeric_value = float(value)
                                    if numeric_value.is_integer():
                                        current_format = formats["integer"][fmt_idx]
                                        value = int(numeric_value)
                                    else:
                                        current_format = formats["decimal"][fmt_idx]
                                except (ValueError, TypeError):
                                    current_format = formats["decimal"][fmt_idx]
                        else:
                            current_format = formats["number"][fmt_idx]

                    elif content_type == "date":
                        # 日期类型 - 居中对齐
                        current_format = formats["date"][fmt_idx]

                    elif content_type == "sequence":
                        # 序号类型 - 居中对齐
                        current_format = formats["sequence"][fmt_idx]

                    else:
                        # 文本类型 - 左对齐
                        current_format = formats["text"][fmt_idx]

                    if content_type == "text" and isinstance(value, str):
                        # 检查是否全单元格加粗 (**text**)
                        match_bold = re.fullmatch(r"\*\*(.+)\*\*", value.strip())
                        # 检查是否全单元格斜体 (*text*)
                        match_italic = re.fullmatch(r"\*(.+)\*", value.strip())
                        # 检查是否全单元格代码 (`text`)
                        match_code = re.fullmatch(r"`(.+)`", value.strip())

                        if match_bold:
                            # 提取内容并应用粗体格式
                            clean_value = match_bold.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["bold"][fmt_idx],
                            )
                        elif match_italic:
                            # 提取内容并应用斜体格式
                            clean_value = match_italic.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["italic"][fmt_idx],
                            )
                        elif match_code:
                            # 提取内容并应用代码格式 (高亮显示)
                            clean_value = match_code.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["code"][fmt_idx],
                            )
                        else:
                            # 移除部分 Markdown 格式符号 (Excel 无法渲染部分格式)
                            # 移除粗体标记 **text** -> text
                            clean_value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
                            # 移除斜体标记 *text* -> text (但不影响 ** 内部的内容)
                            clean_value = re.sub(
                                r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", clean_value
                            )
                            # 移除代码标记 `text` -> text
                            clean_value = re.sub(r"`(.+?)`", r"\1", clean_value)
                            worksheet.write(
                                row_idx + 1, col_idx, clean_value, current_format
                            )
                    else:
                        worksheet.write(row_idx + 1, col_idx, value, current_format)

            # 4. 自动调整列宽
            for col_idx, column in enumerate(headers):
                col_letter = self.get_column_letter(col_idx)

                # 计算表头宽度
                header_width = self.calculate_text_width(str(column))

                # 计算数据列的最大宽度
                max_data_width = 0
                if not df.empty and col_idx < len(df.columns):
                    for value in df.iloc[:, col_idx]:
                        value_width = self.calculate_text_width(str(value))
                        max_data_width = max(max_data_width, value_width)

                # 基础宽度：取表头和数据的最大宽度
                base_width = max(header_width, max_data_width)

                # 根据内容类型调整宽度
                content_type = column_types.get(col_idx, "text")
                if content_type == "sequence":
                    # 序号列通常比较窄
                    optimal_width = max(8, min(15, base_width + 2))
                elif content_type == "number":
                    # 数值列需要额外空间显示数字
                    optimal_width = max(12, min(25, base_width + 3))
                elif content_type == "date":
                    # 日期列需要固定宽度
                    optimal_width = max(15, min(20, base_width + 2))
                else:
                    # 文本列根据内容调整
                    if base_width <= 10:
                        optimal_width = base_width + 3
                    elif base_width <= 20:
                        optimal_width = base_width + 4
                    else:
                        optimal_width = base_width + 5
                    optimal_width = max(10, min(60, optimal_width))

                worksheet.set_column(f"{col_letter}:{col_letter}", optimal_width)

            # 5. 自动调整行高
            # 设置表头行高为35点
            worksheet.set_row(0, 35)

            # 设置数据行行高
            for row_idx, row in df.iterrows():
                max_row_height = 20  # 中国表格规范建议的最小行高

                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):
                        col_width = min(
                            60,
                            max(
                                10, self.calculate_text_width(str(headers[col_idx])) + 5
                            ),
                        )
                    else:
                        col_width = 15

                    cell_lines = self.calculate_text_height(str(value), col_width)
                    cell_height = cell_lines * 20  # 每行20点高度，符合中国规范

                    max_row_height = max(max_row_height, cell_height)

                final_height = min(120, max_row_height)
                worksheet.set_row(row_idx + 1, final_height)

            print(f"Successfully applied Chinese standard formatting")

        except Exception as e:
            print(f"Warning: Failed to apply Chinese standard formatting: {str(e)}")
            # 降级到基础格式化
            self.apply_basic_formatting_fallback(worksheet, df)

    def apply_basic_formatting_fallback(self, worksheet, df):
        """
        基础格式化降级方案
        """
        try:
            # 基础列宽调整
            for i, column in enumerate(df.columns):
                column_width = (
                    max(
                        len(str(column)),
                        (df[column].astype(str).map(len).max() if not df.empty else 0),
                    )
                    + 2
                )

                col_letter = self.get_column_letter(i)
                worksheet.set_column(
                    f"{col_letter}:{col_letter}", min(60, max(10, column_width))
                )

            print("Applied basic formatting fallback")

        except Exception as e:
            print(f"Warning: Even basic formatting failed: {str(e)}")

        except Exception as e:
            print(f"Warning: Even basic formatting failed: {str(e)}")
