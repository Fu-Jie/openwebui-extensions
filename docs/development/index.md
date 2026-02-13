# Development

Learn how to develop plugins and contribute to OpenWebUI Extensions.

---

## Getting Started

<div class="grid cards" markdown>

-   :material-book-open-page-variant:{ .lg .middle } **Plugin Development Guide**

    ---

    The comprehensive guide covering everything from getting started to advanced patterns and best practices.

    [:octicons-arrow-right-24: Read the Guide](plugin-guide.md)

-   :material-file-document-edit:{ .lg .middle } **Documentation Guide**

    ---

    Learn how to write and contribute documentation using MkDocs and Material theme.

    [:octicons-arrow-right-24: Read the Guide](documentation-guide.md)

-   :material-github:{ .lg .middle } **Contributing**

    ---

    Learn how to contribute plugins, prompts, and documentation to the project.

    [:octicons-arrow-right-24: Contribution Guide](../contributing.md)

</div>

---

## Plugin Types Overview

OpenWebUI supports three main plugin types:

| Type | Purpose | Entry Method |
|------|---------|--------------|
| **Action** | Add buttons to messages | `action()` |
| **Filter** | Process messages | `inlet()` / `outlet()` |
| **Pipe** | Custom model integration | `pipe()` |

---

## Quick Start Templates

### Action Plugin

```python
"""
title: My Action
author: Your Name
version: 1.0.0
"""

class Action:
    async def action(self, body: dict, __event_emitter__=None):
        await __event_emitter__({"type": "notification", "data": {"content": "Hello!"}})
        return body
```

### Filter Plugin

```python
"""
title: My Filter
author: Your Name
version: 1.0.0
"""

class Filter:
    async def inlet(self, body: dict, __metadata__: dict) -> dict:
        # Process before LLM
        return body
    
    async def outlet(self, body: dict, __metadata__: dict) -> dict:
        # Process after LLM
        return body
```

### Pipe Plugin

```python
"""
title: My Pipe
author: Your Name
version: 1.0.0
"""

class Pipe:
    def pipes(self):
        return [{"id": "my-model", "name": "My Model"}]
    
    def pipe(self, body: dict):
        return "Response from custom pipe"
```

---

## Core Concepts

### Valves Configuration

Valves allow users to configure plugins through the UI:

```python
from pydantic import BaseModel, Field

class Action:
    class Valves(BaseModel):
        api_key: str = Field(default="", description="API Key")
        enabled: bool = Field(default=True, description="Enable plugin")
    
    def __init__(self):
        self.valves = self.Valves()
```

### Event Emitter

Send notifications and status updates:

```python
# Notification
await __event_emitter__({
    "type": "notification",
    "data": {"type": "success", "content": "Done!"}
})

# Status update
await __event_emitter__({
    "type": "status",
    "data": {"description": "Processing...", "done": False}
})
```

### User Context

Access user information:

```python
user_name = __user__.get("name", "User")
user_id = __user__.get("id")
user_language = __user__.get("language", "en-US")
```

---

## Best Practices

1. **Async Operations**: Always use `async/await` for I/O operations
2. **Error Handling**: Catch exceptions and notify users
3. **Status Updates**: Provide feedback during long operations
4. **Configuration**: Use Valves for customizable options
5. **Documentation**: Include clear docstrings and README files

---

## Resources

- [Full Development Guide](plugin-guide.md)
- [Plugin Examples](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins)
- [OpenWebUI Documentation](https://docs.openwebui.com/)
