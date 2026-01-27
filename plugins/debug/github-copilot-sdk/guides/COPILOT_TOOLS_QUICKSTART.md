# GitHub Copilot SDK 自定义工具快速入门

## 🎯 目标

在 OpenWebUI Pipe 中直接使用 GitHub Copilot SDK 的自定义工具功能，无需集成 OpenWebUI Function 系统。

---

## 📖 基础概念

### Copilot SDK Tool 的三要素

```python
from copilot.types import Tool, ToolInvocation, ToolResult

# 1. Tool Definition（工具定义）
tool = Tool(
    name="tool_name",               # 工具名称
    description="What it does",    # 描述（给 AI 看的）
    parameters={...},              # JSON Schema 参数定义
    handler=handler_function       # 处理函数
)

# 2. Tool Handler（处理函数）
async def handler_function(invocation: ToolInvocation) -> ToolResult:
    # invocation 包含：
    # - session_id: 会话 ID
    # - tool_call_id: 调用 ID
    # - tool_name: 工具名称  
    # - arguments: dict（实际参数）
    
    result = do_something(invocation["arguments"])
    
    return ToolResult(
        textResultForLlm="结果文本",
        resultType="success",  # 或 "failure"
        error=None,
        toolTelemetry={}
    )

# 3. Session Configuration（会话配置）
session_config = SessionConfig(
    model="claude-sonnet-4.5",
    tools=[tool1, tool2, tool3],  # ✅ 传入工具列表
    streaming=True
)
```

---

## 💻 完整实现示例

### 示例 1：获取当前时间

```python
from datetime import datetime
from copilot.types import Tool, ToolInvocation, ToolResult

def create_time_tool():
    """创建获取时间的工具"""
    
    async def get_time_handler(invocation: ToolInvocation) -> ToolResult:
        """工具处理函数"""
        try:
            # 获取参数
            timezone = invocation["arguments"].get("timezone", "UTC")
            format_str = invocation["arguments"].get("format", "%Y-%m-%d %H:%M:%S")
            
            # 执行逻辑
            current_time = datetime.now().strftime(format_str)
            result_text = f"Current time: {current_time}"
            
            # 返回结果
            return ToolResult(
                textResultForLlm=result_text,
                resultType="success",
                error=None,
                toolTelemetry={"execution_time": "fast"}
            )
            
        except Exception as e:
            return ToolResult(
                textResultForLlm=f"Error getting time: {str(e)}",
                resultType="failure",
                error=str(e),
                toolTelemetry={}
            )
    
    # 创建工具定义
    return Tool(
        name="get_current_time",
        description="Get the current date and time. Useful when user asks 'what time is it' or needs to know the current date.",
        parameters={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., 'UTC', 'Asia/Shanghai')",
                    "default": "UTC"
                },
                "format": {
                    "type": "string",
                    "description": "Time format string",
                    "default": "%Y-%m-%d %H:%M:%S"
                }
            }
        },
        handler=get_time_handler
    )
```

### 示例 2：数学计算器

```python
def create_calculator_tool():
    """创建计算器工具"""
    
    async def calculate_handler(invocation: ToolInvocation) -> ToolResult:
        try:
            expression = invocation["arguments"].get("expression", "")
            
            # 安全检查
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Expression contains invalid characters")
            
            # 计算（安全的 eval）
            result = eval(expression, {"__builtins__": {}})
            
            return ToolResult(
                textResultForLlm=f"The result of {expression} is {result}",
                resultType="success",
                error=None,
                toolTelemetry={}
            )
            
        except Exception as e:
            return ToolResult(
                textResultForLlm=f"Calculation error: {str(e)}",
                resultType="failure",
                error=str(e),
                toolTelemetry={}
            )
    
    return Tool(
        name="calculate",
        description="Perform mathematical calculations. Supports basic arithmetic operations (+, -, *, /).",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                }
            },
            "required": ["expression"]
        },
        handler=calculate_handler
    )
```

### 示例 3：随机数生成器

```python
import random

def create_random_number_tool():
    """创建随机数生成工具"""
    
    async def random_handler(invocation: ToolInvocation) -> ToolResult:
        try:
            min_val = invocation["arguments"].get("min", 1)
            max_val = invocation["arguments"].get("max", 100)
            
            if min_val >= max_val:
                raise ValueError("min must be less than max")
            
            number = random.randint(min_val, max_val)
            
            return ToolResult(
                textResultForLlm=f"Generated random number: {number}",
                resultType="success",
                error=None,
                toolTelemetry={}
            )
            
        except Exception as e:
            return ToolResult(
                textResultForLlm=f"Error: {str(e)}",
                resultType="failure",
                error=str(e),
                toolTelemetry={}
            )
    
    return Tool(
        name="generate_random_number",
        description="Generate a random integer within a specified range.",
        parameters={
            "type": "object",
            "properties": {
                "min": {
                    "type": "integer",
                    "description": "Minimum value (inclusive)",
                    "default": 1
                },
                "max": {
                    "type": "integer",
                    "description": "Maximum value (inclusive)",
                    "default": 100
                }
            }
        },
        handler=random_handler
    )
```

