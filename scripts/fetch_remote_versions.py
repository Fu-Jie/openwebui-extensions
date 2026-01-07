"""
Fetch remote plugin versions from OpenWebUI Community
获取远程插件版本信息
"""

import json
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openwebui_community_client import get_client


def main():
    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Fetching remote plugins from OpenWebUI Community...")
    try:
        posts = client.get_all_posts()
    except Exception as e:
        print(f"Error fetching posts: {e}")
        sys.exit(1)

    formatted_plugins = []
    for post in posts:
        post["type"] = "remote_plugin"
        formatted_plugins.append(post)

    output_file = "remote_versions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_plugins, f, indent=2, ensure_ascii=False)

    print(
        f"✅ Successfully saved {len(formatted_plugins)} remote plugins to {output_file}"
    )
    print(f"   You can now compare local vs remote using:")
    print(f"   python scripts/extract_plugin_versions.py --compare {output_file}")


if __name__ == "__main__":
    main()
