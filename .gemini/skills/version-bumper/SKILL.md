---
name: version-bumper
description: Automates version upgrades and changelog synchronization across 7+ files (Code, READMEs, Docs). Use when a plugin is ready for release to ensure version consistency.
---

# Version Bumper

## Overview
This skill ensures that every version upgrade is synchronized across the entire repository, following the strict "Documentation Sync" rule in GEMINI.md.

## Workflow
1. **Prepare Info**: Gather the new version number and brief changelogs in both English and Chinese.
2. **Auto-Patch**: The skill will help you identify and update:
   - `plugins/.../name.py` (docstring version)
   - `plugins/.../README.md` (metadata & What's New)
   - `plugins/.../README_CN.md` (metadata & 最新更新)
   - `docs/plugins/...md` (mirrors)
   - `docs/plugins/index.md` (version badge)
   - `README.md` (updated date badge)
3. **Verify**: Check the diffs to ensure no formatting was broken.

## Tool Integration
Execute the bump script (draft):
```bash
python3 scripts/bump.py <version> "<message_en>" "<message_zh>"
```
