# OpenWebUI Skills Manager Tool

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.2.1 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

A standalone OpenWebUI Tool plugin for managing native Workspace Skills across models.

## What's New

- Added GitHub skills-directory auto-discovery for `install_skill` (e.g., `.../tree/main/skills`) to install all child skills in one request.
- Fixed language detection with robust frontend-first fallback (`__event_call__` + timeout), request header fallback, and profile fallback.

## Key Features

- Native skill management
- User-scoped list/show/install/create/update/delete operations
- Status-bar feedback for each operation

## Methods

- `list_skills`
- `show_skill`
- `install_skill`
- `create_skill`
- `update_skill`
- `delete_skill`

## Installation

1. Open OpenWebUI → Workspace → Tools
2. Install **OpenWebUI Skills Manager Tool** from the official marketplace
3. Save and enable for your chat/model

### Manual Installation (Alternative)

- Create Tool and paste:
   - `plugins/tools/openwebui-skills-manager/openwebui_skills_manager.py`
