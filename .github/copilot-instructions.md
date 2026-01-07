# Copilot Instructions for awesome-openwebui

本文档定义了 OpenWebUI 插件开发的标准规范和最佳实践。Copilot 在生成代码或文档时应遵循这些准则。

This document defines the standard conventions and best practices for OpenWebUI plugin development. Copilot should follow these guidelines when generating code or documentation.

---

## 📚 双语版本要求 (Bilingual Version Requirements)

### 插件代码 (Plugin Code)

每个插件必须提供两个版本：

1. **英文版本**: `plugin_name.py` - 英文界面、提示词和注释
2. **中文版本**: `plugin_name_cn.py` - 中文界面、提示词和注释

示例：
```
plugins/actions/export_to_docx/
├── export_to_word.py      # English version
├── export_to_word_cn.py    # Chinese version
├── README.md               # English documentation
└── README_CN.md            # Chinese documentation
```

### 文档 (Documentation)

每个插件目录必须包含双语 README 文件：

- `README.md` - English documentation
- `README_CN.md` - 中文文档

### README 结构规范 (README Structure Standard)

所有插件 README 必须遵循以下统一结构顺序：

1.  **标题 (Title)**: 插件名称，带 Emoji 图标
2.  **元数据 (Metadata)**: 作者、版本、项目链接 (一行显示)
    - 格式: `**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** x.x.x | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)`
    - **注意**: Author 和 Project 为固定值，仅需更新 Version 版本号
