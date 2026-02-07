# GitHub Copilot SDK & CLI 研究报告

- **model**: gpt-5.2-codex
- **questions**: 68
- **timestamp**: 20260130_114642
- **language**: zh-CN

---

## Q: Provide a python code example for configuring `CopilotClient` to connect to a local MCP server (e.g. Brave Search) via `CopilotClient` config.

SDK 源码显示 MCP 服务器通过 `create_session`/`resume_session` 的 `mcp_servers` 配置传入并映射为 `mcpServers`，不是 CopilotClient 构造参数（源：本地源码 copilot/types.py / copilot/client.py）。下面是本地 stdio MCP（以 Brave Search 为例，命令/密钥请替换）的 Python 示例。  
```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-5",
        "mcp_servers": {
            "brave_search": {
                "type": "local",  # 或 "stdio"
                "command": "/path/to/brave-search-mcp",  # 替换为你的 MCP server 启动命令
                "args": [],
                "env": {"BRAVE_API_KEY": "YOUR_KEY"},
                "tools": ["*"],
                "timeout": 30000,  # 毫秒
            }
        },
    })

    await session.send_and_wait({"prompt": "用 Brave Search 查询 OpenAI 最新公告"})
    await client.stop()

asyncio.run(main())
```

要点/坑：
- `tools`: `["*"]` 表示全量，`[]` 表示不启用
- `timeout`: 毫秒
- `command/args/env`: 按你的 MCP server 实际启动方式替换

建议/落地：
- pipe 内复用同一 session，结束时统一 `client.stop()`

## Q: Explain how to programmatically handle `tool.confirmation_required` events in a non-interactive stream using `session.on()`.

SDK 源码未定义 `tool.confirmation_required` 事件，权限确认由 JSON‑RPC `permission.request` 触发并交给 `on_permission_request` 回调处理，`session.on()` 只能订阅 `tool.user_requested`/`tool.execution_start` 等事件做记录关联（来源：本地源码 copilot/client.py、copilot/session.py、copilot/types.py）。  
在非交互流里必须提供 `on_permission_request` 自动审批/拒绝，否则默认拒绝且回调异常也会被拒绝。

要点/坑  
- 配置键: `on_permission_request`（SessionConfig）  
- 权限类型: `shell` / `write` / `mcp` / `read` / `url`  
- 回调异常或缺失 -> `denied-no-approval-rule-and-could-not-request-from-user`

```python
import asyncio
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType

async def main():
    client = CopilotClient()
    await client.start()

    def on_event(ev):
        if ev.type == SessionEventType.TOOL_USER_REQUESTED:
            print(f"tool requested: {ev.data.tool_name} {ev.data.tool_call_id}")
        elif ev.type == SessionEventType.TOOL_EXECUTION_START:
            print(f"tool start: {ev.data.tool_name}")

    async def on_permission_request(req, ctx):
        kind = req.get("kind")
        if kind in ("read", "mcp"):
            return {"kind": "approved"}
        return {"kind": "denied-by-rules", "rules": [{"kind": "deny-non-read"}]}

    session = await client.create_session({
        "model": "gpt-5",
        "on_permission_request": on_permission_request,
    })
    session.on(on_event)

    await session.send_and_wait({"prompt": "请调用需要权限的工具"})
    await client.stop()

asyncio.run(main())
```

建议/落地  
- pipe 启动时注册审批策略 + `session.on` 记录 `tool_call_id` 做审计

## Q: Show how to implement a 'Device Flow' login helper using SDK primitives (if available) or raw HTTP showing how to persist credentials.

SDK 本身没有 device‑flow 登录 API；可用鉴权原语只有 CopilotClient 的 `github_token`/`use_logged_in_user` 与 `get_auth_status`（源：本地源码 copilot/client.py、copilot/types.py）。  
下面用 GitHub OAuth Device Flow 原始 HTTP 获取 token、持久化本地并注入 `github_token`（端点说明：https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow）。

```python
import asyncio
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from copilot import CopilotClient

CLIENT_ID = "YOUR_OAUTH_APP_CLIENT_ID"
SCOPE = "read:user"  # 按你的 OAuth App 需求调整
TOKEN_PATH = Path.home() / ".config" / "myapp" / "copilot_token.json"

def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def load_token():
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text()).get("access_token")
    return None

def save_token(token):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token))
    os.chmod(TOKEN_PATH, 0o600)

def device_flow():
    code = http_post(
        "https://github.com/login/device/code",
        {"client_id": CLIENT_ID, "scope": SCOPE},
    )
    print(f"Open {code['verification_uri']} and enter {code['user_code']}")
    interval = int(code.get("interval", 5))

    while True:
        token = http_post(
            "https://github.com/login/oauth/access_token",
            {
                "client_id": CLIENT_ID,
                "device_code": code["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        if "access_token" in token:
            return token
        if token.get("error") == "slow_down":
            interval += 5
        elif token.get("error") not in ("authorization_pending",):
            raise RuntimeError(token)
        time.sleep(interval)

async def main():
    access_token = load_token()
    if not access_token:
        token = device_flow()
        save_token(token)
        access_token = token["access_token"]

    client = CopilotClient({"github_token": access_token})
    await client.start()
    # ... create_session / send ...
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

要点/坑  
- `cli_url` 与 `github_token` 互斥  
- SDK 不保存凭据 需自行持久化  
- 轮询需处理 `authorization_pending` / `slow_down`

建议/落地  
- pipe 启动时读取 token 文件 不存在则走 device flow  
- 用 `github_token` 注入 保持非交互运行

## Q: Compare the pros and cons of 'Session Replay' (fast-forwarding history) vs 'Session Resume' (stateful ID) for a stateless web backend like OpenWebUI.

对无状态后端(OpenWebUI)而言，SDK 只支持通过 `resume_session(session_id)` 的状态续接；所谓“Session Replay”需要你自行重放历史 prompt（来源：本地 SDK 源码 copilot/client.py、copilot/session.py）。  
对比要点（短语）：  
- Replay：无状态/易扩展；缺点是耗时耗 tokens、易截断/丢工具状态、可能重复副作用  
- Resume：省 tokens、保留工具/compaction/`workspace_path` 状态；缺点是需持久化 session_id、依赖会话存活/跨实例一致性。  
建议/落地：优先持久化 chat_id→session_id 并 resume_session，失效时回退为重放最近 N 轮并重建工具上下文。

## Q: Detail the exact protocol for 'Virtual Workspace': how to implement a file system provider that feeds content to Copilot without physical files.

SDK 源码里没有“Virtual Workspace”协议或文件系统 provider 接口；会话只识别真实路径（`SessionConfig.working_directory`、`MessageOptions.attachments`）。要在无物理文件情况下供给内容，只能用自定义工具或 MCP 服务器把“读写文件”变成 tool 调用（来源：本地 SDK 源码 copilot/types.py / copilot/client.py）。

可用原语（源码）
- `SessionConfig.tools` / `available_tools`：自定义工具与白名单
- `MessageOptions.attachments`：仅支持真实路径文件/目录

方案 A：自定义工具实现 VFS（推荐）
```python
import asyncio
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool

VFS = {"README.md": "# Virtual README\n内容来自内存\n"}

class VfsReadParams(BaseModel):
    path: str = Field(description="virtual path")

