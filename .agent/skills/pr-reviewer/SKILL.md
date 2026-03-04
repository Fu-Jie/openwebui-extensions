---
name: pr-reviewer
description: Fetches PR review comments, analyzes requested changes, implements fixes, commits and pushes the resolution. Use after a reviewer has left comments on an open PR to close the feedback loop efficiently.
---

# PR Reviewer

## Overview

This skill automates the response cycle for code review. When a reviewer leaves comments on a Pull Request, this skill fetches all pending feedback, categorizes issues by severity, implements fixes, and submits a follow-up commit with appropriate review response comments.

## Prerequisites

- An open PR exists with pending review comments
- The local branch matches the PR's head branch
- `gh` CLI is authenticated

---

## Workflow

### Step 1 — Fetch Review State

Retrieve all review comments and overall review status:

```bash
# Get overall review decisions
PAGER=cat GH_PAGER=cat gh pr view <PR-NUMBER> --json reviews,reviewDecision,headRefName \
  --jq '{decision: .reviewDecision, reviews: [.reviews[] | {author: .author.login, state: .state, body: .body}]}'

# Get inline code comments (specific line comments)
PAGER=cat GH_PAGER=cat gh api repos/Fu-Jie/openwebui-extensions/pulls/<PR-NUMBER>/comments \
  --jq '[.[] | {path: .path, line: .line, body: .body, author: .user.login, id: .id}]'

# Get general issue comments
PAGER=cat GH_PAGER=cat gh issue view <PR-NUMBER> --comments --json comments \
  --jq '[.comments[] | {author: .author.login, body: .body}]'
```

Confirm the current local branch matches the PR head:
```bash
git branch --show-current
```
If mismatched, checkout the correct branch first.

### Step 2 — Categorize Review Feedback

Group feedback into categories:

| Category | Examples | Action |
|----------|---------|--------|
| **Code Bug** | Logic error, incorrect variable, broken condition | Fix code immediately |
| **Style / Formatting** | Indentation, naming convention, missing blank line | Fix code |
| **Documentation** | Missing i18n key, wrong version in README, typo | Fix docs |
| **Design Question** | Suggestion to restructure, alternative approach | Discuss with user before implementing |
| **Nitpick / Optional** | Minor style preferences reviewer marked as optional | Fix if quick; document if skipped |
| **Blocking** | Reviewer explicitly blocks merge | Must fix before proceeding |

Present the full categorized list to the user and confirm the resolution plan.

### Step 3 — Implement Fixes

For each accepted fix:

1. Read the affected file at the commented line for context:
   ```bash
   sed -n '<line-5>,<line+10>p' <file-path>
   ```
2. Apply the fix using appropriate file edit tools
3. After editing, verify the specific area looks correct

**For code changes that might affect behavior:**
- Check if tests exist: `ls tests/test_*.py`
- If tests exist, run them: `python -m pytest tests/ -v`

**For documentation fixes:**
- If modifying README.md, check if `docs/` mirror needs the same fix
- Apply the same fix to both locations

### Step 4 — Run Consistency Checks

After all fixes are applied:

```bash
# Version consistency (if any version files were touched)
python3 scripts/check_version_consistency.py

# Quick syntax check for Python files
python3 -m py_compile plugins/{type}/{name}/{name}.py && echo "✅ Syntax OK"
```

### Step 5 — Stage and Commit

Create a new commit (do NOT amend if the branch has already been pushed, to avoid force-push):

```bash
git add -A
git status
```

Draft a Conventional Commits message for the fixup:

Format: `fix(scope): address review feedback`

Body should list what was fixed, referencing reviewer concerns:
```
fix(github-copilot-sdk): address review feedback from @reviewer

- Fix X per review comment on line Y of file Z
- Update README to clarify auth requirement
- Correct edge case in _parse_mcp_servers logic
```

```bash
git commit -m "<fixup commit message>"
```

### Step 6 — Push the Fix Commit

```bash
git push origin $(git branch --show-current)
```

**Force-push policy:**
- Use `git push` (non-force) by default
- Only use `git push --force-with-lease` if:
  1. The user explicitly requests it, AND
  2. The only change is an amended commit squash (cosmetic, no logic change)
  3. Never use `--force` (without `--lease`)

### Step 7 — Respond to Reviewers

For each addressed review comment, post a reply:

```bash
# Reply to inline comment
gh api repos/Fu-Jie/openwebui-extensions/pulls/<PR-NUMBER>/comments/<COMMENT-ID>/replies \
  -X POST -f body="Fixed in commit <SHORT-SHA>. <Brief explanation of what was changed.>"

# General comment to summarize all fixes
gh issue comment <PR-NUMBER> --body "All review feedback addressed in commit <SHORT-SHA>:
- Fixed: <item 1>
- Fixed: <item 2>
Ready for re-review. 🙏"
```

### Step 8 — Re-Request Review (Optional)

If the reviewer had submitted a `CHANGES_REQUESTED` review, request a new review after fixes:

```bash
PAGER=cat GH_PAGER=cat gh api repos/Fu-Jie/openwebui-extensions/pulls/<PR-NUMBER>/requested_reviewers \
  -X POST -f reviewers[]='<reviewer-login>'
```

---

## Decision Guide

### When NOT to implement a suggestion immediately

- **Design questions**: "Should this be a separate class?" — Present to user for decision
- **Optional nitpicks**: Reviewer marked as `nit:` — Ask user if they want to include it
- **Large refactors**: If fix would require changing >50 lines, propose a separate follow-up issue instead

### When to ask the user before proceeding

- Any fix involving behavioral changes to plugin logic
- Renaming Valve keys (breaking change — requires migration notes)
- Changes that affect the bilingual release notes already committed

---

## Anti-Patterns to Avoid

- ❌ Do NOT `git commit --amend` on a pushed commit without user approval for force-push
- ❌ Do NOT silently skip a reviewer's comment; always acknowledge it (implement or explain why not)
- ❌ Do NOT use `--force` (only `--force-with-lease` when absolutely necessary)
- ❌ Do NOT make unrelated changes in the fixup commit; keep scope focused on review feedback
- ❌ Do NOT respond to reviewer comments in Chinese if the PR language context is English
