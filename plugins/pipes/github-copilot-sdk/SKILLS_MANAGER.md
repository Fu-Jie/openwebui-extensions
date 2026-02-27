# manage_skills Tool Guide

This document describes the `manage_skills` **tool** in GitHub Copilot SDK Pipe.

> Important: `manage_skills` is a tool, not a skill.

---

## Core Model

The plugin uses **one** install/sync location for skills:

- `OPENWEBUI_SKILLS_SHARED_DIR/shared/`

There is no separate install target for "manager skill" or per-workspace skill buckets.

---

## Skill Directory Layout

All skills live under the same directory:

```text
{OPENWEBUI_SKILLS_SHARED_DIR}/shared/
├── finance-reporting/
│   ├── SKILL.md
│   ├── .owui_id
│   ├── scripts/
│   └── templates/
├── docs-writer/
│   ├── SKILL.md
│   └── .owui_id
└── ...
```

- `SKILL.md` is required.
- `.owui_id` links local folder to OpenWebUI DB record.
- Extra files (`scripts/`, `templates/`, `references/`) are optional resources.

---

## What `manage_skills` Does

`manage_skills` provides deterministic skill lifecycle operations:

- `list`
- `install`
- `create`
- `edit`
- `show`
- `delete`

Use this tool for all skill CRUD operations instead of ad-hoc shell workflows.

---

## Sync Mechanism (Local Files ↔ OpenWebUI DB)

The SDK performs **real-time bidirectional sync** between the local filesystem and the OpenWebUI database to ensure consistency.

### How it works

1.  **Identity Link**: Each local skill folder contains a hidden `.owui_id` file. This is the "glue" that links the folder to a specific record in the OpenWebUI database.
2.  **Conflict Resolution**:
    -   **Content Hash**: The SDK first compares the MD5 hash of the local `SKILL.md` content against the DB record. If they match, no sync occurs.
    -   **Timestamp Check**: If content differs, it compares the file's `mtime` with the database's `updated_at`. The newer version wins.
3.  **Operation Sync**:
    -   **Manual Edit (Filesystem)**: If you edit `SKILL.md` via VS Code or terminal, the next SDK request will push those changes to the OpenWebUI UI.
    -   **UI Edit (OpenWebUI)**: If you update instructions in the OpenWebUI workspace, the SDK will pull those changes and overwrite the local `SKILL.md`.
    -   **Tool Actions**: Actions like `manage_skills(action="create")` or `action="delete"` trigger an immediate atomic sync to the database.

> **Warning**: Do not manually delete the `.owui_id` file unless you want to "unlink" the skill and force the SDK to re-register it as a new entry.

---

## Typical Flows (Example Queries)

### 1. Install Skill from GitHub URL

**User Query:** "Help me install the data-visualizer skill from `https://github.com/user/skills/blob/main/data-visualizer/SKILL.md`"
**Tool Call:** `manage_skills(action="install", url="https://github.com/user/skills/blob/main/data-visualizer/SKILL.md")`
**Result:**

- Files downloaded to `{OPENWEBUI_SKILLS_SHARED_DIR}/shared/data-visualizer/`
- Skill metadata automatically synced to OpenWebUI Database.

### 2. Install Multiple Skills from Different URLs at Once

**User Query:** "Install these three skills: URL1, URL2, URL3"
**Tool Call:** `manage_skills(action="install", url=["URL1", "URL2", "URL3"])`
**Result:**

- Each URL is downloaded, extracted, and installed sequentially into `shared/`.
- A single DB sync runs after all installs complete.
- If one URL fails, the others still proceed. Failed URLs are listed in `errors`.

### 3. Install All Skills from One Repository

**User Query:** "Install everything under `https://github.com/myorg/skill-pack/tree/main/`"
**Tool Call:** `manage_skills(action="install", url="https://github.com/myorg/skill-pack/tree/main/")`
**Result:**

- All subdirectories containing a `SKILL.md` are discovered and installed in one shot.

### 4. Create Skill from Current Conversation

**User Query:** "Remember the Python cleanup logic we just discussed as a new skill called 'py-clean'"
**Tool Call:** `manage_skills(action="create", name="py-clean", content="...")`
**Result:**

- New directory `{OPENWEBUI_SKILLS_SHARED_DIR}/shared/py-clean/` created.
- `SKILL.md` written and synced to Database.

---

## Recommended Settings

- `ENABLE_OPENWEBUI_SKILLS=True`
- `OPENWEBUI_SKILLS_SHARED_DIR=/app/backend/data/cache/copilot-openwebui-skills`
- Optional blacklist: `DISABLED_SKILLS=skill-a,skill-b`

---

## Notes

- Do not run skill names as shell commands.
- Use `manage_skills` for lifecycle control.
- Keep all installed skills in one directory: `.../shared/`.