---

## 🔧 集成到 Pipe

### 完整的 Pipe 实现

```python
class Pipe:
    class Valves(BaseModel):
        # ... 现有 Valves ...
        
        ENABLE_TOOLS: bool = Field(
            default=False,
            description="Enable custom tools (time, calculator, random)"
        )
        AVAILABLE_TOOLS: str = Field(
            default="all",
            description="Available tools: 'all' or comma-separated list (e.g., 'get_current_time,calculate')"
        )
    
    def __init__(self):
        # ... 现有初始化 ...
        self._custom_tools = []
        
    def _initialize_custom_tools(self):
        """初始化自定义工具"""
        if not self.valves.ENABLE_TOOLS:
            return []
        
        # 定义所有可用工具
        all_tools = {
            "get_current_time": create_time_tool(),
            "calculate": create_calculator_tool(),
            "generate_random_number": create_random_number_tool(),
        }
        
        # 根据配置过滤工具
        if self.valves.AVAILABLE_TOOLS == "all":
            return list(all_tools.values())
        
        # 只启用指定的工具
        enabled = [t.strip() for t in self.valves.AVAILABLE_TOOLS.split(",")]
        return [all_tools[name] for name in enabled if name in all_tools]
    
    async def pipe(
        self,
        body: dict,
        __metadata__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Union[str, AsyncGenerator]:
        # ... 现有代码 ...
        
        # ✅ 初始化工具
        custom_tools = self._initialize_custom_tools()
        
        if custom_tools:
            await self._emit_debug_log(
                f"Enabled {len(custom_tools)} custom tools: {[t.name for t in custom_tools]}",
                __event_call__
            )
        
        # ✅ 创建会话配置（传入工具）
        from copilot.types import SessionConfig, InfiniteSessionConfig
        
        session_config = SessionConfig(
            session_id=chat_id if chat_id else None,
            model=real_model_id,
            streaming=body.get("stream", False),
            tools=custom_tools,  # ✅✅✅ 关键：传入工具列表
            infinite_sessions=infinite_session_config if self.valves.INFINITE_SESSION else None,
        )
        
        session = await client.create_session(config=session_config)
        
        # ... 其余代码保持不变 ...
```

---

## 📊 处理工具调用事件

### 在 stream_response 中显示工具调用

```python
async def stream_response(
    self, client, session, send_payload, init_message: str = "", __event_call__=None
) -> AsyncGenerator:
    # ... 现有代码 ...
    
    def handler(event):
        event_type = str(getattr(event.type, "value", event.type))
        
        # ✅ 工具调用开始
        if "tool_invocation_started" in event_type or "tool_call_started" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            if tool_name:
                queue.put_nowait(f"\n\n🔧 **Calling tool**: `{tool_name}`\n")
        
        # ✅ 工具调用完成
        elif "tool_invocation_completed" in event_type or "tool_call_completed" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            result = get_event_data(event, "result", "")
            if tool_name:
                queue.put_nowait(f"\n✅ **Tool `{tool_name}` completed**\n")
        
        # ✅ 工具调用失败
        elif "tool_invocation_failed" in event_type or "tool_call_failed" in event_type:
            tool_name = get_event_data(event, "tool_name", "")
            error = get_event_data(event, "error", "")
            if tool_name:
                queue.put_nowait(f"\n❌ **Tool `{tool_name}` failed**: {error}\n")
        
        # ... 其他事件处理 ...
    
    # ... 其余代码 ...
```

---

## 🧪 测试示例

### 测试 1：询问时间

```
User: "What time is it now?"

Expected Flow:
1. Copilot 识别需要调用 get_current_time 工具
2. 调用工具（无参数或默认参数）
3. 工具返回: "Current time: 2026-01-26 15:30:00"
4. Copilot 回答: "The current time is 2026-01-26 15:30:00"

Pipe Output:
---
🔧 **Calling tool**: `get_current_time`
✅ **Tool `get_current_time` completed**
The current time is 2026-01-26 15:30:00
---
```

### 测试 2：数学计算

```
User: "Calculate 123 * 456"

Expected Flow:
1. Copilot 调用 calculate 工具
2. 参数: {"expression": "123 * 456"}
3. 工具返回: "The result of 123 * 456 is 56088"
4. Copilot 回答: "123 multiplied by 456 equals 56,088"

Pipe Output:
---
🔧 **Calling tool**: `calculate`
✅ **Tool `calculate` completed**
123 multiplied by 456 equals 56,088
---
```

