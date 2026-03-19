# `.agent/learnings/` — Engineering Learnings & Reusable Patterns

This directory stores **hard-won engineering insights** discovered during development.
Each file is a standalone Markdown note covering a specific topic, pattern, or gotcha.

The goal is to avoid re-investigating the same issue twice.

---

## Conventions

- **File naming**: `{topic}.md`, e.g., `openwebui-tool-injection.md`
- **Scope**: One clear topic per file. Keep files focused and concise.
- **Format**: Use the template below.

---

## Template

```markdown
# [Topic Title]

> Discovered: YYYY-MM-DD

## Context
Where / when does this apply?

## Finding
What exactly did we learn?

## Solution / Pattern
The code or approach that works.

## Gotchas
Edge cases or caveats to watch out for.
```

---

## Index

| File | Topic |
|------|-------|
| [openwebui-tool-injection.md](./openwebui-tool-injection.md) | How OpenWebUI injects parameters into Tool functions, and what the Pipe must provide |
| [openwebui-mock-request.md](./openwebui-mock-request.md) | How to build a valid Mock Request for calling OpenWebUI-internal APIs from a Pipe |
| [copilot-plan-mode-prompt-parity.md](./copilot-plan-mode-prompt-parity.md) | Why Plan Mode prompt logic must be shared between fresh-session and resume-session injection |
| [richui-default-actions-optout.md](./richui-default-actions-optout.md) | How static RichUI widgets opt out of fallback prompt/link action injection |
| [richui-declarative-priority.md](./richui-declarative-priority.md) | How RichUI resolves priority between declarative actions and inline click handlers |
| [richui-interaction-api.md](./richui-interaction-api.md) | Recommended 4-action RichUI interaction contract for chat continuation, prefill, submit, and links |