3.  **描述 (Description)**: 一句话功能介绍
4.  **最新更新 (What's New)**: **必须**放在描述之后，显著展示最新版本的变更点
5.  **核心特性 (Key Features)**: 使用 Emoji + 粗体标题 + 描述格式
6.  **使用方法 (How to Use)**: 按步骤说明
7.  **配置参数 (Configuration/Valves)**: 使用表格格式，包含参数名、默认值、描述
8.  **其他 (Others)**: 支持的模板类型、语法示例、故障排除等

完整示例 (Full Example):

```markdown
# 📊 Smart Plugin

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.0.0 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)

A one-sentence description of this plugin.

## 🔥 What's New in v1.0.0

- ✨ **Feature Name**: Brief description of the feature.
- 🔧 **Configuration Change**: What changed in settings.
- 🐛 **Bug Fix**: What was fixed.

## ✨ Key Features

- 🚀 **Feature A**: Description of feature A.
- 🎨 **Feature B**: Description of feature B.
- 📥 **Feature C**: Description of feature C.

## 🚀 How to Use

1. **Install**: Search for "Plugin Name" in the Open WebUI Community and install.
2. **Trigger**: Enter your text in the chat, then click the **Action Button**.
3. **Result**: View the generated result.

## ⚙️ Configuration (Valves)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| **Show Status (SHOW_STATUS)** | `True` | Whether to show status updates. |
| **Model ID (MODEL_ID)** | `Empty` | LLM model for processing. |
| **Output Mode (OUTPUT_MODE)** | `image` | `image` for static, `html` for interactive. |

## 🛠️ Supported Types (Optional)

| Category | Type Name | Use Case |
| :--- | :--- | :--- |
| **Category A** | `type-a`, `type-b` | Use case description |

## 📝 Advanced Example (Optional)

\`\`\`syntax
example code or syntax here
\`\`\`
```

### 文档内容要求 (Content Requirements)

- **新增功能**: 必须在 "What's New" 章节中明确列出，使用 Emoji + 粗体标题格式。
- **双语**: 必须提供 `README.md` (英文) 和 `README_CN.md` (中文)。
- **表格对齐**: 配置参数表格使用左对齐 `:---`。
- **Emoji 规范**: 标题使用合适的 Emoji 增强可读性。

### 官方文档 (Official Documentation)

如果插件被合并到主仓库，还需更新 `docs/` 目录下的相关文档：
- `docs/plugins/{type}/plugin-name.md`
- `docs/plugins/{type}/plugin-name.zh.md`

其中 `{type}` 对应插件类型（如 `actions`, `filters`, `pipes` 等）。

---

## 📝 文档字符串规范 (Docstring Standard)

每个插件文件必须以标准化的文档字符串开头：

```python
"""
title: 插件名称 (Plugin Name)
author: Fu-Jie
author_url: https://github.com/Fu-Jie
funding_url: https://github.com/Fu-Jie/awesome-openwebui
version: 0.1.0
icon_url: data:image/svg+xml;base64,<base64-encoded-svg>
requirements: dependency1==1.0.0, dependency2>=2.0.0
description: 插件功能的简短描述。Brief description of plugin functionality.
"""
```

### 字段说明 (Field Descriptions)

| 字段 (Field) | 说明 (Description) | 示例 (Example) |
|--------------|---------------------|----------------|
| `title` | 插件显示名称 | `Export to Word` / `导出为 Word` |
| `author` | 作者名称 | `Fu-Jie` |
| `author_url` | 作者主页链接 | `https://github.com/Fu-Jie` |
| `funding_url` | 赞助/项目链接 | `https://github.com/Fu-Jie/awesome-openwebui` |
| `version` | 语义化版本号 | `0.1.0`, `1.2.3` |
| `icon_url` | 图标 (Base64 编码的 SVG) | 见下方图标规范 |
| `requirements` | 额外依赖 (仅 OpenWebUI 环境未安装的) | `python-docx==1.1.2` |
| `description` | 功能描述 | `将对话导出为 Word 文档` |

### 图标规范 (Icon Guidelines)

- 图标来源：从 [Lucide Icons](https://lucide.dev/icons/) 获取符合插件功能的图标
- 格式：Base64 编码的 SVG
- 获取方法：从 Lucide 下载 SVG，然后使用 Base64 编码
- 示例格式：
```
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0i...（完整的 Base64 编码字符串）
```

---

(Author info is now part of the top metadata section, see "README Structure Standard" above)

---

## 🏗️ 插件目录结构 (Plugin Directory Structure)

```
plugins/
├── actions/           # Action 插件 (用户触发的功能)
│   ├── my_action/
│   │   ├── my_action.py          # English version
│   │   ├── 我的动作.py            # Chinese version
│   │   ├── README.md              # English documentation
│   │   └── README_CN.md           # Chinese documentation
│   ├── ACTION_PLUGIN_TEMPLATE.py      # English template
│   ├── ACTION_PLUGIN_TEMPLATE_CN.py   # Chinese template
│   └── README.md
├── filters/           # Filter 插件 (输入处理)
│   ├── my_filter/
│   │   ├── my_filter.py
│   │   ├── 我的过滤器.py
│   │   ├── README.md
│   │   └── README_CN.md
│   └── README.md
├── pipes/             # Pipe 插件 (输出处理)
│   └── ...
└── pipelines/         # Pipeline 插件
    └── ...
```

---

## ⚙️ Valves 配置规范 (Valves Configuration)

使用 Pydantic BaseModel 定义可配置参数：

```python
from pydantic import BaseModel, Field

class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates."
        )
        MODEL_ID: str = Field(
            default="",
            description="Built-in LLM Model ID. If empty, uses current conversation model."
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="Minimum text length required for processing (characters)."
        )
        CLEAR_PREVIOUS_HTML: bool = Field(
            default=False,
            description="Whether to clear previous plugin results."
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="Number of recent messages to use for generation."
        )

    def __init__(self):
        self.valves = self.Valves()
```

### 命名规则 (Naming Convention)

- 所有 Valves 字段使用 **大写下划线** (UPPER_SNAKE_CASE)
- 示例：`SHOW_STATUS`, `MODEL_ID`, `MIN_TEXT_LENGTH`

---

## 📤 事件发送规范 (Event Emission)

必须实现以下辅助方法：

```python
async def _emit_status(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    description: str,
    done: bool = False,
):
    """Emits a status update event."""
    if self.valves.SHOW_STATUS and emitter:
        await emitter(
            {"type": "status", "data": {"description": description, "done": done}}
        )

async def _emit_notification(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    content: str,
    type: str = "info",
):
    """Emits a notification event (info, success, warning, error)."""
    if emitter:
        await emitter(
            {"type": "notification", "data": {"type": type, "content": content}}
        )
```

---

## 📋 日志规范 (Logging Standard)

- **禁止使用** `print()` 语句
- 必须使用 Python 标准库 `logging`

```python
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 记录关键操作
logger.info(f"Action: {__name__} started")

# 记录异常 (包含堆栈信息)
logger.error(f"Processing failed: {e}", exc_info=True)
```

---

## 🎨 HTML 注入规范 (HTML Injection)

使用统一的标记和结构：

```python
# HTML 包装器标记
HTML_WRAPPER_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <style>
        /* STYLES_INSERTION_POINT */
    </style>
</head>
<body>
    <div id="main-container">
        <!-- CONTENT_INSERTION_POINT -->
    </div>
    <!-- SCRIPTS_INSERTION_POINT -->
</body>
</html>
"""
```

必须实现 HTML 合并方法以支持多次运行插件：

```python
def _remove_existing_html(self, content: str) -> str:
    """Removes existing plugin-generated HTML code blocks."""
    pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
    return re.sub(pattern, "", content).strip()

def _merge_html(
    self,
    existing_html: str,
    new_content: str,
    new_styles: str = "",
    new_scripts: str = "",
    user_language: str = "en-US",
) -> str:
    """
    Merges new content into existing HTML container.
    See ACTION_PLUGIN_TEMPLATE.py for full implementation.
    """
    pass  # Implement based on template
```

---

## 🌍 多语言支持 (Internationalization)

从用户上下文获取语言偏好：

```python
def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Extracts user context information."""
    if isinstance(__user__, (list, tuple)):
        user_data = __user__[0] if __user__ else {}
    elif isinstance(__user__, dict):
        user_data = __user__
    else:
        user_data = {}

    return {
        "user_id": user_data.get("id", "unknown_user"),
        "user_name": user_data.get("name", "User"),
        "user_language": user_data.get("language", "en-US"),
    }
```

中文版插件默认值：
- `user_language`: `"zh-CN"`
- `user_name`: `"用户"`

英文版插件默认值：
- `user_language`: `"en-US"`
- `user_name`: `"User"`

### 用户上下文获取规范 (User Context Retrieval)

所有插件**必须**使用 `_get_user_context` 方法来安全获取用户信息，而不是直接访问 `__user__` 参数。这是因为 `__user__` 的类型可能是 `dict`、`list`、`tuple` 或其他类型，直接调用 `.get()` 可能导致 `AttributeError`。

All plugins **MUST** use the `_get_user_context` method to safely retrieve user information instead of directly accessing the `__user__` parameter. This is because `__user__` can be of type `dict`, `list`, `tuple`, or other types, and directly calling `.get()` may cause `AttributeError`.

**正确做法 (Correct):**

```python
def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """安全提取用户上下文信息。"""
    if isinstance(__user__, (list, tuple)):
        user_data = __user__[0] if __user__ else {}
    elif isinstance(__user__, dict):
        user_data = __user__
    else:
        user_data = {}

    return {
        "user_id": user_data.get("id", "unknown_user"),
        "user_name": user_data.get("name", "User"),
        "user_language": user_data.get("language", "en-US"),
    }

async def action(self, body: dict, __user__: Optional[Dict[str, Any]] = None, ...):
    user_ctx = self._get_user_context(__user__)
    user_id = user_ctx["user_id"]
    user_name = user_ctx["user_name"]
    user_language = user_ctx["user_language"]
```

**禁止的做法 (Prohibited):**

```python
# ❌ 禁止: 直接调用 __user__.get()
# ❌ Prohibited: Directly calling __user__.get()
user_id = __user__.get("id") if __user__ else "default"

# ❌ 禁止: 假设 __user__ 一定是 dict
# ❌ Prohibited: Assuming __user__ is always a dict
user_name = __user__["name"]
```

---

## 📦 依赖管理 (Dependencies)

### requirements 字段规则

- 仅列出 OpenWebUI 环境中**未安装**的依赖
- 使用精确版本号
- 多个依赖用逗号分隔

```python
"""
requirements: python-docx==1.1.2, openpyxl==3.1.2
"""
```

常见 OpenWebUI 已安装依赖（无需在 requirements 中声明）：
- `pydantic`
- `fastapi`
- `logging`
- `re`, `json`, `datetime`, `io`, `base64`

---

## 🗄️ 数据库连接规范 (Database Connection)

### 复用 OpenWebUI 内部连接 (Re-use OpenWebUI's Internal Connection)

当插件需要持久化存储时，**必须**复用 Open WebUI 的内部数据库连接，而不是创建新的数据库引擎。这确保了：

- 插件与数据库类型无关（自动支持 PostgreSQL、SQLite 等）
- 自动继承 Open WebUI 的数据库配置
- 避免连接池资源浪费
- 保持与 Open WebUI 核心的兼容性

When a plugin requires persistent storage, it **MUST** re-use Open WebUI's internal database connection instead of creating a new database engine. This ensures:

- The plugin is database-agnostic (automatically supports PostgreSQL, SQLite, etc.)
- Automatic inheritance of Open WebUI's database configuration
- No wasted connection pool resources
- Compatibility with Open WebUI's core

### 实现示例 (Implementation Example)

```python
# Open WebUI internal database (re-use shared connection)
from open_webui.internal.db import engine as owui_engine
from open_webui.internal.db import Session as owui_Session
from open_webui.internal.db import Base as owui_Base

from sqlalchemy import Column, String, Text, DateTime, Integer, inspect
from datetime import datetime


class PluginTable(owui_Base):
    """Plugin storage table - inherits from OpenWebUI's Base"""

    __tablename__ = "plugin_table_name"
    __table_args__ = {"extend_existing": True}  # Required to avoid conflicts on plugin reload

    id = Column(Integer, primary_key=True, autoincrement=True)
    unique_id = Column(String(255), unique=True, nullable=False, index=True)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Filter:  # or Pipe, Action, etc.
    def __init__(self):
        self.valves = self.Valves()
        self._db_engine = owui_engine
        self._SessionLocal = owui_Session
        self._init_database()

    def _init_database(self):
        """Initialize the database table using OpenWebUI's shared connection."""
        try:
            inspector = inspect(self._db_engine)
            if not inspector.has_table("plugin_table_name"):
                PluginTable.__table__.create(bind=self._db_engine, checkfirst=True)
                print("[Database] ✅ Created plugin table using OpenWebUI's shared connection.")
            else:
                print("[Database] ✅ Using OpenWebUI's shared connection. Table already exists.")
        except Exception as e:
            print(f"[Database] ❌ Initialization failed: {str(e)}")

    def _save_data(self, unique_id: str, data: str):
        """Save data using context manager pattern."""
        try:
            with self._SessionLocal() as session:
                # Your database operations here
                session.commit()
        except Exception as e:
            print(f"[Storage] ❌ Database save failed: {str(e)}")

    def _load_data(self, unique_id: str):
        """Load data using context manager pattern."""
        try:
            with self._SessionLocal() as session:
                record = session.query(PluginTable).filter_by(unique_id=unique_id).first()
                if record:
                    session.expunge(record)  # Detach from session for use after close
                    return record
        except Exception as e:
            print(f"[Load] ❌ Database read failed: {str(e)}")
        return None
```

### 禁止的做法 (Prohibited Practices)

以下做法**已被弃用**，不应在新插件中使用：

The following practices are **deprecated** and should NOT be used in new plugins:

```python
# ❌ 禁止: 读取 DATABASE_URL 环境变量
# ❌ Prohibited: Reading DATABASE_URL environment variable
database_url = os.getenv("DATABASE_URL")

# ❌ 禁止: 创建独立的数据库引擎
# ❌ Prohibited: Creating a separate database engine
from sqlalchemy import create_engine
self._db_engine = create_engine(database_url, **engine_args)

# ❌ 禁止: 创建独立的会话工厂
# ❌ Prohibited: Creating a separate session factory
from sqlalchemy.orm import sessionmaker
self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._db_engine)

# ❌ 禁止: 使用独立的 Base
# ❌ Prohibited: Using a separate Base
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
```

---

## 📂 文件存储访问规范 (File Storage Access)

OpenWebUI 支持多种文件存储后端（本地磁盘、S3/MinIO 对象存储等）。插件在访问用户上传的文件或生成的图片时，必须实现多级回退机制以兼容所有存储配置。

### 存储类型检测 (Storage Type Detection)

通过 `Files.get_file_by_id()` 获取的文件对象，其 `path` 属性决定了存储位置：

| Path 格式 | 存储类型 | 访问方式 |
|-----------|----------|----------|
| `s3://bucket/key` | S3/MinIO 对象存储 | boto3 直连或 API 回调 |
| `/app/backend/data/...` | Docker 卷存储 | 本地文件系统读取 |
| `./uploads/...` | 本地相对路径 | 本地文件系统读取 |
| `gs://bucket/key` | Google Cloud Storage | API 回调 |

### 多级回退机制 (Multi-level Fallback)

推荐实现以下优先级的文件获取策略：

```python
def _get_file_content(self, file_id: str, max_bytes: int) -> Optional[bytes]:
    """获取文件内容，支持多种存储后端"""
    file_obj = Files.get_file_by_id(file_id)
    if not file_obj:
        return None

    # 1️⃣ 数据库直接存储 (小文件)
    data_field = getattr(file_obj, "data", None)
    if isinstance(data_field, dict):
        if "bytes" in data_field:
            return data_field["bytes"]
        if "base64" in data_field:
            return base64.b64decode(data_field["base64"])

    # 2️⃣ S3 直连 (对象存储 - 最快)
    s3_path = getattr(file_obj, "path", None)
    if isinstance(s3_path, str) and s3_path.startswith("s3://"):
        data = self._read_from_s3(s3_path, max_bytes)
        if data:
            return data

    # 3️⃣ 本地文件系统 (磁盘存储)
    for attr in ("path", "file_path"):
        path = getattr(file_obj, attr, None)
        if path and not path.startswith(("s3://", "gs://", "http")):
            # 尝试多个常见路径
            for base in ["", "./data", "/app/backend/data"]:
                full_path = Path(base) / path if base else Path(path)
                if full_path.exists():
                    return full_path.read_bytes()[:max_bytes]

    # 4️⃣ 公共 URL 下载
    url = getattr(file_obj, "url", None)
    if url and url.startswith("http"):
        return self._download_from_url(url, max_bytes)

    # 5️⃣ 内部 API 回调 (通用兜底方案)
    if self._api_base_url:
        api_url = f"{self._api_base_url}/api/v1/files/{file_id}/content"
        return self._download_from_api(api_url, self._api_token, max_bytes)

    return None
```

### S3 直连实现 (S3 Direct Access)

当检测到 `s3://` 路径时，使用 `boto3` 直接访问对象存储，读取以下环境变量：

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `S3_ENDPOINT_URL` | S3 兼容服务端点 | `https://minio.example.com` |
| `S3_ACCESS_KEY_ID` | 访问密钥 ID | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | 访问密钥 | `minioadmin` |
| `S3_ADDRESSING_STYLE` | 寻址样式 | `auto`, `path`, `virtual` |

```python
# S3 直连示例
import boto3
from botocore.config import Config as BotoConfig
import os

def _read_from_s3(self, s3_path: str, max_bytes: int) -> Optional[bytes]:
    """从 S3 直接读取文件 (比 API 回调更快)"""
    if not s3_path.startswith("s3://"):
        return None

    # 解析 s3://bucket/key
    parts = s3_path[5:].split("/", 1)
    bucket, key = parts[0], parts[1]

    # 从环境变量读取配置
    endpoint = os.environ.get("S3_ENDPOINT_URL")
    access_key = os.environ.get("S3_ACCESS_KEY_ID")
    secret_key = os.environ.get("S3_SECRET_ACCESS_KEY")
    
    if not all([endpoint, access_key, secret_key]):
        return None  # 回退到 API 方式

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(s3={"addressing_style": os.environ.get("S3_ADDRESSING_STYLE", "auto")})
    )
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read(max_bytes)
```

### API 回调实现 (API Fallback)

当其他方式失败时，通过 OpenWebUI 内部 API 获取文件：

```python
def _download_from_api(self, api_url: str, token: str, max_bytes: int) -> Optional[bytes]:
    """通过 OpenWebUI API 获取文件内容"""
    import urllib.request
    
    headers = {"User-Agent": "OpenWebUI-Plugin"}
    if token:
        headers["Authorization"] = token

    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        if 200 <= response.status < 300:
            return response.read(max_bytes)
    return None
```

### 获取 API 上下文 (API Context Extraction)

在 `action()` 方法中捕获请求上下文，用于 API 回调：

```python
async def action(self, body: dict, __request__=None, ...):
    # 从请求对象获取 API 凭证
    if __request__:
        self._api_token = __request__.headers.get("Authorization")
        self._api_base_url = str(__request__.base_url).rstrip("/")
    else:
        # 从环境变量获取端口作为备用
        port = os.environ.get("PORT") or "8080"
        self._api_base_url = f"http://localhost:{port}"
        self._api_token = None
```

### 性能对比 (Performance Comparison)

| 方式 | 网络跳数 | 适用场景 |
|------|----------|----------|
| S3 直连 | 1 (插件 → S3) | 对象存储，最快 |
| 本地文件 | 0 | 磁盘存储，最快 |
| API 回调 | 2 (插件 → OpenWebUI → S3/磁盘) | 通用兜底 |

### 参考实现 (Reference Implementation)

- `plugins/actions/export_to_docx/export_to_word.py` - `_image_bytes_from_owui_file_id` 方法

### Python 规范

- 遵循 **PEP 8** 规范
- 使用 **Black** 格式化代码
- 关键逻辑添加注释

### 导入顺序

```python
# 1. Standard library imports
import os
import re
import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable

# 2. Third-party imports
from pydantic import BaseModel, Field
from fastapi import Request

# 3. OpenWebUI imports
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users
```

---

## 📄 文件导出与命名规范 (File Export and Naming)

对于涉及文件导出的插件（通常是 Action），必须提供灵活的标题生成策略。

### Valves 配置 (Valves Configuration)

应包含 `TITLE_SOURCE` 选项：

```python
class Valves(BaseModel):
    TITLE_SOURCE: str = Field(
        default="chat_title",
        description="Title Source: 'chat_title', 'ai_generated', 'markdown_title'",
    )
```

### 标题获取逻辑 (Title Retrieval Logic)

1.  **chat_title**: 尝试从 `body` 获取，若失败且有 `chat_id`，则从数据库获取 (`Chats.get_chat_by_id`)。
2.  **markdown_title**: 从 Markdown 内容提取第一个 H1 或 H2。
3.  **ai_generated**: 使用轻量级 Prompt 让 AI 生成简短标题。

### 优先级与回退 (Priority and Fallback)

代码应根据 `TITLE_SOURCE` 优先尝试指定方法，若失败则按以下顺序回退：
`chat_title` -> `markdown_title` -> `user_name + date`

```python
# 核心逻辑示例
if self.valves.TITLE_SOURCE == "chat_title":
    title = chat_title
elif self.valves.TITLE_SOURCE == "markdown_title":
    title = self.extract_title(content)
elif self.valves.TITLE_SOURCE == "ai_generated":
    title = await self.generate_title_using_ai(...)
```

### AI 标题生成实现 (AI Title Generation Implementation)

如果支持 `ai_generated` 选项，应实现类似以下的方法：

```python
async def generate_title_using_ai(
    self, 
    body: dict, 
    content: str, 
    user_id: str, 
    request: Any
) -> str:
    """Generates a short title using the current LLM model."""
    if not request:
        return ""

    try:
        # 获取当前用户和模型
        user_obj = Users.get_user_by_id(user_id)
        model = body.get("model")

        # 构造请求
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. Generate a short, concise title (max 10 words) for the following text. Do not use quotes. Only output the title."
                },
                {
                    "role": "user", 
                    "content": content[:2000]  # 限制上下文长度以节省 Token
                }
            ],
            "stream": False,
        }

        # 调用 OpenWebUI 内部生成接口
        response = await generate_chat_completion(request, payload, user_obj)
        
        if response and "choices" in response:
            return response["choices"][0]["message"]["content"].strip()
            
    except Exception as e:
        logger.error(f"Error generating title: {e}")

    return ""
```

---

## 🎭 iframe 主题检测规范 (iframe Theme Detection)

当插件在 iframe 中运行（特别是使用 `srcdoc` 属性）时，需要检测应用程序的主题以保持视觉一致性。

### 检测优先级 (Priority Order)

按以下顺序尝试检测主题，直到找到有效结果：

1. **显式切换** (Explicit Toggle) - 用户手动点击主题按钮
2. **父文档 Meta 标签** (Parent Meta Theme-Color) - 从 `window.parent.document` 的 `<meta name="theme-color">` 读取
3. **父文档 Class/Data-Theme** (Parent HTML/Body Class) - 检查父文档 html/body 的 class 或 data-theme 属性
4. **系统偏好** (System Preference) - `prefers-color-scheme: dark` 媒体查询

### 核心实现代码 (Implementation)

```javascript
// 1. 颜色亮度解析（支持 hex 和 rgb）
const parseColorLuma = (colorStr) => {
    if (!colorStr) return null;
    // hex #rrggbb or rrggbb
    let m = colorStr.match(/^#?([0-9a-f]{6})$/i);
    if (m) {
        const hex = m[1];
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    }
    // rgb(r, g, b) or rgba(r, g, b, a)
    m = colorStr.match(/rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
    if (m) {
        const r = parseInt(m[1], 10);
        const g = parseInt(m[2], 10);
        const b = parseInt(m[3], 10);
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    }
    return null;
};

// 2. 从 meta 标签提取主题
const getThemeFromMeta = (doc, scope = 'self') => {
    const metas = Array.from((doc || document).querySelectorAll('meta[name="theme-color"]'));
    if (!metas.length) return null;
    const color = metas[metas.length - 1].content.trim();
    const luma = parseColorLuma(color);
    if (luma === null) return null;
    return luma < 0.5 ? 'dark' : 'light';
};

// 3. 安全地访问父文档
const getParentDocumentSafe = () => {
    try {
        if (!window.parent || window.parent === window) return null;
        const pDoc = window.parent.document;
        void pDoc.title; // 触发跨域检查
        return pDoc;
    } catch (err) {
        console.log(`Parent document not accessible: ${err.name}`);
        return null;
    }
};

// 4. 从父文档的 class/data-theme 检测主题
const getThemeFromParentClass = () => {
    try {
        if (!window.parent || window.parent === window) return null;
        const pDoc = window.parent.document;
        const html = pDoc.documentElement;
        const body = pDoc.body;
        const htmlClass = html ? html.className : '';
        const bodyClass = body ? body.className : '';
        const htmlDataTheme = html ? html.getAttribute('data-theme') : '';
        
        if (htmlDataTheme === 'dark' || bodyClass.includes('dark') || htmlClass.includes('dark')) 
            return 'dark';
        if (htmlDataTheme === 'light' || bodyClass.includes('light') || htmlClass.includes('light')) 
            return 'light';
        return null;
    } catch (err) {
        return null;
    }
};

// 5. 主题设置及检测
const setTheme = (wrapperEl, explicitTheme) => {
    const parentDoc = getParentDocumentSafe();
    const metaThemeParent = parentDoc ? getThemeFromMeta(parentDoc, 'parent') : null;
    const parentClassTheme = getThemeFromParentClass();
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // 按优先级选择
    const chosen = explicitTheme || metaThemeParent || parentClassTheme || (prefersDark ? 'dark' : 'light');
    wrapperEl.classList.toggle('theme-dark', chosen === 'dark');
    return chosen;
};
```

### CSS 变量定义 (CSS Variables)

使用 CSS 变量实现主题切换，避免硬编码颜色：

```css
:root {
    --primary-color: #1e88e5;
    --background-color: #f4f6f8;
    --text-color: #263238;
    --border-color: #e0e0e0;
}

.theme-dark {
    --primary-color: #64b5f6;
    --background-color: #111827;
    --text-color: #e5e7eb;
    --border-color: #374151;
}

.container {
    background-color: var(--background-color);
    color: var(--text-color);
    border-color: var(--border-color);
}
```

### 调试与日志 (Debugging)

添加详细日志便于排查主题检测问题：

```javascript
console.log(`[plugin] [parent] meta theme-color count: ${metas.length}`);
console.log(`[plugin] [parent] meta theme-color picked: "${color}"`);
console.log(`[plugin] [parent] meta theme-color luma=${luma.toFixed(3)}, inferred=${inferred}`);
console.log(`[plugin] parent html.class="${htmlClass}", data-theme="${htmlDataTheme}"`);
console.log(`[plugin] final chosen theme: ${chosen}`);
```

### 最佳实践 (Best Practices)

- 仅尝试访问**父文档**的主题信息，不依赖 srcdoc iframe 自身的 meta（通常为空）
- 在跨域 iframe 中使用 class/data-theme 作为备选方案
- 使用 try-catch 包裹所有父文档访问，避免跨域异常中断
- 提供用户手动切换主题的按钮作为最高优先级
- 记录详细日志便于用户反馈主题检测问题

### OpenWebUI Configuration Requirement (OpenWebUI Configuration)

For iframe plugins to access parent document theme information, users need to configure:

1. **Enable Artifact Same-Origin Access** - In User Settings: **Interface** → **Artifacts** → Check **iframe Sandbox Allow Same Origin**
2. **Configure Sandbox Attributes** - Ensure iframe's sandbox attribute includes both `allow-same-origin` and `allow-scripts`
3. **Verify Meta Tag** - Ensure OpenWebUI page head contains `<meta name="theme-color" content="#color">` tag

**Important Notes**:
- Same-origin access allows iframe to read theme information via `window.parent.document`
- Cross-origin iframes cannot access parent document and should implement class/data-theme detection as fallback
- Using same-origin access in srcdoc iframe is safe (origin is null, doesn't bypass CORS policy)
- Users can provide manual theme toggle button in plugin as highest priority option

---

## ✅ 开发检查清单 (Development Checklist)

开发新插件时，请确保完成以下检查：

- [ ] 创建英文版插件代码 (`plugin_name.py`)
- [ ] 创建中文版插件代码 (`插件名.py` 或 `plugin_name_cn.py`)
- [ ] 编写英文 README (`README.md`)
- [ ] 编写中文 README (`README_CN.md`)
- [ ] 包含标准化文档字符串
- [ ] 添加 Author 和 License 信息
- [ ] 使用 Lucide 图标 (Base64 编码)
- [ ] 实现 Valves 配置
- [ ] 使用 logging 而非 print
- [ ] 测试双语界面
- [ ] **一致性检查 (Consistency Check)**:

---

## 🚀 高级开发模式 (Advanced Development Patterns)

### 混合服务端-客户端生成 (Hybrid Server-Client Generation)

对于需要复杂前端渲染（如 Mermaid 图表、ECharts）但最终生成文件（如 DOCX、PDF）的场景，建议采用混合模式：

1.  **服务端 (Python)**：
    *   处理文本解析、Markdown 转换、文档结构构建。
    *   为复杂组件生成**占位符**（如带有特定 ID 或元数据的图片/文本块）。
    *   将半成品文件（如 Base64 编码的 ZIP/DOCX）发送给前端。

2.  **客户端 (JavaScript)**：
    *   在浏览器中加载半成品文件（使用 JSZip 等库）。
    *   利用浏览器能力渲染复杂组件（如 `mermaid.render`）。
    *   将渲染结果（SVG/PNG）回填到占位符位置。
    *   触发最终文件的下载。

**优势**：
*   无需在服务端安装 Headless Browser（如 Puppeteer），降低部署复杂度。
*   利用用户浏览器的计算能力。
*   支持动态、交互式内容的静态化导出。

### 原生 Word 公式支持 (Native Word Math Support)

对于需要生成高质量数学公式的 Word 文档，推荐使用 `latex2mathml` + `mathml2omml` 组合：

1.  **LaTeX -> MathML**: 使用 `latex2mathml` 将 LaTeX 字符串转换为标准 MathML。
2.  **MathML -> OMML**: 使用 `mathml2omml` 将 MathML 转换为 Office Math Markup Language (OMML)。
3.  **插入 Word**: 将 OMML XML 插入到 `python-docx` 的段落中。

```python
# 示例代码
from latex2mathml.converter import convert as latex2mathml
from mathml2omml import convert as mathml2omml

def add_math(paragraph, latex_str):
    mathml = latex2mathml(latex_str)
    omml = mathml2omml(mathml)
    # ... 插入 OMML 到 paragraph._element ...
```

### JS 渲染并嵌入 Markdown (JS Render to Markdown)

对于需要复杂前端渲染（如 AntV 图表、Mermaid 图表、ECharts）但希望结果**持久化为纯 Markdown 格式**的场景，推荐使用 Data URL 嵌入模式：

#### 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Workflow                          │
├─────────────────────────────────────────────────────────────┤
│  1. Python Action                                            │
│     ├── 分析消息内容                                          │
│     ├── 调用 LLM 生成结构化数据（可选）                        │
│     └── 通过 __event_call__ 发送 JS 代码到前端                │
├─────────────────────────────────────────────────────────────┤
│  2. Browser JS (via __event_call__)                          │
│     ├── 动态加载可视化库（如 AntV、Mermaid）                   │
│     ├── 离屏渲染 SVG/Canvas                                   │
│     ├── 使用 toDataURL() 导出 Base64 Data URL                 │
│     └── 通过 REST API 更新消息内容                            │
├─────────────────────────────────────────────────────────────┤
│  3. Markdown 渲染                                            │
│     └── 显示 ![描述](data:image/svg+xml;base64,...)          │
└─────────────────────────────────────────────────────────────┘
```

#### 核心实现代码

**Python 端（发送 JS 执行）：**

```python
async def action(self, body, __event_call__, __metadata__, ...):
    chat_id = self._extract_chat_id(body, __metadata__)
    message_id = self._extract_message_id(body, __metadata__)
    
    # 生成 JS 代码
    js_code = self._generate_js_code(
        chat_id=chat_id,
        message_id=message_id,
        data=processed_data,  # 可视化所需数据
    )
    
    # 执行 JS
    if __event_call__:
        await __event_call__({
            "type": "execute",
            "data": {"code": js_code}
        })
```

**JavaScript 端（渲染并回写）：**

```javascript
(async function() {
    // 1. 动态加载可视化库
    if (typeof VisualizationLib === 'undefined') {
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.example.com/lib.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    // 2. 创建离屏容器
    const container = document.createElement('div');
    container.style.cssText = 'position:absolute;left:-9999px;';
    document.body.appendChild(container);
    
    // 3. 渲染可视化
    const instance = new VisualizationLib({ container, ... });
    instance.render(data);
    
    // 4. 导出为 Data URL
    const dataUrl = await instance.toDataURL({ type: 'svg', embedResources: true });
    // 或手动转换 SVG:
    // const svgData = new XMLSerializer().serializeToString(svgElement);
    // const base64 = btoa(unescape(encodeURIComponent(svgData)));
    // const dataUrl = "data:image/svg+xml;base64," + base64;
    
    // 5. 清理
    instance.destroy();
    document.body.removeChild(container);
    
    // 6. 生成 Markdown 图片
    const markdownImage = `![描述](${dataUrl})`;
    
    // 7. 通过 API 更新消息
    const token = localStorage.getItem("token");
    await fetch(`/api/v1/chats/${chatId}/messages/${messageId}/event`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            type: "chat:message",
            data: { content: originalContent + "\n\n" + markdownImage }
        })
    });
})();
```

#### 优势

- **纯 Markdown 输出**：结果是标准的 Markdown 图片语法，无需 HTML 代码块
- **高效存储**：图片上传至 `/api/v1/files`，避免 Base64 字符串膨胀聊天记录
- **持久化**：通过 API 回写，消息重新加载后图片仍然存在
- **跨平台**：任何支持 Markdown 图片的客户端都能显示
- **无服务端渲染依赖**：利用用户浏览器的渲染能力

#### 与 HTML 注入模式对比

| 特性 | HTML 注入 (`\`\`\`html`) | JS 渲染 + Markdown 图片 |
|------|-------------------------|------------------------|
| 输出格式 | HTML 代码块 | Markdown 图片 |
| 交互性 | ✅ 支持按钮、动画 | ❌ 静态图片 |
| 外部依赖 | 需要加载 JS 库 | 依赖 `/api/v1/files` 存储 |
| 持久化 | 依赖浏览器渲染 | ✅ 永久可见 |
| 文件导出 | 需特殊处理 | ✅ 直接导出 |
| 适用场景 | 交互式内容 | 信息图、图表快照 |

