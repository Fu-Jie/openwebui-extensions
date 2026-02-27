# GitHub Copilot SDK Pipe Detailed Usage Guide

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.9.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

This guide is for production usage. README remains community-facing and concise; this page focuses on step-by-step operations and troubleshooting.

---

## 1. When to Use This Guide

Use this manual if you need to:

- Run GitHub Copilot official models in OpenWebUI
- Use BYOK providers (OpenAI/Anthropic)
- Generate and publish artifacts (Excel/CSV/HTML/PDF)
- Manage Skills with OpenWebUI bridge and `manage_skills`

---

## 2. Pre-flight Checklist

### 2.1 Required components

- OpenWebUI is running (recommended `v0.8.0+` for Rich UI)
- Pipe is installed: `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py`
- Recommended companion filter:
  - [GitHub Copilot SDK Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6)

### 2.2 Authentication (at least one)

You must configure one of the following:

1. `GH_TOKEN` for official GitHub Copilot models
2. `BYOK_API_KEY` for OpenAI/Anthropic style providers

---

## 3. Installation Flow

1. Open OpenWebUI → **Workspace → Functions**
2. Create function and paste `github_copilot_sdk.py`
3. Save and enable
4. In chat model selector, choose:
   - `github_copilot_official_sdk_pipe.*` (official)
   - or your BYOK model entries

---

## 4. Configuration Baseline

### 4.1 Minimal admin setup

- `GH_TOKEN` or `BYOK_API_KEY`
- `ENABLE_OPENWEBUI_TOOLS = True`
- `ENABLE_MCP_SERVER = True`
- `ENABLE_OPENWEBUI_SKILLS = True`
- `SHOW_THINKING = True`

### 4.2 Recommended production settings

- `COPILOTSDK_CONFIG_DIR=/app/backend/data/.copilot`
  - Persists SDK config/session state across restarts
- `OPENWEBUI_SKILLS_SHARED_DIR=/app/backend/data/cache/copilot-openwebui-skills`
  - Shared skill cache directory
- `DEBUG=True` during troubleshooting only

### 4.3 User-level overrides

Users can override `GH_TOKEN`, `REASONING_EFFORT`, `BYOK_API_KEY`, `DISABLED_SKILLS`, etc.

---

## 5. Model Access Modes

## 5.1 Official Copilot mode

- Set `GH_TOKEN`
- Use official model catalog
- Supports reasoning effort, tools, infinite session features

## 5.2 BYOK mode

- Set `BYOK_TYPE`, `BYOK_BASE_URL`, `BYOK_API_KEY`
- Leave `BYOK_MODELS` empty for auto-fetch, or set explicit list
- Best when no Copilot subscription is available

---

## 6. Artifact Publishing Workflow (Critical)

Use `publish_file_from_workspace` with the sequence: write → publish → return links.

### 6.1 HTML delivery modes

- `artifacts` (default)
  - Returns `[Preview]` + `[Download]`
  - `html_embed` can be rendered in a full-height iframe block
- `richui`
  - Returns `[Preview]` + `[Download]`
  - Rich UI renders automatically (no iframe block in message)

### 6.2 PDF delivery rule

- Output Markdown links only (`[Preview]` + `[Download]` when available)
- **Do not** embed PDF via iframe/html blocks

### 6.3 Images and other files

- Images: prefer direct display + download
- Other artifacts (`xlsx/csv/docx`): provide download links

---

## 7. Skills Operations

> Key rule: `manage_skills` is a **tool**, not a skill; all skills are installed in **one directory**: `OPENWEBUI_SKILLS_SHARED_DIR/shared/`.

## 7.1 OpenWebUI Skills bridge

With `ENABLE_OPENWEBUI_SKILLS=True`:

- Skills from UI sync into SDK directories
- Directory-side updates sync back according to sync policy

## 7.2 `manage_skills` quick actions

- `list`, `install`, `create`, `edit`, `show`, `delete`

## 7.3 Operational tips

- Use `DISABLED_SKILLS` to reduce noisy skill routing
- Keep skill descriptions explicit for better intent matching

---

## 8. First-run Validation Checklist

1. Basic chat response works
2. Tool call can be triggered
3. CSV/XLSX can be published and downloaded
4. HTML mode works (`artifacts` or `richui`)
5. PDF returns links only (no embed)
6. `manage_skills list` returns skill inventory

---

## 9. Troubleshooting

### 9.1 Empty model list

- Ensure at least one of `GH_TOKEN` / `BYOK_API_KEY` is set
- Validate BYOK base URL and model names

### 9.2 Tools not executing

- Check `ENABLE_OPENWEBUI_TOOLS`, `ENABLE_MCP_SERVER`, `ENABLE_OPENAPI_SERVER`
- Confirm session/model has tool access

### 9.3 Publish succeeded but link unavailable

- Use the original URLs returned by tool output
- Verify storage/backend access policy
- For PDF, do not attempt iframe embedding

### 9.4 Status appears stuck

- Upgrade to latest plugin code
- Enable `DEBUG=True` temporarily
- Verify frontend version compatibility for Rich UI

---

## 10. Practical Prompt Templates

- “Analyze `sales.csv`, summarize by month, export `monthly_summary.xlsx`, and give me the download link.”
- “Generate an interactive HTML dashboard and publish it with Preview and Download links.”
- “Create a reusable skill named `finance-reporting` from this workflow.”

---

For deeper architecture and examples:

- [Deep Dive](github-copilot-sdk-deep-dive.md)
- [Advanced Tutorial](github-copilot-sdk-tutorial.md)
- [Main Plugin Doc](github-copilot-sdk.md)
