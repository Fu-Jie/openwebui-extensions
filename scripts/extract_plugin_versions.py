#!/usr/bin/env python3
"""
Script to extract plugin version information from Python files.
用于从 Python 插件文件中提取版本信息的脚本。

This script scans the plugins directory and extracts metadata (title, version, author, description)
from Python files that follow the OpenWebUI plugin docstring format.

Usage:
    python extract_plugin_versions.py                    # Output to console
    python extract_plugin_versions.py --json             # Output as JSON
    python extract_plugin_versions.py --markdown         # Output as Markdown table
    python extract_plugin_versions.py --compare old.json # Compare with previous version file
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def extract_plugin_metadata(file_path: str) -> dict[str, Any] | None:
    """
    Extract plugin metadata from a Python file's docstring.
    从 Python 文件的文档字符串中提取插件元数据。

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary containing plugin metadata or None if not a valid plugin file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None

    # Match the docstring at the beginning of the file (allowing leading whitespace/comments)
    docstring_pattern = r'^\s*"""(.*?)"""'
    match = re.search(docstring_pattern, content, re.DOTALL)

    if not match:
        return None

    docstring = match.group(1)

    # Extract metadata fields
    metadata = {}
    field_patterns = {
        "title": r"title:\s*(.+?)(?:\n|$)",
        "author": r"author:\s*(.+?)(?:\n|$)",
        "author_url": r"author_url:\s*(.+?)(?:\n|$)",
        "funding_url": r"funding_url:\s*(.+?)(?:\n|$)",
        "version": r"version:\s*(.+?)(?:\n|$)",
        "description": r"description:\s*(.+?)(?:\n|$)",
        "requirements": r"requirements:\s*(.+?)(?:\n|$)",
    }

    for field, pattern in field_patterns.items():
        field_match = re.search(pattern, docstring, re.IGNORECASE)
        if field_match:
            metadata[field] = field_match.group(1).strip()

    # Only return if we found at least title and version
    if "title" in metadata and "version" in metadata:
        metadata["file_path"] = file_path
        return metadata

    return None


def scan_plugins_directory(plugins_dir: str) -> list[dict[str, Any]]:
    """
    Scan the plugins directory and extract metadata from all plugin files.
    扫描 plugins 目录并从所有插件文件中提取元数据。

    Args:
        plugins_dir: Path to the plugins directory

    Returns:
        List of plugin metadata dictionaries
    """
    plugins = []
    plugins_path = Path(plugins_dir)

    if not plugins_path.exists():
        print(f"Plugins directory not found: {plugins_dir}", file=sys.stderr)
        return plugins

    # Walk through all subdirectories
    for root, _dirs, files in os.walk(plugins_path):
        for file in files:
            # Skip template files and Python internal files
            if file.endswith(".py") and not file.startswith("__") and "TEMPLATE" not in file.upper():
                file_path = os.path.join(root, file)
                metadata = extract_plugin_metadata(file_path)
                if metadata:
                    # Determine plugin type from directory structure
                    rel_path = os.path.relpath(file_path, plugins_dir)
                    parts = rel_path.split(os.sep)
                    if len(parts) > 0:
                        metadata["type"] = parts[0]  # actions, filters, pipes, etc.
                    plugins.append(metadata)

    return plugins


def compare_versions(
    current: list[dict], previous_file: str
) -> dict[str, list[dict]]:
    """
    Compare current plugin versions with a previous version file.
    比较当前插件版本与之前的版本文件。

    Args:
        current: List of current plugin metadata
        previous_file: Path to JSON file with previous versions

    Returns:
        Dictionary with 'added', 'updated', 'removed' lists
    """
    try:
        with open(previous_file, "r", encoding="utf-8") as f:
            previous = json.load(f)
    except FileNotFoundError:
        return {"added": current, "updated": [], "removed": []}
    except json.JSONDecodeError:
        print(f"Error parsing {previous_file}", file=sys.stderr)
        return {"added": current, "updated": [], "removed": []}

    # Create lookup dictionaries by title
    current_by_title = {p["title"]: p for p in current}
    previous_by_title = {p["title"]: p for p in previous}

    result = {"added": [], "updated": [], "removed": []}

    # Find added and updated plugins
    for title, plugin in current_by_title.items():
        if title not in previous_by_title:
            result["added"].append(plugin)
        elif plugin["version"] != previous_by_title[title]["version"]:
            result["updated"].append(
                {
                    "current": plugin,
                    "previous": previous_by_title[title],
                }
            )

    # Find removed plugins
    for title, plugin in previous_by_title.items():
        if title not in current_by_title:
            result["removed"].append(plugin)

    return result


