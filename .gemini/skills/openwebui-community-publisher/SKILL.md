---
name: openwebui-community-publisher
description: Automatically publishes plugin update posts to openwebui.com. 
---

# OpenWebUI Community Publisher

## Overview

This skill automates the process of creating **new** plugin release notes and announcements directly on the OpenWebUI Community (openwebui.com).

**Note**: This skill is exclusively for **new post creation**. Do NOT use this for updating existing posts, as updates are managed separately via dedicated scripts.

## Prerequisites

- User must be logged into [openwebui.com](https://openwebui.com) in the browser session.
- The content must be prepared in Markdown format (typically following the structure of the plugin's changelog or a dedicated release `.md` file).

## Execution Workflow

### 1. Verification

- Use `browser_subagent` to navigate to `https://openwebui.com`.
- Verify the logged-in user status (look for profile icons or "@Fu-Jie").

### 2. Post Creation

- Navigate to `https://openwebui.com/post`.
- **Post Type Selection**:
  - Choose the appropriate tab based on content:
    - **Text**: General announcements and documentation.
    - **Tool**: Standalone tool plugins.
    - **Function**: Pipes, Filters, or Actions.
    - **Prompt**: Chat prompt templates.
    - **Model**: GGUF/Ollama model files.
  - Unless otherwise specified, default to **Text** for general release introductions.
- **Community Selection**:
  - For general OpenWebUI related posts, select **o/openwebui**.
  - For specialized topics, select the relevant community (e.g., **o/ollama** for models).
- **Metadata Mapping**:
  - **Title**: Use the main header from the source file.
  - **Content/Description**: Paste the Markdown body.
  - **Source Code (for Function/Pipe)**: If publishing a `Function`, retrieve the corresponding `.py` file content and paste it into the code area.
- **Tags**: Leave empty by default unless relevant keywords are explicitly provided.
- **Media**: Optional, only attach if provided.
- **Settings**: Ensure "Adult content" is unchecked.

### 3. Submission & Validation

- Click the "Create" (创建) button.
- Wait for redirection to the final post URL.
- **CRITICAL**: Use `capture_browser_screenshot` to verify the rendering.
- Return the final URL to the user.

## Design Standards

- **Rich Aesthetics**: Use emojis in titles.
- **Structured Data**: Ensure tables and code blocks in the Markdown are preserved.
- **Internal Linking**: Link back to the OpenWebUI market or GitHub repository where applicable.
