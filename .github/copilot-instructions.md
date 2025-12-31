# Copilot Instructions for awesome-openwebui

本文档定义了 OpenWebUI 插件开发的标准规范和最佳实践。Copilot 在生成代码或文档时应遵循这些准则。

This document defines the standard conventions and best practices for OpenWebUI plugin development. Copilot should follow these guidelines when generating code or documentation.

---

## 📚 双语版本要求 (Bilingual Version Requirements)

### 插件代码 (Plugin Code)

每个插件必须提供两个版本：

1. **英文版本**: `plugin_name.py` - 英文界面、提示词和注释
2. **中文版本**: `plugin_name_cn.py` 或 `插件中文名.py` - 中文界面、提示词和注释

示例：
```
plugins/actions/export_to_docx/
├── export_to_word.py      # English version
├── 导出为Word.py           # Chinese version
├── README.md               # English documentation
└── README_CN.md            # Chinese documentation
```

### 文档 (Documentation)

每个插件目录必须包含双语 README 文件：

- `README.md` - English documentation
- `README_CN.md` - 中文文档

README 文件应包含以下内容：
- 功能描述 / Feature description
- 配置参数及默认值 / Configuration parameters with defaults
- 安装和设置说明 / Installation and setup instructions
- 使用示例 / Usage examples
- 故障排除指南 / Troubleshooting guide
- 版本和作者信息 / Version and author information

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

## 👤 作者和许可证信息 (Author and License)

所有 README 文件和主要文档必须包含以下统一信息：

```markdown
## Author

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## License

MIT License
```

中文版本：

```markdown
## 作者

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)

## 许可证

MIT License
```

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

## 🔧 代码规范 (Code Style)

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

---

## � 发布工作流 (Release Workflow)

### 自动发布 (Automatic Release)

当插件更新推送到 `main` 分支时，会**自动触发**发布流程：

1. 🔍 检测版本变化（与上次 release 对比）
2. 📝 生成发布说明（包含更新内容和提交记录）
3. 📦 创建 GitHub Release（包含可下载的插件文件）
4. 🏷️ 自动生成版本号（格式：`vYYYY.MM.DD-运行号`）

### 发布前必须完成 (Pre-release Requirements)

1. ✅ **更新版本号** - 修改插件文档字符串中的 `version` 字段
2. ✅ **中英文版本同步** - 确保两个版本的版本号一致

```python
"""
title: My Plugin
version: 0.2.0  # <- 必须更新这里！
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
