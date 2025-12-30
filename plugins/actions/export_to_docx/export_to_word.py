"""
title: Export to Word
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.1.0
icon_url: data:image/svg+xml;base64,PHN2ZwogIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICB3aWR0aD0iMjQiCiAgaGVpZ2h0PSIyNCIKICB2aWV3Qm94PSIwIDAgMjQgMjQiCiAgZmlsbD0ibm9uZSIKICBzdHJva2U9ImN1cnJlbnRDb2xvciIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNNiAyMmEyIDIgMCAwIDEtMi0yVjRhMiAyIDAgMCAxIDItMmg4YTIuNCAyLjQgMCAwIDEgMS43MDQuNzA2bDMuNTg4IDMuNTg4QTIuNCAyLjQgMCAwIDEgMjAgOHYxMmEyIDIgMCAwIDEtMiAyeiIgLz4KICA8cGF0aCBkPSJNMTQgMnY1YTEgMSAwIDAgMCAxIDFoNSIgLz4KICA8cGF0aCBkPSJNMTAgOUg4IiAvPgogIDxwYXRoIGQ9Ik0xNiAxM0g4IiAvPgogIDxwYXRoIGQ9Ik0xNiAxN0g4IiAvPgo8L3N2Zz4K
requirements: python-docx==1.1.2
description: Export current conversation from Markdown to Word (.docx) file with proper Chinese and English encoding.
"""

