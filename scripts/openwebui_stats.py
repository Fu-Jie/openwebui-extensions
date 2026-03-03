#!/usr/bin/env python3
"""
OpenWebUI community stats utility.

Collect and summarize your published posts/plugins on openwebui.com.

Usage:
    1. Set environment variables:
       - OPENWEBUI_API_KEY: required
       - OPENWEBUI_USER_ID: optional (auto-resolved from /api/v1/auths/ when missing)
    2. Run: python scripts/openwebui_stats.py

How to get API key:
    Visit https://openwebui.com/settings/api and create a key (starts with sk-).

How to get user ID (optional):
    Read the `id` field from /api/v1/auths/, format example:
    b15d1348-4347-42b4-b815-e053342d6cb0
"""

import os
import json
import requests
import zlib
import base64
import re
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

# Beijing timezone (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def get_beijing_time() -> datetime:
    """Get current time in Beijing timezone."""
    return datetime.now(BEIJING_TZ)


# Try loading local .env file (if python-dotenv is installed)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class OpenWebUIStats:
    """OpenWebUI community stats utility."""

    BASE_URL = "https://api.openwebui.com/api/v1"

    def __init__(
        self,
        api_key: str,
        user_id: Optional[str] = None,
        gist_token: Optional[str] = None,
        gist_id: Optional[str] = None,
    ):
        """
        Initialize the stats utility

        Args:
            api_key: OpenWebUI API Key (JWT Token)
            user_id: User ID; if None, will be parsed from token
            gist_token: GitHub Personal Access Token (for reading/writing Gist)
            gist_id: GitHub Gist ID
        """
        self.api_key = api_key
        self.user_id = user_id or self._parse_user_id_from_token(api_key)
        self.gist_token = gist_token
        self.gist_id = gist_id or "db3d95687075a880af6f1fba76d679c6"
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

    # Types considered downloadable (included in total view/download stats)
    DOWNLOADABLE_TYPES = [
        "action",
        "filter",
        "pipe",
        "tool",
        "function",
        "prompt",
        "model",
    ]

    TYPE_ALIASES = {
        "tools": "tool",
    }

    def _normalize_post_type(self, post_type: str) -> str:
        """Normalize post type to avoid synonym type splitting in statistics."""
        normalized = str(post_type or "").strip().lower()
        return self.TYPE_ALIASES.get(normalized, normalized)

    def load_history(self) -> list:
        """Load history records (merge Gist + local file, keep the one with more records)"""
        gist_history = []
        local_history = []

        # 1. Try loading from Gist
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
                        gist_history = json.loads(content)
                        print(
                            f"✅ Loaded history from Gist ({len(gist_history)} records)"
                        )
            except Exception as e:
                print(f"⚠️ Failed to load history from Gist: {e}")

        # 2. Also load from local file
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    local_history = json.load(f)
                    print(
                        f"✅ Loaded history from local file ({len(local_history)} records)"
                    )
            except Exception as e:
                print(f"⚠️ Failed to load local history: {e}")

        # 3. Merge two sources (by date as key, keep newer when conflicts)
        hist_dict = {}
        for item in gist_history:
            hist_dict[item["date"]] = item
        for item in local_history:
            hist_dict[item["date"]] = (
                item  # Local data overrides Gist (more likely to be latest)
            )

        history = sorted(hist_dict.values(), key=lambda x: x["date"])
        print(f"📊 Merged history records: {len(history)}")

        # 4. If merged data is still too short, try rebuilding from Git
        if len(history) < 5 and os.path.isdir(".git"):
            print("📉 History too short, attempting Git rebuild...")
            git_history = self.rebuild_history_from_git()

            if len(git_history) > len(history):
                print(f"✅ Rebuilt history from Git: {len(git_history)} records")
                for item in git_history:
                    if item["date"] not in hist_dict:
                        hist_dict[item["date"]] = item
                history = sorted(hist_dict.values(), key=lambda x: x["date"])

        # 5. If there is new data, sync back to Gist
        if len(history) > len(gist_history) and self.gist_token and self.gist_id:
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
                    print(f"✅ History synced to Gist ({len(history)} records)")
                else:
                    print(f"⚠️ Gist sync failed: {resp.status_code}")
            except Exception as e:
                print(f"⚠️ Error syncing history to Gist: {e}")

        return history

    def save_history(self, stats: dict):
        """Save current snapshot to history (prioritize Gist, fallback to local)"""
        history = self.load_history()
        today = get_beijing_time().strftime("%Y-%m-%d")

        # Build detailed snapshot (including each plugin's download count)
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

        # Update or append data point
        updated = False
        for i, item in enumerate(history):
            if item.get("date") == today:
                history[i] = snapshot
                updated = True
                break
        if not updated:
            history.append(snapshot)

        # Limit length (90 days)
        history = history[-90:]

        # Try saving to Gist
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
                    print(f"✅ History synced to Gist ({self.gist_id})")
                    # If sync succeeds, do not save to local to reduce commit pressure
                    return
            except Exception as e:
                print(f"⚠️ Failed to sync to Gist: {e}")

        # Fallback: save to local
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"✅ History updated to local ({today})")

    def get_stat_delta(self, stats: dict) -> dict:
        """Calculate growth relative to last recorded snapshot (24h delta)"""
        history = self.load_history()
        if not history:
            return {}

        today = get_beijing_time().strftime("%Y-%m-%d")
        prev = None

        # Find last data point from a different day as baseline
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
        """Resolve the post category type"""
        top_type = post.get("type")
        function_data = post.get("data", {}) or {}
        function_obj = function_data.get("function", {}) or {}
        meta = function_obj.get("meta", {}) or {}
        manifest = meta.get("manifest", {}) or {}

        # Category identification priority:
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

        post_type = self._normalize_post_type(post_type)

        # Unified and heuristic identification logic
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
            elif "tool" in all_metadata:
                post_type = "tool"

        return self._normalize_post_type(post_type)

    def rebuild_history_from_git(self) -> list:
        """Rebuild statistics from Git commit history"""
        history = []
        try:
            # Rebuild from Git history of docs/community-stats.json (has richest history)
            # Format: hash date
            target = "docs/community-stats.json"
            cmd = [
                "git",
                "log",
                "--pretty=format:%H %ad",
                "--date=short",
                target,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            commits = result.stdout.strip().splitlines()
            print(f"🔍 Found {len(commits)} commits modifying stats file")

            seen_dates = set()

            # Process from oldest to newest (git log defaults to newest first, so reverse)
            # The order doesn't really matter as long as we sort at the end
            for line in reversed(commits):  # Process from oldest to newest
                parts = line.split()
                if len(parts) < 2:
                    continue

                commit_hash = parts[0]
                commit_date = parts[1]  # YYYY-MM-DD

                if commit_date in seen_dates:
                    continue
                seen_dates.add(commit_date)

                # Read file content at this commit
                # Note: The file name in git show needs to be relative to the repo root
                show_cmd = ["git", "show", f"{commit_hash}:{target}"]
                show_res = subprocess.run(
                    show_cmd, capture_output=True, text=True, check=True
                )

                if show_res.returncode == 0:
                    try:
                        # Git history might contain the full history JSON, or just a single snapshot.
                        # We need to handle both cases.
                        content = show_res.stdout.strip()
                        if content.startswith("[") and content.endswith("]"):
                            # It's a full history list, take the last item
                            data_list = json.loads(content)
                            if data_list:
                                data = data_list[-1]
                            else:
                                continue
                        else:
                            # It's a single snapshot
                            data = json.loads(content)

                        # Ensure the date matches the commit date, or use the one from data if available
                        entry_date = data.get("date", commit_date)
                        if entry_date != commit_date:
                            print(
                                f"⚠️ Date mismatch for commit {commit_hash}: file date {entry_date}, commit date {commit_date}. Using commit date."
                            )
                            entry_date = commit_date

                        history.append(
                            {
                                "date": entry_date,
                                "total_downloads": data.get("total_downloads", 0),
                                "total_views": data.get("total_views", 0),
                                "total_upvotes": data.get("total_upvotes", 0),
                                "total_saves": data.get("total_saves", 0),
                                "followers": data.get("followers", 0),
                                "points": data.get("points", 0),
                                "contributions": data.get("contributions", 0),
                                "posts": data.get(
                                    "posts", {}
                                ),  # Include individual post stats
                            }
                        )
                    except json.JSONDecodeError:
                        print(
                            f"⚠️ Could not decode JSON from commit {commit_hash} for {self.history_file}"
                        )
                    except Exception as e:
                        print(f"⚠️ Error processing commit {commit_hash}: {e}")

            # Sort by date to ensure chronological order
            history.sort(key=lambda x: x["date"])
            return history

        except subprocess.CalledProcessError as e:
            print(
                f"⚠️ Git command failed: {e.cmd}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            )
            return []
        except Exception as e:
            print(f"⚠️ Error rebuilding history from git: {e}")
            return []

    def _parse_user_id_from_token(self, token: str) -> str:
        """Parse user ID from JWT Token"""
        import base64

        if not token or token.startswith("sk-"):
            return ""

        try:
            # JWT format: header.payload.signature
            payload = token.split(".")[1]
            # Add padding
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return data.get("id", "")
        except Exception as e:
            print(f"⚠️ Failed to parse user ID from token: {e}")
            return ""

    def resolve_user_id(self) -> str:
        """Auto-resolve current user ID via community API (for sk- type API keys)"""
        if self.user_id:
            return self.user_id

        try:
            resp = self.session.get(f"{self.BASE_URL}/auths/", timeout=20)
            if resp.status_code == 200:
                data = resp.json() if resp.text else {}
                resolved = str(data.get("id", "")).strip()
                if resolved:
                    self.user_id = resolved
                    return resolved
            else:
                print(f"⚠️ Failed to auto-resolve user ID: HTTP {resp.status_code}")
        except Exception as e:
            print(f"⚠️ Exception while auto-resolving user ID: {e}")

        return ""

    def generate_mermaid_chart(self, stats: dict = None, lang: str = "zh") -> str:
        """Generate dynamic Mermaid chart links with Kroki server-side rendering (zero commit)"""
        history = self.load_history()
        if not history:
            return ""

        # Multi-language labels
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
        Fetch list of posts published by the user

        Args:
            sort: Sort order (new/top/hot)
            page: Page number

        Returns:
            List of posts
        """
        url = f"{self.BASE_URL}/posts/users/{self.user_id}"
        params = {"sort": sort, "page": page}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_all_posts(self, sort: str = "new") -> list:
        """Fetch all posts (automatic pagination)"""
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
        """Generate statistics"""
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
            "user": {},  # User info
        }

        # Extract user info from first post
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

            # Accumulate statistics
            post_downloads = post.get("downloads", 0)
            post_views = post.get("views", 0)

            stats["total_downloads"] += post_downloads
            stats["total_upvotes"] += post.get("upvotes", 0)
            stats["total_downvotes"] += post.get("downvotes", 0)
            stats["total_saves"] += post.get("saveCount", 0)
            stats["total_comments"] += post.get("commentCount", 0)

            # Key: total views do not include non-downloadable types (e.g., post, review)
            if post_type in self.DOWNLOADABLE_TYPES or post_downloads > 0:
                stats["total_views"] += post_views

            if post_type not in stats["by_type"]:
                stats["by_type"][post_type] = 0
            stats["by_type"][post_type] += 1

            # Individual post information
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

        # Sort by download count
        stats["posts"].sort(key=lambda x: x["downloads"], reverse=True)

        return stats

    def print_stats(self, stats: dict):
        """Print statistics report to terminal"""
        print("\n" + "=" * 60)
        print("📊 OpenWebUI Community Statistics Report")
        print("=" * 60)
        print(
            f"📅 Generated (Beijing time): {get_beijing_time().strftime('%Y-%m-%d %H:%M')}"
        )
        print()

        # Overview
        print("📈 Overview")
        print("-" * 40)
        print(f"  📝 Posts: {stats['total_posts']}")
        print(f"  ⬇️  Total Downloads: {stats['total_downloads']}")
        print(f"  👁️  Total Views: {stats['total_views']}")
        print(f"  👍 Total Upvotes: {stats['total_upvotes']}")
        print(f"  💾 Total Saves: {stats['total_saves']}")
        print(f"  💬 Total Comments: {stats['total_comments']}")
        print()

        # By type
        print("📂 By Type")
        print("-" * 40)
        for post_type, count in stats["by_type"].items():
            print(f"  • {post_type}: {count}")
        print()

        # Detailed list
        print("📋 Posts List (sorted by downloads)")
        print("-" * 60)

        # Header
        print(f"{'Rank':<4} {'Title':<30} {'Downloads':<8} {'Views':<8} {'Upvotes':<6}")
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
        """Generate safe filename key (MD5 hash) to avoid Chinese character issues"""
        import hashlib

        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def generate_markdown(self, stats: dict, lang: str = "zh") -> str:
        """
        Generate Markdown format report (fully dynamic badges and Kroki charts)

        Args:
            stats: Statistics data
            lang: Language ("zh" Chinese, "en" English)
        """
        # Get delta data
        delta = self.get_stat_delta(stats)

        # Bilingual text
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

        # 按类型分类 (使用徽章)
        md.append(t["type_title"])
        md.append("")

        type_colors = {
            "post": "blue",
            "filter": "brightgreen",
            "action": "orange",
            "pipe": "blueviolet",
            "tool": "teal",
            "pipeline": "purple",
            "review": "yellow",
            "prompt": "lightgrey",
        }

        for post_type, count in stats["by_type"].items():
            color = type_colors.get(post_type, "gray")
            badge = f"![{post_type}](https://img.shields.io/badge/{post_type}-{count}-{color})"
            md.append(f"- {badge}")
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

            # 版本号使用动态 Shields.io 徽章 (由于列表太长，我们这次没给所有 post 生成单独的 version json)
            # 不过实际上 upload_gist_badges 是给 top 6 生成的。
            # 对于完整列表，还是暂时用静态吧，避免要把几百个 version json 都生成出来传到 Gist
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
        """Save data in JSON format"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON data saved to: {filepath}")

    def generate_shields_endpoints(self, stats: dict, output_dir: str = "docs/badges"):
        """
        Generate Shields.io endpoint JSON files

        Args:
            stats: Statistics data
            output_dir: Output directory
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        def format_number(n: int) -> str:
            """Format number to readable format"""
            if n >= 1000000:
                return f"{n/1000000:.1f}M"
            elif n >= 1000:
                return f"{n/1000:.1f}k"
            return str(n)

        # Badge data
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
                print(f"⚠️ Badge generation failed: {e}")

        print(f"✅ Shields.io endpoints saved to: {output_dir}/")

    def upload_gist_badges(self, stats: dict):
        """Generate and upload Gist badge data (for Shields.io Endpoint)"""
        if not (self.gist_token and self.gist_id):
            return

        delta = self.get_stat_delta(stats)

        # Define badge config {key: (label, value, color)}
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
                diff = 0  # Avoid dict vs int comparison error with 'posts' key

            message = f"{val}"
            if diff > 0:
                message += f" (+{diff}🚀)"
            elif diff < 0:
                message += f" ({diff})"

            # Build Shields.io endpoint JSON
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

        # Generate top 6 plugins badges (based on slots p1, p2...)
        post_deltas = delta.get("posts", {})
        for i, post in enumerate(stats.get("posts", [])[:6]):
            idx = i + 1
            diff = post_deltas.get(post["slug"], 0)

            # Downloads badge
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
            # 版本号徽章
            ver = post.get("version", "N/A") or "N/A"
            ver_color = "blue" if post.get("version") else "gray"
            files_payload[f"badge_p{idx}_version.json"] = {
                "content": json.dumps(
                    {
                        "schemaVersion": 1,
                        "label": "v",
                        "message": ver,
                        "color": ver_color,
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
            if isinstance(val, dict):
                return ""
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

            # 版本号使用动态 Shields.io 徽章
            ver_badge = self.get_badge(
                f"p{idx}_version", stats, user, delta, is_post=True
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

    def update_docs_chart(self, doc_path: str, lang: str = "zh"):
        """更新文档中的图表"""
        import re

        if not os.path.exists(doc_path):
            return

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 生成新的图表 Markdown
        new_chart = self.generate_activity_chart(lang)
        if not new_chart:
            return

        # 匹配 ### 📈 ... \n\n![...](...)
        # 兼容 docs 中使用 Trend 或 Activity 作为 alt text
        pattern = r"(### 📈.*?\n)(!\[.*?\]\(.*?\))"

        if re.search(pattern, content, re.DOTALL):
            # generate_activity_chart 返回的是完整块: ### 📈 Title\n![Activity](url)
            # 我们直接用新块替换整个旧块
            content = re.sub(pattern, new_chart, content, flags=re.DOTALL)

            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 文档图表已更新: {doc_path}")

    def upload_chart_svg(self):
        """生成 Vega-Lite SVG 并上传到 Gist (作为独立文件)"""
        print("🚀 Starting chart SVG generation process...")

        if not (self.gist_token and self.gist_id):
            print("⚠️ Skipping chart upload: GIST_TOKEN or GIST_ID missing")
            return

        history = self.load_history()
        print(f"📊 History records loaded: {len(history)}")

        if len(history) < 1:
            print("⚠️ Skipping chart upload: no history")
            return

        # 准备数据点
        values = []
        for item in history:
            values.append({"date": item["date"], "downloads": item["total_downloads"]})

        # Vega-Lite Spec
        vl_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": "Total Downloads Trend",
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
            # 1. 使用 POST 请求 Kroki (避免 URL 过长问题)
            json_spec = json.dumps(vl_spec)
            kroki_url = "https://kroki.io/vegalite/svg"

            print(f"📥 Generating chart via Kroki (POST)...")
            resp = requests.post(kroki_url, data=json_spec)

            if resp.status_code != 200:
                print(f"⚠️ Kroki request failed: {resp.status_code}")
                # 尝试打印一点错误信息
                print(f"Response: {resp.text[:200]}")
                return

            svg_content = resp.text
            print(f"✅ Kroki SVG generated ({len(svg_content)} bytes)")

            # 3. 上传到 Gist
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {"Authorization": f"token {self.gist_token}"}
            payload = {"files": {"chart.svg": {"content": svg_content}}}
            resp = requests.patch(url, headers=headers, json=payload)
            if resp.status_code == 200:
                print(f"✅ 图表 SVG 已同步至 Gist: chart.svg")
            else:
                print(f"⚠️ Gist upload failed: {resp.status_code} {resp.text[:200]}")

        except Exception as e:
            print(f"⚠️ 上传图表失败: {e}")

    def generate_activity_chart(self, lang: str = "zh") -> str:
        """生成 Markdown 图表链接 (使用 Gist Raw URL，固定链接)"""
        if not self.gist_id:
            return ""

        title = "Total Downloads Trend" if lang == "en" else "总下载量累计趋势"

        # 使用不带 commit hash 的 raw 链接 (指向最新版)
        # 添加时间戳参数避免 GitHub 缓存太久
        # 注意：README 中如果不加时间戳，GitHub 可能会缓存图片。
        # 但我们希望 README 不变。GitHub 的 camo 缓存机制比较激进。
        # 这里的权衡是：要么每天 commit 改时间戳，要么忍受一定的缓存延迟。
        # 实际上 GitHub 对 raw.githubusercontent.com 的缓存大概是 5 分钟 (对于 gist)。
        # 而 camo (github user content proxy) 可能会缓存更久。
        # 我们可以用 purge 缓存的方法，或者接受这个延迟。
        # 对用户来说，昨天的图表和今天的图表区别不大，延迟一天都无所谓。

        # 使用 cache-control: no-cache 的策略通常对 camo 无效。
        # 最佳策略是：链接本身不带 query param (保证 README 文本不变)
        # 相信 GitHub 会最终更新它。

        gist_user = (
            "Fu-Jie"  # Replace with actual username if needed, or parse from somewhere
        )
        # 更好的方式是用 gist_id 直接访问 (不需要用户名，但 Raw 需要)
        # 格式: https://gist.githubusercontent.com/<user>/<id>/raw/chart.svg

        url = f"https://gist.githubusercontent.com/{gist_user}/{self.gist_id}/raw/chart.svg"

        return f"### 📈 {title}\n![Activity]({url})"


def main():
    """CLI entry point."""
    # Load runtime config
    api_key = os.getenv("OPENWEBUI_API_KEY")
    user_id = os.getenv("OPENWEBUI_USER_ID")

    if not api_key:
        print("❌ Error: OPENWEBUI_API_KEY is not set")
        print("Please set environment variable:")
        print("  export OPENWEBUI_API_KEY='your_api_key_here'")
        return 1

    if not user_id:
        print("ℹ️ OPENWEBUI_USER_ID not set, attempting auto-resolve via API key...")

    # Gist config (optional, for badges/history sync)
    gist_token = os.getenv("GIST_TOKEN")
    gist_id = os.getenv("GIST_ID")

    # Initialize client
    stats_client = OpenWebUIStats(api_key, user_id, gist_token, gist_id)

    if not stats_client.user_id:
        stats_client.resolve_user_id()

    if not stats_client.user_id:
        print("❌ Error: failed to auto-resolve OPENWEBUI_USER_ID")
        print("Please set environment variable:")
        print("  export OPENWEBUI_USER_ID='your_user_id_here'")
        print("\nTip: user id is the 'id' field returned by /api/v1/auths/")
        print("     e.g. b15d1348-4347-42b4-b815-e053342d6cb0")
        return 1

    print(f"🔍 User ID: {stats_client.user_id}")
    if gist_id:
        print(f"📦 Gist storage enabled: {gist_id}")

    # Fetch posts
    print("📥 Fetching posts...")
    posts = stats_client.get_all_posts()
    print(f"✅ Retrieved {len(posts)} posts")

    # Build stats
    stats = stats_client.generate_stats(posts)

    # Save history snapshot
    stats_client.save_history(stats)

    # Print terminal report
    stats_client.print_stats(stats)

    # Save markdown reports (zh/en)
    script_dir = Path(__file__).parent.parent

    # Chinese report
    md_zh_path = script_dir / "docs" / "community-stats.zh.md"
    md_zh_content = stats_client.generate_markdown(stats, lang="zh")
    with open(md_zh_path, "w", encoding="utf-8") as f:
        f.write(md_zh_content)
    print(f"\n✅ Chinese report saved to: {md_zh_path}")

    # English report
    md_en_path = script_dir / "docs" / "community-stats.md"
    md_en_content = stats_client.generate_markdown(stats, lang="en")
    with open(md_en_path, "w", encoding="utf-8") as f:
        f.write(md_en_content)
    print(f"✅ English report saved to: {md_en_path}")

    # Save JSON snapshot
    json_path = script_dir / "docs" / "community-stats.json"
    stats_client.save_json(stats, str(json_path))

    # Generate Shields.io endpoint JSON (dynamic badges)
    badges_dir = script_dir / "docs" / "badges"

    # Generate badges
    stats_client.generate_shields_endpoints(stats, str(badges_dir))

    # Generate and upload SVG chart (if Gist is configured)
    stats_client.upload_chart_svg()

    # Update README files
    readme_path = script_dir / "README.md"
    readme_cn_path = script_dir / "README_CN.md"
    stats_client.update_readme(stats, str(readme_path), lang="en")
    stats_client.update_readme(stats, str(readme_cn_path), lang="zh")

    # Update charts in docs pages
    stats_client.update_docs_chart(str(md_en_path), lang="en")
    stats_client.update_docs_chart(str(md_zh_path), lang="zh")

    return 0


if __name__ == "__main__":
    exit(main())
