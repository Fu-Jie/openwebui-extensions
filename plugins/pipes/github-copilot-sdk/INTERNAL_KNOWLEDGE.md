# GitHub Copilot SDK Pipe - Internal Architecture & Knowledge

This document details the core runtime mechanisms, file layout, and deep integration logic of the GitHub Copilot SDK plugin within the OpenWebUI environment.

## 1. Core Environmental Context

### 1.1 Filesystem Layout

| Path | Description | Permissions |
| :--- | :--- | :--- |
| `/app/backend` | OpenWebUI backend Python source code | Read-Only |
| `/app/build` | OpenWebUI frontend assets (Artifacts renderer location) | Read-Only |
| `/root/.copilot/` | SDK core configuration and state storage | **Full Control** |
| `/app/backend/data/copilot_workspace/` | Plugin-specific persistent workspace | **Read/Write** |

### 1.2 Identity Mapping Mechanism

* **Session ID Binding**: The plugin strictly maps OpenWebUI's `Chat ID` to the Copilot SDK's `Session ID`.
* **Outcome**: Every chat session has its own isolated physical directory: `/root/.copilot/session-state/{chat_id}/`.

## 2. TODO List Persistence (TODO Intelligence)

### 2.1 Data Source

TODO data is **not** stored in a standalone database table for basic operations but is captured from the session event stream via the `update_todo` tool:

* **Storage File**: `/root/.copilot/session-state/{chat_id}/events.jsonl`
* **Detection**: Scans for the latest `tool.execution_complete` event where `toolName` is `update_todo`.

### 2.2 Data Format (NDJSON)

```json
{
  "type": "tool.execution_complete",
  "data": {
    "toolName": "update_todo",
    "result": { 
      "detailedContent": "TODO List content...", 
      "toolTelemetry": { "metrics": { "total_items": 3 } } 
    }
  }
}
```

## 3. Toolchain Integration

The plugin harmonizes three distinct tool systems:

1. **Copilot Native**: Built-in capabilities like `bash`, `edit`, and `task`.
2. **OpenWebUI Ecosystem**: Dynamically mounts local Python tools and built-in `Web Search` via `get_tools`.
3. **MCP (Model Context Protocol)**: External capability extensions via servers like `GDMap` or `Pandoc`.

## 4. Security & Permissions

### 4.1 Admin Mode (God Mode)

When `__user__['role'] == 'admin'`:

* `ADMIN_EXTENSIONS` are enabled.
* Access to `DATABASE_URL` via environment variables is permitted.
* `bash` can be used to diagnose internal state within `/root/.copilot/`.

### 4.2 Regular User Mode

* `USER_RESTRICTIONS` are strictly enforced.
* Probing environment variables or database credentials is prohibited.
* `bash` activity is strictly confined to the isolated workspace.

## 5. Common Maintenance

* **Reset Session**: Delete the `/root/.copilot/session-state/{chat_id}` directory.
* **Clear Cache**: Disable `ENABLE_TOOL_CACHE` in Valves.
* **View Logs**: Check latest logs under `/root/.copilot/logs/`.

## 6. Rendering Semantics: Artifacts vs Rich UI (Authoritative Notes)

### 6.1 Artifacts

* **Definition**: Content/code-driven interactive preview rendered from message output (HTML/SVG/code artifacts).
* **Primary references**:
  * `../docs/docs/features/chat-conversations/chat-features/code-execution/artifacts.md`
  * `../open-webui/src/lib/components/chat/Artifacts.svelte`
* **Best fit**:
  * Fast visual preview tied to generated content itself.
  * Lower coupling to tool return contracts.

### 6.2 Rich UI

* **Definition**: Tool/Action-returned embedded UI (typically `HTMLResponse` or embed payload) rendered as a sandboxed iframe and persisted with the conversation.
* **Primary references**:
  * `../docs/docs/features/extensibility/plugin/development/rich-ui.mdx`
  * `../docs/docs/features/extensibility/plugin/tools/development.mdx`
  * `../docs/docs/features/extensibility/plugin/development/events.mdx`
  * `../open-webui/backend/open_webui/utils/actions.py`
* **Best fit**:
  * App-like, stateful, persistent visual blocks.
  * Deterministic tool/action output contracts.

### 6.3 Rich UI vs Execute Event

* **Rich UI**: sandboxed iframe + persistent visual block in chat history.
* **`execute` event**: main-page context, not sandboxed, suitable for transient interactions (dialogs, quick actions, page-state reads), not persistent UI products.

### 6.4 Security and UX Constraints

* Rich UI iframe is sandboxed by default.
* With same-origin off (default), embeds should report height via `postMessage({ type: 'iframe:height', ... })`.
* Enabling same-origin improves interoperability but increases security exposure.
* Sandboxed download behavior can be limited (notably iOS); provide explicit preview/download links as fallback.

### 6.5 Product Direction Heuristics

1. Always use dual delivery: visual output + durable download link.
2. Prefer Rich UI for persistent app-like views; fallback to Artifacts/links when capability limits apply.
3. Make persistence explicit (publish/store), avoid relying on transient UI state.
4. Keep user-visible mode hints and structured status logs for debuggability.
