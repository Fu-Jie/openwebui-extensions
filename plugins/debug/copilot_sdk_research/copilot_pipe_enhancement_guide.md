# OpenWebUI GitHub Copilot Pipe Enhancement Guide

基于 Copilot SDK 源码级研究的深度技术总结，旨在指导 OpenWebUI Pipe 的功能增强开发。

## 1. 认证机制 (Authentication)

官方支持通过环境变量传递 Token。在 Pipe 中，只要确保 `GH_TOKEN` 或 `GITHUB_TOKEN` 存在于环境变量中，Copilot CLI 即可自动识别，无需在 `CopilotClient` 构造函数中重复注入。

### 核心实现

Pipe 应确保将 Token（来自 Valve 或 Env）正确设置到当前进程的环境变量中。

```python
import os
from copilot import CopilotClient

# 1. 设置环境变量 (如果从 Valve 获取)
if self.valves.GH_TOKEN:
    os.environ["GH_TOKEN"] = self.valves.GH_TOKEN

# 2. 初始化客户端
# CopilotClient 启动的 CLI 子进程会自动继承当前环境中的 GH_TOKEN
client = CopilotClient({
    # "cli_path": ...,
    # 注意：无需在此处重复传入 github_token，CLI 会自动读取环境变量
})

# 3. 启动前检查 (建议)
# status = await client.get_auth_status()
# if not status.isAuthenticated: ...
```

## 2. 权限与确认 (Permissions & Tools) - 核心控制点

这是用户最关心的部分：如何知道有哪些工具，以及如何控制它们的执行。

### 2.1 内置工具 (Built-in Tools)

Copilot CLI 内部管理了一组标准工具，**Python SDK 目前没有直接的 API (`client.list_tools()`) 来列出这些工具**。

但是，根据 SDK 的 `PermissionRequest` 类型定义 (`copilot/types.py`)，我们可以反推其能力类别：

* **`shell`**: 执行终端命令 (对应 `run_terminal_command` 等)
* **`filesystem`** (对应 `read/write`): 文件读写 (对应 `read_file`, `edit_file`, `delete_file` 等)
* **`url`**: 网络访问 (对应 `fetch_url` 等)
* **`mcp`**: 连接的 MCP 服务器工具

> **提示**: `available_tools` 参数可以用来“隐藏”工具，让 Agent 根本不知道它有一把锤子。而 `on_permission_request` 是用来拦截 Agent 挥舞锤子的动作。通常我们建议**能力全开 (不设置 available_tools 限制)**，而在**权限层 (on_permission_request) 做拦截**。

### 2.2 实现“全部允许”与“按需允许”

建议在 Valves 中增加权限控制字段，并在 `on_permission_request` 中实现逻辑。

```python
import re

class Valves(BaseModel):
    # ... 其他 Valve ...
    # 权限控制开关
    PERMISSIONS_ALLOW_ALL: bool = Field(default=False, description="DANGER: Auto-approve ALL actions (shell, write, etc).")
    PERMISSIONS_ALLOW_SHELL: bool = Field(default=False, description="Auto-approve shell commands.")
    PERMISSIONS_SHELL_ALLOW_PATTERN: str = Field(default="", description="Regex for approved shell commands (e.g., '^ls|^grep').")
    PERMISSIONS_ALLOW_WRITE: bool = Field(default=False, description="Auto-approve file write/edit/delete.")
    PERMISSIONS_ALLOW_MCP: bool = Field(default=True, description="Auto-approve MCP tool execution.")

# 权限处理 Hook 实现
async def on_user_permission_request(request, context):
    """
    统一权限审批网关
    request keys: kind, toolCallId, ... (shell requests have 'command')
    """
    kind = request.get("kind") # shell, write, mcp, read, url

    # 1. 超级模式：全部允许
    if self.valves.PERMISSIONS_ALLOW_ALL:
        return {"kind": "approved"}

    # 2. 默认安全：始终允许 "读" 和 "Web浏览" (根据需求调整)
    if kind in ["read", "url"]:
        return {"kind": "approved"}

    # 3. 细粒度控制
    if kind == "shell":
        # 3.1 完全允许 Shell
        if self.valves.PERMISSIONS_ALLOW_SHELL:
            return {"kind": "approved"}
        
        # 3.2 基于正则允许特定命令
        command = request.get("command", "")
        pattern = self.valves.PERMISSIONS_SHELL_ALLOW_PATTERN
        if pattern and command:
            try:
                if re.match(pattern, command):
                    return {"kind": "approved"}
            except re.error:
                print(f"[Config Error] Invalid Regex: {pattern}")

    if kind == "write" and self.valves.PERMISSIONS_ALLOW_WRITE:
        return {"kind": "approved"}
        
    if kind == "mcp" and self.valves.PERMISSIONS_ALLOW_MCP:
        return {"kind": "approved"}

    # 4. 默认拒绝
    print(f"[Permission Denied] Blocked request for: {kind} {request.get('command', '')}")
    return {
        "kind": "denied-by-rules", 
        "rules": [{"kind": "check-openwebui-valves"}]
    }

# 注册 Hook
session = await client.create_session({
    # ... 
    "on_permission_request": on_user_permission_request
})
```

## 3. Agent 与 MCP 集成 (Agents & MCP)

SDK 中的 Agent 和 MCP 并非独立文件，而是会话配置 (`SessionConfig`) 的一部分。Pipe 可以通过 Valves 动态构建这些配置。

