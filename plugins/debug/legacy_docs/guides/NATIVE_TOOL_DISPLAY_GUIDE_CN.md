# OpenWebUI 原生工具调用展示实现指南

**日期：** 2026-01-27  
**目的：** 分析并实现 OpenWebUI 的原生工具调用展示机制

---

## 📸 当前展示 vs 原生展示

### 当前实现

```markdown
> 🔧 **Running Tool**: `search_chats`

> ✅ **Tool Completed**: {...}
```

### OpenWebUI 原生展示（来自截图）

- ✅ 可折叠面板："查看来自 search_chats 的结果"
- ✅ 格式化的 JSON 显示
- ✅ 语法高亮
- ✅ 展开/折叠功能
- ✅ 清晰的视觉分隔

---

## 🔍 理解 OpenWebUI 的工具调用格式

### 标准 OpenAI 工具调用消息格式

OpenWebUI 遵循 OpenAI Chat Completion API 的工具调用格式：

#### 1. 带工具调用的助手消息

```python
{
    "role": "assistant",
    "content": None,  # 或解释性文本
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "search_chats",
                "arguments": '{"query": ""}'
            }
        }
    ]
}
```

#### 2. 工具响应消息

```python
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "name": "search_chats",  # 可选但推荐
    "content": '{"count": 5, "results": [...]}'  # JSON 字符串
}
```

---

## 🎯 原生展示的实现策略

### 方案 1：事件发射器方法（推荐）

使用 OpenWebUI 的事件发射器发送结构化工具调用数据：

```python
async def stream_response(self, ...):
    # 工具执行开始时
    if event_type == "tool.execution_start":
        await self._emit_tool_call_start(
            emitter=__event_call__,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=arguments
        )
    
    # 工具执行完成时
    elif event_type == "tool.execution_complete":
        await self._emit_tool_call_result(
            emitter=__event_call__,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            result=result_content
        )
```

#### 辅助方法

```python
async def _emit_tool_call_start(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    tool_call_id: str,
    tool_name: str,
    arguments: dict
):
    """向 OpenWebUI 发射工具调用开始事件。"""
    if not emitter:
        return
    
    try:
        # OpenWebUI 期望 assistant 消息格式的 tool_calls
        await emitter({
            "type": "message",
            "data": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(arguments, ensure_ascii=False)
                        }
                    }
                ]
            }
        })
    except Exception as e:
        logger.error(f"发射工具调用开始事件失败: {e}")

async def _emit_tool_call_result(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    tool_call_id: str,
    tool_name: str,
    result: Any
):
    """向 OpenWebUI 发射工具调用结果。"""
    if not emitter:
        return
    
    try:
        # 将结果格式化为 JSON 字符串
        if isinstance(result, str):
            result_content = result
        else:
            result_content = json.dumps(result, ensure_ascii=False, indent=2)
        
        # OpenWebUI 期望 tool 消息格式的工具结果
        await emitter({
            "type": "message",
            "data": {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": result_content
            }
        })
    except Exception as e:
        logger.error(f"发射工具结果失败: {e}")
```

### 方案 2：消息历史注入

修改对话历史以包含工具调用：

```python
# 工具执行后，追加到消息中
messages.append({
    "role": "assistant",
    "content": None,
    "tool_calls": [{
        "id": tool_call_id,
        "type": "function",
        "function": {
            "name": tool_name,
            "arguments": json.dumps(arguments)
        }
    }]
})

messages.append({
    "role": "tool",
    "tool_call_id": tool_call_id,
    "name": tool_name,
    "content": json.dumps(result)
})
```

---

## ⚠️ 当前架构的挑战

### 1. 流式上下文

我们当前的实现使用：

- **基于队列的流式传输**：事件 → 队列 → 产出块
- **仅文本块**：我们产出纯文本，而非结构化消息

OpenWebUI 的原生展示需要：

- **结构化消息事件**：不是文本块
- **消息级别控制**：需要发射完整消息

### 2. 事件发射器兼容性

**当前用法：**

```python
# 我们使用 event_emitter 发送状态/通知
await event_emitter({
    "type": "status",
    "data": {"description": "处理中..."}
})
```

**工具调用所需：**

```python
# 需要发射 message 类型事件
await event_emitter({
    "type": "message",
    "data": {
        "role": "tool",
        "content": "..."
    }
})
```

**问题：** `__event_emitter__` 是否支持 `message` 类型事件？

### 3. Session SDK 事件 vs OpenWebUI 消息

**Copilot SDK 事件：**

- `tool.execution_start` → 获取工具名称、参数
- `tool.execution_complete` → 获取工具结果
- 为流式文本输出设计

**OpenWebUI 消息：**

- 期望结构化消息对象
- 不为中间流注入设计

---

## 🧪 实验性实现

### 步骤 1：添加原生展示 Valve

```python
class Valves(BaseModel):
    USE_NATIVE_TOOL_DISPLAY: bool = Field(
        default=False,
        description="使用 OpenWebUI 的原生工具调用展示，而非 Markdown 格式"
    )
```

### 步骤 2：修改工具事件处理

