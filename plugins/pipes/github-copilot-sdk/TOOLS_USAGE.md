# 🛠️ Custom Tools Usage / 自定义工具使用指南

## Overview / 概览

This pipe supports **OpenWebUI Native Tools** (Functions) and **Custom Python Tools**.
本 Pipe 支持 **OpenWebUI 原生工具** (Functions) 和 **自定义 Python 工具**。

---

## 🚀 OpenWebUI Native Tools / OpenWebUI 原生工具 (v0.3.1)

**New in v0.3.1**: You can use any tool defined in OpenWebUI directly with Copilot.
**v0.3.1 新增**: 您可以直接在 Copilot 中使用 OpenWebUI 中定义的任何工具。

**How to use / 如何使用:**

1. Go to **Workspace** -> **Tools**.
2. Create a tool (e.g. `get_weather`).
3. In Copilot Chat settings (Valves), ensure `ENABLE_OPENWEBUI_TOOLS` is `True` (default).
4. Ask Copilot: "Search for the latest news" or "Check weather".

**Note / 注意:**

- Tool names are automatically sanitized to match Copilot SDK requirements (e.g. `my.tool` -> `my_tool`).
- 工具名称会自动净化以符合 Copilot SDK 要求（例如 `my.tool` 变为 `my_tool`）。

---

## 📦 Python Custom Tools / Python 自定义工具

This pipe includes **1 example custom tool** that demonstrates how to use GitHub Copilot SDK's tool calling feature directly in Python code.
本 Pipe 包含 **1 个示例自定义工具**，展示如何使用 GitHub Copilot SDK 的工具调用功能。

### 1. `generate_random_number` / 生成随机数

**Description:** Generate a random integer
**描述：** 生成随机整数

**Parameters / 参数:**

- `min` (optional): Minimum value (default: 1)
- `max` (optional): Maximum value (default: 100)
- `min` (可选): 最小值 (默认: 1)
- `max` (可选): 最大值 (默认: 100)

**Example / 示例:**

```
User: "Give me a random number between 1 and 10"
Copilot: [calls generate_random_number with min=1, max=10] "Generated random number: 7"

用户: "给我一个 1 到 10 之间的随机数"
Copilot: [调用 generate_random_number，参数 min=1, max=10] "生成的随机数: 7"
```

---

## ⚙️ Configuration / 配置

### Enable Tools / 启用工具

In Valves configuration:
在 Valves 配置中：

```
ENABLE_TOOLS: true
AVAILABLE_TOOLS: all
```

### Select Specific Tools / 选择特定工具

Instead of enabling all tools, specify which ones to use:
不启用所有工具，而是指定要使用的工具：

```
ENABLE_TOOLS: true
AVAILABLE_TOOLS: generate_random_number
```

---

## 🔧 How Tool Calling Works / 工具调用的工作原理

```
1. User asks a question / 用户提问
        ↓
2. Copilot decides if it needs a tool / Copilot 决定是否需要工具
        ↓
3. If yes, Copilot calls the appropriate tool / 如果需要，调用相应工具
        ↓
4. Tool executes and returns result / 工具执行并返回结果
        ↓
5. Copilot uses the result to answer / Copilot 使用结果回答
```

### Visual Feedback / 可视化反馈

When tools are called, you'll see:
当工具被调用时，你会看到：

```
🔧 **Calling tool**: `generate_random_number`
✅ **Tool `generate_random_number` completed**

Generated random number: 7
```

---

## 📚 Creating Your Own Tools / 创建自定义工具

Want to add your own Python tools? Follow this pattern (module-level tools):
想要添加自己的 Python 工具？遵循这个模式（模块级工具）：

```python
from pydantic import BaseModel, Field
from copilot import define_tool

class MyToolParams(BaseModel):
    param_name: str = Field(description="Parameter description")


@define_tool(description="Clear description of what the tool does and when to use it")
async def my_tool(params: MyToolParams) -> str:
    # Do something
    result = do_something(params.param_name)
    return f"Result: {result}"
```

Then register it in `_initialize_custom_tools()`:
然后将它添加到 `_initialize_custom_tools()`:

```python
def _initialize_custom_tools(self):
    if not self.valves.ENABLE_TOOLS:
        return []

    all_tools = {
        "generate_random_number": generate_random_number,
        "my_tool": my_tool,  # ✅ Add here
    }

    if self.valves.AVAILABLE_TOOLS == "all":
        return list(all_tools.values())

    enabled = [t.strip() for t in self.valves.AVAILABLE_TOOLS.split(",")]
    return [all_tools[name] for name in enabled if name in all_tools]
```

---

## ⚠️ Important Notes / 重要说明

### Security / 安全性

- Tools run in the same process as the pipe
- Be careful with tools that execute code or access files
- Always validate input parameters

- 工具在与 Pipe 相同的进程中运行
- 谨慎处理执行代码或访问文件的工具
- 始终验证输入参数

### Performance / 性能

- Tool execution is synchronous during streaming
- Long-running tools may cause delays
- Consider adding timeouts for external API calls

- 工具执行在流式传输期间是同步的
- 长时间运行的工具可能导致延迟
- 考虑为外部 API 调用添加超时

### Debugging / 调试

- Enable `DEBUG: true` to see tool events in the browser console
- Check tool calls in `🔧 Calling tool` messages
- Tool errors are displayed in the response

- 启用 `DEBUG: true` 在浏览器控制台查看工具事件
- 在 `🔧 Calling tool` 消息中检查工具调用
- 工具错误会显示在响应中

---

**Version:** 0.3.1
**Last Updated:** 2026-02-05