### 测试 3：生成随机数

```
User: "Give me a random number between 1 and 10"

Expected Flow:
1. Copilot 调用 generate_random_number 工具
2. 参数: {"min": 1, "max": 10}
3. 工具返回: "Generated random number: 7"
4. Copilot 回答: "I generated a random number for you: 7"
```

---

## 🔍 调试技巧

### 1. 记录所有工具事件

```python
def handler(event):
    event_type = str(getattr(event.type, "value", event.type))
    
    # 记录所有包含 "tool" 的事件
    if "tool" in event_type.lower():
        event_data = {}
        if hasattr(event, "data"):
            try:
                event_data = {
                    "type": event_type,
                    "data": str(event.data)[:200]  # 截断长数据
                }
            except:
                pass
        
        self._emit_debug_log_sync(
            f"Tool Event: {json.dumps(event_data)}",
            __event_call__
        )
```

### 2. 验证工具注册

```python
async def pipe(...):
    # ...
    custom_tools = self._initialize_custom_tools()
    
    # 调试：打印工具信息
    if self.valves.DEBUG:
        tool_info = [
            {
                "name": t.name,
                "description": t.description[:50],
                "has_handler": t.handler is not None
            }
            for t in custom_tools
        ]
        await self._emit_debug_log(
            f"Registered tools: {json.dumps(tool_info, indent=2)}",
            __event_call__
        )
```

### 3. 测试工具处理函数

```python
# 单独测试工具
async def test_tool():
    tool = create_time_tool()
    
    # 模拟调用
    invocation = {
        "session_id": "test",
        "tool_call_id": "test_call",
        "tool_name": "get_current_time",
        "arguments": {"format": "%H:%M:%S"}
    }
    
    result = await tool.handler(invocation)
    print(f"Result: {result}")
```

---

## ⚠️ 注意事项

### 1. 工具描述的重要性

工具的 `description` 字段非常重要，它告诉 AI 何时应该使用这个工具：

```python
# ❌ 差的描述
description="Get time"

# ✅ 好的描述
description="Get the current date and time. Use this when the user asks 'what time is it', 'what's the date', or needs to know the current timestamp."
```

### 2. 参数定义

使用标准的 JSON Schema 定义参数：

```python
parameters={
    "type": "object",
    "properties": {
        "param_name": {
            "type": "string",  # string, integer, boolean, array, object
            "description": "Clear description",
            "enum": ["option1", "option2"],  # 可选：枚举值
            "default": "default_value"       # 可选：默认值
        }
    },
    "required": ["param_name"]  # 必需参数
}
```

### 3. 错误处理

总是捕获异常并返回有意义的错误：

```python
try:
    result = do_something()
    return ToolResult(
        textResultForLlm=f"Success: {result}",
        resultType="success",
        error=None,
        toolTelemetry={}
    )
except Exception as e:
    return ToolResult(
        textResultForLlm=f"Error occurred: {str(e)}",
        resultType="failure",
        error=str(e),  # 用于调试
        toolTelemetry={}
    )
```

### 4. 异步 vs 同步

工具处理函数可以是同步或异步：

```python
# 同步工具
def sync_handler(invocation):
    result = calculate(invocation["arguments"])
    return ToolResult(...)

# 异步工具（推荐）
async def async_handler(invocation):
    result = await fetch_data(invocation["arguments"])
    return ToolResult(...)
```

---

## 🚀 快速开始清单

- [ ] 1. 在 Valves 中添加 `ENABLE_TOOLS` 配置
- [ ] 2. 定义 2-3 个简单的工具函数
- [ ] 3. 实现 `_initialize_custom_tools()` 方法
- [ ] 4. 修改 `SessionConfig` 传入 `tools` 参数
- [ ] 5. 在 `stream_response` 中添加工具事件处理
- [ ] 6. 测试：询问时间、计算数学、生成随机数
- [ ] 7. 添加调试日志
- [ ] 8. 同步中文版本

---

## 📚 完整的工具事件列表

根据 SDK 源码，可能的工具相关事件：

- `tool_invocation_started` / `tool_call_started`
- `tool_invocation_completed` / `tool_call_completed`
- `tool_invocation_failed` / `tool_call_failed`
- `tool_parameter_validation_failed`

实际事件名称可能因 SDK 版本而异，建议先记录所有事件类型：

```python
def handler(event):
    print(f"Event type: {event.type}")
```

---

**快速实现入口：** 从示例 1（获取时间）开始，这是最简单的工具，可以快速验证整个流程！

**作者：** Fu-Jie  
**日期：** 2026-01-26
