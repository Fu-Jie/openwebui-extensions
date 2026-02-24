# OpenWebUI Plugin Development Guide

> This guide consolidates official documentation, SDK details, and best practices to provide a systematic tutorial for developers, from beginner to expert.

---

## 📚 Table of Contents

1. [Quick Start](#1-quick-start)
2. [Project Structure & Naming](#2-project-structure--naming)
3. [Core Concepts & SDK Details](#3-core-concepts--sdk-details)
4. [Deep Dive into Plugin Types](#4-deep-dive-into-plugin-types)
5. [Advanced Development Patterns](#5-advanced-development-patterns)
6. [Best Practices & Design Principles](#6-best-practices--design-principles)
7. [Workflow & Process](#7-workflow--process)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Quick Start

### 1.1 What are OpenWebUI Plugins?

OpenWebUI Plugins (officially called "Functions") are the primary way to extend the platform's capabilities. Running in a backend Python environment, they allow you to:

- :material-power-plug: **Integrate New Models**: Connect to Claude, Gemini, or custom RAGs via Pipes
- :material-palette: **Enhance Interaction**: Add buttons (e.g., "Export", "Generate Chart") next to messages via Actions
- :material-cog: **Intervene in Processes**: Modify data before requests or after responses via Filters

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

## 2. Project Structure & Naming

### 2.1 Language & Code Requirements

- **Single Code File**: `plugins/{type}/{name}/{name}.py`. Never create separate source files for different languages.
- **Built-in i18n**: Must dynamically switch UI, prompts, and logs based on user language.
- **Documentation**: Must include both `README.md` (English) and `README_CN.md` (Chinese).

### 2.2 Docstring Standard

Each plugin file must start with a standardized docstring:

```python
"""
title: Plugin Name
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.0
icon_url: data:image/svg+xml;base64,<base64-encoded-svg>
requirements: dependency1==1.0.0, dependency2>=2.0.0
description: Brief description of plugin functionality.
"""
```

- **icon_url**: Required for Action plugins. Must be Base64 encoded SVG from [Lucide Icons](https://lucide.dev/icons/).
- **requirements**: Only list dependencies not installed in the OpenWebUI environment.

---

## 3. Core Concepts & SDK Details

### 3.1 ⚠️ Important: Sync vs Async

OpenWebUI plugins run within an `asyncio` event loop.

!!! warning "Critical"
    - **Principle**: All I/O operations (database, file, network) must be non-blocking
    - **Pitfall**: Calling synchronous methods directly (e.g., `time.sleep`, `requests.get`) will freeze the entire server
    - **Solution**: Wrap synchronous calls using `await asyncio.to_thread(sync_func, ...)`

### 3.2 Core Parameters

All plugin methods (`inlet`, `outlet`, `pipe`, `action`) support injecting the following special parameters:

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `body` | `dict` | **Core Data**. Contains request info like `messages`, `model`, `stream` |
| `__user__` | `dict` | **Current User**. Contains `id`, `name`, `role`, `valves` (user config), etc. |
| `__metadata__` | `dict` | **Metadata**. Contains `chat_id`, `message_id`. The `variables` field holds preset variables |
| `__request__` | `Request` | **FastAPI Request Object**. Access `app.state` for cross-plugin communication |
| `__event_emitter__` | `func` | **One-way Notification**. Used to send Toast notifications or status bar updates |
| `__event_call__` | `func` | **Two-way Interaction**. Used to execute JS code, show confirmation dialogs, or input boxes |

### 3.3 Configuration System (Valves)

Use Pydantic BaseModel to define configurable parameters. All Valves fields must use **UPPER_SNAKE_CASE**.

```python
from pydantic import BaseModel, Field

class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(default=True, description="Whether to show operation status updates.")
        # ...
```

### 3.4 Context Access

All plugins **must** use `_get_user_context` and `_get_chat_context` methods to safely extract information, rather than accessing `__user__` or `body` directly.

### 3.5 Event Emission & Logging

- **Event Emission**: Implement helper methods `_emit_status` and `_emit_notification`.
- **Frontend Console Debugging**: Highly recommended for real-time data flow viewing. Use `_emit_debug_log` to print structured debug logs in the browser console.
- **Server-side Logging**: Use Python's standard `logging` module. Do not use `print()`.

### 3.6 Database & File Storage

- **Database**: Re-use Open WebUI's internal database connection (`open_webui.internal.db`).
- **File Storage**: Implement multi-level fallback mechanisms (DB -> S3 -> Local -> URL -> API) to ensure compatibility across all storage configurations.

### 3.7 Internationalization (i18n)

Define a `TRANSLATIONS` dictionary and use a robust language detection mechanism (Multi-level Fallback: JS localStorage -> HTTP Accept-Language -> User Profile -> en-US).

---

## 4. Deep Dive into Plugin Types

### 4.1 Action

**Role**: Adds buttons below messages that trigger upon user click.

#### Advanced Usage: Execute JavaScript on Frontend

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

### 4.2 Filter

**Role**: Middleware that intercepts and modifies requests/responses.

- **`inlet`**: Before request. Used for injecting context, modifying model parameters
- **`outlet`**: After response. Used for formatting output, logging
- **`stream`**: During streaming. Used for real-time sensitive word filtering

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

### 4.3 Pipe

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
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers=headers,
            stream=True
        )
        return r.iter_lines()
```

### 4.4 Copilot SDK Tool Definition Standards

When developing custom tools for GitHub Copilot SDK, you **must** define a Pydantic `BaseModel` for parameters and explicitly reference it using `params_type` in `define_tool`.

### 4.5 Copilot SDK Streaming & Tool Card Standards

- **Reasoning Streaming**: Must use native `<think>` tags and ensure proper closure (`\n</think>\n`) before outputting main content or tool calls.
- **Native Tool Calls Block**: Output strictly formatted HTML `<details type="tool_calls"...>` blocks. Ensure all double quotes in attributes are escaped as `&quot;`.

---

## 5. Advanced Development Patterns

### 5.1 Pipe & Filter Collaboration

Use `__request__.app.state` to share data between plugins:

- **Pipe**: `__request__.app.state.search_results = [...]`
- **Filter (Outlet)**: Read `search_results` and format them as citation links

### 5.2 Async Background Tasks

Execute time-consuming operations without blocking the user response:

```python
import asyncio

async def outlet(self, body, __metadata__):
    asyncio.create_task(self.background_job(__metadata__["chat_id"]))
    return body

async def background_job(self, chat_id):
    # Execute time-consuming operation...
    pass
```

### 5.3 Calling Built-in LLM

```python
from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

# Get user object
user_obj = Users.get_user_by_id(user_id)

# Build LLM request
llm_payload = {
    "model": "model-id",
    "messages": [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User input"}
    ],
    "temperature": 0.7,
    "stream": False
}

# Call LLM
llm_response = await generate_chat_completion(
    __request__, llm_payload, user_obj
)
```

### 5.4 JS Render to Markdown (Data URL Embedding)

For scenarios requiring complex frontend rendering (e.g., AntV charts, Mermaid diagrams) but wanting **persistent pure Markdown output**, use the Data URL embedding pattern:

#### Workflow

```text
┌──────────────────────────────────────────────────────────────┐
│  1. Python Action                                             │
│     ├── Analyze message content                               │
│     ├── Call LLM to generate structured data (optional)       │
│     └── Send JS code to frontend via __event_call__           │
├──────────────────────────────────────────────────────────────┤
│  2. Browser JS (via __event_call__)                           │
│     ├── Dynamically load visualization library                │
│     ├── Render SVG/Canvas offscreen                           │
│     ├── Export to Base64 Data URL via toDataURL()             │
│     └── Update message content via REST API                   │
├──────────────────────────────────────────────────────────────┤
│  3. Markdown Rendering                                        │
│     └── Display ![description](data:image/svg+xml;base64,...) │
└──────────────────────────────────────────────────────────────┘
```

### 5.5 Agent File Delivery Standards (3-Step Delivery Protocol)

1. **Write Local**: Create files in the current execution directory (`.`).
2. **Publish**: Call `publish_file_from_workspace(filename='name.ext')`.
3. **Display Link**: Present the returned `download_url` as a Markdown link.

---

## 6. Best Practices & Design Principles

### 6.1 Naming & Positioning

- **Short & Punchy**: e.g., "FlashCard", "DeepRead". Avoid generic terms like "Text Analysis Assistant"
- **Complementary**: Don't reinvent the wheel; clarify what specific problem your plugin solves

### 6.2 User Experience (UX)

- **Timely Feedback**: Send a `notification` ("Generating...") before time-consuming operations
- **Visual Appeal**: When Action outputs HTML, use modern CSS (rounded corners, shadows, gradients)
- **Smart Guidance**: If text is too short, prompt the user: "Suggest entering more content for better results"

### 6.3 Error Handling

!!! danger "Never fail silently"
    Always catch exceptions and inform the user via `__event_emitter__`.

```python
try:
    # Business logic
    pass
except Exception as e:
    await __event_emitter__({
        "type": "notification",
        "data": {"type": "error", "content": f"Processing failed: {str(e)}"}
    })
```

### 6.4 Long-running Task Notifications

If a foreground task is expected to take more than 3 seconds, implement a user notification mechanism (e.g., sending a notification every 5 seconds).

---

## 7. Workflow & Process

### 7.1 Source-derived Knowledge (from `plugins/`)

- **Input/context safety**: normalize multimodal text extraction, use `_get_user_context` / `_get_chat_context`, and protect frontend language detection with timeout guards.
- **Long task UX**: emit immediate `status/notification`, then staged progress updates; keep full exception detail in backend logs.
- **HTML merge strategy**: use stable wrapper markers (`OPENWEBUI_PLUGIN_OUTPUT`) and support both overwrite and merge modes.
- **Theme consistency**: detect parent/system theme and apply theme-aware rendering/export styles for iframe-based outputs.
- **Render-export-persist loop**: offscreen render (SVG/PNG) -> upload `/api/v1/files/` -> event update + persistence update to avoid refresh loss.
- **DOCX production path**: `TITLE_SOURCE` fallback naming, reasoning-block stripping, native Word math (`latex2mathml + mathml2omml`), and citation/reference anchoring.
- **File retrieval fallback chain**: DB inline -> S3 direct -> local path variants -> public URL -> internal API -> raw fields, with max-byte guards on each stage.
- **Filter singleton discipline**: do not store request-scoped mutable state on `self`; compute from request context each run.
- **Async compression pattern**: `inlet` summary injection + `outlet` background summary generation, with model-threshold override and system-message protection.
- **Workspace/tool hardening**: explicit `params_type` schemas, strict path-boundary validation, and publish flow returning `/api/v1/files/{id}/content` with `skip_rag=true` metadata.
- **MoE refinement pipeline**: detect aggregation prompts, parse segmented responses, and rewrite to synthesis-oriented master prompt with optional reroute model.

### 7.2 Copilot Engineering Configuration

- For repository-wide AI-assisted engineering setup (GitHub Copilot + Gemini CLI + antigravity mode), follow `docs/development/copilot-engineering-plan.md`.
- This plan defines the shared contract for tool parameter schema/routing, file creation/publish protocol, rollback-safe delivery patterns, and streaming/tool-card compatibility.

- **Consistency Maintenance**: Any addition, modification, or removal of a plugin must simultaneously update the plugin code, READMEs, project docs, doc indexes, and the root README.
- **Release Workflow**: Pushing to `main` triggers automatic release. Ensure version numbers are updated and follow SemVer. Use Conventional Commits.

---

## 8. Troubleshooting

??? question "HTML not showing?"
    Ensure it's wrapped in a ` ```html ... ``` ` code block.

??? question "Database error?"
    Check if you called synchronous DB methods directly in an `async` function; use `asyncio.to_thread`.

??? question "Parameters not working?"
    Check if `Valves` are defined correctly and if they are being overridden by `UserValves`.

??? question "Plugin not loading?"
    - Check for syntax errors in the Python file
    - Verify the metadata docstring is correctly formatted
    - Check OpenWebUI logs for error messages

---

## Additional Resources

- [:fontawesome-brands-github: Plugin Examples](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins)
- [:material-book-open-variant: OpenWebUI Official Docs](https://docs.openwebui.com/)
- [:material-forum: Community Discussions](https://github.com/open-webui/open-webui/discussions)
