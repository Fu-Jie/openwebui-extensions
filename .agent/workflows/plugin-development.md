---
description: OpenWebUI Plugin Development & Release Workflow
---

# OpenWebUI Plugin Development Workflow

This workflow outlines the standard process for developing, documenting, and releasing plugins for OpenWebUI, ensuring compliance with project standards and CI/CD requirements.

## 1. Development Standards

Reference: `.github/copilot-instructions.md`

### Bilingual Requirement

Every plugin **MUST** have bilingual versions for both code and documentation:

- **Code**:
  - English: `plugins/{type}/{name}/{name}.py`
  - Chinese: `plugins/{type}/{name}/{name_cn}.py` (or `中文名.py`)
- **README**:
  - English: `plugins/{type}/{name}/README.md`
  - Chinese: `plugins/{type}/{name}/README_CN.md`

### Code Structure

- **Docstring**: Must include `title`, `author`, `version`, `description`, etc.
- **Valves**: Use `pydantic` for configuration.
- **Database**: Re-use `open_webui.internal.db` shared connection.
- **User Context**: Use `_get_user_context` helper method.
- **Chat Context**: Use `_get_chat_context` helper method for `chat_id` and `message_id`.
- **Debugging**: Use `_emit_debug_log` for frontend console logging (requires `SHOW_DEBUG_LOG` valve).
- **Chat API**: For message updates, follow the "OpenWebUI Chat API 更新规范" in `.github/copilot-instructions.md`.
  - Use Event API for immediate UI updates
  - Use Chat Persistence API for database storage
  - Always update both `messages[]` and `history.messages`

### Commit Messages & Release Notes

- **Language**: **English ONLY**. Do not use Chinese in commit messages or release notes.
- **Format**: Conventional Commits (e.g., `feat:`, `fix:`, `docs:`).

## 2. Documentation Updates

When adding or updating a plugin, you **MUST** update the following documentation files to maintain consistency:

### Plugin Directory

- `README.md`: Update version, description, and usage.
  - **Key Capabilities**: **MUST** include ALL core functionalities and features. Do not only list new features in "What's New".
  - **What's New**: Explicitly describe only the latest changes/updates in a prominent position at the beginning. This section is dynamic and changes with versions.
- `README_CN.md`: Update version, description, and usage.
  - **核心功能 (Key Capabilities)**: **必须**包含所有核心功能和特性，不能只在 "What's New" 中列出。
  - **最新更新 (What's New)**: 在开头显眼位置明确描述最新的更改/更新。此部分是动态的，随版本变化。

### Global Documentation (`docs/`)

- **Index Pages**:
  - `docs/plugins/{type}/index.md`: Add/Update list item with **correct version**.
  - `docs/plugins/{type}/index.zh.md`: Add/Update list item with **correct version**.
- **Detail Pages**:
  - `docs/plugins/{type}/{name}.md`: Ensure content matches README.
  - `docs/plugins/{type}/{name}.zh.md`: Ensure content matches README_CN.

### Root README

- `README.md`: Add to "Featured Plugins" if applicable.
- `README_CN.md`: Add to "Featured Plugins" if applicable.

## 3. Version Control & Release

Reference: `.github/workflows/release.yml`

### Version Bumping

- **Rule**: Version bump is required **ONLY when the user explicitly requests a release**. Regular code changes do NOT require version bumps.
- **Format**: Semantic Versioning (e.g., `1.0.0` -> `1.0.1`).
- **When to Bump**: Only update the version when:
  - User says "发布" / "release" / "bump version"
  - User explicitly asks to prepare for release
- **Agent Initiative**: After completing significant changes (new features, bug fixes, or multiple code modifications), the agent **SHOULD proactively ask** the user if they want to release a new version. If confirmed, update all version-related files.
- **Consistency**: When bumping, update version in **ALL** locations:
  1. English Code (`.py`)
  2. Chinese Code (`.py`)
  3. English README (`README.md`)
  4. Chinese README (`README_CN.md`)
  5. Docs Index (`docs/.../index.md`)
  6. Docs Index CN (`docs/.../index.zh.md`)
  7. Docs Detail (`docs/.../{name}.md`)
  8. Docs Detail CN (`docs/.../{name}.zh.md`)

### Automated Release Process

1. **Trigger**: Push to `main` branch with changes in `plugins/**/*.py`.
2. **Detection**: `scripts/extract_plugin_versions.py` detects changed plugins and compares versions.
3. **Release**:
    - Generates release notes based on changes.
    - Creates a GitHub Release tag (e.g., `v2024.01.01-1`).
    - Uploads individual `.py` files of **changed plugins only** as assets.
4. **Market Publishing**:
    - Workflow: `.github/workflows/publish_plugin.yml`
    - Trigger: Release published.
    - Action: Automatically updates the plugin code and metadata on OpenWebUI.com using `scripts/publish_plugin.py`.
    - **Auto-Sync**: If a local plugin has no ID but matches an existing published plugin by **Title**, the script will automatically fetch the ID, update the local file, and proceed with the update.
    - Requirement: `OPENWEBUI_API_KEY` secret must be set.
    - **README Link**: When announcing a release, always include the GitHub README URL for the plugin:
      - Format: `https://github.com/Fu-Jie/awesome-openwebui/blob/main/plugins/{type}/{name}/README.md`
      - Example: `https://github.com/Fu-Jie/awesome-openwebui/blob/main/plugins/filters/folder-memory/README.md`

### Pull Request Check

- Workflow: `.github/workflows/plugin-version-check.yml`
- Checks if plugin files are modified.
- **Fails** if version number is not updated.
- **Fails** if PR description is too short (< 20 chars).

## 4. Verification Checklist

Before committing:

- [ ] Code is bilingual and functional?
- [ ] Docstrings have updated version?
- [ ] READMEs are updated and bilingual?
- [ ] `docs/` index and detail pages are updated?
- [ ] Root `README.md` is updated?
- [ ] All version numbers match exactly?

## 5. Git Operations (Agent Rules)

Strictly follow the rules defined in `.github/copilot-instructions.md` → **Git Operations (Agent Rules)** section.
