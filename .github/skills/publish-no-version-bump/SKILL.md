---
name: publish-no-version-bump
description: Commit and push code to GitHub, then publish to OpenWebUI official marketplace without updating version. Use when fixing bugs or optimizing performance that doesn't warrant a version bump.
---

# Publish Without Version Bump

## Overview

This skill handles the workflow for pushing code changes to the remote repository and syncing them to the OpenWebUI official marketplace **without incrementing the plugin version number**.

This is useful for:
- Bug fixes and patches
- Performance optimizations
- Code refactoring
- Documentation fixes
- Linting and code quality improvements

## When to Use

Use this skill when:
- You've made non-breaking changes (bug fixes, optimizations, refactoring)
- The functionality hasn't changed significantly
- The user-facing behavior is unchanged or only improved
- There's no need to bump the semantic version

**Do NOT use** if:
- You're adding new features → use `release-prep` instead
- You're making breaking changes → use `release-prep` instead
- The version should be incremented → use `version-bumper` first

## Workflow

### Step 1 — Stage and Commit Changes

Ensure all desired code changes are staged in git:

```bash
git status  # Verify what will be committed
git add -A  # Stage all changes
```

Create a descriptive commit message using Conventional Commits format:

```
fix(plugin-name): brief description
- Detailed change 1
- Detailed change 2
```

Example commit types:
- `fix:` — Bug fixes, patches
- `perf:` — Performance improvements, optimization
- `refactor:` — Code restructuring without behavior change
- `test:` — Test updates
- `docs:` — Documentation changes

**Key Rule**: The commit message should make clear that this is NOT a new feature release (no `feat:` type).

### Step 2 — Push to Remote

Push the commit to the main branch:

```bash
git commit -m "<message>" && git push
```

Verify the push succeeded by checking GitHub.

### Step 3 — Publish to Official Marketplace

Run the publish script with `--force` flag to update the marketplace without version change:

```bash
python scripts/publish_plugin.py --force
```

**Important**: The `--force` flag ensures the marketplace version is updated even if the version string in the plugin file hasn't changed.

### Step 4 — Verify Publication

Check that the plugin was successfully updated in the official marketplace:
1. Visit https://openwebui.com/f/
2. Search for your plugin name
3. Verify the code is up-to-date
4. Confirm the version number **has NOT changed**

---

## Command Reference

### Full Workflow (Manual)

```bash
# 1. Stage and commit
git add -A
git commit -m "fix(copilot-sdk): description here"

# 2. Push
git push

# 3. Publish to marketplace
python scripts/publish_plugin.py --force

# 4. Verify
# Check OpenWebUI marketplace for the updated code
```

### Automated (Using This Skill)

When you invoke this skill with a plugin path, Copilot will:
1. Verify staged changes and create the commit
2. Push to the remote repository
3. Execute the publish script
4. Report success/failure status

---

## Implementation Notes

### Version Handling

- The plugin's version string in `docstring` (line ~10) remains **unchanged**
- The `openwebui_id` in the plugin file must be present for the publish script to work
- If the plugin hasn't been published before, use `publish_plugin.py --new <dir>` instead

### Dry Run

To preview what would be published without actually updating the marketplace:

```bash
python scripts/publish_plugin.py --force --dry-run
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `Error: openwebui_id not found` | The plugin hasn't been published yet. Use `publish_plugin.py --new <dir>` for first-time publishing. |
| `Failed to authenticate` | Check that the `OPENWEBUI_API_KEY` environment variable is set. |
| `Skipped (version unchanged)` | This is normal. Without `--force`, unchanged versions are skipped. We use `--force` to override this. |

---

## Related Skills

- **`release-prep`** — Use when you need to bump the version and create release notes
- **`version-bumper`** — Use to manually update version across all 7+ files
- **`pr-submitter`** — Use to create a PR instead of pushing directly to main