@define_tool(name="vfs_read", description="Read a virtual file")
def vfs_read(params: VfsReadParams) -> str:
    return VFS.get(params.path, "")

@define_tool(name="vfs_list", description="List virtual files")
def vfs_list() -> list[str]:
    return sorted(VFS.keys())

async def main():
    client = CopilotClient()
    await client.start()
    session = await client.create_session({
        "model": "gpt-5",
        "tools": [vfs_read, vfs_list],
        "available_tools": ["vfs_read", "vfs_list"],
        "system_message": {"content": "Use vfs_* tools for all file access."},
    })
    await session.send_and_wait({"prompt": "打开 README.md"})
    await client.stop()

asyncio.run(main())
```

方案 B：MCP 服务器（本地 stdio，VFS 由你实现）
```python
session = await client.create_session({
    "model": "gpt-5",
    "mcp_servers": {
        "vfs": {
            "type": "local",
            "command": "python",
            "args": ["-m", "my_vfs_mcp_server"],
            "tools": ["*"],
        }
    },
})
```

注意/坑  
- `available_tools` 只保留你的 VFS 工具以强制使用  
- 内置文件工具只读真实文件；要兼容只能落地临时文件  
- 大文件需分块返回，避免上下文爆炸  

建议/落地  
- pipe 内维护 VFS 存储（DB/Redis/内存）  
- 启动 session 时注入 `system_message` + `available_tools` 强制 VFS 入口

## Q: Create an 'Agent Manifest' example: how to define an Agent capable of specific high-privileged tools via SDK.

SDK 没有独立“Agent Manifest”文件格式，等价于 `create_session` 的 `custom_agents`（CustomAgentConfig），并用 `tools`/`available_tools` 约束高权限工具，权限由 `on_permission_request` 处理（来源：本地 SDK 源码 copilot/types.py、copilot/client.py）。  
示例如下（manifest 为 Python dict，可序列化为 JSON 配置）。

```python
import asyncio
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool

class AdminShellParams(BaseModel):
    cmd: str = Field(description="approved shell command")

@define_tool(name="admin_shell", description="Run an approved shell command")
def admin_shell(params: AdminShellParams) -> str:
    # TODO: 执行受控命令（白名单/沙箱）
    return f"approved: {params.cmd}"

class AdminWriteParams(BaseModel):
    path: str = Field(description="target path")
    content: str = Field(description="content")

@define_tool(name="admin_write", description="Write to privileged store")
def admin_write(params: AdminWriteParams) -> str:
    # TODO: 受控写入
    return "ok"

async def on_permission_request(req, _ctx):
    if req.get("kind") in ("shell", "write"):
        return {"kind": "approved"}
    return {"kind": "denied-by-rules", "rules": [{"kind": "deny"}]}

async def main():
    client = CopilotClient()
    await client.start()

    agent_manifest = {
        "name": "ops-admin",
        "display_name": "Ops Admin",
        "description": "Privileged ops agent",
        "prompt": "Use only admin_* tools for privileged ops.",
        "tools": ["admin_shell", "admin_write"],
        "infer": True,
    }

    session = await client.create_session({
        "model": "gpt-5",
        "tools": [admin_shell, admin_write],
        "custom_agents": [agent_manifest],
        "available_tools": ["admin_shell", "admin_write"],
        "on_permission_request": on_permission_request,
    })

    await session.send_and_wait({"prompt": "使用 ops-admin 执行受控操作"})
    await client.stop()

asyncio.run(main())
```

要点/坑  
- session.tools 未注册 -> agent.tools 不可用  
- custom_agents.tools 仅写名称  
- 非交互缺少 on_permission_request -> 默认拒绝  
- SDK 无显式 agent 选择参数 -> 需在 prompt 指定  

建议/落地  
- pipe 启动时加载 manifest 注入 custom_agents + available_tools + on_permission_request

## Q: List all 'hidden' `SessionConfig` parameters relevant to Agent behavior and personality.

基于本地 SDK 源码 `copilot/types.py` 的 SessionConfig，影响 Agent 行为/人格的相关参数如下（来源：本地 SDK 源码）。  
- `system_message`: `append`/`replace`；`replace` 会移除 SDK guardrails（风险）  
- `custom_agents`: `prompt`/`description`/`display_name`/`tools`/`mcp_servers`/`infer`；`tools` 仅名称且必须在 `tools` 注册  
- `tools` / `available_tools` / `excluded_tools`: 能力与行为边界；`available_tools` 优先于 `excluded_tools`  
- `hooks`: `on_user_prompt_submitted`/`on_pre_tool_use`/`on_post_tool_use`/`on_session_start`/`on_session_end`/`on_error_occurred`，可改写 prompt/工具参数/结果  
- `on_permission_request`: 非交互审批策略；缺失或异常 => 拒绝  
- `on_user_input_request`: 启用/处理 `ask_user`  
- `mcp_servers`: 注入外部工具集  
- `skill_directories` / `disabled_skills`: 技能启用/禁用  
- `model` / `provider`: 模型与 BYOK 影响输出风格与能力  
- `working_directory`: 上下文范围  
- `infinite_sessions`: compaction 阈值影响记忆保留  
- `config_dir`: CLI 配置/状态目录，行为取决于 CLI 侧配置  

建议/落地：在 pipe 启动时固定 `system_message` + `available_tools/excluded_tools` + `hooks`，并持久化 session_id 以便 `resume_session`。

## Q: Give a concise overview of MCP Server Integration: JSON-RPC config and SDK hooks.

SDK 中 MCP 通过 create_session/resume_session 的 mcp_servers 传入（映射到 JSON‑RPC 的 mcpServers），支持 local/stdio 与 http/sse，两类配置字段分别为 type/command/args/env/cwd/timeout/tools 或 type/url/headers/timeout/tools（来源：本地 SDK 源码）。  
SDK hooks 使用 hooks(on_pre_tool_use/on_post_tool_use/on_user_prompt_submitted/on_session_start/on_session_end/on_error_occurred) 进行拦截与附加上下文，权限需 on_permission_request 对 kind='mcp' 明确批准，且 session.on 可审计 tool.execution_* 事件中的 mcp_server_name/mcp_tool_name。  
示例见下，建议/落地：pipe 中启用 on_permission_request、限制 tools 白名单并记录 MCP 事件。

```python
import asyncio
from copilot import CopilotClient

async def on_permission_request(req, _):
    return {"kind": "approved"} if req.get("kind") == "mcp" else {
        "kind": "denied-by-rules",
        "rules": [{"kind": "deny"}],
    }

async def on_pre_tool_use(input, _):
    if input.get("toolName", "").startswith("mcp."):
        return {"additionalContext": "MCP tool call observed"}

async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-5",
        "mcp_servers": {
            "brave": {
                "type": "local",
                "command": "/path/to/brave-mcp",
                "args": [],
                "env": {"BRAVE_API_KEY": "YOUR_KEY"},
                "tools": ["*"],
                "timeout": 30000,
            }
        },
        "hooks": {"on_pre_tool_use": on_pre_tool_use},
        "on_permission_request": on_permission_request,
    })

    await session.send_and_wait({"prompt": "用 Brave Search 查询 Copilot SDK 新闻"})
    await client.stop()

