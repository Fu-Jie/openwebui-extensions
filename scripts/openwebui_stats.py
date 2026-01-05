#!/usr/bin/env python3
"""
OpenWebUI 社区统计工具

获取并统计你在 openwebui.com 上发布的插件/帖子数据。

使用方法：
    1. 设置环境变量：
       - OPENWEBUI_API_KEY: 你的 API Key
       - OPENWEBUI_USER_ID: 你的用户 ID
    2. 运行: python scripts/openwebui_stats.py

获取 API Key：
    访问 https://openwebui.com/settings/api 创建 API Key (sk-开头)

获取 User ID：
    从个人主页的 API 请求中获取，格式如: b15d1348-4347-42b4-b815-e053342d6cb0
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional
from pathlib import Path

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class OpenWebUIStats:
    """OpenWebUI 社区统计工具"""

    BASE_URL = "https://api.openwebui.com/api/v1"

    def __init__(self, api_key: str, user_id: Optional[str] = None):
        """
        初始化统计工具

        Args:
            api_key: OpenWebUI API Key (JWT Token)
            user_id: 用户 ID，如果为 None 则从 token 中解析
        """
        self.api_key = api_key
        self.user_id = user_id or self._parse_user_id_from_token(api_key)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _parse_user_id_from_token(self, token: str) -> str:
        """从 JWT Token 中解析用户 ID"""
        import base64

        try:
            # JWT 格式: header.payload.signature
            payload = token.split(".")[1]
            # 添加 padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return data.get("id", "")
        except Exception as e:
            print(f"⚠️ 无法从 Token 解析用户 ID: {e}")
            return ""

    def get_user_posts(self, sort: str = "new", page: int = 1) -> list:
        """
        获取用户发布的帖子列表

        Args:
            sort: 排序方式 (new/top/hot)
            page: 页码

        Returns:
            帖子列表
        """
        url = f"{self.BASE_URL}/posts/users/{self.user_id}"
        params = {"sort": sort, "page": page}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_all_posts(self, sort: str = "new") -> list:
        """获取所有帖子（自动分页）"""
        all_posts = []
        page = 1

        while True:
            posts = self.get_user_posts(sort=sort, page=page)
            if not posts:
                break
            all_posts.extend(posts)
            page += 1

        return all_posts

    def generate_stats(self, posts: list) -> dict:
        """生成统计数据"""
        stats = {
            "total_posts": len(posts),
            "total_downloads": 0,
            "total_views": 0,
            "total_upvotes": 0,
            "total_downvotes": 0,
            "total_saves": 0,
            "total_comments": 0,
            "by_type": {},
            "posts": [],
        }

        for post in posts:
            # 累计统计
            stats["total_downloads"] += post.get("downloads", 0)
            stats["total_views"] += post.get("views", 0)
            stats["total_upvotes"] += post.get("upvotes", 0)
            stats["total_downvotes"] += post.get("downvotes", 0)
            stats["total_saves"] += post.get("saveCount", 0)
            stats["total_comments"] += post.get("commentCount", 0)

            # 按类型分类
            post_type = post.get("data", {}).get("meta", {}).get("type", "unknown")
            if post_type not in stats["by_type"]:
                stats["by_type"][post_type] = 0
            stats["by_type"][post_type] += 1

            # 单个帖子信息
            manifest = post.get("data", {}).get("meta", {}).get("manifest", {})
            created_at = datetime.fromtimestamp(post.get("createdAt", 0))
            updated_at = datetime.fromtimestamp(post.get("updatedAt", 0))

            stats["posts"].append(
                {
                    "title": post.get("title", ""),
                    "slug": post.get("slug", ""),
                    "type": post_type,
                    "version": manifest.get("version", ""),
                    "downloads": post.get("downloads", 0),
                    "views": post.get("views", 0),
                    "upvotes": post.get("upvotes", 0),
                    "saves": post.get("saveCount", 0),
                    "comments": post.get("commentCount", 0),
                    "created_at": created_at.strftime("%Y-%m-%d"),
                    "updated_at": updated_at.strftime("%Y-%m-%d"),
                    "url": f"https://openwebui.com/posts/{post.get('slug', '')}",
                }
            )

        # 按下载量排序
        stats["posts"].sort(key=lambda x: x["downloads"], reverse=True)

        return stats

    def print_stats(self, stats: dict):
        """打印统计报告到终端"""
        print("\n" + "=" * 60)
        print("📊 OpenWebUI 社区统计报告")
        print("=" * 60)
        print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 总览
        print("📈 总览")
        print("-" * 40)
        print(f"  📝 发布数量: {stats['total_posts']}")
        print(f"  ⬇️  总下载量: {stats['total_downloads']}")
        print(f"  👁️  总浏览量: {stats['total_views']}")
        print(f"  👍 总点赞数: {stats['total_upvotes']}")
        print(f"  💾 总收藏数: {stats['total_saves']}")
        print(f"  💬 总评论数: {stats['total_comments']}")
        print()

        # 按类型分类
        print("📂 按类型分类")
        print("-" * 40)
        for post_type, count in stats["by_type"].items():
            print(f"  • {post_type}: {count}")
        print()

        # 详细列表
        print("📋 发布列表 (按下载量排序)")
        print("-" * 60)

        # 表头
        print(f"{'排名':<4} {'标题':<30} {'下载':<8} {'浏览':<8} {'点赞':<6}")
        print("-" * 60)

        for i, post in enumerate(stats["posts"], 1):
            title = (
                post["title"][:28] + ".." if len(post["title"]) > 30 else post["title"]
            )
            print(
                f"{i:<4} {title:<30} {post['downloads']:<8} {post['views']:<8} {post['upvotes']:<6}"
            )

        print("=" * 60)

    def generate_markdown(self, stats: dict) -> str:
        """生成 Markdown 格式报告"""
        md = []
        md.append("# 📊 OpenWebUI 社区统计报告")
        md.append("")
        md.append(f"> 📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        # 总览
        md.append("## 📈 总览")
        md.append("")
        md.append("| 指标 | 数值 |")
        md.append("|------|------|")
        md.append(f"| 📝 发布数量 | {stats['total_posts']} |")
        md.append(f"| ⬇️ 总下载量 | {stats['total_downloads']} |")
        md.append(f"| 👁️ 总浏览量 | {stats['total_views']} |")
        md.append(f"| 👍 总点赞数 | {stats['total_upvotes']} |")
        md.append(f"| 💾 总收藏数 | {stats['total_saves']} |")
        md.append(f"| 💬 总评论数 | {stats['total_comments']} |")
        md.append("")

        # 按类型分类
        md.append("## 📂 按类型分类")
        md.append("")
        for post_type, count in stats["by_type"].items():
            md.append(f"- **{post_type}**: {count}")
        md.append("")

        # 详细列表
        md.append("## 📋 发布列表")
        md.append("")
        md.append(
            "| 排名 | 标题 | 类型 | 版本 | 下载 | 浏览 | 点赞 | 收藏 | 更新日期 |"
        )
        md.append("|:---:|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

        for i, post in enumerate(stats["posts"], 1):
            title_link = f"[{post['title']}]({post['url']})"
            md.append(
                f"| {i} | {title_link} | {post['type']} | {post['version']} | "
                f"{post['downloads']} | {post['views']} | {post['upvotes']} | "
                f"{post['saves']} | {post['updated_at']} |"
            )

        md.append("")
        return "\n".join(md)

    def save_json(self, stats: dict, filepath: str):
        """保存 JSON 格式数据"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 数据已保存到: {filepath}")

    def generate_readme_stats(self, stats: dict, lang: str = "zh") -> str:
        """
        生成 README 统计徽章区域

        Args:
            stats: 统计数据
            lang: 语言 ("zh" 中文, "en" 英文)
        """
        # 获取 Top 5 插件
        top_plugins = stats["posts"][:5]

        # 中英文文本
        texts = {
            "zh": {
                "title": "## 📊 社区统计",
                "updated": f"> 🕐 自动更新于 {datetime.now().strftime('%Y-%m-%d')}",
                "header": "| 📝 发布 | ⬇️ 下载 | 👁️ 浏览 | 👍 点赞 | 💾 收藏 |",
                "top5_title": "### 🔥 热门插件 Top 5",
                "top5_header": "| 排名 | 插件 | 下载 | 浏览 |",
                "full_stats": "*完整统计请查看 [社区统计报告](./docs/community-stats.md)*",
            },
            "en": {
                "title": "## 📊 Community Stats",
                "updated": f"> 🕐 Auto-updated on {datetime.now().strftime('%Y-%m-%d')}",
                "header": "| 📝 Posts | ⬇️ Downloads | 👁️ Views | 👍 Upvotes | 💾 Saves |",
                "top5_title": "### 🔥 Top 5 Popular Plugins",
                "top5_header": "| Rank | Plugin | Downloads | Views |",
                "full_stats": "*See full stats in [Community Stats Report](./docs/community-stats.md)*",
            },
        }

        t = texts.get(lang, texts["en"])

        lines = []
        lines.append("<!-- STATS_START -->")
        lines.append(t["title"])
        lines.append("")
        lines.append(t["updated"])
        lines.append("")

        # 统计徽章表格
        lines.append(t["header"])
        lines.append("|:---:|:---:|:---:|:---:|:---:|")
        lines.append(
            f"| **{stats['total_posts']}** | **{stats['total_downloads']}** | "
            f"**{stats['total_views']}** | **{stats['total_upvotes']}** | **{stats['total_saves']}** |"
        )
        lines.append("")

        # Top 5 热门插件
        lines.append(t["top5_title"])
        lines.append("")
        lines.append(t["top5_header"])
        lines.append("|:---:|------|:---:|:---:|")

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, post in enumerate(top_plugins):
            medal = medals[i] if i < len(medals) else str(i + 1)
            lines.append(
                f"| {medal} | [{post['title']}]({post['url']}) | {post['downloads']} | {post['views']} |"
            )

        lines.append("")
        lines.append(t["full_stats"])
        lines.append("<!-- STATS_END -->")

        return "\n".join(lines)

    def update_readme(self, stats: dict, readme_path: str, lang: str = "zh"):
        """
        更新 README 文件中的统计区域

        Args:
            stats: 统计数据
            readme_path: README 文件路径
            lang: 语言 ("zh" 中文, "en" 英文)
        """
        import re

        # 读取现有内容
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 生成新的统计区域
        new_stats = self.generate_readme_stats(stats, lang)

        # 检查是否已有统计区域
        pattern = r"<!-- STATS_START -->.*?<!-- STATS_END -->"
        if re.search(pattern, content, re.DOTALL):
            # 替换现有区域
            new_content = re.sub(pattern, new_stats, content, flags=re.DOTALL)
        else:
            # 在简介段落之后插入统计区域
            # 查找模式：标题 -> 语言切换行 -> 简介段落 -> 插入位置
            lines = content.split("\n")
            insert_pos = 0
            found_intro = False

            for i, line in enumerate(lines):
                # 跳过标题
                if line.startswith("# "):
                    continue
                # 跳过空行
                if line.strip() == "":
                    continue
                # 跳过语言切换行 (如 "English | [中文]" 或 "[English] | 中文")
                if ("English" in line or "中文" in line) and "|" in line:
                    continue
                # 找到第一个非空、非标题、非语言切换的段落（简介）
                if not found_intro:
                    found_intro = True
                    # 继续到这个段落结束
                    continue
                # 简介段落后的空行或下一个标题就是插入位置
                if line.strip() == "" or line.startswith("#"):
                    insert_pos = i
                    break

            # 如果没找到合适位置，就放在第3行（标题和语言切换后）
            if insert_pos == 0:
                insert_pos = 3

            # 在适当位置插入
            lines.insert(insert_pos, "")
            lines.insert(insert_pos + 1, new_stats)
            lines.insert(insert_pos + 2, "")
            new_content = "\n".join(lines)

        # 写回文件
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ README 已更新: {readme_path}")


