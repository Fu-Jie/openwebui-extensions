# OpenWebUI Extensions — Gemini CLI Project Context

> This file is loaded automatically by Gemini CLI as project-level instructions.
> Full engineering spec: `.github/copilot-instructions.md`

---

## Project Overview

**openwebui-extensions** is a collection of OpenWebUI plugins authored by Fu-Jie.

Repository: `https://github.com/Fu-Jie/openwebui-extensions`

Plugin types: `actions` / `filters` / `pipes` / `pipelines` / `tools`

---

## Non-Negotiable Rules

1. **No auto-commit.** Never run `git commit`, `git push`, or `gh pr create` unless the user says "发布" / "release" / "commit it". Default output = local file changes only.
2. **No silent failures.** All errors must surface via `__event_emitter__` notification or backend `logging`.
3. **No hardcoded model IDs.** Default to the current conversation model; let `Valves` override.
4. **Chinese responses.** Reply in Simplified Chinese for all planning, explanations, and status summaries. English only for code, commit messages, and docstrings.

---

## Plugin File Contract

Every plugin MUST be a **single-file i18n** Python module:

```text
plugins/{type}/{name}/{name}.py   ← single source file, built-in i18n
plugins/{type}/{name}/README.md   ← English docs
plugins/{type}/{name}/README_CN.md ← Chinese docs
```

### Docstring (required fields)

```python
"""
title: Plugin Display Name
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
version: 0.1.0
description: One-line description.
"""
```

### Required patterns

- `Valves(BaseModel)` with `UPPER_SNAKE_CASE` fields
- `_get_user_context(__user__)` — never access `__user__` directly
- `_get_chat_context(body, __metadata__)` — never infer IDs ad-hoc
- `_emit_status(emitter, msg, done)` / `_emit_notification(emitter, content, type)`
- Async I/O only — wrap sync calls with `asyncio.to_thread`
- `logging` for backend logs — no bare `print()` in production

---

## Antigravity Development Rules

When the user invokes antigravity mode (high-speed iteration), enforce these safeguards automatically:

| Rule | Detail |
|------|--------|
| Small reversible edits | One logical change per file per operation |
| Timeout guards | `asyncio.wait_for(..., timeout=2.0)` on all `__event_call__` JS executions |
| Path sandbox | Verify every workspace path stays inside the repo root before read/write |
| Fallback chains | API upload → DB + local copy; never a single point of failure |
| Progressive status | `status(done=False)` at start, `status(done=True)` on end, `notification(error)` on failure |
| Validate before emit | Check `emitter is not None` before every `await emitter(...)` |

---

## File Creation & Delivery Protocol (3-Step)

1. `local write` — create artifact inside workspace scope
2. `publish_file_from_workspace(filename='...')` — migrate to OpenWebUI storage (S3-compatible)
3. Return `/api/v1/files/{id}/content` download link in Markdown

Set `skip_rag=true` metadata on generated downloadable artifacts.

---

## Copilot SDK Tool Definition (critical)

```python
from pydantic import BaseModel, Field
from copilot import define_tool

class MyToolParams(BaseModel):
    query: str = Field(..., description="Search query")

my_tool = define_tool(
    name="my_tool",
    description="...",
    params_type=MyToolParams,   # REQUIRED — prevents empty schema hallucination
)(async_impl_fn)
```

---

## Streaming Output Format (OpenWebUI 0.8.x)

- Reasoning: `<think>\n...\n</think>\n` — close BEFORE normal content or tool cards
- Tool cards: `<details type="tool_calls" id="..." name="..." arguments="&quot;...&quot;" result="&quot;...&quot;" done="true">\n<summary>Tool Executed</summary>\n</details>\n\n`
- Escape ALL `"` inside `arguments`/`result` attributes as `&quot;`
- Status events via `__event_emitter__` — do NOT pollute the content stream with debug text

---

## Documentation Sync (when changing a plugin)

Must update ALL of these or the PR check fails:

1. `plugins/{type}/{name}/{name}.py` — version in docstring
2. `plugins/{type}/{name}/README.md` — version, What's New
3. `plugins/{type}/{name}/README_CN.md` — same
4. `docs/plugins/{type}/{name}.md` — mirror README
5. `docs/plugins/{type}/{name}.zh.md` — mirror README_CN
6. `docs/plugins/{type}/index.md` — version badge
7. `docs/plugins/{type}/index.zh.md` — version badge

---

## i18n & Language Standards

1. **Alignment**: Keep the number of supported languages in `TRANSLATIONS` consistent with major plugins (e.g., `smart-mind-map`).
2. **Supported Languages**: en-US, zh-CN, zh-HK, zh-TW, ko-KR, ja-JP, fr-FR, de-DE, es-ES, it-IT, vi-VN, id-ID.
3. **Fallback Map**: Must include variant redirects (e.g., `es-MX` -> `es-ES`, `fr-CA` -> `fr-FR`).
4. **Tooltips**: All `description` fields in `Valves` must be **English only** to maintain clean UI.

---

## Commit Message Format

```text
type(scope): brief English description

- Key change 1
- Key change 2
```

Types: `feat` / `fix` / `docs` / `refactor` / `chore`
Scope: plugin folder name (e.g., `github-copilot-sdk`)

---

## Full Reference

`.github/copilot-instructions.md` — complete engineering specification (1000+ lines)
`.agent/workflows/plugin-development.md` — step-by-step development workflow
`.agent/rules/antigravity.md` — antigravity mode detailed rules
`docs/development/copilot-engineering-plan.md` — design baseline