asyncio.run(main())
```

## Q: Provide best practices and common pitfalls for MCP Server Integration: JSON-RPC config and SDK hooks.

基于本地 SDK 源码，MCP 配置通过 `create_session`/`resume_session` 的 `mcp_servers` 进入 JSON‑RPC `mcpServers`，并通过 `on_permission_request` 与 `hooks` 控制工具审批与行为（来源：本地 SDK 源码）  
- 最佳实践：local/stdio 用 `type/command/args/env/cwd/timeout/tools`；remote http/sse 用 `type/url/headers/timeout/tools`；`tools` 尽量白名单、必要时 `["*"]`；`timeout` 毫秒；`hooks.on_pre_tool_use` 做改参/拒绝，`session.on` 记录 `tool.execution_*` 与 `mcp_server_name`/`mcp_tool_name`  
- 常见坑：把 MCP 配置放在 CopilotClient；缺少 `on_permission_request`（kind="mcp"）导致默认拒绝；`tools: []` 等于禁用全部；设置 `available_tools` 却未包含 MCP 工具名导致被过滤  

建议/落地：pipe 中固定审批策略 + 统一 MCP 配置模板 + 审计日志

## Q: Show a minimal example snippet for MCP Server Integration: JSON-RPC config and SDK hooks.

基于本地 SDK 源码，MCP 通过 `mcp_servers` 传入并用 `hooks` 处理工具调用（来源：本地 SDK 源码）。最小示例：  
```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()

    session = await client.create_session({
        "model": "gpt-5",
        "mcp_servers": {
            "brave": {
                "type": "local",
                "command": "/path/to/brave-mcp",
                "args": [],
                "env": {"BRAVE_API_KEY": "YOUR_KEY"},
                "tools": ["*"],
            }
        },
        "hooks": {
            "on_pre_tool_use": lambda input, _: {"additionalContext": "MCP tool call"},
        },
        "on_permission_request": lambda req, _: {"kind": "approved"},
    })

    await session.send_and_wait({"prompt": "用 Brave Search 搜索 Copilot SDK"})
    await client.stop()

asyncio.run(main())
```

建议/落地：固定 `on_permission_request`（kind="mcp"）并限制 `tools` 白名单。

## Q: List recommended configuration defaults for MCP Server Integration: JSON-RPC config and SDK hooks.

推荐默认值（MCP JSON‑RPC 配置，来源：本地 SDK 源码）：local/stdio 服务器用 `type="local"/"stdio"`（远程用 `http`/`sse`）、`tools` 白名单（无则 `"*"`）、`timeout=30000` 毫秒、`env` 仅放密钥、`cwd` 指向受控目录。  
Hooks 默认：`on_pre_tool_use` 追加上下文并可设 `permissionDecision`（ask/allow）、必要时改参，`on_post_tool_use` 记录结果，`on_error_occurred` 设置 retry/skip。  
建议/落地：非交互场景配置 `on_permission_request` 仅放行 `kind="mcp"`，否则拒绝；工具名不确定时先不设 `available_tools`，避免误过滤。

## Q: How does MCP Server Integration: JSON-RPC config and SDK hooks relate to building a custom Agent?

SDK 源码中，自定义 Agent 通过 `SessionConfig.custom_agents` 定义，`CustomAgentConfig` 支持 `mcp_servers`，因此“Agent 绑定 MCP”就是在 agent config 里声明 `mcp_servers`，底层在 `create_session` 时转成 JSON‑RPC 的 `mcpServers`（来源：本地 SDK 源码 copilot/types.py、copilot/client.py）。  
Hooks 是会话级拦截器（`on_pre_tool_use`/`on_post_tool_use` 等），对 MCP 工具同样生效；权限确认需 `on_permission_request` 审批 `kind="mcp"`。  
建议/落地：pipe 中为目标 Agent 绑定 MCP + 审批钩子，示例：  
```python
session = await client.create_session({
    "model": "gpt-5",
    "custom_agents": [{
        "name": "search",
        "prompt": "Use MCP for search.",
        "mcp_servers": {
            "brave": {
                "type": "local",
                "command": "/path/to/brave-mcp",
                "args": [],
                "env": {"BRAVE_API_KEY": "YOUR_KEY"},
                "tools": ["*"],
            }
        },
    }],
    "hooks": {"on_pre_tool_use": lambda i, _: {"additionalContext": "mcp"}},
    "on_permission_request": lambda r, _: {"kind": "approved"},
})
```

## Q: Give a concise overview of Agent Manifests: Defining capabilities and permissions programmatically.

SDK 没有独立的 Agent Manifest 文件，等价做法是用 `SessionConfig.custom_agents` 描述 agent，并用 `tools`/`available_tools`/`excluded_tools` 限定能力。  
权限通过 `on_permission_request` 与 `hooks`（如 `on_pre_tool_use`）在会话级控制，且 `custom_agents.tools` 只能写工具名并需在 `SessionConfig.tools` 注册。  
建议/落地：pipe 启动时加载 manifest→注入 `custom_agents` + `available_tools` + `on_permission_request` 固化权限边界。

## Q: Provide best practices and common pitfalls for Agent Manifests: Defining capabilities and permissions programmatically.

SDK 没有独立 Manifest 文件，等价于 `SessionConfig.custom_agents` + `tools/available_tools/excluded_tools` + `on_permission_request` + `hooks` 来定义能力与权限（来源：本地 SDK 源码）。  
最佳实践：`custom_agents.tools` 只写已在 `SessionConfig.tools` 注册的名称，配合 `available_tools` 白名单与 `on_permission_request` 精准放行，必要时用 `hooks.on_pre_tool_use` 做参数校验/审计，`system_message` 选 append 以保留 guardrails。  
常见坑：工具未注册或名称不一致、缺少 `on_permission_request` 导致默认拒绝、误用 `system_message` replace 去掉安全限制、期待 agent 自动被选中或跨实例不持久 `session_id`；建议/落地：pipe 启动时加载 manifest→注入 `custom_agents/available_tools/on_permission_request` 并持久化 `session_id`。

## Q: Show a minimal example snippet for Agent Manifests: Defining capabilities and permissions programmatically.

最小示例（本地 SDK 源码：`custom_agents` + `tools` + `available_tools` + `on_permission_request`）：  
```python
import asyncio
from pydantic import BaseModel, Field
from copilot import CopilotClient, define_tool

class PingParams(BaseModel):
    text: str = Field(description="text to echo")

@define_tool(name="priv_ping", description="Privileged echo")
def priv_ping(params: PingParams) -> str:
    return f"ok: {params.text}"

async def main():
    client = CopilotClient()
    await client.start()

    agent_manifest = {
        "name": "priv-agent",
        "prompt": "Only use priv_ping for actions.",
        "tools": ["priv_ping"],
        "infer": True,
    }

    session = await client.create_session({
        "model": "gpt-5",
        "tools": [priv_ping],
        "custom_agents": [agent_manifest],
        "available_tools": ["priv_ping"],
        "on_permission_request": lambda req, _: {"kind": "approved"},
    })

    await session.send_and_wait({"prompt": "调用 priv_ping"})
    await client.stop()

