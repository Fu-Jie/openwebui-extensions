# Pipe 插件

Pipe 插件用于创建自定义模型集成或转换 LLM 响应，会在 OpenWebUI 的模型下拉中显示。

## 什么是 Pipes？

Pipes 可以用于：

- :material-api: 连接外部 AI API（Gemini、Claude 等）
- :material-robot: 创建自定义模型封装
- :material-cog-transfer: 变换请求与响应
- :material-middleware: 实现中间件逻辑

---

## 可用的 Pipe 插件

- [GitHub Copilot SDK](github-copilot-sdk.zh.md) (v0.5.1) - GitHub Copilot SDK 官方集成。**零配置工具桥接**与**BYOK (自带 Key) 支持**。支持流式输出、多模态及无限会话。

---

## Pipe 工作原理

```mermaid
graph LR
    A[User selects Pipe as Model] --> B[Pipe receives request]
    B --> C[Transform/Route request]
    C --> D[External API / Custom Logic]
    D --> E[Return response]
    E --> F[Display to User]
```

### `pipes` 方法

定义此 Pipe 提供的模型列表：

```python
def pipes(self):
    return [
        {"id": "my-model", "name": "My Custom Model"},
        {"id": "my-model-fast", "name": "My Custom Model (Fast)"}
    ]
```

### `pipe` 方法

负责处理实际请求：

```python
def pipe(self, body: dict) -> Generator:
    # 处理请求
    messages = body.get("messages", [])
    
    # 调用外部 API 或自定义逻辑
    response = call_external_api(messages)
    
    # 返回响应（可流式）
    return response
```

---

## 快速安装

1. 下载需要的 Pipe `.py` 文件
2. 前往 **Admin Panel** → **Settings** → **Functions**
3. 上传并配置 API Key
4. 该 Pipe 会作为模型选项出现

---

## 开发模板

```python
"""
title: My Custom Pipe
author: Your Name
version: 1.0.0
description: Description of your pipe plugin
"""

from pydantic import BaseModel, Field
from typing import Generator, Iterator, Union

class Pipe:
    class Valves(BaseModel):
        API_KEY: str = Field(
            default="",
            description="API key for the external service"
        )
        API_URL: str = Field(
            default="https://api.example.com",
            description="API endpoint URL"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    def pipes(self) -> list[dict]:
        """Define available models."""
        return [
            {"id": "my-model", "name": "My Custom Model"},
        ]
    
    def pipe(
        self,
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """Process the request and return response."""
        messages = body.get("messages", [])
        model = body.get("model", "")
        
        # 自定义逻辑
        # 返回值可以是：
        # - str：单次响应
        # - Generator/Iterator：流式响应
        
        return "Response from custom pipe"
```

更多细节见 [插件开发指南](../../development/plugin-guide.md)。
