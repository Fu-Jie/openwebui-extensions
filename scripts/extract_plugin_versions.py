"""
Script to extract plugin version information from Python files.


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
    for root, dirs, files in os.walk(plugins_path):
        # Exclude debug directory from scan
        if "debug" in dirs:
            dirs.remove("debug")

        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                # Skip specific files that should not trigger release
                if file in [
                    "gemini_manifold.py",
                    "gemini_manifold_companion.py",
                    "ACTION_PLUGIN_TEMPLATE.py",
                    "ACTION_PLUGIN_TEMPLATE_CN.py",
                ]:
                    continue

                file_path = os.path.join(root, file)
                metadata = extract_plugin_metadata(file_path)
                if metadata:
                    # Determine plugin type from directory structure
                    rel_path = os.path.relpath(file_path, plugins_dir)

                    # Normalize file_path to always start with "plugins/" for consistent ID comparison
                    # regardless of where we scan from (/tmp/old_repo or ./plugins)
                    metadata["file_path"] = os.path.join("plugins", rel_path)

                    parts = rel_path.split(os.sep)
                    if len(parts) > 0:
                        metadata["type"] = parts[0]  # actions, filters, pipes, etc.
                    plugins.append(metadata)

    return plugins


def compare_versions(current: list[dict], previous_file: str) -> dict[str, list[dict]]:
    """
    Compare current plugin versions with a previous version file.


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

    # Create lookup dictionaries by file_path (fallback to title)
    # Helper to extract title/version/file_path from either simple dict or raw post object
    def get_info(p):
        if "data" in p and "function" in p["data"]:
            # It's a raw post object
            manifest = p["data"]["function"].get("meta", {}).get("manifest", {})
            title = manifest.get("title") or p.get("title")
            version = manifest.get("version", "0.0.0")
            file_path = p.get("file_path")
            return title, version, file_path, p
        else:
            # It's a simple dict
            return p.get("title"), p.get("version"), p.get("file_path"), p

    current_by_key = {}
    for p in current:
        title, _, file_path, _ = get_info(p)
        key = file_path or title
        if key:
            current_by_key[key] = p

    previous_by_key = {}
    for p in previous:
        title, _, file_path, _ = get_info(p)
        key = file_path or title
        if key:
            previous_by_key[key] = p

    result = {"added": [], "updated": [], "removed": []}

    # Find added and updated plugins
    for key, plugin in current_by_key.items():
        curr_title, curr_ver, _file_path, _ = get_info(plugin)

        if key not in previous_by_key:
            result["added"].append(plugin)
        else:
            prev_plugin = previous_by_key[key]
            _, prev_ver, _prev_file_path, _ = get_info(prev_plugin)

            if curr_ver != prev_ver:
                result["updated"].append(
                    {
                        "current": plugin,
                        "previous": prev_plugin,
                    }
                )

    # Find removed plugins
    for key, plugin in previous_by_key.items():
        if key not in current_by_key:
            result["removed"].append(plugin)

    return result


def format_markdown_table(plugins: list[dict]) -> str:
    """
    Format plugins as a Markdown table.
    """
    lines = [
        "| Plugin | Version | Type | Description |",
        "|---------------|----------------|-------------|---------------------|",
    ]

    for plugin in sorted(
        plugins, key=lambda x: (x.get("type", ""), x.get("title", ""))
    ):
        title = plugin.get("title", "Unknown")
        version = plugin.get("version", "Unknown")
        plugin_type = plugin.get("type", "Unknown").capitalize()
        full_description = plugin.get("description", "")
        description = full_description[:50]
        if len(full_description) > 50:
            description += "..."
        lines.append(f"| {title} | {version} | {plugin_type} | {description} |")

    return "\n".join(lines)


def _get_readme_url(file_path: str) -> str:
    """
    Generate GitHub README URL from plugin file path.
    """
    if not file_path:
        return ""
    # Extract plugin directory (e.g., plugins/filters/folder-memory/folder_memory.py -> plugins/filters/folder-memory)
    from pathlib import Path

    plugin_dir = Path(file_path).parent
    # Convert to GitHub URL
    return f"https://github.com/Fu-Jie/openwebui-extensions/blob/main/{plugin_dir}/README.md"


def format_release_notes(
    comparison: dict[str, list], ignore_removed: bool = False
) -> str:
    """
    Format version comparison as release notes.
    """
    lines = []

    if comparison["added"]:
        lines.append("### New Plugins")
        for plugin in comparison["added"]:
            readme_url = _get_readme_url(plugin.get("file_path", ""))
            lines.append(f"- **{plugin['title']}** v{plugin['version']}")
            if plugin.get("description"):
                lines.append(f"  - {plugin['description']}")
            if readme_url:
                lines.append(f"  - 📖 [README]({readme_url})")
        lines.append("")

    if comparison["updated"]:
        lines.append("### Plugin Updates")
        for update in comparison["updated"]:
            curr = update["current"]
            prev = update["previous"]

            # Extract info safely
            curr_manifest = (
                curr.get("data", {})
                .get("function", {})
                .get("meta", {})
                .get("manifest", {})
            )
            curr_title = curr_manifest.get("title") or curr.get("title")
            curr_ver = curr_manifest.get("version") or curr.get("version")

            prev_manifest = (
                prev.get("data", {})
                .get("function", {})
                .get("meta", {})
                .get("manifest", {})
            )
            prev_ver = prev_manifest.get("version") or prev.get("version")

            readme_url = _get_readme_url(curr.get("file_path", ""))
            lines.append(f"- **{curr_title}**: v{prev_ver} → v{curr_ver}")
            if readme_url:
                lines.append(f"  - 📖 [README]({readme_url})")
        lines.append("")

    if comparison["removed"] and not ignore_removed:
        lines.append("### Removed Plugins")
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
        "--compare",
        metavar="FILE",
        help="Compare with previous version JSON file",
    )
    parser.add_argument(
        "--ignore-removed",
        action="store_true",
        help="Ignore removed plugins in output",
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
        else:
            output = format_release_notes(
                comparison, ignore_removed=args.ignore_removed
            )
            if not output.strip():
                output = "No changes detected."
    elif args.json:
        output = json.dumps(plugins, indent=2, ensure_ascii=False)
    elif args.markdown:
        output = format_markdown_table(plugins)
    else:
        # Default: simple list
        lines = []
        for plugin in sorted(plugins, key=lambda x: x.get("title", "")):
            lines.append(
                f"{plugin.get('title', 'Unknown')}: v{plugin.get('version', '?')}"
            )
        output = "\n".join(lines)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
            if not output.endswith("\n"):
                f.write("\n")
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
