# 异步上下文压缩过滤器

**作者:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **版本:** 1.2.2 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可证:** MIT

> **重要提示**：为了确保所有过滤器的可维护性和易用性，每个过滤器都应附带清晰、完整的文档，以确保其功能、配置和使用方法得到充分说明。

本过滤器通过智能摘要和消息压缩技术，在保持对话连贯性的同时，显著降低长对话的 Token 消耗。

## 1.2.2 版本更新

- **严重错误修复**: 解决了因日志函数变量名冲突导致的 `TypeError: 'str' object is not callable` 错误。
- **兼容性增强**: 改进了 `params` 处理逻辑以支持 Pydantic 对象，提高了对不同 OpenWebUI 版本的兼容性。

---

## 核心特性

- ✅ **自动压缩**: 基于 Token 阈值自动触发上下文压缩。
- ✅ **异步摘要**: 后台生成摘要，不阻塞当前对话响应。
- ✅ **持久化存储**: 复用 Open WebUI 共享数据库连接，自动支持 PostgreSQL/SQLite 等。
- ✅ **灵活保留策略**: 可配置保留对话头部和尾部消息，确保关键信息连贯。
- ✅ **智能注入**: 将历史摘要智能注入到新上下文中。
- ✅ **结构感知裁剪**: 智能折叠过长消息，保留文档骨架（标题、首尾）。
- ✅ **原生工具输出裁剪**: 支持裁剪冗长的工具调用输出。
- ✅ **实时监控**: 实时监控上下文使用情况，超过 90% 发出警告。
- ✅ **详细日志**: 提供精确的 Token 统计日志，便于调试。
- ✅ **智能模型匹配**: 自定义模型自动继承基础模型的阈值配置。
- ⚠ **多模态支持**: 图片内容会被保留，但其 Token **不参与计算**。请相应调整阈值。

详细的工作原理和流程请参考 [工作流程指南](WORKFLOW_GUIDE_CN.md)。

---

## 安装与配置

### 1. 数据库（自动）

- 自动使用 Open WebUI 的共享数据库连接，**无需额外配置**。
- 首次运行自动创建 `chat_summary` 表。

### 2. 过滤器顺序

- 建议顺序：前置过滤器（<10）→ 本过滤器（10）→ 后置过滤器（>10）。

---

## 配置参数

您可以在过滤器的设置中调整以下参数：

### 核心参数

| 参数                           | 默认值   | 描述                                                                                  |
| :----------------------------- | :------- | :------------------------------------------------------------------------------------ |
| `priority`                     | `10`     | 过滤器执行顺序，数值越小越先执行。                                                    |
| `compression_threshold_tokens` | `64000`  | **重要**: 当上下文总 Token 超过此值时后台生成摘要，建议设为模型上下文窗口的 50%-70%。 |
| `max_context_tokens`           | `128000` | **重要**: 上下文硬上限，超过即移除最早消息（保留受保护消息）。                        |
| `keep_first`                   | `1`      | 始终保留对话开始的 N 条消息，保护系统提示或环境变量。                                 |
| `keep_last`                    | `6`      | 始终保留对话末尾的 N 条消息，确保最近上下文连贯。                                     |

### 摘要生成配置

| 参数                  | 默认值  | 描述                                                                                                                                        |
| :-------------------- | :------ | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `summary_model`       | `None`  | 用于生成摘要的模型 ID。**强烈建议**配置快速、经济、上下文窗口大的模型（如 `gemini-2.5-flash`、`deepseek-v3`）。留空则尝试复用当前对话模型。 |
| `summary_model_max_context` | `0`     | 摘要模型的最大上下文 Token 数。如果为 0，则回退到 `model_thresholds` 或全局 `max_context_tokens`。                                          |
| `max_summary_tokens`  | `16384` | 生成摘要时允许的最大 Token 数。                                                                                                             |
| `summary_temperature` | `0.1`   | 控制摘要生成的随机性，较低的值结果更稳定。                                                                                                  |

### 高级配置

#### `model_thresholds` (模型特定阈值)

这是一个字典配置，可为特定模型 ID 覆盖全局 `compression_threshold_tokens` 与 `max_context_tokens`，适用于混合不同上下文窗口的模型。

**默认包含 GPT-4、Claude 3.5、Gemini 1.5/2.0、Qwen 2.5/3、DeepSeek V3 等推荐阈值。**

**配置示例：**

```json
{
  "gpt-4": {
    "compression_threshold_tokens": 8000,
    "max_context_tokens": 32000
  },
  "gemini-2.5-flash": {
    "compression_threshold_tokens": 734000,
    "max_context_tokens": 1048576
  }
}
```

| 参数                           | 默认值   | 描述                                                                                                                                    |
| :----------------------------- | :------- | :-------------------------------------------------------------------------------------------------------------------------------------- |
| `enable_tool_output_trimming`  | `false`  | 启用时，若 `function_calling: "native"` 激活，将裁剪冗长的工具输出以仅提取最终答案。                                                        |
| `debug_mode`                   | `true`   | 是否在 Open WebUI 的控制台日志中打印详细的调试信息（如 Token 计数、压缩进度、数据库操作等）。生产环境建议设为 `false`。 |
| `show_debug_log`               | `false`  | 是否在浏览器控制台 (F12) 打印调试日志。便于前端调试。                                                                   |
| `show_token_usage_status`      | `true`   | 是否在对话结束时显示 Token 使用情况的状态通知。                                                                         |

---

## ⭐ 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 故障排除 (Troubleshooting) ❓

- **初始系统提示丢失**：将 `keep_first` 设置为大于 0。
- **压缩效果不明显**：提高 `compression_threshold_tokens`，或降低 `keep_first` / `keep_last` 以增强压缩力度。
- **提交 Issue**: 如果遇到任何问题，请在 GitHub 上提交 Issue：[OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## 更新日志

完整历史请查看 GitHub 项目： [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
