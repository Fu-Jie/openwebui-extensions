# 🤖 Custom Agents Reference (Copilot SDK Python)

This document explains how to create **custom agent profiles** using the SDK at:

- `/Users/fujie/app/python/oui/copilot-sdk/python`

and apply them in this pipe:

- `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py`

---

## 1) What is a “Custom Agent” here?

In Copilot SDK Python, a custom agent is not a separate runtime class from the SDK itself.
It is typically a **session configuration bundle**:

- model + reasoning level
- system message/persona
- tools exposure
- hooks lifecycle behavior
- user input strategy
- infinite session compaction strategy
- provider (optional BYOK)

So the practical implementation is:

1. Define an `AgentProfile` data structure.
2. Convert profile -> `session_config`.
3. Call `client.create_session(session_config)`.

---

## 2) SDK capabilities you can use

From `copilot-sdk/python/README.md`, the key knobs are:

- `model`
- `reasoning_effort`
- `tools`
- `system_message`
- `streaming`
- `provider`
- `infinite_sessions`
- `on_user_input_request`
- `hooks`

These are enough to create different agent personas without forking core logic.

---

## 3) Recommended architecture in pipe

Use a **profile registry** + a single factory method.

```python
from dataclasses import dataclass
from typing import Any, Callable, Optional

@dataclass
class AgentProfile:
    name: str
    model: str
    reasoning_effort: str = "medium"
    system_message: Optional[str] = None
    enable_tools: bool = True
    enable_openwebui_tools: bool = True
    enable_hooks: bool = False
    enable_user_input: bool = False
    infinite_sessions_enabled: bool = True
    compaction_threshold: float = 0.8
    buffer_exhaustion_threshold: float = 0.95
```

Then map profile -> session config:

```python
def build_session_config(profile: AgentProfile, tools: list, hooks: dict, user_input_handler: Optional[Callable[..., Any]]):
    config = {
        "model": profile.model,
        "reasoning_effort": profile.reasoning_effort,
        "streaming": True,
        "infinite_sessions": {
            "enabled": profile.infinite_sessions_enabled,
            "background_compaction_threshold": profile.compaction_threshold,
            "buffer_exhaustion_threshold": profile.buffer_exhaustion_threshold,
        },
    }

    if profile.system_message:
        config["system_message"] = {"content": profile.system_message}

    if profile.enable_tools:
        config["tools"] = tools

    if profile.enable_hooks and hooks:
        config["hooks"] = hooks

    if profile.enable_user_input and user_input_handler:
        config["on_user_input_request"] = user_input_handler

    return config
```

---

## 4) Example profile presets

```python
AGENT_PROFILES = {
    "builder": AgentProfile(
        name="builder",
        model="claude-sonnet-4.6",
        reasoning_effort="high",
        system_message="You are a precise coding agent. Prefer minimal, verifiable changes.",
        enable_tools=True,
        enable_hooks=True,
    ),
    "analyst": AgentProfile(
        name="analyst",
        model="gpt-5-mini",
        reasoning_effort="medium",
        system_message="You analyze and summarize with clear evidence mapping.",
        enable_tools=False,
        enable_hooks=False,
    ),
    "reviewer": AgentProfile(
        name="reviewer",
        model="claude-sonnet-4.6",
        reasoning_effort="high",
        system_message="Review diffs, identify risks, and propose minimal fixes.",
        enable_tools=True,
        enable_hooks=True,
    ),
}
```

---

## 5) Integrating with this pipe

In `github_copilot_sdk.py`:

1. Add a Valve like `AGENT_PROFILE` (default: `builder`).
2. Resolve profile from registry at runtime.
3. Build `session_config` from profile.
4. Merge existing valve toggles (`ENABLE_TOOLS`, `ENABLE_OPENWEBUI_TOOLS`) as final override.

Priority recommendation:

- explicit runtime override > valve toggle > profile default

This keeps backward compatibility while enabling profile-based behavior.

---

## 6) Hook strategy (safe defaults)

