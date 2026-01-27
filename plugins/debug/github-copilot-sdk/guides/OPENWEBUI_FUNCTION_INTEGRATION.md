# OpenWebUI Function 集成方案

## 🎯 核心挑战

在 Copilot Tool Handler 中调用 OpenWebUI Functions 的关键问题：

**问题：** Copilot SDK 的 Tool Handler 是一个独立的回调函数，如何在这个上下文中访问和执行 OpenWebUI 的 Function？

---

## 🔍 OpenWebUI Function 系统分析

### 1. Function 数据结构

OpenWebUI 的 Function/Tool 传递格式：

```python
body = {
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
}
```

### 2. Function 执行机制

OpenWebUI Functions 的执行方式有几种可能：

#### 选项 A: 通过 Function ID 调用内部 API

```python
# 假设 OpenWebUI 提供内部 API
from open_webui.apps.webui.models.functions import Functions

function_id = "function_uuid"  # 需要从配置中获取
result = await Functions.execute_function(
    function_id=function_id,
    arguments={"location": "Beijing"}
)
```

#### 选项 B: 通过 **event_emitter** 触发

```python
# 通过事件系统触发 function 执行
if __event_emitter__:
    await __event_emitter__({
        "type": "function_call",
        "data": {
            "name": "get_weather",
            "arguments": {"location": "Beijing"}
        }
    })
```

#### 选项 C: 自己实现 Function 逻辑

```python
# 在 Pipe 内部实现常用功能
class Pipe:
    def _builtin_get_weather(self, location: str) -> dict:
        # 实现天气查询
        pass
    
    def _builtin_search_web(self, query: str) -> dict:
        # 实现网页搜索
        pass
```

---

## 💡 推荐方案：混合架构

### 架构设计

```
User Message
    ↓
OpenWebUI UI (Functions 已配置)
    ↓
Pipe.pipe(body) - body 包含 tools[]
    ↓
转换为 Copilot Tools + 存储 Function Registry
    ↓
Copilot 决定调用 Tool
    ↓
Tool Handler 查询 Registry → 执行对应逻辑
    ↓
返回结果给 Copilot
    ↓
继续生成回答
```

### 核心实现

#### 1. Function Registry（函数注册表）

```python
class Pipe:
    def __init__(self):
        # ...
        self._function_registry = {}  # {function_name: callable}
        self._function_metadata = {}  # {function_name: metadata}
```

#### 2. 注册 Functions

```python
def _register_openwebui_functions(
    self, 
    owui_functions: List[dict],
    __event_emitter__=None,
    __event_call__=None
):
    """
    注册 OpenWebUI Functions 到内部 registry
    
    关键：将 function 定义和执行逻辑关联起来
    """
    for func_def in owui_functions:
        if func_def.get("type") != "function":
            continue
        
        func_info = func_def.get("function", {})
        func_name = func_info.get("name")
        
        if not func_name:
            continue
        
        # 存储元数据
        self._function_metadata[func_name] = {
            "description": func_info.get("description", ""),
            "parameters": func_info.get("parameters", {}),
            "original_def": func_def
        }
        
        # 创建执行器（关键）
        executor = self._create_function_executor(
            func_name,
            func_def,
            __event_emitter__,
            __event_call__
        )
        
        self._function_registry[func_name] = executor
```

#### 3. Function Executor 工厂

