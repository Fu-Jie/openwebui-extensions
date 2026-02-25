---
name: pr-submitter
description: Submits a feature branch as a Pull Request with a validated, properly formatted bilingual PR body. Handles shell-escape-safe body writing via temp files. Use after release-prep has committed all changes.
---

# PR Submitter

## Overview

This skill handles the final step of pushing a feature branch and creating a validated Pull Request on GitHub. Its primary purpose is to avoid the shell-escaping pitfalls (backticks, special characters in `gh pr create --body`) by always writing the PR body to a **temp file** first.

## Prerequisites

- All changes are committed (use `release-prep` skill first)
- The `gh` CLI is authenticated (`gh auth status`)
- Current branch is NOT `main` or `master`

---

## Workflow

### Step 1 — Pre-Flight Checks

Run these checks before any push:

```bash
# 1. Confirm not on protected branch
git branch --show-current

# 2. Verify there are commits to push
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "No remote tracking branch yet"

# 3. Check gh CLI auth
gh auth status
```

If any check fails, stop and report clearly.

### Step 2 — Collect PR Metadata

Gather:
- **PR Title**: Must follow Conventional Commits format, English only (e.g., `feat(github-copilot-sdk): release v0.8.0 with conditional tool filtering`)
- **Target base branch**: Default is `main`
- **Plugin name + version** (to build body sections)
- **Key changes** (reuse from release-prep or the latest What's New section)

### Step 3 — Build PR Body File (Shell-Escape-Safe)

**Always write the body to a temp file.** Never embed multi-line markdown with special characters directly in a shell command.

```bash
cat > /tmp/pr_body.md << 'HEREDOC'
## Summary

Brief one-sentence description of what this PR accomplishes.

## Changes

### New Features
- Feature 1 description
- Feature 2 description

### Bug Fixes
- Fix 1 description

## Plugin Version
- `PluginName` bumped to `vX.X.X`

## Documentation
- README.md / README_CN.md updated
- docs/ mirrors synced

## Testing
- [ ] Tested locally in OpenWebUI
- [ ] i18n validated (all language keys present)
- [ ] Version consistency check passed (`python3 scripts/check_version_consistency.py`)

---

## 变更摘要（中文）

简要描述本次 PR 的改动内容。

### 新功能
- 功能1描述
- 功能2描述

### 问题修复
- 修复1描述
HEREDOC
```

**Critical rules for the body file:**
- Use `<< 'HEREDOC'` (quoted heredoc) to prevent variable expansion
- Keep all backticks literal — they are safe inside a heredoc
- Paths like `/api/v1/files/` are safe too since heredoc doesn't interpret them as commands

### Step 4 — Validate PR Body

Before submitting, verify the body file contains expected sections:

```bash
# Check key sections exist
grep -q "## Summary" /tmp/pr_body.md && echo "✅ Summary" || echo "❌ Summary missing"
grep -q "## Changes" /tmp/pr_body.md && echo "✅ Changes" || echo "❌ Changes missing"
grep -q "## 变更摘要" /tmp/pr_body.md && echo "✅ CN Section" || echo "❌ CN Section missing"

# Preview the body
cat /tmp/pr_body.md
```

Ask the user to confirm the body content before proceeding.

### Step 5 — Push Branch

```bash
git push -u origin $(git branch --show-current)
```

If push is rejected (non-fast-forward), report to user and ask whether to force-push. **Do NOT force-push without explicit confirmation.**

### Step 6 — Create Pull Request

```bash
gh pr create \
  --base main \
  --head $(git branch --show-current) \
  --title "<PR title from Step 2>" \
  --body-file /tmp/pr_body.md
```

Always use `--body-file`, never `--body` with inline markdown.

### Step 7 — Verify PR Creation

```bash
PAGER=cat GH_PAGER=cat gh pr view --json number,url,title,body --jq '{number: .number, url: .url, title: .title, body_preview: .body[:200]}'
```

Confirm:
- PR number and URL
- Title matches intended Conventional Commits format
- Body preview includes key sections (not truncated/corrupted)

If the body appears corrupted (empty sections, missing backtick content), use edit:

```bash
gh pr edit <PR-NUMBER> --body-file /tmp/pr_body.md
```

### Step 8 — Cleanup

```bash
rm -f /tmp/pr_body.md
```

Report final PR URL to the user.

---

## Shell-Escape Safety Rules

| Risk | Safe Approach |
|------|--------------|
| Backticks in `--body` | Write to file, use `--body-file` |
| Paths like `/api/...` | Safe in heredoc; risky in inline `--body` |
| Newlines in `--body` | File-based only |
| `$variable` expansion | Use `<< 'HEREDOC'` (quoted) |
| Double quotes in body | Safe in heredoc file |

---

## Anti-Patterns to Avoid

- ❌ Never use `--body "..."` with multi-line content directly in shell command
- ❌ Never interpolate variables directly into heredoc without quoting the delimiter
- ❌ Never force-push (`--force`) without explicit user confirmation
- ❌ Never target `main` as the source branch (only as base)
- ❌ Never skip the body validation step — a PR with empty body is worse than a delayed PR
