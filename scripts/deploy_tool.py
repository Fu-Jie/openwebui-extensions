#!/usr/bin/env python3
"""
Deploy Tools plugins to OpenWebUI instance.

This script deploys tool plugins to a running OpenWebUI instance.
It reads the plugin metadata and submits it to the local API.

Usage:
    python deploy_tool.py                       # Deploy OpenWebUI Skills Manager Tool
    python deploy_tool.py <tool_name>           # Deploy specific tool
    python deploy_tool.py --list                # List available tools
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
TOOLS_DIR = SCRIPT_DIR.parent / "plugins/tools"

# Default target tool
DEFAULT_TOOL = "openwebui-skills-manager"


def _load_api_key() -> str:
    """Load API key from .env file in the same directory as this script."""
    env_values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip().lower()] = value.strip().strip('"').strip("'")

    api_key = (
        os.getenv("OPENWEBUI_API_KEY")
        or os.getenv("api_key")
        or env_values.get("api_key")
        or env_values.get("openwebui_api_key")
    )

    if not api_key:
        raise ValueError(
            f"Missing api_key. Please create {ENV_FILE} with: "
            "api_key=sk-xxxxxxxxxxxx"
        )
    return api_key


def _get_base_url() -> str:
    """Load base URL from .env file or environment."""
    env_values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_values[key.strip().lower()] = value.strip().strip('"').strip("'")

    base_url = (
        os.getenv("OPENWEBUI_URL")
        or os.getenv("OPENWEBUI_BASE_URL")
        or os.getenv("url")
        or env_values.get("url")
        or env_values.get("openwebui_url")
        or env_values.get("openwebui_base_url")
    )

    if not base_url:
        raise ValueError(
            f"Missing url. Please create {ENV_FILE} with: "
            "url=http://localhost:3000"
        )
    return base_url.rstrip("/")


def _find_tool_file(tool_name: str) -> Optional[Path]:
    """Find the main Python file for a tool.
    
    Args:
        tool_name: Directory name of the tool (e.g., 'openwebui-skills-manager')
    
    Returns:
        Path to the main Python file, or None if not found.
    """
    tool_dir = TOOLS_DIR / tool_name
    if not tool_dir.exists():
        return None
    
    # Try to find a .py file matching the tool name
    py_files = list(tool_dir.glob("*.py"))
    
    # Prefer a file with the tool name (with hyphens converted to underscores)
    preferred_name = tool_name.replace("-", "_") + ".py"
    for py_file in py_files:
        if py_file.name == preferred_name:
            return py_file
    
    # Otherwise, return the first .py file (usually the only one)
    if py_files:
        return py_files[0]
    
    return None


def _extract_metadata(content: str) -> Dict[str, Any]:
    """Extract metadata from the plugin docstring."""
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


def _build_tool_payload(
    tool_name: str, file_path: Path, content: str, metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the payload for the tool update/create API."""
    tool_id = metadata.get("id", tool_name).replace("-", "_")
    title = metadata.get("title", tool_name)
    author = metadata.get("author", "Fu-Jie")
    author_url = metadata.get("author_url", "https://github.com/Fu-Jie/openwebui-extensions")
    funding_url = metadata.get("funding_url", "https://github.com/open-webui")
    description = metadata.get("description", f"Tool plugin: {title}")
    version = metadata.get("version", "1.0.0")
    openwebui_id = metadata.get("openwebui_id", "")
    
    payload = {
        "id": tool_id,
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
                "type": "tool",
            },
            "type": "tool",
        },
        "content": content,
    }
    
    # Add openwebui_id if available
    if openwebui_id:
        payload["meta"]["manifest"]["openwebui_id"] = openwebui_id
    
    return payload


def deploy_tool(tool_name: str = DEFAULT_TOOL) -> bool:
    """Deploy a tool plugin to OpenWebUI.
    
    Args:
        tool_name: Directory name of the tool to deploy
    
    Returns:
        True if successful, False otherwise
    """
    # 1. Load API key and base URL
    try:
        api_key = _load_api_key()
        base_url = _get_base_url()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return False

    # 2. Find tool file
    file_path = _find_tool_file(tool_name)
    if not file_path:
        print(f"[ERROR] Tool '{tool_name}' not found in {TOOLS_DIR}")
        print(f"[INFO] Available tools:")
        for d in TOOLS_DIR.iterdir():
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
    title = metadata.get("title", tool_name)
    tool_id = metadata.get("id", tool_name).replace("-", "_")

    # 4. Build payload
    payload = _build_tool_payload(tool_name, file_path, content, metadata)

    # 5. Build headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # 6. Send update request through the native tool endpoints
    update_url = f"{base_url}/api/v1/tools/id/{tool_id}/update"
    create_url = f"{base_url}/api/v1/tools/create"
    
    print(f"📦 Deploying tool '{title}' (version {version})...")
    print(f"   File: {file_path}")
    
    try:
        # Try update first
        response = requests.post(
            update_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully updated '{title}' tool!")
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
                print(f"✅ Successfully created '{title}' tool!")
                return True
            else:
                print(f"❌ Failed to update or create. Status: {res_create.status_code}")
                try:
                    error_msg = res_create.json()
                    print(f"   Error: {error_msg}")
                except:
                    print(f"   Response: {res_create.text[:500]}")
                return False
                
    except requests.exceptions.ConnectionError:
        print(
            "❌ Connection error: Could not reach OpenWebUI at {base_url}"
        )
        print("   Make sure OpenWebUI is running and accessible.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout: OpenWebUI took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False


def list_tools() -> None:
    """List all available tools."""
    print("📋 Available tools:")
    tools = [d.name for d in TOOLS_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")]
    
    if not tools:
        print("   (No tools found)")
        return
    
    for tool_name in sorted(tools):
        tool_dir = TOOLS_DIR / tool_name
        py_file = _find_tool_file(tool_name)
        
        if py_file:
            content = py_file.read_text(encoding="utf-8")
            metadata = _extract_metadata(content)
            title = metadata.get("title", tool_name)
            version = metadata.get("version", "?")
            print(f"   - {tool_name:<30} {title:<40} v{version}")
        else:
            print(f"   - {tool_name:<30} (no Python file found)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list" or sys.argv[1] == "-l":
            list_tools()
        else:
            tool_name = sys.argv[1]
            success = deploy_tool(tool_name)
            sys.exit(0 if success else 1)
    else:
        # Deploy default tool
        success = deploy_tool()
        sys.exit(0 if success else 1)
