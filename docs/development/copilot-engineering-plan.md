# Copilot Engineering Configuration Plan

> This document defines production-grade engineering configuration for plugin development with GitHub Copilot, Gemini CLI, and antigravity development mode.

---

## 1. Goals

- Standardize plugin engineering workflow for AI-assisted development.
- Support dual assistant stack:
  - GitHub Copilot (primary in-editor agent)
  - Gemini CLI (secondary external execution/research lane)
- Introduce antigravity development mode for safer, reversible, high-velocity iteration.

---

## 2. Scope

This plan applies to:

- Plugin development (`actions`, `filters`, `pipes`, `pipelines`, `tools`)
- Documentation synchronization
- File generation/delivery workflow in OpenWebUI
- Streaming/tool-call rendering compatibility

---

## 3. Engineering Configuration (Copilot-centered)

### 3.1 Source of truth

- Primary standard file: `.github/copilot-instructions.md`
- Agent workflow file: `.agent/workflows/plugin-development.md`
- Runtime guidance docs:
  - `docs/development/plugin-guide.md`
  - `docs/development/plugin-guide.zh.md`

### 3.2 Required development contract

- Single-file i18n plugin source.
- Bilingual README (`README.md` + `README_CN.md`).
- Safe context extraction (`_get_user_context`, `_get_chat_context`).
- Structured event handling (`status`, `notification`, `execute`).
- No silent failures; logging + user-visible status.

### 3.3 Tool definition contract (Copilot SDK)

- Define tool params explicitly with `pydantic.BaseModel`.
- Use `params_type` in tool registration.
- Preserve defaults by avoiding forced null overrides.
- Keep tool names normalized and deterministic.

---

## 4. Gemini CLI Compatibility Profile

Gemini CLI is treated as a parallel capability channel, not a replacement.

### 4.1 Usage boundary

- Use for:
  - rapid drafts
  - secondary reasoning
  - cross-checking migration plans
- Do not bypass repository conventions or plugin contracts.

### 4.2 Output normalization

All Gemini CLI outputs must be normalized before merge:

- Match repository style and naming rules.
- Preserve OpenWebUI plugin signatures and context methods.
- Convert speculative outputs into explicit, testable implementation points.

### 4.3 Conflict policy

When Copilot and Gemini suggestions differ:

1. Prefer repository standard compliance.
2. Prefer safer fallback behavior.
3. Prefer lower integration risk.

---

## 5. Antigravity Development Mode

Antigravity mode means high-speed delivery with strict reversibility.

### 5.1 Core principles

- Small, isolated edits
- Deterministic interfaces
- Multi-level fallback paths
- Roll-forward and rollback both feasible

### 5.2 Required patterns

- Timeout guards on frontend execution calls.
- Path sandbox validation for all workspace file operations.
- Dual-channel upload fallback (API first, local/DB fallback).
- Progressive status reporting for long-running tasks.

---

## 6. File Creation & Delivery Standard

### 6.1 Create files in controlled workspace

- Write artifacts in current workspace scope.
- Never use paths outside workspace boundary for deliverables.

### 6.2 Publish protocol

Use 3-step delivery:

1. local write
2. publish from workspace
3. present `/api/v1/files/{id}/content` link

### 6.3 Metadata policy

- Set `skip_rag=true` for generated downloadable artifacts where applicable.
- Keep filename generation deterministic (`chat_title -> markdown_title -> user+date`).

---

## 7. Plugin Development Norms for Multi-Agent Stack

- Compatible with GitHub Copilot and Gemini CLI under same coding contract.
- Keep streaming compatible with OpenWebUI native blocks (`<think>`, `<details type="tool_calls">`).
- Escape tool card attributes safely (`&quot;`) for parser stability.
- Preserve async non-blocking behavior.

---

## 8. Documentation Sync Rule

Any meaningful plugin engineering change must sync:

1. plugin code
2. plugin bilingual README
3. docs plugin detail pages (EN/ZH)
4. docs plugin indexes (EN/ZH)
5. root README update badge/date when release is prepared

---

## 9. Acceptance Checklist

- Copilot config and workflow references are valid.
- Gemini CLI outputs can be merged without violating conventions.
- Antigravity safety mechanisms are present.
- File creation and publication flow is reproducible.
- Streaming/tool-card output format remains OpenWebUI-compatible.
