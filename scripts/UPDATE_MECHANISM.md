# 🔄 部署脚本的更新机制 (Deployment Update Mechanism)

## 核心答案

✅ **是的，再次部署会自动更新！**

部署脚本采用**智能两阶段策略**：
1. 🔄 **优先尝试更新** (UPDATE) — 如果插件已存在
2. 📝 **自动创建** (CREATE) — 如果更新失败（插件不存在）

## 工作流程图

```
运行部署脚本
    ↓
读取本地代码和元数据
    ↓
发送 UPDATE 请求到 OpenWebUI
    ↓
       ├─ HTTP 200 ✅
       │  └─ 插件已存在 → 更新成功！
       │
       └─ 其他状态代码 (404, 400 等)
          └─ 插件不存在或更新失败
             ↓
             发送 CREATE 请求
             ↓
             ├─ HTTP 200 ✅
             │  └─ 创建成功！
             │
             └─ 失败
                └─ 显示错误信息
```

## 详细步骤分析

### 步骤 1️⃣: 尝试更新 (UPDATE)

```python
# 代码位置: deploy_filter.py 第 220-230 行

update_url = "http://localhost:3003/api/v1/functions/id/{filter_id}/update"

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

**这一步**:
- 向 OpenWebUI API 发送 **POST** 到 `/api/v1/functions/id/{filter_id}/update`
- 如果返回 **HTTP 200**，说明插件已存在且成功更新
- 包含的内容:
  - 完整的最新代码
  - 元数据 (title, version, author, description 等)
  - 清单信息 (manifest)

### 步骤 2️⃣: 若更新失败，尝试创建 (CREATE)

```python
# 代码位置: deploy_filter.py 第 231-245 行

if response.status_code != 200:
    print(f"⚠️  Update failed with status {response.status_code}, "
          "attempting to create instead...")
    
    create_url = "http://localhost:3003/api/v1/functions/create"
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

**这一步**:
- 如果更新失败 (HTTP ≠ 200)，自动尝试创建
- 向 `/api/v1/functions/create` 发送 **POST** 请求
- 使用**相同的 payload**（代码、元数据都一样）
- 如果创建成功，第一次部署到 OpenWebUI

## 实际使用场景

### 场景 A: 第一次部署

```bash
$ python deploy_async_context_compression.py

📦 Deploying filter 'Async Context Compression' (version 1.3.0)...
   File: .../async_context_compression.py
⚠️  Update failed with status 404, attempting to create instead...  ← 第一次，插件不存在
✅ Successfully created 'Async Context Compression' filter!         ← 创建成功
```

**发生的事**:
1. 尝试 UPDATE → 失败 (HTTP 404 — 插件不存在)
2. 自动尝试 CREATE → 成功 (HTTP 200)
3. 插件被创建到 OpenWebUI

---

### 场景 B: 再次部署 (修改代码后)

```bash
# 第一次修改代码，再次部署
$ python deploy_async_context_compression.py

📦 Deploying filter 'Async Context Compression' (version 1.3.1)...
   File: .../async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!         ← 直接更新！
```

**发生的事**:
1. 读取修改后的代码
2. 尝试 UPDATE → 成功 (HTTP 200 — 插件已存在)
3. OpenWebUI 中的插件被更新为最新代码
4. **无需重启 OpenWebUI**，立即生效！

---

### 场景 C: 多次快速迭代

```bash
# 第1次修改
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# 第2次修改
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# 第3次修改
$ python deploy_async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

# ... 无限制地重复 ...
```

**特点**:
- 🚀 每次更新只需 5 秒
- 📝 每次都是增量更新
- ✅ 无需重启 OpenWebUI
- 🔄 可以无限制地重复

## 更新的内容清单

每次部署时，以下内容会被更新：

