#!/usr/bin/env python3
"""
Deploy Filter plugins to OpenWebUI instance.

This script deploys filter plugins (like async_context_compression) to a running
OpenWebUI instance. It reads the plugin metadata and submits it to the local API.

Usage:
    python deploy_filter.py                      # Deploy async_context_compression
    python deploy_filter.py <filter_name>        # Deploy specific filter
"""

import requests
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# ─── Configuration ───────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"
FILTERS_DIR = SCRIPT_DIR.parent / "plugins/filters"

# Default target filter
DEFAULT_FILTER = "async-context-compression"


def _load_api_key() -> str:
    """Load API key from .env file in the same directory as this script.

    The .env file should contain a line like:
        api_key=sk-xxxxxxxxxxxx
    """
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env file not found at {ENV_FILE}. "
            "Please create it with: api_key=sk-xxxxxxxxxxxx"
        )

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("api_key="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key

    raise ValueError("api_key not found in .env file.")


def _load_openwebui_base_url() -> str:
    """Load OpenWebUI base URL from .env file or environment.

    Checks in order:
    1. OPENWEBUI_BASE_URL in .env
    2. OPENWEBUI_BASE_URL environment variable
    3. Default to http://localhost:3000
    """
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENWEBUI_BASE_URL="):
                url = line.split("=", 1)[1].strip()
                if url:
                    return url

    # Try environment variable
    url = os.environ.get("OPENWEBUI_BASE_URL")
    if url:
        return url

    # Default
    return "http://localhost:3000"


def _find_filter_file(filter_name: str) -> Optional[Path]:
    """Find the main Python file for a filter.

    Args:
        filter_name: Directory name of the filter (e.g., 'async-context-compression')

    Returns:
        Path to the main Python file, or None if not found.
    """
    filter_dir = FILTERS_DIR / filter_name
    if not filter_dir.exists():
        return None

    # Try to find a .py file matching the filter name
    py_files = list(filter_dir.glob("*.py"))

    # Prefer a file with the filter name (with hyphens converted to underscores)
    preferred_name = filter_name.replace("-", "_") + ".py"
    for py_file in py_files:
        if py_file.name == preferred_name:
            return py_file

    # Otherwise, return the first .py file (usually the only one)
    if py_files:
        return py_files[0]

    return None


def _extract_metadata(content: str) -> Dict[str, Any]:
    """Extract metadata from the plugin docstring.

    Args:
        content: Python file content

    Returns:
        Dictionary with extracted metadata (title, author, version, etc.)
    """
    metadata = {}

    # Extract docstring
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if not match:
        return metadata

    docstring = match.group(1)

    # Extract key-value pairs
    for line in docstring.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#") and not line.startswith("═"):
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            value = parts[1].strip()
            metadata[key] = value

    return metadata


def _build_filter_payload(
    filter_name: str, file_path: Path, content: str, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the payload for the filter update/create API.

    Args:
        filter_name: Directory name of the filter
        file_path: Path to the plugin file
        content: File content
        metadata: Extracted metadata

    Returns:
        Payload dictionary ready for API submission
    """
    # Generate a unique ID from filter name
    filter_id = metadata.get("id", filter_name).replace("-", "_")
    title = metadata.get("title", filter_name)
    author = metadata.get("author", "Fu-Jie")
    author_url = metadata.get(
        "author_url", "https://github.com/Fu-Jie/openwebui-extensions"
    )
    funding_url = metadata.get("funding_url", "https://github.com/open-webui")
    description = metadata.get("description", f"Filter plugin: {title}")
    version = metadata.get("version", "1.0.0")
    openwebui_id = metadata.get("openwebui_id", "")

    payload = {
        "id": filter_id,
        "name": title,
        "meta": {
            "description": description,
            "manifest": {
                "title": title,
                "author": author,
                "author_url": author_url,
                "funding_url": funding_url,
                "description": description,
                "version": version,
                "type": "filter",
            },
            "type": "filter",
        },
        "content": content,
    }

    # Add openwebui_id if available
    if openwebui_id:
        payload["meta"]["manifest"]["openwebui_id"] = openwebui_id

    return payload


def deploy_filter(filter_name: str = DEFAULT_FILTER) -> bool:
    """Deploy a filter plugin to OpenWebUI.

    Args:
        filter_name: Directory name of the filter to deploy

    Returns:
        True if successful, False otherwise
    """
    # 1. Load API key
    try:
        api_key = _load_api_key()
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERROR] {e}")
        return False

    # 2. Find filter file
    file_path = _find_filter_file(filter_name)
    if not file_path:
        print(f"[ERROR] Filter '{filter_name}' not found in {FILTERS_DIR}")
        print(f"[INFO] Available filters:")
        for d in FILTERS_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                print(f"       - {d.name}")
        return False

    # 3. Read local source file
    if not file_path.exists():
        print(f"[ERROR] Source file not found: {file_path}")
        return False

    content = file_path.read_text(encoding="utf-8")
    metadata = _extract_metadata(content)

    if not metadata:
        print(f"[ERROR] Could not extract metadata from {file_path}")
        return False

    version = metadata.get("version", "1.0.0")
    title = metadata.get("title", filter_name)
    filter_id = metadata.get("id", filter_name).replace("-", "_")

    # 4. Build payload
    payload = _build_filter_payload(filter_name, file_path, content, metadata)

    # 5. Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # 6. Send update request
    base_url = _load_openwebui_base_url()
    update_url = "{}/api/v1/functions/id/{}/update".format(base_url, filter_id)
    create_url = "{}/api/v1/functions/create".format(base_url)

    print(f"📦 Deploying filter '{title}' (version {version})...")
    print(f"   File: {file_path}")
    print(f"   Target: {base_url}")

    try:
        # Try update first
        response = requests.post(
            update_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )

        if response.status_code == 200:
            print(f"✅ Successfully updated '{title}' filter!")
            return True
        else:
            print(
                f"⚠️  Update failed with status {response.status_code}, "
                "attempting to create instead..."
            )

            # Try create if update fails
            res_create = requests.post(
                create_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10,
            )

            if res_create.status_code == 200:
                print(f"✅ Successfully created '{title}' filter!")
                return True
            else:
                print(
                    f"❌ Failed to update or create. Status: {res_create.status_code}"
                )
                try:
                    error_msg = res_create.json()
                    print(f"   Error: {error_msg}")
                except:
                    print(f"   Response: {res_create.text[:500]}")
                return False

    except requests.exceptions.ConnectionError:
        base_url = _load_openwebui_base_url()
        print(f"❌ Connection error: Could not reach OpenWebUI at {base_url}")
        print("   Make sure OpenWebUI is running and accessible.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout: OpenWebUI took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def list_filters() -> None:
    """List all available filters."""
    print("📋 Available filters:")
    filters = [
        d.name
        for d in FILTERS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    if not filters:
        print("   (No filters found)")
        return

    for filter_name in sorted(filters):
        filter_dir = FILTERS_DIR / filter_name
        py_file = _find_filter_file(filter_name)

        if py_file:
            content = py_file.read_text(encoding="utf-8")
            metadata = _extract_metadata(content)
            title = metadata.get("title", filter_name)
            version = metadata.get("version", "?")
            print(f"   - {filter_name:<30} {title:<40} v{version}")
        else:
            print(f"   - {filter_name:<30} (no Python file found)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list" or sys.argv[1] == "-l":
            list_filters()
        else:
            filter_name = sys.argv[1]
            success = deploy_filter(filter_name)
            sys.exit(0 if success else 1)
    else:
        # Deploy default filter
        success = deploy_filter()
        sys.exit(0 if success else 1)
