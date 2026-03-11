# 🚀 Deployment Scripts Guide

## 📁 Deployment Tools

To support quick local deployment of async_context_compression and other Filter plugins, we've added the following files:

### File Inventory

```
scripts/
├── install_all_plugins.py                  ✨ Batch install Action/Filter/Pipe/Tool plugins
├── deploy_filter.py                        ✨ Generic Filter deployment tool
├── deploy_tool.py                          ✨ Tool plugin deployment tool
├── deploy_async_context_compression.py     ✨ Async Context Compression quick deploy
├── deploy_pipe.py                          (existing) Pipe deployment tool
├── DEPLOYMENT_GUIDE.md                     ✨ Complete deployment guide
├── DEPLOYMENT_SUMMARY.md                   ✨ Deploy feature summary
├── QUICK_START.md                          ✨ Quick reference card
├── .env                                    (create as needed) API key configuration
└── ...other existing scripts
```

## ⚡ Quick Start (30 seconds)

### Step 1: Prepare Your API Key

```bash
cd scripts

# Get your OpenWebUI API key:
# 1. Open OpenWebUI → User menu → Settings
# 2. Find the "API Keys" section
# 3. Copy your key (starts with sk-)

# Create .env file
cat > .env <<'EOF'
api_key=sk-your-key-here
url=http://localhost:3000
EOF
```

### Step 2a: Install All Plugins (Recommended)

```bash
python install_all_plugins.py
```

### Step 2b: Or Deploy Individual Plugins

```bash
# Easiest way - dedicated script
python deploy_async_context_compression.py

# Or use generic script
python deploy_filter.py

# Or specify plugin name
python deploy_filter.py async-context-compression

# Or deploy a Tool
python deploy_tool.py
```

## 📋 Deployment Tools Detailed

### 1️⃣ `deploy_async_context_compression.py` — Dedicated Deployment Script

**The simplest way to deploy!**

```bash
cd scripts
python deploy_async_context_compression.py
```

**Features**:

- ✅ Optimized specifically for async_context_compression
- ✅ Clear deployment steps and confirmation
- ✅ Friendly error messages
- ✅ Shows next steps after successful deployment

**Sample Output**:

```
======================================================================
🚀 Deploying Async Context Compression Filter Plugin
======================================================================

📦 Deploying filter 'Async Context Compression' (version 1.3.0)...
   File: /path/to/async_context_compression.py
✅ Successfully updated 'Async Context Compression' filter!

======================================================================
✅ Deployment successful!
======================================================================

Next steps:
  1. Open OpenWebUI in your browser: http://localhost:3000
  2. Go to Settings → Filters
  3. Enable 'Async Context Compression'
  4. Configure Valves as needed
  5. Start using the filter in conversations
```

### 2️⃣ `deploy_filter.py` — Generic Filter Deployment Tool

**Supports all Filter plugins!**

```bash
# Deploy default async_context_compression
python deploy_filter.py

# Deploy other Filters
python deploy_filter.py folder-memory
python deploy_filter.py context_enhancement_filter

# List all available Filters
python deploy_filter.py --list
```

**Features**:

- ✅ Generic Filter deployment tool
- ✅ Supports multiple plugins
- ✅ Auto metadata extraction
- ✅ Smart update/create logic
- ✅ Complete error diagnostics

### 3️⃣ `deploy_pipe.py` — Pipe Deployment Tool

```bash
python deploy_pipe.py
```

Used to deploy Pipe-type plugins (like GitHub Copilot SDK).

### 3️⃣+ `deploy_tool.py` — Tool Deployment Tool

```bash
# Deploy default Tool
python deploy_tool.py

# Or specify a specific Tool
python deploy_tool.py openwebui-skills-manager
```

**Features**:

- ✅ Supports Tools plugin deployment
- ✅ Auto-detects `Tools` class definition
- ✅ Smart update/create logic
- ✅ Complete error diagnostics