```python
def _create_function_executor(
    self,
    func_name: str,
    func_def: dict,
    __event_emitter__=None,
    __event_call__=None
):
    """
    为每个 function 创建执行器
    
    策略：
    1. 优先使用内置实现
    2. 尝试调用 OpenWebUI API
    3. 返回错误
    """
    
    async def executor(arguments: dict) -> dict:
        # 策略 1: 检查是否有内置实现
        builtin_method = getattr(self, f"_builtin_{func_name}", None)
        if builtin_method:
            self._emit_debug_log_sync(
                f"Using builtin implementation for {func_name}",
                __event_call__
            )
            try:
                result = builtin_method(arguments)
                if inspect.iscoroutine(result):
                    result = await result
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 策略 2: 尝试通过 Event Emitter 调用
        if __event_emitter__:
            try:
                # 尝试触发 function_call 事件
                response_queue = asyncio.Queue()
                
                await __event_emitter__({
                    "type": "function_call",
                    "data": {
                        "name": func_name,
                        "arguments": arguments,
                        "response_queue": response_queue  # 回调队列
                    }
                })
                
                # 等待结果（带超时）
                result = await asyncio.wait_for(
                    response_queue.get(),
                    timeout=self.valves.TOOL_TIMEOUT
                )
                
                return {"success": True, "result": result}
            except asyncio.TimeoutError:
                return {"success": False, "error": "Function execution timeout"}
            except Exception as e:
                self._emit_debug_log_sync(
                    f"Event emitter call failed: {e}",
                    __event_call__
                )
                # 继续尝试其他方法
        
        # 策略 3: 尝试调用 OpenWebUI internal API
        try:
            # 这需要研究 OpenWebUI 源码确定正确的调用方式
            from open_webui.apps.webui.models.functions import Functions
            
            # 需要获取 function_id（这是关键问题）
            function_id = self._get_function_id_by_name(func_name)
            
            if function_id:
                result = await Functions.execute(
                    function_id=function_id,
                    params=arguments
                )
                return {"success": True, "result": result}
        except ImportError:
            pass
        except Exception as e:
            self._emit_debug_log_sync(
                f"OpenWebUI API call failed: {e}",
                __event_call__
            )
        
        # 策略 4: 返回"未实现"错误
        return {
            "success": False,
            "error": f"Function '{func_name}' is not implemented. "
                     "Please implement it as a builtin method or ensure OpenWebUI API is available."
        }
    
    return executor
```

#### 4. Tool Handler 实现

```python
def _create_tool_handler(self, tool_name: str, __event_call__=None):
    """为 Copilot SDK 创建 Tool Handler"""
    
    async def handler(invocation: dict) -> dict:
        """
        Copilot Tool Handler
        
        invocation: {
            "session_id": str,
            "tool_call_id": str,
            "tool_name": str,
            "arguments": dict
        }
        """
        try:
            # 从 registry 获取 executor
            executor = self._function_registry.get(invocation["tool_name"])
            
            if not executor:
                return {
                    "textResultForLlm": f"Function '{invocation['tool_name']}' not found.",
                    "resultType": "failure",
                    "error": "function_not_found",
                    "toolTelemetry": {}
                }
            
            # 执行 function
            self._emit_debug_log_sync(
                f"Executing function: {invocation['tool_name']}({invocation['arguments']})",
                __event_call__
            )
            
            exec_result = await executor(invocation["arguments"])
            
            # 处理结果
            if exec_result.get("success"):
                result_text = str(exec_result.get("result", ""))
                return {
                    "textResultForLlm": result_text,
                    "resultType": "success",
                    "error": None,
                    "toolTelemetry": {}
                }
            else:
                error_msg = exec_result.get("error", "Unknown error")
                return {
                    "textResultForLlm": f"Function execution failed: {error_msg}",
                    "resultType": "failure",
                    "error": error_msg,
                    "toolTelemetry": {}
                }
                
        except Exception as e:
            self._emit_debug_log_sync(
                f"Tool handler error: {e}",
                __event_call__
            )
            return {
                "textResultForLlm": "An unexpected error occurred during function execution.",
                "resultType": "failure",
                "error": str(e),
                "toolTelemetry": {}
            }
    
    return handler
```

---

## 🔌 内置 Functions 实现示例

### 示例 1: 获取当前时间

```python
def _builtin_get_current_time(self, arguments: dict) -> str:
    """内置实现：获取当前时间"""
    from datetime import datetime
    
    timezone = arguments.get("timezone", "UTC")
    format_str = arguments.get("format", "%Y-%m-%d %H:%M:%S")
    
    now = datetime.now()
    return now.strftime(format_str)
```

