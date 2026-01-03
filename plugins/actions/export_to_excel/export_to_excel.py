"""
title: Export to Excel
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.3.7
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xNSAySDZhMiAyIDAgMCAwLTIgMnYxNmEyIDIgMCAwIDAgMiAyaDEyYTIgMiAwIDAgMCAyLTJWN1oiLz48cGF0aCBkPSJNMTQgMnY0YTIgMiAwIDAgMCAyIDJoNCIvPjxwYXRoIGQ9Ik04IDEzaDIiLz48cGF0aCBkPSJNMTQgMTNoMiIvPjxwYXRoIGQ9Ik04IDE3aDIiLz48cGF0aCBkPSJNMTQgMTdoMiIvPjwvc3ZnPg==
description: Extracts tables from chat messages and exports them to Excel (.xlsx) files with smart formatting.
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
            description="Title Source: 'chat_title' (Chat Title), 'ai_generated' (AI Generated), 'markdown_title' (Markdown Title)",
        )
        EXPORT_SCOPE: Literal["last_message", "all_messages"] = Field(
            default="last_message",
            description="Export Scope: 'last_message' (Last Message Only), 'all_messages' (All Messages)",
        )
        MODEL_ID: str = Field(
            default="",
            description="Model ID for AI title generation. Leave empty to use the current chat model.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def _send_notification(self, emitter: Callable, type: str, content: str):
        await emitter(
            {"type": "notification", "data": {"type": type, "content": content}}
        )

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
                    "data": {"description": "Saving to file...", "done": False},
                }
            )

            try:
                messages = body.get("messages", [])
                if not messages:
                    raise HTTPException(status_code=400, detail="No messages found.")

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
                    # If multiple messages, we need to ensure uniqueness across the whole workbook
                    # We'll generate base names here and deduplicate later if needed,
                    # or better: generate unique names on the fly.

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
                        # Note: Generating titles for EVERY table in all messages might be too slow/expensive.
                        # We'll skip this for 'all_messages' scope to avoid timeout, unless it's just one message.
                        if (
                            not sheet_name
                            and self.valves.TITLE_SOURCE == "ai_generated"
                            and len(target_messages) == 1
                        ):
                            # Logic for AI generation (simplified for now, reusing existing flow if possible)
                            pass

                        # 3. Fallback: Message Index
                        if not sheet_name:
                            if len(target_messages) > 1:
                                # Use global message index (from original list if possible, but here we iterate target_messages)
                                # Let's use the loop index.
                                # If multiple tables in one message: "Msg 1 - Table 1"
                                if len(tables) > 1:
                                    sheet_name = f"Msg{msg_index+1}-Tab{table_index+1}"
                                else:
                                    sheet_name = f"Msg{msg_index+1}"
                            else:
                                # Single message (last_message scope)
                                if len(tables) > 1:
                                    sheet_name = f"Table {table_index+1}"
                                else:
                                    sheet_name = "Sheet1"

                        all_tables.append(table)
                        all_sheet_names.append(sheet_name)

                if not all_tables:
                    raise HTTPException(
                        status_code=400, detail="No tables found in the selected scope."
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

                # Notify user about the number of tables found
                table_count = len(all_tables)
                if self.valves.EXPORT_SCOPE == "all_messages":
                    await self._send_notification(
                        __event_emitter__,
                        "info",
                        f"Found {table_count} table(s) in all messages.",
                    )
                    # Wait a moment for user to see the notification before download dialog
                    await asyncio.sleep(1.5)
                # Generate Workbook Title (Filename)
                # Use the title of the chat, or the first header of the first message with tables
                title = ""
                chat_id = self.extract_chat_id(body, None)
                chat_title = ""
                if chat_id:
                    chat_title = await self.fetch_chat_title(chat_id, user_id)

                if (
                    self.valves.TITLE_SOURCE == "chat_title"
                    or not self.valves.TITLE_SOURCE
                ):
                    title = chat_title
                elif self.valves.TITLE_SOURCE == "ai_generated":
                    # Use AI to generate a title based on message content
                    if target_messages and __request__:
                        # Get content from the first message with tables
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
                    # Try to find first header in the first message that has content
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
                        # Try extracting from content again if not already tried
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
                        "data": {"description": "File saved", "done": True},
                    }
                )

                # Clean up temp file
                if os.path.exists(excel_file_path):
                    os.remove(excel_file_path)

                return {"message": "Download triggered"}

            except HTTPException as e:
                print(f"Error processing tables: {str(e.detail)}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error saving file: {e.detail}",
                            "done": True,
                        },
                    }
                )
                await self._send_notification(
                    __event_emitter__, "error", "No tables found to export!"
                )
                raise e
            except Exception as e:
                print(f"Error processing tables: {str(e)}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Error saving file: {str(e)}",
                            "done": True,
                        },
                    }
                )
                await self._send_notification(
                    __event_emitter__, "error", "No tables found to export!"
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
            # Use configured MODEL_ID or fallback to current chat model
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
                        "content": "You are a helpful assistant. Generate a short, concise filename (max 10 words) for an Excel export based on the following content. Do not use quotes or file extensions. Avoid special characters that are invalid in filenames. Only output the filename.",
                    },
                    {"role": "user", "content": content[:2000]},  # Limit content length
                ],
                "stream": False,
            }

            # Define the generation task
            async def generate_task():
                return await generate_chat_completion(request, payload, user_obj)

            # Define the notification task
            async def notification_task():
                # Send initial notification immediately
                if event_emitter:
                    await self._send_notification(
                        event_emitter,
                        "info",
                        "AI is generating a filename for your Excel file...",
                    )

                # Subsequent notifications every 5 seconds
                while True:
                    await asyncio.sleep(5)
                    if event_emitter:
                        await self._send_notification(
                            event_emitter,
                            "info",
                            "Still generating filename, please be patient...",
                        )

            # Run tasks concurrently
            gen_future = asyncio.ensure_future(generate_task())
            notify_future = asyncio.ensure_future(notification_task())

            done, pending = await asyncio.wait(
                [gen_future, notify_future], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel notification task if generation is done
            if not notify_future.done():
                notify_future.cancel()

            # Get result
            if gen_future in done:
                response = gen_future.result()
                if response and "choices" in response:
                    return response["choices"][0]["message"]["content"].strip()
            else:
                # Should not happen if return_when=FIRST_COMPLETED and we cancel notify
                await gen_future
                response = gen_future.result()
                if response and "choices" in response:
                    return response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"Error generating title: {e}")
            if event_emitter:
                await self._send_notification(
                    event_emitter,
                    "warning",
                    f"AI title generation failed, using default title. Error: {str(e)}",
                )

        return ""

    def extract_title(self, content: str) -> str:
        """Extract title from Markdown h1/h2 only"""
        lines = content.split("\n")
        for line in lines:
            # Match h1-h2 headings only
            match = re.match(r"^#{1,2}\s+(.+)$", line.strip())
            if match:
                return match.group(1).strip()
        return ""

    def extract_chat_id(self, body: dict, metadata: Optional[dict]) -> str:
        """Extract chat_id from body or metadata"""
        if isinstance(body, dict):
            chat_id = body.get("chat_id") or body.get("id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()

            for key in ("chat", "conversation"):
                nested = body.get(key)
                if isinstance(nested, dict):
                    nested_id = nested.get("id") or nested.get("chat_id")
                    if isinstance(nested_id, str) and nested_id.strip():
                        return nested_id.strip()
        if isinstance(metadata, dict):
            chat_id = metadata.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()
        return ""

    async def fetch_chat_title(self, chat_id: str, user_id: str = "") -> str:
        """Fetch chat title from database by chat_id"""
        if not chat_id:
            return ""

        def _load_chat():
            if user_id:
                return Chats.get_chat_by_id_and_user_id(id=chat_id, user_id=user_id)
            return Chats.get_chat_by_id(chat_id)

        try:
            chat = await asyncio.to_thread(_load_chat)
        except Exception as exc:
            print(f"Failed to load chat {chat_id}: {exc}")
            return ""

        if not chat:
            return ""

        data = getattr(chat, "chat", {}) or {}
        title = data.get("title") or getattr(chat, "title", "")
        return title.strip() if isinstance(title, str) else ""

    def extract_tables_from_message(self, message: str) -> List[Dict]:
        """
        Extract Markdown tables and their positions from message text
        Returns structure: [{
            "data": table data,
            "start_line": start line number,
            "end_line": end line number
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
                    start_line = current_line  # Record table start line

                # Process table row
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]

                # Skip separator row
                is_separator_row = all(re.fullmatch(r"[:\-]+", cell) for cell in cells)
                if not is_separator_row:
                    current_table.append(cells)
            elif current_table:
                # Table ends
                tables.append(
                    {
                        "data": current_table,
                        "start_line": start_line,
                        "end_line": current_line - 1,
                    }
                )
                current_table = []
                start_line = None

        # Process the last table
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
        Generate workbook name and sheet names based on content
        - Ignore non-empty paragraphs, only use markdown headers (h1-h6).
        - Single table: Use the closest header as workbook and sheet name.
        - Multiple tables: Use the first header in the document as workbook name, and closest header for each table as sheet name.
        - Default naming:
            - Workbook: Handled in main flow (user_yyyymmdd.xlsx).
            - Sheet: Sheet1, Sheet2, ...
        """
        lines = content.split("\n")
        workbook_name = ""
        sheet_names = []
        all_headers = []

        # 1. Find all h1-h6 headers and their positions
        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+", line):
                all_headers.append(
                    {"text": re.sub(r"^#{1,6}\s+", "", line).strip(), "line_num": i}
                )

        # 2. Generate sheet name for each table
        for i, table in enumerate(tables):
            table_start_line = table["start_line"] - 1  # Convert to 0-based index
            closest_header_text = None

            # Find closest header above current table
            candidate_headers = [
                h for h in all_headers if h["line_num"] < table_start_line
            ]
            if candidate_headers:
                # Find the header with the largest line number among candidates
                closest_header = max(candidate_headers, key=lambda x: x["line_num"])
                closest_header_text = closest_header["text"]

            if closest_header_text:
                # Clean and add found header
                sheet_names.append(self.clean_sheet_name(closest_header_text))
            else:
                # If no header found, use default name "Sheet{i+1}"
                sheet_names.append(f"Sheet{i+1}")

        # 3. Determine workbook name based on table count
        if len(tables) == 1:
            # Single table: Use its sheet name as workbook name (if not default "Sheet1")
            if sheet_names[0] != "Sheet1":
                workbook_name = sheet_names[0]
        elif len(tables) > 1:
            # Multiple tables: Use the first header in the document as workbook name
            if all_headers:
                # Find header with smallest line number
                first_header = min(all_headers, key=lambda x: x["line_num"])
                workbook_name = first_header["text"]

        # 4. Clean workbook name (if empty, main flow will use default name)
        workbook_name = self.clean_filename(workbook_name) if workbook_name else ""

        return workbook_name, sheet_names

    def clean_filename(self, name: str) -> str:
        """Clean illegal characters in filename"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def clean_sheet_name(self, name: str) -> str:
        """Clean sheet name (limit 31 chars, remove illegal chars)"""
        name = re.sub(r"[\\/*?[\]:]", "", name).strip()
        return name[:31] if len(name) > 31 else name

    # ======================== Enhanced Formatting ========================

    def calculate_text_width(self, text: str) -> float:
        """
        Calculate text display width, considering CJK characters
        CJK characters count as 2 units, others as 1 unit
        """
        if not text:
            return 0

        width = 0
        for char in str(text):
            # Check if CJK character
            if "\u4e00" <= char <= "\u9fff" or "\u3000" <= char <= "\u303f":
                width += 2
            else:
                width += 1

        return width

    def calculate_text_height(self, text: str, max_width: int = 50) -> int:
        """
        Calculate required lines for text display
        Based on newlines and text length
        """
        if not text:
            return 1

        text = str(text)
        # Calculate lines from newlines
        explicit_lines = text.count("\n") + 1

        # Calculate extra lines from wrapping
        text_width = self.calculate_text_width(text.replace("\n", ""))
        wrapped_lines = max(
            1, int(text_width / max_width) + (1 if text_width % max_width > 0 else 0)
        )

        return max(explicit_lines, wrapped_lines)

    def get_column_letter(self, col_index: int) -> str:
        """
        Convert column index to Excel column letter (A, B, C, ..., AA, AB, ...)
        """
        result = ""
        while col_index >= 0:
            result = chr(65 + col_index % 26) + result
            col_index = col_index // 26 - 1
        return result

    def determine_content_type(self, header: str, values: list) -> str:
        """
        Intelligently determine data type based on header and content
        Returns: 'number', 'date', 'sequence', 'text'
        """
        header_lower = str(header).lower().strip()

        # Check header keywords
        number_keywords = [
            "quantity",
            "amount",
            "price",
            "cost",
            "revenue",
            "expense",
            "total",
            "subtotal",
            "percentage",
            "%",
            "ratio",
            "rate",
            "value",
            "score",
            "points",
        ]
        date_keywords = ["date", "time", "year", "month", "moment"]
        sequence_keywords = [
            "no",
            "no.",
            "id",
            "index",
            "rank",
            "order",
            "sequence",
            "code",
        ]

        # Check header
        for keyword in number_keywords:
            if keyword in header_lower:
                return "number"

        for keyword in date_keywords:
            if keyword in header_lower:
                return "date"

        for keyword in sequence_keywords:
            if keyword in header_lower:
                return "sequence"

        # Check data content
        if not values:
            return "text"

        sample_values = [
            str(v).strip() for v in values[:10] if str(v).strip()
        ]  # Use first 10 non-empty values as sample
        if not sample_values:
            return "text"

        numeric_count = 0
        date_count = 0
        sequence_count = 0

        for value in sample_values:
            # Check if number
            try:
                float(value.replace(",", "").replace("%", ""))
                numeric_count += 1
                continue
            except ValueError:
                pass

            # Check if date format
            date_patterns = [
                r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
                r"\d{1,2}[-/]\d{1,2}[-/]\d{4}",
                r"\d{4}\d{2}\d{2}",
            ]
            for pattern in date_patterns:
                if re.match(pattern, value):
                    date_count += 1
                    break

            # Check if sequence format
            if (
                re.match(r"^\d+$", value) and len(value) <= 4
            ):  # Pure digits and <= 4 chars, likely sequence
                sequence_count += 1

        total_count = len(sample_values)

        # Determine type based on ratio
        if numeric_count / total_count >= 0.7:
            return "number"
        elif date_count / total_count >= 0.7:
            return "date"
        elif sequence_count / total_count >= 0.8 and sequence_count > 2:
            return "sequence"
        else:
            return "text"

    def save_tables_to_excel_enhanced(
        self, tables: List[Dict], file_path: str, sheet_names: List[str]
    ):
        """
        Enhanced Excel saving function with standard formatting
        """
        try:
            with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
                workbook = writer.book

                # OpenWebUI-style theme colors
                HEADER_BG = "#1f2937"  # Dark gray (matches OpenWebUI sidebar)
                HEADER_FG = "#ffffff"  # White text
                ROW_ODD_BG = "#ffffff"  # White for odd rows
                ROW_EVEN_BG = "#f3f4f6"  # Light gray for even rows (zebra striping)
                BORDER_COLOR = "#e5e7eb"  # Light border

                # Define header style - Center aligned
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

                # Text cell style - Left aligned (odd rows)
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

                # Text cell style - Left aligned (even rows - zebra)
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

                # Number cell style - Right aligned
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

                # Integer format - Right aligned
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

                # Decimal format - Right aligned
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

                # Date format - Center aligned
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

                # Sequence format - Center aligned
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

                # Bold cell style (for full cell bolding)
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

                # Italic cell style (for full cell italics)
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

                # Code cell style (for inline code with highlight background)
                CODE_BG = "#f0f0f0"  # Light gray background for code
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

                        # Get sheet name
                        sheet_name = (
                            sheet_names[i] if i < len(sheet_names) else f"Sheet{i+1}"
                        )

                        # Create DataFrame
                        headers = [
                            str(cell).strip()
                            for cell in table_data[0]
                            if str(cell).strip()
                        ]
                        if not headers:
                            print(f"Warning: No valid headers found for table {i+1}")
                            headers = [f"Col{j+1}" for j in range(len(table_data[0]))]

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

                        # Smart data type conversion using pandas infer_objects
                        for col in df.columns:
                            # Try numeric conversion first
                            try:
                                df[col] = pd.to_numeric(df[col])
                            except (ValueError, TypeError):
                                # Try datetime conversion
                                try:
                                    df[col] = pd.to_datetime(df[col], errors="raise")
                                except (ValueError, TypeError):
                                    # Keep as string, use infer_objects for optimization
                                    df[col] = df[col].infer_objects()

                        # Write data first (without header)
                        df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False,
                            header=False,
                            startrow=1,
                        )
                        worksheet = writer.sheets[sheet_name]

                        # Apply enhanced formatting with zebra striping
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
                        self.apply_enhanced_formatting(
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

    def apply_enhanced_formatting(
        self,
        worksheet,
        df,
        headers,
        workbook,
        formats,
    ):
        """
        Apply enhanced formatting with zebra striping
        - Header: Center aligned (dark background)
        - Number: Right aligned
        - Text: Left aligned
        - Date: Center aligned
        - Sequence: Center aligned
        - Zebra striping: alternating row colors
        - Supports full cell Markdown bold (**text**) and italic (*text*)
        """
        try:
            # Extract format from formats dict
            header_format = formats["header"]

            # 1. Write headers (Center aligned)
            print(f"Writing headers with enhanced alignment: {headers}")
            for col_idx, header in enumerate(headers):
                if header and str(header).strip():
                    worksheet.write(0, col_idx, str(header).strip(), header_format)
                else:
                    default_header = f"Col{col_idx+1}"
                    worksheet.write(0, col_idx, default_header, header_format)

            # 2. Analyze column types
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

            # 3. Write and format data with zebra striping
            for row_idx, row in df.iterrows():
                # Determine if odd or even row (0-indexed, so row 0 is odd visually as row 1)
                is_alt_row = (
                    row_idx % 2 == 1
                )  # Even index = odd visual row, use alt format

                for col_idx, value in enumerate(row):
                    content_type = column_types.get(col_idx, "text")

                    # Select format based on content type and zebra striping
                    fmt_idx = 1 if is_alt_row else 0

                    if content_type == "number":
                        # Number - Right aligned
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
                        # Date - Center aligned
                        current_format = formats["date"][fmt_idx]

                    elif content_type == "sequence":
                        # Sequence - Center aligned
                        current_format = formats["sequence"][fmt_idx]

                    else:
                        # Text - Left aligned
                        current_format = formats["text"][fmt_idx]

                    if content_type == "text" and isinstance(value, str):
                        # Check for full cell bold (**text**)
                        match_bold = re.fullmatch(r"\*\*(.+)\*\*", value.strip())
                        # Check for full cell italic (*text*)
                        match_italic = re.fullmatch(r"\*(.+)\*", value.strip())
                        # Check for full cell code (`text`)
                        match_code = re.fullmatch(r"`(.+)`", value.strip())

                        if match_bold:
                            # Extract content and apply bold format
                            clean_value = match_bold.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["bold"][fmt_idx],
                            )
                        elif match_italic:
                            # Extract content and apply italic format
                            clean_value = match_italic.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["italic"][fmt_idx],
                            )
                        elif match_code:
                            # Extract content and apply code format (highlighted)
                            clean_value = match_code.group(1)
                            worksheet.write(
                                row_idx + 1,
                                col_idx,
                                clean_value,
                                formats["code"][fmt_idx],
                            )
                        else:
                            # Remove partial markdown formatting symbols (can't render partial formatting in Excel)
                            # Remove bold markers **text** -> text
                            clean_value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
                            # Remove italic markers *text* -> text (but not inside **)
                            clean_value = re.sub(
                                r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", clean_value
                            )
                            # Remove code markers `text` -> text
                            clean_value = re.sub(r"`(.+?)`", r"\1", clean_value)
                            worksheet.write(
                                row_idx + 1, col_idx, clean_value, current_format
                            )
                    else:
                        worksheet.write(row_idx + 1, col_idx, value, current_format)

            # 4. Auto-adjust column width
            for col_idx, column in enumerate(headers):
                col_letter = self.get_column_letter(col_idx)

                # Calculate header width
                header_width = self.calculate_text_width(str(column))

                # Calculate max data width
                max_data_width = 0
                if not df.empty and col_idx < len(df.columns):
                    for value in df.iloc[:, col_idx]:
                        value_width = self.calculate_text_width(str(value))
                        max_data_width = max(max_data_width, value_width)

                # Base width
                base_width = max(header_width, max_data_width)

                # Adjust width based on type
                content_type = column_types.get(col_idx, "text")
                if content_type == "sequence":
                    optimal_width = max(8, min(15, base_width + 2))
                elif content_type == "number":
                    optimal_width = max(12, min(25, base_width + 3))
                elif content_type == "date":
                    optimal_width = max(15, min(20, base_width + 2))
                else:
                    if base_width <= 10:
                        optimal_width = base_width + 3
                    elif base_width <= 20:
                        optimal_width = base_width + 4
                    else:
                        optimal_width = base_width + 5
                    optimal_width = max(10, min(60, optimal_width))

                worksheet.set_column(f"{col_letter}:{col_letter}", optimal_width)

            # 5. Auto-adjust row height
            worksheet.set_row(0, 35)

            for row_idx, row in df.iterrows():
                max_row_height = 20

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
                    cell_height = cell_lines * 20

                    max_row_height = max(max_row_height, cell_height)

                final_height = min(120, max_row_height)
                worksheet.set_row(row_idx + 1, final_height)

            print(f"Successfully applied enhanced formatting")

        except Exception as e:
            print(f"Warning: Failed to apply enhanced formatting: {str(e)}")
            self.apply_basic_formatting_fallback(worksheet, df)

    def apply_basic_formatting_fallback(self, worksheet, df):
        """
        Basic formatting fallback
        """
        try:
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

        except Exception as e:
            print(f"Error in basic formatting: {str(e)}")

        except Exception as e:
            print(f"Error in basic formatting: {str(e)}")
