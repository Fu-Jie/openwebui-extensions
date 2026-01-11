"""
title: Markdown 格式修复器 (Markdown Normalizer)
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 1.0.1
description: 生产级内容规范化过滤器，修复 LLM 输出中常见的 Markdown 格式问题，如损坏的代码块、LaTeX 公式、Mermaid 图表和列表格式。
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Callable
import re
import logging
import asyncio
import json
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class NormalizerConfig:
    """配置类，用于启用/禁用特定的规范化规则"""

    enable_escape_fix: bool = True  # 修复过度的转义字符
    enable_thought_tag_fix: bool = True  # 规范化思维链标签
    enable_code_block_fix: bool = True  # 修复代码块格式
    enable_latex_fix: bool = True  # 修复 LaTeX 公式格式
    enable_list_fix: bool = False  # 修复列表项换行 (默认关闭，因为可能过于激进)
    enable_unclosed_block_fix: bool = True  # 自动闭合未闭合的代码块
    enable_fullwidth_symbol_fix: bool = False  # 修复代码块中的全角符号
    enable_mermaid_fix: bool = True  # 修复常见的 Mermaid 语法错误
    enable_heading_fix: bool = True  # 修复标题中缺失的空格 (#Header -> # Header)
    enable_table_fix: bool = True  # 修复表格中缺失的闭合管道符
    enable_xml_tag_cleanup: bool = True  # 清理残留的 XML 标签

    # 自定义清理函数 (用于高级扩展)
    custom_cleaners: List[Callable[[str], str]] = field(default_factory=list)


class ContentNormalizer:
    """LLM Output Content Normalizer - Production Grade Implementation"""

    # --- 1. Pre-compiled Regex Patterns (Performance Optimization) ---
    _PATTERNS = {
        # Code block prefix: if ``` is not at start of line or file
        "code_block_prefix": re.compile(r"(?<!^)(?<!\n)(```)", re.MULTILINE),
        # Code block suffix: ```lang followed by non-whitespace (no newline)
        "code_block_suffix": re.compile(r"(```[\w\+\-\.]*)[ \t]+([^\n\r])"),
        # Code block indent: whitespace at start of line + ```
        "code_block_indent": re.compile(r"^[ \t]+(```)", re.MULTILINE),
        # Thought tag: </thought> followed by optional whitespace/newlines
        "thought_end": re.compile(
            r"</(thought|think|thinking)>[ \t]*\n*", re.IGNORECASE
        ),
        "thought_start": re.compile(r"<(thought|think|thinking)>", re.IGNORECASE),
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
        # Mermaid: 匹配各种形状的节点并为未加引号的标签添加引号
        # 修复"反向优化"问题：必须精确匹配各种形状的定界符，避免破坏形状结构
        # 优先级：长定界符优先匹配
        "mermaid_node": re.compile(
            r'("[^"\\]*(?:\\.[^"\\]*)*")|'  # Match quoted strings first (Group 1)
            r"(\w+)\s*(?:"
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
            r"(\()(?![\"])(.*?)(?<![\"])(\))|"  # (...) Round
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

            # 3. Code block formatting fix
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

            # 9. Custom cleaners
            for cleaner in self.config.custom_cleaners:
                original = content
                content = cleaner(content)
                if content != original:
                    self.applied_fixes.append("Custom Cleaner")

            if self.applied_fixes:
                print(f"[Markdown Normalizer] Applied fixes: {self.applied_fixes}")
                print(
                    f"[Markdown Normalizer] --- Original Content ---\n{original_content}\n------------------------"
                )
                print(
                    f"[Markdown Normalizer] --- Normalized Content ---\n{content}\n--------------------------"
                )

            return content

        except Exception as e:
            # Production safeguard: return original content on error
            logger.error(f"Content normalization failed: {e}", exc_info=True)
            return content

    def _fix_escape_characters(self, content: str) -> str:
        """Fix excessive escape characters"""
        content = content.replace("\\r\\n", "\n")
        content = content.replace("\\n", "\n")
        content = content.replace("\\t", "\t")
        content = content.replace("\\\\", "\\")
        return content

    def _fix_thought_tags(self, content: str) -> str:
        """Normalize thought tags: unify naming and fix spacing"""
        # 1. Standardize start tag: <think>, <thinking> -> <thought>
        content = self._PATTERNS["thought_start"].sub("<thought>", content)
        # 2. Standardize end tag and ensure newlines: </think> -> </thought>\n\n
        return self._PATTERNS["thought_end"].sub("</thought>\n\n", content)

    def _fix_code_blocks(self, content: str) -> str:
        """Fix code block formatting (prefixes, suffixes, indentation)"""
        # Remove indentation before code blocks
        content = self._PATTERNS["code_block_indent"].sub(r"\1", content)
        # Ensure newline before ```
        content = self._PATTERNS["code_block_prefix"].sub(r"\n\1", content)
        # Ensure newline after ```lang
        content = self._PATTERNS["code_block_suffix"].sub(r"\1\n\2", content)
        return content

    def _fix_latex_formulas(self, content: str) -> str:
        """Normalize LaTeX formulas: \[ -> $$ (block), \( -> $ (inline)"""
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
            '"': '"',
            '"': '"',
            """: "'", """: "'",
        }

        parts = content.split("```")
        # Code block content is at odd indices: 1, 3, 5...
        for i in range(1, len(parts), 2):
            for full, half in FULLWIDTH_MAP.items():
                parts[i] = parts[i].replace(full, half)

        return "```".join(parts)

    def _fix_mermaid_syntax(self, content: str) -> str:
        """修复常见的 Mermaid 语法错误，同时保留节点形状"""

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

                    # 如果内容包含引号，进行转义
                    content = content.replace('"', '\\"')

                    return f'{id_str}{open_char}"{content}"{close_char}'

            return match.group(0)

        parts = content.split("```")
        for i in range(1, len(parts), 2):
            # Check if it's a mermaid block
            lang_line = parts[i].split("\n", 1)[0].strip().lower()
            if "mermaid" in lang_line:
                # Apply the comprehensive regex fix
                parts[i] = self._PATTERNS["mermaid_node"].sub(replacer, parts[i])

                # Auto-close subgraphs
                # Count 'subgraph' and 'end' (case-insensitive)
                # We use a simple regex to avoid matching words inside labels (though labels are now quoted, so it's safer)
                # But for simplicity and speed, we just count occurrences in the whole block.
                # A more robust way would be to strip quoted strings first, but that's expensive.
                # Given we just quoted everything, let's try to count keywords outside quotes?
                # Actually, since we just normalized nodes, most text is in quotes.
                # Let's just do a simple count. It's a heuristic fix.
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


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=50,
            description="优先级。数值越高运行越晚 (建议在其他过滤器之后运行)。",
        )
        enable_escape_fix: bool = Field(
            default=True, description="修复过度的转义字符 (\\n, \\t 等)"
        )
        enable_thought_tag_fix: bool = Field(
            default=True, description="规范化思维链标签 (<think> -> <thought>)"
        )
        enable_code_block_fix: bool = Field(
            default=True,
            description="修复代码块格式 (缩进、换行)",
        )
        enable_latex_fix: bool = Field(
            default=True, description="规范化 LaTeX 公式 (\\[ -> $$, \\( -> $)"
        )
        enable_list_fix: bool = Field(
            default=False, description="修复列表项换行 (实验性)"
        )
        enable_unclosed_block_fix: bool = Field(
            default=True, description="自动闭合未闭合的代码块"
        )
        enable_fullwidth_symbol_fix: bool = Field(
            default=False, description="修复代码块中的全角符号"
        )
        enable_mermaid_fix: bool = Field(
            default=True,
            description="修复常见的 Mermaid 语法错误 (如未加引号的标签)",
        )
        enable_heading_fix: bool = Field(
            default=True,
            description="修复标题中缺失的空格 (#Header -> # Header)",
        )
        enable_table_fix: bool = Field(
            default=True, description="修复表格中缺失的闭合管道符"
        )
        enable_xml_tag_cleanup: bool = Field(
            default=True, description="清理残留的 XML 标签"
        )
        show_status: bool = Field(default=True, description="应用修复时显示状态通知")
        show_debug_log: bool = Field(
            default=True, description="在浏览器控制台打印调试日志 (F12)"
        )

    def __init__(self):
        self.valves = self.Valves()

    def _contains_html(self, content: str) -> bool:
        """Check if content contains HTML tags (to avoid breaking HTML output)"""
        pattern = r"<\s*/?\s*(?:html|head|body|div|span|p|br|hr|ul|ol|li|table|thead|tbody|tfoot|tr|td|th|img|a|b|i|strong|em|code|pre|blockquote|h[1-6]|script|style|form|input|button|label|select|option|iframe|link|meta|title)\b"
        return bool(re.search(pattern, content, re.IGNORECASE))

    async def _emit_status(self, __event_emitter__, applied_fixes: List[str]):
        """Emit status notification"""
        if not self.valves.show_status or not applied_fixes:
            return

        description = "✓ Markdown 已修复"
        if applied_fixes:
            # Translate fix names for status display
            fix_map = {
                "Fix Escape Chars": "转义字符",
                "Normalize Thought Tags": "思维标签",
                "Fix Code Blocks": "代码块",
                "Normalize LaTeX": "LaTeX公式",
                "Fix List Format": "列表格式",
                "Close Code Blocks": "闭合代码块",
                "Fix Full-width Symbols": "全角符号",
                "Fix Mermaid Syntax": "Mermaid语法",
                "Fix Headings": "标题格式",
                "Fix Tables": "表格格式",
                "Cleanup XML Tags": "XML清理",
                "Custom Cleaner": "自定义清理",
            }
            translated_fixes = [fix_map.get(fix, fix) for fix in applied_fixes]
            description += f": {', '.join(translated_fixes)}"

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
        __event_emitter__,
        applied_fixes: List[str],
        original: str,
        normalized: str,
    ):
        """Emit debug log to browser console via JS execution"""

    async def _emit_debug_log(
        self, __event_call__, applied_fixes: List[str], original: str, normalized: str
    ):
        """Emit debug log to browser console via JS execution"""
        if not self.valves.show_debug_log or not __event_call__:
            return

        try:
            # Prepare data for JS
            log_data = {
                "fixes": applied_fixes,
                "original": original,
                "normalized": normalized,
            }

            # Construct JS code
            js_code = f"""
                (async function() {{
                    console.group("🛠️ Markdown Normalizer Debug");
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

                # Configure normalizer based on valves
                config = NormalizerConfig(
                    enable_escape_fix=self.valves.enable_escape_fix,
                    enable_thought_tag_fix=self.valves.enable_thought_tag_fix,
                    enable_code_block_fix=self.valves.enable_code_block_fix,
                    enable_latex_fix=self.valves.enable_latex_fix,
                    enable_list_fix=self.valves.enable_list_fix,
                    enable_unclosed_block_fix=self.valves.enable_unclosed_block_fix,
                    enable_fullwidth_symbol_fix=self.valves.enable_fullwidth_symbol_fix,
                    enable_mermaid_fix=self.valves.enable_mermaid_fix,
                    enable_heading_fix=self.valves.enable_heading_fix,
                    enable_table_fix=self.valves.enable_table_fix,
                    enable_xml_tag_cleanup=self.valves.enable_xml_tag_cleanup,
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
                        await self._emit_debug_log(
                            __event_call__,
                            normalizer.applied_fixes,
                            content,
                            new_content,
                        )

        return body
