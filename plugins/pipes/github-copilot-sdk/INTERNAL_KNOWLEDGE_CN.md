# GitHub Copilot SDK Pipe - 内部架构与通用知识 (Internal Knowledge)

本文档记录了 GitHub Copilot SDK 插件在 OpenWebUI 环境下的核心运行机制、文件布局及深度集成逻辑。

## 1. 核心环境上下文 (Environment)

### 1.1 文件系统布局

| 路径 | 说明 | 权限 |
| :--- | :--- | :--- |
| `/app/backend` | OpenWebUI 后端 Python 源码 | 只读 |
| `/app/build` | OpenWebUI 前端静态资源 (Artifacts 渲染器位置) | 只读 |
| `/root/.copilot/` | SDK 核心配置与状态存储 | **完全控制** |
| `/app/backend/data/copilot_workspace/` | 插件指定的持久化工作区 | **读写自如** |

### 1.2 身份映射机制

* **Session ID 绑定**: 插件强制将 OpenWebUI 的 `Chat ID` 映射为 Copilot SDK 的 `Session ID`。
* **结果**: 每个对话窗口都有独立的物理存储目录：`/root/.copilot/session-state/{chat_id}/`。

## 2. TODO List 存储机制 (TODO Intelligence)

### 2.1 数据源

TODO 数据**并不**仅存储在独立数据库，而是通过 `update_todo` 工具写入会话事件流：

* **文件**: `/root/.copilot/session-state/{chat_id}/events.jsonl`
* **识别**: 查找类型为 `tool.execution_complete` 且 `toolName` 为 `update_todo` 的最新 JSON 行。

### 2.2 数据格式 (NDJSON)

```json
{
  "type": "tool.execution_complete",
  "data": {
    "toolName": "update_todo",
    "result": { "detailedContent": "TODO List内容...", "toolTelemetry": { "metrics": { "total_items": 39 } } }
  }
}
```

## 3. 工具体系 (Toolchain)

插件整合了三套工具系统：

1. **Copilot Native**: SDK 内置的 `bash`, `edit`, `task` 等。
2. **OpenWebUI Ecosystem**: 通过 `get_tools` 挂载的本地 Python 脚本和内置 `Web Search`。
3. **MCP (Model Context Protocol)**: 通过 `GDMap`, `Pandoc` 等服务器扩展的外部能力。

## 4. 安全与权限 (Security)

### 4.1 管理员模式 (God Mode)

当 `__user__['role'] == 'admin'` 时：

* 启用 `ADMIN_EXTENSIONS`。
* 允许通过环境变量获取 `DATABASE_URL`。
* 允许使用 `bash` 诊断 `/root/.copilot/` 内部状态。

### 4.2 普通用户模式

* 启用 `USER_RESTRICTIONS`。
* 严禁探测环境变量和数据库。
* 限制 `bash` 只能在工作区内活动。

## 5. 常见维护操作

* **重置会话**: 删除 `/root/.copilot/session-state/{chat_id}` 目录。
* **清理缓存**: 在 Valves 中关闭 `ENABLE_TOOL_CACHE`。
* **查看日志**: 检查 `/root/.copilot/logs/` 下的最新日志。