```python
async def stream_response(self, ...):
    # ...现有代码...
    
    def handler(event):
        event_type = get_event_type(event)
        
        if event_type == "tool.execution_start":
            tool_name = safe_get_data_attr(event, "name")
            
            # 获取工具参数
            tool_input = safe_get_data_attr(event, "input") or {}
            tool_call_id = safe_get_data_attr(event, "tool_call_id", f"call_{time.time()}")
            
            if tool_call_id:
                active_tools[tool_call_id] = {
                    "name": tool_name,
                    "arguments": tool_input
                }
            
            if self.valves.USE_NATIVE_TOOL_DISPLAY:
                # 发射结构化工具调用
                asyncio.create_task(
                    self._emit_tool_call_start(
                        __event_call__,
                        tool_call_id,
                        tool_name,
                        tool_input
                    )
                )
            else:
                # 当前 Markdown 展示
                queue.put_nowait(f"\n\n> 🔧 **运行工具**: `{tool_name}`\n\n")
        
        elif event_type == "tool.execution_complete":
            tool_call_id = safe_get_data_attr(event, "tool_call_id")
            tool_info = active_tools.get(tool_call_id, {})
            tool_name = tool_info.get("name", "未知")
            
            # 提取结果
            result_obj = safe_get_data_attr(event, "result")
            result_content = ""
            if hasattr(result_obj, "content"):
                result_content = result_obj.content
            elif isinstance(result_obj, dict):
                result_content = result_obj.get("content", "")
            
            if self.valves.USE_NATIVE_TOOL_DISPLAY:
                # 发射结构化工具结果
                asyncio.create_task(
                    self._emit_tool_call_result(
                        __event_call__,
                        tool_call_id,
                        tool_name,
                        result_content
                    )
                )
            else:
                # 当前 Markdown 展示
                queue.put_nowait(f"> ✅ **工具完成**: {result_content}\n\n")
```

---

## 🔬 测试计划

### 测试 1：事件发射器消息类型支持

```python
# 在测试对话中尝试：
await __event_emitter__({
    "type": "message",
    "data": {
        "role": "assistant",
        "content": "测试消息"
    }
})
```

**预期：** 消息出现在聊天中  
**如果失败：** 事件发射器不支持 message 类型

### 测试 2：工具调用消息格式

```python
# 发送工具调用消息
await __event_emitter__({
    "type": "message",
    "data": {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "test_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{"param": "value"}'
            }
        }]
    }
})

# 发送工具结果
await __event_emitter__({
    "type": "message",
    "data": {
        "role": "tool",
        "tool_call_id": "test_123",
        "name": "test_tool",
        "content": '{"result": "success"}'
    }
})
```

**预期：** OpenWebUI 显示可折叠工具面板  
**如果失败：** 事件格式与 OpenWebUI 期望不符

### 测试 3：中间流工具调用注入

测试是否可以在流式传输期间注入工具调用消息：

```python
# 开始流式文本
yield "正在处理您的请求..."

# 中间流：发射工具调用
await __event_emitter__({"type": "message", "data": {...}})

# 继续流式传输
yield "完成！"
```

**预期：** 工具面板出现在响应中间  
**风险：** 可能破坏流式传输流程

---

## 📋 实施检查清单

- [x] 添加 `REASONING_EFFORT` valve（已完成）
- [ ] 添加 `USE_NATIVE_TOOL_DISPLAY` valve
- [ ] 实现 `_emit_tool_call_start()` 辅助方法
- [ ] 实现 `_emit_tool_call_result()` 辅助方法
- [ ] 修改 `stream_response()` 中的工具事件处理
- [ ] 测试事件发射器消息类型支持
- [ ] 测试工具调用消息格式
- [ ] 测试中间流注入
- [ ] 更新文档
- [ ] 添加用户配置指南

---

## 🤔 建议

### 混合方法（最安全）

保留两种展示模式：

1. **默认（当前）：** 基于 Markdown 的展示
   - ✅ 与流式传输可靠工作
   - ✅ 无 OpenWebUI API 依赖
   - ✅ 跨版本一致

2. **实验性（原生）：** 结构化工具消息
   - ✅ 更好的视觉集成
   - ⚠️ 需要测试 OpenWebUI 内部
   - ⚠️ 可能不适用于所有场景

**配置：**

```python
USE_NATIVE_TOOL_DISPLAY: bool = Field(
    default=False,
    description="[实验性] 使用 OpenWebUI 的原生工具调用展示"
)
```

### 为什么 Markdown 展示目前更好

1. **可靠性：** 始终与流式传输兼容
2. **灵活性：** 可以轻松自定义格式
3. **上下文：** 与推理内联显示工具
4. **兼容性：** 跨 OpenWebUI 版本工作

### 何时使用原生展示

- 非流式模式（更容易注入消息）
- 确认事件发射器支持 message 类型后
- 对于具有大型 JSON 结果的工具（更好的格式化）

---

## 📚 后续步骤

1. **研究 OpenWebUI 源代码**
   - 检查 `__event_emitter__` 实现
   - 验证支持的事件类型
   - 测试消息注入模式

2. **创建概念验证**
   - 简单测试插件
   - 发射工具调用消息
   - 验证 UI 渲染

3. **记录发现**
   - 使用测试结果更新本指南
   - 添加有效的代码示例
   - 如果成功，创建迁移指南

---

## 🔗 参考资料

- [OpenAI Chat Completion API](https://platform.openai.com/docs/api-reference/chat/create)
- [OpenWebUI 插件开发](https://docs.openwebui.com/)
- [Copilot SDK 事件](https://github.com/github/copilot-sdk)

---

**作者：** Fu-Jie  
**状态：** 分析完成 - 实施等待测试
