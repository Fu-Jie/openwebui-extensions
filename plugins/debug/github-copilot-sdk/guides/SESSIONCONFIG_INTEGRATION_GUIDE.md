# SessionConfig 完整功能集成指南

## 📋 概述

本文档详细说明如何将 GitHub Copilot SDK 的 `SessionConfig` 所有功能集成到 OpenWebUI Pipe 中。

---

## 🎯 功能清单与集成状态

| 功能 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `session_id` | ✅ 已实现 | 高 | 使用 OpenWebUI chat_id |
| `model` | ✅ 已实现 | 高 | 从 body 动态获取 |
| `tools` | ✅ 已实现 | 高 | v0.2.0 新增示例工具 |
| `streaming` | ✅ 已实现 | 高 | 支持流式输出 |
| `infinite_sessions` | ✅ 已实现 | 高 | 自动上下文压缩 |
| `system_message` | ⚠️ 部分支持 | 中 | 可通过 Valves 添加 |
| `available_tools` | ⚠️ 部分支持 | 中 | 已有 AVAILABLE_TOOLS |
| `excluded_tools` | 🔲 未实现 | 低 | 可添加到 Valves |
| `on_permission_request` | 🔲 未实现 | 中 | 需要 UI 交互支持 |
| `provider` (BYOK) | 🔲 未实现 | 低 | 高级功能 |
| `mcp_servers` | 🔲 未实现 | 低 | MCP 协议支持 |
| `custom_agents` | 🔲 未实现 | 低 | 自定义代理 |
| `config_dir` | 🔲 未实现 | 低 | 可通过 WORKSPACE_DIR |
| `skill_directories` | 🔲 未实现 | 低 | 技能系统 |
| `disabled_skills` | 🔲 未实现 | 低 | 技能过滤 |

---

## 📖 详细集成方案

### 1. ✅ session_id（已实现）

**功能：** 持久化会话 ID

**当前实现：**

```python
session_config = SessionConfig(
    session_id=chat_id if chat_id else None,  # 使用 OpenWebUI 的 chat_id
    ...
)
```

**工作原理：**

- OpenWebUI 的 `chat_id` 直接映射为 Copilot 的 `session_id`
- 会话状态持久化到磁盘
- 支持跨重启恢复对话

---

### 2. ✅ model（已实现）

**功能：** 选择 Copilot 模型

**当前实现：**

```python
# 从用户选择的模型中提取
request_model = body.get("model", "")
if request_model.startswith(f"{self.id}-"):
    real_model_id = request_model[len(f"{self.id}-"):]
```

**Valves 配置：**

```python
MODEL_ID: str = Field(
    default="claude-sonnet-4.5",
    description="默认模型（动态获取失败时使用）"
)
```

---

### 3. ✅ tools（已实现 - v0.2.0）

**功能：** 自定义工具/函数调用

**当前实现：**

```python
custom_tools = self._initialize_custom_tools()
session_config = SessionConfig(
    tools=custom_tools,
    ...
)
```

**Valves 配置：**

```python
ENABLE_TOOLS: bool = Field(default=False)
AVAILABLE_TOOLS: str = Field(default="all")
```

**内置示例工具：**

- `get_current_time` - 获取当前时间
- `calculate` - 数学计算
- `generate_random_number` - 随机数生成

**扩展方法：** 参考 [TOOLS_USAGE.md](TOOLS_USAGE.md)

---

### 4. ⚠️ system_message（部分支持）

**功能：** 自定义系统提示词

**集成方案：**

#### 方案 A：通过 Valves 添加（推荐）

```python
class Valves(BaseModel):
    SYSTEM_MESSAGE: str = Field(
        default="",
        description="Custom system message (append mode)"
    )
    SYSTEM_MESSAGE_MODE: str = Field(
        default="append",
        description="System message mode: 'append' or 'replace'"
    )
```

**实现：**

```python
async def pipe(self, body, ...):
    system_message_config = None
    
    if self.valves.SYSTEM_MESSAGE:
        if self.valves.SYSTEM_MESSAGE_MODE == "replace":
            system_message_config = {
                "mode": "replace",
                "content": self.valves.SYSTEM_MESSAGE
            }
        else:
            system_message_config = {
                "mode": "append",
                "content": self.valves.SYSTEM_MESSAGE
            }
    
    session_config = SessionConfig(
        system_message=system_message_config,
        ...
    )
```

#### 方案 B：从 OpenWebUI 系统提示词读取