### 关键映射关系

| SDK 概念 | OpenWebUI 对应 | 实现位置 | 关键参数 |
| :--- | :--- | :--- | :--- |
| **Custom Agent** | 自定义模型 / Persona | `create_session(custom_agents=[...])` | `name`, `prompt`, `tools` (仅名称) |
| **Agent Tools** | Valve 开关 / 预置工具 | `create_session(tools=[func1, func2])` | 必须先在 `tools` 注册函数，Agent 才能引用 |
| **MCP Server** | Valve 配置 (JSON) | `create_session(mcp_servers={...})` | `command`, `args`, `env` (本地) |

### 代码范式：动态构建 Agent

```python
async def create_agent_session(client, user_prompt, model_name):
    # 1. 定义工具 (必须是函数引用)
    # 假设已从 OpenWebUI Tools 转换或内置
    available_tools = [tool_web_search, tool_run_script] 
    
    # 2. 构建 Agent Manifest (针对当前请求的虚拟 Agent)
    agent_manifest = {
        "name": "openwebui_agent",
        "description": "Dynamic agent from OpenWebUI",
        "prompt": "You are a helpful assistant...", # 这里注入 System Prompt
        "tools": ["web_search", "run_script"],    # 引用上方工具的 name
        "mcp_servers": {
            # 可以在这里为特定 Agent 绑定 MCP
        }
    }

    # 3. 创建会话
    session = await client.create_session({
        "model": "gpt-4", # 底层模型
        "custom_agents": [agent_manifest],
        "tools": available_tools,          # 注册实际代码
        "available_tools": ["web_search"], # 白名单控制当前可用工具
        # ... 权限配置
    })
```

## 4. MCP 服务器配置 (Native MCP Support)

Pipe 可以直接支持标准 MCP 协议（Stdio）。不需要额外的 MCP 客户端代理，SDK 原生支持。

### Valve 配置结构建议

建议在 Pipe 的 Valves 中增加一个 `MCP_CONFIG` 字段（JSON 字符串），解析后直接传给 SDK。

```python
# Valve 输入示例 (JSON)
# {
#   "brave_search": {
#     "type": "local",
#     "command": "npx",
#     "args": ["-y", "@modelcontextprotocol/server-brave-search"],
#     "env": {"BRAVE_API_KEY": "..."}
#   }
# }

# 代码实现
mcp_config = json.loads(self.valves.MCP_CONFIG)
session = await client.create_session({
    # ...
    "mcp_servers": mcp_config,
    # 注意：必须配合权限自动审批，否则 MCP 工具无法调用
    "on_permission_request": auto_approve_policy 
})
```

## 5. 会话管理：持久化 vs 重放 (Persistence)

OpenWebUI 是无状态的，但 Copilot SDK 是有状态的（保留上下文窗口优化）。

### 最佳实践：以 `chat_id` 为锚点

利用 OpenWebUI 提供的 `chat_id` 来决定是 `resume` 还是 `start`。

1. **Map**: 维护 `Dict[chat_id, session_id]` (内存或数据库)。
2. **Flow**:
    * 请求进来 -> 检查 `chat_id` 是否有对应的 `session_id`。
    * **有**: 尝试 `client.resume_session(session_id)`。
        * *注意*：Resume 时必须重新传入 `tools`, `hooks`, `on_permission_request`，因为这些 Python 对象不会被序列化保存。
    * **无/失败**: 调用 `client.create_session()`，并将新 `session_id` 存入 Map。
3. **Fallback**: 如果 Resume 失败（例如后端重启 SDK 进程丢失），回退到 Create 新会话，并可选地将 OpenWebUI 传来的 `messages` 历史以 System Message 或历史插入的方式“重放”进去（虽然 SDK 不直接支持 insert history，但可以通过连续的 `send` 模拟，但这很慢）。
    * *简易方案*：Resume 失败就作为新对话开始，只带入 System Prompt。

## 6. 高级 Hook：提示词增强

利用 `on_user_prompt_submitted` 钩子，可以在不修改用户可见内容的情况下，向 Copilot 注入隐式上下文（例如当前文件内容、Pipe 的元指令）。

```python
async def inject_context_hook(input_data, ctx):
    user_prompt = input_data["prompt"]
    
    # 比如：检测到用户在问代码，自动附加上下文
    additional_context = "Current Language: Python. Framework: OpenWebUI."
    
    return {
        "modifiedPrompt": user_prompt, # 可以在这里改写提示词
        "additionalContext": additional_context # 注入隐藏上下文
    }

session = await client.create_session({
    # ...
    "hooks": {
        "on_user_prompt_submitted": inject_context_hook
    }
})
```

---

**总结开发清单：**

1. [ ] **Env Auth**: 读取环境变量 -> `CopilotClient`。
2. [ ] **Permission Valve**: 实现 `PERMISSIONS_ALLOW_ALL/SHELL` 等 Valves。
3. [ ] **Auto-Approve Hook**: 实现 `on_permission_request` 逻辑。
4. [ ] **MCP Valve**: 添加 JSON Valve -> `session.mcp_servers`。
5. [ ] **Session Map**: 实现 `chat_id` <-> `session_id` 的简单的内存映射。
6. [ ] **Resume Logic**: 优先 `resume_session`，并记得并在 resume 时重传 Hook 和 Tools。
