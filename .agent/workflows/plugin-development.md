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
- **Chat API**: For message updates, follow the "OpenWebUI Chat API 更新规范" in `.github/copilot-instructions.md`.
  - Use Event API for immediate UI updates
  - Use Chat Persistence API for database storage
  - Always update both `messages[]` and `history.messages`

### Commit Messages
- **Language**: **English ONLY**. Do not use Chinese in commit messages.
- **Format**: Conventional Commits (e.g., `feat:`, `fix:`, `docs:`).

## 2. Documentation Updates

When adding or updating a plugin, you **MUST** update the following documentation files to maintain consistency:

### Plugin Directory
- `README.md`: Update version, description, and usage. **Explicitly describe new features in a prominent position at the beginning.**
- `README_CN.md`: Update version, description, and usage. **Explicitly describe new features in a prominent position at the beginning.**

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
1.  **Trigger**: Push to `main` branch with changes in `plugins/**/*.py`.
2.  **Detection**: `scripts/extract_plugin_versions.py` detects changed plugins and compares versions.
3.  **Release**:
    - Generates release notes based on changes.
    - Creates a GitHub Release tag (e.g., `v2024.01.01-1`).
    - Uploads individual `.py` files of **changed plugins only** as assets.
4.  **Market Publishing**:
    - Workflow: `.github/workflows/publish_plugin.yml`
    - Trigger: Release published.
    - Action: Automatically updates the plugin code and metadata on OpenWebUI.com using `scripts/publish_plugin.py`.
    - Requirement: `OPENWEBUI_API_KEY` secret must be set.

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


