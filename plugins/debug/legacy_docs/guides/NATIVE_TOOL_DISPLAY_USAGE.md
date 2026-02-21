# Native Tool Display Usage Guide

## 🎨 What is Native Tool Display?

Native Tool Display is an experimental feature that integrates with OpenWebUI's built-in tool call visualization system. When enabled, tool calls and their results are displayed in **collapsible JSON panels** instead of plain markdown text.

### Visual Comparison

**Traditional Display (markdown):**

```
> 🔧 Running Tool: `get_current_time`
> ✅ Tool Completed: 2026-01-27 10:30:00
```

**Native Display (collapsible panels):**

- Tool call appears in a collapsible `assistant.tool_calls` panel
- Tool result appears in a separate collapsible `tool.content` panel
- JSON syntax highlighting for better readability
- Compact by default, expandable on click

## 🚀 How to Enable

1. Open the GitHub Copilot SDK Pipe configuration (Valves)
2. Set `USE_NATIVE_TOOL_DISPLAY` to `true`
3. Save the configuration
4. Start a new conversation with tool calls

## 📋 Requirements

- OpenWebUI with native tool display support
- `__event_emitter__` must support `message` type events
- Tool-enabled models (e.g., GPT-4, Claude Sonnet)

## ⚙️ How It Works

### OpenAI Standard Format

The native display uses the OpenAI standard message format:

**Tool Call (Assistant Message):**

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "get_current_time",
        "arguments": "{\"timezone\":\"UTC\"}"
      }
    }
  ]
}
```

**Tool Result (Tool Message):**

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "2026-01-27 10:30:00 UTC"
}
```

### Message Flow

1. **Tool Execution Start**:
   - SDK emits `tool.execution_start` event
   - Plugin sends `assistant` message with `tool_calls` array
   - OpenWebUI displays collapsible tool call panel

2. **Tool Execution Complete**:
   - SDK emits `tool.execution_complete` event
   - Plugin sends `tool` message with `tool_call_id` and `content`
   - OpenWebUI displays collapsible result panel

## 🔧 Troubleshooting

### Panel Not Showing

**Symptoms:** Tool calls still appear as markdown text

**Possible Causes:**

1. `__event_emitter__` doesn't support `message` type events
2. OpenWebUI version too old
3. Feature not enabled (`USE_NATIVE_TOOL_DISPLAY = false`)

**Solution:**

- Enable DEBUG mode to see error messages in browser console
- Check browser console for "Native message emission failed" warnings
- Update OpenWebUI to latest version
- Keep `USE_NATIVE_TOOL_DISPLAY = false` to use traditional markdown display

### Duplicate Tool Information

**Symptoms:** Tool calls appear in both native panels and markdown

**Cause:** Mixed display modes

**Solution:**

- Ensure `USE_NATIVE_TOOL_DISPLAY` is either `true` (native only) or `false` (markdown only)
- Restart the conversation after changing this setting

## 🧪 Experimental Status

This feature is marked as **EXPERIMENTAL** because:

1. **Event Emitter API**: The `__event_emitter__` support for `message` type events is not fully documented
2. **OpenWebUI Version Dependency**: Requires recent versions of OpenWebUI with native tool display support
3. **Streaming Architecture**: May have compatibility issues with streaming responses

### Fallback Behavior

If native message emission fails:

- Plugin automatically falls back to markdown display
- Error logged to browser console (when DEBUG is enabled)
- No interruption to conversation flow

## 📊 Performance Considerations

Native display has slightly better performance characteristics:

| Aspect | Native Display | Markdown Display |
|--------|----------------|------------------|
| **Rendering** | Native UI components | Markdown parser |
| **Interactivity** | Collapsible panels | Static text |
| **JSON Parsing** | Handled by UI | Not formatted |
| **Token Usage** | Minimal overhead | Formatting tokens |

## 🔮 Future Enhancements

Planned improvements for native tool display:

- [ ] Automatic fallback detection
- [ ] Tool call history persistence
- [ ] Rich metadata display (execution time, arguments preview)
- [ ] Copy tool call JSON button
- [ ] Tool call replay functionality

## 💡 Best Practices

1. **Enable DEBUG First**: Test with DEBUG mode before using in production
2. **Monitor Browser Console**: Check for warning messages during tool calls
3. **Test with Simple Tools**: Verify with built-in tools before custom implementations
4. **Keep Fallback Option**: Don't rely solely on native display until it exits experimental status

## 📖 Related Documentation

- [TOOLS_USAGE.md](TOOLS_USAGE.md) - How to create and use custom tools
- [NATIVE_TOOL_DISPLAY_GUIDE.md](NATIVE_TOOL_DISPLAY_GUIDE.md) - Technical implementation details
- [WORKFLOW.md](WORKFLOW.md) - Complete integration workflow

## 🐛 Reporting Issues

If you encounter issues with native tool display:

1. Enable `DEBUG` and `USE_NATIVE_TOOL_DISPLAY`
2. Open browser console (F12)
3. Trigger a tool call
4. Copy any error messages
5. Report to [GitHub Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

Include:

- OpenWebUI version
- Browser and version
- Error messages from console
- Steps to reproduce

---

**Author:** Fu-Jie | **Version:** 0.2.0 | **License:** MIT
