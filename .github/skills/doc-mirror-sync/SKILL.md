---
name: doc-mirror-sync
description: Automatically synchronizes plugin READMEs to the official documentation directory (docs/). Use after editing a plugin's local documentation to keep the MkDocs site up to date.
---

# Doc Mirror Sync

## Overview
Automates the mirroring of `plugins/{type}/{name}/README.md` to `docs/plugins/{type}/{name}.md`.

## Workflow
1. Identify changed READMEs.
2. Copy content to corresponding mirror paths.
3. Update version badges in `docs/plugins/{type}/index.md`.
