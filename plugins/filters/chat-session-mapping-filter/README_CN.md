# 🔗 聊天会话映射过滤器

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 0.1.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

自动追踪并持久化用户 ID 与聊天 ID 的映射关系，实现无缝的会话管理。

## 核心功能

🔄 **自动追踪** - 无需手动干预，在每条消息上自动捕获 user_id 和 chat_id  
💾 **持久化存储** - 将映射关系保存到 JSON 文件，便于会话恢复和数据分析  
🛡️ **原子性操作** - 使用临时文件写入防止数据损坏  
⚙️ **灵活配置** - 通过 Valves 参数启用/禁用追踪功能  
🔍 **智能上下文提取** - 从多个数据源（body、metadata、__metadata__）安全提取 ID

## 使用方法

1. **安装过滤器** - 将其添加到 OpenWebUI 插件
2. **全局启用** - 无需配置，追踪功能默认启用
3. **查看映射** - 检查 `copilot_workspace/api_key_chat_id_mapping.json` 中的存储映射

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_TRACKING` | `true` | 聊天会话映射追踪的主开关 |

## 工作原理

该过滤器在 **inlet** 阶段（消息处理前）拦截消息并执行以下步骤：

1. **提取 ID**: 安全地从 `__user__` 获取 user_id，从 `body`/`metadata` 获取 chat_id
2. **验证**: 确认两个 ID 都非空后再继续
3. **持久化**: 使用原子文件操作将映射写入或更新 JSON 文件
4. **错误处理**: 任何步骤失败时都会优雅地记录警告，不阻断聊天流程

### 存储位置

- **容器环境**（存在 `/app/backend/data`）:  
  `/app/backend/data/copilot_workspace/api_key_chat_id_mapping.json`

- **本地开发**（无 `/app/backend/data`）:  
  `./copilot_workspace/api_key_chat_id_mapping.json`

### 文件格式

存储为 JSON 对象，键是用户 ID，值是聊天 ID：

```json
{
  "user-1": "chat-abc-123",
  "user-2": "chat-def-456",
  "user-3": "chat-ghi-789"
}
```

## 支持我们

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。

## 技术细节

- **不修改响应**: outlet 钩子直接返回响应不做修改
- **原子写入**: 使用 `.tmp` 临时文件防止不完整的写入
- **上下文敏感的 ID 提取**: 处理 `__user__` 为 dict/list/None 的情况，以及来自多个源的 metadata
- **日志记录**: 所有操作都会被记录，便于调试；可通过启用依赖插件的 `SHOW_DEBUG_LOG` 查看详细日志
