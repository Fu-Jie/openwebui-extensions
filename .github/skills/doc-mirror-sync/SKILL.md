---
name: doc-mirror-sync
description: Automatically synchronizes plugin READMEs to the official documentation directory (docs/). Use after editing a plugin's local documentation to keep the MkDocs site up to date.
---

# Doc Mirror Sync

## Overview
Automates the mirroring of `plugins/{type}/{name}/README.md` to `docs/plugins/{type}/{name}.md`.

## Docs-Only Mode (No Release Changes)
Use this mode when the request is "only sync docs".

- Only update documentation mirror files under `docs/plugins/**`.
- Do **not** bump plugin version.
- Do **not** modify plugin code (`plugins/**.py`) unless explicitly requested.
- Do **not** update root badges/dates for release.
- Do **not** run release preparation steps.

## Workflow
1. Identify changed READMEs.
2. Copy content to corresponding mirror paths.
3. Update version badges in `docs/plugins/{type}/index.md`.

## Commands

### Sync all mirrors (EN + ZH)

```bash
python .github/skills/doc-mirror-sync/scripts/sync.py
```

### Sync only one plugin (EN only)

```bash
cp plugins/<type>/<name>/README.md docs/plugins/<type>/<name>.md
```

### Sync only one plugin (EN + ZH)

```bash
cp plugins/<type>/<name>/README.md docs/plugins/<type>/<name>.md
cp plugins/<type>/<name>/README_CN.md docs/plugins/<type>/<name>.zh.md
```

## Notes

- If asked for English-only update, sync only `README.md` -> `.md` mirror.
- If both languages are requested, sync both `README.md` and `README_CN.md`.
- After syncing, verify git diff only contains docs file changes.