#### 参考实现

- `plugins/actions/js-render-poc/infographic_markdown.py` - AntV Infographic 生成并嵌入
- `plugins/actions/js-render-poc/js_render_poc.py` - 基础概念验证

### OpenWebUI Chat API 更新规范 (Chat API Update Specification)

当插件需要修改消息内容并持久化到数据库时，必须遵循 OpenWebUI 的 Backend-Controlled API 流程。

When a plugin needs to modify message content and persist it to the database, follow OpenWebUI's Backend-Controlled API flow.

#### 核心概念 (Core Concepts)

1. **Event API** (`/api/v1/chats/{chatId}/messages/{messageId}/event`)
   - 用于**即时更新前端显示**，用户无需刷新页面
   - 是可选的，部分版本可能不支持
   - 仅影响当前会话的 UI，不持久化

2. **Chat Persistence API** (`/api/v1/chats/{chatId}`)
   - 用于**持久化到数据库**，确保刷新页面后数据仍存在
   - 必须同时更新 `messages[]` 数组和 `history.messages` 对象
   - 是消息持久化的唯一可靠方式

#### 数据结构 (Data Structure)

OpenWebUI 的 Chat 对象包含两个关键位置存储消息内容：

```javascript
{
  "chat": {
    "id": "chat-uuid",
    "title": "Chat Title",
    "messages": [                              // 1️⃣ 消息数组
      { "id": "msg-1", "role": "user", "content": "..." },
      { "id": "msg-2", "role": "assistant", "content": "..." }
    ],
    "history": {
      "current_id": "msg-2",
      "messages": {                            // 2️⃣ 消息索引对象
        "msg-1": { "id": "msg-1", "role": "user", "content": "..." },
        "msg-2": { "id": "msg-2", "role": "assistant", "content": "..." }
      }
    }
  }
}
```

