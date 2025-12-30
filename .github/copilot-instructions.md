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
