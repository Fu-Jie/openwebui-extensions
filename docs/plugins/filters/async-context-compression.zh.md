# Async Context Compression（异步上下文压缩）

<span class="category-badge filter">Filter</span>
<span class="version-badge">v1.2.2</span>

通过智能摘要减少长对话的 token 消耗，同时保持对话连贯。

---

## 概览

Async Context Compression 过滤器通过以下方式帮助管理长对话的 token 使用：

- 智能总结较早的消息
- 保留关键信息
- 降低 API 成本
- 保持对话一致性

特别适用于：

- 长时间会话
- 多轮复杂讨论
- 成本优化
- 上下文长度控制

## 功能特性

- :material-arrow-collapse-vertical: **智能压缩**：AI 驱动的上下文摘要
- :material-clock-fast: **异步处理**：后台非阻塞压缩
- :material-memory: **保留上下文**：尽量保留重要信息
- :material-currency-usd-off: **降低成本**：减少 token 使用
- :material-console: **前端调试**：支持浏览器控制台日志
- :material-alert-circle-check: **增强错误报告**：清晰的错误状态通知
- :material-check-all: **Open WebUI v0.7.x 兼容性**：动态数据库会话处理
- :material-account-convert: **兼容性提升**：摘要角色改为 `assistant`
- :material-shield-check: **稳定性增强**：解决状态管理竞态条件
- :material-ruler: **预检上下文检查**：发送前验证上下文是否超限
- :material-format-align-justify: **结构感知裁剪**：保留文档结构的智能裁剪
- :material-content-cut: **原生工具输出裁剪**：自动裁剪冗长的工具输出（注意：非原生工具调用输出不会完整注入上下文）
- :material-chart-bar: **详细 Token 日志**：提供细粒度的 Token 统计
- :material-account-search: **智能模型匹配**：自定义模型自动继承基础模型配置
- :material-image-off: **多模态支持**：图片内容保留但 Token **不参与计算**

---

## 安装

1. 下载插件文件：[`async_context_compression.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/async-context-compression)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 配置压缩参数
4. 启用过滤器

---

## 工作原理

```mermaid
graph TD
    A[Incoming Messages] --> B{Token Count > Threshold?}
    B -->|No| C[Pass Through]
    B -->|Yes| D[Summarize Older Messages]
    D --> E[Preserve Recent Messages]
    E --> F[Combine Summary + Recent]
    F --> G[Send to LLM]
```

---

## 配置项

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `compression_threshold_tokens` | integer | `64000` | 超过该 token 数触发压缩 |
| `max_context_tokens` | integer | `128000` | 上下文硬性上限 |
| `keep_first` | integer | `1` | 始终保留的前 N 条消息 |
| `keep_last` | integer | `6` | 始终保留的后 N 条消息 |
| `summary_model` | string | `None` | 用于摘要的模型 |
| `summary_model_max_context` | integer | `0` | 摘要模型的最大上下文 Token 数 |
| `max_summary_tokens` | integer | `16384` | 摘要的最大 token 数 |
| `enable_tool_output_trimming` | boolean | `false` | 启用长工具输出裁剪 |

---

## 示例

### 压缩前

```
[Message 1] User: Tell me about Python...
[Message 2] AI: Python is a programming language...
[Message 3] User: What about its history?
[Message 4] AI: Python was created by Guido...
[Message 5] User: And its features?
[Message 6] AI: Python has many features...
... (many more messages)
[Message 20] User: Current question
```

### 压缩后

```
[Summary] Previous conversation covered Python basics,
history, features, and common use cases...

[Message 18] User: Recent question about decorators
[Message 19] AI: Decorators in Python are...
[Message 20] User: Current question
```

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上
    - 需要可用的 LLM 用于摘要

!!! tip "最佳实践"
    - 根据模型上下文窗口设置合适的 token 阈值
    - 技术讨论可适当提高 `preserve_recent`
    - 先在非关键对话中测试压缩效果

---

## 常见问题

??? question "没有触发压缩？"
    检查 token 数是否超过配置的阈值，并开启调试日志了解细节。

??? question "重要上下文丢失？"
    提高 `preserve_recent` 或降低压缩比例。

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/async-context-compression){ .md-button }
