# 开发指南

了解如何开发插件并为 OpenWebUI Extensions 做出贡献。

---

## 快速开始

<div class="grid cards" markdown>

-   :material-book-open-page-variant:{ .lg .middle } **插件开发指南**

    ---

    从入门到高级模式、最佳实践的完整指南。

    [:octicons-arrow-right-24: 阅读指南](plugin-guide.md)

-   :material-file-document-edit:{ .lg .middle } **文档编写指南**

    ---

    学习如何使用 MkDocs 与 Material 主题编写和贡献文档。

    [:octicons-arrow-right-24: 阅读指南](documentation-guide.md)

-   :material-github:{ .lg .middle } **贡献指南**

    ---

    了解如何贡献插件、提示词与文档。

    [:octicons-arrow-right-24: 贡献说明](../contributing.md)

</div>

---

## 插件类型概览

OpenWebUI 支持三种主要插件类型：

| 类型 | 目的 | 入口方法 |
|------|---------|--------------|
| **Action** | 为消息添加按钮 | `action()` |
| **Filter** | 处理消息 | `inlet()` / `outlet()` |
| **Pipe** | 自定义模型集成 | `pipe()` |

---

## 快速开始模板

### Action 插件

```python
"""
title: My Action
author: Your Name
version: 1.0.0
"""

class Action:
    async def action(self, body: dict, __event_emitter__=None):
        await __event_emitter__({"type": "notification", "data": {"content": "Hello!"}})
        return body
```

### Filter 插件

```python
"""
title: My Filter
author: Your Name
version: 1.0.0
"""

class Filter:
    async def inlet(self, body: dict, __metadata__: dict) -> dict:
        # 发送到 LLM 之前处理
        return body
    
    async def outlet(self, body: dict, __metadata__: dict) -> dict:
        # LLM 返回后处理
        return body
```

### Pipe 插件

```python
"""
title: My Pipe
author: Your Name
version: 1.0.0
"""

class Pipe:
    def pipes(self):
        return [{"id": "my-model", "name": "My Model"}]
    
    def pipe(self, body: dict):
        return "Response from custom pipe"
```

---

## 核心概念

### Valves 配置

Valves 允许用户在界面中配置插件：

```python
from pydantic import BaseModel, Field

class Action:
    class Valves(BaseModel):
        api_key: str = Field(default="", description="API Key")
        enabled: bool = Field(default=True, description="Enable plugin")
    
    def __init__(self):
        self.valves = self.Valves()
```

### 事件发送器

发送通知与状态更新：

```python
# Notification
await __event_emitter__({
    "type": "notification",
    "data": {"type": "success", "content": "Done!"}
})

# Status update
await __event_emitter__({
    "type": "status",
    "data": {"description": "Processing...", "done": False}
})
```

### 用户上下文

获取用户信息：

```python
user_name = __user__.get("name", "User")
user_id = __user__.get("id")
user_language = __user__.get("language", "en-US")
```

---

## 最佳实践

1. **异步操作**：I/O 请使用 `async/await`
2. **错误处理**：捕获异常并通知用户
3. **状态反馈**：长耗时操作提供进度提示
4. **配置化**：使用 Valves 暴露可调参数
5. **文档**：提供清晰的 docstring 与 README

---

## 资源

- [完整开发指南](plugin-guide.md)
- [插件示例](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins)
- [OpenWebUI 文档](https://docs.openwebui.com/)
