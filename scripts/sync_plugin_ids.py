"""
Sync OpenWebUI Post IDs to local plugin files
同步远程插件 ID 到本地文件
"""

import os
import sys
import re
import difflib

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openwebui_community_client import get_client

try:
    from extract_plugin_versions import scan_plugins_directory
except ImportError:
    print("Error: extract_plugin_versions.py not found.")
    sys.exit(1)


def normalize(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.lower().strip())


def insert_id_into_file(file_path, post_id):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False
    in_frontmatter = False

    for line in lines:
        # Check for start/end of frontmatter
        if line.strip() == '"""':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                # End of frontmatter
                in_frontmatter = False

        # Check if ID already exists
        if in_frontmatter and (
            line.strip().startswith("openwebui_id:")
            or line.strip().startswith("post_id:")
        ):
            print(f"  ID already exists in {os.path.basename(file_path)}")
            return False

        new_lines.append(line)

        # Insert after version
        if in_frontmatter and not inserted and line.strip().startswith("version:"):
            new_lines.append(f"openwebui_id: {post_id}\n")
            inserted = True

    if inserted:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


def main():
    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Fetching remote posts from OpenWebUI Community...")
    remote_posts = client.get_all_posts()
    print(f"Fetched {len(remote_posts)} remote posts.")

    plugins_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins"
    )
    local_plugins = scan_plugins_directory(plugins_dir)
    print(f"Found {len(local_plugins)} local plugins.")

    matched_count = 0

    for plugin in local_plugins:
        local_title = plugin.get("title", "")
        if not local_title:
            continue

        file_path = plugin.get("file_path")
        best_match = None
        highest_ratio = 0.0

        # 1. Try Exact Match on Manifest Title (High Confidence)
        for post in remote_posts:
            manifest_title = (
                post.get("data", {})
                .get("function", {})
                .get("meta", {})
                .get("manifest", {})
                .get("title")
            )
            if manifest_title and normalize(manifest_title) == normalize(local_title):
                best_match = post
                highest_ratio = 1.0
                break

        # 2. Try Fuzzy Match on Post Title if no exact match
        if not best_match:
            for post in remote_posts:
                post_title = post.get("title", "")
                ratio = difflib.SequenceMatcher(
                    None, normalize(local_title), normalize(post_title)
                ).ratio()
                if ratio > 0.8 and ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match = post

        if best_match:
            post_id = best_match.get("id")
            post_title = best_match.get("title")
            print(
                f"Match found: '{local_title}' <--> '{post_title}' (ID: {post_id}) [Score: {highest_ratio:.2f}]"
            )

            if insert_id_into_file(file_path, post_id):
                print(f"  -> Updated {os.path.basename(file_path)}")
                matched_count += 1
        else:
            print(f"No match found for: '{local_title}'")

    print(f"\nTotal updated: {matched_count}")


if __name__ == "__main__":
    main()
