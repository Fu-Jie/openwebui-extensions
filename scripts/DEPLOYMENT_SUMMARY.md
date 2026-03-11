# 📦 Async Context Compression — Local Deployment Tools

## 🎯 Feature Overview

Added a complete local deployment toolchain for the `async_context_compression` Filter plugin, supporting fast iterative development without restarting OpenWebUI.

## 📋 New Files

### 1. **deploy_filter.py** — Filter Plugin Deployment Script

- **Location**: `scripts/deploy_filter.py`
- **Function**: Auto-deploy Filter-type plugins to local OpenWebUI instance
- **Features**:
  - ✅ Auto-extract metadata from Python docstring
  - ✅ Smart semantic version recognition
  - ✅ Support multiple Filter plugin management
  - ✅ Auto-update or create plugins
  - ✅ Detailed error diagnostics and connection testing
  - ✅ List command to view all available Filters
- **Code Lines**: ~300

### 2. **DEPLOYMENT_GUIDE.md** — Complete Deployment Guide

- **Location**: `scripts/DEPLOYMENT_GUIDE.md`
- **Contents**:
  - Prerequisites and quick start
  - Detailed script documentation
  - API key retrieval method
  - Troubleshooting guide
  - Step-by-step workflow examples

### 3. **QUICK_START.md** — Quick Reference Card

- **Location**: `scripts/QUICK_START.md`
- **Contents**:
  - One-line deployment command
  - Setup steps
  - Common commands table
  - Troubleshooting quick-reference table
  - CI/CD integration examples

### 4. **test_deploy_filter.py** — Unit Test Suite

- **Location**: `tests/scripts/test_deploy_filter.py`
- **Test Coverage**:
  - ✅ Filter file discovery (3 tests)
  - ✅ Metadata extraction (3 tests)
  - ✅ API payload building (4 tests)
- **Pass Rate**: 10/10 ✅

## 🚀 Usage

### Basic Deploy (One-liner)

```bash
cd scripts
python deploy_filter.py
```

### List All Available Filters

```bash
python deploy_filter.py --list
```

### Deploy Specific Filter

```bash
python deploy_filter.py folder-memory
python deploy_filter.py context_enhancement_filter
```

## 🔧 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Load API key (.env)                                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 2. Find Filter plugin file                                  │
│    - Infer file path from name                              │
│    - Support hyphen-case and snake_case lookup              │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 3. Read Python source code                                  │
│    - Extract docstring metadata                             │
│    - title, version, author, description, openwebui_id      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 4. Build API request payload                                │
│    - Assemble manifest and meta info                        │
│    - Include complete source code content                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 5. Send request                                             │
│    - POST /api/v1/functions/id/{id}/update (update)         │
│    - POST /api/v1/functions/create (create fallback)        │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 6. Display results and diagnostics                          │
│    - ✅ Update/create success                               │
│    - ❌ Error messages and solutions                        │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Supported Filters List

Script auto-discovers the following Filters:

| Filter Name | Python File | Version |
|-----------|-----------|------|
| async-context-compression | async_context_compression.py | 1.3.0+ |
| chat-session-mapping-filter | chat_session_mapping_filter.py | 0.1.0+ |
| context_enhancement_filter | context_enhancement_filter.py | 0.3+ |
| folder-memory | folder_memory.py | 0.1.0+ |
| github_copilot_sdk_files_filter | github_copilot_sdk_files_filter.py | 0.1.3+ |
| markdown_normalizer | markdown_normalizer.py | 1.2.8+ |
| web_gemini_multimodel_filter | web_gemini_multimodel_filter.py | 0.3.2+ |

## ⚙️ Technical Details

### Metadata Extraction

Script extracts metadata from the docstring at the top of Python file:

```python
"""
title: Async Context Compression
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
description: Reduces token consumption...
version: 1.3.0
openwebui_id: b1655bc8-6de9-4cad-8cb5-a6f7829a02ce
"""
```

**Supported Metadata Fields**:

- `title` — Filter display name ✅
- `id` — Unique identifier ✅
- `author` — Author name ✅
- `author_url` — Author homepage ✅
- `funding_url` — Project link ✅
- `description` — Feature description ✅
- `version` — Semantic version number ✅
- `openwebui_id` — OpenWebUI UUID (optional)

### API Integration

Script uses OpenWebUI REST API:

```
POST /api/v1/functions/id/{filter_id}/update
- Update existing Filter
- HTTP 200: Update success
- HTTP 404: Filter not found, auto-attempt create

POST /api/v1/functions/create
- Create new Filter
- HTTP 200: Creation success
```

**Authentication**: Bearer token (API key method)

## 🔐 Security

### API Key Management

