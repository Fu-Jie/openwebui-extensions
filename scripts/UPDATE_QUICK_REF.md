# 🔄 Quick Reference: Deployment Update Mechanism

## The Shortest Answer

✅ **Re-deploying automatically updates the plugin.**

## How It Works (30-second understanding)

```
Each time you run the deploy script:
1. Priority: try UPDATE (if plugin exists) → succeeds
2. Fallback: auto CREATE (first deployment) → succeeds

Result:
✅ Works correctly every time, regardless of deployment count
✅ No manual judgement needed between create vs update
✅ Takes effect immediately, no restart needed
```

## Three Scenarios

| Scenario | What Happens | Result |
|----------|-------------|--------|
| **First deployment** | UPDATE fails → CREATE succeeds | ✅ Plugin created |
| **Deploy after code change** | UPDATE succeeds directly | ✅ Plugin updates instantly |
| **Deploy without changes** | UPDATE succeeds (no change) | ✅ Safe (no effect) |

## Development Workflow

```bash
# 1. First deployment
python deploy_async_context_compression.py
# Result: ✅ Created

# 2. Modify code
vim ../plugins/filters/async-context-compression/async_context_compression.py
# Edit...

# 3. Deploy again (auto-update)
python deploy_async_context_compression.py
# Result: ✅ Updated

# 4. Continue editing and redeploying
# ... can repeat infinitely ...
```

## Key Points

✅ **Automated** — No need to worry about create vs update  
✅ **Fast** — Each deployment takes 5 seconds  
✅ **Safe** — User configuration never gets overwritten  
✅ **Instant** — No need to restart OpenWebUI  
✅ **Version Management** — Auto-extracted from code  

## How to Manage Version Numbers?

Modify the version in your code:

```python
# async_context_compression.py

"""
version: 1.3.0 → 1.3.1 (Bug fixes)
version: 1.3.0 → 1.4.0 (New features)
version: 1.3.0 → 2.0.0 (Major updates)
"""
```

Then deploy, the script will auto-read the new version and update.

## Quick Q&A

**Q: Will user configuration be overwritten?**  
A: ❌ No, Valves configuration stays the same

**Q: Do I need to restart OpenWebUI?**  
A: ❌ No, takes effect immediately

**Q: What if update fails?**  
A: ✅ Safe, keeps original plugin intact

**Q: Can I deploy unlimited times?**  
A: ✅ Yes, completely idempotent

## One-liner Summary

> First deployment creates plugin, subsequent deployments auto-update, 5-second feedback, no restart needed.

---

📖 Full docs: `scripts/UPDATE_MECHANISM.md`
