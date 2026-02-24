---
name: gh-issue-replier
description: Professional English replier for GitHub issues. Use when a task is completed, a bug is fixed, or more info is needed from the user. Automates replying using the 'gh' CLI tool.
---

# Gh Issue Replier

## Overview

The `gh-issue-replier` skill enables Gemini CLI to interact with GitHub issues professionally. It enforces English for all communications and leverages the `gh` CLI to post comments.

## Workflow

1.  **Identify the Issue**: Find the issue number (e.g., #49).
2.  **Check Star Status**: Run the bundled script to check if the author has starred the repo.
    *   Command: `bash scripts/check_star.sh <issue-number>`
    *   Interpretation: 
        *   Exit code **0**: User has starred. Use "Already Starred" templates.
        *   Exit code **1**: User has NOT starred. Include "Star Request" in the reply.
3.  **Select a Template**: Load [templates.md](references/templates.md) to choose a suitable English response pattern.
4.  **Draft the Reply**: Compose a concise message based on the star status.
5.  **Post the Comment**: Use the `gh` tool to submit the reply.

## Tool Integration

### Check Star Status
```bash
bash scripts/check_star.sh <issue-number>
```

### Post Comment
```bash
gh issue comment <issue-number> --body "<message-body>"
```

Example (if user has NOT starred):
```bash
gh issue comment 49 --body "This has been fixed in v1.2.7. If you find this helpful, a star on the repo would be much appreciated! ⭐"
```

Example (if user HAS starred):
```bash
gh issue comment 49 --body "This has been fixed in v1.2.7. Thanks for your support!"
```

## Guidelines

-   **Language**: ALWAYS use English for the comment body, even if the system prompt or user conversation is in another language.
-   **Tone**: Professional, helpful, and appreciative.
-   **Precision**: When announcing a fix, mention the specific version or the logic change (e.g., "Updated regex pattern").
-   **Closing**: If the issue is resolved and you have permission, you can also use `gh issue close <number>`.
