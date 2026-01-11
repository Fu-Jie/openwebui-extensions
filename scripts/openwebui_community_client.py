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
        # 如果没有 user_id，尝试通过 API 获取
        if not self.user_id:
            self.user_id = self._get_user_id_from_api()

    def _parse_user_id_from_token(self, token: str) -> Optional[str]:
        """从 JWT Token 中解析用户 ID"""
        # sk- 开头的是 API Key，无法解析用户 ID
        if token.startswith("sk-"):
            return None
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

    def _get_user_id_from_api(self) -> Optional[str]:
        """通过 API 获取当前用户 ID"""
        try:
            url = f"{self.BASE_URL}/auths/"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("id")
        except Exception:
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
        url = f"{self.BASE_URL}/posts/users/{self.user_id}?sort={sort}&page={page}"
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

    # ========== 帖子/插件创建 ==========

    def create_post(
        self,
        title: str,
        content: str,
        post_type: str = "function",
        data: Optional[Dict] = None,
        media: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """
        创建新帖子

        Args:
            title: 帖子标题
            content: 帖子内容（README/描述）
            post_type: 帖子类型 (function/tool/filter/pipeline)
            data: 插件数据结构
            media: 图片 URL 列表

        Returns:
            创建成功返回帖子数据，失败返回 None
        """
        try:
            url = f"{self.BASE_URL}/posts/create"

            # 将字符串 URL 转换为字典格式 (API 要求)
            media_list = []
            if media:
                for item in media:
                    if isinstance(item, str):
                        media_list.append({"url": item})
                    elif isinstance(item, dict):
                        media_list.append(item)

            payload = {
                "title": title,
                "content": content,
                "type": post_type,
                "data": data or {},
                "media": media_list,
            }
            print(f"  [DEBUG] Payload keys: {list(payload.keys())}")
            print(
                f"  [DEBUG] media format: {media_list[:1] if media_list else 'empty'}"
            )
            response = requests.post(url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"  [DEBUG] Response status: {response.status_code}")
                print(f"  [DEBUG] Response body: {response.text[:500]}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Error creating post: {e}")
            return None

    def create_plugin(
        self,
        title: str,
        source_code: str,
        readme_content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        media_urls: Optional[List[str]] = None,
        plugin_type: str = "action",
    ) -> Optional[str]:
        """
        创建新插件帖子

        Args:
            title: 插件标题
            source_code: 插件源代码
            readme_content: README 内容
            metadata: 插件元数据
            media_urls: 图片 URL 列表
            plugin_type: 插件类型 (action/filter/pipe)

        Returns:
            创建成功返回帖子 ID，失败返回 None
        """
        # 构建 function 数据结构
        function_data = {
            "id": "",  # 服务器会生成
            "name": title,
            "type": plugin_type,
            "content": source_code,
            "meta": {
                "description": metadata.get("description", "") if metadata else "",
                "manifest": metadata or {},
            },
        }

        data = {"function": function_data}

        result = self.create_post(
            title=title,
            content=(
                readme_content or metadata.get("description", "") if metadata else ""
            ),
            post_type="function",
            data=data,
            media=media_urls,
        )

        if result:
            return result.get("id")
        return None

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

        # 仅发送允许更新的字段，避免 422 错误
        allowed_keys = ["title", "content", "type", "data", "media"]
        payload = {k: v for k, v in post_data.items() if k in allowed_keys}

        print(f"  [DEBUG] Updating post {post_id} with keys: {list(payload.keys())}")
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code != 200:
            print(f"  [DEBUG] Update failed status: {response.status_code}")
            print(f"  [DEBUG] Update failed response: {response.text[:500]}")

        response.raise_for_status()
        return True

    def update_plugin(
        self,
        post_id: str,
        source_code: str,
        readme_content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        media_urls: Optional[List[str]] = None,
    ) -> bool:
        """
        更新插件（代码 + README + 元数据 + 图片）

        Args:
            post_id: 帖子 ID
            source_code: 插件源代码
            readme_content: README 内容（用于社区页面展示）
            metadata: 插件元数据（title, version, description 等）
            media_urls: 图片 URL 列表

        Returns:
            是否成功
        """
        post_data = self.get_post(post_id)
        if not post_data:
            return False

        # 严格重建 data 结构，避免包含只读字段（如 data.function.id）
        current_function = post_data.get("data", {}).get("function", {})

        # 过滤 metadata，移除 openwebui_id 等系统字段
        clean_metadata = {
            k: v
            for k, v in (metadata or {}).items()
            if k not in ["openwebui_id", "post_id"]
        }

        function_data = {
            "name": metadata.get("title", current_function.get("name", "Plugin")),
            "type": current_function.get("type", "action"),
            "content": source_code,
            "meta": {
                "description": metadata.get(
                    "description",
                    current_function.get("meta", {}).get("description", ""),
                ),
                "manifest": clean_metadata,
            },
        }

        post_data["data"] = {"function": function_data}
        post_data["type"] = "function"

        # 更新 README（社区页面展示内容）
        if readme_content:
            post_data["content"] = readme_content

        # 更新标题
        if metadata and "title" in metadata:
            post_data["title"] = metadata["title"]

        # 更新图片
        if media_urls:
            # 将字符串 URL 转换为字典格式 (API 要求)
            media_list = []
            for item in media_urls:
                if isinstance(item, str):
                    media_list.append({"url": item})
                elif isinstance(item, dict):
                    media_list.append(item)
            post_data["media"] = media_list
        else:
            # 如果没有新图片，保留原有的（如果有）
            pass

        return self.update_post(post_id, post_data)

    # ========== 图片上传 ==========

    def upload_image(self, file_path: str) -> Optional[str]:
        """
        上传图片到 OpenWebUI 社区

        Args:
            file_path: 图片文件路径

        Returns:
            上传成功后的图片 URL，失败返回 None
        """
        if not os.path.exists(file_path):
            return None

        # 获取文件信息
        filename = os.path.basename(file_path)

        # 根据文件扩展名确定 MIME 类型
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        content_type = mime_types.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                files = {"file": (filename, f, content_type)}
                # 上传时不使用 JSON Content-Type
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                }
                response = requests.post(
                    f"{self.BASE_URL}/files/",
                    headers=headers,
                    files=files,
                )
                response.raise_for_status()
                result = response.json()

                # 返回图片 URL
                return result.get("url")
        except Exception as e:
            print(f"  Warning: Failed to upload image: {e}")
            return None

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
        self, file_path: str, force: bool = False, auto_create: bool = True
    ) -> Tuple[bool, str]:
        """
        从文件发布插件（支持首次创建和更新）

        Args:
            file_path: 插件文件路径
            force: 是否强制更新（忽略版本检查）
            auto_create: 如果没有 openwebui_id，是否自动创建新帖子

        Returns:
            (是否成功, 消息)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = self._parse_frontmatter(content)
        if not metadata:
            return False, "No frontmatter found"

        title = metadata.get("title")
        if not title:
            return False, "No title in frontmatter"

        post_id = metadata.get("openwebui_id") or metadata.get("post_id")
        local_version = metadata.get("version")

        # 查找 README
        readme_content = self._find_readme(file_path)

        # 查找并上传图片
        media_urls = None
        image_path = self._find_image(file_path)
        if image_path:
            print(f"  Found image: {os.path.basename(image_path)}")
            image_url = self.upload_image(image_path)
            if image_url:
                print(f"  Uploaded image: {image_url}")
                media_urls = [image_url]

        # 如果没有 post_id，尝试创建新帖子
        if not post_id:
            if not auto_create:
                return False, "No openwebui_id found and auto_create is disabled"

            print(f"  Creating new post for: {title}")
            new_post_id = self.create_plugin(
                title=title,
                source_code=content,
                readme_content=readme_content or metadata.get("description", ""),
                metadata=metadata,
                media_urls=media_urls,
            )

            if new_post_id:
                # 将新 ID 写回本地文件
                self._inject_id_to_file(file_path, new_post_id)
                return True, f"Created new post (ID: {new_post_id})"
            return False, "Failed to create new post"

        # 获取远程帖子信息（只需获取一次）
        remote_post = None
        if post_id:
            remote_post = self.get_post(post_id)

        # 版本检查（仅对更新有效）
        if not force and local_version and remote_post:
            remote_version = (
                remote_post.get("data", {})
                .get("function", {})
                .get("meta", {})
                .get("manifest", {})
                .get("version")
            )

            version_changed = local_version != remote_version

            # 检查 README 是否变化
            readme_changed = False
            remote_content = remote_post.get("content", "")
            local_content = readme_content or metadata.get("description", "")

            # 简单的内容比较 (去除首尾空白)
            if (local_content or "").strip() != (remote_content or "").strip():
                readme_changed = True

            if not version_changed and not readme_changed:
                return (
                    True,
                    f"Skipped: version {local_version} matches remote and no README changes",
                )

            if readme_changed and not version_changed:
                print(
                    f"  ℹ️  Version match ({local_version}) but README changed. Updating..."
                )

        # 更新
        success = self.update_plugin(
            post_id=post_id,
            source_code=content,
            readme_content=readme_content or metadata.get("description", ""),
            metadata=metadata,
            media_urls=media_urls,
        )

        if success:
            if local_version:
                return True, f"Updated to version {local_version}"
            return True, "Updated plugin"
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

    def _find_image(self, plugin_file_path: str) -> Optional[str]:
        """
        查找插件对应的图片文件
        图片名称需要和插件文件名一致（不含扩展名）

        例如：
            export_to_word.py -> export_to_word.png / export_to_word.jpg
        """
        plugin_dir = os.path.dirname(plugin_file_path)
        plugin_name = os.path.splitext(os.path.basename(plugin_file_path))[0]

        # 支持的图片格式
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

        for ext in image_extensions:
            image_path = os.path.join(plugin_dir, plugin_name + ext)
            if os.path.exists(image_path):
                return image_path
        return None

    def _inject_id_to_file(self, file_path: str, post_id: str) -> bool:
        """
        将新创建的帖子 ID 写回本地插件文件的 frontmatter

        Args:
            file_path: 插件文件路径
            post_id: 新创建的帖子 ID

        Returns:
            是否成功
        """
        try:
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
                        in_frontmatter = False

                new_lines.append(line)

                # Insert after version line
                if (
                    in_frontmatter
                    and not inserted
                    and line.strip().startswith("version:")
                ):
                    new_lines.append(f"openwebui_id: {post_id}\n")
                    inserted = True
                    print(f"  Injected openwebui_id: {post_id}")

            if inserted:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return True

            print(f"  Warning: Could not inject ID (no version line found)")
            return False

        except Exception as e:
            print(f"  Error injecting ID to file: {e}")
            return False

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
