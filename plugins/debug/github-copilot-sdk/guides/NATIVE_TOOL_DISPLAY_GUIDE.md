# OpenWebUI Native Tool Call Display Implementation Guide

**Date:** 2026-01-27  
**Purpose:** Analyze and implement OpenWebUI's native tool call display mechanism

---

## 📸 Current vs Native Display

### Current Implementation

```markdown
> 🔧 **Running Tool**: `search_chats`

> ✅ **Tool Completed**: {...}
```

### OpenWebUI Native Display (from screenshot)

- ✅ Collapsible panel: "查看来自 search_chats 的结果"
- ✅ Formatted JSON display
- ✅ Syntax highlighting
- ✅ Expand/collapse functionality
- ✅ Clean visual separation

---

## 🔍 Understanding OpenWebUI's Tool Call Format

### Standard OpenAI Tool Call Message Format

OpenWebUI follows the OpenAI Chat Completion API format for tool calls:

#### 1. Assistant Message with Tool Calls

```python
{
    "role": "assistant",
    "content": None,  # or explanatory text
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

#### 2. Tool Response Message

```python
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "name": "search_chats",  # Optional but recommended
    "content": '{"count": 5, "results": [...]}'  # JSON string
}
```

---

## 🎯 Implementation Strategy for Native Display

### Option 1: Event Emitter Approach (Recommended)

Use OpenWebUI's event emitter to send structured tool call data:

```python
async def stream_response(self, ...):
    # When tool execution starts
    if event_type == "tool.execution_start":
        await self._emit_tool_call_start(
            emitter=__event_call__,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            arguments=arguments
        )
    
    # When tool execution completes
    elif event_type == "tool.execution_complete":
        await self._emit_tool_call_result(
            emitter=__event_call__,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            result=result_content
        )
```

#### Helper Methods

```python
async def _emit_tool_call_start(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    tool_call_id: str,
    tool_name: str,
    arguments: dict
):
    """Emit a tool call start event to OpenWebUI."""
    if not emitter:
        return
    
    try:
        # OpenWebUI expects tool_calls in assistant message format
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
        logger.error(f"Failed to emit tool call start: {e}")

async def _emit_tool_call_result(
    self,
    emitter: Optional[Callable[[Any], Awaitable[None]]],
    tool_call_id: str,
    tool_name: str,
    result: Any
):
    """Emit a tool call result to OpenWebUI."""
    if not emitter:
        return
    
    try:
        # Format result as JSON string
        if isinstance(result, str):
            result_content = result
        else:
            result_content = json.dumps(result, ensure_ascii=False, indent=2)
        
        # OpenWebUI expects tool results in tool message format
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
        logger.error(f"Failed to emit tool result: {e}")
```

### Option 2: Message History Injection

Modify the conversation history to include tool calls:

```python
# After tool execution, append to messages
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

## ⚠️ Challenges with Current Architecture

### 1. Streaming Context

Our current implementation uses:

- **Queue-based streaming**: Events → Queue → Yield chunks
- **Text chunks only**: We yield plain text, not structured messages

OpenWebUI's native display requires:

- **Structured message events**: Not text chunks
- **Message-level control**: Need to emit complete messages

### 2. Event Emitter Compatibility

**Current usage:**

```python
# We use event_emitter for status/notifications
await event_emitter({
    "type": "status",
    "data": {"description": "Processing..."}
})
```

**Need for tool calls:**

```python
# Need to emit message-type events
await event_emitter({
    "type": "message",
    "data": {
        "role": "tool",
        "content": "..."
    }
})
```

**Question:** Does `__event_emitter__` support `message` type events?

### 3. Session SDK Events vs OpenWebUI Messages

**Copilot SDK events:**

- `tool.execution_start` → We get tool name, arguments
- `tool.execution_complete` → We get tool result
- Designed for streaming text output

**OpenWebUI messages:**

- Expect structured message objects
- Not designed for mid-stream injection

---

## 🧪 Experimental Implementation

### Step 1: Add Valve for Native Display

```python
class Valves(BaseModel):
    USE_NATIVE_TOOL_DISPLAY: bool = Field(
        default=False,
        description="Use OpenWebUI's native tool call display instead of markdown formatting"
    )
```

### Step 2: Modify Tool Event Handling