✅ **代码** — 全部最新的 Python 代码  
✅ **版本号** — 从 docstring 自动提取  
✅ **标题** — 插件的显示名称  
✅ **作者信息** — author, author_url  
✅ **描述** — plugin description  
✅ **元数据** — funding_url, openwebui_id 等  

❌ **配置不会被覆盖** — 用户在 OpenWebUI 中设置的 Valves 配置保持不变

## 版本号管理

### 更新时版本号会变吗？

✅ **是的，会变！**

```python
# async_context_compression.py 的 docstring

"""
title: Async Context Compression
version: 1.3.0
"""
```

**每次部署时**:
1. 脚本从 docstring 读取版本号
2. 发送给 OpenWebUI 的 manifest 包含这个版本号
3. 如果代码中改了版本号，部署时会更新到新版本

**最佳实践**:
```bash
# 1. 修改代码
vim async_context_compression.py

# 2. 更新版本号（在 docstring 中）
# 版本: 1.3.0 → 1.3.1

# 3. 部署
python deploy_async_context_compression.py

# 结果: OpenWebUI 中显示版本 1.3.1
```

## 部署失败的情况

### 情况 1: 网络错误

```bash
❌ Connection error: Could not reach OpenWebUI at localhost:3003
   Make sure OpenWebUI is running and accessible.
```

**原因**: OpenWebUI 未运行或端口错误  
**解决**: 检查 OpenWebUI 是否在运行

### 情况 2: API 密钥无效

```bash
❌ Failed to update or create. Status: 401
   Error: {"error": "Unauthorized"}
```

**原因**: .env 中的 API 密钥无效或过期  
**解决**: 更新 `.env` 文件中的 api_key

### 情况 3: 服务器错误

```bash
❌ Failed to update or create. Status: 500
   Error: Internal server error
```

**原因**: OpenWebUI 服务器内部错误  
**解决**: 检查 OpenWebUI 日志

## 设置版本号的最佳实践

### 语义化版本 (Semantic Versioning)

遵循 `MAJOR.MINOR.PATCH` 格式：

```python
"""
version: 1.3.0
  │  │  │
  │  │  └─ PATCH: Bug 修复 (1.3.0 → 1.3.1)
  │  └────── MINOR: 新功能 (1.3.0 → 1.4.0)
  └───────── MAJOR: 破坏性变更 (1.3.0 → 2.0.0)
"""
```

**例子**:

```python
# Bug 修复 (PATCH)
version: 1.3.0 → 1.3.1

# 新功能 (MINOR)
version: 1.3.0 → 1.4.0

# 重大更新 (MAJOR)
version: 1.3.0 → 2.0.0
```

## 完整的迭代工作流

```bash
# 1. 首次部署
cd scripts
python deploy_async_context_compression.py
# 结果: 创建插件 (第一次)

# 2. 修改代码
vim ../plugins/filters/async-context-compression/async_context_compression.py
# 修改内容...

# 3. 再次部署 (自动更新)
python deploy_async_context_compression.py
# 结果: 更新插件 (立即生效，无需重启 OpenWebUI)

# 4. 重复步骤 2-3，无限次迭代
# 每次修改 → 每次部署 → 立即测试 → 继续改进
```

## 自动更新的优势

| 优势 | 说明 |
|-----|------|
| ⚡ **快速迭代** | 修改代码 → 部署 (5秒) → 测试，无需等待 |
| 🔄 **自动检测** | 无需手动判断是创建还是更新 |
| 📝 **版本管理** | 版本号自动从代码提取 |
| ✅ **无需重启** | OpenWebUI 无需重启，配置保持不变 |
| 🛡️ **安全更新** | 用户配置 (Valves) 不会被覆盖 |

## 禁用自动更新? ❌

通常**不需要**禁用自动更新，因为：

1. ✅ 更新是幂等的 (多次更新相同代码 = 无变化)
2. ✅ 用户配置不会被修改
3. ✅ 版本号自动管理
4. ✅ 失败时自动回退

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