def main():
    """主函数"""
    # 获取配置
    api_key = os.getenv("OPENWEBUI_API_KEY")
    user_id = os.getenv("OPENWEBUI_USER_ID")

    if not api_key:
        print("❌ 错误: 未设置 OPENWEBUI_API_KEY 环境变量")
        print("请设置环境变量：")
        print("  export OPENWEBUI_API_KEY='your_api_key_here'")
        return 1

    if not user_id:
        print("❌ 错误: 未设置 OPENWEBUI_USER_ID 环境变量")
        print("请设置环境变量：")
        print("  export OPENWEBUI_USER_ID='your_user_id_here'")
        print("\n提示: 用户 ID 可以从之前的 curl 请求中获取")
        print("     例如: b15d1348-4347-42b4-b815-e053342d6cb0")
        return 1

    # 初始化
    stats_client = OpenWebUIStats(api_key, user_id)
    print(f"🔍 用户 ID: {stats_client.user_id}")

    # 获取所有帖子
    print("📥 正在获取帖子数据...")
    posts = stats_client.get_all_posts()
    print(f"✅ 获取到 {len(posts)} 个帖子")

    # 生成统计
    stats = stats_client.generate_stats(posts)

    # 打印到终端
    stats_client.print_stats(stats)

    # 保存 Markdown 报告
    script_dir = Path(__file__).parent.parent
    md_path = script_dir / "docs" / "community-stats.md"
    md_content = stats_client.generate_markdown(stats)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n✅ Markdown 报告已保存到: {md_path}")

    # 保存 JSON 数据
    json_path = script_dir / "docs" / "community-stats.json"
    stats_client.save_json(stats, str(json_path))

    # 更新 README 文件
    readme_path = script_dir / "README.md"
    readme_cn_path = script_dir / "README_CN.md"
    stats_client.update_readme(stats, str(readme_path), lang="en")
    stats_client.update_readme(stats, str(readme_cn_path), lang="zh")

    return 0


if __name__ == "__main__":
    exit(main())