### 示例 2: 简单计算器

```python
def _builtin_calculate(self, arguments: dict) -> str:
    """内置实现：数学计算"""
    expression = arguments.get("expression", "")
    
    try:
        # 安全的数学计算（仅允许基本运算）
        allowed_chars = set("0123456789+-*/()., ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
```

### 示例 3: 网页搜索（需要外部 API）

```python
async def _builtin_search_web(self, arguments: dict) -> str:
    """内置实现：网页搜索（使用 DuckDuckGo）"""
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    try:
        # 使用 duckduckgo_search 库
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
        
        # 格式化结果
        formatted = "\n\n".join([
            f"**{r['title']}**\n{r['url']}\n{r['snippet']}"
            for r in results
        ])
        
        return formatted
    except Exception as e:
        raise ValueError(f"Search failed: {e}")
```

---

## 🚀 完整集成流程

### pipe() 方法中的集成

```python
async def pipe(
    self,
    body: dict,
    __metadata__: Optional[dict] = None,
    __event_emitter__=None,
    __event_call__=None,
) -> Union[str, AsyncGenerator]:
    # ... 现有代码 ...
    
    # ✅ Step 1: 提取 OpenWebUI Functions
    owui_functions = body.get("tools", [])
    
    # ✅ Step 2: 注册 Functions
    if self.valves.ENABLE_TOOLS and owui_functions:
        self._register_openwebui_functions(
            owui_functions,
            __event_emitter__,
            __event_call__
        )
    
    # ✅ Step 3: 转换为 Copilot Tools
    copilot_tools = []
    for func_name in self._function_registry.keys():
        metadata = self._function_metadata[func_name]
        copilot_tools.append({
            "name": func_name,
            "description": metadata["description"],
            "parameters": metadata["parameters"],
            "handler": self._create_tool_handler(func_name, __event_call__)
        })
    
    # ✅ Step 4: 创建 Session 并传递 Tools
    session_config = SessionConfig(
        model=real_model_id,
        tools=copilot_tools,  # ✅ 关键
        ...
    )
    
    session = await client.create_session(config=session_config)
    
    # ... 后续代码 ...
```

---

## ⚠️ 待解决问题

### 1. Function ID 映射

**问题：** OpenWebUI Functions 通常通过 UUID 标识，但 body 中只有 name

**解决思路：**

- 在 OpenWebUI 启动时建立 name → id 映射表
- 或者修改 OpenWebUI 在 body 中同时传递 id

### 2. Event Emitter 回调机制

**问题：** 不确定 **event_emitter** 是否支持 function_call 事件

**验证方法：**

```python
# 测试代码
await __event_emitter__({
    "type": "function_call",
    "data": {"name": "test_func", "arguments": {}}
})
```

### 3. 异步执行超时

**问题：** 某些 Functions 可能执行很慢

**解决方案：**

- 实现 timeout 机制（已在 executor 中实现）
- 对于长时间运行的任务，考虑返回"processing"状态

---

## 📝 实现清单

- [ ] 实现 _function_registry 和 _function_metadata
- [ ] 实现 _register_openwebui_functions()
- [ ] 实现 _create_function_executor()
- [ ] 实现 _create_tool_handler()
- [ ] 实现 3-5 个常用内置 Functions
- [ ] 测试 Function 注册和调用流程
- [ ] 验证 **event_emitter** 机制
- [ ] 研究 OpenWebUI Functions API
- [ ] 添加错误处理和超时机制
- [ ] 更新文档

---

**下一步行动：**

1. 实现基础的 Function Registry
2. 添加 2-3 个简单的内置 Functions（如 get_time, calculate）
3. 测试基本的 Tool Calling 流程
4. 根据测试结果调整架构

**作者：** Fu-Jie  
**日期：** 2026-01-26
