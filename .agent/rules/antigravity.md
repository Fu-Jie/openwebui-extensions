---
description: >
  Antigravity development mode rules. Apply when the user requests high-speed iteration,
  a quick prototype, or says "反重力开发" / "antigravity mode".
globs: "plugins/**/*.py"
always_on: false
---
# Antigravity Development Mode

> High-speed delivery + strict reversibility. Every decision must keep both roll-forward and rollback feasible.

---

## Core Principles

1. **Small, isolated edits** — one logical change per operation; no mixing refactor + feature.
2. **Deterministic interfaces** — function signatures and return shapes must not change without an explicit contract update.
3. **Multi-level fallback** — every I/O path has a degraded alternative (e.g., S3 → local → DB).
4. **Reversible by default** — every file write, API call, or schema change must have an undo path recorded or be idempotent.

---

## Mandatory Safety Patterns

### 1. Timeout Guards on All Frontend Calls

Any `__event_call__` or `__event_emitter__` JS execution MUST be wrapped:

```python
import asyncio

try:
    result = await asyncio.wait_for(
        __event_call__({"type": "execute", "data": {"code": js_code}}),
        timeout=2.0
    )
except asyncio.TimeoutError:
    logger.warning("Frontend JS execution timed out; falling back.")
    result = fallback_value
except Exception as e:
    logger.error(f"Frontend call failed: {e}", exc_info=True)
    result = fallback_value
```

JS side must also guard internally:

```javascript
try {
    return (localStorage.getItem('locale') || navigator.language || 'en-US');
} catch (e) {
    return 'en-US';
}
```

### 2. Path Sandbox Validation

Resolve every workspace path and verify it stays inside the repo root:

```python
import os

def _validate_workspace_path(path: str, workspace_root: str) -> str:
    resolved = os.path.realpath(os.path.abspath(path))
    root = os.path.realpath(workspace_root)
    if not resolved.startswith(root + os.sep) and resolved != root:
        raise PermissionError(f"Path escape detected: {resolved} is outside {root}")
    return resolved
```

### 3. Dual-Channel Upload Fallback

Always try API first; fall back to DB/local on failure:

```python
async def _upload_file(self, filename: str, content: bytes) -> str:
    # Channel 1: API upload (S3-compatible)
    try:
        url = await self._api_upload(filename, content)
        if url:
            return url
    except Exception as e:
        logger.warning(f"API upload failed: {e}; falling back to local.")

    # Channel 2: Local file + DB registration
    return await self._local_db_upload(filename, content)
```

### 4. Progressive Status Reporting

For tasks > 3 seconds, emit staged updates:

```python
await self._emit_status(emitter, "正在分析内容...", done=False)
# ... phase 1 ...
await self._emit_status(emitter, "正在生成输出...", done=False)
# ... phase 2 ...
await self._emit_status(emitter, "完成", done=True)
```

Always emit `done=True` on completion and `notification(error)` on failure.

### 5. Emitter Guard

Check before every emit to prevent crashes on missing emitter:

```python
if emitter and self.valves.SHOW_STATUS:
    await emitter({"type": "status", "data": {"description": msg, "done": done}})
```

### 6. Exception Surface Rule

Never swallow exceptions silently. Every `except` block must:

- Log to backend: `logger.error(f"...: {e}", exc_info=True)`
- Notify user: `await self._emit_notification(emitter, f"处理失败: {str(e)}", "error")`

---

## Edit Discipline

| ✅ DO | ❌ DO NOT |
|-------|-----------|
| One function / one Valve / one method per edit | Mix multiple unrelated changes in one operation |
| Validate input at the function boundary | Assume upstream data is well-formed |
| Return early on invalid state | Nest complex logic beyond 3 levels |
| Check fallback availability before primary path | Assume primary path always succeeds |
| Log before and after expensive I/O | Skip logging for "obvious" operations |

---

## Rollback Checklist

Before completing an antigravity operation, confirm:

- [ ] No global state mutated on `self` (filter singleton rule)
- [ ] File writes are atomic or can be recreated
- [ ] Database changes are idempotent (safe to re-run)
- [ ] Timeout guards are in place for all async calls to external systems
- [ ] The user can observe progress through status/notification events

---

## References

- Full engineering spec: `.github/copilot-instructions.md` → Section: **Antigravity Development Mode**
- Design document: `docs/development/copilot-engineering-plan.md` → Section 5
