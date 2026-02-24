# OpenWebUI 插件开发权威指南

> 本指南整合了官方文档、SDK 详解及最佳实践，旨在为开发者提供一份从入门到精通的系统化教程。

## 📚 目录

1. [插件开发快速入门](#1-插件开发快速入门)
2. [核心概念与 SDK 详解](#2-核心概念与-sdk-详解)
3. [插件类型深度解析](#3-插件类型深度解析)
    * [Action (动作)](#31-action-动作)
    * [Filter (过滤器)](#32-filter-过滤器)
    * [Pipe (管道)](#33-pipe-管道)
4. [高级开发模式](#4-高级开发模式)
5. [最佳实践与设计原则](#5-最佳实践与设计原则)
6. [仓库规范（openwebui-extensions）](#6-仓库规范openwebui-extensions)
7. [自定义 Agents 设计建议](#7-自定义-agents-设计建议)
8. [故障排查](#8-故障排查)

---

## 1. 插件开发快速入门

### 1.1 什么是 OpenWebUI 插件？

OpenWebUI 插件（官方称为 "Functions"）是扩展平台功能的主要方式。它们运行在后端 Python 环境中，允许你：

* 🔌 **集成新模型**：通过 Pipe 接入 Claude、Gemini 或自定义 RAG。
* 🎨 **增强交互**：通过 Action 在消息旁添加按钮（如"导出"、"生成图表"）。
* 🔧 **干预流程**：通过 Filter 在请求前后修改数据（如注入上下文、敏感词过滤）。

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

## 2. 核心概念与 SDK 详解

### 2.1 ⚠️ 重要：同步与异步

OpenWebUI 插件运行在 `asyncio` 事件循环中。

* **原则**：所有 I/O 操作（数据库、文件、网络）必须非阻塞。
* **陷阱**：直接调用同步方法（如 `time.sleep`, `requests.get`）会卡死整个服务器。
* **解决**：使用 `await asyncio.to_thread(sync_func, ...)` 包装同步调用。

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

* **`Valves`**: 管理员全局配置。
* **`UserValves`**: 用户级配置（优先级更高，可覆盖全局）。

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

## 3. 插件类型深度解析

### 3.1 Action (动作)

**定位**：在消息下方添加按钮，用户点击触发。

#### 高级用法：前端执行 JavaScript (文件下载示例)

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

### 3.2 Filter (过滤器)

**定位**：中间件，拦截并修改请求/响应。

* **`inlet`**: 请求前。用于注入上下文、修改模型参数。
* **`outlet`**: 响应后。用于格式化输出、保存日志。
* **`stream`**: 流式处理中。用于实时敏感词过滤。

#### 示例：注入环境变量

```python
async def inlet(self, body, __metadata__):
    vars = __metadata__.get("variables", {})
    context = f"当前时间: {vars.get('{{CURRENT_DATETIME}}')}"
    
    # 注入到 System Prompt 或第一条消息
    if body.get("messages"):
        body["messages"][0]["content"] += f"\n\n{context}"
    return body
```

### 3.3 Pipe (管道)

**定位**：自定义模型/代理。

#### 示例：简单的 OpenAI 代理

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

## 4. 高级开发模式

### 4.1 Pipe 与 Filter 协同

利用 `__request__.app.state` 在不同插件间共享数据。

* **Pipe**: `__request__.app.state.search_results = [...]`
* **Filter (Outlet)**: 读取 `search_results` 并将其格式化为引用链接附加到回复末尾。

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

---

## 5. 最佳实践与设计原则

### 5.1 命名与定位

* **简短有力**：如 "闪记卡", "精读"。避免 "文本分析助手" 这种泛词。
* **功能互补**：不要重复造轮子，明确你的插件解决了什么特定问题。

### 5.2 用户体验 (UX)

* **反馈及时**：耗时操作前先发送 `notification` ("正在生成...")。
* **视觉美观**：Action 输出 HTML 时，使用现代化的 CSS（圆角、阴影、渐变）。
* **智能引导**：检测到文本过短时，提示用户"建议输入更多内容以获得更好结果"。

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

## 6. 仓库规范（openwebui-extensions）

### 6.1 单文件 i18n 规范

本仓库要求每个插件采用**单文件源码 + 内置多语言**方案，禁止按语言拆分多个 `.py` 文件。

* 代码路径规范：`plugins/{type}/{name}/{name}.py`
* 文档规范：必须同时提供 `README.md` 与 `README_CN.md`

### 6.2 上下文访问规范（必选）

优先通过 `_get_user_context` 与 `_get_chat_context` 提取上下文，避免直接硬编码读取 `__user__` 或 `body` 字段。

### 6.3 事件与日志规范

* 用状态/通知事件给用户反馈进度。
* 前端调试优先使用 `execute` 注入的控制台日志。
* 后端统一使用 Python `logging`，生产代码避免 `print()`。

### 6.4 前端语言探测防卡死

通过 `__event_call__` 获取前端语言时，必须同时满足：

* JS 端 `try...catch` 并保证返回值
* 后端 `asyncio.wait_for(..., timeout=2.0)`

这样可以避免前端异常导致后端永久等待。

### 6.5 Copilot SDK 工具参数定义

开发 Copilot SDK 工具时，应使用 `pydantic.BaseModel` 显式声明参数，并在 `define_tool(...)` 中通过 `params_type` 传入。

### 6.6 Copilot SDK 流式输出格式

* 思考过程使用原生 `<think>...</think>`。
* 正文或工具卡片输出前，必须先闭合 `</think>`。
* 工具卡片使用 `<details type="tool_calls" ...>` 原生结构。
* `arguments` 与 `result` 属性中的双引号必须转义为 `&quot;`。

### 6.7 从源码提炼的实战模式（建议直接复用）

以下模式来自 `github_copilot_sdk.py` 与 `workspace_file_manager.py`：

* **工具参数防漂移**：工具定义使用 `params_type=BaseModel`，执行时用 `model_dump(exclude_unset=True)`，避免把未提供参数传成 `None` 覆盖函数默认值。
* **工具名规范化**：将工具名限制为 `^[a-zA-Z0-9_-]+$`，若全中文等导致空名，使用 `md5` 后缀兜底，保证 SDK 可注册。
* **工作区沙箱**：所有文件路径在解析后必须校验仍位于 workspace 根目录内，阻断目录穿越。
* **文件发布三段式**：本地写入 -> `publish_file_from_workspace` -> 返回 `/api/v1/files/{id}/content`；并写入 `skip_rag=true` 元数据。
* **S3/本地双通道上传**：优先走 API 上传（兼容对象存储），失败再回退 DB + 本地文件。
* **流式渲染稳定性**：`assistant.message_delta` 前确保关闭 `<think>`，避免正文被吞进思考块。
* **原生工具卡片输出**：`tool.execution_complete` 统一输出 `<details type="tool_calls">`，并对属性执行 HTML 转义（尤其 `&quot;`、换行）。
* **TODO 持久化联动**：`update_todo` 成功后同时回写 `TODO.md` 与数据库，保持会话可恢复。

### 6.8 从 `plugins/` 全量提炼的开发知识（Action / Filter / Pipe / Pipeline / Tool）

以下内容来自 `plugins/` 真实源码的横向归纳：

* **Action 输入治理**：统一抽取多模态文本内容，注入新 HTML 前清理旧插件块（`OPENWEBUI_PLUGIN_OUTPUT`），并在调用模型前做最小长度校验。
* **Action i18n 工程化**：采用 `TRANSLATIONS + fallback_map + 基础语言回退`（如 `fr-CA -> fr-FR`、`en-GB -> en-US`），状态/UI/JS 文案统一走翻译键，并对 `format(**kwargs)` 做异常兜底。
* **前端语言探测（生产可用）**：优先链路为 `document.lang -> localStorage(locale/language) -> navigator.language -> profile/request`，且 `__event_call__(execute)` 必须加超时保护。
* **长任务体验模式**：开始即发送 `status + notification`，处理中分阶段更新，失败时对用户提示简洁并将详情写入后端日志。
* **HTML 插件可组合模式**：通过样式/内容/脚本插入点支持多次累积，兼容覆盖模式（`CLEAR_PREVIOUS_HTML`）与合并模式。
* **iframe 主题一致性**：从父页面 `meta[name=theme-color]`、父级 class/data-theme、系统主题逐级判定明暗，并在导出 SVG/PNG 时注入主题样式。
* **前端渲染-导出-回写闭环**：离屏渲染图表/思维导图后导出 SVG/PNG 并上传 `/api/v1/files/`，再通过事件 API + 持久化 API 同步更新消息。
* **DOCX 导出实战模式**：使用 `TITLE_SOURCE` 回退链（`chat_title -> markdown_title -> 用户名+日期`），导出前剔除 reasoning 块，公式走 `latex2mathml + mathml2omml` 并支持降级，引用可落地为参考文献与锚点。
* **OpenWebUI 文件读取多级回退**：DB 内联字节/base64 -> S3 直连 -> 本地路径多变体 -> 公共 URL -> 内部 API `/api/v1/files/{id}/content` -> 原始对象字段，且每层都做字节上限控制。
* **Filter 单例安全**：不在 `self` 保存请求级临时状态，请求内数据应基于 `body` 与上下文方法即时计算。
* **异步上下文压缩模式**：采用 `inlet` 注入历史摘要 + `outlet` 异步生成新摘要，支持模型级阈值覆盖、快速估算与精算切换，并保护系统提示（`effective_keep_first`）。
* **模型兼容性护栏**：对不兼容模型族（如 `copilot_sdk`）跳过特定处理，默认优先使用当前会话模型，避免硬编码。
* **文件夹记忆（Folder Memory）模式**：每 N 条消息触发规则提炼，使用 `RULES_BLOCK_START/END` 做幂等替换，并可选上推至根文件夹。
* **工作区工具加固**：`list/read/write/delete/publish` 全链路做路径越界校验，读写设置大小限制并区分文本/二进制，发布后返回可直接展示的 Markdown 下载链接。
* **MoE 提示词精炼（Pipeline）模式**：通过触发前缀识别聚合请求，解析原问题与多模型回答后重写为综合分析主提示词，并支持聚合阶段模型切换。

### 6.9 Copilot 相关工程化配置

为了同时支持 **GitHub Copilot + Gemini CLI + 反重力开发**，建议采用以下工程化控制：

* **主辅双通道**：Copilot 负责主实现，Gemini CLI 负责草案与交叉校验。
* **统一合入契约**：两条通道都必须遵守同一仓库规范（单文件 i18n、上下文方法、事件规范、发布规则）。
* **工具参数治理**：Copilot SDK 工具必须使用 Pydantic `params_type` 显式建模。
* **反重力安全机制**：小步可回滚、超时保护、回退链路、输出路径确定性。
* **文件创建协议**：在 workspace 范围内创建，按发布流程输出，并返回 `/api/v1/files/{id}/content` 进行交付。

设计文档：

* `docs/development/copilot-engineering-plan.zh.md`

---

## 7. 自定义 Agents 设计建议

### 7.1 推荐架构（适合你的项目）

* **Orchestrator Pipe**：负责会话、模型路由、流式事件。
* **Tool Adapter Layer**：统一接入 OpenWebUI Tools / OpenAPI / MCP，并做参数校验与名称规范化。
* **Workspace I/O Layer**：统一文件读写、发布、沙箱校验。
* **Render Layer**：统一处理 `<think>`、工具卡片、通知事件。

### 7.2 最小可用 Agent 清单（MVP）

1. `Valves + UserValves` 双层配置（用户优先覆盖）。
2. `_get_user_context` / `_get_chat_context` 统一上下文入口。
3. 至少 1 个可落地产物工具（如 `publish_file_from_workspace`）。
4. 流式事件最小闭环：`reasoning_delta`、`message_delta`、`tool.execution_complete`。
5. 错误统一走通知事件，不静默失败。

### 7.3 你现在就可以新增的 3 类 Agent

* **Repo Analyst Agent**：扫描仓库并输出“架构图 + 风险清单 + 重构建议”。
* **Release Draft Agent**：自动生成 Conventional Commit、双语变更摘要、发布检查清单。
* **Docs Sync Agent**：对比代码与文档版本差异，自动给出需同步文件列表。

### 7.4 实施优先级建议

* **P0**：先做 `Release Draft Agent`（收益最高、风险最低）。
* **P1**：再做 `Docs Sync Agent`（减少文档漂移）。
* **P2**：最后做 `Repo Analyst Agent`（用于中长期演进）。

---

## 8. 故障排查

* **HTML 不显示？** 确保包裹在 ` ```html ... ``` ` 代码块中。
* **数据库报错？** 检查是否在 `async` 函数中直接调用了同步的 DB 方法，请使用 `asyncio.to_thread`。
* **参数未生效？** 检查 `Valves` 定义是否正确，以及是否被 `UserValves` 覆盖。