```bash
# 1. Create .env file
echo "api_key=sk-your-key-here" > scripts/.env

# 2. Add .env to .gitignore
echo "scripts/.env" >> .gitignore

# 3. Don't commit API key
git add scripts/.gitignore
git commit -m "chore: add .env to gitignore"
```

### Best Practices

- ✅ Use long-term auth tokens (not short-term JWT)
- ✅ Rotate API keys periodically
- ✅ Limit key permission scope
- ✅ Use only on trusted networks
- ✅ Use CI/CD secret management in production

## 🧪 Test Verification

### Run Test Suite

```bash
pytest tests/scripts/test_deploy_filter.py -v
```

### Test Coverage

```
✅ TestFilterDiscovery (3 tests)
   - test_find_async_context_compression
   - test_find_nonexistent_filter
   - test_find_filter_with_underscores

✅ TestMetadataExtraction (3 tests)
   - test_extract_metadata_from_async_compression
   - test_extract_metadata_empty_file
   - test_extract_metadata_multiline_docstring

✅ TestPayloadBuilding (4 tests)
   - test_build_filter_payload_basic
   - test_payload_has_required_fields
   - test_payload_with_openwebui_id

✅ TestVersionExtraction (1 test)
   - test_extract_valid_version

Result: 10/10 PASSED ✅
```

## 💡 Common Use Cases

### Use Case 1: Quick Test After Bug Fix

```bash
# 1. Modify code
vim plugins/filters/async-context-compression/async_context_compression.py

# 2. Deploy immediately (no OpenWebUI restart needed)
cd scripts && python deploy_filter.py

# 3. Test fix in OpenWebUI
# 4. Iterate (return to step 1)
```

### Use Case 2: Develop New Filter

```bash
# 1. Create new Filter directory
mkdir plugins/filters/my-new-filter

# 2. Write code (include required docstring metadata)
cat > plugins/filters/my-new-filter/my_new_filter.py << 'EOF'
"""
title: My New Filter
author: Your Name
version: 1.0.0
description: Filter description
"""

class Filter:
    # ... implementation ...
EOF

# 3. First deployment (create)
cd scripts && python deploy_filter.py my-new-filter

# 4. Test in OpenWebUI UI
# 5. Repeat updates
cd scripts && python deploy_filter.py my-new-filter
```

### Use Case 3: Version Update and Release

```bash
# 1. Update version number
vim plugins/filters/async-context-compression/async_context_compression.py
# Change: version: 1.3.0 → version: 1.4.0

# 2. Deploy new version
cd scripts && python deploy_filter.py

# 3. After testing, commit
git add plugins/filters/async-context-compression/
git commit -m "feat(filters): update async-context-compression to 1.4.0"
git push
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Filter on Release

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Deploy Filter
        run: |
          cd scripts
          python deploy_filter.py async-context-compression
        env:
          api_key: ${{ secrets.OPENWEBUI_API_KEY }}
```

## 📚 Reference Documentation

- [Complete Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Quick Reference Card](QUICK_START.md)
- [Test Suite](../tests/scripts/test_deploy_filter.py)
- [Plugin Development Guide](../docs/development/plugin-guide.md)
- [OpenWebUI Documentation](https://docs.openwebui.com/)

## 🎓 Learning Resources

### Architecture Understanding

```
OpenWebUI System Design
    ↓
Filter Plugin Type Definition
    ↓
REST API Interface (/api/v1/functions)
    ↓
Local Deployment Script Implementation (deploy_filter.py)
    ↓
Metadata Extraction and Delivery
```

### Debugging Tips

1. **Enable Verbose Logging**:

   ```bash
   python deploy_filter.py 2>&1 | tee deploy.log
   ```

2. **Test API Connection**:

   ```bash
   curl -X GET http://localhost:3000/api/v1/functions \
     -H "Authorization: Bearer $API_KEY"
   ```

3. **Verify .env File**:

   ```bash
   grep "api_key=" scripts/.env
   ```

## 📞 Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Connection error | Wrong OpenWebUI address/port | Check localhost:3000; modify URL if needed |
| .env not found | Config file not created | `echo "api_key=sk-..." > scripts/.env` |
| Filter not found | Wrong Plugin name | Run `python deploy_filter.py --list` |
| Status 401 | Invalid/expired API key | Update key in `.env` |
| Status 500 | Server error | Check OpenWebUI service logs |

## ✨ Highlight Features

| Feature | Description |
|---------|-------------|
| 🔍 Auto Discovery | Automatically find all Filter plugins |
| 📊 Metadata Extraction | Auto-extract version and metadata from code |
| ♻️ Auto-update | Smart handling of update or create |
| 🛡️ Error Handling | Detailed error messages and diagnostics |
| 🚀 Fast Iteration | Second-level deployment, no restart |
| 🧪 Complete Testing | 10 unit tests covering core functions |

---

**Last Updated**: 2026-03-09  
**Author**: Fu-Jie  
**Project**: [openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)
