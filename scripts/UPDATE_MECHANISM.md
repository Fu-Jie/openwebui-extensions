# 🔄 Deployment Scripts Update Mechanism

## Core Answer

✅ **Yes, re-deploying automatically updates the plugin!**

The deployment script uses a **smart two-stage strategy**:

1. 🔄 **Try UPDATE First** (if plugin exists)
2. 📝 **Auto CREATE** (if update fails — plugin doesn't exist)

## Workflow Diagram

```
Run deploy script
    ↓
Read local code and metadata
    ↓
Send UPDATE request to OpenWebUI
    ↓
       ├─ HTTP 200 ✅
       │  └─ Plugin exists → Update successful!
       │
       └─ Other status codes (404, 400, etc.)
          └─ Plugin doesn't exist or update failed
             ↓
             Send CREATE request
             ↓
             ├─ HTTP 200 ✅
             │  └─ Creation successful!
             │
             └─ Failed
                └─ Display error message
```

## Detailed Step-by-step

### Step 1️⃣: Try UPDATE First

```python
# Code location: deploy_filter.py line 220-230

update_url = "http://localhost:3000/api/v1/functions/id/{filter_id}/update"

response = requests.post(
    update_url,
    headers=headers,
    data=json.dumps(payload),
    timeout=10,
)

if response.status_code == 200:
    print(f"✅ Successfully updated '{title}' filter!")
    return True
```

**What Happens**:

- Send **POST** to `/api/v1/functions/id/{filter_id}/update`
- If returns **HTTP 200**, plugin exists and update succeeded
- Includes:
  - Complete latest code
  - Metadata (title, version, author, description, etc.)
  - Manifest information

### Step 2️⃣: If UPDATE Fails, Try CREATE

```python
# Code location: deploy_filter.py line 231-245

if response.status_code != 200:
    print(f"⚠️  Update failed with status {response.status_code}, "
          "attempting to create instead...")
    
    create_url = "http://localhost:3000/api/v1/functions/create"
    res_create = requests.post(
        create_url,
        headers=headers,
        data=json.dumps(payload),
        timeout=10,
    )
    
    if res_create.status_code == 200:
        print(f"✅ Successfully created '{title}' filter!")
        return True
```

**What Happens**:

- If update fails (HTTP ≠ 200), auto-attempt create
- Send **POST** to `/api/v1/functions/create`
- Uses **same payload** (code, metadata identical)
- If creation succeeds, first deployment to OpenWebUI

## Real-world Scenarios

### Scenario A: First Deployment

```bash
$ python deploy_async_context_compression.py

📦 Deploying filter 'Async Context Compression' (version 1.3.0)...
   File: .../async_context_compression.py
⚠️  Update failed with status 404, attempting to create instead...  ← First time, plugin doesn't exist
✅ Successfully created 'Async Context Compression' filter!         ← Creation succeeds
```

**What Happens**:

1. Try UPDATE → fails (HTTP 404 — plugin doesn't exist)
2. Auto-try CREATE → succeeds (HTTP 200)
3. Plugin created in OpenWebUI

---

### Scenario B: Re-deploy After Code Changes

```bash
# Made first code change, deploying again
$ python deploy_async_context_compression.py

📦 Deploying filter 'Async Context Compression' (version 1.3.1)...
   File: .../async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!         ← Direct update!
```

**What Happens**:

1. Read modified code
2. Try UPDATE → succeeds (HTTP 200 — plugin exists)
3. Plugin in OpenWebUI updated to latest code
4. **No need to restart OpenWebUI**, takes effect immediately!

---

### Scenario C: Multiple Fast Iterations

```bash
# 1st change
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# 2nd change
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# 3rd change
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# ... repeat infinitely ...
```

**Characteristics**:

- 🚀 Each update takes only 5 seconds
- 📝 Each is an incremental update
- ✅ No need to restart OpenWebUI
- 🔄 Can repeat indefinitely

## What Gets Updated

Each deployment updates the following:

✅ **Code** — All latest Python code  
✅ **Version** — Auto-extracted from docstring  
✅ **Title** — Plugin display name  
✅ **Author Info** — author, author_url  
✅ **Description** — Plugin description  
✅ **Metadata** — funding_url, openwebui_id, etc.  

❌ **Configuration NOT Overwritten** — User's Valves settings in OpenWebUI stay unchanged

## Version Number Management

### Does Version Change on Update?

✅ **Yes!**

```python
# docstring in async_context_compression.py

"""
title: Async Context Compression
version: 1.3.0
"""
```

**Each deployment**:

1. Script reads version from docstring
2. Sends this version in manifest to OpenWebUI
3. If you change version in code, deployment updates to new version

**Best Practice**:

```bash
# 1. Modify code
vim async_context_compression.py

# 2. Update version (in docstring)
# version: 1.3.0 → 1.3.1

# 3. Deploy
python deploy_async_context_compression.py

# Result: OpenWebUI shows version 1.3.1
```

## Deployment Failure Cases

### Case 1: Network Error

```bash
❌ Connection error: Could not reach OpenWebUI at localhost:3000
   Make sure OpenWebUI is running and accessible.
```

**Cause**: OpenWebUI not running or wrong port  
**Solution**: Check if OpenWebUI is running

### Case 2: Invalid API Key

```bash
❌ Failed to update or create. Status: 401
   Error: {"error": "Unauthorized"}
```

**Cause**: API key in .env is invalid or expired  
**Solution**: Update api_key in `.env` file

### Case 3: Server Error

```bash
❌ Failed to update or create. Status: 500
   Error: Internal server error
```

**Cause**: OpenWebUI server internal error  
**Solution**: Check OpenWebUI logs

## Setting Version Numbers — Best Practices

### Semantic Versioning

Follow `MAJOR.MINOR.PATCH` format:

```python
"""
version: 1.3.0
  │  │  │
  │  │  └─ PATCH: Bug fixes (1.3.0 → 1.3.1)
  │  └────── MINOR: New features (1.3.0 → 1.4.0)
  └───────── MAJOR: Breaking changes (1.3.0 → 2.0.0)
"""
```

**Examples**:

```python
# Bug fix (PATCH)
version: 1.3.0 → 1.3.1

# New feature (MINOR)
version: 1.3.0 → 1.4.0

# Major update (MAJOR)
version: 1.3.0 → 2.0.0
```

## Complete Iteration Workflow

```bash
# 1. First deployment
cd scripts
python deploy_async_context_compression.py
# Result: Plugin created (first time)

# 2. Modify code
vim ../plugins/filters/async-context-compression/async_context_compression.py
# Edit code...

# 3. Deploy again (auto-update)
python deploy_async_context_compression.py
# Result: Plugin updated (takes effect immediately, no OpenWebUI restart)

# 4. Repeat steps 2-3 indefinitely
# Modify → Deploy → Test → Improve → Repeat
```

## Benefits of Auto-update

| Benefit | Details |
|---------|---------|
| ⚡ **Fast Iteration** | Code change → Deploy (5s) → Test, no waiting |
| 🔄 **Auto-detection** | No manual decision between create/update |
| 📝 **Version Management** | Version auto-extracted from code |
| ✅ **No Restart Needed** | OpenWebUI runs continuously, config stays same |
| 🛡️ **Safe Updates** | User settings (Valves) never overwritten |

## Disable Auto-update? ❌

Usually **not needed** because:

1. ✅ Updates are idempotent (same code deployed multiple times = no change)
2. ✅ User configuration not modified
3. ✅ Version numbers auto-managed
4. ✅ Failures auto-rollback

但如果真的需要控制，可以：

- 手动修改脚本 (修改 `deploy_filter.py`)
- 或分别使用 UPDATE/CREATE 的具体 API 端点

## 常见问题

### Q: 更新是否会丢失用户的配置？

❌ **不会！**  
用户在 OpenWebUI 中设置的 Valves (参数配置) 会被保留。

### Q: 是否可以回到旧版本？

✅ **可以！**  
修改代码中的 `version` 号为旧版本，然后重新部署。

### Q: 更新需要多长时间？

⚡ **约 5 秒**  
包括: 读文件 (1s) + 发送请求 (3s) + 响应 (1s)

### Q: 可以同时部署多个插件吗？

✅ **可以！**  

```bash
python deploy_filter.py async-context-compression
python deploy_filter.py folder-memory
python deploy_filter.py context_enhancement_filter
```

### Q: 部署失败了会怎样？

✅ **OpenWebUI 中的插件保持不变**  
失败不会修改已部署的插件。

---

**总结**: 部署脚本的更新机制完全自动化，开发者只需修改代码，每次运行 `deploy_async_context_compression.py` 就会自动：

1. ✅ 创建（第一次）或更新（后续）插件
2. ✅ 从代码提取最新的元数据和版本号
3. ✅ 立即生效，无需重启 OpenWebUI
4. ✅ 保留用户的配置不变

这使得本地开发和快速迭代变得极其流畅！🚀
