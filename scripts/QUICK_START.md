# ⚡ Quick Deployment Reference

## One-line Deploy Commands

```bash
# Deploy async_context_compression Filter (default)
cd scripts && python deploy_filter.py

# List all available Filters
cd scripts && python deploy_filter.py --list
```

## Setup Steps (One time only)

```bash
# 1. Enter scripts directory
cd scripts

# 2. Create .env file with your OpenWebUI API key
echo "api_key=sk-your-api-key-here" > .env

# 3. Make sure OpenWebUI is running on localhost:3000
```

## Get Your API Key

1. Open OpenWebUI → user avatar → Settings
2. Find "API Keys" section
3. Copy your key (starts with sk-)
4. Paste into `.env` file

## Deployment Workflow

```bash
# 1. Edit plugin code
vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. Deploy to local
python deploy_filter.py

# 3. Test in OpenWebUI (no restart needed)

# 4. Deploy again (auto-overwrites)
python deploy_filter.py
```

## Common Commands

| Command | Description |
|---------|-------------|
| `python deploy_filter.py` | Deploy async_context_compression |
| `python deploy_filter.py filter-name` | Deploy specific Filter |
| `python deploy_filter.py --list` | List all available Filters |
| `python deploy_pipe.py` | Deploy GitHub Copilot SDK Pipe |

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Connection error | OpenWebUI not running | Start OpenWebUI or check port |
| .env not found | Config file not created | `echo "api_key=sk-..." > .env` |
| Filter not found | Filter name is wrong | Run `python deploy_filter.py --list` |
| Status 401 | API key invalid | Update key in `.env` |

## File Locations

```
openwebui-extensions/
├── scripts/
│   ├── deploy_filter.py        ← Filter deployment tool
│   ├── deploy_pipe.py          ← Pipe deployment tool
│   ├── .env                    ← API key (don't commit)
│   └── DEPLOYMENT_GUIDE.md     ← Full guide
│
└── plugins/
    └── filters/
        └── async-context-compression/
            ├── async_context_compression.py
            ├── README.md
            └── README_CN.md
```

## Suggested Workflow

### Fast Iterative Development

```bash
# Terminal 1: Start OpenWebUI (if not running)
docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:latest

# Terminal 2: Development loop (repeated)
cd scripts
code ../plugins/filters/async-context-compression/  # Edit code
python deploy_filter.py                             # Deploy
# → Test in OpenWebUI
# → Go back to edit, repeat
```

### CI/CD Integration

```bash
# In GitHub Actions
- name: Deploy filter to staging
  run: |
    cd scripts
    python deploy_filter.py async-context-compression
  env:
    api_key: ${{ secrets.OPENWEBUI_API_KEY }}
```

---

📚 **More Help**: See `DEPLOYMENT_GUIDE.md`