```python
# 从 body 中获取系统提示词
system_prompt = body.get("system", "")
if system_prompt:
    system_message_config = {
        "mode": "append",
        "content": system_prompt
    }
```

**注意事项：**

- `append` 模式：在默认系统提示词后追加
- `replace` 模式：完全替换（移除 SDK 安全保护）

---

### 5. ⚠️ available_tools / excluded_tools

**功能：** 工具白名单/黑名单

**当前部分支持：**

```python
AVAILABLE_TOOLS: str = Field(
    default="all",
    description="'all' or comma-separated list"
)
```

**增强实现：**

```python
class Valves(BaseModel):
    AVAILABLE_TOOLS: str = Field(
        default="all",
        description="Available tools (comma-separated or 'all')"
    )
    EXCLUDED_TOOLS: str = Field(
        default="",
        description="Excluded tools (comma-separated)"
    )
```

**应用到 SessionConfig：**

```python
session_config = SessionConfig(
    tools=custom_tools,
    available_tools=self._parse_tool_list(self.valves.AVAILABLE_TOOLS),
    excluded_tools=self._parse_tool_list(self.valves.EXCLUDED_TOOLS),
    ...
)

def _parse_tool_list(self, value: str) -> list[str]:
    """解析工具列表"""
    if not value or value == "all":
        return []
    return [t.strip() for t in value.split(",") if t.strip()]
```

---

### 6. 🔲 on_permission_request（未实现）

**功能：** 处理权限请求（shell 命令、文件写入等）

**使用场景：**

- Copilot 需要执行 shell 命令
- 需要写入文件
- 需要访问 URL

**集成挑战：**

- 需要 OpenWebUI 前端支持实时权限弹窗
- 需要异步处理用户确认

**推荐方案：**

#### 方案 A：自动批准（开发/测试环境）

```python
async def auto_approve_permission_handler(
    request: dict,
    context: dict
) -> dict:
    """自动批准所有权限请求（危险！）"""
    return {
        "kind": "approved",
        "rules": []
    }

session_config = SessionConfig(
    on_permission_request=auto_approve_permission_handler,
    ...
)
```

#### 方案 B：基于规则的批准

```python
class Valves(BaseModel):
    ALLOW_SHELL_COMMANDS: bool = Field(default=False)
    ALLOW_FILE_WRITE: bool = Field(default=False)
    ALLOW_URL_ACCESS: bool = Field(default=True)

async def rule_based_permission_handler(
    request: dict,
    context: dict
) -> dict:
    kind = request.get("kind")
    
    if kind == "shell" and not self.valves.ALLOW_SHELL_COMMANDS:
        return {"kind": "denied-by-rules"}
    
    if kind == "write" and not self.valves.ALLOW_FILE_WRITE:
        return {"kind": "denied-by-rules"}
    
    if kind == "url" and not self.valves.ALLOW_URL_ACCESS:
        return {"kind": "denied-by-rules"}
    
    return {"kind": "approved", "rules": []}
```

#### 方案 C：通过 Event Emitter 请求用户确认（理想）

```python
async def interactive_permission_handler(
    request: dict,
    context: dict
) -> dict:
    """通过前端请求用户确认"""
    if not __event_emitter__:
        return {"kind": "denied-no-approval-rule-and-could-not-request-from-user"}
    
    # 发送权限请求到前端
    response_queue = asyncio.Queue()
    await __event_emitter__({
        "type": "permission_request",
        "data": {
            "kind": request.get("kind"),
            "description": request.get("description"),
            "response_queue": response_queue
        }
    })
    
    # 等待用户响应（带超时）
    try:
        user_response = await asyncio.wait_for(
            response_queue.get(),
            timeout=30.0
        )
        
        if user_response.get("approved"):
            return {"kind": "approved", "rules": []}
        else:
            return {"kind": "denied-interactively-by-user"}
    except asyncio.TimeoutError:
        return {"kind": "denied-no-approval-rule-and-could-not-request-from-user"}
```

---

### 7. 🔲 provider（BYOK - Bring Your Own Key）

**功能：** 使用自己的 API 密钥连接 OpenAI/Azure/Anthropic

**使用场景：**

- 不使用 GitHub Copilot 配额
- 直接连接云服务提供商
- 使用 Azure OpenAI 部署

**集成方案：**