```python
async def stream_response(self, ...):
    # ...existing code...
    
    def handler(event):
        event_type = get_event_type(event)
        
        if event_type == "tool.execution_start":
            tool_name = safe_get_data_attr(event, "name")
            
            # Get tool arguments
            tool_input = safe_get_data_attr(event, "input") or {}
            tool_call_id = safe_get_data_attr(event, "tool_call_id", f"call_{time.time()}")
            
            if tool_call_id:
                active_tools[tool_call_id] = {
                    "name": tool_name,
                    "arguments": tool_input
                }
            
            if self.valves.USE_NATIVE_TOOL_DISPLAY:
                # Emit structured tool call
                asyncio.create_task(
                    self._emit_tool_call_start(
                        __event_call__,
                        tool_call_id,
                        tool_name,
                        tool_input
                    )
                )
            else:
                # Current markdown display
                queue.put_nowait(f"\n\n> 🔧 **Running Tool**: `{tool_name}`\n\n")
        
        elif event_type == "tool.execution_complete":
            tool_call_id = safe_get_data_attr(event, "tool_call_id")
            tool_info = active_tools.get(tool_call_id, {})
            tool_name = tool_info.get("name", "Unknown")
            
            # Extract result
            result_obj = safe_get_data_attr(event, "result")
            result_content = ""
            if hasattr(result_obj, "content"):
                result_content = result_obj.content
            elif isinstance(result_obj, dict):
                result_content = result_obj.get("content", "")
            
            if self.valves.USE_NATIVE_TOOL_DISPLAY:
                # Emit structured tool result
                asyncio.create_task(
                    self._emit_tool_call_result(
                        __event_call__,
                        tool_call_id,
                        tool_name,
                        result_content
                    )
                )
            else:
                # Current markdown display
                queue.put_nowait(f"> ✅ **Tool Completed**: {result_content}\n\n")
```

---

## 🔬 Testing Plan

### Test 1: Event Emitter Message Type Support

```python
# In a test conversation, try:
await __event_emitter__({
    "type": "message",
    "data": {
        "role": "assistant",
        "content": "Test message"
    }
})
```

**Expected:** Message appears in chat  
**If fails:** Event emitter doesn't support message type

### Test 2: Tool Call Message Format

```python
# Send a tool call message
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

# Send tool result
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

**Expected:** OpenWebUI displays collapsible tool panel  
**If fails:** Event format doesn't match OpenWebUI expectations

### Test 3: Mid-Stream Tool Call Injection

Test if tool call messages can be injected during streaming:

```python
# Start streaming text
yield "Processing your request..."

# Mid-stream: emit tool call
await __event_emitter__({"type": "message", "data": {...}})

# Continue streaming
yield "Done!"
```

**Expected:** Tool panel appears mid-response  
**Risk:** May break streaming flow

---

## 📋 Implementation Checklist

- [x] Add `REASONING_EFFORT` valve (completed)
- [ ] Add `USE_NATIVE_TOOL_DISPLAY` valve
- [ ] Implement `_emit_tool_call_start()` helper
- [ ] Implement `_emit_tool_call_result()` helper
- [ ] Modify tool event handling in `stream_response()`
- [ ] Test event emitter message type support
- [ ] Test tool call message format
- [ ] Test mid-stream injection
- [ ] Update documentation
- [ ] Add user configuration guide

---

## 🤔 Recommendation

### Hybrid Approach (Safest)

Keep both display modes:

1. **Default (Current):** Markdown-based display
   - ✅ Works reliably with streaming
   - ✅ No OpenWebUI API dependencies
   - ✅ Consistent across versions

2. **Experimental (Native):** Structured tool messages
   - ✅ Better visual integration
   - ⚠️ Requires testing with OpenWebUI internals
   - ⚠️ May not work in all scenarios

**Configuration:**

```python
USE_NATIVE_TOOL_DISPLAY: bool = Field(
    default=False,
    description="[EXPERIMENTAL] Use OpenWebUI's native tool call display"
)
```

### Why Markdown Display is Currently Better

1. **Reliability:** Always works with streaming
2. **Flexibility:** Can customize format easily
3. **Context:** Shows tools inline with reasoning
4. **Compatibility:** Works across OpenWebUI versions

### When to Use Native Display

- Non-streaming mode (easier to inject messages)
- After confirming event emitter supports message type
- For tools with large JSON results (better formatting)

---

## 📚 Next Steps

1. **Research OpenWebUI Source Code**
   - Check `__event_emitter__` implementation
   - Verify supported event types
   - Test message injection patterns

2. **Create Proof of Concept**
   - Simple test plugin
   - Emit tool call messages
   - Verify UI rendering

3. **Document Findings**
   - Update this guide with test results
   - Add code examples that work
   - Create migration guide if successful

---

## 🔗 References

- [OpenAI Chat Completion API](https://platform.openai.com/docs/api-reference/chat/create)
- [OpenWebUI Plugin Development](https://docs.openwebui.com/)
- [Copilot SDK Events](https://github.com/github/copilot-sdk)

---

**Author:** Fu-Jie  
**Status:** Analysis Complete - Implementation Pending Testing
