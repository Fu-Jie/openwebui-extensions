# 🚀 Local Deployment Scripts Guide

## Overview

This directory contains automated scripts for deploying plugins in development to a local OpenWebUI instance. They enable quick code pushes without restarting OpenWebUI.

## Prerequisites

1. **OpenWebUI Running**: Make sure OpenWebUI is running locally (default `http://localhost:3000`)
2. **API Key**: You need a valid OpenWebUI API key
3. **Environment File**: Create a `.env` file in this directory containing your API key:
   ```
   api_key=sk-xxxxxxxxxxxxx
   ```

## Quick Start

### Deploy a Pipe Plugin

```bash
# Deploy GitHub Copilot SDK Pipe
python deploy_pipe.py
```

### Deploy a Filter Plugin

```bash
# Deploy async_context_compression Filter (default)
python deploy_filter.py

# Deploy a specific Filter plugin
python deploy_filter.py my-filter-name

# List all available Filters
python deploy_filter.py --list
```

## Script Documentation

### `deploy_filter.py` — Filter Plugin Deployment Tool

Used to deploy Filter-type plugins (such as message filtering, context compression, etc.).

**Key Features**:
- ✅ Auto-extracts metadata from Python files (version, author, description, etc.)
- ✅ Attempts to update existing plugins, creates if not found
- ✅ Supports multiple Filter plugin management
- ✅ Detailed error messages and connection diagnostics

**Usage**:
```bash
# Deploy async_context_compression (default)
python deploy_filter.py

# Deploy other Filters
python deploy_filter.py async-context-compression
python deploy_filter.py workflow-guide

# List all available Filters
python deploy_filter.py --list
python deploy_filter.py -l
```

**Workflow**:
1. Load API key from `.env`
2. Find target Filter plugin directory
3. Read Python source file
4. Extract metadata from docstring (title, version, author, description, etc.)
5. Build API request payload
6. Send update request to OpenWebUI
7. If update fails, auto-attempt to create new plugin
8. Display results and diagnostic info

### `deploy_pipe.py` — Pipe Plugin Deployment Tool

Used to deploy Pipe-type plugins (such as GitHub Copilot SDK).

**Usage**:
```bash
python deploy_pipe.py
```

## Get an API Key

### Method 1: Use Existing User Token (Recommended)

1. Open OpenWebUI interface
2. Click user avatar → Settings
3. Find the API Keys section
4. Copy your API key (starts with sk-)
5. Paste into `.env` file

### Method 2: Create a Long-term API Key

Create a dedicated long-term API key in OpenWebUI Settings for deployment purposes.

## Troubleshooting

### "Connection error: Could not reach OpenWebUI at localhost:3000"

**Cause**: OpenWebUI is not running or port is different

**Solution**:
- Make sure OpenWebUI is running
- Check which port OpenWebUI is actually listening on (usually 3000)
- Edit the URL in the script if needed

### ".env file not found"

**Cause**: `.env` file was not created

**Solution**:
```bash
echo "api_key=sk-your-api-key-here" > .env
```

### "Filter 'xxx' not found"

**Cause**: Filter directory name is incorrect

**Solution**:
```bash
# List all available Filters
python deploy_filter.py --list
```

### "Failed to update or create. Status: 401"

**Cause**: API key is invalid or expired

**Solution**:
1. Verify your API key is valid
2. Generate a new API key
3. Update the `.env` file

## Workflow Examples

### Develop and Deploy a New Filter

```bash
# 1. Create new Filter directory in plugins/filters/
mkdir plugins/filters/my-new-filter

# 2. Create my_new_filter.py with required metadata:
# """
# title: My New Filter
# author: Your Name
# version: 1.0.0
# description: Filter description
# """

# 3. Deploy to local OpenWebUI
cd scripts
python deploy_filter.py my-new-filter

# 4. Test the plugin in OpenWebUI UI

# 5. Continue development
# ... modify code ...

# 6. Re-deploy (auto-overwrites)
python deploy_filter.py my-new-filter
```

### Fix a Bug and Deploy Quickly

```bash
# 1. Modify the source code
# vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. Deploy immediately to local
python deploy_filter.py async-context-compression

# 3. Test the fix in OpenWebUI
# (No need to restart OpenWebUI)
```

## Security Considerations

⚠️ **Important**: 
- ✅ Add `.env` file to `.gitignore` (avoid committing sensitive info)
- ✅ Never commit API keys to version control
- ✅ Use only on trusted networks
- ✅ Rotate API keys periodically

## File Structure

```
scripts/
├── deploy_filter.py        # Filter plugin deployment tool
├── deploy_pipe.py          # Pipe plugin deployment tool
├── .env                    # API key (local, not committed)
├── README.md               # This file
└── ...
```

## Reference Resources

- [OpenWebUI Documentation](https://docs.openwebui.com/)
- [Plugin Development Guide](../docs/development/plugin-guide.md)
- [Filter Plugin Examples](../plugins/filters/)

---

**Last Updated**: 2026-03-09  
**Author**: Fu-Jie