Use hooks only when needed:

- `on_pre_tool_use`: allow/deny tools, sanitize args
- `on_post_tool_use`: add short execution context
- `on_user_prompt_submitted`: normalize unsafe prompt patterns
- `on_error_occurred`: retry/skip/abort policy

Start with no-op hooks, then incrementally enforce policy.

---

## 7) Validation checklist

- Profile can be selected by valve and takes effect.
- Session created with expected model/reasoning.
- Tool availability matches profile + valve overrides.
- Hook handlers run only when enabled.
- Infinite-session compaction settings are applied.
- Fallback to default profile if unknown profile name is provided.

---

## 8) Anti-patterns to avoid

- Hardcoding profile behavior in multiple places.
- Mixing tool registration logic with prompt-format logic.
- Enabling expensive hooks for all profiles by default.
- Coupling profile name to exact model id with no fallback.

---

## 9) Minimal rollout plan

1. Add profile dataclass + registry.
2. Add one valve: `AGENT_PROFILE`.
3. Build session config factory.
4. Keep existing behavior as default profile.
5. Add 2 more profiles (`analyst`, `reviewer`) and test.

---

## 10) SDK gap analysis for current pipe (high-value missing features)

Current pipe already implements many advanced capabilities:

- `SessionConfig` with `tools`, `system_message`, `infinite_sessions`, `provider`, `mcp_servers`
- Session resume/create path
- `list_models()` cache path
- Attachments in `session.send(...)`
- Hook integration (currently `on_post_tool_use`)

Still missing (or partially implemented) high-value SDK features:

### A. `on_user_input_request` handler (ask-user loop)

**Why valuable**
- Enables safe clarification for ambiguous tasks instead of hallucinated assumptions.

**Current state**
- Not wired into `create_session(...)`.

**Implementation idea**
- Add valves:
    - `ENABLE_USER_INPUT_REQUEST: bool`
    - `DEFAULT_USER_INPUT_ANSWER: str`
- Add a handler function and pass:
    - `session_params["on_user_input_request"] = handler`

### B. Full lifecycle hooks (beyond `on_post_tool_use`)

**Why valuable**
- Better policy control and observability.

**Current state**
- Only `on_post_tool_use` implemented.

**Implementation idea**
- Add optional handlers for:
    - `on_pre_tool_use`
    - `on_user_prompt_submitted`
    - `on_session_start`
    - `on_session_end`
    - `on_error_occurred`

### C. Provider type coverage gap (`azure`)

**Why valuable**
- Azure OpenAI users cannot configure provider type natively.

**Current state**
- Valve type only allows `openai | anthropic`.

**Implementation idea**
- Extend valve enum to include `azure`.
- Add `BYOK_AZURE_API_VERSION` valve.
- Build `provider` payload with `azure` block when selected.

### D. Client transport options exposure (`cli_url`, `use_stdio`, `port`)

**Why valuable**
- Enables remote/shared Copilot server and tuning transport mode.

**Current state**
- `_build_client_config` sets `cli_path/cwd/config_dir/log_level/env`, but not transport options.

**Implementation idea**
- Add valves:
    - `COPILOT_CLI_URL`
    - `COPILOT_USE_STDIO`
    - `COPILOT_PORT`
- Conditionally inject into `client_config`.

### E. Foreground session lifecycle APIs

**Why valuable**
- Better multi-session UX and control in TUI/server mode.

**Current state**
- No explicit usage of:
    - `get_foreground_session_id()`
    - `set_foreground_session_id()`
    - `client.on("session.foreground", ...)`

**Implementation idea**
- Optional debug/admin feature only.
- Add event bridge for lifecycle notifications.

---

## 11) Recommended implementation priority

1. `on_user_input_request` (highest value / low risk)
2. Full lifecycle hooks (high value / medium risk)
3. Azure provider support (high value for enterprise users)
4. Client transport valves (`cli_url/use_stdio/port`)
5. Foreground session APIs (optional advanced ops)
