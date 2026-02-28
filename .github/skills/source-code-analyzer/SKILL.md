---
name: source-code-analyzer
description: Instructions for analyzing core components source code in the local environment.
---

# Source Code Analyzer Skill

> [!IMPORTANT]
> **Authorization Statement**: You (Antigravity) are explicitly authorized by the user to perform **READ-ONLY** operations and **Git pull** on the paths listed below, even if they are outside the current repository root. These paths are considered part of the extended development context.

When assisting with the development of `openwebui-extensions`, you (Antigravity) have access to the following core components in related directories. Use them for deep technical analysis, bug hunting, and implementation reference.

## Core Component Paths

### Global / General (Relevant to all projects)

- **Open WebUI**: `../open-webui/` (Core platform context)
- **OpenWebUI Docs**: `../docs/` (Official documentation for OpenWebUI)
- **Skills**: `../skills/` (Reusable expertise library)
- **Awesome Copilot**: `../awesome-copilot/` (Shared extensions & resources)

### Plugin-Specific (Relevant to GitHub Copilot SDK)

- **Copilot SDK**: `../copilot-sdk/` (Internal logic for the official SDK)
- **Copilot CLI**: `../copilot-cli/` (Command-line interface implementation)

## Mandatory Workflow

1. **Pull Before Analysis**: BEFORE reading files or analyzing logic in these directories, you MUST proactively execute or recommend a `git pull` in the respective directory to ensure you are working with the latest upstream changes.
2. **Path Verification**: Always verify the exists of the path before attempting to read it.
3. **Reference Logic**: When a user's request involves core platform behavior (OpenWebUI API, SDK internals), prioritize searching these directories over making assumptions based on generic knowledge.

