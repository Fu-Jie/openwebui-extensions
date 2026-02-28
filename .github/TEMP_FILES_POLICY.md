# Temporary Files Handling Policy

**Last Updated**: 2026-02-26  
**Status**: Active Guideline

## Overview

All temporary files created during skill execution or development workflows must follow this centralized policy to maintain project cleanliness and workspace isolation alignment.

## Core Rule

**Temporary files MUST be stored in the project's `.temp/` directory, NOT in system directories like `/tmp`.**

## Rationale

1. **Workspace Isolation**: Aligns with OpenWebUI's workspace-per-user model
2. **Project Cohesion**: All project artifacts (temporary or permanent) stay within project boundaries
3. **Multi-User Safety**: Avoids conflicts between multiple developers using the same system
4. **Cleanup Traceability**: Easy to verify all temp files are cleaned up via single `.temp/` directory
5. **Debugging**: Inspectable before deletion if issues occur

## Usage Pattern

### Creating Temp File

```bash
# Step 1: Ensure temp directory exists
mkdir -p .temp

# Step 2: Write temp file
cat > .temp/my_temp_file.md << 'EOF'
...content...
EOF

# Step 3: Use the file in your workflow
# (e.g., pass to gh CLI, process with script, etc.)
```

### Cleanup After Use

```bash
# Remove individual temp files
rm -f .temp/my_temp_file.md

# Or full cleanup of entire temp directory
rm -rf .temp/
```

## Skills Affected

| Skill | Implementation | Status |
|-------|----------------|--------|
| `pr-submitter` | PR body file (`.temp/pr_body.md`) | ✅ Updated |
| `release-prep` | Draft notes (if any) | ✅ Policy Added |
| `version-bumper` | Backup files (if any) | ℹ️ Check needed |
| Future skills | TBD | 📋 Must follow policy |

## .gitignore Configuration

The following entry in `.gitignore` ensures temp files are never committed:

```
# Temporary files
.temp/
.build/
```

## Examples

### Example 1: PR Submitter Skill

```bash
# Create PR body in temp directory
mkdir -p .temp
cat > .temp/pr_body.md << 'EOF'
## Summary
New feature implementation
EOF

# Use with gh CLI
gh pr create --body-file .temp/pr_body.md --title "feat: new feature"

# Cleanup
rm -f .temp/pr_body.md
```

### Example 2: Release Prepare Workflow

```bash
# Create draft changelog
mkdir -p .temp
cat > .temp/changelog_draft.md << 'EOF'
# v1.0.0 Release Notes
EOF

# Edit, validate, then integrate into real files
# ...

# Cleanup
rm -f .temp/changelog_draft.md
```

## Anti-Patterns (❌ Don't Do This)

- ❌ Writing temp files to `/tmp` — will be lost/orphaned
- ❌ Writing to root directory or `plugins/` — pollutes repo
- ❌ Not cleaning up temp files — accumulates clutter
- ❌ Committing `.temp/` files to git — defeats the purpose
- ❌ Using absolute paths — breaks workflow portability

## Enforcement

1. **Code Review**: PRs should verify no `/tmp` references in scripts
2. **CI/CD**: Setup can validate `.temp/` cleanup via git status before commit
3. **Documentation**: All skill docs must reference this policy (link to this file)
4. **Automated**: Consider adding pre-commit hook to ensure `.temp/` is not staged

## Questions / Clarifications

For questions about this policy, refer to:

- `.github/skills/pr-submitter/SKILL.md` — Practical example
- `.github/skills/release-prep/SKILL.md` — Policy integration
- `/memories/repo/temp-file-handling-convention.md` — Internal notes
