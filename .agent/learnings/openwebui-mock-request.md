# Building a Valid Mock Request for OpenWebUI Pipes

> Discovered: 2026-03-05

## Context

OpenWebUI Pipes run as a Pipe plugin, not as a real HTTP request handler. When the Pipe
needs to call OpenWebUI-internal APIs (like `generate_chat_completion`, `get_tools`, etc.)
or load Tools that do the same, it must provide a **fake-but-complete Request object**.

## Finding

OpenWebUI's internal functions expect `request` to satisfy several contracts:

```
request.app.state.MODELS     → dict { model_id: ModelModel }  — MUST be populated!
request.app.state.config     → config object with all env variables
request.app.state.TOOLS      → dict (can start empty)
request.app.state.FUNCTIONS  → dict (can start empty)
request.app.state.redis      → None is fine
request.app.state.TOOL_SERVERS → []  is fine
request.app.url_path_for(name, **path_params) → str
request.headers              → dict with Authorization, host, user-agent
request.state.user           → user dict
request.state.token.credentials → str (the Bearer token, without "Bearer " prefix)
await request.json()         → dict (the raw request body)
await request.body()         → bytes (the raw request body as JSON bytes)
```

## Solution / Pattern

```python
from types import SimpleNamespace
import json as _json_mod

def _build_openwebui_request(user: dict, token: str, body: dict = None):
    from open_webui.config import PERSISTENT_CONFIG_REGISTRY
    from open_webui.models.models import Models as _Models

    # 1. Build config from registry
    config = SimpleNamespace()
    for item in PERSISTENT_CONFIG_REGISTRY:
        val = item.value
        if hasattr(val, "value"):
            val = val.value
        setattr(config, item.env_name, val)

    # 2. Populate MODELS from DB — critical for model validation
    system_models = {}
    try:
        for m in _Models.get_all_models():
            system_models[m.id] = m
    except Exception:
        pass

    # 3. Build app_state
    app_state = SimpleNamespace(
        config=config,
        TOOLS={},
        TOOL_CONTENTS={},
        FUNCTIONS={},
        FUNCTION_CONTENTS={},
        MODELS=system_models,   # <-- KEY: must not be empty!
        redis=None,
        TOOL_SERVERS=[],
    )

    # 4. url_path_for helper
    def url_path_for(name: str, **params):
        if name == "get_file_content_by_id":
            return f"/api/v1/files/{params.get('id')}/content"
        return f"/mock/{name}"

    app = SimpleNamespace(state=app_state, url_path_for=url_path_for)

    # 5. Async body helpers
    async def _json():
        return body or {}

    async def _body_fn():
        return _json_mod.dumps(body or {}).encode("utf-8")

    # 6. Headers
    headers = {
        "user-agent": "Mozilla/5.0",
        "host": "localhost:8080",
        "accept": "*/*",
    }
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

    return SimpleNamespace(
        app=app,
        headers=headers,
        method="POST",
        cookies={},
        base_url="http://localhost:8080",
        url=SimpleNamespace(path="/api/chat/completions", base_url="http://localhost:8080"),
        state=SimpleNamespace(
            token=SimpleNamespace(credentials=token or ""),
            user=user or {},
        ),
        json=_json,
        body=_body_fn,
    )
```

## Token Extraction

Tokens can be found in multiple places. Check in order:

```python
# 1. Direct in body (some SDK requests embed it)
token = body.get("token")

# 2. In metadata
token = token or (metadata or {}).get("token")

# 3. In the original __request__ Authorization header
if not token and __request__ is not None:
    auth = getattr(__request__, "headers", {}).get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
```

## Gotchas

- **`app.state.MODELS` empty = "Model not found"** for *any* model ID, even correct ones.
- `TOOL_SERVER_CONNECTIONS` must be synced from DB, not from in-memory cache (stale in multi-worker).
- `request.state.token.credentials` should be the **raw token** (no "Bearer " prefix).
- Tools may call `await request.json()` — must be an async method, not a regular attribute.
