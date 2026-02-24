# Agent Skills Index

This folder contains reusable Agent Skills for GitHub Copilot / VS Code custom agent workflows.

## Available Skills

- **community-announcer**
  - Purpose: Generate community announcement content and related assets.
  - Entry: `community-announcer/SKILL.md`

- **doc-mirror-sync**
  - Purpose: Sync mirrored documentation content and helper scripts.
  - Entry: `doc-mirror-sync/SKILL.md`

- **gh-issue-replier**
  - Purpose: Draft standardized issue replies with templates.
  - Entry: `gh-issue-replier/SKILL.md`

- **gh-issue-scheduler**
  - Purpose: Schedule and discover unanswered issues for follow-up.
  - Entry: `gh-issue-scheduler/SKILL.md`

- **i18n-validator**
  - Purpose: Validate translation key consistency across i18n dictionaries.
  - Entry: `i18n-validator/SKILL.md`

- **plugin-scaffolder**
  - Purpose: Scaffold OpenWebUI plugin boilerplate with repository standards.
  - Entry: `plugin-scaffolder/SKILL.md`

- **version-bumper**
  - Purpose: Assist with semantic version bumping workflows.
  - Entry: `version-bumper/SKILL.md`

- **xlsx-single-file**
  - Purpose: Single-file spreadsheet operations workflow without LibreOffice.
  - Entry: `xlsx-single-file/SKILL.md`

## Notes

- Skill definitions follow the expected location pattern:
  - `.github/skills/<skill-name>/SKILL.md`
- Each skill may include optional `assets/`, `references/`, and `scripts/` folders.
- This directory mirrors `.gemini/skills` for compatibility.
