# Implementation Plan (Current)

## 1. Objective

Define an engineering-ready design baseline for OpenWebUI plugin development that:

- uses GitHub Copilot as the primary coding agent,
- supports Gemini CLI as a secondary execution/research lane,
- adopts antigravity development mode for reversible, low-risk iteration.

## 2. Current Decision

The active design document is:

- `docs/development/copilot-engineering-plan.md`
- `docs/development/copilot-engineering-plan.zh.md`

This file is retained as a stable pointer to avoid design drift.

## 3. Engineering Baseline

- Single-file i18n plugin code architecture.
- Bilingual documentation contract.
- Copilot SDK tool schema discipline (`params_type`).
- Gemini CLI output normalization before merge.
- Workspace file sandbox + publish protocol.
- Streaming compatibility with native `<think>` and `<details type="tool_calls">`.

## 4. File Creation & Delivery Baseline

- Create artifacts in workspace-scoped paths.
- Publish artifacts via workspace publish flow.
- Return and display `/api/v1/files/{id}/content` links for delivery.

## 5. Maintenance Rule

Any update to plugin engineering standards must be reflected in:

1. `docs/development/copilot-engineering-plan.md`
2. `docs/development/copilot-engineering-plan.zh.md`
3. `docs/development/plugin-guide.md`
4. `docs/development/plugin-guide.zh.md`

---

Updated: 2026-02-23
