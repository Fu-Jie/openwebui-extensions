"""
title: Markdown Normalizer
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
version: 1.2.4
openwebui_id: baaa8732-9348-40b7-8359-7e009660e23c
description: A content normalizer filter that fixes common Markdown formatting issues in LLM outputs, such as broken code blocks, LaTeX formulas, and list formatting.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Callable, Dict
import re
import logging
import asyncio
import json
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class NormalizerConfig:
    """Configuration class for enabling/disabling specific normalization rules"""

    enable_escape_fix: bool = True  # Fix excessive escape characters
    enable_escape_fix_in_code_blocks: bool = (
        False  # Apply escape fix inside code blocks (default: False for safety)
    )
    enable_thought_tag_fix: bool = True  # Normalize thought tags
    enable_details_tag_fix: bool = True  # Normalize <details> tags (like thought tags)
    enable_code_block_fix: bool = True  # Fix code block formatting
    enable_latex_fix: bool = True  # Fix LaTeX formula formatting
    enable_list_fix: bool = (
        False  # Fix list item newlines (default off as it can be aggressive)
    )
    enable_unclosed_block_fix: bool = True  # Auto-close unclosed code blocks
    enable_fullwidth_symbol_fix: bool = False  # Fix full-width symbols in code blocks
    enable_mermaid_fix: bool = True  # Fix common Mermaid syntax errors
    enable_heading_fix: bool = (
        True  # Fix missing space in headings (#Header -> # Header)
    )
    enable_table_fix: bool = True  # Fix missing closing pipe in tables
    enable_xml_tag_cleanup: bool = True  # Cleanup leftover XML tags
    enable_emphasis_spacing_fix: bool = False  # Fix spaces inside **emphasis**

    # Custom cleaner functions (for advanced extension)
    custom_cleaners: List[Callable[[str], str]] = field(default_factory=list)


class ContentNormalizer:
    """LLM Output Content Normalizer - Production Grade Implementation"""

    # --- 1. Pre-compiled Regex Patterns (Performance Optimization) ---
    _PATTERNS = {
        # Code block prefix: if ``` is not at start of line (ignoring whitespace)
        "code_block_prefix": re.compile(r"(\S[ \t]*)(```)"),
        # Code block suffix: ```lang followed by non-whitespace (no newline)
        "code_block_suffix": re.compile(r"(```[\w\+\-\.]*)[ \t]+([^\n\r])"),
        # Code block indent: whitespace at start of line + ```
        "code_block_indent": re.compile(r"^[ \t]+(```)", re.MULTILINE),
        # Thought tag: </thought> followed by optional whitespace/newlines
        "thought_end": re.compile(
            r"</(thought|think|thinking)>[ \t]*\n*", re.IGNORECASE
        ),
        "thought_start": re.compile(r"<(thought|think|thinking)>", re.IGNORECASE),
        # Details tag: </details> followed by optional whitespace/newlines
        "details_end": re.compile(r"</details>[ \t]*\n*", re.IGNORECASE),
        # Self-closing details tag: <details ... /> followed by optional whitespace (but NOT already having newline)
        "details_self_closing": re.compile(
            r"(<details[^>]*/\s*>)(?!\n)", re.IGNORECASE
        ),
        # LaTeX block: \[ ... \]
        "latex_bracket_block": re.compile(r"\\\[(.+?)\\\]", re.DOTALL),
        # LaTeX inline: \( ... \)
        "latex_paren_inline": re.compile(r"\\\((.+?)\\\)"),
        # List item: non-newline + digit + dot + space
        "list_item": re.compile(r"([^\n])(\d+\. )"),
        # XML artifacts (e.g. Claude's)
        "xml_artifacts": re.compile(
            r"</?(?:antArtifact|antThinking|artifact)[^>]*>", re.IGNORECASE
        ),
        # Mermaid: Match various node shapes and quote unquoted labels
        # Fix "reverse optimization": Must precisely match shape delimiters to avoid breaking structure
        # Priority: Longer delimiters match first
        "mermaid_node": re.compile(
            r'("[^"\\]*(?:\\.[^"\\]*)*")|'  # Match quoted strings first (Group 1)
            r"(\w+)(?:"
            r"(\(\(\()(?![\"])(.*?)(?<![\"])(\)\)\))|"  # (((...))) Double Circle
            r"(\(\()(?![\"])(.*?)(?<![\"])(\)\))|"  # ((...)) Circle
            r"(\(\[)(?![\"])(.*?)(?<![\"])(\]\))|"  # ([...]) Stadium
            r"(\[\()(?![\"])(.*?)(?<![\"])(\)\])|"  # [(...)] Cylinder
            r"(\[\[)(?![\"])(.*?)(?<![\"])(\]\])|"  # [[...]] Subroutine
            r"(\{\{)(?![\"])(.*?)(?<![\"])(\}\})|"  # {{...}} Hexagon
            r"(\[/)(?![\"])(.*?)(?<![\"])(/\])|"  # [/.../] Parallelogram
            r"(\[\\)(?![\"])(.*?)(?<![\"])(\\\])|"  # [\...\] Parallelogram Alt
            r"(\[/)(?![\"])(.*?)(?<![\"])(\\\])|"  # [/...\] Trapezoid
            r"(\[\\)(?![\"])(.*?)(?<![\"])(/\])|"  # [\.../] Trapezoid Alt
            r"(\()(?![\"])([^)]*?)(?<![\"])(\))|"  # (...) Round - Modified to be safer
            r"(\[)(?![\"])(.*?)(?<![\"])(\])|"  # [...] Square
            r"(\{)(?![\"])(.*?)(?<![\"])(\})|"  # {...} Rhombus
            r"(>)(?![\"])(.*?)(?<![\"])(\])"  # >...] Asymmetric
            r")"
            r"(\s*\[\d+\])?",  # Capture optional citation [1]
            re.DOTALL,
        ),
        # Heading: #Heading -> # Heading
        "heading_space": re.compile(r"^(#+)([^ \n#])", re.MULTILINE),
        # Table: | col1 | col2 -> | col1 | col2 |
        "table_pipe": re.compile(r"^(\|.*[^|\n])$", re.MULTILINE),
        # Emphasis spacing: ** text ** -> **text**, __ text __ -> __text__
        # Matches emphasis blocks within a single line. We use a recursive approach
        # in _fix_emphasis_spacing to handle nesting and spaces correctly.
        # NOTE: We use [^\n] instead of . to prevent cross-line matching.
        # Supports: * (italic), ** (bold), *** (bold+italic), _ (italic), __ (bold), ___ (bold+italic)
        "emphasis_spacing": re.compile(
            r"(?<!\*|_)(\*{1,3}|_{1,3})(?P<inner>[^\n]*?)(\1)(?!\*|_)"
        ),
    }

    def __init__(self, config: Optional[NormalizerConfig] = None):
        self.config = config or NormalizerConfig()
        self.applied_fixes = []

    def normalize(self, content: str) -> str:
        """Main entry point: apply all normalization rules in order"""
        self.applied_fixes = []
        if not content:
            return content

        original_content = content  # Keep a copy for logging

        try:
            # 1. Escape character fix (Must be first)
            if self.config.enable_escape_fix:
                original = content
                content = self._fix_escape_characters(content)
                if content != original:
                    self.applied_fixes.append("Fix Escape Chars")

            # 2. Thought tag normalization
            if self.config.enable_thought_tag_fix:
                original = content
                content = self._fix_thought_tags(content)
                if content != original:
                    self.applied_fixes.append("Normalize Thought Tags")

            # 3. Details tag normalization (must be before heading fix)
            if self.config.enable_details_tag_fix:
                original = content
                content = self._fix_details_tags(content)
                if content != original:
                    self.applied_fixes.append("Normalize Details Tags")

            # 4. Code block formatting fix
            if self.config.enable_code_block_fix:
                original = content
                content = self._fix_code_blocks(content)
                if content != original:
                    self.applied_fixes.append("Fix Code Blocks")

            # 4. LaTeX formula normalization
            if self.config.enable_latex_fix:
                original = content
                content = self._fix_latex_formulas(content)
                if content != original:
                    self.applied_fixes.append("Normalize LaTeX")

            # 5. List formatting fix
            if self.config.enable_list_fix:
                original = content
                content = self._fix_list_formatting(content)
                if content != original:
                    self.applied_fixes.append("Fix List Format")

            # 6. Unclosed code block fix
            if self.config.enable_unclosed_block_fix:
                original = content
                content = self._fix_unclosed_code_blocks(content)
                if content != original:
                    self.applied_fixes.append("Close Code Blocks")

            # 7. Full-width symbol fix (in code blocks only)
            if self.config.enable_fullwidth_symbol_fix:
                original = content
                content = self._fix_fullwidth_symbols_in_code(content)
                if content != original:
                    self.applied_fixes.append("Fix Full-width Symbols")

            # 8. Mermaid syntax fix
            if self.config.enable_mermaid_fix:
                original = content
                content = self._fix_mermaid_syntax(content)
                if content != original:
                    self.applied_fixes.append("Fix Mermaid Syntax")

            # 9. Heading fix
            if self.config.enable_heading_fix:
                original = content
                content = self._fix_headings(content)
                if content != original:
                    self.applied_fixes.append("Fix Headings")

            # 10. Table fix
            if self.config.enable_table_fix:
                original = content
                content = self._fix_tables(content)
                if content != original:
                    self.applied_fixes.append("Fix Tables")

            # 11. XML tag cleanup
            if self.config.enable_xml_tag_cleanup:
                original = content
                content = self._cleanup_xml_tags(content)
                if content != original:
                    self.applied_fixes.append("Cleanup XML Tags")

            # 12. Emphasis spacing fix
            if self.config.enable_emphasis_spacing_fix:
                original = content
                content = self._fix_emphasis_spacing(content)
                if content != original:
                    self.applied_fixes.append("Fix Emphasis Spacing")

            # 9. Custom cleaners
            for cleaner in self.config.custom_cleaners:
                original = content
                content = cleaner(content)
                if content != original:
                    self.applied_fixes.append("Custom Cleaner")

            if self.applied_fixes:
                logger.info(f"Markdown Normalizer Applied Fixes: {self.applied_fixes}")
                logger.debug(
                    f"--- Original Content ---\n{original_content}\n------------------------"
                )
                logger.debug(
                    f"--- Normalized Content ---\n{content}\n--------------------------"
                )

            return content

        except Exception as e:
            # Production safeguard: return original content on error
            logger.error(f"Content normalization failed: {e}", exc_info=True)
            return content

    def _fix_escape_characters(self, content: str) -> str:
        """Fix excessive escape characters

        If enable_escape_fix_in_code_blocks is False (default), this method will only
        fix escape characters outside of code blocks to avoid breaking valid code
        examples (e.g., JSON strings with \\n, regex patterns, etc.).
        """
        if self.config.enable_escape_fix_in_code_blocks:
            # Apply globally (original behavior)
            content = content.replace("\\r\\n", "\n")
            content = content.replace("\\n", "\n")
            content = content.replace("\\t", "\t")
            content = content.replace("\\\\", "\\")
            return content
        else:
            # Apply only outside code blocks (safe mode)
            parts = content.split("```")
            for i in range(
                0, len(parts), 2
            ):  # Even indices are markdown text (not code)
                parts[i] = parts[i].replace("\\r\\n", "\n")
                parts[i] = parts[i].replace("\\n", "\n")
                parts[i] = parts[i].replace("\\t", "\t")
                parts[i] = parts[i].replace("\\\\", "\\")
            return "```".join(parts)

    def _fix_thought_tags(self, content: str) -> str:
        """Normalize thought tags: unify naming and fix spacing"""
        # 1. Standardize start tag: <think>, <thinking> -> <thought>
        content = self._PATTERNS["thought_start"].sub("<thought>", content)
        # 2. Standardize end tag and ensure newlines: </think> -> </thought>\n\n
        return self._PATTERNS["thought_end"].sub("</thought>\n\n", content)

    def _fix_details_tags(self, content: str) -> str:
        """Normalize <details> tags: ensure proper spacing after closing tags

        Handles two cases:
        1. </details> followed by content -> ensure double newline
        2. <details .../> (self-closing) followed by content -> ensure newline

        Note: Only applies outside of code blocks to avoid breaking code examples.
        """
        parts = content.split("```")
        for i in range(0, len(parts), 2):  # Even indices are markdown text
            # 1. Ensure double newline after </details>
            parts[i] = self._PATTERNS["details_end"].sub("</details>\n\n", parts[i])
            # 2. Ensure newline after self-closing <details ... />
            parts[i] = self._PATTERNS["details_self_closing"].sub(r"\1\n", parts[i])

        return "```".join(parts)

    def _fix_code_blocks(self, content: str) -> str:
        """Fix code block formatting (prefixes, suffixes, indentation)"""
        # Ensure newline before ```
        content = self._PATTERNS["code_block_prefix"].sub(r"\n\1", content)
        # Ensure newline after ```lang
        content = self._PATTERNS["code_block_suffix"].sub(r"\1\n\2", content)
        return content

    def _fix_latex_formulas(self, content: str) -> str:
        r"""Normalize LaTeX formulas: \[ -> $$ (block), \( -> $ (inline)"""
        content = self._PATTERNS["latex_bracket_block"].sub(r"$$\1$$", content)
        content = self._PATTERNS["latex_paren_inline"].sub(r"$\1$", content)
        return content

    def _fix_list_formatting(self, content: str) -> str:
        """Fix missing newlines in lists (e.g., 'text1. item' -> 'text\\n1. item')"""
        return self._PATTERNS["list_item"].sub(r"\1\n\2", content)

    def _fix_unclosed_code_blocks(self, content: str) -> str:
        """Auto-close unclosed code blocks"""
        if content.count("```") % 2 != 0:
            content += "\n```"
        return content

    def _fix_fullwidth_symbols_in_code(self, content: str) -> str:
        """Convert full-width symbols to half-width inside code blocks"""
        FULLWIDTH_MAP = {
            "，": ",",
            "。": ".",
            "（": "(",
            "）": ")",
            "【": "[",
            "】": "]",
            "；": ";",
            "：": ":",
            "？": "?",
            "！": "!",
            "＂": '"',  # U+FF02 FULLWIDTH QUOTATION MARK
            "＇": "'",  # U+FF07 FULLWIDTH APOSTROPHE
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
        }

        parts = content.split("```")
        # Code block content is at odd indices: 1, 3, 5...
        for i in range(1, len(parts), 2):
            for full, half in FULLWIDTH_MAP.items():
                parts[i] = parts[i].replace(full, half)

        return "```".join(parts)

    def _fix_mermaid_syntax(self, content: str) -> str:
        """Fix common Mermaid syntax errors while preserving node shapes"""

        def replacer(match):
            # Group 1 is Quoted String (if matched)
            if match.group(1):
                return match.group(1)

            # Group 2 is ID
            id_str = match.group(2)

            # Find matching shape group
            groups = match.groups()
            citation = groups[-1] or ""  # Last group is citation

            # Iterate over shape groups (excluding the last citation group)
            for i in range(2, len(groups) - 1, 3):
                if groups[i] is not None:
                    open_char = groups[i]
                    content = groups[i + 1]
                    close_char = groups[i + 2]

                    # Append citation to content if present
                    if citation:
                        content += citation

                    # Escape quotes in content
                    content = content.replace('"', '\\"')

                    return f'{id_str}{open_char}"{content}"{close_char}'

            return match.group(0)

        parts = content.split("```")
        for i in range(1, len(parts), 2):
            # Check if it's a mermaid block
            lang_line = parts[i].split("\n", 1)[0].strip().lower()
            if "mermaid" in lang_line:
                # Protect edge labels (text between link start and arrow) from being modified
                # by temporarily replacing them with placeholders.
                # Covers all Mermaid link types:
                #   - Solid line:  A -- text --> B, A -- text --o B, A -- text --x B
                #   - Dotted line: A -. text .-> B, A -. text .-o B
                #   - Thick line:  A == text ==> B, A == text ==o B
                #   - No arrow:    A -- text --- B
                edge_labels = []

                def protect_edge_label(m):
                    start = m.group(1)  # Link start: --, -., or ==
                    label = m.group(2)  # Text content
                    arrow = m.group(3)  # Arrow/end pattern
                    edge_labels.append((start, label, arrow))
                    return f"___EDGE_LABEL_{len(edge_labels)-1}___"

                # Comprehensive edge label pattern for all Mermaid link types
                edge_label_pattern = (
                    r"(--|-\.|\=\=)\s+(.+?)\s+(--+[>ox]?|--+\|>|\.-[>ox]?|=+[>ox]?)"
                )
                protected = re.sub(edge_label_pattern, protect_edge_label, parts[i])

                # Apply the comprehensive regex fix to protected content
                fixed = self._PATTERNS["mermaid_node"].sub(replacer, protected)

                # Restore edge labels
                for idx, (start, label, arrow) in enumerate(edge_labels):
                    fixed = fixed.replace(
                        f"___EDGE_LABEL_{idx}___", f"{start} {label} {arrow}"
                    )

                parts[i] = fixed

                # Auto-close subgraphs
                subgraph_count = len(
                    re.findall(r"\bsubgraph\b", parts[i], re.IGNORECASE)
                )
                end_count = len(re.findall(r"\bend\b", parts[i], re.IGNORECASE))

                if subgraph_count > end_count:
                    missing_ends = subgraph_count - end_count
                    parts[i] = parts[i].rstrip() + ("\n    end" * missing_ends) + "\n"

        return "```".join(parts)

    def _fix_headings(self, content: str) -> str:
        """Fix missing space in headings: #Heading -> # Heading"""
        # We only fix if it's not inside a code block.
        # But splitting by code block is expensive.
        # Given headings usually don't appear inside code blocks without space in valid code (except comments),
        # we might risk false positives in comments like `#TODO`.
        # To be safe, let's split by code blocks.

        parts = content.split("```")
        for i in range(0, len(parts), 2):  # Even indices are markdown text
            parts[i] = self._PATTERNS["heading_space"].sub(r"\1 \2", parts[i])
        return "```".join(parts)

    def _fix_tables(self, content: str) -> str:
        """Fix tables missing closing pipe"""
        parts = content.split("```")
        for i in range(0, len(parts), 2):
            parts[i] = self._PATTERNS["table_pipe"].sub(r"\1|", parts[i])
        return "```".join(parts)

    def _cleanup_xml_tags(self, content: str) -> str:
        """Remove leftover XML tags"""
        return self._PATTERNS["xml_artifacts"].sub("", content)

    def _fix_emphasis_spacing(self, content: str) -> str:
        """Fix spaces inside **emphasis** or _emphasis_
        Example: ** text ** -> **text**, **text ** -> **text**, ** text** -> **text**
        """

        def replacer(match):
            symbol = match.group(1)
            inner = match.group("inner")

            # Recursive step: Fix emphasis spacing INSIDE the current block first
            # This ensures that ** _ italic _ ** becomes ** _italic_ ** before we strip outer spaces.
            inner = self._PATTERNS["emphasis_spacing"].sub(replacer, inner)

            # If no leading/trailing whitespace, nothing to fix at this level
            stripped_inner = inner.strip()
            if stripped_inner == inner:
                return f"{symbol}{inner}{symbol}"

            # Safeguard: If inner content is just whitespace, don't touch it
            if not stripped_inner:
                return match.group(0)

            # Safeguard: If it looks like a math expression or list of variables (e.g. " * 3 * " or " _ b _ ")
            # If the symbol is surrounded by spaces in the original text, it's likely an operator.
            if inner.startswith(" ") and inner.endswith(" "):
                # If it's single '*' or '_', and both sides have spaces, it's almost certainly an operator.
                if symbol in ["*", "_"]:
                    return match.group(0)

            # Safeguard: List marker protection
            # If symbol is single '*' and inner content starts with whitespace followed by emphasis markers,
            # this is likely a list item like "*   **bold**" - don't merge them.
            # Pattern: "*   **text**" should NOT become "***text**"
            if symbol == "*" and inner.lstrip().startswith(("*", "_")):
                return match.group(0)

            # Extended list marker protection:
            # If symbol is single '*' and inner starts with multiple spaces (list indentation pattern),
            # this is likely a list item like "*   text" - don't strip the spaces.
            # Pattern: "*   U16 forward **Kuang**" should NOT become "*U16 forward **Kuang**"
            if symbol == "*" and inner.startswith("   "):
                return match.group(0)

            return f"{symbol}{stripped_inner}{symbol}"

        parts = content.split("```")
        for i in range(0, len(parts), 2):  # Even indices are markdown text
            # We use a while loop to handle overlapping or multiple occurrences at the top level
            while True:
                new_part = self._PATTERNS["emphasis_spacing"].sub(replacer, parts[i])
                if new_part == parts[i]:
                    break
                parts[i] = new_part
        return "```".join(parts)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=50,
            description="Priority level. Higher runs later (recommended to run after other filters).",
        )
        enable_escape_fix: bool = Field(
            default=True, description="Fix excessive escape characters (\\n, \\t, etc.)"
        )
        enable_escape_fix_in_code_blocks: bool = Field(
            default=False,
            description="Apply escape fix inside code blocks (⚠️ Warning: May break valid code like JSON strings or regex patterns. Default: False for safety)",
        )
        enable_thought_tag_fix: bool = Field(
            default=True, description="Normalize </thought> tags"
        )
        enable_details_tag_fix: bool = Field(
            default=True,
            description="Normalize <details> tags (add blank line after </details> and handle self-closing tags)",
        )
        enable_code_block_fix: bool = Field(
            default=True,
            description="Fix code block formatting (indentation, newlines)",
        )
        enable_latex_fix: bool = Field(
            default=True, description="Normalize LaTeX formulas (\\[ -> $$, \\( -> $)"
        )
        enable_list_fix: bool = Field(
            default=False, description="Fix list item newlines (Experimental)"
        )
        enable_unclosed_block_fix: bool = Field(
            default=True, description="Auto-close unclosed code blocks"
        )
        enable_fullwidth_symbol_fix: bool = Field(
            default=False, description="Fix full-width symbols in code blocks"
        )
        enable_mermaid_fix: bool = Field(
            default=True,
            description="Fix common Mermaid syntax errors (e.g. unquoted labels)",
        )
        enable_heading_fix: bool = Field(
            default=True,
            description="Fix missing space in headings (#Header -> # Header)",
        )
        enable_table_fix: bool = Field(
            default=True, description="Fix missing closing pipe in tables"
        )
        enable_xml_tag_cleanup: bool = Field(
            default=True, description="Cleanup leftover XML tags"
        )
        enable_emphasis_spacing_fix: bool = Field(
            default=False,
            description="Fix spaces inside **emphasis** (e.g. ** text ** -> **text**)",
        )
        show_status: bool = Field(
            default=True, description="Show status notification when fixes are applied"
        )
        show_debug_log: bool = Field(
            default=True, description="Print debug logs to browser console (F12)"
        )

    def __init__(self):
        self.valves = self.Valves()

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

    def _contains_html(self, content: str) -> bool:
        """Check if content contains HTML tags (to avoid breaking HTML output)"""
        # Removed common Mermaid-compatible tags like br, b, i, strong, em, span
        pattern = r"<\s*/?\s*(?:html|head|body|div|p|hr|ul|ol|li|table|thead|tbody|tfoot|tr|td|th|img|a|code|pre|blockquote|h[1-6]|script|style|form|input|button|label|select|option|iframe|link|meta|title)\b"
        return bool(re.search(pattern, content, re.IGNORECASE))

    async def _emit_status(self, __event_emitter__, applied_fixes: List[str]):
        """Emit status notification"""
        if not self.valves.show_status or not applied_fixes:
            return

        description = "✓ Markdown Normalized"
        if applied_fixes:
            description += f": {', '.join(applied_fixes)}"

        try:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "done": True,
                    },
                }
            )
        except Exception as e:
            print(f"Error emitting status: {e}")

    async def _emit_debug_log(
        self,
        __event_call__,
        applied_fixes: List[str],
        original: str,
        normalized: str,
        chat_id: str = "",
    ):
        """Emit debug log to browser console via JS execution"""
        if not self.valves.show_debug_log or not __event_call__:
            return

        try:
            # Construct JS code
            js_code = f"""
                (async function() {{
                    console.group("🛠️ Markdown Normalizer Debug");
                    console.log("Chat ID:", {json.dumps(chat_id)});
                    console.log("Applied Fixes:", {json.dumps(applied_fixes, ensure_ascii=False)});
                    console.log("Original Content:", {json.dumps(original, ensure_ascii=False)});
                    console.log("Normalized Content:", {json.dumps(normalized, ensure_ascii=False)});
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

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
        __metadata__: Optional[dict] = None,
    ) -> dict:
        """
        Process the response body to normalize Markdown content.
        """
        if "messages" in body and body["messages"]:
            last = body["messages"][-1]
            content = last.get("content", "") or ""

            if last.get("role") == "assistant" and isinstance(content, str):
                # Skip if content looks like HTML to avoid breaking it
                if self._contains_html(content):
                    return body

                # Skip if content contains tool output markers (native function calling)
                # Pattern: ""&quot;...&quot;"" or tool_call_id or <details type="tool_calls"...>
                if (
                    '""&quot;' in content
                    or "tool_call_id" in content
                    or '<details type="tool_calls"' in content
                ):
                    return body

                # Configure normalizer based on valves
                config = NormalizerConfig(
                    enable_escape_fix=self.valves.enable_escape_fix,
                    enable_escape_fix_in_code_blocks=self.valves.enable_escape_fix_in_code_blocks,
                    enable_thought_tag_fix=self.valves.enable_thought_tag_fix,
                    enable_details_tag_fix=self.valves.enable_details_tag_fix,
                    enable_code_block_fix=self.valves.enable_code_block_fix,
                    enable_latex_fix=self.valves.enable_latex_fix,
                    enable_list_fix=self.valves.enable_list_fix,
                    enable_unclosed_block_fix=self.valves.enable_unclosed_block_fix,
                    enable_fullwidth_symbol_fix=self.valves.enable_fullwidth_symbol_fix,
                    enable_mermaid_fix=self.valves.enable_mermaid_fix,
                    enable_heading_fix=self.valves.enable_heading_fix,
                    enable_table_fix=self.valves.enable_table_fix,
                    enable_xml_tag_cleanup=self.valves.enable_xml_tag_cleanup,
                    enable_emphasis_spacing_fix=self.valves.enable_emphasis_spacing_fix,
                )

                normalizer = ContentNormalizer(config)

                # Execute normalization
                new_content = normalizer.normalize(content)

                # Update content if changed
                if new_content != content:
                    last["content"] = new_content

                    # Emit status if enabled
                    if __event_emitter__:
                        await self._emit_status(
                            __event_emitter__, normalizer.applied_fixes
                        )
                        chat_ctx = self._get_chat_context(body, __metadata__)
                        await self._emit_debug_log(
                            __event_call__,
                            normalizer.applied_fixes,
                            content,
                            new_content,
                            chat_id=chat_ctx["chat_id"],
                        )

        return body
