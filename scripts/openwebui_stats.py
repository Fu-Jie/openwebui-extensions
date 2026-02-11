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
import zlib
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class OpenWebUIStats:
    """OpenWebUI 社区统计工具"""

    BASE_URL = "https://api.openwebui.com/api/v1"

    def __init__(
        self,
        api_key: str,
        user_id: Optional[str] = None,
        gist_token: Optional[str] = None,
        gist_id: Optional[str] = None,
    ):
        """
        初始化统计工具

        Args:
            api_key: OpenWebUI API Key (JWT Token)
            user_id: 用户 ID，如果为 None 则从 token 中解析
            gist_token: GitHub Personal Access Token (用于读写 Gist)
            gist_id: GitHub Gist ID
        """
        self.api_key = api_key
        self.user_id = user_id or self._parse_user_id_from_token(api_key)
        self.gist_token = gist_token
        self.gist_id = gist_id
        self.history_filename = "community-stats-history.json"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self.history_file = Path("docs/stats-history.json")

    # 定义下载类别的判定（这些类别会计入总浏览量/下载量统计）
    DOWNLOADABLE_TYPES = [
        "action",
        "filter",
        "pipe",
        "toolkit",
        "function",
        "prompt",
        "model",
    ]

    def load_history(self) -> list:
        """加载历史记录 (优先尝试 Gist, 其次本地文件)"""
        # 尝试从 Gist 加载
        if self.gist_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.gist_token}"}
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    gist_data = resp.json()
                    file_info = gist_data.get("files", {}).get(self.history_filename)
                    if file_info:
                        content = file_info.get("content")
                        print(f"✅ 已从 Gist 加载历史记录 ({self.gist_id})")
                        return json.loads(content)
            except Exception as e:
                print(f"⚠️ 无法从 Gist 加载历史: {e}")

        # 降级：从本地加载
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 无法加载本地历史记录: {e}")
        return []

    def save_history(self, stats: dict):
        """保存当前快照到历史记录 (优先保存到 Gist, 其次本地)"""
        history = self.load_history()
        today = get_beijing_time().strftime("%Y-%m-%d")

        # 构造详细快照 (包含每个插件的下载量)
        snapshot = {
            "date": today,
            "total_posts": stats["total_posts"],
            "total_downloads": stats["total_downloads"],
            "total_views": stats["total_views"],
            "total_upvotes": stats["total_upvotes"],
            "total_saves": stats["total_saves"],
            "followers": stats.get("user", {}).get("followers", 0),
            "points": stats.get("user", {}).get("total_points", 0),
            "contributions": stats.get("user", {}).get("contributions", 0),
            "posts": {p["slug"]: p["downloads"] for p in stats.get("posts", [])},
        }

        # 更新或追加数据点
        updated = False
        for i, item in enumerate(history):
            if item.get("date") == today:
                history[i] = snapshot
                updated = True
                break
        if not updated:
            history.append(snapshot)

        # 限制长度 (90天)
        history = history[-90:]

        # 尝试保存到 Gist
        if self.gist_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.gist_token}"}
                payload = {
                    "files": {
                        self.history_filename: {
                            "content": json.dumps(history, ensure_ascii=False, indent=2)
                        }
                    }
                }
                resp = requests.patch(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    print(f"✅ 历史记录已同步至 Gist ({self.gist_id})")
                    # 如果同步成功，不再保存到本地，减少 commit 压力
                    return
            except Exception as e:
                print(f"⚠️ 同步至 Gist 失败: {e}")

        # 降级：保存到本地
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"✅ 历史记录已更新至本地 ({today})")

    def get_stat_delta(self, stats: dict) -> dict:
        """计算相对于上次记录的增长 (24h)"""
        history = self.load_history()
        if not history:
            return {}

        today = get_beijing_time().strftime("%Y-%m-%d")
        prev = None

        # 查找非今天的最后一笔数据作为基准
        for item in reversed(history):
            if item.get("date") != today:
                prev = item
                break

        if not prev:
            return {}

        return {
            "downloads": stats["total_downloads"] - prev.get("total_downloads", 0),
            "views": stats["total_views"] - prev.get("total_views", 0),
            "upvotes": stats["total_upvotes"] - prev.get("total_upvotes", 0),
            "saves": stats["total_saves"] - prev.get("total_saves", 0),
            "followers": stats.get("user", {}).get("followers", 0)
            - prev.get("followers", 0),
            "points": stats.get("user", {}).get("total_points", 0)
            - prev.get("points", 0),
            "contributions": stats.get("user", {}).get("contributions", 0)
            - prev.get("contributions", 0),
            "posts": {
                p["slug"]: p["downloads"]
                - prev.get("posts", {}).get(p["slug"], p["downloads"])
                for p in stats.get("posts", [])
            },
        }

    def _resolve_post_type(self, post: dict) -> str:
        """解析帖子类别"""
        top_type = post.get("type")
        function_data = post.get("data", {}) or {}
        function_obj = function_data.get("function", {}) or {}
        meta = function_obj.get("meta", {}) or {}
        manifest = meta.get("manifest", {}) or {}

        # 类别识别优先级：
        if top_type == "review":
            return "review"

        post_type = "unknown"
        if meta.get("type"):
            post_type = meta.get("type")
        elif function_obj.get("type"):
            post_type = function_obj.get("type")
        elif top_type:
            post_type = top_type
        elif not meta and not function_obj:
            post_type = "post"

        # 统一和启发式识别逻辑
        if post_type == "unknown" and function_obj:
            post_type = "action"

        if post_type == "action" or post_type == "unknown":
            all_metadata = (
                post.get("title", "")
                + json.dumps(meta, ensure_ascii=False)
                + json.dumps(manifest, ensure_ascii=False)
            ).lower()

            if "filter" in all_metadata:
                post_type = "filter"
            elif "pipe" in all_metadata:
                post_type = "pipe"
            elif "toolkit" in all_metadata:
                post_type = "toolkit"

        return post_type

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

    def generate_mermaid_chart(self, stats: dict = None, lang: str = "zh") -> str:
        """生成支持 Kroki 服务端渲染的动态 Mermaid 图表链接 (零 Commit)"""
        history = self.load_history()
        if not history:
            return ""

        # 多语言标签
        labels = {
            "zh": {
                "trend_title": "增长与趋势 (Last 14 Days)",
                "trend_subtitle": "Engagement & Downloads Trend",
                "legend": "蓝色: 总下载量 | 紫色: 总浏览量 (实时动态生成)",
                "dist_title": "内容分类占比 (Distribution)",
                "dist_subtitle": "Plugin Types Distribution",
            },
            "en": {
                "trend_title": "Growth & Trends (Last 14 Days)",
                "trend_subtitle": "Engagement & Downloads Trend",
                "legend": "Blue: Downloads | Purple: Views (Real-time dynamic)",
                "dist_title": "Content Distribution",
                "dist_subtitle": "Plugin Types Distribution",
            },
        }
        l = labels.get(lang, labels["en"])

        def kroki_render(mermaid_code: str) -> str:
            """将 Mermaid 代码压缩并编码为 Kroki 链接"""
            try:
                compressed = zlib.compress(mermaid_code.encode("utf-8"), level=9)
                encoded = base64.urlsafe_b64encode(compressed).decode("utf-8")
                return f"https://kroki.io/mermaid/svg/{encoded}"
            except:
                return ""

        charts = []

        # 1. 增长趋势图 (XY Chart)
        if len(history) >= 3:
            data = history[-14:]
            dates = [item["date"][-5:] for item in data]
            dates_str = ", ".join([f'"{d}"' for d in dates])
            dls = [str(item["total_downloads"]) for item in data]
            vws = [str(item["total_views"]) for item in data]

            mm = f"""xychart-beta
    title "{l['trend_subtitle']}"
    x-axis [{dates_str}]
    y-axis "Total Counts"
    line [{', '.join(dls)}]
    line [{', '.join(vws)}]"""

            charts.append(f"### 📈 {l['trend_title']}")
            charts.append(f"![Trend]({kroki_render(mm)})")
            charts.append(f"\n> *{l['legend']}*")
            charts.append("")

        # 2. 插件类型分布 (Pie Chart)
        if stats and stats.get("by_type"):
            pie_data = "\n".join(
                [
                    f'    "{p_type}" : {count}'
                    for p_type, count in stats["by_type"].items()
                ]
            )
            mm = f"pie title \"{l['dist_subtitle']}\"\n{pie_data}"
            charts.append(f"### 📂 {l['dist_title']}")
            charts.append(f"![Distribution]({kroki_render(mm)})")
            charts.append("")

        return "\n".join(charts)

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
            "user": {},  # 用户信息
        }

        # 从第一个帖子中提取用户信息
        if posts and "user" in posts[0]:
            user = posts[0]["user"]
            stats["user"] = {
                "username": user.get("username", ""),
                "name": user.get("name", ""),
                "profile_url": f"https://openwebui.com/u/{user.get('username', '')}",
                "profile_image": user.get("profileImageUrl", ""),
                "followers": user.get("followerCount", 0),
                "following": user.get("followingCount", 0),
                "total_points": user.get("totalPoints", 0),
                "post_points": user.get("postPoints", 0),
                "comment_points": user.get("commentPoints", 0),
                "contributions": user.get("totalContributions", 0),
            }

        for post in posts:
            post_type = self._resolve_post_type(post)

            function_data = post.get("data", {}) or {}
            function_obj = function_data.get("function", {}) or {}
            meta = function_obj.get("meta", {}) or {}
            manifest = meta.get("manifest", {}) or {}

            # 累计统计
            post_downloads = post.get("downloads", 0)
            post_views = post.get("views", 0)

            stats["total_downloads"] += post_downloads
            stats["total_upvotes"] += post.get("upvotes", 0)
            stats["total_downvotes"] += post.get("downvotes", 0)
            stats["total_saves"] += post.get("saveCount", 0)
            stats["total_comments"] += post.get("commentCount", 0)

            # 关键：总浏览量不包括不可以下载的类型 (如 post, review)
            if post_type in self.DOWNLOADABLE_TYPES or post_downloads > 0:
                stats["total_views"] += post_views

            if post_type not in stats["by_type"]:
                stats["by_type"][post_type] = 0
            stats["by_type"][post_type] += 1

            # 单个帖子信息
            created_at = datetime.fromtimestamp(post.get("createdAt", 0))
            updated_at = datetime.fromtimestamp(post.get("updatedAt", 0))

            stats["posts"].append(
                {
                    "title": post.get("title", ""),
                    "slug": post.get("slug", ""),
                    "type": post_type,
                    "version": manifest.get("version", ""),
                    "author": manifest.get("author", ""),
                    "description": meta.get("description", ""),
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
        print(f"📅 生成时间 (北京): {get_beijing_time().strftime('%Y-%m-%d %H:%M')}")
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

    def _safe_key(self, key: str) -> str:
        """生成安全的文件名 Key (MD5 hash) 以避免中文字符问题"""
        import hashlib

        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def generate_markdown(self, stats: dict, lang: str = "zh") -> str:
        """
        生成 Markdown 格式报告 (全动态徽章与 Kroki 图表)

        Args:
            stats: 统计数据
            lang: 语言 ("zh" 中文, "en" 英文)
        """
        # 获取增量数据
        delta = self.get_stat_delta(stats)

        # 中英文文本
        texts = {
            "zh": {
                "title": "# 📊 OpenWebUI 社区统计报告",
                "updated_label": "更新时间",
                "overview_title": "## 📈 总览",
                "overview_header": "| 指标 | 数值 |",
                "posts": "📝 发布数量",
                "downloads": "⬇️ 总下载量",
                "views": "👁️ 总浏览量",
                "upvotes": "👍 总点赞数",
                "saves": "💾 总收藏数",
                "comments": "💬 总评论数",
                "author_points": "⭐ 作者总积分",
                "author_followers": "👥 粉丝数量",
                "type_title": "## 📂 按类型分类",
                "list_title": "## 📋 发布列表",
                "list_header": "| 排名 | 标题 | 类型 | 版本 | 下载 | 浏览 | 点赞 | 收藏 | 更新日期 |",
            },
            "en": {
                "title": "# 📊 OpenWebUI Community Stats Report",
                "updated_label": "Updated",
                "overview_title": "## 📈 Overview",
                "overview_header": "| Metric | Value |",
                "posts": "📝 Total Posts",
                "downloads": "⬇️ Total Downloads",
                "views": "👁️ Total Views",
                "upvotes": "👍 Total Upvotes",
                "saves": "💾 Total Saves",
                "comments": "💬 Total Comments",
                "author_points": "⭐ Author Points",
                "author_followers": "👥 Followers",
                "type_title": "## 📂 By Type",
                "list_title": "## 📋 Posts List",
                "list_header": "| Rank | Title | Type | Version | Downloads | Views | Upvotes | Saves | Updated |",
            },
        }

        t = texts.get(lang, texts["en"])
        user = stats.get("user", {})

        md = []
        md.append(t["title"])
        md.append("")

        updated_key = "updated_zh" if lang == "zh" else "updated"
        md.append(f"> {self.get_badge(updated_key, stats, user, delta)}")
        md.append("")

        # 插入趋势图 (使用 Kroki SVG 链接)
        chart = self.generate_mermaid_chart(stats, lang=lang)
        if chart:
            md.append(chart)
            md.append("")

        # 总览
        md.append(t["overview_title"])
        md.append("")
        md.append(t["overview_header"])
        md.append("|------|------|")
        md.append(f"| {t['posts']} | {self.get_badge('posts', stats, user, delta)} |")
        md.append(
            f"| {t['downloads']} | {self.get_badge('downloads', stats, user, delta)} |"
        )
        md.append(f"| {t['views']} | {self.get_badge('views', stats, user, delta)} |")
        md.append(
            f"| {t['upvotes']} | {self.get_badge('upvotes', stats, user, delta)} |"
        )
        md.append(f"| {t['saves']} | {self.get_badge('saves', stats, user, delta)} |")

        # 作者信息
        if user:
            md.append(
                f"| {t['author_points']} | {self.get_badge('points', stats, user, delta)} |"
            )
            md.append(
                f"| {t['author_followers']} | {self.get_badge('followers', stats, user, delta)} |"
            )

        md.append("")

        # 按类型分类
        md.append(t["type_title"])
        md.append("")
        for post_type, count in stats["by_type"].items():
            md.append(f"- **{post_type}**: {count}")
        md.append("")

        # 详细列表
        md.append(t["list_title"])
        md.append("")
        md.append(t["list_header"])
        md.append("|:---:|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

        for i, post in enumerate(stats["posts"], 1):
            title_link = f"[{post['title']}]({post['url']})"
            slug_hash = self._safe_key(post["slug"])

            # 使用针对每个帖子的动态徽章 (使用 Hash 保证文件名安全)
            dl_badge = self.get_badge(
                f"post_{slug_hash}_dl", stats, user, delta, is_post=True
            )
            vw_badge = self.get_badge(
                f"post_{slug_hash}_vw", stats, user, delta, is_post=True
            )
            up_badge = self.get_badge(
                f"post_{slug_hash}_up", stats, user, delta, is_post=True
            )
            sv_badge = self.get_badge(
                f"post_{slug_hash}_sv", stats, user, delta, is_post=True
            )

            # 版本号使用静态 Shields.io 徽章
            ver = post["version"] if post["version"] else "N/A"
            ver_color = "blue" if post["version"] else "gray"
            ver_badge = (
                f"![v](https://img.shields.io/badge/v-{ver}-{ver_color}?style=flat)"
            )

            md.append(
                f"| {i} | {title_link} | {post['type']} | {ver_badge} | "
                f"{dl_badge} | {vw_badge} | {up_badge} | "
                f"{sv_badge} | {post['updated_at']} |"
            )

        md.append("")
        return "\n".join(md)

    def save_json(self, stats: dict, filepath: str):
        """保存 JSON 格式数据"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 数据已保存到: {filepath}")

    def generate_shields_endpoints(self, stats: dict, output_dir: str = "docs/badges"):
        """
        生成 Shields.io endpoint JSON 文件

        Args:
            stats: 统计数据
            output_dir: 输出目录
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        def format_number(n: int) -> str:
            """格式化数字为易读格式"""
            if n >= 1000000:
                return f"{n/1000000:.1f}M"
            elif n >= 1000:
                return f"{n/1000:.1f}k"
            return str(n)

        # 各种徽章数据
        badges = {
            "downloads": {
                "schemaVersion": 1,
                "label": "downloads",
                "message": format_number(stats["total_downloads"]),
                "color": "blue",
                "namedLogo": "openwebui",
            },
            "plugins": {
                "schemaVersion": 1,
                "label": "plugins",
                "message": str(stats["total_posts"]),
                "color": "green",
            },
            "followers": {
                "schemaVersion": 1,
                "label": "followers",
                "message": format_number(stats.get("user", {}).get("followers", 0)),
                "color": "blue",
            },
            "points": {
                "schemaVersion": 1,
                "label": "points",
                "message": format_number(stats.get("user", {}).get("total_points", 0)),
                "color": "orange",
            },
            "upvotes": {
                "schemaVersion": 1,
                "label": "upvotes",
                "message": format_number(stats["total_upvotes"]),
                "color": "brightgreen",
            },
        }

        for name, data in badges.items():
            filepath = Path(output_dir) / f"{name}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"  📊 Generated badge: {name}.json")

        if self.gist_token and self.gist_id:
            try:
                # 构造并上传 Shields.io 徽章数据
                self.upload_gist_badges(stats)
            except Exception as e:
                print(f"⚠️ 徽章生成失败: {e}")

        print(f"✅ Shields.io endpoints saved to: {output_dir}/")

    def upload_gist_badges(self, stats: dict):
        """生成并上传 Gist 徽章数据 (用于 Shields.io Endpoint)"""
        if not (self.gist_token and self.gist_id):
            return

        delta = self.get_stat_delta(stats)

        # 定义徽章配置 {key: (label, value, color)}
        badges_config = {
            "downloads": ("Downloads", stats["total_downloads"], "brightgreen"),
            "views": ("Views", stats["total_views"], "blue"),
            "upvotes": ("Upvotes", stats["total_upvotes"], "orange"),
            "saves": ("Saves", stats["total_saves"], "lightgrey"),
            "followers": (
                "Followers",
                stats.get("user", {}).get("followers", 0),
                "blueviolet",
            ),
            "points": (
                "Points",
                stats.get("user", {}).get("total_points", 0),
                "yellow",
            ),
            "contributions": (
                "Contributions",
                stats.get("user", {}).get("contributions", 0),
                "green",
            ),
            "posts": ("Posts", stats["total_posts"], "informational"),
        }

        files_payload = {}
        for key, (label, val, color) in badges_config.items():
            diff = delta.get(key, 0)
            if isinstance(diff, dict):
                diff = 0  # 避免 'posts' key 导致的 dict vs int 比较错误

            message = f"{val}"
            if diff > 0:
                message += f" (+{diff}🚀)"
            elif diff < 0:
                message += f" ({diff})"

            # 构造 Shields.io endpoint JSON
            # 参考: https://shields.io/badges/endpoint-badge
            badge_data = {
                "schemaVersion": 1,
                "label": label,
                "message": message,
                "color": color,
            }

            filename = f"badge_{key}.json"
            files_payload[filename] = {
                "content": json.dumps(badge_data, ensure_ascii=False)
            }

        # 生成 Top 6 插件徽章 (基于槽位 p1, p2...)
        post_deltas = delta.get("posts", {})
        for i, post in enumerate(stats.get("posts", [])[:6]):
            idx = i + 1
            diff = post_deltas.get(post["slug"], 0)

            # 下载量徽章
            dl_msg = f"{post['downloads']}"
            if diff > 0:
                dl_msg += f" (+{diff}🚀)"

            files_payload[f"badge_p{idx}_dl.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Downloads",
                        "message": dl_msg,
                        "color": "brightgreen",
                    }
                )
            }
            # 浏览量徽章 (由于历史记录没记单个 post 浏览量，暂时只显总数)
            files_payload[f"badge_p{idx}_vw.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Views",
                        "message": f"{post['views']}",
                        "color": "blue",
                    }
                )
            }

        # 生成所有帖子的个体徽章 (用于详细报表)
        # 生成所有帖子的个体徽章 (用于详细报表)
        for post in stats.get("posts", []):
            slug_hash = self._safe_key(post["slug"])
            diff = post_deltas.get(post["slug"], 0)

            # 1. Downloads
            dl_msg = f"{post['downloads']}"
            if diff > 0:
                dl_msg += f" (+{diff}🚀)"

            files_payload[f"badge_post_{slug_hash}_dl.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Downloads",
                        "message": dl_msg,
                        "color": "brightgreen",
                    }
                )
            }

            # 2. Views
            files_payload[f"badge_post_{slug_hash}_vw.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Views",
                        "message": f"{post['views']}",
                        "color": "blue",
                    }
                )
            }

            # 3. Upvotes
            files_payload[f"badge_post_{slug_hash}_up.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Upvotes",
                        "message": f"{post['upvotes']}",
                        "color": "orange",
                    }
                )
            }

            # 4. Saves
            files_payload[f"badge_post_{slug_hash}_sv.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "Saves",
                        "message": f"{post['saves']}",
                        "color": "lightgrey",
                    }
                )
            }

        # 生成更新时间徽章
        now_str = get_beijing_time().strftime("%Y-%m-%d %H:%M")
        files_payload["badge_updated.json"] = {
            "content": json.dumps(
                {
                    "schemaVersion": 1,
                    "label": "Auto-updated",
                    "message": now_str,
                    "color": "gray",
                }
            )
        }
        files_payload["badge_updated_zh.json"] = {
            "content": json.dumps(
                {
                    "schemaVersion": 1,
                    "label": "自动更新于",
                    "message": now_str,
                    "color": "gray",
                }
            )
        }

        # 将生成的 Markdown 报告也作为一个普通 JSON 文件上传到 Gist
        for lang in ["zh", "en"]:
            report_content = self.generate_markdown(stats, lang=lang)
            files_payload[f"report_{lang}.md"] = {"content": report_content}

        # 批量上传到 Gist
        url = f"https://api.github.com/gists/{self.gist_id}"
        headers = {"Authorization": f"token {self.gist_token}"}
        payload = {"files": files_payload}

        resp = requests.patch(url, headers=headers, json=payload)
        if resp.status_code == 200:
            print(f"✅ 动态数据与报告已同步至 Gist ({len(files_payload)} files)")
        else:
            print(f"⚠️ Gist 同步失败: {resp.status_code} {resp.text}")

    def get_badge(
        self,
        key: str,
        stats: dict,
        user: dict,
        delta: dict,
        is_post: bool = False,
        style: str = "flat",
    ) -> str:
        """获取 Shields.io 徽章 URL (包含增量显示)"""
        import urllib.parse

        gist_user = "Fu-Jie"

        def _fmt_delta(k: str) -> str:
            val = delta.get(k, 0)
            if val > 0:
                return f" <br><sub>(+{val}🚀)</sub>"
            return ""

        if not self.gist_id:
            if is_post:
                return "**-**"
            val = stats.get(f"total_{key}", 0)
            if key == "followers":
                val = user.get("followers", 0)
            if key == "points":
                val = user.get("total_points", 0)
            if key == "contributions":
                val = user.get("contributions", 0)
            if key == "posts":
                val = stats.get("total_posts", 0)
            if key == "saves":
                val = stats.get("total_saves", 0)
            if key.startswith("updated"):
                return f"🕐 {get_beijing_time().strftime('%Y-%m-%d %H:%M')}"
            return f"**{val}**{_fmt_delta(key)}"

        raw_url = f"https://gist.githubusercontent.com/{gist_user}/{self.gist_id}/raw/badge_{key}.json"
        encoded_url = urllib.parse.quote(raw_url, safe="")
        return (
            f"![{key}](https://img.shields.io/endpoint?url={encoded_url}&style={style})"
        )

    def generate_readme_stats(self, stats: dict, lang: str = "zh") -> str:
        """
        生成 README 统计区域 (精简版)

        Args:
            stats: 统计数据
            lang: 语言 ("zh" 中文, "en" 英文)
        """
        # 获取 Top 6 插件
        top_plugins = stats["posts"][:6]
        delta = self.get_stat_delta(stats)

        def fmt_delta(key: str) -> str:
            val = delta.get(key, 0)
            if val > 0:
                return f" <br><sub>(+{val}🚀)</sub>"
            return ""

        # 中英文文本
        texts = {
            "zh": {
                "title": "## 📊 社区统计",
                "author_header": "| 👤 作者 | 👥 粉丝 | ⭐ 积分 | 🏆 贡献 |",
                "header": "| 📝 发布 | ⬇️ 下载 | 👁️ 浏览 | 👍 点赞 | 💾 收藏 |",
                "top6_title": "### 🔥 热门插件 Top 6",
                "top6_header": "| 排名 | 插件 | 版本 | 下载 | 浏览 | 📅 更新 |",
                "full_stats": "*完整统计与趋势图请查看 [社区统计报告](./docs/community-stats.zh.md)*",
            },
            "en": {
                "title": "## 📊 Community Stats",
                "author_header": "| 👤 Author | 👥 Followers | ⭐ Points | 🏆 Contributions |",
                "header": "| 📝 Posts | ⬇️ Downloads | 👁️ Views | 👍 Upvotes | 💾 Saves |",
                "top6_title": "### 🔥 Top 6 Popular Plugins",
                "top6_header": "| Rank | Plugin | Version | Downloads | Views | 📅 Updated |",
                "full_stats": "*See full stats and charts in [Community Stats Report](./docs/community-stats.md)*",
            },
        }

        t = texts.get(lang, texts["en"])
        user = stats.get("user", {})

        lines = []
        lines.append("<!-- STATS_START -->")
        lines.append(t["title"])

        updated_key = "updated_zh" if lang == "zh" else "updated"
        lines.append(f"> {self.get_badge(updated_key, stats, user, delta)}")
        lines.append("")

        delta = self.get_stat_delta(stats)

        # 作者信息表格
        if user:
            username = user.get("username", "")
            profile_url = user.get("profile_url", "")
            lines.append(t["author_header"])
            lines.append("| :---: | :---: | :---: | :---: |")
            lines.append(
                f"| [{username}]({profile_url}) | {self.get_badge('followers', stats, user, delta)} | "
                f"{self.get_badge('points', stats, user, delta)} | {self.get_badge('contributions', stats, user, delta)} |"
            )
            lines.append("")

        # 统计面板
        lines.append(t["header"])
        lines.append("| :---: | :---: | :---: | :---: | :---: |")
        lines.append(
            f"| {self.get_badge('posts', stats, user, delta)} | {self.get_badge('downloads', stats, user, delta)} | "
            f"{self.get_badge('views', stats, user, delta)} | {self.get_badge('upvotes', stats, user, delta)} | {self.get_badge('saves', stats, user, delta)} |"
        )
        lines.append("")
        lines.append("")

        # Top 6 热门插件
        lines.append(t["top6_title"])
        lines.append(t["top6_header"])
        lines.append("| :---: | :--- | :---: | :---: | :---: | :---: |")

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
        for i, post in enumerate(top_plugins):
            idx = i + 1
            medal = medals[i] if i < len(medals) else str(idx)

            dl_cell = self.get_badge(f"p{idx}_dl", stats, user, delta, is_post=True)
            vw_cell = self.get_badge(f"p{idx}_vw", stats, user, delta, is_post=True)

            # 版本号使用静态 Shields.io 徽章
            ver = post["version"] if post["version"] else "N/A"
            ver_color = "blue" if post["version"] else "gray"
            ver_badge = (
                f"![v](https://img.shields.io/badge/v-{ver}-{ver_color}?style=flat)"
            )

            # 更新时间使用静态 Shields.io 徽章
            updated_str = post.get("updated_at", "")
            updated_badge = ""
            if updated_str:
                # 替换 - 为 -- 用于 shields.io url
                safe_date = updated_str.replace("-", "--")
                updated_badge = f"![updated](https://img.shields.io/badge/{safe_date}-gray?style=flat)"

            lines.append(
                f"| {medal} | [{post['title']}]({post['url']}) | {ver_badge} | {dl_cell} | {vw_cell} | {updated_badge} |"
            )

        lines.append("")

        # 插入全量趋势图 (Vega-Lite)
        activity_chart = self.generate_activity_chart(lang)
        if activity_chart:
            lines.append(activity_chart)
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
            content = re.sub(pattern, new_stats, content, flags=re.DOTALL)
        else:
            # 在简介段落之后插入统计区域
            lines = content.split("\n")
            insert_pos = 0
            found_intro = False

            for i, line in enumerate(lines):
                if line.startswith("# "):
                    continue
                if line.strip() == "":
                    continue
                if ("English" in line or "中文" in line) and "|" in line:
                    continue
                if not found_intro:
                    found_intro = True
                    continue
                if line.strip() == "" or line.startswith("#"):
                    insert_pos = i
                    break

            if insert_pos == 0:
                insert_pos = 3
            lines.insert(insert_pos, "")
            lines.insert(insert_pos + 1, new_stats)
            lines.insert(insert_pos + 2, "")
            content = "\n".join(lines)

        # 移除旧的底部图表 (如果有的话)
        chart_pattern = r"<!-- ACTIVITY_CHART_START -->.*?<!-- ACTIVITY_CHART_END -->"
        if re.search(chart_pattern, content, re.DOTALL):
            content = re.sub(chart_pattern, "", content, flags=re.DOTALL)
            # 清理可能产生的多余空行
            content = re.sub(r"\n{3,}", "\n\n", content)

        # 写回文件
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ README 已更新: {readme_path}")

    def generate_activity_chart(self, lang: str = "zh") -> str:
        """生成 Vega-Lite 趋势图 (内嵌数据，确保稳定性)"""
        history = self.load_history()
        if len(history) < 3:
            return ""

        # 准备数据点
        values = []
        for item in history:
            values.append({"date": item["date"], "downloads": item["total_downloads"]})

        title = "Total Downloads Trend" if lang == "en" else "总下载量累计趋势"

        # Vega-Lite Spec (内嵌数据)
        vl_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": title,
            "width": 800,
            "height": 200,
            "padding": 5,
            "background": "transparent",
            "config": {
                "view": {"stroke": "transparent"},
                "axis": {"domain": False, "grid": False},
            },
            "data": {"values": values},
            "mark": {
                "type": "area",
                "line": {"color": "#2563eb"},
                "color": {
                    "x1": 1,
                    "y1": 1,
                    "x2": 1,
                    "y2": 0,
                    "gradient": "linear",
                    "stops": [
                        {"offset": 0, "color": "white"},
                        {"offset": 1, "color": "#2563eb"},
                    ],
                },
            },
            "encoding": {
                "x": {
                    "field": "date",
                    "type": "temporal",
                    "axis": {"format": "%m-%d", "title": None, "labelColor": "#666"},
                },
                "y": {
                    "field": "downloads",
                    "type": "quantitative",
                    "axis": {"title": None, "labelColor": "#666"},
                },
            },
        }

        try:
            # Kroki encoding for Vega-Lite
            json_spec = json.dumps(vl_spec)
            compressed = zlib.compress(json_spec.encode("utf-8"), level=9)
            encoded = base64.urlsafe_b64encode(compressed).decode("utf-8")
            url = f"https://kroki.io/vegalite/svg/{encoded}"
            return f"### 📈 {title}\n![Activity]({url})"
        except Exception:
            return ""


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

    # 获取 Gist 配置 (用于存储历史记录)
    gist_token = os.getenv("GIST_TOKEN")
    gist_id = os.getenv("GIST_ID")

    # 初始化
    stats_client = OpenWebUIStats(api_key, user_id, gist_token, gist_id)
    print(f"🔍 用户 ID: {stats_client.user_id}")
    if gist_id:
        print(f"📦 Gist 存储已启用: {gist_id}")

    # 获取所有帖子
    print("📥 正在获取帖子数据...")
    posts = stats_client.get_all_posts()
    print(f"✅ 获取到 {len(posts)} 个帖子")

    # 生成统计
    stats = stats_client.generate_stats(posts)

    # 保存历史快照
    stats_client.save_history(stats)

    # 打印到终端
    stats_client.print_stats(stats)

    # 保存 Markdown 报告 (中英文双版本)
    script_dir = Path(__file__).parent.parent

    # 中文报告
    md_zh_path = script_dir / "docs" / "community-stats.zh.md"
    md_zh_content = stats_client.generate_markdown(stats, lang="zh")
    with open(md_zh_path, "w", encoding="utf-8") as f:
        f.write(md_zh_content)
    print(f"\n✅ 中文报告已保存到: {md_zh_path}")

    # 英文报告
    md_en_path = script_dir / "docs" / "community-stats.md"
    md_en_content = stats_client.generate_markdown(stats, lang="en")
    with open(md_en_path, "w", encoding="utf-8") as f:
        f.write(md_en_content)
    print(f"✅ 英文报告已保存到: {md_en_path}")

    # 保存 JSON 数据
    json_path = script_dir / "docs" / "community-stats.json"
    stats_client.save_json(stats, str(json_path))

    # 生成 Shields.io endpoint JSON (用于动态徽章)
    badges_dir = script_dir / "docs" / "badges"

    # 生成徽章
    stats_client.generate_shields_endpoints(stats, str(badges_dir))

    # 更新 README 文件
    readme_path = script_dir / "README.md"
    readme_cn_path = script_dir / "README_CN.md"
    stats_client.update_readme(stats, str(readme_path), lang="en")
    stats_client.update_readme(stats, str(readme_cn_path), lang="zh")

    return 0


if __name__ == "__main__":
    exit(main())
