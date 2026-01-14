# OpenWebUI Plugin Development Guide

> This guide consolidates official documentation, SDK details, and best practices to provide a systematic tutorial for developers, from beginner to expert.

---

## 📚 Table of Contents

1. [Quick Start](#1-quick-start)
2. [Core Concepts & SDK Details](#2-core-concepts-sdk-details)
3. [Deep Dive into Plugin Types](#3-deep-dive-into-plugin-types)
4. [Advanced Development Patterns](#4-advanced-development-patterns)
5. [Best Practices & Design Principles](#5-best-practices-design-principles)
6. [Troubleshooting](#6-troubleshooting)

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

## 2. Core Concepts & SDK Details

### 2.1 ⚠️ Important: Sync vs Async

OpenWebUI plugins run within an `asyncio` event loop.

!!! warning "Critical"
    - **Principle**: All I/O operations (database, file, network) must be non-blocking
    - **Pitfall**: Calling synchronous methods directly (e.g., `time.sleep`, `requests.get`) will freeze the entire server
    - **Solution**: Wrap synchronous calls using `await asyncio.to_thread(sync_func, ...)`

### 2.2 Core Parameters

All plugin methods (`inlet`, `outlet`, `pipe`, `action`) support injecting the following special parameters:

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `body` | `dict` | **Core Data**. Contains request info like `messages`, `model`, `stream` |
| `__user__` | `dict` | **Current User**. Contains `id`, `name`, `role`, `valves` (user config), etc. |
| `__metadata__` | `dict` | **Metadata**. Contains `chat_id`, `message_id`. The `variables` field holds preset variables |
| `__request__` | `Request` | **FastAPI Request Object**. Access `app.state` for cross-plugin communication |
| `__event_emitter__` | `func` | **One-way Notification**. Used to send Toast notifications or status bar updates |
| `__event_call__` | `func` | **Two-way Interaction**. Used to execute JS code, show confirmation dialogs, or input boxes |

### 2.3 Configuration System (Valves)

- **`Valves`**: Global admin configuration
- **`UserValves`**: User-level configuration (higher priority, overrides global)

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

### 3.2 Filter

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
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers=headers,
            stream=True
        )
        return r.iter_lines()
```

---

## 4. Advanced Development Patterns

### 4.1 Pipe & Filter Collaboration

Use `__request__.app.state` to share data between plugins:

- **Pipe**: `__request__.app.state.search_results = [...]`
- **Filter (Outlet)**: Read `search_results` and format them as citation links

### 4.2 Async Background Tasks

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

### 4.3 Calling Built-in LLM

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

### 4.4 JS Render to Markdown (Data URL Embedding)

For scenarios requiring complex frontend rendering (e.g., AntV charts, Mermaid diagrams) but wanting **persistent pure Markdown output**, use the Data URL embedding pattern:

#### Workflow

```
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

#### Python Side (Send JS for Execution)

```python
async def action(self, body, __event_call__, __metadata__, ...):
    chat_id = self._extract_chat_id(body, __metadata__)
    message_id = self._extract_message_id(body, __metadata__)
    
    # Generate JS code
    js_code = self._generate_js_code(
        chat_id=chat_id,
        message_id=message_id,
        data=processed_data,
    )
    
    # Execute JS
    if __event_call__:
        await __event_call__({
            "type": "execute",
            "data": {"code": js_code}
        })
```

#### JavaScript Side (Render and Write-back)

```javascript
(async function() {
    // 1. Load visualization library
    if (typeof VisualizationLib === 'undefined') {
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.example.com/lib.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    // 2. Create offscreen container
    const container = document.createElement('div');
    container.style.cssText = 'position:absolute;left:-9999px;';
    document.body.appendChild(container);
    
    // 3. Render visualization
    const instance = new VisualizationLib({ container });
    instance.render(data);
    
    // 4. Export to Data URL
    const dataUrl = await instance.toDataURL({ type: 'svg', embedResources: true });
    
    // 5. Cleanup
    instance.destroy();
    document.body.removeChild(container);
    
    // 6. Generate Markdown image
    const markdownImage = `![Chart](${dataUrl})`;
    
    // 7. Update message via API
    const token = localStorage.getItem("token");
    await fetch(`/api/v1/chats/${chatId}/messages/${messageId}/event`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
            type: "chat:message",
            data: { content: originalContent + "\n\n" + markdownImage }
        })
    });
})();
```

#### Benefits

- **Pure Markdown Output**: Standard Markdown image syntax, no HTML code blocks
- **Self-Contained**: Images embedded as Base64 Data URL, no external dependencies
- **Persistent**: Via API write-back, images remain after page reload
- **Cross-Platform**: Works on any client supporting Markdown images

#### HTML Injection vs JS Render to Markdown

| Feature | HTML Injection | JS Render + Markdown |
|---------|----------------|----------------------|
| Output Format | HTML code block | Markdown image |
| Interactivity | ✅ Buttons, animations | ❌ Static image |
| External Deps | Requires JS libraries | None (self-contained) |
| Persistence | Depends on browser | ✅ Permanent |
| File Export | Needs special handling | ✅ Direct export |
| Use Case | Interactive content | Infographics, chart snapshots |

#### Reference Implementations

- `plugins/actions/infographic/infographic.py` - Production-ready implementation using AntV + Data URL

---

## 5. Best Practices & Design Principles

### 5.1 Naming & Positioning

- **Short & Punchy**: e.g., "FlashCard", "DeepRead". Avoid generic terms like "Text Analysis Assistant"
- **Complementary**: Don't reinvent the wheel; clarify what specific problem your plugin solves

### 5.2 User Experience (UX)

- **Timely Feedback**: Send a `notification` ("Generating...") before time-consuming operations
- **Visual Appeal**: When Action outputs HTML, use modern CSS (rounded corners, shadows, gradients)
- **Smart Guidance**: If text is too short, prompt the user: "Suggest entering more content for better results"

### 5.3 Error Handling

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

---

## 6. Troubleshooting

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

- [:fontawesome-brands-github: Plugin Examples](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins)
- [:material-book-open-variant: OpenWebUI Official Docs](https://docs.openwebui.com/)
- [:material-forum: Community Discussions](https://github.com/open-webui/open-webui/discussions)