```python
class Valves(BaseModel):
    USE_CUSTOM_PROVIDER: bool = Field(default=False)
    PROVIDER_TYPE: str = Field(
        default="openai",
        description="Provider type: openai, azure, anthropic"
    )
    PROVIDER_BASE_URL: str = Field(default="")
    PROVIDER_API_KEY: str = Field(default="")
    PROVIDER_BEARER_TOKEN: str = Field(default="")
    AZURE_API_VERSION: str = Field(default="2024-10-21")

def _build_provider_config(self) -> dict | None:
    """构建 Provider 配置"""
    if not self.valves.USE_CUSTOM_PROVIDER:
        return None
    
    config = {
        "type": self.valves.PROVIDER_TYPE,
        "base_url": self.valves.PROVIDER_BASE_URL,
    }
    
    if self.valves.PROVIDER_API_KEY:
        config["api_key"] = self.valves.PROVIDER_API_KEY
    
    if self.valves.PROVIDER_BEARER_TOKEN:
        config["bearer_token"] = self.valves.PROVIDER_BEARER_TOKEN
    
    if self.valves.PROVIDER_TYPE == "azure":
        config["azure"] = {
            "api_version": self.valves.AZURE_API_VERSION
        }
    
    # 自动推断 wire_api
    if self.valves.PROVIDER_TYPE == "anthropic":
        config["wire_api"] = "responses"
    else:
        config["wire_api"] = "completions"
    
    return config
```

**应用：**

```python
session_config = SessionConfig(
    provider=self._build_provider_config(),
    ...
)
```

---

### 8. ✅ streaming（已实现）

**功能：** 流式输出

**当前实现：**

```python
session_config = SessionConfig(
    streaming=body.get("stream", False),
    ...
)
```

---

### 9. 🔲 mcp_servers（MCP 协议）

**功能：** Model Context Protocol 服务器集成

**使用场景：**

- 连接外部数据源（数据库、API）
- 集成第三方服务

**集成方案：**

```python
class Valves(BaseModel):
    MCP_SERVERS_CONFIG: str = Field(
        default="{}",
        description="MCP servers configuration (JSON format)"
    )

def _parse_mcp_servers(self) -> dict | None:
    """解析 MCP 服务器配置"""
    if not self.valves.MCP_SERVERS_CONFIG:
        return None
    
    try:
        return json.loads(self.valves.MCP_SERVERS_CONFIG)
    except:
        return None
```

**配置示例：**

```json
{
  "database": {
    "type": "local",
    "command": "mcp-server-sqlite",
    "args": ["--db", "/path/to/db.sqlite"],
    "tools": ["*"]
  },
  "weather": {
    "type": "http",
    "url": "https://weather-api.example.com/mcp",
    "tools": ["get_weather", "get_forecast"]
  }
}
```

---

### 10. 🔲 custom_agents

**功能：** 自定义 AI 代理

**使用场景：**

- 专门化的子代理（如代码审查、文档编写）
- 不同的提示词策略

**集成方案：**

```python
class Valves(BaseModel):
    CUSTOM_AGENTS_CONFIG: str = Field(
        default="[]",
        description="Custom agents configuration (JSON array)"
    )

def _parse_custom_agents(self) -> list | None:
    """解析自定义代理配置"""
    if not self.valves.CUSTOM_AGENTS_CONFIG:
        return None
    
    try:
        return json.loads(self.valves.CUSTOM_AGENTS_CONFIG)
    except:
        return None
```

**配置示例：**

```json
[
  {
    "name": "code_reviewer",
    "display_name": "Code Reviewer",
    "description": "Reviews code for best practices",
    "prompt": "You are an expert code reviewer. Focus on security, performance, and maintainability.",
    "tools": ["read_file", "write_file"],
    "infer": true
  }
]
```

---

### 11. 🔲 config_dir

**功能：** 自定义配置目录

**当前支持：**

- 已有 `WORKSPACE_DIR` 控制工作目录

**增强方案：**

```python
class Valves(BaseModel):
    CONFIG_DIR: str = Field(
        default="",
        description="Custom config directory for session state"
    )

session_config = SessionConfig(
    config_dir=self.valves.CONFIG_DIR if self.valves.CONFIG_DIR else None,
    ...
)
```

---

### 12. 🔲 skill_directories / disabled_skills

**功能：** Copilot Skills 系统

**使用场景：**

- 加载自定义技能包
- 禁用特定技能

**集成方案：**

