# Copilot Plan Mode Prompt Parity

> Discovered: 2026-03-06

## Context

The GitHub Copilot SDK pipe builds system prompts in two paths:

- fresh session creation via `_build_session_config(...)`
- resumed session injection via the `system_parts` rebuild branch

Plan Mode guidance was duplicated across those branches.

## Finding

If Plan Mode instructions are edited in only one branch, resumed sessions silently lose planning behavior or capability hints that fresh sessions still have.

This is especially easy to miss because both branches still work, but resumed chats receive a weaker or stale prompt.

Session mode switching alone is also not enough. Even when `session.rpc.mode.set(Mode.PLAN)` succeeds, the SDK may still skip creating the expected `plan.md` if the runtime system prompt does not explicitly include the original Plan Mode persistence contract.

## Solution / Pattern

Extract the Plan Mode prompt into one shared helper and call it from both branches:

```python
def _build_plan_mode_context(plan_path: str) -> str:
    ...
```

Then inject it in both places with the chat-specific `plan.md` path.

For extra safety, when the pipe later reads `session.rpc.plan.read()`, mirror the returned content into the chat-specific `COPILOTSDK_CONFIG_DIR/session-state/<chat_id>/plan.md` path. This keeps the UI-visible file in sync even if the SDK persists plan state internally but does not materialize the file where the chat integration expects it.

## Gotchas

- Keep the helper dynamic: the `plan.md` path must still be resolved per chat/session.
- Do not only update debug prompt artifacts; the effective runtime prompt lives in `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py`.
- Resume-session parity matters for capability guidance just as much as for session context.
- If users report that Plan Mode is active but `plan.md` is missing, check both halves: prompt parity and the final `rpc.plan.read()` -> `plan.md` sync path.
