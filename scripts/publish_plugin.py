"""
Publish plugins to OpenWebUI Community
使用 OpenWebUICommunityClient 发布插件到官方社区

用法：
    python scripts/publish_plugin.py          # 只更新有版本变化的插件
    python scripts/publish_plugin.py --force  # 强制更新所有插件
"""

import os
import sys
import re
import argparse

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openwebui_community_client import OpenWebUICommunityClient, get_client


def find_plugins_with_id(plugins_dir: str) -> list:
    """查找所有带 openwebui_id 的插件文件"""
    plugins = []
    for root, _, files in os.walk(plugins_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(2000)  # 只读前 2000 字符检查 ID

                id_match = re.search(
                    r"(?:openwebui_id|post_id):\s*([a-z0-9-]+)", content
                )
                if id_match:
                    plugins.append(
                        {"file_path": file_path, "post_id": id_match.group(1).strip()}
                    )
    return plugins


def main():
    parser = argparse.ArgumentParser(description="Publish plugins to OpenWebUI Market")
    parser.add_argument(
        "--force", action="store_true", help="Force update even if version matches"
    )
    args = parser.parse_args()

    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plugins_dir = os.path.join(base_dir, "plugins")

    plugins = find_plugins_with_id(plugins_dir)
    print(f"Found {len(plugins)} plugins with OpenWebUI ID.\n")

    updated = 0
    skipped = 0
    failed = 0

    for plugin in plugins:
        file_path = plugin["file_path"]
        file_name = os.path.basename(file_path)
        post_id = plugin["post_id"]

        print(f"Processing {file_name} (ID: {post_id})...")

        success, message = client.publish_plugin_from_file(file_path, force=args.force)

        if success:
            if "Skipped" in message:
                print(f"  ⏭️  {message}")
                skipped += 1
            else:
                print(f"  ✅ {message}")
                updated += 1
        else:
            print(f"  ❌ {message}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Finished: {updated} updated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
