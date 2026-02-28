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

## 6. 渲染语义：Artifacts 与 Rich UI（权威笔记）

### 6.1 Artifacts（产物渲染）

* **定义**：由消息内容/代码驱动的交互式预览（HTML/SVG/代码产物）。
* **主要参考**：
  * `../docs/docs/features/chat-conversations/chat-features/code-execution/artifacts.md`
  * `../open-webui/src/lib/components/chat/Artifacts.svelte`
* **适用场景**：
  * 以内容本身为核心的快速可视化预览。
  * 对工具返回结构依赖较低。

### 6.2 Rich UI（工具/动作嵌入）

* **定义**：由 Tool/Action 返回（如 `HTMLResponse` 或 embed payload）的嵌入式 UI，以沙箱 iframe 形式渲染并随会话持久化。
* **主要参考**：
  * `../docs/docs/features/extensibility/plugin/development/rich-ui.mdx`
  * `../docs/docs/features/extensibility/plugin/tools/development.mdx`
  * `../docs/docs/features/extensibility/plugin/development/events.mdx`
  * `../open-webui/backend/open_webui/utils/actions.py`
* **适用场景**：
  * 应用化、状态化、可持久回看的交互块。
  * 需要确定性的工具返回渲染契约。

### 6.3 Rich UI 与 `execute` 事件区别

* **Rich UI**：沙箱 iframe + 会话持久化视觉区块。
* **`execute` 事件**：运行在主页面上下文（非沙箱），适合瞬时交互（弹窗、快捷动作、页面状态读取），不适合持久化产品级 UI。

### 6.4 安全与体验约束

* Rich UI iframe 默认处于沙箱。
* 在 same-origin 关闭（默认）时，嵌入内容应通过 `postMessage({ type: 'iframe:height', ... })` 上报高度。
* 开启 same-origin 可增强互操作性，但会增加安全暴露面。
* 沙箱内下载能力在部分环境受限（尤其 iOS）；应提供显式预览/下载链接作为兜底。

### 6.5 高价值开发策略

1. 采用双通道交付：可视化结果 + 可持久下载链接。
2. 持久化应用视图优先使用 Rich UI；受限时降级到 Artifacts/链接。
3. 文件持久化必须显式发布/存储，不依赖瞬时 UI 状态。
4. 保留可见模式提示与结构化状态日志，提升可诊断性。
