---
name: release-finalizer
description: Merges a release PR, associates it with resolved issues, replies to issue reporters, and closes issues. Use after PR review is complete and ready for merge. Closes the release cycle.
---

# Release Finalizer

## Overview

This skill completes the final step of the release cycle: merging the release PR to `main`, replying to all related issues with solutions, and automatically closing them using GitHub's issue linking mechanism.

## Prerequisites

- The PR is in `OPEN` state and ready to merge
- All status checks have passed (CI green)
- All review feedback has been addressed
- The PR relates to one or more GitHub issues (either in PR description or through commits)

---

## Workflow

### Step 1 — Pre-Merge Verification

Verify that the PR is ready:

```bash
PAGER=cat GH_PAGER=cat gh pr view <PR-NUMBER> --json state,statusCheckRollup,reviewDecision
```

Checklist:
- ✅ `state` is `OPEN`
- ✅ `statusCheckRollup` all have `conclusion: SUCCESS`
- ✅ `reviewDecision` is `APPROVED` or empty (no blocking reviews)

If any check fails, **do NOT merge**. Report the issue to the user.

### Step 2 — Identify Related Issues

Issues can be linked to a PR in multiple ways. Check the PR description and commit messages for keywords:

```bash
PAGER=cat GH_PAGER=cat gh pr view <PR-NUMBER> --json body,commits
```

Look for patterns like:
- `Closes #XX`, `Fixes #XX`, `Resolves #XX` (in description or commit bodies)
- `#XX` mentioned as "related to" or "addresses"

**Manual input**: If issue links are not in the PR, ask the user which issue(s) this PR resolves.

Extract all issue numbers into a list: `[#48, #52, ...]`

### Step 3 — Select Merge Strategy

Offer the user three options:

| Strategy | Git Behavior | Use Case |
|----------|-------------|----------|
| **Squash** | All commits squashed into one commit on main | Clean history, recommended for release PRs |
| **Rebase** | Linear history, no merge commit | Preserve commit granularity |
| **Merge** | Merge commit created | Preserve full PR context |

**Recommendation for release PRs**: Use `--squash` to create a single clean commit.

If user doesn't specify, default to `--squash`.

### Step 4 — Prepare Merge Commit Message

If using `--squash`, craft a single comprehensive commit message:

**Format** (Conventional Commits + Github linking):
```
type(scope): description

- Bullet point 1
- Bullet point 2

Closes #48
Closes #52
```

The `Closes #XX` keyword tells GitHub to automatically close those issues when the commit lands on `main`.

Example:
```
feat(pipes,filters): release Copilot SDK Pipe v0.8.0 and Files Filter v0.1.3

- Implement P1~P4 conditional tool filtering system
- Fix file publishing reliability across all storage backends
- Add strict file URL validation
- Update bilingual documentation

Closes #48
```

### Step 5 — Execute Merge

```bash
gh pr merge <PR-NUMBER> \
  --squash \
  --delete-branch \
  -m "type(scope): description" \
  -b "- Bullet 1\n- Bullet 2\n\nCloses #48"
```

**Key flags:**
- `--squash`: Squash commits (recommended for releases)
- `--delete-branch`: Delete the feature branch after merge
- `-m`: Commit subject
- `-b`: Commit body (supports `\n` for newlines)

Confirm the merge is successful; GitHub will automatically close related issues with `Closes #XX` keyword.

### Step 6 — Verify Auto-Close

GitHub automatically closes issues when a commit with `Closes #XX` lands on the default branch (`main`).

To verify:
```bash
PAGER=cat GH_PAGER=cat gh issue view <ISSUE-NUMBER> --json state
```

Should show `state: CLOSED`.

### Step 7 — Post Closing Message (Optional but Recommended)

For better UX, manually post a summary comment to **each issue** before it auto-closes (since auto-close happens silently):

```bash
gh issue comment <ISSUE-NUMBER> --body "
This has been fixed in PR #<PR-NUMBER>, which is now merged to main.

**Solution Summary:**
- <Key fix 1>
- <Key fix 2>

The fix will be available in the next plugin release. Thank you for reporting! ⭐
"
```

### Step 8 — (Optional) Regenerate Release Notes

If the merge revealed any final tweaks to release notes:

```bash
# Re-export release notes from merged commit
git log --oneline -1 <merged-commit-sha>
```

If needed, create a follow-up PR with doc polish (do NOT force-push the merged commit).

---

## Merge Strategy Decision Tree

```
Is this a patch/hotfix release?
├─ YES → Use --squash
└─ NO → Multi-feature release?
     ├─ YES → Use --squash (cleaner history)
     └─ NO → Preserve detail? 
          ├─ YES → Use --rebase
          └─ NO → Use --merge (preserve PR context)
```

---

## Issue Auto-Close Keywords

These keywords in commit/PR messages will auto-close issues when merged to `main`:

- `Closes #XX`
- `Fixes #XX`
- `Resolves #XX`
- `close #XX` (case-insensitive)
- `fix #XX`
- `resolve #XX`

**Important**: The keyword must be on the **final commit that lands on** `main`. For squash merges, it must be in the squash commit message body.

---

## Anti-Patterns to Avoid

- ❌ Do NOT merge if any status checks are PENDING or FAILED
- ❌ Do NOT merge if there are blocking reviews (reviewDecision: `CHANGES_REQUESTED`)
- ❌ Do NOT merge without verifying the Conventional Commits format in the merge message
- ❌ Do NOT merge without including `Closes #XX` keywords for all related issues
- ❌ Do NOT assume issues will auto-close silently — post a courtesy comment first
- ❌ Do NOT delete the branch if it might be needed for cherry-pick or hotfixes later

---

## Troubleshooting

### Issue did not auto-close after merge
- Verify the `Closes #XX` keyword is in the **final commit message** (use `git log` to check)
- Ensure the commit is on the `main` branch
- GitHub sometimes takes a few seconds to process; refresh the issue page

### Multiple issues to close
- List all in separate `Closes #XX` lines in the commit body
- Each one will be independently auto-closed

### Want to close issue without merge?
- Use `gh issue close <ISSUE-NUMBER>` manually
- Only recommended if the PR was manually reverted or deemed invalid
