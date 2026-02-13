# 原生工具显示使用指南

## 🎨 什么是原生工具显示？

原生工具显示是一项实验性功能，与 OpenWebUI 的内置工具调用可视化系统集成。启用后，工具调用及其结果将以**可折叠的 JSON 面板**显示，而不是纯文本 markdown。

### 视觉对比

**传统显示 (markdown):**

```
> 🔧 正在运行工具: `get_current_time`
> ✅ 工具已完成: 2026-01-27 10:30:00
```

**原生显示 (可折叠面板):**

- 工具调用显示在可折叠的 `assistant.tool_calls` 面板中
- 工具结果显示在单独的可折叠 `tool.content` 面板中
- JSON 语法高亮，提高可读性
- 默认折叠，点击即可展开

## 🚀 如何启用

1. 打开 GitHub Copilot SDK Pipe 配置 (Valves)
2. 将 `USE_NATIVE_TOOL_DISPLAY` 设置为 `true`
3. 保存配置
4. 开始新的对话并使用工具调用

## 📋 要求

- 支持原生工具显示的 OpenWebUI
- `__event_emitter__` 必须支持 `message` 类型事件
- 支持工具的模型（例如 GPT-4、Claude Sonnet）

## ⚙️ 工作原理

### OpenAI 标准格式

原生显示使用 OpenAI 标准消息格式：

**工具调用（助手消息）：**

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_current_time",
        "arguments": "{\"timezone\":\"UTC\"}"
      }
    }
  ]
}
```

**工具结果（工具消息）：**

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "2026-01-27 10:30:00 UTC"
}
```

### 消息流程

1. **工具执行开始**：
   - SDK 发出 `tool.execution_start` 事件
   - 插件发送带有 `tool_calls` 数组的 `assistant` 消息
   - OpenWebUI 显示可折叠的工具调用面板

2. **工具执行完成**：
   - SDK 发出 `tool.execution_complete` 事件
   - 插件发送带有 `tool_call_id` 和 `content` 的 `tool` 消息
   - OpenWebUI 显示可折叠的结果面板

## 🔧 故障排除

### 面板未显示

**症状：** 工具调用仍以 markdown 文本形式显示

**可能原因：**

1. `__event_emitter__` 不支持 `message` 类型事件
2. OpenWebUI 版本过旧
3. 功能未启用（`USE_NATIVE_TOOL_DISPLAY = false`）

**解决方案：**

- 启用 DEBUG 模式查看浏览器控制台中的错误消息
- 检查浏览器控制台的 "Native message emission failed" 警告
- 更新 OpenWebUI 到最新版本
- 保持 `USE_NATIVE_TOOL_DISPLAY = false` 使用传统 markdown 显示

### 重复的工具信息

**症状：** 工具调用同时出现在原生面板和 markdown 中

**原因：** 混合显示模式

**解决方案：**

- 确保 `USE_NATIVE_TOOL_DISPLAY` 为 `true`（仅原生）或 `false`（仅 markdown）
- 更改设置后重启对话

## 🧪 实验性状态

此功能标记为**实验性**，因为：

1. **事件发射器 API**：`__event_emitter__` 对 `message` 类型事件的支持未完全文档化
2. **OpenWebUI 版本依赖**：需要支持原生工具显示的较新 OpenWebUI 版本
3. **流式架构**：可能与流式响应存在兼容性问题

### 回退行为

如果原生消息发送失败：

- 插件自动回退到 markdown 显示
- 错误记录到浏览器控制台（启用 DEBUG 时）
- 不会中断对话流程

## 📊 性能考虑

原生显示具有略好的性能特征：

| 方面 | 原生显示 | Markdown 显示 |
|------|----------|---------------|
| **渲染** | 原生 UI 组件 | Markdown 解析器 |
| **交互性** | 可折叠面板 | 静态文本 |
| **JSON 解析** | 由 UI 处理 | 未格式化 |
| **Token 使用** | 最小开销 | 格式化 token |

## 🔮 未来增强

原生工具显示的计划改进：

- [ ] 自动回退检测
- [ ] 工具调用历史持久化
- [ ] 丰富的元数据显示（执行时间、参数预览）
- [ ] 复制工具调用 JSON 按钮
- [ ] 工具调用重放功能

## 💡 最佳实践

1. **先启用 DEBUG**：在生产环境使用前先在 DEBUG 模式下测试
2. **监控浏览器控制台**：在工具调用期间检查警告消息
3. **使用简单工具测试**：在自定义实现前先用内置工具验证
4. **保留回退选项**：在退出实验性状态前不要完全依赖原生显示

## 📖 相关文档

- [TOOLS_USAGE.md](TOOLS_USAGE.md) - 如何创建和使用自定义工具
- [NATIVE_TOOL_DISPLAY_GUIDE.md](NATIVE_TOOL_DISPLAY_GUIDE.md) - 技术实现细节
- [WORKFLOW.md](WORKFLOW.md) - 完整集成工作流程

## 🐛 报告问题

如果您在使用原生工具显示时遇到问题：

1. 启用 `DEBUG` 和 `USE_NATIVE_TOOL_DISPLAY`
2. 打开浏览器控制台（F12）
3. 触发工具调用
4. 复制任何错误消息
5. 报告到 [GitHub Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

包含：

- OpenWebUI 版本
- 浏览器和版本
- 控制台的错误消息
- 复现步骤

---

**作者:** Fu-Jie | **版本:** 0.2.0 | **许可证:** MIT
