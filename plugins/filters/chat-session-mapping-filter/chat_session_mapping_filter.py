"""
title: Chat Session Mapping Filter
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.0
description: Automatically tracks and persists the mapping between user IDs and chat IDs for session management.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Determine the chat mapping file location
if os.path.exists("/app/backend/data"):
    CHAT_MAPPING_FILE = Path(
        "/app/backend/data/copilot_workspace/api_key_chat_id_mapping.json"
    )
else:
    CHAT_MAPPING_FILE = Path(os.getcwd()) / "copilot_workspace" / "api_key_chat_id_mapping.json"


class Filter:
    class Valves(BaseModel):
        ENABLE_TRACKING: bool = Field(
            default=True,
            description="Enable chat session mapping tracking."
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        **kwargs,
    ) -> dict:
        """
        Inlet hook: Called before message processing.
        Persists the mapping of user_id to chat_id.
        """
        if not self.valves.ENABLE_TRACKING:
            return body

        user_id = self._get_user_id(__user__)
        chat_id = self._get_chat_id(body, __metadata__)

        if user_id and chat_id:
            self._persist_mapping(user_id, chat_id)

        return body

    def outlet(
        self,
        body: dict,
        response: str,
        __user__: Optional[dict] = None,
        __metadata__: Optional[dict] = None,
        **kwargs,
    ) -> str:
        """
        Outlet hook: No modification to response needed.
        This filter only tracks mapping on inlet.
        """
        return response

    def _get_user_id(self, __user__: Optional[dict]) -> Optional[str]:
        """Safely extract user ID from __user__ parameter."""
        if isinstance(__user__, (list, tuple)):
            user_data = __user__[0] if __user__ else {}
        elif isinstance(__user__, dict):
            user_data = __user__
        else:
            user_data = {}

        return str(user_data.get("id", "")).strip() or None

    def _get_chat_id(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Optional[str]:
        """Safely extract chat ID from body or metadata."""
        chat_id = ""

        # Try to extract from body
        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")

            # Fallback: Check body.metadata
            if not chat_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    chat_id = body_metadata.get("chat_id", "")

        # Fallback: Check __metadata__
        if not chat_id and __metadata__ and isinstance(__metadata__, dict):
            chat_id = __metadata__.get("chat_id", "")

        return str(chat_id).strip() or None

    def _persist_mapping(self, user_id: str, chat_id: str) -> None:
        """Persist the user_id to chat_id mapping to file."""
        try:
            # Create parent directory if needed
            CHAT_MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Load existing mapping
            mapping = {}
            if CHAT_MAPPING_FILE.exists():
                try:
                    loaded = json.loads(
                        CHAT_MAPPING_FILE.read_text(encoding="utf-8")
                    )
                    if isinstance(loaded, dict):
                        mapping = {str(k): str(v) for k, v in loaded.items()}
                except Exception as e:
                    logger.warning(
                        f"Failed to read mapping file {CHAT_MAPPING_FILE}: {e}"
                    )

            # Update mapping with current user_id and chat_id
            mapping[user_id] = chat_id

            # Write to temporary file and atomically replace
            temp_file = CHAT_MAPPING_FILE.with_suffix(
                CHAT_MAPPING_FILE.suffix + ".tmp"
            )
            temp_file.write_text(
                json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            temp_file.replace(CHAT_MAPPING_FILE)

            logger.info(
                f"Persisted mapping: user_id={user_id} -> chat_id={chat_id}"
            )

        except Exception as e:
            logger.warning(f"Failed to persist chat session mapping: {e}")
