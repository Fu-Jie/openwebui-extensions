# 🔗 Chat Session Mapping Filter

| By [Fu-Jie](https://github.com/Fu-Jie) · v0.1.0 | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

Automatically tracks and persists the mapping between user IDs and chat IDs for seamless session management.

## Install with Batch Install Plugins

If you already use [Batch Install Plugins from GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins), you can install or update this plugin with:

```text
Install plugin from Fu-Jie/openwebui-extensions
```

When the selection dialog opens, search for this plugin, check it, and continue.

> [!IMPORTANT]
> If the official OpenWebUI Community version is already installed, remove it first. After that, Batch Install Plugins can keep this plugin updated in future runs.

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