> **重要**：修改消息时，**必须同时更新两个位置**，否则可能导致数据不一致。

#### 标准实现流程 (Standard Implementation)

```javascript
(async function() {
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    const token = localStorage.getItem("token");
    
    // 1️⃣ 获取当前 Chat 数据
    const getResponse = await fetch(`/api/v1/chats/${chatId}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    });
    const chatData = await getResponse.json();
    
    // 2️⃣ 使用 map 遍历 messages，只修改目标消息
    let newContent = "";
    const updatedMessages = chatData.chat.messages.map(m => {
        if (m.id === messageId) {
            const originalContent = m.content || "";
            newContent = originalContent + "\n\n" + newMarkdown;
            
            // 3️⃣ 同时更新 history.messages 中对应的消息
            if (chatData.chat.history && chatData.chat.history.messages) {
                if (chatData.chat.history.messages[messageId]) {
                    chatData.chat.history.messages[messageId].content = newContent;
                }
            }
            
            // 4️⃣ 保留消息的其他属性，只修改 content
            return { ...m, content: newContent };
        }
        return m;  // 其他消息原样返回
    });
    
    // 5️⃣ 通过 Event API 即时更新前端（可选）
    try {
        await fetch(`/api/v1/chats/${chatId}/messages/${messageId}/event`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                type: "chat:message",
                data: { content: newContent }
            })
        });
    } catch (e) {
        // Event API 是可选的，继续执行持久化
        console.log("Event API not available, continuing...");
    }
    
    // 6️⃣ 持久化到数据库（必须）
    const updatePayload = {
        chat: {
            ...chatData.chat,      // 保留所有原有属性
            messages: updatedMessages
            // history 已在上面原地修改
        }
    };
    
    await fetch(`/api/v1/chats/${chatId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(updatePayload)
    });
})();
```

#### 最佳实践 (Best Practices)

1. **保留原有结构**：使用展开运算符 `...chatData.chat` 和 `...m` 确保不丢失任何原有属性
2. **双位置更新**：必须同时更新 `messages[]` 和 `history.messages[id]`
3. **错误处理**：Event API 调用应包裹在 try-catch 中，失败时继续持久化
4. **重试机制**：对持久化 API 实现重试逻辑，提高可靠性

```javascript
// 带重试的请求函数
const fetchWithRetry = async (url, options, retries = 3) => {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);
            if (response.ok) return response;
            if (i < retries - 1) {
                await new Promise(r => setTimeout(r, 1000 * (i + 1)));  // 指数退避
            }
        } catch (e) {
            if (i === retries - 1) throw e;
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
    return null;
};
```

5. **禁止使用的 API**：不要使用 `/api/v1/chats/{chatId}/share` 作为持久化备用方案，该 API 用于分享功能，不是更新功能

#### 提取 Chat ID 和 Message ID (Extracting IDs)

```python
def _extract_chat_id(self, body: dict, metadata: Optional[dict]) -> str:
    """从 body 或 metadata 中提取 chat_id"""
    if isinstance(body, dict):
        chat_id = body.get("chat_id")
        if isinstance(chat_id, str) and chat_id.strip():
            return chat_id.strip()
        
        body_metadata = body.get("metadata", {})
        if isinstance(body_metadata, dict):
            chat_id = body_metadata.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()
    
    if isinstance(metadata, dict):
        chat_id = metadata.get("chat_id")
        if isinstance(chat_id, str) and chat_id.strip():
            return chat_id.strip()
    
    return ""

def _extract_message_id(self, body: dict, metadata: Optional[dict]) -> str:
    """从 body 或 metadata 中提取 message_id"""
    if isinstance(body, dict):
        message_id = body.get("id")
        if isinstance(message_id, str) and message_id.strip():
            return message_id.strip()
        
        body_metadata = body.get("metadata", {})
        if isinstance(body_metadata, dict):
            message_id = body_metadata.get("message_id")
            if isinstance(message_id, str) and message_id.strip():
                return message_id.strip()
    
    if isinstance(metadata, dict):
        message_id = metadata.get("message_id")
        if isinstance(message_id, str) and message_id.strip():
            return message_id.strip()
    
    return ""
```

#### 参考实现

- `plugins/actions/smart-mind-map/smart_mind_map.py` - 思维导图图片模式实现
- 官方文档: [Backend-Controlled, UI-Compatible API Flow](https://docs.openwebui.com/tutorials/tips/backend-controlled-ui-compatible-api-flow)

---

## 🔄 一致性维护 (Consistency Maintenance)

任何插件的**新增、修改或移除**，必须同时更新以下三个位置，保持完全一致：

1. **插件代码 (Plugin Code)**: 更新 `version` 和功能实现。
2. **项目文档 (Docs)**: 更新 `docs/` 下对应的文档文件（版本号、功能描述）。
3. **自述文件 (README)**: 更新根目录下的 `README.md` 和 `README_CN.md` 中的插件列表。

> [!IMPORTANT]
> 提交 PR 前，请务必检查这三处是否同步。例如：如果删除了一个插件，必须同时从 README 列表中移除，并删除对应的 docs 文档。

---

## � 发布工作流 (Release Workflow)

### 自动发布 (Automatic Release)

当插件更新推送到 `main` 分支时，会**自动触发**发布流程：

1. 🔍 检测版本变化（与上次 release 对比）
2. 📝 生成发布说明（包含更新内容和提交记录）
3. 📦 创建 GitHub Release（包含可下载的插件文件）
4. 🏷️ 自动生成版本号（格式：`vYYYY.MM.DD-运行号`）

**注意**：仅**移除插件**（删除文件）**不会触发**自动发布。只有新增或修改插件（且更新了版本号）才会触发发布。移除的插件将不会出现在发布日志中。

### 发布前必须完成 (Pre-release Requirements)

> [!IMPORTANT]
> 版本号**仅在用户明确要求发布时**才需要更新。日常代码更改**无需**更新版本号。

**触发版本更新的关键词**：
- 用户说 "发布"、"release"、"bump version"
- 用户明确要求准备发布

**Agent 主动询问发布 (Agent-Initiated Release Prompt)**：

当 Agent 完成以下类型的更改后，**应主动询问**用户是否需要发布新版本：

| 更改类型 | 示例 | 是否询问发布 |
|---------|------|-------------|
| 新功能 | 新增导出格式、新的配置选项 | ✅ 询问 |
| 重要 Bug 修复 | 修复导致崩溃或数据丢失的问题 | ✅ 询问 |
| 累积多次更改 | 同一插件在会话中被修改 >= 3 次 | ✅ 询问 |
| 小优化 | 代码清理、格式符号处理 | ❌ 不询问 |
| 文档更新 | 只改 README、注释 | ❌ 不询问 |

如果用户确认发布，Agent 需要更新所有版本相关的文件（代码、README、docs 等）。

**发布时需要完成**：
1. ✅ **更新版本号** - 修改插件文档字符串中的 `version` 字段
2. ✅ **中英文版本同步** - 确保两个版本的版本号一致

```python
"""
title: My Plugin
version: 0.2.0  # <- 发布时更新这里！
...
"""
```

### 版本编号规则 (Versioning)

遵循[语义化版本](https://semver.org/lang/zh-CN/)：

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| Bug 修复 | PATCH +1 | 0.1.0 → 0.1.1 |
| 新功能 | MINOR +1 | 0.1.1 → 0.2.0 |
| 不兼容变更 | MAJOR +1 | 0.2.0 → 1.0.0 |

### 发布方式 (Release Methods)

**方式 A：直接推送到 main（推荐）**

```bash
# 1. 暂存更改
git add plugins/actions/my-plugin/

# 2. 提交（使用规范的 commit message）
git commit -m "feat(my-plugin): add new feature X

- Add feature X for better user experience
- Fix bug Y
- Update version to 0.2.0"

# 3. 推送到 main
git push origin main

# GitHub Actions 会自动创建 Release
```

**方式 B：创建 PR（团队协作）**

```bash
# 1. 创建功能分支
git checkout -b feature/my-plugin-v0.2.0

# 2. 提交更改
git commit -m "feat(my-plugin): add new feature X"

# 3. 推送并创建 PR
git push origin feature/my-plugin-v0.2.0

# 4. PR 合并后自动触发发布
```

**方式 C：手动触发发布**

1. 前往 GitHub Actions → "Plugin Release / 插件发布"
2. 点击 "Run workflow"
3. 填写版本号和发布说明

### Commit Message 规范 (Commit Convention)

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

常用类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 代码重构
- `style`: 代码格式调整
- `perf`: 性能优化

示例：
```
feat(flash-card): add _get_user_context for safer user info retrieval

- Add _get_user_context method to handle various __user__ types
- Prevent AttributeError when __user__ is not a dict
- Update version to 0.2.2 for both English and Chinese versions
```

### 发布检查清单 (Release Checklist)

发布前确保完成以下检查：

- [ ] 更新插件版本号（英文版 + 中文版）
- [ ] 测试插件功能正常
- [ ] 确保代码通过格式检查
- [ ] 编写清晰的 commit message
- [ ] 推送到 main 分支或合并 PR

---

## �📚 参考资源 (Reference Resources)

- [Action 插件模板 (英文)](plugins/actions/ACTION_PLUGIN_TEMPLATE.py)
- [Action 插件模板 (中文)](plugins/actions/ACTION_PLUGIN_TEMPLATE_CN.py)
- [插件开发指南](plugins/actions/PLUGIN_DEVELOPMENT_GUIDE.md)
- [Lucide Icons](https://lucide.dev/icons/)
- [OpenWebUI 文档](https://docs.openwebui.com/)

---

## Author

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License

---

## 📝 Commit Message Guidelines

**Commit messages MUST be in English.** Do not use Chinese.

### Format
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Examples

✅ **Good:**
- `feat: add new export to pdf plugin`
- `fix: resolve icon rendering issue in documentation`
- `docs: update README with installation steps`

❌ **Bad:**
- `新增导出PDF插件` (Chinese is not allowed)
- `update code` (Too vague)

---

## 🤖 Git Operations (Agent Rules)

**重要规则 (CRITICAL RULES FOR AI AGENTS)**:

AI Agent（如 Copilot、Gemini、Claude 等）在执行 Git 操作时必须遵守以下规则：

| 操作 (Operation) | 允许 (Allowed) | 说明 (Description) |
|-----------------|---------------|---------------------|
| 创建功能分支 | ✅ 允许 | `git checkout -b feature/xxx` |
| 推送到功能分支 | ✅ 允许 | `git push origin feature/xxx` |
| 直接推送到 main | ❌ 禁止 | `git push origin main` 需要用户手动执行 |
| 合并到 main | ❌ 禁止 | 任何合并操作需要用户明确批准 |
| Rebase 到 main | ❌ 禁止 | 任何 rebase 操作需要用户明确批准 |

**规则详解 (Rule Details)**:

1. **Feature Branches Allowed**: Agent **可以**创建新的功能分支并推送到远程仓库
2. **No Direct Push to Main**: Agent **禁止**直接推送任何更改到 `main` 分支
3. **No Auto-Merge**: Agent **禁止**在未经用户明确批准的情况下合并任何分支到 `main`
4. **User Approval Required**: 任何影响 `main` 分支的操作（push、merge、rebase）都需要用户明确批准

> [!CAUTION]
> 违反上述规则可能导致代码库不稳定或触发意外的 CI/CD 流程。Agent 应始终在功能分支上工作，并让用户决定何时合并到主分支。

---

## ⏳ 长时间运行任务通知 (Long-running Task Notifications)

如果一个前台任务（Foreground Task）的运行时间预计超过 **3秒**，必须实现用户通知机制，以避免用户感到困惑。

**要求 (Requirements):**

1. **初始通知 (Initial Notification)**: 任务开始时**立即**发送第一条通知，告知用户正在处理中（例如：“正在使用 AI 生成中...”）。
2. **周期性通知 (Periodic Notification)**: 之后每隔 **5秒** 发送一次通知，告知用户任务仍在运行中。
3. **完成清理 (Cleanup)**: 任务完成后，应自动取消通知任务。

**代码示例 (Code Example):**

```python
import asyncio

async def long_running_task_with_notification(self, event_emitter, ...):
    # 定义实际任务
    async def actual_task():
        # ... 执行耗时操作 ...
        return result

    # 定义通知任务
    async def notification_task():
        # 立即发送首次通知
        if event_emitter:
            await self._send_notification(event_emitter, "info", "正在使用 AI 生成中...")
        
        # 之后每5秒通知一次
        while True:
            await asyncio.sleep(5)
            if event_emitter:
                await self._send_notification(event_emitter, "info", "仍在处理中，请耐心等待...")

    # 并发运行任务
    task_future = asyncio.ensure_future(actual_task())
    notify_future = asyncio.ensure_future(notification_task())

    # 等待任务完成
    done, pending = await asyncio.wait(
        [task_future, notify_future], 
        return_when=asyncio.FIRST_COMPLETED
    )

    # 取消通知任务
    if not notify_future.done():
        notify_future.cancel()

    # 获取结果
    if task_future in done:
        return task_future.result()
```
