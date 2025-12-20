# OpenWebUI HTML Action 插件开发指南

> 本文档定义了开发 OpenWebUI Action 插件的标准规范和最佳实践。

## 📐 核心技术规范

### 1. Valves 配置规范 (Pydantic BaseModel)

**命名规则**: 所有字段必须使用 **大写+下划线** (UPPER_CASE)。

```python
class Valves(BaseModel):
    SHOW_STATUS: bool = Field(default=True, description="是否显示状态更新")
    MODEL_ID: str = Field(default="", description="指定模型 ID，留空则使用当前对话模型")
    MIN_TEXT_LENGTH: int = Field(default=50, description="最小字符限制")
    CLEAR_PREVIOUS_HTML: bool = Field(default=False, description="是否清除旧结果")
    # 根据需要添加更多配置...
```

**常用字段参考**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `SHOW_STATUS` | `bool` | 控制是否显示状态更新 |
| `MODEL_ID` | `str` | 允许用户指定 LLM 模型 |
| `MIN_TEXT_LENGTH` | `int` | 设置触发分析的最小字符数 |
| `MAX_TEXT_LENGTH` | `int` | 设置推荐的最大字符数 |
| `CLEAR_PREVIOUS_HTML` | `bool` | 控制是覆盖还是合并旧的插件输出 |
| `LANGUAGE` | `str` | 目标语言 (如 'zh', 'en') |

---

### 2. 事件发送规范 (Event Emission)

**禁止直接调用** `await __event_emitter__`。必须实现并使用以下辅助方法：

```python
async def _emit_status(self, emitter, description: str, done: bool = False):
    """发送状态更新事件。"""
    if self.valves.SHOW_STATUS and emitter:
        await emitter(
            {"type": "status", "data": {"description": description, "done": done}}
        )

async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
    """发送通知事件 (info/success/warning/error)。"""
    if emitter:
        await emitter(
            {"type": "notification", "data": {"type": ntype, "content": content}}
        )
```

**使用示例**:
```python
# 开始处理
await self._emit_status(__event_emitter__, "正在分析文本...", done=False)

# 处理完成
await self._emit_status(__event_emitter__, "分析完成！", done=True)
await self._emit_notification(__event_emitter__, "报告已生成", "success")

# 发生错误
await self._emit_status(__event_emitter__, "处理失败。", done=True)
await self._emit_notification(__event_emitter__, f"错误: {str(e)}", "error")
```

---

### 3. 日志与调试

- **严禁使用** `print()`
- 必须使用 Python 标准库 `logging`

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 记录关键路径
logger.info(f"Action: {__name__} started")

# 记录异常 (包含堆栈信息)
logger.error(f"处理失败: {str(e)}", exc_info=True)
```

---

### 4. HTML 注入逻辑

#### 4.1 HTML 包装器
使用统一的注释标记插件内容：
```html
<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<div class="plugin-container">
    <!-- STYLE_INSERTION_POINT -->
    <!-- CONTENT_INSERTION_POINT -->
    <!-- SCRIPT_INSERTION_POINT -->
</div>
```

#### 4.2 合并机制
必须实现以下方法，支持在同一条消息中多次运行插件：

```python
def _remove_existing_html(self, content: str) -> str:
    """移除已存在的插件 HTML 块。"""
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
    """合并新内容到已有 HTML 容器，或创建新容器。"""
    # 实现逻辑...
```

#### 4.3 注入流程
```python
# 1. 提取已有 HTML
existing_html_block = ""
match = re.search(
    r"```html\s*(<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?)```",
    original_content,
)
if match:
    existing_html_block = match.group(1)

# 2. 根据配置决定是否清除旧内容
if self.valves.CLEAR_PREVIOUS_HTML:
    original_content = self._remove_existing_html(original_content)
    final_html = self._merge_html("", new_content, new_styles, "", user_language)
else:
    # 合并到已有 HTML
    final_html = self._merge_html(existing_html_block, new_content, new_styles, "", user_language)

# 3. 注入到消息
html_embed_tag = f"```html\n{final_html}\n```"
body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"
```

---

## 📝 完整代码结构模板

```python
"""
title: 插件名称
author: 作者名
version: 0.1.0
description: 插件描述
"""

import logging
import re
import json
import time
from typing import Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, Field
from starlette.requests import Request

