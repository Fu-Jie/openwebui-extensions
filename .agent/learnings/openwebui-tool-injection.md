# OpenWebUI Tool Parameter Injection

> Discovered: 2026-03-05

## Context

When OpenWebUI loads a Python Tool and calls one of its functions (e.g. `generate_mind_map`),
it automatically matches parameters from an `extra_params` dict against the function's
signature **by name**. This is done in:

```
open_webui/utils/tools.py → get_async_tool_function_and_apply_extra_params()
```

The lookup is: `extra_params = {k: v for k, v in extra_params.items() if k in sig.parameters}`

## Finding

A Tool function declares its dependencies via its parameter names. Common injected names:

| Parameter Name        | What it contains                                  |
|-----------------------|---------------------------------------------------|
| `__user__`            | User context dict (id, email, role, name)         |
| `__event_emitter__`   | Async callable to emit status/notification events |
| `__event_call__`      | Async callable for JS `__event_call__` roundtrips |
| `__request__`         | Request-like object (must have `.app.state.MODELS`) |
| `__metadata__`        | Dict: `{model, base_model_id, chat_id, ...}`      |
| `__messages__`        | Full conversation history list                    |
| `__chat_id__`         | Current chat UUID                                 |
| `__message_id__`      | Current message UUID                              |
| `__session_id__`      | Current session UUID                              |
| `__files__`           | Files attached to the current message             |
| `__task__`            | Task type string (e.g. `title_generation`)        |
| `body`                | Raw request body dict (non-dunder variant)        |
| `request`             | Request object (non-dunder variant)               |

## Key Rule

**`extra_params` must contain ALL keys a Tool's function signature declares.**
If a key is missing from `extra_params`, the parameter silently receives its default
value (e.g. `{}` for `__metadata__`). This means the Tool appears to work but
gets empty/wrong context.

## Solution / Pattern

When a Pipe calls an OpenWebUI Tool, it must populate `extra_params` with **all** the above:

```python
extra_params = {
    "__request__": request,      # Must have app.state.MODELS populated!
    "request": request,          # Non-dunder alias
    "__user__": user_data,
    "__event_emitter__": __event_emitter__,
    "__event_call__": __event_call__,
    "__messages__": messages,
    "__metadata__": __metadata__ or {},
    "__chat_id__": chat_id,
    "__message_id__": message_id,
    "__session_id__": session_id,
    "__files__": files,
    "__task__": task,
    "__task_body__": task_body,
    "body": body,                # Non-dunder alias
    ...
}
```

## Model Resolution

Tools that call `generate_chat_completion` internally need a **valid model ID**.
When the conversation is running under a Pipe/Manifold model (e.g. `github_copilot.gpt-4o`),
the Tool's `valves.MODEL_ID` must be a *real* model known to the system.

`generate_chat_completion` validates model IDs against `request.app.state.MODELS`.
➡️  That dict **must be populated** from the database (see `openwebui-mock-request.md`).

## Gotchas

- Tools call `generate_chat_completion` with a `request` arg that must be the full Mock Request.
- If `app.state.MODELS` is empty, even a correctly-spelled model ID will cause "Model not found".
- `__metadata__['model']` can be a **dict** (from DB) **or a string** (manifold ID). Tools must
  handle both types.
- For manifold models not in the DB, strip the prefix: `github_copilot.gpt-4o` → `gpt-4o`.
