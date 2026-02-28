---
name: test-copilot-pipe
description: Automotive deployment and testing of GitHub Copilot SDK Pipe plugin for frontend/backend status stability.
---

# 🤖 Skill: Test Copilot Pipe

This is a **universal testing framework** for publishing the latest `github_copilot_sdk.py` (Pipe) code to a local OpenWebUI instance and verifying it via an automated agent (`browser_subagent`).

## 🎯 Core Principles

- **Fixed Infrastructure**: The deployment script and the test entry URL are always static.
- **Dynamic Test Planning**: Specific test prompts and expectations (acceptance criteria) **must** be dynamically planned by you based on the code changes or specific user requests before execution.

---

## 🛠️ Static Environment Info

| Attribute | Fixed Value |
|------|--------|
| **Deployment Script** | `/Users/fujie/app/python/oui/openwebui-extensions/scripts/deploy_pipe.py` |
| **Python Path** | `/opt/homebrew/Caskroom/miniconda/base/envs/ai/bin/python3` |
| **Test URL** | `http://localhost:3003/?model=github_copilot_official_sdk_pipe.github_copilot_sdk-gpt-4.1` |

---

## 📋 Standard Workflow

### Step 1: Analyze Changes & Plan Test (Plan)

Before triggering the test, you must define the purpose of this test turn.
Example: *Modified tool calling logic -> Test prompt should trigger a specific tool; observe if the tool executes and returns the correct result.*

### Step 2: Deploy Latest Code (Deploy)

Use the `run_command` tool to execute the fixed update task:

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/ai/bin/python3 /Users/fujie/app/python/oui/openwebui-extensions/scripts/deploy_pipe.py
```

> **Mechanism**: `deploy_pipe.py` automatically loads the API Key from `scripts/.env` in the same directory.
> **Verification**: Look for `✅ Successfully updated... version X.X.X` or `✅ Successfully created...`. If a 401 error occurs, remind the user to generate a new API Key in OpenWebUI and update `.env`.

### Step 3: Verify via Browser Subagent (Verify)

Use the `browser_subagent` tool. **You must fill in the `[Dynamic Content]` slots based on Step 1**:

```text
Task:
1. Access The Fixed URL: http://localhost:3003/?model=github_copilot_official_sdk_pipe.github_copilot_sdk-gpt-4.1
2. RELIABILITY WAIT: Wait until the page fully loads. Wait until the chat input text area (`#chat-input`) is present in the DOM.
3. ACTION - FAST INPUT: Use the `execute_browser_javascript` tool to instantly inject the query and submit it. Use exactly this script format to ensure stability:
   `const input = document.getElementById('chat-input'); input.value = "[YOUR_DYNAMIC_TEST_PROMPT]"; input.dispatchEvent(new Event('input', { bubbles: true })); const e = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }); input.dispatchEvent(e);`
4. WAITING: Wait patiently for the streaming response to stop completely. You should wait for the Stop button to disappear, or wait for the system to settle (approximately 10-15 seconds depending on the query).
5. CHECK THE OUTCOME: [List the phenomena you expect to see, e.g., status bar shows specific text, tool card appears, result contains specific keywords, etc.]
6. CAPTURE: Take a screenshot of the settled state to prove the outcome.
7. REPORT: Report the EXACT outcome matching the criteria from step 5.
```

### Step 4: Evaluate & Iterate (Evaluate)

- **PASS**: Screenshot and phenomena match expectations. Report success to the user.
- **FAIL**: Analyze the issue based on screenshots/logs (e.g., race condition reappeared, API error). Modify the code and **re-run the entire skill workflow**.