from open_webui.apps.webui.models.users import Users
from open_webui.main import generate_chat_completion

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============ 提示词模板 ============
SYSTEM_PROMPT = """你是一个专业的..."""
USER_PROMPT_TEMPLATE = """请分析以下内容: {content}"""

# ============ HTML 模板 ============
HTML_WRAPPER_TEMPLATE = """<!-- OPENWEBUI_PLUGIN_OUTPUT -->
<div class="plugin-container" lang="{user_language}">
<style>/* 样式 */</style>
<!-- CONTENT_INSERTION_POINT -->
</div>
"""

class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(default=True, description="是否显示状态更新")
        MODEL_ID: str = Field(default="", description="指定模型 ID")
        MIN_TEXT_LENGTH: int = Field(default=50, description="最小字符限制")
        CLEAR_PREVIOUS_HTML: bool = Field(default=False, description="是否清除旧结果")

    def __init__(self):
        self.valves = self.Valves()

    # ========== 事件发送辅助方法 ==========
    async def _emit_status(self, emitter, description: str, done: bool = False):
        if self.valves.SHOW_STATUS and emitter:
            await emitter({"type": "status", "data": {"description": description, "done": done}})

    async def _emit_notification(self, emitter, content: str, ntype: str = "info"):
        if emitter:
            await emitter({"type": "notification", "data": {"type": ntype, "content": content}})

    # ========== HTML 处理辅助方法 ==========
    def _remove_existing_html(self, content: str) -> str:
        pattern = r"```html\s*<!-- OPENWEBUI_PLUGIN_OUTPUT -->[\s\S]*?```"
        return re.sub(pattern, "", content).strip()

    def _merge_html(self, existing_html: str, new_content: str, new_styles: str = "", new_scripts: str = "", user_language: str = "en-US") -> str:
        # 实现合并逻辑...
        pass

    # ========== 主入口 ==========
    async def action(
        self,
        body: dict,
        __user__: Optional[Dict[str, Any]] = None,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __request__: Optional[Request] = None,
    ) -> Optional[dict]:
        logger.info(f"Action: {__name__} started")

        # 1. 输入校验
        messages = body.get("messages", [])
        if not messages or not messages[-1].get("content"):
            return body

        original_content = messages[-1]["content"]

        if len(original_content) < self.valves.MIN_TEXT_LENGTH:
            await self._emit_notification(__event_emitter__, "文本过短", "warning")
            return body

        # 2. 发送开始状态
        await self._emit_status(__event_emitter__, "正在处理...", done=False)

        try:
            # 3. 调用 LLM
            user_id = __user__.get("id") if __user__ else "default"
            user_obj = Users.get_user_by_id(user_id)

            target_model = self.valves.MODEL_ID or body.get("model")

            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(content=original_content)},
                ],
                "stream": False,
            }

            llm_response = await generate_chat_completion(__request__, payload, user_obj)
            result = llm_response["choices"][0]["message"]["content"]

            # 4. 生成 HTML
            # ...

            # 5. 注入到消息
            html_embed_tag = f"```html\n{final_html}\n```"
            body["messages"][-1]["content"] = f"{original_content}\n\n{html_embed_tag}"

            # 6. 发送成功通知
            await self._emit_status(__event_emitter__, "处理完成！", done=True)
            await self._emit_notification(__event_emitter__, "操作成功", "success")

        except Exception as e:
            logger.error(f"处理失败: {e}", exc_info=True)
            await self._emit_status(__event_emitter__, "处理失败", done=True)
            await self._emit_notification(__event_emitter__, f"错误: {str(e)}", "error")

        return body
```

---

## 🎨 UI 设计原则

1. **响应式**: 确保 HTML 在移动端和桌面端都能完美显示
2. **交互性**: 适当添加 JavaScript 交互（如点击展开、切换视图、复制内容）
3. **本地化**: 根据 `__user__.get("language")` 自动适配中英文界面
4. **美学设计**: 优先使用现代 UI 设计
   - 毛玻璃效果 (backdrop-filter)
   - 渐变色 (linear-gradient)
   - 圆角卡片 (border-radius)
   - Google Fonts 字体

---

## 📚 参考模板

- [英文模板](./ACTION_PLUGIN_TEMPLATE.py)
- [中文模板](./ACTION_PLUGIN_TEMPLATE_CN.py)