def format_markdown_table(plugins: list[dict]) -> str:
    """
    Format plugins as a Markdown table.
    将插件格式化为 Markdown 表格。
    """
    lines = [
        "| Plugin / 插件 | Version / 版本 | Type / 类型 | Description / 描述 |",
        "|---------------|----------------|-------------|---------------------|",
    ]

    for plugin in sorted(plugins, key=lambda x: (x.get("type", ""), x.get("title", ""))):
        title = plugin.get("title", "Unknown")
        version = plugin.get("version", "Unknown")
        plugin_type = plugin.get("type", "Unknown").capitalize()
        full_description = plugin.get("description", "")
        description = full_description[:50]
        if len(full_description) > 50:
            description += "..."
        lines.append(f"| {title} | {version} | {plugin_type} | {description} |")

    return "\n".join(lines)


def format_changed_plugins_table(comparison: dict[str, list]) -> str:
    """
    Format only changed plugins (added and updated) as a Markdown table.
    仅将变更的插件（新增和更新）格式化为 Markdown 表格。
    """
    if not comparison["added"] and not comparison["updated"]:
        return ""
    
    lines = [
        "| Plugin / 插件 | Version / 版本 | Type / 类型 | Description / 描述 |",
        "|---------------|----------------|-------------|---------------------|",
    ]
    
    # Collect all changed plugins
    changed_plugins = []
    
    # Add new plugins
    for plugin in comparison["added"]:
        changed_plugins.append({
            "title": plugin.get("title", "Unknown"),
            "version": plugin.get("version", "Unknown") + " 🆕",
            "type": plugin.get("type", "Unknown").capitalize(),
            "description": plugin.get("description", "")
        })
    
    # Add updated plugins
    for update in comparison["updated"]:
        curr = update["current"]
        prev = update["previous"]
        changed_plugins.append({
            "title": curr.get("title", "Unknown"),
            "version": f"{prev.get('version', '?')} → {curr.get('version', '?')}",
            "type": curr.get("type", "Unknown").capitalize(),
            "description": curr.get("description", "")
        })
    
    # Sort and format
    for plugin in sorted(changed_plugins, key=lambda x: (x["type"], x["title"])):
        title = plugin["title"]
        version = plugin["version"]
        plugin_type = plugin["type"]
        full_description = plugin["description"]
        description = full_description[:50]
        if len(full_description) > 50:
            description += "..."
        lines.append(f"| {title} | {version} | {plugin_type} | {description} |")
    
    return "\n".join(lines)


def format_release_notes(comparison: dict[str, list]) -> str:
    """
    Format version comparison as release notes.
    将版本比较格式化为发布说明。
    """
    lines = []

    if comparison["added"]:
        lines.append("### 新增插件 / New Plugins")
        for plugin in comparison["added"]:
            lines.append(f"- **{plugin['title']}** v{plugin['version']}")
            if plugin.get("description"):
                lines.append(f"  - {plugin['description']}")
        lines.append("")

    if comparison["updated"]:
        lines.append("### 插件更新 / Plugin Updates")
        for update in comparison["updated"]:
            curr = update["current"]
            prev = update["previous"]
            lines.append(
                f"- **{curr['title']}**: v{prev['version']} → v{curr['version']}"
            )
        lines.append("")

    if comparison["removed"]:
        lines.append("### 移除插件 / Removed Plugins")
        for plugin in comparison["removed"]:
            lines.append(f"- **{plugin['title']}** v{plugin['version']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract and compare plugin version information"
    )
    parser.add_argument(
        "--plugins-dir",
        default="plugins",
        help="Path to plugins directory (default: plugins)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output as Markdown table",
    )
    parser.add_argument(
        "--changed-table",
        action="store_true",
        help="Output changed plugins as Markdown table (use with --compare)",
    )
    parser.add_argument(
        "--compare",
        metavar="FILE",
        help="Compare with previous version JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Write output to file instead of stdout",
    )

    args = parser.parse_args()

    # Scan plugins
    plugins = scan_plugins_directory(args.plugins_dir)

    # Generate output
    if args.compare:
        comparison = compare_versions(plugins, args.compare)
        if args.json:
            output = json.dumps(comparison, indent=2, ensure_ascii=False)
        elif args.changed_table:
            # Output a markdown table of only changed plugins
            output = format_changed_plugins_table(comparison)
            if not output.strip():
                output = "No changes detected. / 未检测到更改。"
        else:
            output = format_release_notes(comparison)
            if not output.strip():
                output = "No changes detected. / 未检测到更改。"
    elif args.json:
        output = json.dumps(plugins, indent=2, ensure_ascii=False)
    elif args.markdown:
        output = format_markdown_table(plugins)
    else:
        # Default: simple list
        lines = []
        for plugin in sorted(plugins, key=lambda x: x.get("title", "")):
            lines.append(f"{plugin.get('title', 'Unknown')}: v{plugin.get('version', '?')}")
        output = "\n".join(lines)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
