# Copilot Instructions for awesome-openwebui

本文档定义了 OpenWebUI 插件开发的标准规范和最佳实践。Copilot 在生成代码或文档时应遵循这些准则。

This document defines the standard conventions and best practices for OpenWebUI plugin development. Copilot should follow these guidelines when generating code or documentation.

---

## 🏗️ 项目结构与命名 (Project Structure & Naming)

### 1. 双语版本要求 (Bilingual Version Requirements)

#### 插件代码 (Plugin Code)

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

#### 文档 (Documentation)

每个插件目录必须包含双语 README 文件：

- `README.md` - English documentation
- `README_CN.md` - 中文文档

#### README 结构规范 (README Structure Standard)

所有插件 README 必须遵循以下统一结构顺序：

1.  **标题 (Title)**: 插件名称，带 Emoji 图标
2.  **元数据 (Metadata)**: 作者、版本、项目链接 (一行显示)
    - 格式: `**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** x.x.x | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)`
    - **注意**: Author 和 Project 为固定值，仅需更新 Version 版本号
3.  **描述 (Description)**: 一句话功能介绍
4.  **最新更新 (What's New)**: **必须**放在描述之后，仅展示**最近 1 次**更新
5.  **核心特性 (Key Features)**: 使用 Emoji + 粗体标题 + 描述格式
6.  **使用方法 (How to Use)**: 按步骤说明
7.  **配置参数 (Configuration/Valves)**: 使用表格格式，包含参数名、默认值、描述
8.  **支持 (Support)**: **必须**包含，放在配置参数之后、故障排除之前
    - English: `If this plugin has been useful, a star on [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) is a big motivation for me. Thank you for the support.`
    - 中文: `如果这个插件对你有帮助，欢迎到 [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) 点个 Star，这将是我持续改进的动力，感谢支持。`
9.  **其他 (Others)**: 支持的模板类型、语法示例、故障排除等
    - **Changelog**: 统一指向 GitHub 项目历史，不在 README 中列出具体变更

### 2. 插件目录结构 (Plugin Directory Structure)

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
│   └── ...
├── pipes/             # Pipe 插件 (输出处理)
│   └── ...
├── pipelines/         # Pipeline 插件
    └── ...
├── debug/             # 调试与开发工具 (Debug & Development Tools)
│   ├── my_debug_tool/
│   │   ├── debug_script.py
│   │   └── notes.md
│   └── ...
```

#### 调试目录规范 (Debug Directory Standards)

`plugins/debug/` 目录用于存放调试用的脚本、临时验证代码或开发笔记。

**目录结构 (Directory Structure)**:
应根据调试工具所属的插件或功能模块进行子目录分类，而非将文件散落在根目录。

```
plugins/debug/
├── my_plugin_name/      # 特定插件的调试文件 (Debug files for specific plugin)
│   ├── debug_script.py
│   └── guides/
├── common_tools/        # 通用调试工具 (General debug tools)
│   └── ...
└── ...
```

**规范说明 (Guidelines)**:
- **不强制要求 README**: 该目录下的子项目不需要包含 `README.md`。
- **发布豁免**: 该目录下的内容**绝不会**被发布脚本处理。
- **内容灵活性**: 可以包含 Python 脚本、Markdown 文档、JSON 数据等。
- **分类存放**: 任何调试产物（如 `test_*.py`, `inspect_*.py`）都不应直接存放在项目根目录，必须移动到此目录下相应的子文件夹中。

### 3. 文档字符串规范 (Docstring Standard)

每个插件文件必须以标准化的文档字符串开头：

```python
"""
title: 插件名称 (Plugin Name)
author: Fu-Jie
author_url: https://github.com/Fu-Jie/awesome-openwebui
funding_url: https://github.com/open-webui
version: 0.1.0
icon_url: data:image/svg+xml;base64,<base64-encoded-svg>
requirements: dependency1==1.0.0, dependency2>=2.0.0
description: 插件功能的简短描述。Brief description of plugin functionality.
"""
```

#### 字段说明 (Field Descriptions)

| 字段 (Field) | 说明 (Description) | 示例 (Example) |
|--------------|---------------------|----------------|
| `title` | 插件显示名称 | `Export to Word` / `导出为 Word` |
| `author` | 作者名称 | `Fu-Jie` |
| `author_url` | 作者主页链接 | `https://github.com/Fu-Jie/awesome-openwebui` |
| `funding_url` | 赞助/项目链接 | `https://github.com/open-webui` |
| `version` | 语义化版本号 | `0.1.0`, `1.2.3` |
| `icon_url` | 图标 (Base64 编码的 SVG) | 仅 Action 插件**必须**提供。其他类型可选。 |
| `requirements` | 额外依赖 (仅 OpenWebUI 环境未安装的) | `python-docx==1.1.2` |
| `description` | 功能描述 | `将对话导出为 Word 文档` |

#### 图标规范 (Icon Guidelines)

- 图标来源：从 [Lucide Icons](https://lucide.dev/icons/) 获取符合插件功能的图标
- 适用范围：Action 插件**必须**提供，其他插件可选
- 格式：Base64 编码的 SVG
- 获取方法：从 Lucide 下载 SVG，然后使用 Base64 编码
- 示例格式：
```
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0i...（完整的 Base64 编码字符串）
```

### 4. 依赖管理 (Dependencies)

#### requirements 字段规则

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

## 💻 核心开发规范 (Core Development Standards)

### 1. Valves 配置规范 (Valves Configuration)

使用 Pydantic BaseModel 定义可配置参数：

```python
from pydantic import BaseModel, Field

class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates."
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="Whether to print debug logs in the browser console."
        )
        MODEL_ID: str = Field(
            default="",
            description="Built-in LLM Model ID. If empty, uses current conversation model."
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="Minimum text length required for processing (characters)."
        )

    def __init__(self):
        self.valves = self.Valves()
```

#### 命名规则 (Naming Convention)

- 所有 Valves 字段使用 **大写下划线** (UPPER_SNAKE_CASE)
- 示例：`SHOW_STATUS`, `MODEL_ID`, `MIN_TEXT_LENGTH`

### 2. 上下文获取规范 (Context Access)

所有插件**必须**使用 `_get_user_context` 和 `_get_chat_context` 方法来安全获取信息，而不是直接访问 `__user__` 或 `body`。

#### 用户上下文 (User Context)

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
```

#### 聊天上下文 (Chat Context)

```python
def _get_chat_context(self, body: dict, __metadata__: Optional[dict] = None) -> Dict[str, str]:
    """
    统一提取聊天上下文信息 (chat_id, message_id)。
    优先从 body 中提取，其次从 metadata 中提取。
    """
    chat_id = ""
    message_id = ""

    # 1. 尝试从 body 获取
    if isinstance(body, dict):
        chat_id = body.get("chat_id", "")
        message_id = body.get("id", "") # message_id 在 body 中通常是 id
        
        # 再次检查 body.metadata
        if not chat_id or not message_id:
            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                if not chat_id:
                    chat_id = body_metadata.get("chat_id", "")
                if not message_id:
                    message_id = body_metadata.get("message_id", "")

    # 2. 尝试从 __metadata__ 获取 (作为补充)
    if (__metadata__ and isinstance(__metadata__, dict)):
        if not chat_id:
            chat_id = __metadata__.get("chat_id", "")
        if not message_id:
            message_id = __metadata__.get("message_id", "")

    return {
        "chat_id": str(chat_id).strip(),
        "message_id": str(message_id).strip(),
    }
```

#### 使用示例

```python
async def action(self, body: dict, __user__: Optional[Dict[str, Any]] = None, __metadata__: Optional[dict] = None, ...):
    user_ctx = self._get_user_context(__user__)
    chat_ctx = self._get_chat_context(body, __metadata__)
    
    user_id = user_ctx["user_id"]
    chat_id = chat_ctx["chat_id"]
    message_id = chat_ctx["message_id"]
```

### 3. 事件发送与日志规范 (Event Emission & Logging)

#### 事件发送 (Event Emission)

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
    ntype: str = "info",
):
    """Emits a notification event (info, success, warning, error)."""
    if emitter:
        await emitter(
            {"type": "notification", "data": {"type": ntype, "content": content}}
        )
```

#### 前端控制台调试 (Frontend Console Debugging) - **优先推荐**

对于需要实时查看数据流、排查 UI 交互或内容变更的场景，**优先使用**前端控制台日志。

```python
async def _emit_debug_log(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    title: str,
    data: dict,
):
    """Print structured debug logs in the browser console."""
    if not self.valves.SHOW_DEBUG_LOG or not emitter:
        return

    try:
        js_code = f"""
            (async function() {{
                console.group("🛠️ {title}");
                console.log({json.dumps(data, ensure_ascii=False)});
                console.groupEnd();
            }})();
        """

        await emitter({"type": "execute", "data": {"code": js_code}})
    except Exception as e:
        print(f"Error emitting debug log: {e}")
```

#### 服务端日志 (Server-side Logging)

用于记录系统级错误、异常堆栈或无需前端感知的后台任务。

- **禁止使用** `print()` 语句 (除非用于简单的脚本调试)
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

### 4. 数据库连接规范 (Database Connection)

当插件需要持久化存储时，**必须**复用 Open WebUI 的内部数据库连接，而不是创建新的数据库引擎。

```python
# Open WebUI internal database (re-use shared connection)
from open_webui.internal.db import engine as owui_engine
from open_webui.internal.db import Session as owui_Session
from open_webui.internal.db import Base as owui_Base

class PluginTable(owui_Base):
    # ... definition ...
    pass

class Filter:
    def __init__(self):
        self._db_engine = owui_engine
        self._SessionLocal = owui_Session
        # ...
```

### 5. 文件存储访问规范 (File Storage Access)

插件在访问用户上传的文件或生成的图片时，必须实现多级回退机制以兼容所有存储配置（本地磁盘、S3/MinIO 等）。

推荐实现以下优先级的文件获取策略：
1. 数据库直接存储 (小文件)
2. S3 直连 (对象存储 - 最快)
3. 本地文件系统 (磁盘存储)
4. 公共 URL 下载
5. 内部 API 回调 (通用兜底方案)

(详细实现参考 `plugins/actions/export_to_docx/export_to_word.py` 中的 `_image_bytes_from_owui_file_id` 方法)

### 6. 长时间运行任务通知 (Long-running Task Notifications)

如果一个前台任务的运行时间预计超过 **3秒**，必须实现用户通知机制。

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
            await self._emit_notification(event_emitter, "正在使用 AI 生成中...", "info")
        
        # 之后每5秒通知一次
        while True:
            await asyncio.sleep(5)
            if event_emitter:
                await self._emit_notification(event_emitter, "仍在处理中，请耐心等待...", "info")

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

### 7. 前端数据获取与交互规范 (Frontend Data Access & Interaction)

#### 获取前端信息 (Retrieving Frontend Info)

当需要获取用户浏览器的上下文信息（如语言、时区、LocalStorage）时，**必须**使用 `__event_call__` 的 `execute` 类型，而不是通过文件上传或复杂的 API 请求。

```python
async def _get_frontend_value(self, js_code: str) -> str:
    """Helper to execute JS and get return value."""
    try:
        response = await __event_call__(
            {
                "type": "execute",
                "data": {
                    "code": js_code,
                },
            }
        )
        return str(response)
    except Exception as e:
        logger.error(f"Failed to execute JS: {e}")
        return ""

# 示例：获取界面语言 (Get UI Language)
async def get_user_language(self):
    js_code = """
        return (
            localStorage.getItem('locale') || 
            localStorage.getItem('language') || 
            navigator.language || 
            'en-US'
        );
    """
    return await self._get_frontend_value(js_code)
```

#### 适用场景与引导 (Usage Guidelines)

- **语言适配**: 动态获取界面语言 (`ru-RU`, `zh-CN`) 自动切换输出语言。
- **时区处理**: 获取 `Intl.DateTimeFormat().resolvedOptions().timeZone` 处理时间。
- **客户端存储**: 读取 `localStorage` 中的用户偏好设置。
- **硬件能力**: 获取 `navigator.clipboard` 或 `navigator.geolocation` (需授权)。

**注意**: 即使插件有 `Valves` 配置，也应优先尝试自动探测，提升用户体验。

### 8. 智能代理文件交付规范 (Agent File Delivery Standards)

在开发具备文件生成能力的智能代理插件（如 GitHub Copilot SDK 集成）时，必须遵循以下标准流程，以确保文件在不同存储后端（本地/S3）下的可用性并绕过不必要的 RAG 处理。

#### 核心协议：三步交付法 (The 3-Step Delivery Protocol)

1.  **本地写入 (Write Local)**:
    - 代理必须在当前执行目录 (`.`) 下创建文件。
    - **严禁**使用系统临时目录（如 `/tmp`）存放待发布的文件，因为这些路径在隔离的工作空间外不可见。
2.  **显式发布 (Publish)**:
    - 必须调用内建工具 `publish_file_from_workspace(filename='name.ext')`。
    - 该工具负责将文件迁移至 Open WebUI 正式存储（自动适配 S3），并注入 `skip_rag` 元数据以防止触发向量化流程（RAG Bypass）。
3.  **呈现链接 (Display Link)**:
    - 获取工具返回的 `download_url`（正确格式为 `/api/v1/files/{id}/content`）。
    - **必须**以 Markdown 链接形式（如 `[点击下载报告](url)`）展示给用户。

#### 路径语义 (Path Semantics)
- 代理应始终将“当前目录”视为其受保护所在的私有工作空间。
- `publish_file_from_workspace` 的参数 `filename` 仅需传入相对于当前目录的文件名。

### 9. Copilot SDK 插件工具定义规范 (Copilot SDK Tool Definition Standards)

在为 GitHub Copilot SDK 开发自定义工具时，为了确保大模型能正确识别参数（避免生成空的 `properties` Schema），必须遵循以下定义模式：

#### 显式参数模型 (Explicit Parameter Schema)
**禁止**仅依赖函数签名和类型提示。**必须**定义一个继承自 `pydantic.BaseModel` 的类来描述参数，并在 `define_tool` 中通过 `params_type` 显式引用。

```python
from pydantic import BaseModel, Field
from copilot import define_tool

# 1. 定义参数模型
class MyToolParams(BaseModel):
    query: str = Field(..., description="搜索关键词")
    limit: int = Field(default=10, description="返回结果数量限制")

# 2. 实现工具逻辑
async def my_custom_search(query: str, limit: int) -> dict:
    # ... 逻辑实现 ...
    return {"results": []}

# 3. 注册工具（关键：使用 params_type）
my_tool = define_tool(
    name="my_custom_search",
    description="在特定数据源中执行搜索",
    params_type=MyToolParams,  # 显式传递参数模型以生成正确的 JSON Schema
)(my_custom_search)
```

#### 关键要点 (Key Requirements)
1.  **params_type**: 必须在 `define_tool` 中使用此参数。这是防止大模型幻觉认为工具“无参数”的唯一可靠方法。
2.  **Field 描述**: 在 `BaseModel` 中使用 `Field(..., description="...")` 为每个参数提供详细的描述信息。
3.  **Required vs Optional**: 明确标注必填项（无默认值）和可选项（带 `default`）。

---

## ⚡ Action 插件规范 (Action Plugin Standards)

### 1. HTML 注入规范 (HTML Injection)

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

必须实现 HTML 合并方法 `_remove_existing_html` 和 `_merge_html` 以支持多次运行插件。

### 2. HTML 生成插件的完整模板 (Complete Template)

以下是生成 HTML 输出的 Action 插件需要包含的完整公共代码：

```python
import re
import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# HTML Template with insertion points
HTML_WRAPPER_TEMPLATE = """
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<!DOCTYPE html>
<html lang="{user_language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 10px; 
            background-color: transparent; 
        }
        #main-container { 
            display: flex; 
            flex-direction: column;
            gap: 16px; 
            width: 100%;
            max-width: 100%;
        }
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

class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True,
            description="Whether to show operation status updates."
        )
        SHOW_DEBUG_LOG: bool = Field(
            default=False,
            description="Whether to print debug logs in the browser console."
        )
        # ... other valves ...

    def __init__(self):
        self.valves = self.Valves()

    # ==================== Common Helper Methods ====================
    
    def _get_user_context(self, __user__: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Safely extracts user context information."""
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

    def _get_chat_context(
        self, body: dict, __metadata__: Optional[dict] = None
    ) -> Dict[str, str]:
        """
        Unified extraction of chat context information (chat_id, message_id).
        Prioritizes extraction from body, then metadata.
        """
        chat_id = ""
        message_id = ""

        if isinstance(body, dict):
            chat_id = body.get("chat_id", "")
            message_id = body.get("id", "")

            if not chat_id or not message_id:
                body_metadata = body.get("metadata", {})
                if isinstance(body_metadata, dict):
                    if not chat_id:
                        chat_id = body_metadata.get("chat_id", "")
                    if not message_id:
                        message_id = body_metadata.get("message_id", "")

        if __metadata__ and isinstance(__metadata__, dict):
            if not chat_id:
                chat_id = __metadata__.get("chat_id", "")
            if not message_id:
                message_id = __metadata__.get("message_id", "")

        return {
            "chat_id": str(chat_id).strip(),
            "message_id": str(message_id).strip(),
        }

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
        ntype: str = "info",
    ):
        """Emits a notification event (info, success, warning, error)."""
        if emitter:
            await emitter(
                {"type": "notification", "data": {"type": ntype, "content": content}}
            )

    async def _emit_debug_log(
        self,
        emitter: Optional[Callable[[Any], Awaitable[None]]],
        title: str,
        data: dict,
    ):
        """Print structured debug logs in the browser console."""
        if not self.valves.SHOW_DEBUG_LOG or not emitter:
            return

        try:
            js_code = f"""
                (async function() {{
                    console.group("🛠️ {title}");
                    console.log({json.dumps(data, ensure_ascii=False)});
                    console.groupEnd();
                }})();
            """

            await emitter({"type": "execute", "data": {"code": js_code}})
        except Exception as e:
            print(f"Error emitting debug log: {e}")

    # ==================== HTML Helper Methods ====================

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
        """Merges new content into existing HTML container."""
        if not existing_html:
            base_html = HTML_WRAPPER_TEMPLATE.replace("{user_language}", user_language)
        else:
            base_html = existing_html

        if "<!-- CONTENT_INSERTION_POINT -->" in base_html:
            base_html = base_html.replace(
                "<!-- CONTENT_INSERTION_POINT -->",
                f"{new_content}\n        <!-- CONTENT_INSERTION_POINT -->"
            )

        if new_styles and "/* STYLES_INSERTION_POINT */" in base_html:
            base_html = base_html.replace(
                "/* STYLES_INSERTION_POINT */",
                f"{new_styles}\n        /* STYLES_INSERTION_POINT */"
            )

        if new_scripts and "<!-- SCRIPTS_INSERTION_POINT -->" in base_html:
            base_html = base_html.replace(
                "<!-- SCRIPTS_INSERTION_POINT -->",
                f"{new_scripts}\n    <!-- SCRIPTS_INSERTION_POINT -->"
            )

        return base_html
```

### 3. 文件导出与命名规范 (File Export and Naming)

对于涉及文件导出的插件，必须提供灵活的标题生成策略。

#### Valves 配置

```python
class Valves(BaseModel):
    TITLE_SOURCE: str = Field(
        default="chat_title",
        description="Title Source: 'chat_title', 'ai_generated', 'markdown_title'",
    )
```

#### 优先级与回退 (Priority & Fallback)

`chat_title` -> `markdown_title` -> `user_name + date`

#### 实现示例 (Implementation Example)

```python
    async def _get_filename(
        self,
        body: dict,
        content: str,
        user_id: str,
        request: Optional[Any] = None,
    ) -> str:
        """
        Generate filename based on priority:
        1. TITLE_SOURCE (chat_title / markdown_title / ai_generated)
        2. Fallback: chat_title -> markdown_title -> user_name + date
        """
        title = ""
        chat_title = ""
        
        # 1. Get Chat Title
        chat_ctx = self._get_chat_context(body)
        chat_id = chat_ctx["chat_id"]
        if chat_id:
            chat_title = await self._fetch_chat_title(chat_id, user_id)

        # 2. Determine Title based on Valve
        source = self.valves.TITLE_SOURCE
        if source == "chat_title":
            title = chat_title
        elif source == "markdown_title":
            title = self._extract_title(content)
        elif source == "ai_generated":
            # Optional: Implement AI title generation
            # title = await self._generate_title_using_ai(body, content, user_id, request)
            pass

        # 3. Fallback Logic
        if not title:
            # Fallback to chat_title if not already tried
            if source != "chat_title" and chat_title:
                title = chat_title
            # Fallback to markdown_title if not already tried
            elif source != "markdown_title":
                title = self._extract_title(content)

        # 4. Final Fallback: User + Date
        if not title:
            user_ctx = self._get_user_context(body.get("user"))
            user_name = user_ctx["user_name"]
            date_str = datetime.datetime.now().strftime("%Y%m%d")
            title = f"{user_name}_{date_str}"

        return self._clean_filename(title)

    async def _fetch_chat_title(self, chat_id: str, user_id: str) -> str:
        try:
            from open_webui.apps.webui.models.chats import Chats
            chat = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
            return chat.title if chat else ""
        except Exception:
            return ""

    def _extract_title(self, content: str) -> str:
        """Extract title from Markdown h1 (# Title)"""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _clean_filename(self, filename: str) -> str:
        """Remove invalid characters for filenames"""
        return re.sub(r'[\\/*?:"<>|]', "", filename).strip()
```

### 4. iframe 主题检测规范 (iframe Theme Detection)

当插件在 iframe 中运行（特别是使用 `srcdoc` 属性）时，需要检测应用程序的主题以保持视觉一致性。

优先级：
1. 显式切换 (Explicit Toggle)
2. 父文档 Meta 标签 (Parent Meta Theme-Color)
3. 父文档 Class/Data-Theme (Parent HTML/Body Class)
4. 系统偏好 (System Preference)

### 5. 高级开发模式 (Advanced Development Patterns)

#### 混合服务端-客户端生成 (Hybrid Server-Client Generation)
服务端生成半成品（如 ZIP），客户端渲染复杂组件（如 Mermaid）并回填。

#### 原生 Word 公式支持 (Native Word Math Support)
使用 `latex2mathml` + `mathml2omml`。

#### JS 渲染并嵌入 Markdown (JS Render to Markdown)
利用浏览器渲染图表，导出为 Data URL 图片，回写到 Markdown 中。

#### OpenWebUI Chat API 更新规范 (Chat API Update Specification)
当插件需要修改消息内容并持久化到数据库时，必须遵循 OpenWebUI 的 Backend-Controlled API 流程。

1. **Event API**: 即时更新前端显示。
2. **Chat Persistence API**: 持久化到数据库（必须同时更新 `messages[]` 和 `history.messages`）。

---

## 🛡️ Filter 插件规范 (Filter Plugin Standards)

### 1. 状态管理 (State Management) - **关键**

Filter 实例是**单例 (Singleton)**。

- **❌ 禁止**: 使用 `self` 存储请求级别的临时状态。
- **✅ 推荐**: 无状态设计，或使用 `body` 传递临时数据。

### 2. 摘要注入角色 (Summary Injection Role)

- **✅ 推荐**: 使用 **`assistant`** 角色。

### 3. 模型默认值 (Model Defaults)

- **❌ 禁止**: 硬编码特定模型 ID。
- **✅ 推荐**: 默认值为 `None`，优先使用当前对话模型。

### 4. 异步处理 (Async Processing)

- **✅ 推荐**: 在 `outlet` 中使用 `asyncio.create_task()` 启动后台任务。

---

## 🧪 测试规范 (Testing Standards)

### 1. Copilot SDK 测试模型 (Copilot SDK Test Models)

在编写 Copilot SDK 相关的测试脚本时 (如 `test_injection.py`, `test_capabilities.py` 等)，**必须**优先使用以下免费/低成本模型之一，严禁使用高昂费用的模型进行常规测试，除非用户明确要求：

- `gpt-5-mini` (首选 / Preferred)
- `gpt-4.1`

此规则适用于所有自动化测试脚本和临时验证脚本。

---

## 🔄 工作流与流程 (Workflow & Process)

### 1. ✅ 开发检查清单 (Development Checklist)

- [ ] 创建英文版插件代码 (`plugin_name.py`)
- [ ] 创建中文版插件代码 (`plugin_name_cn.py`)
- [ ] 编写英文 README (`README.md`)
- [ ] 编写中文 README (`README_CN.md`)
- [ ] 包含标准化文档字符串
- [ ] 添加 Author 和 License 信息
- [ ] 使用 Lucide 图标
- [ ] 实现 Valves 配置
- [ ] 使用 logging 而非 print
- [ ] 测试双语界面
- [ ] **一致性检查**: 确保文档、代码、README 同步
- [ ] **README 结构**: 
    - **Key Capabilities** (英文) / **核心功能** (中文): 必须包含所有核心功能
    - **What's New** (英文) / **最新更新** (中文): 仅包含最新版本的变更信息

### 2. 🔄 一致性维护 (Consistency Maintenance)

任何插件的**新增、修改或移除**，必须同时更新：
1. **插件代码** (version)
2. **项目文档** (`docs/`)
3. **自述文件** (`README.md`)

### 3.  发布工作流 (Release Workflow)

#### 自动发布 (Automatic Release)
推送到 `main` 分支会自动触发发布。

#### 发布前必须完成
- 更新版本号（中英文同步）
- 遵循语义化版本 (SemVer)

#### Commit Message 规范
使用 Conventional Commits 格式 (`feat`, `fix`, `docs`, etc.)。
**必须**在提交标题与正文中清晰描述变更内容，确保在 Release 页面可读且可追踪。

要求：
- 标题必须包含“做了什么”与影响范围（避免含糊词）。
- 正文必须列出关键变更点（1-3 条），与实际改动一一对应。
- 若影响用户或插件行为，必须在正文标明影响与迁移说明。

推荐格式：
- `feat(actions): add export settings panel`
- `fix(filters): handle empty metadata to avoid crash`
- `docs(plugins): update bilingual README structure`

正文示例：
- Add valves for export format selection
- Update README/README_CN to include What's New section
- Migration: default TITLE_SOURCE changed to chat_title

#### 发布信息生成准则 (Release Summary Generation)
当准备提交时，必须向用户展示以下格式的“发布草案”：
1. **Commit Message**: 符合 Conventional Commits 的英文标题及摘要。
2. **变更列表 (Bilingual Changes)**: 
   - 英文: Clear descriptions of technical/functional changes.
   - 中文: 清晰描述用户可见的功能改进或修复。
3. **核查状态 (Verification)**: 确认版本号已在相关 8+ 处位置同步更新。

### 4. 🤖 Git 提交与推送规范 (Git Operations & Push Rules)

- **核心原则**: 默认仅进行**本地文件准备**（更新代码、READMEs、Docs、版本号），**严禁**在未获用户明确许可的情况下自动执行 `git commit` 或 `git push`。
- **允许 (需确认)**: 只有在用户明确表示“发布”、“Commit it”、“Release”或“提交”后，才允许直接推送到 `main` 分支或创建 PR。
- **功能分支**: 推荐在进行大规模重构或实验性功能开发时，创建功能分支 (`feature/xxx`) 进行隔离。

### 5. 🤝 贡献者认可规范 (Contributor Recognition)

使用 `@all-contributors please add @username for <type>` 指令。

---

## 📚 参考资源 (Reference Resources)

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
