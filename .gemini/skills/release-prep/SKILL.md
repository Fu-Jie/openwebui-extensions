---
name: release-prep
description: Orchestrates the full release preparation flow for a plugin — version sync across 7+ files, bilingual release notes creation, and commit message drafting. Use before submitting a PR. Does NOT push or create a PR; that is handled by pr-submitter.
---

# Release Prep

## Overview

This skill drives the complete pre-PR release pipeline. It enforces the repository rule that every release must synchronize the version number and changelog across **at least 7 locations** before a commit is created.

## Scope

This skill covers:
1. Version sync (delegates detail to `version-bumper` if needed)
2. Bilingual release notes file creation
3. 7-location consistency verification
4. Conventional Commits message drafting
5. `git add -A && git commit` execution

It **stops before** `git push` or `gh pr create`. Use the `pr-submitter` skill for those steps.

---

## Workflow

### Step 1 — Collect Release Info

Ask the user (or infer from current state) the following:
- **Plugin name** and **type** (actions / filters / pipes / tools)
- **New version number** (e.g., `0.8.0`)
- **Key changes** in English and Chinese (1-5 bullet points each)

If a `What's New` section already exists in README.md, extract it as the source of truth.

### Step 2 — Sync Version Across 7 Locations

Verify AND update the version string in all of the following. Mark each as ✅ or ❌:

| # | File | Location |
|---|------|----------|
| 1 | `plugins/{type}/{name}/{name}.py` | `version:` in docstring |
| 2 | `plugins/{type}/{name}/README.md` | `**Version:** x.x.x` metadata line |
| 3 | `plugins/{type}/{name}/README_CN.md` | `**Version:** x.x.x` metadata line |
| 4 | `docs/plugins/{type}/{name}.md` | `**Version:** x.x.x` metadata line |
| 5 | `docs/plugins/{type}/{name}.zh.md` | `**Version:** x.x.x` metadata line |
| 6 | `docs/plugins/{type}/index.md` | version badge for this plugin |
| 7 | `docs/plugins/{type}/index.zh.md` | version badge for this plugin |

Additionally update the root-level **updated date badge** in:
- `README.md` — `![updated](https://img.shields.io/badge/YYYY--MM--DD-gray?style=flat)`
- `README_CN.md` — same badge format

Use today's date (`YYYY-MM-DD`) for the badge.

### Step 3 — Update What's New (All 4 Doc Files)

The `What's New` / `最新更新` section must contain **only the most recent release's changes**. Previous entries should be removed from this section (they live in CHANGELOG or release notes files).

Update these 4 files' `What's New` / `最新更新` block consistently:
- `plugins/{type}/{name}/README.md`
- `plugins/{type}/{name}/README_CN.md`
- `docs/plugins/{type}/{name}.md`
- `docs/plugins/{type}/{name}.zh.md`

### Step 4 — Create Bilingual Release Notes Files

Create two versioned release notes files:

**Path**: `plugins/{type}/{name}/v{version}.md`
**Path**: `plugins/{type}/{name}/v{version}_CN.md`

#### Required Sections

Each file must include:
0. **Marketplace Badge**: A prominent button linking to the plugin on openwebui.com using shields.io (e.g., `[![](https://img.shields.io/badge/OpenWebUI%20Community-Get%20Plugin-blue?style=for-the-badge)](URL)`).
1. **Overview Header**: Use `## Overview` as the first header.
2. **Summary Paragraph**: A paragraph summarizing the release. **NEVER** include the version number as a title.
3. **README Link**: Direct link to the plugin's README file on GitHub.
4. **New Features** / **新功能**: Bulleted list of features
5. **Bug Fixes** / **问题修复**: Bulleted list of fixes
6. **Related Issues** / **相关 Issue**: Link to GitHub Issues. **ONLY** include if a specific issue is resolved. **NEVER use placeholders.**
7. **Related PRs** / **相关 PR**: Link to the Pull Request. **ONLY** include if the PR is already created and the ID is known. **NEVER use placeholders.**
8. **Migration Notes**: Breaking changes or Valve key renames (omit section if none)

---

## Language Standard

- **Release Notes Files**: Use **English ONLY** for the final `.md` files to maintain professional consistency on GitHub. Avoid bilingual content in the release description.
6. **Companion Plugins** / **配套插件** (optional): If a companion plugin was updated

If a release notes file already exists for this version, update it rather than creating a new one.

### Step 5 — Verify Consistency (Pre-Commit Check)

Run the consistency check script:

```bash
python3 scripts/check_version_consistency.py
```

If issues are found, fix them before proceeding. Do not commit with inconsistencies.

### Step 6 — Draft Conventional Commits Message

Generate the commit message following `commit-message.instructions.md` rules:
- **Language**: English ONLY
- **Format**: `type(scope): subject` + blank line + body bullets
- **Scope**: use plugin folder name (e.g., `github-copilot-sdk`)
- **Body**: 
    - 1-3 bullets summarizing key changes
    - Explicitly mention "READMEs and docs synced" if version was bumped
    - **MUST** end with `Closes #XX` or `Fixes #XX` if an issue is being resolved.

Present the full commit message to the user for review before executing.

### Step 7 — Stage and Commit

After user approval (or if user says "commit it"):

```bash
git add -A
git commit -m "<approved commit message>"
```

Confirm the commit hash and list the number of files changed.

---

## Checklist (Auto-Verify Before Commit)

- [ ] `version:` in `.py` docstring matches target version
- [ ] `**Version:**` in all 4 README/docs files matches
- [ ] Both `index.md` version badges updated
- [ ] Root `README.md` and `README_CN.md` date badges updated to today
- [ ] `What's New` / `最新更新` contains ONLY the latest release
- [ ] `v{version}.md` and `v{version}_CN.md` created or updated
- [ ] `python3 scripts/check_version_consistency.py` returns no errors
- [ ] Commit message is English-only Conventional Commits format

---

## Anti-Patterns to Avoid

- ❌ Do NOT add extra features or refactor code during release prep — only version/doc updates
- ❌ Do NOT push or create PR in this skill — use `pr-submitter`
- ❌ Do NOT use today's date in commit messages; only in badge URLs
- ❌ Do NOT leave stale What's New content from prior versions
