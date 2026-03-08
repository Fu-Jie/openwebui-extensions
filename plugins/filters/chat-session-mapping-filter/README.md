# 🔗 Chat Session Mapping Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 0.1.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

Automatically tracks and persists the mapping between user IDs and chat IDs for seamless session management.

## Key Features

🔄 **Automatic Tracking** - Captures user_id and chat_id on every message without manual intervention  
💾 **Persistent Storage** - Saves mappings to JSON file for session recovery and analytics  
🛡️ **Atomic Operations** - Uses temporary file writes to prevent data corruption  
⚙️ **Configurable** - Enable/disable tracking via Valves setting  
🔍 **Smart Context Extraction** - Safely extracts IDs from multiple source locations (body, metadata, __metadata__)

## How to Use

1. **Install the filter** - Add it to your OpenWebUI plugins
2. **Enable globally** - No configuration needed; tracking is enabled by default
3. **Monitor mappings** - Check `copilot_workspace/api_key_chat_id_mapping.json` for stored mappings

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ENABLE_TRACKING` | `true` | Master switch for chat session mapping tracking |

## How It Works

This filter intercepts messages at the **inlet** stage (before processing) and:

1. **Extracts IDs**: Safely gets user_id from `__user__` and chat_id from `body`/`metadata`
2. **Validates**: Confirms both IDs are non-empty before proceeding
3. **Persists**: Writes or updates the mapping in a JSON file with atomic file operations
4. **Handles Errors**: Gracefully logs warnings if any step fails, without blocking the chat flow

### Storage Location

- **Container Environment** (`/app/backend/data` exists):  
  `/app/backend/data/copilot_workspace/api_key_chat_id_mapping.json`

- **Local Development** (no `/app/backend/data`):  
  `./copilot_workspace/api_key_chat_id_mapping.json`

### File Format

Stored as a JSON object with user IDs as keys and chat IDs as values:

```json
{
  "user-1": "chat-abc-123",
  "user-2": "chat-def-456",
  "user-3": "chat-ghi-789"
}
```

## Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## Technical Notes

- **No Response Modification**: The outlet hook returns the response unchanged
- **Atomic Writes**: Prevents partial writes using `.tmp` intermediate files
- **Context-Aware ID Extraction**: Handles `__user__` as dict/list/None and metadata from multiple sources
- **Logging**: All operations are logged for debugging; enable verbose logging with `SHOW_DEBUG_LOG` in dependent plugins
