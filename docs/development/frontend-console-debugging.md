# 🛠️ Debugging Python Plugins with Frontend Console

When developing plugins for Open WebUI, debugging can be challenging. Standard `print()` statements or server-side logging might not always be accessible, especially in hosted environments or when you want to see the data flow in real-time alongside the UI interactions.

This guide introduces a powerful technique: **Frontend Console Debugging**. By injecting JavaScript from your Python plugin, you can print structured logs directly to the browser's Developer Tools console (F12).

## Why Frontend Debugging?

*   **Real-time Feedback**: See logs immediately as actions happen in the browser.
*   **Rich Objects**: Inspect complex JSON objects (like `body` or `messages`) interactively, rather than reading massive text dumps.
*   **No Server Access Needed**: Debug issues even if you don't have SSH/Console access to the backend server.
*   **Clean Output**: Group logs using `console.group()` to keep your console organized.

## The Core Mechanism

Open WebUI plugins (both Actions and Filters) support an event system. We can leverage the `__event_call__` (or sometimes `__event_emitter__`) to send a special event of type `execute`. This tells the frontend to run the provided JavaScript code.

### The Helper Method

To make this easy to use, we recommend adding a helper method `_emit_debug_log` to your plugin class.

```python
import json
from typing import List

async def _emit_debug_log(
    self, 
    __event_call__, 
    title: str, 
    data: dict
):
    """
    Emit debug log to browser console via JS execution.
    
    Args:
        __event_call__: The event callable passed to action/outlet.
        title: A title for the log group.
        data: A dictionary of data to log.
    """
    # 1. Check if debugging is enabled (recommended)
    if not getattr(self.valves, "show_debug_log", True) or not __event_call__:
        return

    try:
        # 2. Construct the JavaScript code
        # We use an async IIFE (Immediately Invoked Function Expression) 
        # to ensure a clean scope and support await if needed.
        js_code = f"""
            (async function() {{
                console.group("🛠️ Plugin Debug: {title}");
                console.log({json.dumps(data, ensure_ascii=False)});
                console.groupEnd();
            }})();
        """

        # 3. Send the execute event
        await __event_call__(
            {
                "type": "execute",
                "data": {"code": js_code},
            }
        )
    except Exception as e:
        print(f"Error emitting debug log: {e}")
```

## Implementation Steps

### 1. Add a Valve for Control

It's best practice to make debugging optional so it doesn't clutter the console for normal users.

```python
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        show_debug_log: bool = Field(
            default=False, 
            description="Print debug logs to browser console (F12)"
        )
    
    def __init__(self):
        self.valves = self.Valves()
```

### 2. Inject `__event_call__`

Ensure your `action` (for Actions) or `outlet` (for Filters) method accepts `__event_call__`.

**For Filters (`outlet`):**

```python
async def outlet(
    self,
    body: dict,
    __user__: Optional[dict] = None,
    __event_call__=None,  # <--- Add this
    __metadata__: Optional[dict] = None,
) -> dict:
```

**For Actions (`action`):**

```python
async def action(
    self,
    body: dict,
    __user__=None,
    __event_call__=None, # <--- Add this
    __request__=None,
):
```

### 3. Call the Helper

Now you can log anything, anywhere in your logic!

```python
# Inside your logic...
new_content = self.process_content(content)

# Log the before and after
await self._emit_debug_log(
    __event_call__,
    "Content Normalization",
    {
        "original": content,
        "processed": new_content,
        "changes": diff_list
    }
)
```

## Best Practices

1.  **Use `json.dumps`**: Always serialize your Python dictionaries to JSON strings before embedding them in the f-string. This handles escaping quotes and special characters correctly.
2.  **Async IIFE**: Wrapping your JS in `(async function() { ... })();` is safer than raw code. It prevents variable collisions with other scripts and allows using `await` inside your debug script if you ever need to check DOM elements.
3.  **Check for None**: Always check if `__event_call__` is not None before using it, as it might not be available in all contexts (e.g., when running tests or in older Open WebUI versions).

## Example Output

When enabled, your browser console will show:

```text
> 🛠️ Plugin Debug: Content Normalization
  > {original: "...", processed: "...", changes: [...]}
```

You can expand the object to inspect every detail of your data. Happy debugging!
