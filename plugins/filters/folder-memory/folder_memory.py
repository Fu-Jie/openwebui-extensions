"""
title: 📂 Folder Memory
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
version: 0.1.0
description: Automatically extracts project rules from conversations and injects them into the folder's system prompt.
requirements:
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from fastapi import Request
import logging
import json
import re
import asyncio
from datetime import datetime

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
from open_webui.models.folders import Folders, FolderUpdateForm
from open_webui.models.chats import Chats

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Markers for rule injection
RULES_BLOCK_START = "<!-- OWUI_PROJECT_RULES_START -->"
RULES_BLOCK_END = "<!-- OWUI_PROJECT_RULES_END -->"

# System Prompt for Rule Generation
SYSTEM_PROMPT_RULE_GENERATOR = """
You are a project rule extractor. Your task is to extract "Project Rules" from the conversation and merge them with existing rules.

### Input
1. **Existing Rules**: Current rules in the folder system prompt.
2. **Conversation**: Recent chat history.

### Goal
Synthesize a concise list of rules that apply to this project/folder.
- **Remove** rules that are no longer relevant or were one-off instructions.
- **Add** new consistent requirements found in the conversation.
- **Merge** similar rules.
- **Format**: Concise bullet points (Markdown).

### Output Format
ONLY output the rules list as Markdown bullet points. Do not include any intro/outro text.
Example:
- Always use Python 3.11 for type hinting.
- Docstrings must follow Google style.
- Commit messages should be in English.
"""


class Filter:
    class Valves(BaseModel):
        PRIORITY: int = Field(
            default=20, description="Priority level for the filter operations."
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False, description="Show debug logs in console."
        )
        MESSAGE_TRIGGER_COUNT: int = Field(
            default=10, description="Analyze rules after every N messages in a chat."
        )
        MODEL_ID: str = Field(
            default="",
            description="Model used for rule extraction. If empty, uses the current chat model.",
        )
        RULES_BLOCK_TITLE: str = Field(
            default="## 📂 Project Rules",
            description="Title displayed above the rules block.",
        )
        UPDATE_ROOT_FOLDER: bool = Field(
            default=False,
            description="If enabled, finds and updates the root folder rules instead of the current subfolder.",
        )

    def __init__(self):
        self.valves = self.Valves()

    # ==================== Helper Methods ====================

    def _get_user_context(self, __user__: Optional[dict]) -> Dict[str, str]:
        """Safely extracts user context information."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return {
            "user_id": user_data.get("id", ""),
            "user_name": user_data.get("name", "User"),
            "user_language": user_data.get("language", "en-US"),
        }

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """Unified extraction of chat context information (chat_id, message_id)."""
        chat_id = ""
        message_id = ""

        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")

            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

    async def _emit_debug_log(self, __event_emitter__, title: str, data: dict):
        if self.valves.SHOW_DEBUG_LOG and __event_emitter__:
            try:
                # Flat log format as requested
                js_code = f"""
                    console.log("[Folder Memory] {title}", {json.dumps(data, ensure_ascii=False)});
                """
                await __event_emitter__({"type": "execute", "data": {"code": js_code}})
            except Exception as e:
                logger.error(f"Error emitting log: {e}")

    async def _emit_status(
        self, __event_emitter__, description: str, done: bool = False
    ):
        if __event_emitter__:
            await __event_emitter__(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    def _get_folder_id(self, body: dict) -> Optional[str]:
        # 1. Try retrieving folder_id specifically from metadata
        if "metadata" in body and isinstance(body["metadata"], dict):
            if "folder_id" in body["metadata"]:
                return body["metadata"]["folder_id"]

        # 2. Check regular body chat object if available
        if "chat" in body and isinstance(body["chat"], dict):
            if "folder_id" in body["chat"]:
                return body["chat"]["folder_id"]

        # 3. Try fallback via Chat ID (Most reliable)
        chat_id = body.get("chat_id")
        if not chat_id:
            if "metadata" in body and isinstance(body["metadata"], dict):
                chat_id = body["metadata"].get("chat_id")

        if chat_id:
            try:
                chat = Chats.get_chat_by_id(chat_id)
                if chat and chat.folder_id:
                    return chat.folder_id
            except Exception as e:
                logger.error(f"Failed to fetch chat {chat_id}: {e}")

        return None

    def _extract_existing_rules(self, system_prompt: str) -> str:
        pattern = re.compile(
            re.escape(RULES_BLOCK_START) + r"([\s\S]*?)" + re.escape(RULES_BLOCK_END)
        )
        match = pattern.search(system_prompt)
        if match:
            # Remove title if it's inside the block
            content = match.group(1).strip()
            # Simple cleanup of the title if user formatted it inside
            title_pat = re.compile(r"^#+\s+.*$", re.MULTILINE)
            return title_pat.sub("", content).strip()
        return ""

    def _inject_rules(self, system_prompt: str, new_rules: str, title: str) -> str:
        new_block_content = f"\n{title}\n\n{new_rules}\n"
        new_block = f"{RULES_BLOCK_START}{new_block_content}{RULES_BLOCK_END}"

        system_prompt = system_prompt or ""
        pattern = re.compile(
            re.escape(RULES_BLOCK_START) + r"[\s\S]*?" + re.escape(RULES_BLOCK_END)
        )

        if pattern.search(system_prompt):
            return pattern.sub(new_block, system_prompt).strip()
        else:
            # Append if not found
            if system_prompt:
                return f"{system_prompt}\n\n{new_block}"
            else:
                return new_block

    async def _generate_new_rules(
        self,
        current_rules: str,
        messages: List[Dict],
        user_id: str,
        __request__: Request,
    ) -> str:
        # Prepare context
        conversation_text = "\n".join(
            [
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in messages[-20:]  # Analyze last 20 messages context
            ]
        )

        prompt = f"""
Existing Rules:
{current_rules if current_rules else "None"}

Conversation Excerpt:
{conversation_text}

Please output the updated Project Rules:
"""

        payload = {
            "model": self.valves.MODEL_ID,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_RULE_GENERATOR},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        try:
            # We need a user object for permission checks in generate_chat_completion
            user = Users.get_user_by_id(user_id)
            if not user:
                return current_rules

            completion = await generate_chat_completion(__request__, payload, user)
            if "choices" in completion and len(completion["choices"]) > 0:
                content = completion["choices"][0]["message"]["content"].strip()
                # Basic validation: ensure it looks like a list
                if (
                    content.startswith("-")
                    or content.startswith("*")
                    or content.startswith("1.")
                ):
                    return content
        except Exception as e:
            logger.error(f"Rule generation failed: {e}")

        return current_rules

    async def _process_rules_update(
        self,
        folder_id: str,
        body: dict,
        user_id: str,
        __request__: Request,
        __event_emitter__,
    ):
        try:
            await self._emit_debug_log(
                __event_emitter__,
                "Start Processing",
                {"step": "start", "initial_folder_id": folder_id, "user_id": user_id},
            )

            # 1. Fetch Folder Data (ORM)
            initial_folder = Folders.get_folder_by_id_and_user_id(folder_id, user_id)
            if not initial_folder:
                await self._emit_debug_log(
                    __event_emitter__,
                    "Error: Initial folder not found",
                    {
                        "step": "fetch_initial_folder",
                        "initial_folder_id": folder_id,
                        "user_id": user_id,
                    },
                )
                return

            # Subfolder handling logic
            target_folder = initial_folder
            if self.valves.UPDATE_ROOT_FOLDER:
                # Traverse up until a folder with no parent_id is found
                while target_folder and getattr(target_folder, "parent_id", None):
                    try:
                        parent = Folders.get_folder_by_id_and_user_id(
                            target_folder.parent_id, user_id
                        )
                        if parent:
                            target_folder = parent
                        else:
                            break
                    except Exception as e:
                        await self._emit_debug_log(
                            __event_emitter__,
                            "Warning: Failed to traverse parent folder",
                            {"step": "traverse_root", "error": str(e)},
                        )
                        break

            target_folder_id = target_folder.id

            await self._emit_debug_log(
                __event_emitter__,
                "Target Folder Resolved",
                {
                    "step": "target_resolved",
                    "target_folder_id": target_folder_id,
                    "target_folder_name": target_folder.name,
                    "is_root_update": target_folder_id != folder_id,
                },
            )

            existing_data = target_folder.data if target_folder.data else {}
            existing_sys_prompt = existing_data.get("system_prompt", "")

            # 2. Extract Existing Rules
            current_rules_content = self._extract_existing_rules(existing_sys_prompt)

            # 3. Generate New Rules
            await self._emit_status(
                __event_emitter__, "Analyzing project rules...", done=False
            )

            messages = body.get("messages", [])
            new_rules_content = await self._generate_new_rules(
                current_rules_content, messages, user_id, __request__
            )

            rules_changed = new_rules_content != current_rules_content

            # 4. If no change, skip
            if not rules_changed:
                await self._emit_debug_log(
                    __event_emitter__,
                    "No Changes",
                    {
                        "step": "check_changes",
                        "reason": "content_identical_or_generation_failed",
                    },
                )
                await self._emit_status(
                    __event_emitter__,
                    "Rule analysis complete: No new content.",
                    done=True,
                )
                return

            # 5. Inject Rules into System Prompt
            updated_sys_prompt = existing_sys_prompt
            if rules_changed:
                updated_sys_prompt = self._inject_rules(
                    updated_sys_prompt,
                    new_rules_content,
                    self.valves.RULES_BLOCK_TITLE,
                )

            await self._emit_debug_log(
                __event_emitter__,
                "Ready to Update DB",
                {"step": "pre_db_update", "target_folder_id": target_folder_id},
            )

            # 6. Update Folder (ORM) - Only update 'data' field
            existing_data["system_prompt"] = updated_sys_prompt

            updated_folder = Folders.update_folder_by_id_and_user_id(
                target_folder_id,
                user_id,
                FolderUpdateForm(data=existing_data),
            )

            if not updated_folder:
                raise Exception("Update folder failed (ORM returned None)")

            await self._emit_status(
                __event_emitter__, "Rule analysis complete: Rules updated.", done=True
            )
            await self._emit_debug_log(
                __event_emitter__,
                "Rule Generation Process & Change Details",
                {
                    "step": "success",
                    "folder_id": target_folder_id,
                    "target_is_root": target_folder_id != folder_id,
                    "model_used": self.valves.MODEL_ID,
                    "analyzed_messages_count": len(messages),
                    "old_rules_length": len(current_rules_content),
                    "new_rules_length": len(new_rules_content),
                    "changes_digest": {
                        "old_rules_preview": (
                            current_rules_content[:100] + "..."
                            if current_rules_content
                            else "None"
                        ),
                        "new_rules_preview": (
                            new_rules_content[:100] + "..."
                            if new_rules_content
                            else "None"
                        ),
                    },
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Async rule processing error: {e}")
            await self._emit_status(
                __event_emitter__, "Failed to update rules.", done=True
            )
            # Emit error to console for debugging
            await self._emit_debug_log(
                __event_emitter__,
                "Execution Error",
                {"error": str(e), "folder_id": folder_id},
            )

    # ==================== Filter Hooks ====================

    async def inlet(
        self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None
    ) -> dict:
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __request__: Optional[Request] = None,
    ) -> dict:
        user_ctx = self._get_user_context(__user__)
        chat_ctx = self._get_chat_context(body)

        messages = body.get("messages", [])
        if not messages:
            return body

        # Trigger logic: Message Count threshold
        if len(messages) % self.valves.MESSAGE_TRIGGER_COUNT != 0:
            return body

        folder_id = self._get_folder_id(body)
        if not folder_id:
            await self._emit_debug_log(
                __event_emitter__,
                "Skipping Analysis",
                {
                    "reason": "Chat does not belong to any folder",
                    "chat_id": chat_ctx.get("chat_id"),
                },
            )
            return body

        # User Info
        user_id = user_ctx.get("user_id")
        if not user_id:
            return body

        # Async Task
        if self.valves.MODEL_ID == "":
            self.valves.MODEL_ID = body.get("model", "")

        asyncio.create_task(
            self._process_rules_update(
                folder_id, body, user_id, __request__, __event_emitter__
            )
        )

        return body
