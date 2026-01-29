#!/usr/bin/env python3
"""
======================================================================
Staged README Synchronizer to OpenWebUI Community
暂存 README 文件同步到 OpenWebUI 社区工具
======================================================================

PURPOSE / 用途:
--------------
This script synchronizes staged README.md/README_CN.md files to their
corresponding OpenWebUI Community posts automatically. It's designed for
batch updating documentation content without modifying plugin versions
or media attachments.

本脚本自动将暂存的 README.md/README_CN.md 文件同步到对应的 OpenWebUI
社区帖子。专为批量更新文档内容设计，不修改插件版本或媒体附件。

USAGE / 使用方法:
----------------
1. Set up environment:
   配置环境：

   Create a .env file in the repository root with:
   在仓库根目录创建 .env 文件，包含：

   OPENWEBUI_API_KEY=your_api_key_here

2. Stage README files to sync:
   暂存需要同步的 README 文件：

   git add plugins/actions/my_plugin/README.md
   git add plugins/actions/my_plugin/README_CN.md

3. Run the script:
   运行脚本：

   python plugins/debug/common_tools/update_readmes_to_market.py

WORKFLOW / 工作流程:
-------------------
1. Load OPENWEBUI_API_KEY from .env file
   从 .env 文件加载 OPENWEBUI_API_KEY

2. Get list of staged README.md/README_CN.md files via git
   通过 git 获取暂存的 README.md/README_CN.md 文件列表

3. For each staged README:
   对于每个暂存的 README：

   a. Locate the corresponding plugin .py file
      定位对应的插件 .py 文件

   b. Extract openwebui_id/post_id from plugin frontmatter
      从插件前置信息中提取 openwebui_id/post_id

   c. Fetch existing post data from OpenWebUI Community API
      从 OpenWebUI 社区 API 获取现有帖子数据

   d. Update post content with new README content
      用新的 README 内容更新帖子内容

   e. Push changes via API (preserves version & media)
      通过 API 推送更改（保留版本和媒体）

REQUIREMENTS / 依赖要求:
-----------------------
- python-dotenv: For loading .env configuration
                 用于加载 .env 配置文件
- Git repository: Must be run from a git-tracked workspace
                  必须在 git 跟踪的工作区中运行

KEY FEATURES / 关键特性:
-----------------------
✅ Only updates content field (不仅更新内容字段)
✅ Skips files without openwebui_id (跳过没有 openwebui_id 的文件)
✅ Automatically matches CN/EN plugin files (自动匹配中英文插件文件)
✅ Safe: Won't modify version or media fields (安全：不会修改版本或媒体字段)

NOTES / 注意事项:
---------------
- This is a DEBUG/DEVELOPMENT tool, not for production workflows
  这是一个调试/开发工具，不用于生产工作流

- Always verify changes in OpenWebUI Community after sync
  同步后务必在 OpenWebUI 社区中验证更改

- Requires valid API key with update permissions
  需要具有更新权限的有效 API 密钥

AUTHOR / 作者:
-------------
Fu-Jie
GitHub: https://github.com/Fu-Jie/awesome-openwebui

======================================================================
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional, List


def _load_dotenv(repo_root: Path) -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception as exc:  # pragma: no cover
        print("Missing dependency: python-dotenv. Please install it and retry.")
        raise SystemExit(1) from exc

    env_path = repo_root / ".env"
    load_dotenv(env_path)


def _get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _get_staged_readmes(repo_root: Path) -> List[Path]:
    try:
        output = subprocess.check_output(
            [
                "git",
                "-C",
                str(repo_root),
                "diff",
                "--cached",
                "--name-only",
                "--",
                "*.md",
            ],
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to read staged files: {exc}")
        return []

    paths = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith("README.md") or line.endswith("README_CN.md"):
            paths.append(repo_root / line)
    return paths


def _parse_frontmatter(content: str) -> Dict[str, str]:
    match = re.search(r'^\s*"""\n(.*?)\n"""', content, re.DOTALL)
    if not match:
        match = re.search(r'"""\n(.*?)\n"""', content, re.DOTALL)
        if not match:
            return {}

    frontmatter = match.group(1)
    meta: Dict[str, str] = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def _find_plugin_file(readme_path: Path) -> Optional[Path]:
    plugin_dir = readme_path.parent
    is_cn = readme_path.name.lower().endswith("readme_cn.md")

    py_files = [
        p
        for p in plugin_dir.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith("test_")
    ]
    if not py_files:
        return None

    cn_files = [p for p in py_files if p.stem.endswith("_cn")]
    en_files = [p for p in py_files if not p.stem.endswith("_cn")]

    candidates = cn_files + en_files if is_cn else en_files + cn_files

    # Prefer files that contain openwebui_id/post_id in frontmatter
    for candidate in candidates:
        post_id = _get_post_id(candidate)
        if post_id:
            return candidate

    return candidates[0] if candidates else None


def _get_post_id(plugin_file: Path) -> Optional[str]:
    try:
        content = plugin_file.read_text(encoding="utf-8")
    except Exception:
        return None

    meta = _parse_frontmatter(content)
    return meta.get("openwebui_id") or meta.get("post_id")


def main() -> int:
    repo_root = _get_repo_root()
    _load_dotenv(repo_root)

    api_key = os.environ.get("OPENWEBUI_API_KEY")
    if not api_key:
        print("OPENWEBUI_API_KEY is not set in environment.")
        return 1

    client_module_path = repo_root / "scripts" / "openwebui_community_client.py"
    spec = importlib.util.spec_from_file_location(
        "openwebui_community_client", client_module_path
    )
    if not spec or not spec.loader:
        print("Failed to load openwebui_community_client module.")
        return 1

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = module.get_client(api_key)

    staged_readmes = _get_staged_readmes(repo_root)
    if not staged_readmes:
        print("No staged README files found.")
        return 0

    for readme_path in staged_readmes:
        if not readme_path.exists():
            print(f"Skipped (missing): {readme_path}")
            continue

        plugin_file = _find_plugin_file(readme_path)
        if not plugin_file:
            print(f"Skipped (no plugin file): {readme_path}")
            continue

        post_id = _get_post_id(plugin_file)
        if not post_id:
            print(f"Skipped (no openwebui_id): {readme_path}")
            continue

        try:
            post_data = client.get_post(post_id)
            if not post_data:
                print(f"Skipped (post not found): {readme_path}")
                continue

            readme_content = readme_path.read_text(encoding="utf-8")

            # Update README content only, keep other fields unchanged.
            post_data["content"] = readme_content

            ok = client.update_post(post_id, post_data)
            if ok:
                print(f"Updated README -> {readme_path} (post_id: {post_id})")
        except Exception as exc:
            print(f"Failed: {readme_path} ({exc})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
