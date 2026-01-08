"""
Download plugin images from OpenWebUI Community
下载远程插件图片到本地目录
"""

import os
import sys
import re
import requests
from urllib.parse import urlparse

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openwebui_community_client import get_client


def find_local_plugin_by_id(plugins_dir: str, post_id: str) -> str | None:
    """根据 post_id 查找本地插件文件"""
    for root, _, files in os.walk(plugins_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(2000)

                id_match = re.search(
                    r"(?:openwebui_id|post_id):\s*([a-z0-9-]+)", content
                )
                if id_match and id_match.group(1).strip() == post_id:
                    return file_path
    return None


def download_image(url: str, save_path: str) -> bool:
    """下载图片"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error downloading: {e}")
        return False


def get_image_extension(url: str) -> str:
    """从 URL 获取图片扩展名"""
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        return ext
    return ".png"  # 默认


def main():
    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plugins_dir = os.path.join(base_dir, "plugins")

    print("Fetching remote posts from OpenWebUI Community...")
    posts = client.get_all_posts()
    print(f"Found {len(posts)} remote posts.\n")

    downloaded = 0
    skipped = 0
    not_found = 0

    for post in posts:
        post_id = post.get("id")
        title = post.get("title", "Unknown")
        media = post.get("media", [])

        if not media:
            continue

        # 只取第一张图片
        first_media = media[0] if isinstance(media, list) else media

        # 处理字典格式 {'url': '...', 'type': 'image'}
        if isinstance(first_media, dict):
            image_url = first_media.get("url")
        else:
            image_url = first_media

        if not image_url:
            continue

        print(f"Processing: {title}")
        print(f"  Image URL: {image_url}")

        # 查找对应的本地插件
        local_plugin = find_local_plugin_by_id(plugins_dir, post_id)
        if not local_plugin:
            print(f"  ⚠️  No local plugin found for ID: {post_id}")
            not_found += 1
            continue

        # 确定保存路径
        plugin_dir = os.path.dirname(local_plugin)
        plugin_name = os.path.splitext(os.path.basename(local_plugin))[0]
        ext = get_image_extension(image_url)
        save_path = os.path.join(plugin_dir, plugin_name + ext)

        # 检查是否已存在
        if os.path.exists(save_path):
            print(f"  ⏭️  Image already exists: {os.path.basename(save_path)}")
            skipped += 1
            continue

        # 下载
        print(f"  Downloading to: {save_path}")
        if download_image(image_url, save_path):
            print(f"  ✅ Downloaded: {os.path.basename(save_path)}")
            downloaded += 1
        else:
            print(f"  ❌ Failed to download")

    print(f"\n{'='*50}")
    print(
        f"Finished: {downloaded} downloaded, {skipped} skipped, {not_found} not found locally"
    )


if __name__ == "__main__":
    main()
