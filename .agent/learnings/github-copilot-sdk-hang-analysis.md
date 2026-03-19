# GitHub Copilot SDK 卡顿/悬停问题深度源码分析报告

## 📌 问题现象

用户反馈在 agent 处理过程中（工具调用、思考、内容输出），`github_copilot_sdk.py` 管道偶尔会卡住（界面转圈不停）。

## 🔍 事件流架构（SDK 源码分析）

通过阅读 `copilot-sdk` 源码 (`jsonrpc.py`, `client.py`, `session.py`)，事件流路径如下：

```
Copilot CLI (subprocess)
  └─ stdout (JSON-RPC over stdio)
      └─ JsonRpcClient._read_loop() [daemon thread]
          └─ _handle_message()
              └─ notification_handler("session.event", params) [线程安全调度到 event loop]
                  └─ CopilotSession._dispatch_event(event)
                      └─ plugin handler(event) → queue.put_nowait(chunk)
                          └─ main loop: await queue.get() → yield chunk
```

## 🚨 已确认的三个卡顿根因

### 根因 1: Stall 检测豁免盲区

原始代码的防卡死检测仅在 `content_sent=False` 且 `thinking_started=False` 且 `running_tool_calls` 为空时才触发。一旦 agent 开始处理（输出内容/调用工具），所有豁免条件为真，防卡死机制永久失效。

### 根因 2: 工具调用状态泄漏

`running_tool_calls.add(tool_call_id)` 在 `tool.execution_start` 时添加，但如果 SDK 连接断开导致 `tool.execution_complete` 事件丢失，集合永远不为空，直接阻塞 Stall 检测。

### 根因 3: `session.abort()` 自身可能卡住（SDK 源码确认）

**SDK 源码关键证据** (`jsonrpc.py:107-148`):

```python
async def request(self, method, params=None, timeout=None):
    ...
    if timeout is not None:
        return await asyncio.wait_for(future, timeout=timeout)
    return await future  # ← 无 timeout，永久等待！
```

`session.abort()` 底层调用 `self._client.request("session.abort", ...)` **没有传 timeout**。
当 CLI 进程挂死但 `_read_loop` 尚未检测到断流（例如 TCP 半开连接），`abort()` RPC 自身会无限等待响应，造成**修复代码自身也卡住**。

## ✅ 修复记录 (2026-03-18)

### 修复 1: `assistant.turn_end` / `session.error` 兜底清理

`running_tool_calls.clear()` — 即时清除孤儿工具状态。

### 修复 2: 绝对不活跃保护 (Absolute Inactivity Guard)

当距最后一个事件超过 `min(TIMEOUT, 90) × 2 = 180s` 且无任何新事件时，**无条件**推送错误并结束流。不受 `content_sent` / `thinking_started` / `running_tool_calls` 任何豁免条件限制。

### 修复 3: `session.abort()` 超时保护

所有 `session.abort()` 调用使用 `asyncio.wait_for(..., timeout=5.0)` 包裹。即使 abort RPC 自身卡住也不会阻塞主循环。

## 📊 修复后超时时间线

| 场景 | 保护机制 | 触发时间 |
|------|----------|----------|
| Turn 开始后完全无事件 | Primary Stall Detection | 90 秒 |
| Agent 处理中突然断流 | Absolute Inactivity Guard | 180 秒 |
| abort() 调用本身卡住 | asyncio.wait_for timeout | 5 秒 |
| Turn 结束/Session 错误 | 兜底 running_tool_calls.clear() | 即时 |

---

*Created by Antigravity using Source-Code-Analyzer skill on 2026-03-18.*
