# OpenWebUI 插件开发权威指南

> 本指南整合了官方文档、SDK 详解及最佳实践，旨在为开发者提供一份从入门到精通的系统化教程。

## 📚 目录

1.  [插件开发快速入门](#1-quick-start)
2.  [核心概念与 SDK 详解](#2-core-concepts-sdk-details)
3.  [插件类型深度解析](#3-plugin-types)
    *   [Action (动作)](#31-action)
    *   [Filter (过滤器)](#32-filter)
    *   [Pipe (管道)](#33-pipe)
4.  [高级开发模式](#4-advanced-patterns)
5.  [最佳实践与设计原则](#5-best-practices)
6.  [故障排查](#6-troubleshooting)

---

## 1. 插件开发快速入门 {: #1-quick-start }

### 1.1 什么是 OpenWebUI 插件？

OpenWebUI 插件（官方称为 "Functions"）是扩展平台功能的主要方式。它们运行在后端 Python 环境中，允许你：
*   🔌 **集成新模型**：通过 Pipe 接入 Claude、Gemini 或自定义 RAG。
*   🎨 **增强交互**：通过 Action 在消息旁添加按钮（如"导出"、"生成图表"）。
*   🔧 **干预流程**：通过 Filter 在请求前后修改数据（如注入上下文、敏感词过滤）。

### 1.2 你的第一个插件 (Hello World)

保存以下代码为 `hello.py` 并上传到 OpenWebUI 的 **Functions** 面板：

```python
"""
title: Hello World Action
author: Demo
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional

class Action:
    class Valves(BaseModel):
        greeting: str = Field(default="你好", description="问候语")

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __event_emitter__=None,
        __user__=None
    ) -> Optional[dict]:
        user_name = __user__.get("name", "朋友") if __user__ else "朋友"
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "notification",
                "data": {"type": "success", "content": f"{self.valves.greeting}, {user_name}!"}
            })
        return body
```

---

## 2. 核心概念与 SDK 详解 {: #2-core-concepts-sdk-details }

### 2.1 ⚠️ 重要：同步与异步

OpenWebUI 插件运行在 `asyncio` 事件循环中。
*   **原则**：所有 I/O 操作（数据库、文件、网络）必须非阻塞。
*   **陷阱**：直接调用同步方法（如 `time.sleep`, `requests.get`）会卡死整个服务器。
*   **解决**：使用 `await asyncio.to_thread(sync_func, ...)` 包装同步调用。

### 2.2 核心参数详解

所有插件方法（`inlet`, `outlet`, `pipe`, `action`）都支持注入以下特殊参数：

| 参数名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `body` | `dict` | **核心数据**。包含 `messages`, `model`, `stream` 等请求信息。 |
| `__user__` | `dict` | **当前用户**。包含 `id`, `name`, `role`, `valves` (用户配置) 等。 |
| `__metadata__` | `dict` | **元数据**。包含 `chat_id`, `message_id`。其中 `variables` 字段包含 `{{USER_NAME}}`, `{{CURRENT_TIME}}` 等预置变量。 |
| `__request__` | `Request` | **FastAPI 请求对象**。可访问 `app.state` 进行跨插件通信。 |
| `__event_emitter__` | `func` | **单向通知**。用于发送 Toast 通知或状态条更新。 |
| `__event_call__` | `func` | **双向交互**。用于在前端执行 JS 代码、弹出确认框或输入框。 |

### 2.3 配置系统 (Valves)

*   **`Valves`**: 管理员全局配置。
*   **`UserValves`**: 用户级配置（优先级更高，可覆盖全局）。

```python
class Filter:
    class Valves(BaseModel):
        API_KEY: str = Field(default="", description="全局 API Key")
        
    class UserValves(BaseModel):
        API_KEY: str = Field(default="", description="用户私有 API Key")
        
    def inlet(self, body, __user__):
        # 优先使用用户的 Key
        user_valves = __user__.get("valves", self.UserValves())
        api_key = user_valves.API_KEY or self.valves.API_KEY
```

---

## 3. 插件类型深度解析 {: #3-plugin-types }

### 3.1 Action (动作) {: #31-action }

**定位**：在消息下方添加按钮，用户点击触发。

**高级用法：前端执行 JavaScript (文件下载示例)**

```python
import base64

async def action(self, body, __event_call__):
    # 1. 后端生成内容
    content = "Hello OpenWebUI".encode()
    b64 = base64.b64encode(content).decode()
    
    # 2. 发送 JS 到前端执行
    js = f"""
    const blob = new Blob([atob('{b64}')], {{type: 'text/plain'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'hello.txt';
    a.click();
    """
    await __event_call__({"type": "execute", "data": {"code": js}})
```

### 3.2 Filter (过滤器) {: #32-filter }

**定位**：中间件，拦截并修改请求/响应。

*   **`inlet`**: 请求前。用于注入上下文、修改模型参数。
*   **`outlet`**: 响应后。用于格式化输出、保存日志。
*   **`stream`**: 流式处理中。用于实时敏感词过滤。

**示例：注入环境变量**

```python
async def inlet(self, body, __metadata__):
    vars = __metadata__.get("variables", {})
    context = f"当前时间: {vars.get('{{CURRENT_DATETIME}}')}"
    
    # 注入到 System Prompt 或第一条消息
    if body.get("messages"):
        body["messages"][0]["content"] += f"\n\n{context}"
    return body
```

### 3.3 Pipe (管道) {: #33-pipe }

**定位**：自定义模型/代理。

**示例：简单的 OpenAI 代理**

```python
import requests

class Pipe:
    def pipes(self):
        return [{"id": "my-gpt", "name": "My GPT Wrapper"}]

    def pipe(self, body):
        # 可以在这里修改 body，例如强制添加 prompt
        headers = {"Authorization": f"Bearer {self.valves.API_KEY}"}
        r = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, stream=True)
        return r.iter_lines()
```

---

## 4. 高级开发模式 {: #4-advanced-patterns }

### 4.1 Pipe 与 Filter 协同
利用 `__request__.app.state` 在不同插件间共享数据。
*   **Pipe**: `__request__.app.state.search_results = [...]`
*   **Filter (Outlet)**: 读取 `search_results` 并将其格式化为引用链接附加到回复末尾。

### 4.2 异步后台任务
不阻塞用户响应，在后台执行耗时操作（如生成总结、存库）。

```python
import asyncio

async def outlet(self, body, __metadata__):
    asyncio.create_task(self.background_job(__metadata__["chat_id"]))
    return body

async def background_job(self, chat_id):
    # 执行耗时操作...
    pass
```

### 4.3 JS 渲染并嵌入 Markdown (Data URL 嵌入)

对于需要复杂前端渲染（如 AntV 图表、Mermaid 图表）但希望结果**持久化为纯 Markdown 格式**的场景，推荐使用 Data URL 嵌入模式：

#### 工作流程

```
┌──────────────────────────────────────────────────────────────┐
│  1. Python Action                                             │
│     ├── 分析消息内容                                           │
│     ├── 调用 LLM 生成结构化数据（可选）                         │
│     └── 通过 __event_call__ 发送 JS 代码到前端                 │
├──────────────────────────────────────────────────────────────┤
│  2. Browser JS (通过 __event_call__)                          │
│     ├── 动态加载可视化库                                       │
│     ├── 离屏渲染 SVG/Canvas                                    │
│     ├── 使用 toDataURL() 导出 Base64 Data URL                  │
│     └── 通过 REST API 更新消息内容                             │
├──────────────────────────────────────────────────────────────┤
│  3. Markdown 渲染                                             │
│     └── 显示 ![描述](data:image/svg+xml;base64,...)           │
└──────────────────────────────────────────────────────────────┘
```

#### Python 端（发送 JS 执行）

```python
async def action(self, body, __event_call__, __metadata__, ...):
    chat_id = self._extract_chat_id(body, __metadata__)
    message_id = self._extract_message_id(body, __metadata__)
    
    # 生成 JS 代码
    js_code = self._generate_js_code(
        chat_id=chat_id,
        message_id=message_id,
        data=processed_data,
    )
    
    # 执行 JS
    if __event_call__:
        await __event_call__({
            "type": "execute",
            "data": {"code": js_code}
        })
```

#### JavaScript 端（渲染并回写）

```javascript
(async function() {
    // 1. 加载可视化库
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
    const instance = new VisualizationLib({ container });
    instance.render(data);
    
    // 4. 导出为 Data URL
    const dataUrl = await instance.toDataURL({ type: 'svg', embedResources: true });
    
    // 5. 清理
    instance.destroy();
    document.body.removeChild(container);
    
    // 6. 生成 Markdown 图片
    const markdownImage = `![图表](${dataUrl})`;
    
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
- **自包含**：图片以 Base64 Data URL 嵌入，无外部依赖
- **持久化**：通过 API 回写，消息重新加载后图片仍然存在
- **跨平台**：任何支持 Markdown 图片的客户端都能显示

#### HTML 注入 vs JS 渲染嵌入 Markdown

| 特性 | HTML 注入 | JS 渲染 + Markdown 图片 |
|------|----------|------------------------|
| 输出格式 | HTML 代码块 | Markdown 图片 |
| 交互性 | ✅ 支持按钮、动画 | ❌ 静态图片 |
| 外部依赖 | 需要加载 JS 库 | 无（图片自包含） |
| 持久化 | 依赖浏览器渲染 | ✅ 永久可见 |
| 文件导出 | 需特殊处理 | ✅ 直接导出 |
| 适用场景 | 交互式内容 | 信息图、图表快照 |

#### 参考实现

- `plugins/actions/infographic/infographic.py` - 基于 AntV + Data URL 的生产级实现

## 5. 最佳实践与设计原则 {: #5-best-practices }

### 5.1 命名与定位
*   **简短有力**：如 "闪记卡", "精读"。避免 "文本分析助手" 这种泛词。
*   **功能互补**：不要重复造轮子，明确你的插件解决了什么特定问题。

### 5.2 用户体验 (UX)
*   **反馈及时**：耗时操作前先发送 `notification` ("正在生成...")。
*   **视觉美观**：Action 输出 HTML 时，使用现代化的 CSS（圆角、阴影、渐变）。
*   **智能引导**：检测到文本过短时，提示用户"建议输入更多内容以获得更好结果"。

### 5.3 错误处理
永远不要让插件静默失败。捕获异常并通过 `__event_emitter__` 告知用户。

```python
try:
    # 业务逻辑
except Exception as e:
    await __event_emitter__({
        "type": "notification",
        "data": {"type": "error", "content": f"处理失败: {str(e)}"}
    })
```

---

## 6. 故障排查 {: #6-troubleshooting }

*   **HTML 不显示？** 确保包裹在 ` ```html ... ``` ` 代码块中。
*   **数据库报错？** 检查是否在 `async` 函数中直接调用了同步的 DB 方法，请使用 `asyncio.to_thread`。
*   **参数未生效？** 检查 `Valves` 定义是否正确，以及是否被 `UserValves` 覆盖。