import os
import re
import base64
import datetime
import io
import asyncio
import logging
from typing import Optional, Callable, Awaitable, Any, List, Tuple
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from open_webui.models.chats import Chats


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Action:
    def __init__(self):
        pass

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
        __metadata__: Optional[dict] = None,
    ):
        logger.info(f"action:{__name__}")

        # Parse user info
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
            last_assistant_message = body["messages"][-1]

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Converting to Word document...",
                        "done": False,
                    },
                }
            )

            try:
                message_content = last_assistant_message["content"]

                if not message_content or not message_content.strip():
                    await self._send_notification(
                        __event_emitter__, "error", "No content found to export!"
                    )
                    return

                # Generate filename (prefer chat title; fetch via chat_id if missing; then markdown title; then fallback)
                chat_id = self.extract_chat_id(body, __metadata__)
                chat_title = self.extract_chat_title(body)
                if not chat_title and chat_id:
                    chat_title = await self.fetch_chat_title(chat_id, user_id)
                title = self.extract_title(message_content)
                current_datetime = datetime.datetime.now()
                formatted_date = current_datetime.strftime("%Y%m%d")

                if chat_title:
                    filename = f"{self.clean_filename(chat_title)}.docx"
                elif title:
                    filename = f"{self.clean_filename(title)}.docx"
                else:
                    filename = f"{user_name}_{formatted_date}.docx"

                # Create Word document; if no h1 exists, inject chat title as h1
                has_h1 = bool(re.search(r"^#\s+.+$", message_content, re.MULTILINE))
                doc = self.markdown_to_docx(
                    message_content, top_heading=chat_title, has_h1=has_h1
                )

                # Save to memory
                doc_buffer = io.BytesIO()
                doc.save(doc_buffer)
                doc_buffer.seek(0)
                file_content = doc_buffer.read()
                base64_blob = base64.b64encode(file_content).decode("utf-8")

                # Trigger file download
                if __event_call__:
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
                                    const blob = new Blob([arrayBuffer], {{ type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }});
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
                        "data": {"description": "Word document exported", "done": True},
                    }
                )

                await self._send_notification(
                    __event_emitter__, "success", f"Successfully exported to {filename}"
                )

                return {"message": "Download triggered"}

            except Exception as e:
                logger.exception(f"Error exporting to Word: {str(e)}")
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Export failed: {str(e)}",
                            "done": True,
                        },
                    }
                )
                await self._send_notification(
                    __event_emitter__,
                    "error",
                    f"Error exporting Word document: {str(e)}",
                )

    def extract_title(self, content: str) -> str:
        """Extract title from Markdown h1/h2 only"""
        lines = content.split("\n")
        for line in lines:
            # Match h1-h2 headings only
            match = re.match(r"^#{1,2}\s+(.+)$", line.strip())
            if match:
                return match.group(1).strip()
        return ""

    def extract_chat_title(self, body: dict) -> str:
        """Extract chat title from common payload fields."""
        if not isinstance(body, dict):
            return ""

        candidates = []

        for key in ("chat", "conversation"):
            if isinstance(body.get(key), dict):
                candidates.append(body.get(key, {}).get("title", ""))

        for key in ("title", "chat_title"):
            value = body.get(key)
            if isinstance(value, str):
                candidates.append(value)

        for candidate in candidates:
            if candidate and isinstance(candidate, str):
                return candidate.strip()
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
            logger.warning(f"Failed to load chat {chat_id}: {exc}")
            return ""

        if not chat:
            return ""

        data = getattr(chat, "chat", {}) or {}
        title = data.get("title") or getattr(chat, "title", "")
        return title.strip() if isinstance(title, str) else ""

    def clean_filename(self, name: str) -> str:
        """Clean illegal characters from filename"""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()[:50]

    def markdown_to_docx(
        self, markdown_text: str, top_heading: str = "", has_h1: bool = False
    ) -> Document:
        """
        Convert Markdown text to Word document
        Supports: headings, paragraphs, bold, italic, code blocks, lists, tables, links
        """
        doc = Document()

        # Set default fonts
        self.set_document_default_font(doc)

        # If there is no h1 in content, prepend chat title as h1 when provided
        if top_heading and not has_h1:
            self.add_heading(doc, top_heading, 1)

        lines = markdown_text.split("\n")
        i = 0
        in_code_block = False
        code_block_content = []
        code_block_lang = ""
        in_list = False
        list_items = []
        list_type = None  # 'ordered' or 'unordered'

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Process pending list first
                    if in_list and list_items:
                        self.add_list_to_doc(doc, list_items, list_type)
                        list_items = []
                        in_list = False

                    in_code_block = True
                    code_block_lang = line.strip()[3:].strip()
                    code_block_content = []
                else:
                    # End code block
                    in_code_block = False
                    self.add_code_block(
                        doc, "\n".join(code_block_content), code_block_lang
                    )
                    code_block_content = []
                    code_block_lang = ""
                i += 1
                continue

            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue

            # Handle tables
            if line.strip().startswith("|") and line.strip().endswith("|"):
                # Process pending list first
                if in_list and list_items:
                    self.add_list_to_doc(doc, list_items, list_type)
                    list_items = []
                    in_list = False

                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                self.add_table(doc, table_lines)
                continue

            # Handle headings
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if header_match:
                # Process pending list first
                if in_list and list_items:
                    self.add_list_to_doc(doc, list_items, list_type)
                    list_items = []
                    in_list = False

                level = len(header_match.group(1))
                text = header_match.group(2)
                self.add_heading(doc, text, level)
                i += 1
                continue

            # Handle unordered lists
            unordered_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            if unordered_match:
                if not in_list or list_type != "unordered":
                    if in_list and list_items:
                        self.add_list_to_doc(doc, list_items, list_type)
                        list_items = []
                    in_list = True
                    list_type = "unordered"
                indent = len(unordered_match.group(1)) // 2
                list_items.append((indent, unordered_match.group(2)))
                i += 1
                continue

            # Handle ordered lists
            ordered_match = re.match(r"^(\s*)\d+[.)]\s+(.+)$", line)
            if ordered_match:
                if not in_list or list_type != "ordered":
                    if in_list and list_items:
                        self.add_list_to_doc(doc, list_items, list_type)
                        list_items = []
                    in_list = True
                    list_type = "ordered"
                indent = len(ordered_match.group(1)) // 2
                list_items.append((indent, ordered_match.group(2)))
                i += 1
                continue

            # Handle horizontal rules
            if re.match(r"^[-*_]{3,}$", line.strip()):
                # Process pending list first
                if in_list and list_items:
                    self.add_list_to_doc(doc, list_items, list_type)
                    list_items = []
                    in_list = False

                self.add_horizontal_rule(doc)
                i += 1
                continue

            # Handle empty lines
            if not line.strip():
                # End list
                if in_list and list_items:
                    self.add_list_to_doc(doc, list_items, list_type)
                    list_items = []
                    in_list = False
                i += 1
                continue

            # Handle normal paragraphs
            if in_list and list_items:
                self.add_list_to_doc(doc, list_items, list_type)
                list_items = []
                in_list = False

            self.add_paragraph(doc, line)
            i += 1

        # Process remaining list
        if in_list and list_items:
            self.add_list_to_doc(doc, list_items, list_type)

        return doc

    def set_document_default_font(self, doc: Document):
        """Set document default fonts for both Chinese and English"""
        # Set Normal style
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Times New Roman"  # English font
        font.size = Pt(11)

        # Set Chinese font
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

        # Set paragraph format
        paragraph_format = style.paragraph_format
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        paragraph_format.space_after = Pt(6)

    def add_heading(self, doc: Document, text: str, level: int):
        """Add heading"""
        # Word heading levels start from 0, Markdown from 1
        heading_level = min(level, 9)  # Word supports up to Heading 9
        heading = doc.add_heading(level=heading_level)

        # Parse and add formatted text
        self.add_formatted_text(heading, text)

        # Set Chinese font
        for run in heading.runs:
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")

    def add_paragraph(self, doc: Document, text: str):
        """Add paragraph with inline formatting support"""
        paragraph = doc.add_paragraph()
        self.add_formatted_text(paragraph, text)

        # Set Chinese font
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    def add_formatted_text(self, paragraph, text: str):
        """
        Parse Markdown inline formatting and add to paragraph
        Supports: bold, italic, inline code, links, strikethrough
        """
        # Define formatting patterns
        patterns = [
            # Bold italic ***text*** or ___text___
            (r"\*\*\*(.+?)\*\*\*|___(.+?)___", {"bold": True, "italic": True}),
            # Bold **text** or __text__
            (r"\*\*(.+?)\*\*|__(.+?)__", {"bold": True}),
            # Italic *text* or _text_
            (
                r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)",
                {"italic": True},
            ),
            # Inline code `code`
            (r"`([^`]+)`", {"code": True}),
            # Link [text](url)
            (r"\[([^\]]+)\]\(([^)]+)\)", {"link": True}),
            # Strikethrough ~~text~~
            (r"~~(.+?)~~", {"strike": True}),
        ]

        # Collect all matches
        all_matches = []

        for pattern, style in patterns:
            for match in re.finditer(pattern, text):
                # Get matched text content
                groups = match.groups()
                matched_text = next((g for g in groups if g is not None), "")
                all_matches.append(
                    {
                        "start": match.start(),
                        "end": match.end(),
                        "text": matched_text,
                        "style": style,
                        "full_match": match.group(0),
                        "url": (
                            groups[1] if style.get("link") and len(groups) > 1 else None
                        ),
                    }
                )

        # Sort by position
        all_matches.sort(key=lambda x: x["start"])

        # Remove overlapping matches
        filtered_matches = []
        last_end = 0
        for m in all_matches:
            if m["start"] >= last_end:
                filtered_matches.append(m)
                last_end = m["end"]

        # Build final text
        pos = 0
        for match in filtered_matches:
            # Add plain text before match
            if match["start"] > pos:
                plain_text = text[pos : match["start"]]
                if plain_text:
                    paragraph.add_run(plain_text)

            # Add formatted text
            style = match["style"]
            run_text = match["text"]

            if style.get("link"):
                # Link handling
                run = paragraph.add_run(run_text)
                run.font.color.rgb = RGBColor(0, 0, 255)
                run.font.underline = True
            elif style.get("code"):
                # Inline code
                run = paragraph.add_run(run_text)
                run.font.name = "Consolas"
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")
                run.font.size = Pt(10)
                # Add background color
                shading = OxmlElement("w:shd")
                shading.set(qn("w:fill"), "E8E8E8")
                run._element.rPr.append(shading)
            else:
                run = paragraph.add_run(run_text)
                if style.get("bold"):
                    run.bold = True
                if style.get("italic"):
                    run.italic = True
                if style.get("strike"):
                    run.font.strike = True

            pos = match["end"]

        # Add remaining plain text
        if pos < len(text):
            paragraph.add_run(text[pos:])

    def add_code_block(self, doc: Document, code: str, language: str = ""):
        """Add code block"""
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.5)
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(6)

        # Set code block font
        run = paragraph.add_run(code)
        run.font.name = "Consolas"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimHei")
        run.font.size = Pt(10)

        # Add light gray background
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "F5F5F5")
        paragraph._element.pPr.append(shading)

    def add_table(self, doc: Document, table_lines: List[str]):
        """Add table"""
        if len(table_lines) < 2:
            return

        # Parse table data
        rows = []
        for line in table_lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            # Skip separator row
            if all(re.fullmatch(r"[-:]+", cell) for cell in cells):
                continue
            rows.append(cells)

        if not rows:
            return

        # Determine column count
        num_cols = max(len(row) for row in rows)

        # Create table
        table = doc.add_table(rows=len(rows), cols=num_cols)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Fill table
        for row_idx, row_data in enumerate(rows):
            row = table.rows[row_idx]
            for col_idx, cell_text in enumerate(row_data):
                if col_idx < num_cols:
                    cell = row.cells[col_idx]
                    # Clear default paragraph
                    cell.paragraphs[0].clear()
                    self.add_formatted_text(cell.paragraphs[0], cell_text)

                    # Set cell font
                    for run in cell.paragraphs[0].runs:
                        run.font.name = "Times New Roman"
                        run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")
                        run.font.size = Pt(10)

                    # Bold header
                    if row_idx == 0:
                        for run in cell.paragraphs[0].runs:
                            run.bold = True

        # Center align cells
        for row in table.rows:
            for cell in row.cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_list_to_doc(
        self, doc: Document, items: List[Tuple[int, str]], list_type: str
    ):
        """Add list"""
        for indent, text in items:
            paragraph = doc.add_paragraph()

            if list_type == "unordered":
                # Unordered list with bullets
                paragraph.style = "List Bullet"
            else:
                # Ordered list with numbers
                paragraph.style = "List Number"

            # Set indent
            paragraph.paragraph_format.left_indent = Cm(0.5 * (indent + 1))

            # Add formatted text
            self.add_formatted_text(paragraph, text)

            # Set font
            for run in paragraph.runs:
                run.font.name = "Times New Roman"
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "SimSun")

    def add_horizontal_rule(self, doc: Document):
        """Add horizontal rule"""
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(12)
        paragraph.paragraph_format.space_after = Pt(12)

        # Add bottom border as horizontal rule
        pPr = paragraph._element.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "auto")
        pBdr.append(bottom)
        pPr.append(pBdr)
