# GitHub Copilot SDK - Tool 功能实现指南

## 📋 概述

本指南介绍如何在 GitHub Copilot SDK Pipe 中实现 Function/Tool Calling 功能。

---

## 🏗️ 架构设计

### 工作流程

```
OpenWebUI Tools/Functions
    ↓ (转换)
Copilot SDK Tool Definition
    ↓ (注册)
Session Tool Handlers
    ↓ (调用)
Tool Execution → Result
    ↓ (返回)
Continue Conversation
```

### 核心接口

#### 1. Tool Definition（工具定义）

```python
from copilot.types import Tool

tool = Tool(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g., 'San Francisco'"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        "required": ["location"]
    },
    handler=weather_handler  # 处理函数
)
```

#### 2. Tool Handler（处理函数）

```python
from copilot.types import ToolInvocation, ToolResult

async def weather_handler(invocation: ToolInvocation) -> ToolResult:
    """
    invocation 包含：
    - session_id: str
    - tool_call_id: str
    - tool_name: str
    - arguments: dict  # {"location": "San Francisco", "unit": "celsius"}
    """
    location = invocation["arguments"]["location"]
    
    # 执行实际逻辑
    weather_data = await fetch_weather(location)
    
    # 返回结果
    return ToolResult(
        textResultForLlm=f"Weather in {location}: {weather_data['temp']}°C, {weather_data['condition']}",
        resultType="success",  # or "failure"
        error=None,
        toolTelemetry={"execution_time_ms": 150}
    )
```

#### 3. Session Configuration（会话配置）

```python
from copilot.types import SessionConfig

session_config = SessionConfig(
    model="claude-sonnet-4.5",
    tools=[tool1, tool2, tool3],  # ✅ 传递工具列表
    available_tools=["get_weather", "search_web"],  # 可选：过滤可用工具
    excluded_tools=["dangerous_tool"],  # 可选：排除工具
)

session = await client.create_session(config=session_config)
```

---

## 💻 实现方案

### 方案 A：桥接 OpenWebUI Tools（推荐）

#### 1. 添加 Valves 配置

```python
class Valves(BaseModel):
    ENABLE_TOOLS: bool = Field(
        default=True,
        description="Enable OpenWebUI tool integration"
    )
    TOOL_TIMEOUT: int = Field(
        default=30,
        description="Tool execution timeout (seconds)"
    )
    AVAILABLE_TOOLS: str = Field(
        default="",
        description="Filter specific tools (comma separated, empty = all)"
    )
```

#### 2. 实现 Tool 转换器

```python
def _convert_openwebui_tools_to_copilot(
    self, 
    owui_tools: List[dict],
    __event_call__=None
) -> List[dict]:
    """
    将 OpenWebUI tools 转换为 Copilot SDK 格式
    
    OpenWebUI Tool 格式：
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather info",
            "parameters": {...}  # JSON Schema
        }
    }
    """
    copilot_tools = []
    
    for tool in owui_tools:
        if tool.get("type") != "function":
            continue
        
        func = tool.get("function", {})
        tool_name = func.get("name")
        
        if not tool_name:
            continue
        
        # 应用过滤器
        if self.valves.AVAILABLE_TOOLS:
            allowed = [t.strip() for t in self.valves.AVAILABLE_TOOLS.split(",")]
            if tool_name not in allowed:
                continue
        
        copilot_tools.append({
            "name": tool_name,
            "description": func.get("description", ""),
            "parameters": func.get("parameters", {}),
            "handler": self._create_tool_handler(tool_name, __event_call__)
        })
        
        self._emit_debug_log_sync(
            f"Registered tool: {tool_name}",
            __event_call__
        )
    
    return copilot_tools
```

#### 3. 实现动态 Tool Handler

```python
def _create_tool_handler(self, tool_name: str, __event_call__=None):
    """为每个 tool 创建 handler 函数"""
    
    async def handler(invocation: dict) -> dict:
        """
        Tool handler 实现
        
        invocation 结构：
        {
            "session_id": "...",
            "tool_call_id": "...",
            "tool_name": "get_weather",
            "arguments": {"location": "Beijing"}
        }
        """
        try:
            self._emit_debug_log_sync(
                f"Tool called: {invocation['tool_name']} with {invocation['arguments']}",
                __event_call__
            )
            
            # 方法 1: 调用 OpenWebUI 内部 Function API
            result = await self._execute_openwebui_function(
                function_name=invocation["tool_name"],
                arguments=invocation["arguments"]
            )
            
            # 方法 2: 通过 __event_emitter__ 触发（需要测试）
            # 方法 3: 直接实现工具逻辑
            
            return {
                "textResultForLlm": str(result),
                "resultType": "success",
                "error": None,
                "toolTelemetry": {}
            }
            
        except asyncio.TimeoutError:
            return {
                "textResultForLlm": "Tool execution timed out.",
                "resultType": "failure",
                "error": "timeout",
                "toolTelemetry": {}
            }
        except Exception as e:
            self._emit_debug_log_sync(
                f"Tool error: {e}",
                __event_call__
            )
            return {
                "textResultForLlm": f"Tool execution failed: {str(e)}",
                "resultType": "failure",
                "error": str(e),
                "toolTelemetry": {}
            }
    
    return handler
```