```python
class Valves(BaseModel):
    SKILL_DIRECTORIES: str = Field(
        default="",
        description="Comma-separated skill directories"
    )
    DISABLED_SKILLS: str = Field(
        default="",
        description="Comma-separated disabled skills"
    )

def _parse_skills_config(self):
    """解析技能配置"""
    skill_dirs = []
    if self.valves.SKILL_DIRECTORIES:
        skill_dirs = [
            d.strip() 
            for d in self.valves.SKILL_DIRECTORIES.split(",") 
            if d.strip()
        ]
    
    disabled = []
    if self.valves.DISABLED_SKILLS:
        disabled = [
            s.strip() 
            for s in self.valves.DISABLED_SKILLS.split(",") 
            if s.strip()
        ]
    
    return skill_dirs, disabled

# 应用
skill_dirs, disabled_skills = self._parse_skills_config()
session_config = SessionConfig(
    skill_directories=skill_dirs if skill_dirs else None,
    disabled_skills=disabled_skills if disabled_skills else None,
    ...
)
```

---

### 13. ✅ infinite_sessions（已实现）

**功能：** 无限会话与自动上下文压缩

**当前实现：**

```python
class Valves(BaseModel):
    INFINITE_SESSION: bool = Field(default=True)
    COMPACTION_THRESHOLD: float = Field(default=0.8)
    BUFFER_THRESHOLD: float = Field(default=0.95)

infinite_session_config = None
if self.valves.INFINITE_SESSION:
    infinite_session_config = {
        "enabled": True,
        "background_compaction_threshold": self.valves.COMPACTION_THRESHOLD,
        "buffer_exhaustion_threshold": self.valves.BUFFER_THRESHOLD,
    }

session_config = SessionConfig(
    infinite_sessions=infinite_session_config,
    ...
)
```

---

## 🎯 实施优先级建议

### 🔥 高优先级（立即实现）

1. **system_message** - 用户最常需要的功能
2. **on_permission_request (基于规则)** - 安全性需求

### 📌 中优先级（下一阶段）

3. **excluded_tools** - 完善工具管理
4. **provider (BYOK)** - 高级用户需求
5. **config_dir** - 增强会话管理

### 📋 低优先级（可选）

6. **mcp_servers** - 高级集成
7. **custom_agents** - 专业化功能
8. **skill_directories** - 生态系统功能

---

## 🚀 快速实施计划

### Phase 1: 基础增强（1-2小时）

```python
# 添加到 Valves
SYSTEM_MESSAGE: str = Field(default="")
SYSTEM_MESSAGE_MODE: str = Field(default="append")
EXCLUDED_TOOLS: str = Field(default="")

# 添加到 pipe() 方法
system_message_config = self._build_system_message_config()
excluded_tools = self._parse_tool_list(self.valves.EXCLUDED_TOOLS)

session_config = SessionConfig(
    system_message=system_message_config,
    excluded_tools=excluded_tools,
    ...
)
```

### Phase 2: 权限管理（2-3小时）

```python
# 添加权限控制 Valves
ALLOW_SHELL_COMMANDS: bool = Field(default=False)
ALLOW_FILE_WRITE: bool = Field(default=False)
ALLOW_URL_ACCESS: bool = Field(default=True)

# 实现权限处理器
session_config = SessionConfig(
    on_permission_request=self._create_permission_handler(),
    ...
)
```

### Phase 3: BYOK 支持（3-4小时）

```python
# 添加 Provider Valves
USE_CUSTOM_PROVIDER: bool = Field(default=False)
PROVIDER_TYPE: str = Field(default="openai")
PROVIDER_BASE_URL: str = Field(default="")
PROVIDER_API_KEY: str = Field(default="")

# 实现 Provider 配置
session_config = SessionConfig(
    provider=self._build_provider_config(),
    ...
)
```

---

## 📚 参考资源

- **SDK 类型定义**: `/opt/homebrew/.../copilot/types.py`
- **工具系统**: [TOOLS_USAGE.md](TOOLS_USAGE.md)
- **SDK 文档**: <https://github.com/github/copilot-sdk>

---

## ✅ 实施检查清单

使用此清单跟踪实施进度：

- [x] session_id
- [x] model
- [x] tools
- [x] streaming
- [x] infinite_sessions
- [ ] system_message
- [ ] available_tools (完善)
- [ ] excluded_tools
- [ ] on_permission_request
- [ ] provider (BYOK)
- [ ] mcp_servers
- [ ] custom_agents
- [ ] config_dir
- [ ] skill_directories
- [ ] disabled_skills

---

**作者：** Fu-Jie  
**版本：** v1.0  
**日期：** 2026-01-26  
**更新：** 随功能实施持续更新
