# OpenWebUI Community API Patterns

## Post Data Structure Variations

When fetching posts from the OpenWebUI Community API (`https://api.openwebui.com/api/v1/posts/...`), the structure of the `data` field varies significantly depending on the `type` of the post.

### Observed Mappings

| Post Type | Data Key (under `data`) | Usual Content |
|-----------|-------------------------|---------------|
| `action`  | `function`              | Plugin code and metadata |
| `filter`  | `function`              | Filter logic and metadata |
| `pipe`    | `function`              | Pipe logic and metadata |
| `tool`    | `tool`                  | Tool definition and logic |
| `prompt`  | `prompt`                | Prompt template strings |
| `model`   | `model`                 | Model configuration |

### Implementation Workaround

To robustly extract metadata (like `version` or `description`) regardless of the post type, the following heuristic logic is recommended:

```python
def _get_plugin_obj(post: dict) -> dict:
    data = post.get("data", {}) or {}
    post_type = post.get("type")
    
    # Priority 1: Use specific type key
    if post_type in data:
        return data[post_type]
    
    # Priority 2: Fallback to common keys
    for k in ["function", "tool", "pipe"]:
        if k in data:
            return data[k]
            
    # Priority 3: First available key
    if data:
        return list(data.values())[0]
        
    return {}
```

### Gotchas
- Some older posts or different categories might not have a `version` field in `manifest`, leading to empty strings or `N/A` in reports.
- `slug` should be used as the unique identifier rather than `title` when tracking stats across history.