asyncio.run(main())
```

建议/落地：保持工具名一致并白名单化，非交互务必提供 `on_permission_request`。

## Q: List recommended configuration defaults for Agent Manifests: Defining capabilities and permissions programmatically.

基于本地 SDK 源码（copilot/types.py / copilot/client.py），推荐默认值如下：  
- custom_agents：name 必填、prompt 必填、tools 仅名称、infer=True，display_name/description 可选  
- available_tools=白名单、excluded_tools=空、system_message=append  
- on_permission_request：除明确允许的 kind 其余拒绝；hooks.on_pre_tool_use 做审计/参数校验（其余 hooks 按需）  
建议/落地：pipe 启动时加载 manifest→注册 tools + available_tools + on_permission_request，并持久化 session_id。

## Q: How does Agent Manifests: Defining capabilities and permissions programmatically relate to building a custom Agent?

“Agent Manifest”在 SDK 里就是 `SessionConfig.custom_agents` 的配置对象，用它定义自定义 Agent 的 `name/prompt/tools/mcp_servers/infer`，并在同一 session 里用 `tools` 注册实际工具、用 `available_tools/excluded_tools` 限定能力（来源：本地 SDK 源码）。  
权限不在 manifest 内，而是由会话级 `on_permission_request` 和 hooks（如 `on_pre_tool_use`）统一控制，且对所有 Agent 生效。  
建议/落地：pipe 启动时把 manifest 转成 `custom_agents` 并同步注册工具 + 白名单，再配置 `on_permission_request` 作为权限策略。

## Q: Give a concise overview of Headless Auth: Device Code Flow and credential persistence.

SDK 仅提供 `CopilotClient` 的 `github_token/use_logged_in_user` 与 `get_auth_status()`，没有内置 device‑flow API（源码：copilot/client.py、copilot/types.py）。  
Headless Device Flow 需走 GitHub OAuth Device Flow HTTP 端点获取 token（https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow），将 token 持久化（权限 600）并通过 `CopilotClient({"github_token": token})` 注入，且与 `cli_url` 互斥。  
建议/落地：启动时读 token 文件，不存在则执行 device flow 并保存，再启动客户端。

```python
token = load_token() or device_flow()  # 调用 device code + access_token 端点
save_token(token)  # chmod 600
client = CopilotClient({"github_token": token["access_token"]})
await client.start()
```

## Q: Provide best practices and common pitfalls for Headless Auth: Device Code Flow and credential persistence.

SDK 不内置 device flow，只能用 GitHub OAuth Device Flow HTTP 换取 token 并通过 CopilotClient({github_token}) 注入，且与 cli_url 互斥（源码：copilot/client.py、copilot/types.py）。  
最佳实践/坑：- token 文件 chmod 600 或 OS keychain；- 记录到期与刷新策略，启动时用 get_auth_status 验证；- 轮询需处理 authorization_pending/slow_down；- 未持久化、use_logged_in_user 与 github_token 同时使用或与 cli_url 混用会失败（端点说明：https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow）。  
建议/落地：pipe 启动时读 token 文件，不存在则走 device flow 并保存，失败时回退重新授权。

## Q: Show a minimal example snippet for Headless Auth: Device Code Flow and credential persistence.

最小示例：用 GitHub Device Flow（端点说明见 https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow）拿 token，持久化后注入 CopilotClient({github_token}).  
```python
import asyncio
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from copilot import CopilotClient

CLIENT_ID = "YOUR_OAUTH_APP_CLIENT_ID"
TOKEN_PATH = Path.home() / ".config" / "myapp" / "copilot_token.json"

