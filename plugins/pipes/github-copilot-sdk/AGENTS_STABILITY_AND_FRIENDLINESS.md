# 🧭 Agents Stability & Friendliness Guide

This guide focuses on how to improve **reliability** and **user experience** of agents in `github_copilot_sdk.py`.

---

## 1) Goals

- Reduce avoidable failures (timeouts, tool-call dead ends, invalid outputs).
- Keep responses predictable under stress (large context, unstable upstream, partial tool failures).
- Make interaction friendly (clear progress, clarification before risky actions, graceful fallback).
- Preserve backwards compatibility while introducing stronger defaults.

---

## 2) Stability model (4 layers)

## Layer A — Input safety

- Validate essential runtime context early (user/chat/model/tool availability).
- Use strict parsing for JSON-like user/task config (never trust raw free text).
- Add guardrails for unsupported mode combinations (e.g., no tools + tool-required task).

**Implementation hints**
- Add preflight validator before `create_session`.
- Return fast-fail structured errors with recovery actions.

## Layer B — Session safety

- Use profile-driven defaults (`model`, `reasoning_effort`, `infinite_sessions` thresholds).
- Auto-fallback to safe profile when unknown profile is requested.
- Isolate each chat in a deterministic workspace path.

**Implementation hints**
- Add `AGENT_PROFILE` + fallback to `default`.
- Keep `infinite_sessions` enabled by default for long tasks.

## Layer C — Tool-call safety

- Add `on_pre_tool_use` to validate and sanitize args.
- Add denylist/allowlist checks for dangerous operations.
- Add timeout budget per tool class (file/network/shell).

**Implementation hints**
- Keep current `on_post_tool_use` behavior.
- Extend hooks gradually: `on_pre_tool_use` first, then `on_error_occurred`.

## Layer D — Recovery safety

- Retry only idempotent operations with capped attempts.
- Distinguish recoverable vs non-recoverable failures.
- Add deterministic fallback path (summary answer + explicit limitation).

**Implementation hints**
- Retry policy table by event type.
- Emit "what succeeded / what failed / what to do next" blocks.

---

## 3) Friendliness model (UX contract)

## A. Clarification first for ambiguity

Use `on_user_input_request` for:
- Missing constraints (scope, target path, output format)
- High-risk actions (delete/migrate/overwrite)
- Contradictory instructions

**Rule**: ask once with concise choices; avoid repeated back-and-forth.

## B. Progress visibility

Emit status in major phases:
1. Context check
2. Planning/analysis
3. Tool execution
4. Verification
5. Final result

**Rule**: no silent waits > 8 seconds.

## C. Friendly failure style

Every failure should include:
- what failed
- why (short)
- what was already done
- next recommended action

## D. Output readability

Standardize final response blocks:
- `Outcome`
- `Changes`
- `Validation`
- `Limitations`
- `Next Step`

---

## 4) High-value features to add (priority)

## P0 (immediate)

1. `on_user_input_request` handler with default answer strategy
2. `on_pre_tool_use` for argument checks + risk gates
3. Structured progress events (phase-based)

## P1 (short-term)

4. Error taxonomy + retry policy (`network`, `provider`, `tool`, `validation`)
5. Profile-based session factory with safe fallback
6. Auto quality gate for final output sections

## P2 (mid-term)

7. Transport flexibility (`cli_url`, `use_stdio`, `port`) for deployment resilience
8. Azure provider path completion
9. Foreground session lifecycle support for advanced multi-session control

---

## 5) Suggested valves for stability/friendliness

- `AGENT_PROFILE`: `default | builder | analyst | reviewer`
- `ENABLE_USER_INPUT_REQUEST`: `bool`
- `DEFAULT_USER_INPUT_ANSWER`: `str`
- `TOOL_CALL_TIMEOUT_SECONDS`: `int`
- `MAX_RETRY_ATTEMPTS`: `int`
- `ENABLE_SAFE_TOOL_GUARD`: `bool`
- `ENABLE_PHASE_STATUS_EVENTS`: `bool`
- `ENABLE_FRIENDLY_FAILURE_TEMPLATE`: `bool`

---

## 6) Failure playbooks (practical)

## Playbook A — Provider timeout

- Retry once if request is idempotent.
- Downgrade reasoning effort if timeout persists.
- Return concise fallback and preserve partial result.

## Playbook B — Tool argument mismatch

- Block execution in `on_pre_tool_use`.
- Ask user one clarification question if recoverable.
- Otherwise skip tool and explain impact.

## Playbook C — Large output overflow

- Save large output to workspace file.
- Return file path + short summary.
- Avoid flooding chat with huge payload.

## Playbook D — Conflicting user instructions

- Surface conflict explicitly.
- Offer 2-3 fixed choices.
- Continue only after user selection.

---

## 7) Metrics to track

- Session success rate
- Tool-call success rate
- Average recovery rate after first failure
- Clarification rate vs hallucination rate
- Mean time to first useful output
- User follow-up dissatisfaction signals (e.g., “not what I asked”)

---

## 8) Minimal rollout plan

1. Add `on_user_input_request` + `on_pre_tool_use` (feature-gated).
2. Add phase status events and friendly failure template.
3. Add retry policy + error taxonomy.
4. Add profile fallback and deployment transport options.
5. Observe metrics for 1-2 weeks, then tighten defaults.

---

## 9) Quick acceptance checklist

- Agent asks clarification only when necessary.
- No long silent period without status updates.
- Failures always include next actionable step.
- Unknown profile/provider config does not crash session.
- Large outputs are safely redirected to file.
- Final response follows a stable structure.
