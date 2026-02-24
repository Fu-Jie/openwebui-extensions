# OpenWebUI Plugin Development Guide

> This guide consolidates official documentation, SDK details, and best practices to provide a systematic tutorial for developers, from beginner to expert.

## 📚 Table of Contents

1. [Quick Start](#1-quick-start)
2. [Core Concepts & SDK Details](#2-core-concepts--sdk-details)
3. [Deep Dive into Plugin Types](#3-deep-dive-into-plugin-types)
    * [Action](#31-action)
    * [Filter](#32-filter)
    * [Pipe](#33-pipe)
4. [Advanced Development Patterns](#4-advanced-development-patterns)
5. [Best Practices & Design Principles](#5-best-practices--design-principles)
6. [Repository Standards (openwebui-extensions)](#6-repository-standards-openwebui-extensions)
7. [Custom Agent Design Recommendations](#7-custom-agent-design-recommendations)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Quick Start

### 1.1 What are OpenWebUI Plugins?

OpenWebUI Plugins (officially called "Functions") are the primary way to extend the platform's capabilities. Running in a backend Python environment, they allow you to:

* 🔌 **Integrate New Models**: Connect to Claude, Gemini, or custom RAGs via Pipes.
* 🎨 **Enhance Interaction**: Add buttons (e.g., "Export", "Generate Chart") next to messages via Actions.
* 🔧 **Intervene in Processes**: modify data before requests or after responses (e.g., inject context, filter sensitive words) via Filters.

### 1.2 Your First Plugin (Hello World)

Save the following code as `hello.py` and upload it to the **Functions** panel in OpenWebUI:

```python
"""
title: Hello World Action
author: Demo
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional

class Action:
    class Valves(BaseModel):
        greeting: str = Field(default="Hello", description="Greeting message")

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __event_emitter__=None,
        __user__=None
    ) -> Optional[dict]:
        user_name = __user__.get("name", "Friend") if __user__ else "Friend"
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "notification",
                "data": {"type": "success", "content": f"{self.valves.greeting}, {user_name}!"}
            })
        return body
```

---

## 2. Core Concepts & SDK Details

### 2.1 ⚠️ Important: Sync vs Async

OpenWebUI plugins run within an `asyncio` event loop.

* **Principle**: All I/O operations (database, file, network) must be non-blocking.
* **Pitfall**: Calling synchronous methods directly (e.g., `time.sleep`, `requests.get`) will freeze the entire server.
* **Solution**: Wrap synchronous calls using `await asyncio.to_thread(sync_func, ...)`.

### 2.2 Core Parameters

All plugin methods (`inlet`, `outlet`, `pipe`, `action`) support injecting the following special parameters:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `body` | `dict` | **Core Data**. Contains request info like `messages`, `model`, `stream`. |
| `__user__` | `dict` | **Current User**. Contains `id`, `name`, `role`, `valves` (user config), etc. |
| `__metadata__` | `dict` | **Metadata**. Contains `chat_id`, `message_id`. The `variables` field holds preset variables like `{{USER_NAME}}`, `{{CURRENT_TIME}}`. |
| `__request__` | `Request` | **FastAPI Request Object**. Access `app.state` for cross-plugin communication. |
| `__event_emitter__` | `func` | **One-way Notification**. Used to send Toast notifications or status bar updates. |
| `__event_call__` | `func` | **Two-way Interaction**. Used to execute JS code, show confirmation dialogs, or input boxes on the frontend. |

### 2.3 Configuration System (Valves)

* **`Valves`**: Global admin configuration.
* **`UserValves`**: User-level configuration (higher priority, overrides global).

```python
class Filter:
    class Valves(BaseModel):
        API_KEY: str = Field(default="", description="Global API Key")
        
    class UserValves(BaseModel):
        API_KEY: str = Field(default="", description="User Private API Key")
        
    def inlet(self, body, __user__):
        # Prioritize user's Key
        user_valves = __user__.get("valves", self.UserValves())
        api_key = user_valves.API_KEY or self.valves.API_KEY
```

---

## 3. Deep Dive into Plugin Types

### 3.1 Action

**Role**: Adds buttons below messages that trigger upon user click.

#### Advanced Usage: Execute JavaScript on Frontend (File Download Example)

```python
import base64

async def action(self, body, __event_call__):
    # 1. Generate content on backend
    content = "Hello OpenWebUI".encode()
    b64 = base64.b64encode(content).decode()
    
    # 2. Send JS to frontend for execution
    js = f"""
    const blob = new Blob([atob('{b64}')], {{type: 'text/plain'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'hello.txt';
    a.click();
    """
    await __event_call__({"type": "execute", "data": {"code": js}})
```

### 3.2 Filter

**Role**: Middleware that intercepts and modifies requests/responses.

* **`inlet`**: Before request. Used for injecting context, modifying model parameters.
* **`outlet`**: After response. Used for formatting output, logging.
* **`stream`**: During streaming. Used for real-time sensitive word filtering.

#### Example: Injecting Environment Variables

```python
async def inlet(self, body, __metadata__):
    vars = __metadata__.get("variables", {})
    context = f"Current Time: {vars.get('{{CURRENT_DATETIME}}')}"
    
    # Inject into System Prompt or first message
    if body.get("messages"):
        body["messages"][0]["content"] += f"\n\n{context}"
    return body
```

### 3.3 Pipe

**Role**: Custom Model/Agent.

#### Example: Simple OpenAI Wrapper

```python
import requests

class Pipe:
    def pipes(self):
        return [{"id": "my-gpt", "name": "My GPT Wrapper"}]

    def pipe(self, body):
        # Modify body here, e.g., force add prompt
        headers = {"Authorization": f"Bearer {self.valves.API_KEY}"}
        r = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, stream=True)
        return r.iter_lines()
```

---

## 4. Advanced Development Patterns

### 4.1 Pipe & Filter Collaboration

Use `__request__.app.state` to share data between plugins.

* **Pipe**: `__request__.app.state.search_results = [...]`
* **Filter (Outlet)**: Read `search_results` and format them as citation links appended to the response.

### 4.2 Async Background Tasks

Execute time-consuming operations (e.g., summarization, database storage) in the background without blocking the user response.

```python
import asyncio

async def outlet(self, body, __metadata__):
    asyncio.create_task(self.background_job(__metadata__["chat_id"]))
    return body

async def background_job(self, chat_id):
    # Execute time-consuming operation...
    pass
```

---

## 5. Best Practices & Design Principles

### 5.1 Naming & Positioning

* **Short & Punchy**: e.g., "FlashCard", "DeepRead". Avoid generic terms like "Text Analysis Assistant".
* **Complementary**: Don't reinvent the wheel; clarify what specific problem your plugin solves.

### 5.2 User Experience (UX)

* **Timely Feedback**: Send a `notification` ("Generating...") before time-consuming operations.
* **Visual Appeal**: When Action outputs HTML, use modern CSS (rounded corners, shadows, gradients).
* **Smart Guidance**: If text is too short, prompt the user: "Suggest entering more content for better results".

### 5.3 Error Handling

Never let a plugin fail silently. Catch exceptions and inform the user via `__event_emitter__`.

```python
try:
    # Business logic
except Exception as e:
    await __event_emitter__({
        "type": "notification",
        "data": {"type": "error", "content": f"Processing failed: {str(e)}"}
    })
```

---

## 6. Repository Standards (openwebui-extensions)

### 6.1 Single-file i18n Requirement

In this repository, each plugin must use a **single source file** with built-in i18n logic. Do not split source code by language.

* Required pattern: `plugins/{type}/{name}/{name}.py`
* Required docs: `README.md` + `README_CN.md`

### 6.2 Safe Context Access (Required)

Prefer helper methods like `_get_user_context` and `_get_chat_context` instead of direct, fragile field access from `__user__` / `body`.

### 6.3 Event and Logging Conventions

* Use status/notification events for user-visible progress.
* Use frontend console debug logs (`execute`) for live debugging during development.
* Use Python `logging` for backend logs; avoid `print()` in production plugin code.

### 6.4 Frontend Language Detection and Timeout Guard

When reading frontend language via `__event_call__`, always use:

* JS `try...catch` fallback return
* backend `asyncio.wait_for(..., timeout=2.0)`

This prevents deadlocks when frontend execution fails.

### 6.5 Copilot SDK Tool Definition

For custom Copilot SDK tools, define explicit parameter schema using a `pydantic.BaseModel` and pass it with `params_type` in `define_tool(...)`.

### 6.6 Copilot SDK Streaming Output Format

* Use native `<think>...</think>` for reasoning output.
* Ensure `</think>` is closed before normal content or tool cards.
* For tool result cards, use native `<details type="tool_calls" ...>` format.
* Escape attribute quotes in `arguments` and `result` as `&quot;`.

### 6.7 Source-derived Production Patterns (Recommended)

The following patterns are extracted from `github_copilot_sdk.py` and `workspace_file_manager.py`:

* **Tool parameter anti-drift**: define tools with `params_type=BaseModel`, and execute with `model_dump(exclude_unset=True)` so missing params do not become explicit `None`.
* **Tool name normalization**: enforce `^[a-zA-Z0-9_-]+$`; if non-ASCII names collapse, use an `md5` suffix fallback to keep registration stable.
* **Workspace sandboxing**: resolve and verify every path stays inside the workspace root to prevent traversal.
* **3-step file delivery**: local write -> `publish_file_from_workspace` -> return `/api/v1/files/{id}/content`, with `skip_rag=true` metadata.
* **Dual upload channel**: prefer API upload (S3-compatible), fallback to DB + local copy.
* **Streaming stability**: close `<think>` before emitting `assistant.message_delta` content.
* **Native tool cards**: emit `<details type="tool_calls">` on `tool.execution_complete` with strict HTML escaping (`&quot;`, newline escaping).
* **TODO persistence linkage**: on successful `update_todo`, sync both `TODO.md` and database state.

### 6.8 Full Source-derived Knowledge Base (from `plugins/`)

The following is a broader extraction from `actions/`, `filters/`, `pipes/`, `pipelines/`, and `tools/`:

* **Action input hygiene**: normalize multimodal message content, strip old plugin HTML blocks (`OPENWEBUI_PLUGIN_OUTPUT`), and enforce minimum text length before expensive model calls.
* **Action i18n hardening**: use `TRANSLATIONS + fallback_map + base-lang fallback` (`fr-CA -> fr-FR`, `en-GB -> en-US`), keep all status/UI/JS strings in i18n keys, and protect `format(**kwargs)` formatting.
* **Frontend language detection (production-safe)**: use priority chain `document.lang -> localStorage(locale/language) -> navigator.language -> profile/request`, and always wrap `__event_call__(execute)` with timeout.
* **Long-running UX pattern**: emit immediate `status + notification`, report staged progress (`analyzing/rendering/saving`), and keep detailed exception data in backend logs.
* **HTML plugin composability**: use insertion markers for style/content/script, support both overwrite (`CLEAR_PREVIOUS_HTML`) and merge mode, and keep wrappers deterministic.
* **Theme-aware iframe rendering**: detect theme from parent meta/class/data-theme with system fallback, and inject theme-aware colors for SVG/PNG export.
* **Client-side render-and-export pipeline**: render offscreen chart/mindmap, export SVG/PNG, upload via `/api/v1/files/`, and persist updates through event API + chat persistence API.
* **DOCX export production patterns**: apply `TITLE_SOURCE` fallback chain (`chat_title -> markdown_title -> user+date`), remove reasoning blocks, convert LaTeX via `latex2mathml + mathml2omml`, and emit citation-aware references/bookmarks.
* **OpenWebUI file retrieval fallback ladder**: DB inline bytes/base64 -> S3 direct read -> local path variants -> public URL -> internal `/api/v1/files/{id}/content` -> raw object attrs, with max-byte guards at every stage.
* **Filter singleton-safe design**: never store request-scoped mutable state on `self`; compute per-request values from `body` and context helpers.
* **Async context compression patterns**: two-phase flow (`inlet` apply summary, `outlet` async generate summary), model-level threshold overrides, fast estimate + precise count near limit, and system-message protection (`effective_keep_first`).
* **Model compatibility guardrails**: skip incompatible model families (e.g., `copilot_sdk` paths) and avoid hardcoded default model IDs.
* **Folder memory pattern**: trigger periodic rule extraction (`every N messages`), replace rules idempotently using block markers (`RULES_BLOCK_START/END`), and optionally update root folder.
* **Tool workspace hardening**: all file APIs (`list/read/write/delete/publish`) must re-check sandbox boundary, enforce size limits, and return user-ready download hints.
* **MoE prompt refiner pattern (pipeline)**: detect aggregation prompts via trigger prefix, parse original query + segmented responses, then rewrite to synthesis-oriented master prompt with optional aggregation model reroute.

### 6.9 Copilot-related Engineering Configuration

To support plugin engineering with **GitHub Copilot + Gemini CLI + antigravity mode**, adopt these controls:

* **Primary/secondary assistant lanes**: Copilot is primary implementation lane; Gemini CLI is secondary draft/verification lane.
* **Single merge contract**: both lanes must pass the same repository constraints (single-file i18n, context helpers, event conventions, release workflow rules).
* **Tool schema discipline**: all Copilot SDK tools use explicit `params_type` with Pydantic models.
* **Antigravity safety**: small reversible edits, timeout guards, fallback routing, and deterministic file/output paths.
* **File creation protocol**: write in workspace scope, publish via workspace publish flow, return `/api/v1/files/{id}/content` for delivery.

Detailed design document:

* `docs/development/copilot-engineering-plan.md`

---

## 7. Custom Agent Design Recommendations

### 7.1 Suggested architecture (for this repo)

* **Orchestrator Pipe**: session lifecycle, model routing, streaming events.
* **Tool Adapter Layer**: unify OpenWebUI Tools / OpenAPI / MCP with param validation and name normalization.
* **Workspace I/O Layer**: sandboxed file operations + publish pipeline.
* **Render Layer**: `<think>` lifecycle, tool cards, status/notification events.

### 7.2 MVP checklist

1. Dual config model: `Valves + UserValves` (user overrides first).
2. Unified context helpers: `_get_user_context` / `_get_chat_context`.
3. At least one artifact-delivery tool (e.g., `publish_file_from_workspace`).
4. Minimal streaming loop: `reasoning_delta`, `message_delta`, `tool.execution_complete`.
5. Unified error reporting via notification events.

### 7.3 Three high-impact agents you can build now

* **Repo Analyst Agent**: output architecture map, risk list, and refactor proposals.
* **Release Draft Agent**: generate Conventional Commit title/body + bilingual release summary.
* **Docs Sync Agent**: compare source/doc versions and output a concrete sync file list.

### 7.4 Implementation priority

* **P0**: Release Draft Agent (highest ROI, lowest risk).
* **P1**: Docs Sync Agent (reduces doc drift).
* **P2**: Repo Analyst Agent (medium/long-term evolution).

---

## 8. Troubleshooting

* **HTML not showing?** Ensure it's wrapped in a ` ```html ... ``` ` code block.
* **Database error?** Check if you called synchronous DB methods directly in an `async` function; use `asyncio.to_thread`.
* **Parameters not working?** Check if `Valves` are defined correctly and if they are being overridden by `UserValves`.
