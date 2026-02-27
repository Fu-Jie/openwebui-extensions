# Skills Best Practices

A concise guide to writing, organizing, and maintaining Copilot SDK skills effectively.

---

## Understanding How Skills Work

Skills are **not command-line tools**. They are context-injected instruction sets:

1. The Copilot SDK daemon reads every `SKILL.md` file from your `skill_directories`
2. It extracts the YAML `description` field from each skill
3. When the user sends a message, the SDK compares intent against all descriptions
4. If a match is found, the SDK fires `skill.invoked` and **injects the full SKILL.md body** into the conversation as instructions
5. The agent reads those instructions and executes them using `bash`, `create_file`, `view_file`, etc.

**Key implication**: never run a skill's name as a bash command (e.g., `finance-reporting`). The skill IS the instructions, not an executable.

---

## Writing a Good `description` Field

The `description` in `SKILL.md` frontmatter is the **primary trigger mechanism**. The SDK uses it like a semantic router.

### Do ✅

- Start with a verb: "Manage…", "Generate…", "Analyze…"
- Include explicit "Use when:" scenarios — this is the most reliable trigger signal
- Cover all the intent variations a user might express

```yaml
description: Generate a PowerPoint presentation from an outline or topic.
  Use when: creating slides, building a deck, making a presentation, exporting to PPTX.
```

### Don't ❌

- Vague descriptions: "A useful skill for various things"
- Overlapping descriptions with other skills (causes misfires)
- Omitting "Use when:" examples (reduces trigger reliability significantly)

### Rule of Thumb

If two people would phrase the same request differently (e.g., "make slides" vs. "create a deck"), both phrasings should appear somewhere in the description.

---

## Structure: What Goes Where

```
skill-name/
├── SKILL.md          ← Required. Frontmatter + core instructions
├── .owui_id          ← Auto-generated. DO NOT edit or delete
├── references/       ← Optional. Supplementary docs, loaded on demand
│   └── advanced.md
├── scripts/          ← Optional. Helper shell/Python scripts
└── assets/           ← Optional. Templates, sample files, static data
```

### When to Use `references/`

Put content in `references/` when it is:

- Only needed for edge cases or advanced usage
- Too long to read every time (> ~100 lines)
- Reference material (API specs, format docs, examples)

Use progressive disclosure: the agent reads `SKILL.md` first, then loads a specific reference file only when the task requires it.

```markdown
## Advanced Export Options

See [references/export-options.md](references/export-options.md) for the full list.
```

### When to Inline in `SKILL.md`

Keep content in `SKILL.md` when it is:

- Needed for every run of the skill
- Short enough not to slow down context injection (< ~150 lines total)
- Core to the skill's main workflow

---

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Skill directory name | `kebab-case` | `export-to-pptx` |
| `name` field in frontmatter | `kebab-case`, matches dir name | `export-to-pptx` |
| Script filenames | `snake_case.py` or `snake_case.sh` | `build_slide.py` |
| Reference filenames | `kebab-case.md` | `advanced-options.md` |

Avoid spaces and uppercase in skill directory names — the SDK uses the directory name as the skill identifier.

---

## Writing Effective SKILL.md Instructions

### Open With a Role Statement

Tell the agent who it is in this skill context:

```markdown
# Export to PowerPoint

You are a presentation builder. Your job is to convert the user's content into a well-structured PPTX file using the scripts in this skill directory.
```

### Use Imperative Steps

Write instructions as numbered steps, not prose:

```markdown
1. Ask the user for the outline if not provided.
2. Run `python3 {scripts_dir}/build_slide.py --title "..." --output "{cwd}/output.pptx"`
3. Confirm success by checking the file exists.
4. Provide the user with the download path.
```

### Handle Errors Explicitly

Tell the agent what to do when things go wrong:

```markdown
If the script exits with a non-zero code, show the user the stderr output and ask how to proceed.
```

### End With a Closing Instruction

```markdown
After completing the task, summarize what was created and remind the user where to find the file.
```

---

## Skill Scope

Each skill should do **one thing well**. Signs a skill is too broad:

- The description has more than 4–5 "Use when:" entries covering unrelated domains
- The SKILL.md is > 300 lines
- You've added more than 3 reference files

When a skill grows too large, split it: one parent skill for routing + separate child skills per major function.

---

## Managing the `shared/` Directory

The `shared/` directory is **bidirectionally synced** with the OpenWebUI database:

- Skills created via the OpenWebUI UI are automatically imported into `shared/`
- Skills created by the agent in `shared/` are exported back to OpenWebUI at session start

### Safe operations

| Operation | Method |
|---|---|
| Install from URL | `python3 {scripts_dir}/install_skill.py --url <url> --dest {shared_dir}` |
| Create new skill | `mkdir -p {shared_dir}/<name>/ && create SKILL.md` |
| Edit skill | Read → modify → write `SKILL.md` |
| Delete skill | `rm -rf {shared_dir}/<name>/` (does NOT delete from OpenWebUI UI — do that separately) |
| List skills | `python3 {scripts_dir}/list_skills.py --path {shared_dir}` |

### The `.owui_id` file

Every skill synced with OpenWebUI has a `.owui_id` file containing the database UUID. **Never edit or delete this file** — it is the link between the filesystem and OpenWebUI DB. If deleted, the skill will be treated as new on next sync and may create a duplicate.

---

## Session Lifecycle Awareness

Skills are loaded **once at session start**. Changes made during a session take effect in the **next session**.

| When | What happens |
|---|---|
| Session starts | SDK daemon reads all `SKILL.md` files; `_sync_openwebui_skills` runs bidirectional DB↔file sync |
| During a session | New/edited/deleted skill files exist on disk but are NOT yet loaded by the daemon |
| After user starts new session | New skills become available; edited descriptions take effect |

**Always tell the user** after any create/edit/delete: "This change will take effect when you start a new session."

---

## Anti-Patterns to Avoid

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| Running `<skill-name>` as a bash command | Skills are not executables | Read the SKILL.md instructions and act with standard tools |
| Editing `.owui_id` | Breaks DB sync | Never touch it |
| Storing per-session state in `SKILL.md` | SKILL.md is static instructions, not a state file | Use separate workspace files for session state |
| Ultra-broad skill descriptions | Causes false positives on every message | Narrow to specific intent with "Use when:" |
| Putting all logic in one 500-line SKILL.md | Slow context injection, hard to maintain | Split into SKILL.md + `references/*.md` |
| Creating skills in `/tmp` | Not persisted, not found by SDK | Always create in `{shared_dir}/` |

---

## Quick Checklist for a New Skill

- [ ] Directory name is `kebab-case` and matches the `name` field
- [ ] `description` starts with a verb and has "Use when:" examples
- [ ] SKILL.md opens with a role statement for the agent
- [ ] Instructions use imperative numbered steps
- [ ] Long reference content moved to `references/`
- [ ] Scripts placed in `scripts/`
- [ ] Confirmed: skill does NOT overlap in description with other loaded skills
- [ ] User informed: "new skill takes effect next session"
