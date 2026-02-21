# Plugin Release Workflow

This document describes the workflow for releasing plugin updates.

---

## Overview

The release workflow consists of the following components:

1. **CHANGELOG.md** - Records all notable changes
2. **Version Extraction Script** - Automatically extracts plugin versions
3. **GitHub Actions Workflows** - Automates the release process

---

## Automatic Release Process ⭐

When a plugin update PR is merged to `main` branch, the release process is **triggered automatically**:

### PR Merge Requirements

PRs that modify plugin files must meet the following conditions to merge:

1. ✅ **Version must be updated** - The plugin's `version` field must be changed
2. ✅ **PR description must contain update notes** - At least 20 characters of description

If these conditions are not met, the PR check will fail and cannot be merged.

### Automatic Release Contents

After successful merge, the system will automatically:

1. 🔍 Detect version changes (compared to last release)
2. 📝 Generate release notes (with update content and commit history)
3. 📦 Create GitHub Release (with downloadable plugin files)
4. 🏷️ Auto-generate version number (format: `vYYYY.MM.DD-run_number`)

### Release Includes

- **plugins_release.zip** - All updated plugin files packaged
- **plugin_versions.json** - All plugin version information (JSON format)
- **Release Notes** - Includes:
  - List of new/updated plugins
  - Related commit history
  - Complete plugin version table
  - Installation instructions

---

## Release Process

### Step 1: Update Plugin Version

When you make changes to a plugin, you **must** update the version number:

```python
"""
title: My Plugin
author: Fu-Jie
version: 0.2.0  # <- Must update this!
...
"""
```

### Step 2: Create PR with Update Notes

Add update notes in your PR description (at least 20 characters):

```markdown
## Changes

- Added XXX feature
- Fixed YYY issue
- Improved ZZZ performance
```

### Step 3: Merge PR

After checks pass, merge the PR to `main` branch - the system will automatically create a Release.

---

## Manual Release (Optional)

In addition to automatic release, you can also trigger manually:

### Option A: Manual Trigger

1. Go to GitHub Actions → "Plugin Release / 插件发布"
2. Click "Run workflow"
3. Fill in the details:
   - **version**: e.g., `v1.0.0` (leave empty for auto-generation)
   - **release_title**: e.g., "Smart Mind Map Major Update"
   - **release_notes**: Additional notes in Markdown
   - **prerelease**: Check if this is a pre-release

### Option B: Tag-based Release

```bash
# Create and push a version tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes

### Examples

| Change Type | Version Change |
|-------------|----------------|
| Bug fix | 0.1.0 → 0.1.1 |
| New feature | 0.1.1 → 0.2.0 |
| Breaking change | 0.2.0 → 1.0.0 |

---

## GitHub Actions Workflows

### release.yml

**Triggers:**
- ⭐ Push to `main` branch with `plugins/**/*.py` changes (auto-release)
- Manual workflow dispatch
- Push of version tags (`v*`)

**Actions:**
1. Detects version changes compared to last release
2. Collects updated plugin files
3. Generates release notes (with commit history)
4. Creates GitHub Release (with downloadable attachments)

### plugin-version-check.yml

**Trigger:**
- Pull requests that modify `plugins/**/*.py`

**Actions:**
1. Compares plugin versions between base and PR
2. Checks if version was updated
3. Checks if PR description is detailed enough
4. ❌ Fails if no version update detected
5. ⚠️ Fails if PR description is too short

---

## Scripts

### extract_plugin_versions.py

Usage:

```bash
# Output to console
python scripts/extract_plugin_versions.py

# Output as JSON
python scripts/extract_plugin_versions.py --json

# Output as Markdown table
python scripts/extract_plugin_versions.py --markdown

# Compare with previous version
python scripts/extract_plugin_versions.py --compare old_versions.json

# Save to file
python scripts/extract_plugin_versions.py --json --output versions.json
```

---

## Best Practices

1. **Always update version numbers** when making functional changes (required)
2. **Write clear PR descriptions** describing what changed and why (required)
3. **Test locally** before creating a PR
4. **Use pre-releases** for testing new features
5. **Reference issues** in PR descriptions

---

## Author

Fu-Jie  
GitHub: [Fu-Jie/openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)
