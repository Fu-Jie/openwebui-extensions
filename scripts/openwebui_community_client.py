"""
OpenWebUI Community Client
统一封装所有与 OpenWebUI 官方社区 (openwebui.com) 的 API 交互。

功能：
- 获取用户发布的插件/帖子
- 更新插件内容和元数据
- 版本比较
- 同步插件 ID

使用方法：
    from openwebui_community_client import OpenWebUICommunityClient

    client = OpenWebUICommunityClient(api_key="your_api_key")
    posts = client.get_all_posts()
"""

import os
import re
import json
import base64
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any, Tuple

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class OpenWebUICommunityClient:
    """OpenWebUI 官方社区 API 客户端"""

    BASE_URL = "https://api.openwebui.com/api/v1"

    def __init__(self, api_key: str, user_id: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: OpenWebUI API Key (JWT Token)
            user_id: 用户 ID，如果为 None 则从 token 中解析
        """
        self.api_key = api_key
        self.user_id = user_id or self._parse_user_id_from_token(api_key)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _parse_user_id_from_token(self, token: str) -> Optional[str]:
        """从 JWT Token 中解析用户 ID"""
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                payload = parts[1]
                # 添加 padding
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += "=" * padding
                decoded = base64.urlsafe_b64decode(payload)
                data = json.loads(decoded)
                return data.get("id") or data.get("sub")
        except Exception:
            pass
        return None

    # ========== 帖子/插件获取 ==========

    def get_user_posts(self, sort: str = "new", page: int = 1) -> List[Dict]:
        """
        获取用户发布的帖子列表

        Args:
            sort: 排序方式 (new/top/hot)
            page: 页码

        Returns:
            帖子列表
        """
        url = f"{self.BASE_URL}/posts/user/{self.user_id}?sort={sort}&page={page}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_all_posts(self, sort: str = "new") -> List[Dict]:
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

    def get_post(self, post_id: str) -> Optional[Dict]:
        """
        获取单个帖子详情

        Args:
            post_id: 帖子 ID

        Returns:
            帖子数据，如果不存在返回 None
        """
        try:
            url = f"{self.BASE_URL}/posts/{post_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    # ========== 帖子/插件更新 ==========

    def update_post(self, post_id: str, post_data: Dict) -> bool:
        """
        更新帖子

        Args:
            post_id: 帖子 ID
            post_data: 完整的帖子数据

        Returns:
            是否成功
        """
        url = f"{self.BASE_URL}/posts/{post_id}/update"
        response = requests.post(url, headers=self.headers, json=post_data)
        response.raise_for_status()
        return True

    def update_plugin(
        self,
        post_id: str,
        source_code: str,
        readme_content: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        更新插件（代码 + README + 元数据）

        Args:
            post_id: 帖子 ID
            source_code: 插件源代码
            readme_content: README 内容（用于社区页面展示）
            metadata: 插件元数据（title, version, description 等）

        Returns:
            是否成功
        """
        post_data = self.get_post(post_id)
        if not post_data:
            return False

        # 确保结构存在
        if "data" not in post_data:
            post_data["data"] = {}
        if "function" not in post_data["data"]:
            post_data["data"]["function"] = {}
        if "meta" not in post_data["data"]["function"]:
            post_data["data"]["function"]["meta"] = {}
        if "manifest" not in post_data["data"]["function"]["meta"]:
            post_data["data"]["function"]["meta"]["manifest"] = {}

        # 更新源代码
        post_data["data"]["function"]["content"] = source_code

        # 更新 README（社区页面展示内容）
        if readme_content:
            post_data["content"] = readme_content

        # 更新元数据
        if metadata:
            post_data["data"]["function"]["meta"]["manifest"].update(metadata)
            if "title" in metadata:
                post_data["title"] = metadata["title"]
                post_data["data"]["function"]["name"] = metadata["title"]
            if "description" in metadata:
                post_data["data"]["function"]["meta"]["description"] = metadata[
                    "description"
                ]

        return self.update_post(post_id, post_data)

    # ========== 版本比较 ==========

    def get_remote_version(self, post_id: str) -> Optional[str]:
        """
        获取远程插件版本

        Args:
            post_id: 帖子 ID

        Returns:
            版本号，如果不存在返回 None
        """
        post_data = self.get_post(post_id)
        if not post_data:
            return None
        return (
            post_data.get("data", {})
            .get("function", {})
            .get("meta", {})
            .get("manifest", {})
            .get("version")
        )

    def version_needs_update(self, post_id: str, local_version: str) -> bool:
        """
        检查是否需要更新

        Args:
            post_id: 帖子 ID
            local_version: 本地版本号

        Returns:
            如果本地版本与远程不同，返回 True
        """
        remote_version = self.get_remote_version(post_id)
        if not remote_version:
            return True  # 远程不存在，需要更新
        return local_version != remote_version

    # ========== 插件发布 ==========

    def publish_plugin_from_file(
        self, file_path: str, force: bool = False
    ) -> Tuple[bool, str]:
        """
        从文件发布插件

        Args:
            file_path: 插件文件路径
            force: 是否强制更新（忽略版本检查）

        Returns:
            (是否成功, 消息)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = self._parse_frontmatter(content)
        if not metadata:
            return False, "No frontmatter found"

        post_id = metadata.get("openwebui_id") or metadata.get("post_id")
        if not post_id:
            return False, "No openwebui_id found"

        local_version = metadata.get("version")

        # 版本检查
        if not force and local_version:
            if not self.version_needs_update(post_id, local_version):
                return True, f"Skipped: version {local_version} matches remote"

        # 查找 README
        readme_content = self._find_readme(file_path)

        # 更新
        success = self.update_plugin(
            post_id=post_id,
            source_code=content,
            readme_content=readme_content or metadata.get("description", ""),
            metadata=metadata,
        )

        if success:
            return True, f"Updated to version {local_version}"
        return False, "Update failed"

    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """解析插件文件的 frontmatter"""
        match = re.search(r'^\s*"""\n(.*?)\n"""', content, re.DOTALL)
        if not match:
            match = re.search(r'"""\n(.*?)\n"""', content, re.DOTALL)
            if not match:
                return {}

        frontmatter = match.group(1)
        meta = {}
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
        return meta

    def _find_readme(self, plugin_file_path: str) -> Optional[str]:
        """查找插件对应的 README 文件"""
        plugin_dir = os.path.dirname(plugin_file_path)
        base_name = os.path.basename(plugin_file_path).lower()

        # 确定优先顺序
        if base_name.endswith("_cn.py"):
            readme_files = ["README_CN.md", "README.md"]
        else:
            readme_files = ["README.md", "README_CN.md"]

        for readme_name in readme_files:
            readme_path = os.path.join(plugin_dir, readme_name)
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    return f.read()
        return None

    # ========== 统计功能 ==========

    def generate_stats(self, posts: List[Dict]) -> Dict:
        """
        生成统计数据

        Args:
            posts: 帖子列表

        Returns:
            统计数据字典
        """
        stats = {
            "total_posts": len(posts),
            "total_downloads": 0,
            "total_likes": 0,
            "posts_by_type": {},
            "posts_detail": [],
            "generated_at": datetime.now(BEIJING_TZ).isoformat(),
        }

        for post in posts:
            downloads = post.get("downloadCount", 0)
            likes = post.get("likeCount", 0)
            post_type = post.get("type", "unknown")

            stats["total_downloads"] += downloads
            stats["total_likes"] += likes
            stats["posts_by_type"][post_type] = (
                stats["posts_by_type"].get(post_type, 0) + 1
            )

            stats["posts_detail"].append(
                {
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "type": post_type,
                    "downloads": downloads,
                    "likes": likes,
                    "created_at": post.get("createdAt"),
                    "updated_at": post.get("updatedAt"),
                }
            )

        # 按下载量排序
        stats["posts_detail"].sort(key=lambda x: x["downloads"], reverse=True)

        return stats


# 便捷函数
def get_client(api_key: Optional[str] = None) -> OpenWebUICommunityClient:
    """
    获取客户端实例

    Args:
        api_key: API Key，如果为 None 则从环境变量获取

    Returns:
        OpenWebUICommunityClient 实例
    """
    key = api_key or os.environ.get("OPENWEBUI_API_KEY")
    if not key:
        raise ValueError("OPENWEBUI_API_KEY not set")
    return OpenWebUICommunityClient(key)
