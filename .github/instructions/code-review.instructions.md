---
name: Plugin Code Review
description: Comprehensive OpenWebUI plugin review checklist covering i18n, context helpers, antigravity safety, and streaming compatibility
applyTo: "plugins/**/*.py"
---
# Code Review Instructions — OpenWebUI Plugins

You are an expert Senior Software Engineer reviewing OpenWebUI plugins for the `openwebui-extensions` repository.
When reviewing plugin code, you MUST verify each point below to ensure the code meets the strict repository standards.

## 1. Single-file i18n Pattern (CRITICAL)
- **One File Rule**: One `.py` file per plugin. No `_cn.py` or language-split files.
- **Translations**: All user-visible strings (status, notification, UI text) MUST go through a `TRANSLATIONS` dictionary and a `FALLBACK_MAP`.
- **Safety**: `format(**kwargs)` calls on translated strings MUST be wrapped in `try/except KeyError` to prevent crashes if a translation is missing a placeholder.

## 2. Context Helpers (CRITICAL)
- **User Context**: MUST use `_get_user_context(__user__)` instead of direct `__user__["name"]` access. `__user__` can be a list, dict, or None.
- **Chat Context**: MUST use `_get_chat_context(body, __metadata__)` instead of ad-hoc `body.get("chat_id")` calls.

## 3. Event & Logging
- **No Print**: No bare `print()` in production code. Use `logging.getLogger(__name__)`.
- **Emitter Safety**: Every `await emitter(...)` call MUST be guarded by `if emitter:` (or equivalent).
- **Status Lifecycle**: 
  - `_emit_status(done=False)` at task start.
  - `_emit_status(done=True)` on completion.
  - `_emit_notification("error")` on failure.

## 4. Antigravity Safety (CRITICAL)
- **Timeout Guards**: All `__event_call__` JS executions MUST be wrapped with `asyncio.wait_for(..., timeout=2.0)`. Failure to do this can hang the entire backend.
- **JS Fallbacks**: JS code executed via `__event_call__` MUST have an internal `try { ... } catch (e) { return fallback; }` block.
- **Path Sandboxing**: File path operations MUST be validated against the workspace root (no directory traversal vulnerabilities).
- **Upload Fallbacks**: Upload paths MUST have a dual-channel fallback (API → local/DB).

## 5. Filter Singleton Safety
- **No Mutable State**: Filter plugins are singletons. There MUST be NO request-scoped mutable state stored on `self` (e.g., `self.current_user = ...`).
- **Statelessness**: Per-request values MUST be computed from `body` and context helpers on each call.

## 6. Copilot SDK Tools
- **Pydantic Models**: Tool parameters MUST be defined as a `pydantic.BaseModel` subclass.
- **Explicit Params**: `define_tool(...)` MUST include `params_type=MyParams`.
- **Naming**: Tool names MUST match `^[a-zA-Z0-9_-]+$` (ASCII only).

## 7. Streaming Compatibility (OpenWebUI 0.8.x)
- **Thinking Tags**: The `</think>` tag MUST be closed before any normal content or tool cards are emitted.
- **Attribute Escaping**: Tool card `arguments` and `result` attributes MUST escape `"` as `&quot;`.
- **Newline Requirement**: The `<details type="tool_calls" ...>` block MUST be followed by a newline immediately after `>`.

## 8. Performance & Memory
- **Streaming**: Large files or responses MUST be streamed, not loaded entirely into memory.
- **Database Connections**: Plugins MUST reuse the OpenWebUI internal database connection (`owui_engine`, `owui_Session`) rather than creating new ones.

## 9. HTML Injection (Action Plugins)
- **Wrapper Template**: HTML output MUST use the standard `<!-- OPENWEBUI_PLUGIN_OUTPUT -->` wrapper.
- **Idempotency**: The plugin MUST implement `_remove_existing_html` to ensure multiple runs do not duplicate the HTML output.
