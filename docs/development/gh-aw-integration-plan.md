# gh-aw Integration Plan

> This document proposes a safe, incremental adoption plan for GitHub Agentic Workflows (`gh-aw`) in the `openwebui-extensions` repository.

---

## 1. Goals

- Add repository-aware AI maintenance without replacing stable script-based CI.
- Use `gh-aw` where natural language reasoning is stronger than deterministic shell logic.
- Preserve the current release, deploy, publish, and stats workflows as the execution backbone.
- Introduce observability, diagnosis, and long-term maintenance memory for repository operations.

---

## 2. Why gh-aw Fits This Repository

This repository already has strong deterministic automation:

- `/.github/workflows/release.yml`
- `/.github/workflows/plugin-version-check.yml`
- `/.github/workflows/deploy.yml`
- `/.github/workflows/publish_plugin.yml`
- `/.github/workflows/community-stats.yml`

Those workflows are good at exact execution, but they do not deeply understand repository policy.

`gh-aw` is a good fit for tasks that require:

- reading code, docs, and PR descriptions together
- applying repository conventions with nuance
- generating structured review comments
- diagnosing failed workflow runs
- keeping long-term maintenance notes across runs

This matches the repository's real needs:

- bilingual documentation synchronization
- plugin code + README + docs consistency
- release-prep validation across many files
- issue and PR maintenance at scale

---

## 3. Non-Goals

The first adoption phase should not:

- replace `release.yml`
- replace `publish_plugin.yml`
- replace MkDocs deployment
- auto-merge or auto-push code changes by default
- grant broad write permissions to the agent

`gh-aw` should begin as a review, diagnosis, and preflight layer.

---

## 4. Adoption Principles

### 4.1 Keep deterministic workflows for execution

Existing YAML workflows remain responsible for:

- release creation
- plugin publishing
- documentation deployment
- version extraction and comparison
- stats generation

### 4.2 Add agentic workflows for judgment

`gh-aw` workflows should focus on:

- policy-aware review
- release readiness checks
- docs drift analysis
- CI failure investigation
- issue triage and response drafting

### 4.3 Default to read-only behavior

Start with minimal permissions and use safe outputs only for controlled comments or issue creation.

### 4.4 Keep the blast radius small

Roll out one workflow at a time, verify output quality, then expand.

---

## 5. Proposed Repository Layout

### 5.1 New files and directories

```text
.github/
├── workflows/
│   ├── release.yml
│   ├── plugin-version-check.yml
│   ├── deploy.yml
│   ├── publish_plugin.yml
│   ├── community-stats.yml
│   ├── aw-pr-maintainer-review.md
│   ├── aw-pr-maintainer-review.lock.yml
│   ├── aw-release-preflight.md
│   ├── aw-release-preflight.lock.yml
│   ├── aw-ci-audit.md
│   ├── aw-ci-audit.lock.yml
│   ├── aw-docs-drift-review.md
│   └── aw-docs-drift-review.lock.yml
├── gh-aw/
│   ├── prompts/
│   │   ├── pr-review-policy.md
│   │   ├── release-preflight-policy.md
│   │   ├── ci-audit-policy.md
│   │   └── docs-drift-policy.md
│   ├── schemas/
│   │   └── review-output-example.json
│   └── README.md
└── copilot-instructions.md
```

### 5.2 Naming convention

Use an `aw-` prefix for all agentic workflow source files:

- `aw-pr-maintainer-review.md`
- `aw-release-preflight.md`
- `aw-ci-audit.md`
- `aw-docs-drift-review.md`

Reasons:

- clearly separates agentic workflows from existing handwritten YAML workflows
- keeps `gh-aw` assets easy to search
- avoids ambiguity during debugging and release review

### 5.3 Why not replace `.yml` files

The current workflows are production logic. `gh-aw` should complement them first, not absorb their responsibility.

---

## 6. Recommended Workflow Portfolio

### 6.1 Phase 1: PR Maintainer Review

**File**: `/.github/workflows/aw-pr-maintainer-review.md`

**Purpose**:

- review PRs that touch plugins, docs, or development guidance
- comment on missing repository-standard updates
- act as a semantic layer on top of `plugin-version-check.yml`

**Checks to perform**:

- plugin version updated when code changes
- `README.md` and `README_CN.md` both updated when required
- docs mirror pages updated when required
- root README badge/date update needed for release-related changes
- i18n and helper-method standards followed for plugin code
- Conventional Commit quality in PR title/body if relevant

**Suggested permissions**:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

**Suggested tools**:

- `github:` read-focused issue/PR/repo tools
- `bash:` limited read commands only
- `edit:` disabled in early phase
- `agentic-workflows:` optional only after adoption matures

### 6.2 Phase 1: Release Preflight

**File**: `/.github/workflows/aw-release-preflight.md`

**Purpose**:

- run before release or on manual dispatch
- verify release completeness before `release.yml` does packaging and publishing

**Checks to perform**:

- code version and docs versions are aligned
- bilingual README updates exist
- docs plugin mirrors exist and match the release target
- release notes sources exist where expected
- commit message and release draft are coherent

**Output style**:

- summary comment on PR or issue
- optional checklist artifact
- no direct release creation

### 6.3 Phase 2: CI Audit

**File**: `/.github/workflows/aw-ci-audit.md`

**Purpose**:

- inspect failed runs of `release.yml`, `publish_plugin.yml`, `community-stats.yml`, and other important workflows
- summarize likely root cause and next fix steps

**Why gh-aw is strong here**:

- it can use `logs` and `audit` via `gh aw mcp-server`
- it is designed for workflow introspection and post-hoc analysis

### 6.4 Phase 2: Docs Drift Review

**File**: `/.github/workflows/aw-docs-drift-review.md`

**Purpose**:

- periodically inspect whether plugin code, local README files, mirrored docs, and root indexes have drifted apart

**Checks to perform**:

- missing `README_CN.md`
- README sections out of order
- docs page missing after plugin update
- version mismatches across code and docs

### 6.5 Phase 3: Issue Maintainer

**Candidate file**: `/.github/workflows/aw-issue-maintainer.md`

**Purpose**:

- summarize unreplied issues
- propose bilingual responses
- group repeated bug reports by plugin

This should come after the earlier review and audit flows are trusted.

---

## 7. Mapping to Existing Workflows

| Current Workflow | Keep As-Is | gh-aw Companion | Role Split |
|------|------|------|------|
| `/.github/workflows/release.yml` | Yes | `aw-release-preflight.md` | `release.yml` executes; `gh-aw` judges readiness |
| `/.github/workflows/plugin-version-check.yml` | Yes | `aw-pr-maintainer-review.md` | hard gate + semantic review |
| `/.github/workflows/deploy.yml` | Yes | none initially | deterministic build and deploy |
| `/.github/workflows/publish_plugin.yml` | Yes | `aw-ci-audit.md` | deterministic publish + failure diagnosis |
| `/.github/workflows/community-stats.yml` | Yes | `aw-ci-audit.md` | deterministic stats + anomaly diagnosis |

---

## 8. Tooling Model

### 8.1 Built-in tools to enable first

For early workflows, prefer a narrow tool set:

```yaml
tools:
  github:
    toolsets: [default]
  bash:
    - echo
    - pwd
    - ls
    - cat
    - head
    - tail
    - grep
    - wc
    - git status
    - git diff
```

Do not enable unrestricted shell access in phase 1.

### 8.2 MCP usage model

Use `gh aw mcp-server` later for:

- workflow `status`
- workflow `compile`
- workflow `logs`
- workflow `audit`
- `mcp-inspect`

This is especially valuable for `aw-ci-audit.md`.

### 8.3 Safe output policy

In early adoption, only allow safe outputs that:

- comment on PRs
- comment on issues
- open a low-risk maintenance issue when explicitly needed

Avoid any automatic code-writing safe outputs at first.

---

## 9. Repo Memory Strategy

`gh-aw` repo memory is a strong fit for this repository, but it should be constrained.

### 9.1 Recommended first use cases

- recurring CI failure signatures
- repeated docs sync omissions
- common reviewer reminders
- issue clusters by plugin name

### 9.2 Recommended configuration shape

- store only `.md` and `.json`
- small patch size limit
- one memory stream per concern

Suggested conceptual layout:

```text
memory/review-notes/*.md
memory/ci-patterns/*.md
memory/issue-clusters/*.json
```

### 9.3 Important caution

Do not store secrets, tokens, or unpublished sensitive data in repo memory.

---

## 10. Rollout Plan

### Phase 0: Preparation

- install `gh-aw` locally for maintainers
- add a short `/.github/gh-aw/README.md`
- document workflow naming and review expectations

### Phase 1: Read-only semantic review

- introduce `aw-pr-maintainer-review.md`
- introduce `aw-release-preflight.md`
- keep outputs limited to summaries and comments

### Phase 2: Diagnostics and memory

- introduce `aw-ci-audit.md`
- enable `agentic-workflows:` where useful
- add constrained `repo-memory` configuration for repeated failure patterns

### Phase 3: Maintenance automation

- add docs drift patrol
- add issue maintenance workflow
- consider limited code-change proposals only after trust is established

---

## 11. Local Maintainer Setup

For local experimentation and debugging:

### 11.1 Install CLI

```bash
curl -sL https://raw.githubusercontent.com/github/gh-aw/main/install-gh-aw.sh | bash
```

### 11.2 Useful commands

```bash
gh aw version
gh aw compile
gh aw status
gh aw run aw-pr-maintainer-review
gh aw logs
gh aw audit <run-id>
```

### 11.3 VS Code MCP integration

A future optional improvement is adding `gh aw mcp-server` to local MCP configuration so workflow introspection tools are available in editor-based agent sessions.

---

## 12. Recommended First Deliverables

Start with these two workflows only:

1. `aw-pr-maintainer-review.md`
2. `aw-release-preflight.md`

This gives the repository the highest-value upgrade with the lowest operational risk.

---

## 13. Success Criteria

Adoption is working if:

- PR review comments become more specific and repository-aware
- release preparation catches missing docs or version sync earlier
- CI failures produce actionable summaries faster
- maintainers spend less time on repetitive policy review
- deterministic workflows remain stable and unchanged in core behavior

---

## 14. Summary

For `openwebui-extensions`, `gh-aw` should be adopted as an intelligent maintenance layer.

- Keep current YAML workflows for execution.
- Add agentic workflows for policy-aware review and diagnosis.
- Start read-only.
- Expand only after signal quality is proven.

This approach aligns with the repository's existing strengths: strong conventions, bilingual maintenance, plugin lifecycle complexity, and growing repository operations.
