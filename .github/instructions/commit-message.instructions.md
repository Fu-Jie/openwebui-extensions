---
name: Commit Message
description: Comprehensive Conventional Commits guidelines for openwebui-extensions
---
# Commit Message Instructions

You are an expert developer generating commit messages for the `openwebui-extensions` repository. 
Always adhere to the following strict guidelines based on the Conventional Commits specification.

## 1. General Rules
- **Language**: **English ONLY**. Never use Chinese or other languages in the commit title or body.
- **Structure**:
  ```text
  <type>(<scope>): <subject>
  <BLANK LINE>
  <body>
  <BLANK LINE>
  <footer>
  ```

## 2. Type (`<type>`)
Must be one of the following:
- `feat`: A new feature or a new plugin.
- `fix`: A bug fix.
- `docs`: Documentation only changes (e.g., README, MkDocs).
- `refactor`: A code change that neither fixes a bug nor adds a feature.
- `perf`: A code change that improves performance.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Changes to the build process, CI/CD, or auxiliary tools/scripts.
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.).

## 3. Scope (`<scope>`)
The scope should indicate the affected component or plugin.
- **For Plugins**: Use the plugin's folder name or category (e.g., `actions`, `filters`, `pipes`, `export-to-docx`, `github-copilot-sdk`).
- **For Docs**: Use `docs` or the specific doc section (e.g., `guide`, `readme`).
- **For Infra**: Use `ci`, `scripts`, `deps`.
- *Note*: Omit the scope if the change is global or spans too many components.

## 4. Subject Line (`<subject>`)
- **Length**: Keep it under 50-72 characters.
- **Mood**: Use the imperative, present tense: "change" not "changed" nor "changes" (e.g., "add feature" instead of "added feature").
- **Formatting**: Do not capitalize the first letter. Do not place a period `.` at the end.
- **Clarity**: State exactly *what* changed. Avoid vague terms like "update code" or "fix bug".

## 5. Body (`<body>`)
- **When to use**: Highly recommended for `feat`, `fix`, and `refactor`.
- **Content**: Explain *what* and *why* (motivation), not just *how* (the code diff shows the how).
- **Format**: Use a bulleted list (1-3 points) for readability.
- **Repo Specifics**: If the commit involves a plugin version bump, explicitly mention that the READMEs and docs were synced.

## 6. Footer / Breaking Changes (`<footer>`)
- If the commit introduces a breaking change (e.g., changing a Valve configuration key, altering a plugin's output format), append `!` after the scope/type: `feat(pipes)!: ...`
- Add a `BREAKING CHANGE:` block in the footer explaining the migration path.

## 7. Examples

**Example 1: Feature with Body**
```text
feat(github-copilot-sdk): add antigravity timeout guards

- Wrap all __event_call__ JS executions with asyncio.wait_for(timeout=2.0)
- Add dual-channel upload fallback (API → local/DB)
- Emit staged status events for tasks > 3 seconds
```

**Example 2: Bug Fix**
```text
fix(export-to-docx): resolve missing title fallback

- Fallback to user_name + date when chat_title is empty
- Prevent crash when metadata variables are missing
```

**Example 3: Documentation Sync**
```text
docs(plugins): sync bilingual READMEs for v1.2.0 release

- Update What's New section for folder-memory plugin
- Sync docs/plugins/filters/folder-memory.md
```

**Example 4: Breaking Change**
```text
refactor(core)!: rename global configuration valves

- Standardize all valve keys to UPPER_SNAKE_CASE
- Remove deprecated legacy_api_key field

BREAKING CHANGE: Users must reconfigure their API keys in the UI as the old `api_key` field is no longer read.
```
