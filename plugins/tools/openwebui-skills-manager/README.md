# 🧰 OpenWebUI Skills Manager Tool

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 0.2.1 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

A standalone OpenWebUI Tool plugin to manage native **Workspace > Skills** for any model.

## What's New

- Added GitHub skills-directory auto-discovery for `install_skill` (e.g., `.../tree/main/skills`) to install all child skills in one request.
- Fixed language detection with robust frontend-first fallback (`__event_call__` + timeout), request header fallback, and profile fallback.

## Key Features

- **🌐 Model-agnostic**: Can be enabled for any model that supports OpenWebUI Tools.
- **🛠️ Simple Skill Management**: Directly manage OpenWebUI skill records.
- **🔐 User-scoped Safety**: Operates on current user's accessible skills.
- **📡 Friendly Status Feedback**: Emits status bubbles for each operation.

## How to Use

1. Open OpenWebUI and go to **Workspace > Tools**.
2. Create a new Tool and paste `openwebui_skills_manager.py`.
3. Enable this tool for your model/chat.
4. Ask the model to call tool operations, for example:
   - "List my skills"
   - "Show skill named docs-writer"
   - "Create a skill named meeting-notes with content ..."
   - "Update skill ..."
   - "Delete skill ..."

## Example: Install Skills

This tool can fetch and install skills directly from URLs (supporting GitHub tree/blob, raw markdown, and .zip/.tar archives).

### Install a single skill from GitHub

- "Install skill from <https://github.com/anthropics/skills/tree/main/skills/search_manager>"
- "Install skill from <https://github.com/Fu-Jie/openwebui-extensions/blob/main/.agent/skills/test-copilot-pipe/SKILL.md>"

### Batch install multiple skills

- "Install these skills: ['https://github.com/anthropics/skills/tree/main/skills/search_manager', 'https://github.com/anthropics/skills/tree/main/skills/guide_writer']"

> **Tip**: For GitHub, the tool automatically resolves directory (tree) URLs by looking for `SKILL.md` or `README.md`.

## Configuration (Valves)

| Parameter | Default | Description |
| --- | ---: | --- |
| `SHOW_STATUS` | `True` | Show operation status updates in OpenWebUI status bar. |
| `ALLOW_OVERWRITE_ON_CREATE` | `False` | Allow `create_skill`/`install_skill` to overwrite same-name skill by default. |
| `INSTALL_FETCH_TIMEOUT` | `12.0` | URL fetch timeout in seconds for skill installation. |

## Supported Tool Methods

| Method | Purpose |
| --- | --- |
| `list_skills` | List current user's skills. |
| `show_skill` | Show one skill by `skill_id` or `name`. |
| `install_skill` | Install skill from URL into OpenWebUI native skills. |
| `create_skill` | Create a new skill (or overwrite when allowed). |
| `update_skill` | Update skill fields (`new_name`, `description`, `content`, `is_active`). |
| `delete_skill` | Delete a skill by `skill_id` or `name`. |

## Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## Others

- This tool manages OpenWebUI native skill records and supports direct URL installation.
- For advanced orchestration, combine with other Pipe/Tool workflows.

## Changelog

See full history in the GitHub repository releases and commits.
