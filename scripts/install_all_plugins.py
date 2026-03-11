#!/usr/bin/env python3
"""
Bulk install OpenWebUI plugins from this repository.

This script installs plugins from the local repository into a target OpenWebUI
instance. It only installs plugins that:
- live under plugins/actions, plugins/filters, plugins/pipes, or plugins/tools
- contain an `openwebui_id` in the plugin header docstring
- do not use a Chinese filename
- do not use a `_cn.py` localized filename suffix

Supported Plugin Types:
- Action (standard Function class)
- Filter (standard Function class)
- Pipe (standard Function class)
- Tool (native Tools class via /api/v1/tools endpoints)

Configuration:
Create `scripts/.env` with:
    api_key=sk-your-api-key
    url=http://localhost:3000

Usage:
    python scripts/install_all_plugins.py
    python scripts/install_all_plugins.py --list
    python scripts/install_all_plugins.py --dry-run
    python scripts/install_all_plugins.py --types pipe action filter tool
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ENV_FILE = SCRIPT_DIR / ".env"
DEFAULT_TIMEOUT = 20
DEFAULT_TYPES = ("pipe", "action", "filter", "tool")
SKIP_PREFIXES = ("test_", "verify_")
DOCSTRING_PATTERN = re.compile(r'^\s*"""\n(.*?)\n"""', re.DOTALL)

PLUGIN_TYPE_DIRS = {
    "action": REPO_ROOT / "plugins" / "actions",
    "filter": REPO_ROOT / "plugins" / "filters",
    "pipe": REPO_ROOT / "plugins" / "pipes",
    "tool": REPO_ROOT / "plugins" / "tools",
}


@dataclass(frozen=True)
class PluginCandidate:
    plugin_type: str
    file_path: Path
    metadata: Dict[str, str]
    content: str
    function_id: str

    @property
    def title(self) -> str:
        return self.metadata.get("title", self.file_path.stem)

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")


def _load_env_file(env_path: Path = ENV_FILE) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key_lower = key.strip().lower()
        values[key_lower] = value.strip().strip('"').strip("'")
    return values


def load_config(env_path: Path = ENV_FILE) -> Tuple[str, str]:
    env_values = _load_env_file(env_path)

    api_key = (
        os.getenv("OPENWEBUI_API_KEY")
        or os.getenv("api_key")
        or env_values.get("api_key")
        or env_values.get("openwebui_api_key")
    )
    base_url = (
        os.getenv("OPENWEBUI_URL")
        or os.getenv("OPENWEBUI_BASE_URL")
        or os.getenv("url")
        or env_values.get("url")
        or env_values.get("openwebui_url")
        or env_values.get("openwebui_base_url")
    )

    missing = []
    if not api_key:
        missing.append("api_key")
    if not base_url:
        missing.append("url")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            f"Missing required config: {joined}. "
            f"Please set them in environment variables or {env_path}."
        )

    return api_key, normalize_base_url(base_url)


def normalize_base_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValueError("URL cannot be empty.")
    return normalized.rstrip("/")


def extract_metadata(content: str) -> Dict[str, str]:
    match = DOCSTRING_PATTERN.search(content)
    if not match:
        return {}

    metadata: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata


def contains_non_ascii_filename(file_path: Path) -> bool:
    try:
        file_path.stem.encode("ascii")
        return False
    except UnicodeEncodeError:
        return True


def should_skip_plugin_file(file_path: Path) -> Optional[str]:
    stem = file_path.stem.lower()

    if contains_non_ascii_filename(file_path):
        return "non-ascii filename"
    if stem.endswith("_cn"):
        return "localized _cn file"
    if stem.startswith(SKIP_PREFIXES):
        return "test or helper script"
    return None


def slugify_function_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug or "plugin"


def build_function_id(file_path: Path, metadata: Dict[str, str]) -> str:
    if metadata.get("id"):
        return slugify_function_id(metadata["id"])
    if metadata.get("title"):
        return slugify_function_id(metadata["title"])
    return slugify_function_id(file_path.stem)


def has_tools_class(content: str) -> bool:
    """Check if plugin content defines a Tools class instead of Function class."""
    return "\nclass Tools:" in content or "\nclass Tools (" in content


def build_payload(candidate: PluginCandidate) -> Dict[str, object]:
    manifest = dict(candidate.metadata)
    manifest.setdefault("title", candidate.title)
    manifest.setdefault("author", "Fu-Jie")
    manifest.setdefault("author_url", "https://github.com/Fu-Jie/openwebui-extensions")
    manifest.setdefault("funding_url", "https://github.com/open-webui")
    manifest.setdefault(
        "description", f"{candidate.plugin_type.title()} plugin: {candidate.title}"
    )
    manifest.setdefault("version", "1.0.0")
    manifest["type"] = candidate.plugin_type

    if candidate.plugin_type == "tool":
        return {
            "id": candidate.function_id,
            "name": manifest["title"],
            "meta": {
                "description": manifest["description"],
                "manifest": {},
            },
            "content": candidate.content,
            "access_grants": [],
        }

    return {
        "id": candidate.function_id,
        "name": manifest["title"],
        "meta": {
            "description": manifest["description"],
            "manifest": manifest,
            "type": candidate.plugin_type,
        },
        "content": candidate.content,
    }


def build_api_urls(base_url: str, candidate: PluginCandidate) -> Tuple[str, str]:
    if candidate.plugin_type == "tool":
        return (
            f"{base_url}/api/v1/tools/id/{candidate.function_id}/update",
            f"{base_url}/api/v1/tools/create",
        )
    return (
        f"{base_url}/api/v1/functions/id/{candidate.function_id}/update",
        f"{base_url}/api/v1/functions/create",
    )


def discover_plugins(
    plugin_types: Sequence[str],
) -> Tuple[List[PluginCandidate], List[Tuple[Path, str]]]:
    candidates: List[PluginCandidate] = []
    skipped: List[Tuple[Path, str]] = []

    for plugin_type in plugin_types:
        plugin_dir = PLUGIN_TYPE_DIRS[plugin_type]
        if not plugin_dir.exists():
            continue

        for file_path in sorted(plugin_dir.rglob("*.py")):
            skip_reason = should_skip_plugin_file(file_path)
            if skip_reason:
                skipped.append((file_path, skip_reason))
                continue

            content = file_path.read_text(encoding="utf-8")
            metadata = extract_metadata(content)
            if not metadata:
                skipped.append((file_path, "missing plugin header"))
                continue
            if not metadata.get("openwebui_id"):
                skipped.append((file_path, "missing openwebui_id"))
                continue

            candidates.append(
                PluginCandidate(
                    plugin_type=plugin_type,
                    file_path=file_path,
                    metadata=metadata,
                    content=content,
                    function_id=build_function_id(file_path, metadata),
                )
            )

    candidates.sort(key=lambda item: (item.plugin_type, item.file_path.as_posix()))
    skipped.sort(key=lambda item: item[0].as_posix())
    return candidates, skipped


def install_plugin(
    candidate: PluginCandidate,
    api_key: str,
    base_url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = build_payload(candidate)
    update_url, create_url = build_api_urls(base_url, candidate)

    try:
        update_response = requests.post(
            update_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
        )
        if 200 <= update_response.status_code < 300:
            return True, "updated"

        create_response = requests.post(
            create_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
        )
        if 200 <= create_response.status_code < 300:
            return True, "created"

        message = _response_message(create_response)
        return False, f"create failed ({create_response.status_code}): {message}"
    except requests.exceptions.Timeout:
        return False, "request timed out"
    except requests.exceptions.ConnectionError:
        return False, f"cannot connect to {base_url}"
    except Exception as exc:
        return False, str(exc)


def _response_message(response: requests.Response) -> str:
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except Exception:
        return response.text[:500]


def print_candidates(candidates: Sequence[PluginCandidate]) -> None:
    if not candidates:
        print("No installable plugins found.")
        return

    print(f"Found {len(candidates)} installable plugins:")
    for candidate in candidates:
        relative_path = candidate.file_path.relative_to(REPO_ROOT)
        print(
            f"  - [{candidate.plugin_type}] {candidate.title} "
            f"v{candidate.version} -> {relative_path}"
        )


def print_skipped_summary(skipped: Sequence[Tuple[Path, str]]) -> None:
    if not skipped:
        return

    counts: Dict[str, int] = {}
    for _, reason in skipped:
        counts[reason] = counts.get(reason, 0) + 1

    summary = ", ".join(
        f"{reason}: {count}" for reason, count in sorted(counts.items())
    )
    print(f"Skipped {len(skipped)} files ({summary}).")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install repository plugins into an OpenWebUI instance."
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=sorted(PLUGIN_TYPE_DIRS.keys()),
        default=list(DEFAULT_TYPES),
        help="Plugin types to install. Defaults to all supported types.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List installable plugins without calling the API.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be installed without calling the API.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds. Default: {DEFAULT_TIMEOUT}.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    candidates, skipped = discover_plugins(args.types)

    print_candidates(candidates)
    print_skipped_summary(skipped)

    if args.list or args.dry_run:
        return 0

    if not candidates:
        print("Nothing to install.")
        return 1

    try:
        api_key, base_url = load_config()
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"Installing to: {base_url}")

    success_count = 0
    failed_candidates = []
    for candidate in candidates:
        relative_path = candidate.file_path.relative_to(REPO_ROOT)
        print(
            f"\nInstalling [{candidate.plugin_type}] {candidate.title} "
            f"v{candidate.version} ({relative_path})"
        )
        ok, message = install_plugin(
            candidate=candidate,
            api_key=api_key,
            base_url=base_url,
            timeout=args.timeout,
        )
        if ok:
            success_count += 1
            print(f"  [OK] {message}")
        else:
            failed_candidates.append(candidate)
            print(f"  [FAILED] {message}")

    print(f"\n" + "=" * 80)
    print(
        f"Finished: {success_count}/{len(candidates)} plugins installed successfully."
    )

    if failed_candidates:
        print(f"\n❌ {len(failed_candidates)} plugin(s) failed to install:")
        for candidate in failed_candidates:
            print(f"   • {candidate.title} ({candidate.plugin_type})")
            print(f"     → Check the error message above")
        print()

    print("=" * 80)
    return 0 if success_count == len(candidates) else 1


if __name__ == "__main__":
    sys.exit(main())