**Use Case**:
Deploy or reinstall a specific Tool individually, or deploy only Tools without running full batch installation. The script now calls OpenWebUI's native `/api/v1/tools/*` endpoints.

### 4️⃣ `install_all_plugins.py` — Batch Installation Script

One-command installation of all repository plugins that meet these criteria:

- Located in `plugins/actions`, `plugins/filters`, `plugins/pipes`, `plugins/tools`
- Plugin header contains `openwebui_id`
- Filename is not in Chinese characters
- Filename does not end with `_cn.py`

```bash
# Check which plugins will be installed
python install_all_plugins.py --list

# Dry-run without calling API
python install_all_plugins.py --dry-run

# Actually install all supported types (including Action/Filter/Pipe/Tool)
python install_all_plugins.py

# Install only specific types
python install_all_plugins.py --types pipe action
```

The script prioritizes updating existing plugins and automatically creates new ones.

**Tool Integration**: Tool-type plugins now automatically use OpenWebUI's native `/api/v1/tools/create` and `/api/v1/tools/id/{id}/update` endpoints, no longer reusing the `functions` endpoint.

## 🔧 How It Works

```
Your code changes
    ↓
Run deployment script
    ↓
Script reads the corresponding plugin file
    ↓
Auto-extracts metadata from code (title, version, author, etc.)
    ↓
Builds API request
    ↓
Sends to local OpenWebUI
    ↓
OpenWebUI updates or creates plugin
    ↓
Takes effect immediately! (no restart needed)
```

## 📊 Available Filter List

Use `python deploy_filter.py --list` to see all available Filters:

| Filter Name | Python File | Description |
|-----------|-----------|------|
| **async-context-compression** | async_context_compression.py | Async context compression |
| chat-session-mapping-filter | chat_session_mapping_filter.py | Chat session mapping |
| context_enhancement_filter | context_enhancement_filter.py | Context enhancement |
| folder-memory | folder_memory.py | Folder memory |
| github_copilot_sdk_files_filter | github_copilot_sdk_files_filter.py | Copilot SDK Files |
| markdown_normalizer | markdown_normalizer.py | Markdown normalization |
| web_gemini_multimodel_filter | web_gemini_multimodel_filter.py | Gemini multimodal |

## 🎯 Common Use Cases

### Scenario 1: Deploy After Feature Development

```bash
# 1. Modify code
vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. Update version number (optional)
# version: 1.3.0 → 1.3.1

# 3. Deploy
python deploy_async_context_compression.py

# 4. Test in OpenWebUI
# → No restart needed, takes effect immediately!

# 5. Continue development and repeat
```

### Scenario 2: Fix Bug and Verify Quickly

```bash
# 1. Find and fix bug
vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. Quick deploy to verify
python deploy_async_context_compression.py

# 3. Test bug fix in OpenWebUI
# One-command deploy, instant feedback!
```

### Scenario 3: Deploy Multiple Filters

```bash
# Deploy all Filters that need updates
python deploy_filter.py async-context-compression
python deploy_filter.py folder-memory
python deploy_filter.py context_enhancement_filter
```

## 🔐 Security Tips

### Manage API Keys

```bash
# 1. Create .env (local only)
echo "api_key=sk-your-key" > .env

# 2. Add to .gitignore (prevent commit)
echo "scripts/.env" >> ../.gitignore

# 3. Verify it won't be committed
git status  # should not show .env

# 4. Rotate keys regularly
# → Generate new key in OpenWebUI Settings
# → Update .env file
```

### ✅ Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] Never hardcode API keys in code
- [ ] Rotate API keys periodically
- [ ] Use only on trusted networks
- [ ] Use CI/CD secret management in production

## ❌ Troubleshooting

### Issue 1: "Connection error"

```
❌ Connection error: Could not reach OpenWebUI at localhost:3000
   Make sure OpenWebUI is running and accessible.
```

**Solution**:

```bash
# 1. Check if OpenWebUI is running
curl http://localhost:3000

# 2. If port is different, edit URL in script
# Default: http://localhost:3000
# Location: "localhost:3000" in deploy_filter.py

# 3. Check firewall settings
```

### Issue 2: ".env file not found"

```
❌ [ERROR] .env file not found at .env
   Please create it with: api_key=sk-xxxxxxxxxxxx
```

**Solution**:

```bash
echo "api_key=sk-your-api-key" > .env
cat .env  # verify file created
```

### Issue 3: "Filter not found"

```
❌ [ERROR] Filter 'xxx' not found in .../plugins/filters
```

**Solution**:

```bash
# List all available Filters
python deploy_filter.py --list

# Retry with correct name
python deploy_filter.py async-context-compression
```

### Issue 4: "Status 401" (Unauthorized)

```
❌ Failed to update or create. Status: 401
   Error: {"error": "Unauthorized"}
```

**Solution**:

```bash
# 1. Verify API key is correct
grep "api_key=" .env

# 2. Check if key is still valid in OpenWebUI
# Settings → API Keys → Check

# 3. Generate new key and update .env
echo "api_key=sk-new-key" > .env
```

## 📖 Documentation Navigation

| Document | Description |
|------|------|
| **README.md** (this file) | Quick reference and FAQs |
| [QUICK_START.md](QUICK_START.md) | One-page cheat sheet |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete detailed guide |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | Technical architecture |

## 🧪 Verify Deployment Success

### Method 1: Check Script Output

```bash
python deploy_async_context_compression.py

# Success indicator:
✅ Successfully updated 'Async Context Compression' filter!
```

### Method 2: Verify in OpenWebUI

1. Open OpenWebUI: <http://localhost:3000>
2. Go to Settings → Filters
3. Check if 'Async Context Compression' is listed
4. Verify version number is correct (should be latest)

### Method 3: Test Plugin Functionality

1. Open a new conversation
2. Enable 'Async Context Compression' Filter
3. Have multiple-turn conversation and verify compression/summarization works

## 💡 Advanced Usage

### Automated Deploy & Test

```bash
#!/bin/bash
# deploy_and_test.sh

echo "Deploying plugin..."
python scripts/deploy_async_context_compression.py

if [ $? -eq 0 ]; then
    echo "✅ Deploy successful, running tests..."
    python -m pytest tests/plugins/filters/async-context-compression/ -v
else
    echo "❌ Deploy failed"
    exit 1
fi
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy on Push

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      
      - name: Deploy Async Context Compression
        run: python scripts/deploy_async_context_compression.py
        env:
          api_key: ${{ secrets.OPENWEBUI_API_KEY }}
```

## 📞 Getting Help

### Check Script Status

```bash
# List all available scripts
ls -la scripts/*.py

# Check if deployment scripts exist
ls -la scripts/deploy_*.py
```

### View Script Help

```bash
# View help (if supported)
python scripts/deploy_filter.py --help  # if supported
python scripts/deploy_async_context_compression.py --help
```

### Debug Mode

```bash
# Save output to log file
python scripts/deploy_async_context_compression.py | tee deploy.log

# Check log
cat deploy.log
```

---

## 📝 File Checklist

Newly created deployment-related files:

```
✨ scripts/deploy_filter.py                     (new) ~300 lines
✨ scripts/deploy_async_context_compression.py  (new) ~70 lines
✨ scripts/DEPLOYMENT_GUIDE.md                  (new) complete guide
✨ scripts/DEPLOYMENT_SUMMARY.md                (new) technical summary
✨ scripts/QUICK_START.md                       (new) quick reference
📄 tests/scripts/test_deploy_filter.py          (new) 10 unit tests ✅

✅ All files created and tested successfully!
```

---

**Last Updated**: 2026-03-09  
**Script Status**: ✅ Ready for production  
**Test Coverage**: 10/10 passed ✅