def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def device_flow():
    code = post("https://github.com/login/device/code", {"client_id": CLIENT_ID, "scope": "read:user"})
    print(f"Open {code['verification_uri']} and enter {code['user_code']}")
    interval = int(code.get("interval", 5))
    while True:
        tok = post(
            "https://github.com/login/oauth/access_token",
            {
                "client_id": CLIENT_ID,
                "device_code": code["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        if "access_token" in tok:
            return tok
        if tok.get("error") == "slow_down":
            interval += 5
        elif tok.get("error") != "authorization_pending":
            raise RuntimeError(tok)
        time.sleep(interval)

def load_token():
    return json.loads(TOKEN_PATH.read_text()).get("access_token") if TOKEN_PATH.exists() else None

def save_token(tok):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(tok))
    os.chmod(TOKEN_PATH, 0o600)

async def main():
    access_token = load_token()
    if not access_token:
        tok = device_flow()
        save_token(tok)
        access_token = tok["access_token"]

    client = CopilotClient({"github_token": access_token})
    await client.start()
    # ... create_session / send ...
    await client.stop()

asyncio.run(main())
```

建议/落地  
- 启动先读 token 文件；缺失再 device flow  
- token 文件权限 600  
- 失效则重新授权

## Q: List recommended configuration defaults for Headless Auth: Device Code Flow and credential persistence.

基于本地 SDK 源码（`github_token` 与 `cli_url` 互斥）与 GitHub Device Flow 文档（https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow），推荐默认值：  
- Token 持久化：`~/.config/<app>/copilot_token.json` 或系统密钥链，文件权限 600  
- Client 选项：仅 `github_token`，`use_logged_in_user` 留空/False，禁用 `cli_url`  
- 轮询：使用 device code 返回的 `interval`（缺省 5s），处理 `authorization_pending`/`slow_down`  
- 启动校验：`get_auth_status()` 失败即重新授权  

建议/落地：启动先读 token 文件 → 无则 device flow → 保存 → `client.start()`

## Q: How does Headless Auth: Device Code Flow and credential persistence relate to building a custom Agent?

Headless Auth 只负责拿到并持久化 `github_token`，让 `CopilotClient` 能在无交互环境启动会话并加载 `custom_agents`；因此它是自定义 Agent 能稳定运行的前置条件，而不是 Agent 定义本身（来源：本地 SDK 源码）。  
建议/落地：在无状态后端启动时读取 token 文件（不存在就走 device flow）→ `CopilotClient({"github_token": token})` → `create_session(custom_agents=...)`。

## Q: Give a concise overview of Session Replay vs Resume: Handling stateless frontend history.

基于本地 SDK 源码（copilot/client.py、copilot/session.py），Resume 是 `resume_session(session_id)` 保留会话状态，Replay 只能由应用重放历史 prompt。优缺点：Resume 省 tokens/保工具与 compaction 状态但依赖持久化 session_id；Replay 无状态易扩展但成本高且易丢副作用控制。建议/落地：无状态前端请保存 session_id 并优先 Resume，失效时回放最近 N 轮。

## Q: Provide best practices and common pitfalls for Session Replay vs Resume: Handling stateless frontend history.

最佳实践：在无状态前端每次请求携带 session_id 并优先 `resume_session`，同时恢复 tools/hooks/on_permission_request/system_message 以保持行为一致（来源：本地 SDK 源码）。  
常见坑：Replay 会重复执行工具且耗 tokens；Resume 未重新注册工具或权限处理器会出现 tool not supported/默认拒绝；会话失效未回退。  
建议/落地：持久化 chat_id→session_id，resume 失败时仅回放最近 N 轮并禁用/幂等化有副作用的工具。

## Q: Show a minimal example snippet for Session Replay vs Resume: Handling stateless frontend history.

来源：本地 SDK 源码（copilot/client.py, copilot/session.py），最小示例如下（优先 Resume，失败则 Replay）。  
```python
import asyncio
from copilot import CopilotClient

async def handle_request(session_id: str | None, history: list[str], latest: str):
    client = CopilotClient()
    await client.start()

    try:
        # Resume: 复用会话状态
        if not session_id:
            raise RuntimeError("no session_id")
        session = await client.resume_session(session_id)
    except Exception:
        # Replay: 逐条重放历史
        session = await client.create_session({"model": "gpt-5"})
        session_id = session.session_id
        for prompt in history:
            await session.send_and_wait({"prompt": prompt})

    response = await session.send_and_wait({"prompt": latest})
    await client.stop()
    return response.data.content, session_id

# asyncio.run(handle_request(session_id, history, latest_prompt))
```
建议/落地：持久化 session_id，resume 失败时仅回放最近 N 轮。

## Q: List recommended configuration defaults for Session Replay vs Resume: Handling stateless frontend history.

基于本地 SDK 源码，推荐默认配置如下（Resume / Replay）：  
- Resume：持久化 session_id；`resume_session({...})` 传回 tools、hooks、on_permission_request、working_directory、streaming、provider、mcp_servers、custom_agents、skill_directories、disabled_skills；`disable_resume` 保持默认 False  
- Replay：`create_session({...})` 传回 model、system_message、tools、available_tools/excluded_tools、hooks、on_permission_request、working_directory、provider、mcp_servers、custom_agents、infinite_sessions(默认启用)；仅回放最近 N 轮；默认拒绝 write/shell 或用只读白名单

## Q: How does Session Replay vs Resume: Handling stateless frontend history relate to building a custom Agent?

Resume 会保留 session_id 关联的 custom_agents/工具状态，Replay 需要每次 create_session 时重新注入 custom_agents + tools，否则 persona/能力会丢失（来源：本地 SDK 源码）。对于无状态前端，Resume 更可靠且省 token，但要持久化 session_id 并在 resume 时重新注册 tools/hooks；Replay 则需回放历史并保证相同 custom_agents 配置。建议/落地：pipe 优先 resume_session，失败再 replay 最近 N 轮并重建 custom_agents/tools/权限策略。

## Q: Give a concise overview of Advanced Session Hooks: Intercepting and modifying user prompts.

拦截/修改用户提示要用 `SessionHooks.on_user_prompt_submitted`（不是 `session.on` 事件订阅），`input.prompt` 可改为 `output.modifiedPrompt` 并附加 `additionalContext`/`suppressOutput`，且需在 `create_session`/`resume_session` 传入 `hooks` 才会触发 `hooks.invoke`（来源：本地 SDK 源码 copilot/types.py、copilot/session.py、copilot/client.py）。  
```python
from copilot import CopilotClient

async def on_user_prompt_submitted(input, _ctx):
    return {"modifiedPrompt": input["prompt"].strip(), "additionalContext": "normalize whitespace"}

session = await client.create_session({
    "model": "gpt-5",
    "hooks": {"on_user_prompt_submitted": on_user_prompt_submitted},
})
```
建议/落地：在 pipe 入口统一做 prompt 清洗/拼接上下文，并记录修改前后用于审计。

## Q: Provide best practices and common pitfalls for Advanced Session Hooks: Intercepting and modifying user prompts.

最佳实践：在 create_session/resume_session 传入 hooks.on_user_prompt_submitted，返回 {modifiedPrompt, additionalContext, suppressOutput}，修改保持幂等、最小化、可审计（来源：本地 SDK 源码 copilot/types.py、copilot/client.py、copilot/session.py）。  
常见坑：忘记传 hooks 或 resume 时未重新传、handler 抛异常会被吞并返回 None、返回非 dict 或过度改写提示导致无效/偏航。  
建议/落地：在 pipe 入口统一注册该 hook 并记录修改前后，保持 system_message 为 append。

## Q: Show a minimal example snippet for Advanced Session Hooks: Intercepting and modifying user prompts.

最小示例（来源：本地 SDK 源码）：  
```python
import asyncio
from copilot import CopilotClient

async def on_user_prompt_submitted(hook_input, _ctx):
    return {
        "modifiedPrompt": hook_input["prompt"].strip(),
        "additionalContext": "normalized",
    }

async def main():
    client = CopilotClient()
    await client.start()
    session = await client.create_session({
        "model": "gpt-5",
        "hooks": {"on_user_prompt_submitted": on_user_prompt_submitted},
    })
    await session.send_and_wait({"prompt": "  hello  "})
    await client.stop()

asyncio.run(main())
```
建议/落地：在 pipe 入口统一注册该 hook，并记录修改前后以便审计。

## Q: List recommended configuration defaults for Advanced Session Hooks: Intercepting and modifying user prompts.

- 推荐默认值（来源：本地 SDK 源码 copilot/types.py）：`hooks={"on_user_prompt_submitted": handler}`，handler 默认返回 `{"modifiedPrompt": input["prompt"], "additionalContext": "", "suppressOutput": False}` 或 `None`（不改写）。  
- `create_session`/`resume_session` 都要传同一 hooks；`system_message` 保持 append 以保留 guardrails。  
- 建议/落地：pipe 入口统一注册该 hook 并记录原/改提示用于审计。

## Q: How does Advanced Session Hooks: Intercepting and modifying user prompts relate to building a custom Agent?

Hooks 是会话级拦截器，对所有自定义 Agent 都生效；因此它是定义 Agent 行为边界和输入规范化的“外层控制”，而不是 Agent Manifest 本身（来源：本地 SDK 源码 copilot/types.py、copilot/session.py）。  
在自定义 Agent 场景下，`on_user_prompt_submitted` 可统一清洗/增强用户指令，再由 custom_agents 的 prompt 决定具体风格。  
建议/落地：pipe 启动时同时注入 custom_agents + hooks，确保 resume 时同样注册 hooks。

## Q: Give a concise overview of Workspace Virtualization: Handling CWD for remote/virtual files.

SDK 只有 `SessionConfig.working_directory` 来约束 CWD，`attachments` 也要求真实路径，没有“虚拟工作区/FS provider”协议（来源：本地 SDK 源码 copilot/types.py、copilot/client.py）。要处理远程/虚拟文件，需用自定义工具或 MCP 服务器实现 VFS 读写，或把内容落地到 working_directory 下的临时文件再交给模型。建议/落地：pipe 固定 working_directory 映射到会话工作区，统一走 vfs_* 工具/MCP，且在 on_permission_request 限制 write/shell。

## Q: Provide best practices and common pitfalls for Workspace Virtualization: Handling CWD for remote/virtual files.

SDK 没有虚拟工作区/FS provider，仅支持 `SessionConfig.working_directory` 与真实路径 `attachments`（来源：本地 SDK 源码），因此远程/虚拟文件需落地或用自定义工具/MCP 提供内容。  
最佳实践：固定 working_directory 到可控目录/会话 workspace，VFS 工具分块返回，配合 `available_tools`/`on_permission_request` 限权；常见坑：直接传虚拟路径/URL、working_directory 不存在、resume 未重注册工具/权限、一次性返回过大内容导致上下文截断。  
建议/落地：pipe 入口做 remote→临时文件或 vfs_* 映射，并持久化路径索引。

## Q: Show a minimal example snippet for Workspace Virtualization: Handling CWD for remote/virtual files.

SDK 仅提供 `SessionConfig.working_directory` 与真实路径附件，没有虚拟 FS/provider（来源：本地 SDK 源码 copilot/types.py）。最小做法是把远程内容落地到 CWD 下再作为附件传入：  
```python
import asyncio
import pathlib
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()

    workdir = "/tmp/owui"
    pathlib.Path(workdir).mkdir(parents=True, exist_ok=True)
    remote_content = "..."
    path = f"{workdir}/remote.txt"
    pathlib.Path(path).write_text(remote_content)

    session = await client.create_session({"model": "gpt-5", "working_directory": workdir})
    await session.send_and_wait({
        "prompt": "Summarize remote.txt",
        "attachments": [{"type": "file", "path": path}],
    })
    await client.stop()

asyncio.run(main())
```
建议/落地：pipe 入口固定 working_directory，落地临时文件后立即处理，并用 `on_permission_request` 限制 write/shell。

## Q: List recommended configuration defaults for Workspace Virtualization: Handling CWD for remote/virtual files.

推荐默认值（来源：本地 SDK 源码 copilot/types.py）：  
- `working_directory`: 指向可控的会话目录（如 session.workspace_path 或 /tmp/<app>/<session_id>）  
- `available_tools`: 只允许 vfs_* 或只读工具，避免任意 shell/write  
- `on_permission_request`: 默认拒绝 write/shell，仅放行 read/mcp  
- `attachments`: 仅真实路径文件；远程内容先落地  

建议/落地：pipe 入口统一映射 remote→临时文件或 VFS 工具，并持久化映射表。

## Q: How does Workspace Virtualization: Handling CWD for remote/virtual files relate to building a custom Agent?

SDK 没有虚拟文件系统协议，custom agent 只能依赖 `working_directory` 和真实路径附件，因此处理远程/虚拟文件需通过自定义工具/MCP 并在 agent prompt/available_tools 中强制使用（来源：本地 SDK 源码 copilot/types.py、copilot/client.py）。  
这使“工作区虚拟化”成为 agent 能力与权限设计的一部分，需要 `available_tools`/`on_permission_request`/hooks 来限定访问范围。  
建议/落地：pipe 中固定 working_directory 到会话目录，注入 vfs_* 工具白名单并在 prompt 明确使用 VFS。

## Q: Give a concise overview of Error Recovery: Handling session disconnects and re-auth.

本地 SDK 源码中没有显式“重连”API，断线通常表现为请求异常或 `SessionEventType.SESSION_ERROR`，需要 `stop()/force_stop()` 后重新 `start()` 并 `resume_session`（失败则 replay）（来源：本地 SDK 源码）。  
认证可用 `get_auth_status()` 检测，未认证时重新创建 `CopilotClient({"github_token": token})`；若 `cli_url` 连接外部服务器则认证由外部处理（来源：本地 SDK 源码）。

```python
import asyncio
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType

async def safe_send(session_id, prompt, token):
    client = CopilotClient({"github_token": token})
    await client.start()
    try:
        session = await (client.resume_session(session_id) if session_id else client.create_session({"model": "gpt-5"}))
        session.on(lambda ev: ev.type == SessionEventType.SESSION_ERROR and print(ev.data.message))
        resp = await session.send_and_wait({"prompt": prompt})
        return resp, session.session_id
    except Exception:
        await client.stop()
        client = CopilotClient({"github_token": token})
        await client.start()
        session = await client.create_session({"model": "gpt-5"})
        resp = await session.send_and_wait({"prompt": prompt})
        return resp, session.session_id
    finally:
        await client.stop()
```

建议/落地：持久化 session_id 与 token，优先 resume，失败再回放最近 N 轮。

## Q: Provide best practices and common pitfalls for Error Recovery: Handling session disconnects and re-auth.

最佳实践（基于本地 SDK 源码）：监听 `SESSION_ERROR`/捕获请求异常后 `stop()/force_stop()`→重新 `start()`→`resume_session`（失败再 replay），启动时用 `get_auth_status()` 校验并在失效时重建 `CopilotClient({"github_token": ...})`，同时在 resume 时重新注册 tools/hooks/权限处理器。  
常见坑：把 `cli_url` 与 `github_token` 混用、忘记重注册工具导致 `tool not supported`、缺少 `on_permission_request` 导致默认拒绝、以及不回退到 replay 造成会话中断。  
建议/落地：无状态后端持久化 `session_id+token`、实现幂等的重试/回放策略并记录错误上下文用于告警。

## Q: Show a minimal example snippet for Error Recovery: Handling session disconnects and re-auth.

最小示例（本地 SDK 源码：copilot/client.py、copilot/session.py）：  
```python
import asyncio
from copilot import CopilotClient

async def send_with_recovery(session_id, prompt, token):
    client = CopilotClient({"github_token": token})
    await client.start()
    try:
        session = await (client.resume_session(session_id) if session_id else client.create_session({"model": "gpt-5"}))
        resp = await session.send_and_wait({"prompt": prompt})
        return resp.data.content, session.session_id
    except Exception:
        await client.stop()
        client = CopilotClient({"github_token": token})
        await client.start()
        session = await client.create_session({"model": "gpt-5"})
        resp = await session.send_and_wait({"prompt": prompt})
        return resp.data.content, session.session_id
    finally:
        await client.stop()
```
建议/落地：持久化 token+session_id，resume 失败再重建并回放必要历史。

## Q: List recommended configuration defaults for Error Recovery: Handling session disconnects and re-auth.

推荐默认值（字段来源：本地 SDK 源码）：CopilotClientOptions—auto_start=True、log_level='info'、use_stdio=True（非 cli_url）、github_token=持久化 token；SessionConfig/ResumeSessionConfig—hooks.on_error_occurred=handler、on_permission_request=非交互审批、working_directory 固定、mcp_servers/custom_agents/streaming 与首次一致、可固定 config_dir 并持久化 session_id。  
常见坑：cli_url 与 github_token 互斥、resume 时未重传 tools/hooks 导致 tool not supported 或默认拒绝。  
建议/落地：pipe 保存 token+session_id，断线后先 resume_session，失败再回放最近 N 轮。

## Q: How does Error Recovery: Handling session disconnects and re-auth relate to building a custom Agent?

错误恢复与自定义 Agent 强相关：Agent 定义与工具/权限处理器都是 session 级配置，断线或重认证后必须重建客户端并重新注入 `custom_agents`、`tools`、`hooks`、`on_permission_request`，否则能力/人格会丢失（来源：本地 SDK 源码）。  
建议/落地：持久化 session_id+token，重连优先 `resume_session` 并重新注册上述配置，失败再回放最近 N 轮。

## Q: Give a concise overview of Confirmation Events: programmatic handling of 'confirmation_required'.

SDK 源码里没有独立的 `confirmation_required` 事件；权限确认是 JSON‑RPC `permission.request`，通过 `SessionConfig.on_permission_request` 回调处理（缺失或异常会默认拒绝）。  
`session.on()` 只能用于审计/关联工具事件（如 `tool.user_requested`、`tool.execution_start`），不能替代确认逻辑。

## Q: Provide best practices and common pitfalls for Confirmation Events: programmatic handling of 'confirmation_required'.

SDK 源码未定义 `confirmation_required` 事件，确认流程必须用 `SessionConfig.on_permission_request` 处理，缺失或异常会默认拒绝（来源：本地 SDK 源码）。  
最佳实践/坑：  
- ✅ 对 `kind` 建立白名单策略（如仅允许 `read/mcp`），记录决策并用 `session.on` 仅做审计关联 `tool.user_requested`  
- ✅ `resume_session` 时重新注册 `on_permission_request`/hooks  
- ❌ 误以为 `session.on()` 可完成确认、返回非规范 dict 或抛异常导致全部拒绝

## Q: Show a minimal example snippet for Confirmation Events: programmatic handling of 'confirmation_required'.

SDK 里没有 `confirmation_required` 事件，需用 `SessionConfig.on_permission_request` 处理权限确认。  
最小示例：  
```python
from copilot import CopilotClient

client = CopilotClient()
await client.start()

session = await client.create_session({
    "model": "gpt-5",
    "on_permission_request": lambda req, _: {"kind": "approved"},
})
```
建议/落地：在 pipe 中统一注册 on_permission_request，并在 resume_session 时重复注册。

## Q: List recommended configuration defaults for Confirmation Events: programmatic handling of 'confirmation_required'.

推荐默认值（SDK 无 confirmation_required 事件，改用 on_permission_request，来源：本地 SDK 源码）：- 对 kind 建白名单（常见只放行 read/mcp）- 未命中默认返回 denied-by-rules 并给 rules - resume_session 时重注册 on_permission_request/hooks。  
建议/落地：pipe 启动即注入 on_permission_request 并记录审批日志。

## Q: How does Confirmation Events: programmatic handling of 'confirmation_required' relate to building a custom Agent?

SDK 没有 `confirmation_required` 事件，权限确认由 `create_session`/`resume_session` 的 `on_permission_request` 处理，且对同一 session 的所有 custom agent 生效（来源：本地 SDK 源码）。  
建议/落地：在 pipe 启动时注入 `on_permission_request` 白名单策略并在 resume 时重注册，以约束高权限工具。

## Q: Give a concise overview of Skills: Conflict resolution and precedence defaults.

在本地 SDK 源码中，Skills 只通过 SessionConfig 的 `skill_directories` 与 `disabled_skills` 暴露，未定义冲突解析/优先级规则，因此行为取决于 CLI 运行时实现（来源：本地 SDK 源码 copilot/types.py）。  
为可控性，建议确保技能名唯一、仅配置单一目录或由你自行按顺序拼接目录，并用 `disabled_skills` 明确屏蔽同名/不应启用的技能。  
建议/落地：在无状态后端每次 `create_session`/`resume_session` 时显式传入同一份 `skill_directories` 与 `disabled_skills`，避免因默认加载顺序差异导致行为漂移。

## Q: Provide best practices and common pitfalls for Skills: Conflict resolution and precedence defaults.

SDK 源码仅暴露 SessionConfig/ResumeSessionConfig 的 `skill_directories` 和 `disabled_skills`，未定义冲突解析或优先级，行为由 CLI 侧决定（来源：本地 SDK 源码 copilot/types.py）。  
最佳实践：技能名全局唯一、只配置单一目录或显式排序，并用 `disabled_skills` 禁用冲突项；常见坑是依赖默认加载顺序或 resume 未重传这两个字段导致行为漂移。  
建议/落地：在 pipe 启动与 resume 时统一注入同一份 `skill_directories`/`disabled_skills` 并记录变更。

## Q: Show a minimal example snippet for Skills: Conflict resolution and precedence defaults.

SDK 里技能只通过 `skill_directories` 与 `disabled_skills` 配置，冲突/优先级未在源码定义，需自行避免同名。  
最小示例：  
```python
session = await client.create_session({
    "model": "gpt-5",
    "skill_directories": ["/opt/skills"],
    "disabled_skills": ["legacy_skill"],
})
```  
建议：技能名唯一并在 `resume_session` 时重传这两项。

## Q: List recommended configuration defaults for Skills: Conflict resolution and precedence defaults.

推荐默认值（基于 SDK 仅暴露 `skill_directories`/`disabled_skills`）：  
- `skill_directories`: 明确设置为单一目录（或你自己控制顺序的列表），不要依赖 CLI 默认搜索顺序  
- `disabled_skills`: 默认空列表；如存在同名/旧技能则显式禁用  
- Resume/Replay：始终复用同一份配置以避免“隐式优先级”漂移

## Q: How does Skills: Conflict resolution and precedence defaults relate to building a custom Agent?

Skills 是会话级配置（`skill_directories`/`disabled_skills`），会影响所有自定义 Agent 的可用能力与提示行为；SDK 不定义冲突优先级，因此需要你在构建自定义 Agent 时确保技能命名唯一并显式禁用冲突项（来源：本地 SDK 源码）。  
建议/落地：为 custom agent 固定同一份 skills 配置，并在 resume 时重复传入，避免行为漂移。

## Q: Give a concise overview of Debugging: Tracing JSON-RPC traffic in the SDK.

本地 SDK 源码里 JsonRpcClient 没有内置 JSON‑RPC trace，只能通过 `CopilotClient({"log_level":"debug"})` 打开 CLI 侧日志（非原始包）（来源：本地 SDK 源码）。  
要抓实际 JSON‑RPC 流量，可 monkey‑patch `JsonRpcClient._send_message`/`_read_message` 或包装 stdio 进行 tee，最小示例如下。  
建议/落地：在 pipe 中开启 patch 并对日志做脱敏与采样。  
```python
from copilot.jsonrpc import JsonRpcClient

orig_send = JsonRpcClient._send_message
async def _send(self, message):
    print(">>", message)
    return await orig_send(self, message)
JsonRpcClient._send_message = _send

orig_read = JsonRpcClient._read_message
def _read(self):
    msg = orig_read(self)
    if msg:
        print("<<", msg)
    return msg
JsonRpcClient._read_message = _read
```

## Q: Provide best practices and common pitfalls for Debugging: Tracing JSON-RPC traffic in the SDK.

源码里 JsonRpcClient 没有内置 trace，只能用 `CopilotClient({"log_level":"debug"})` 查看 CLI 侧日志或 monkey‑patch `JsonRpcClient._send_message/_read_message` 做 tee（来源：本地 SDK 源码）。  
最佳实践：仅在调试启用、对 github_token/API key/内容脱敏、采样/限流、只读不改消息并注意线程安全；常见坑：记录完整 prompt/工具参数导致泄露，或同步打印阻塞 IO 造成超时/断连。

## Q: Show a minimal example snippet for Debugging: Tracing JSON-RPC traffic in the SDK.

最小示例（monkey‑patch `JsonRpcClient` 打印收发）：  
```python
from copilot.jsonrpc import JsonRpcClient

orig_send = JsonRpcClient._send_message
async def _send(self, msg):
    print(">>", msg)
    return await orig_send(self, msg)
JsonRpcClient._send_message = _send

orig_read = JsonRpcClient._read_message
def _read(self):
    msg = orig_read(self)
    if msg:
        print("<<", msg)
    return msg
JsonRpcClient._read_message = _read
```
建议：仅在调试启用并脱敏日志。

## Q: List recommended configuration defaults for Debugging: Tracing JSON-RPC traffic in the SDK.

推荐默认值（基于 SDK 源码）：- 生产环境关闭 trace；- 调试时 `CopilotClient({"log_level":"debug"})`；- 如需 JSON‑RPC 报文，采用临时 monkey‑patch 并启用脱敏/采样；- 不修改消息内容，避免线程阻塞。  
建议/落地：pipe 中通过环境变量开关调试与采样率。

## Q: How does Debugging: Tracing JSON-RPC traffic in the SDK relate to building a custom Agent?

JSON‑RPC trace 能看到 custom_agents 在 `session.create/session.resume` 的实际 payload，以及后续 `tool.call`/`permission.request`/`hooks.invoke` 是否按预期触发，从而验证自定义 Agent 的能力与权限边界（来源：本地 SDK 源码）。  
建议/落地：仅在开发环境开启并脱敏日志；用它核对 customAgents/tools/权限决策与 MCP 配置。

## Q: Give a concise overview of Billing & Policies: How seat management affects SDK features.

- 访问与政策：SDK 依赖 Copilot CLI，需有效 Copilot 订阅且组织/企业未禁用 CLI，否则无法使用（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）  
- 计费与认证：每次 prompt 计入 Copilot premium requests 配额，PAT 需 Copilot Requests 权限（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）

建议/落地：启动先 `get_auth_status()`，失败时提示分配席位/启用 CLI 或更新 token

## Q: Provide best practices and common pitfalls for Billing & Policies: How seat management affects SDK features.

最佳实践：确认用户/组织席位允许 Copilot CLI/SDK 使用，启动前用 `get_auth_status()` 预检，使用 PAT 时确保具备 Copilot Requests 权限（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）。  
常见坑：未分配席位或组织/企业策略禁用 CLI 导致 SDK 失效、PAT 权限不足或 premium requests 用尽引发认证/配额错误（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）。  
建议/落地：在 pipe 启动时做席位与鉴权检测并给出明确提示/自助链接，记录每次请求计费与配额告警阈值以便限流。

## Q: Show a minimal example snippet for Billing & Policies: How seat management affects SDK features.

基于 SDK README，最小示例是在启动时用 `get_auth_status()` 检查是否已分配席位/可用认证（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md）。  
```python
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()

    auth = await client.get_auth_status()
    if not auth.isAuthenticated:
        raise RuntimeError("Copilot 未认证/未分配席位，请先登录或分配权限")

    # ...正常创建 session...
    await client.stop()

asyncio.run(main())
```
建议/落地：pipe 启动先做该检查，失败时提示分配席位或更新 PAT 权限。

## Q: List recommended configuration defaults for Billing & Policies: How seat management affects SDK features.

推荐默认值：CopilotClient 用 `use_logged_in_user=True`、`auto_start=True`、`log_level="info"`；如用 PAT 则用 `github_token` 注入并确保具备 Copilot Requests 权限，且启动前 `get_auth_status()` 失败即按席位/策略限制处理（来源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md ，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）。  
建议/落地：pipe 启动先做 auth 预检并给出续订/分配席位提示，避免会话中途才触发权限或配额错误。

## Q: How does Billing & Policies: How seat management affects SDK features relate to building a custom Agent?

席位与组织策略决定 Copilot CLI/SDK 是否可用，因此自定义 Agent 只是同一会话上的配置，前提仍是有有效订阅与允许的策略，否则 Agent 无法运行（源：https://raw.githubusercontent.com/github/copilot-sdk/main/README.md ，https://raw.githubusercontent.com/github/copilot-cli/main/README.md）。  
建议/落地：在创建自定义 Agent 前先 `get_auth_status()` 预检并对配额/政策限制做降级提示。

## Q: How to configure MCP servers in ~/.copilot/config.json for SDK usage?

我在 CLI 文档里未看到 `~/.copilot/config.json` 的 MCP 配置结构；CLI 仅提供 `/mcp add|edit|delete|show` 命令管理配置（来源：Copilot CLI 文档）。  
因此建议用 CLI 写入配置，并在 SDK 中用 `config_dir` 指向该配置目录；或直接在 SDK 的 `create_session(mcp_servers=...)` 传入。  
如果你确认存在 `~/.copilot/config.json` 的具体 schema，请提供示例或路径，我可按你的文件格式给出精确配置。

## Q: What CLI environment variables force 'Agent' mode vs 'Generic' mode?

CLI 文档未提到任何“通过环境变量强制 Agent 模式/Generic 模式”的开关（源：Copilot CLI 文档）。  
已知与模式相关的是命令/参数，例如 `--agent` 选择自定义 agent，或交互内 `/agent` 切换；但不是环境变量。  
如果你指的是内部实验开关，请提供具体变量名或版本线索，我可继续追索。

## Q: Explain the 'confirmation' flow in CLI and how it maps to SDK events.

- CLI：工具权限弹窗确认，可用 `/allow-all` 或 `/yolo` 自动批准。（源: https://raw.githubusercontent.com/github/copilot-cli/main/README.md）  
- SDK：对应 JSON‑RPC `permission.request`→`on_permission_request` 返回 `approved/denied-*`，`session.on()` 只用于审计 tool.execution_*，无独立 confirmation 事件。（源: 本地 SDK 源码 copilot/client.py、copilot/session.py、copilot/types.py）

示例：
```python
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType

client = CopilotClient()
await client.start()
session = await client.create_session({
    "model": "gpt-5",
    "on_permission_request": lambda req, _: {"kind": "approved"},
})
session.on(lambda ev: ev.type == SessionEventType.TOOL_EXECUTION_START and print(ev.data.tool_name))
```

建议/落地：非交互模式实现 `on_permission_request` 并记录 `tool.execution_*` 事件。

## Q: Does the CLI support 'dry-run' permission checks for tools?

CLI 文档未提到“dry-run”权限检查，只有正常确认与 `/allow-all`、`/yolo` 自动批准（源：https://raw.githubusercontent.com/github/copilot-cli/main/README.md）。SDK 侧仅有 `permission.request`→`on_permission_request` 与 `hooks.on_pre_tool_use` 的拦截/拒绝（本地 SDK 源码），不提供不执行的试运行；建议/落地：pipe 中用 `on_permission_request` 记录/拒绝高风险工具并在 hooks 做审计。

## Q: What are the undocumented requirements for 'workspace' context updates?

CLI 文档与本地 SDK 源码都未提到“workspace context updates”的未公开要求；SDK 只暴露 `working_directory` 与 `session.workspace_path`，以及 `attachments` 真实路径（来源：本地 SDK 源码）。  
如果你指的是 CLI 的“工作区/会话文件”更新规则，请提供具体页面或日志片段，我可以进一步定位。

## Q: How does the CLI handle 'device code' re-authentication automatically?

CLI 文档未说明“自动 device code 重新认证”的具体机制；只提到未登录时使用 `/login`，PAT 可通过 `GH_TOKEN/GITHUB_TOKEN` 提供（源：Copilot CLI 文档）。因此无法确认是否有自动 re-auth 或缓存刷新策略。  
若需无交互场景，请使用 SDK 的 `github_token` 注入并自行实现 device flow 轮询与持久化。