#### 4. 集成到 pipe() 方法

```python
async def pipe(
    self,
    body: dict,
    __metadata__: Optional[dict] = None,
    __event_emitter__=None,
    __event_call__=None,
) -> Union[str, AsyncGenerator]:
    # ... 现有代码 ...
    
    # ✅ 提取并转换 tools
    copilot_tools = []
    if self.valves.ENABLE_TOOLS and body.get("tools"):
        copilot_tools = self._convert_openwebui_tools_to_copilot(
            body["tools"],
            __event_call__
        )
        
        await self._emit_debug_log(
            f"Enabled {len(copilot_tools)} tools",
            __event_call__
        )
    
    # ✅ 传递给 SessionConfig
    session_config = SessionConfig(
        session_id=chat_id if chat_id else None,
        model=real_model_id,
        streaming=body.get("stream", False),
        tools=copilot_tools,  # ✅ 关键
        infinite_sessions=infinite_session_config,
    )
    
    session = await client.create_session(config=session_config)
    # ...
```

#### 5. 处理 Tool 调用事件

```python
def stream_response(...):
    def handler(event):
        event_type = str(event.type)
        
        # ✅ Tool 调用开始
        if "tool_invocation_started" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            yield f"\n🔧 **Calling tool**: `{tool_name}`\n"
        
        # ✅ Tool 调用完成
        elif "tool_invocation_completed" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            result = get_event_data(event, "result", "")
            yield f"\n✅ **Tool result**: {result}\n"
        
        # ✅ Tool 调用失败
        elif "tool_invocation_failed" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            error = get_event_data(event, "error", "")
            yield f"\n❌ **Tool failed**: `{tool_name}` - {error}\n"
```

---

### 方案 B：自定义 Tool 实现

#### Valves 配置

```python
class Valves(BaseModel):
    CUSTOM_TOOLS: str = Field(
        default="[]",
        description="Custom tools JSON: [{name, description, parameters, implementation}]"
    )
```

#### 工具定义示例

```json
[
  {
    "name": "calculate",
    "description": "Perform mathematical calculations",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "Math expression, e.g., '2 + 2 * 3'"
        }
      },
      "required": ["expression"]
    },
    "implementation": "eval"  // 或指定 Python 函数名
  }
]
```

---

## 🧪 测试方案

### 1. 测试 Tool 定义

```python
# 在 OpenWebUI 中创建一个简单的 Function:
# Name: get_time
# Description: Get current time
# Parameters: {"type": "object", "properties": {}}

# 测试对话：
# User: "What time is it?"
# Expected: Copilot 调用 get_time tool，返回当前时间
```

### 2. 测试 Tool 调用链

```python
# User: "Search for Python tutorials and summarize the top 3 results"
# Expected Flow:
# 1. Copilot calls search_web(query="Python tutorials")
# 2. Copilot receives search results
# 3. Copilot summarizes top 3
# 4. Returns final answer
```

### 3. 测试错误处理

```python
# User: "Call a non-existent tool"
# Expected: 返回 "Tool not supported" error
```

---

## 📊 事件监听

Tool 相关事件类型：

- `tool_invocation_started` - Tool 调用开始
- `tool_invocation_completed` - Tool 完成
- `tool_invocation_failed` - Tool 失败
- `tool_parameter_validation_failed` - 参数验证失败

---

## ⚠️ 注意事项

### 1. 安全性

- ✅ 验证 tool parameters
- ✅ 限制执行超时
- ✅ 不暴露详细错误信息给 LLM
- ❌ 禁止执行危险命令（如 `rm -rf`）

### 2. 性能

- ⏱️ 设置合理的 timeout
- 🔄 考虑异步执行长时间运行的 tool
- 📊 记录 tool 执行时间（toolTelemetry）

### 3. 调试

- 🐛 在 DEBUG 模式下记录所有 tool 调用
- 📝 记录 arguments 和 results
- 🔍 使用前端 console 显示 tool 流程

---

## 🔗 参考资源

- [GitHub Copilot SDK 官方文档](https://github.com/github/copilot-sdk)
- [OpenWebUI Function API](https://docs.openwebui.com/features/plugin-system)
- [JSON Schema 规范](https://json-schema.org/)

---

## 📝 实现清单

- [ ] 添加 ENABLE_TOOLS Valve
- [ ] 实现 _convert_openwebui_tools_to_copilot()
- [ ] 实现 _create_tool_handler()
- [ ] 修改 SessionConfig 传递 tools
- [ ] 处理 tool 事件流
- [ ] 添加调试日志
- [ ] 测试基础 tool 调用
- [ ] 测试错误处理
- [ ] 更新文档和 README
- [ ] 同步中文版本

---

**作者：** Fu-Jie  
**版本：** v1.0  
**日期：** 2026-01-26
