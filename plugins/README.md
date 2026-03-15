# Plugins

English | [中文](./README_CN.md)

This folder is the repository-side hub for plugin source files in OpenWebUI Extensions. If you want the best discovery experience, start with the [Plugin Center](../docs/plugins/index.md) first, then come back here when you want the source tree, local READMEs, or repo-only entries.

## Best Way to Browse

1. Use the [Plugin Center](../docs/plugins/index.md) for curated recommendations and the current catalog
2. Jump into a type folder when you already know you need an Action, Filter, Pipe, Tool, or Pipeline reference
3. Open the local plugin folder when you need the source file, local README, or repo-only notes

## Choose by Goal

| I want to... | Go to | What you'll find |
| --- | --- | --- |
| Create visual or interactive outputs | [Actions](../docs/plugins/actions/index.md) | Mind maps, infographics, flash cards, deep explainers, exports |
| Improve context or output quality | [Filters](../docs/plugins/filters/index.md) | Compression, formatting cleanup, context injection, repo-aware helpers |
| Build autonomous model workflows | [Pipes](../docs/plugins/pipes/index.md) | Advanced model integrations and agent-style behavior |
| Reuse tools across models | [Tools](../docs/plugins/tools/index.md) | Skills management, proactive mind-map generation, batch installation helpers |
| Browse everything from a discovery-first view | [Plugin Center](../docs/plugins/index.md) | Curated picks, current catalog, and repo-only entries |

## Plugin Types

- [Actions](./actions/README.md) — interactive buttons, exports, visualizations, and user-facing chat experiences
- [Filters](./filters/README.md) — message-pipeline logic for context, cleanup, and response shaping
- [Pipes](./pipes/README.md) — model integrations and advanced workflow runtimes
- [Tools](./tools/README.md) — native tools that can be called across models and workflows
- [Pipelines](../docs/plugins/pipelines/index.md) — orchestration-oriented references and historical experiments

## Repository Structure

```text
plugins/
├── actions/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── filters/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── pipes/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── tools/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
└── pipelines/<plugin>/
    └── ...
```

> **Current repo rule:** plugin source stays in a single Python file with built-in i18n. Do **not** split source into separate `_cn.py` files.

## Repo-only Entries

Some items may appear in the repository before a mirrored docs page exists. Right now, notable repo-only entries include:

- `plugins/pipes/iflow-sdk-pipe/`
- `plugins/filters/chat-session-mapping-filter/`

## Installation Paths

1. **OpenWebUI Community** — install directly from [Fu-Jie's profile](https://openwebui.com/u/Fu-Jie)
2. **Docs + repo source** — use the docs pages to choose, then upload the matching `.py` file
3. **Bulk install locally** — run `python scripts/install_all_plugins.py` after setting up `.env`
