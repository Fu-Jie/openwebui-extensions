# Agent Coordination Protocol (FOR AGENTS ONLY)

## 🛡️ The Golden Rule
**NEVER modify code without verifying the lock status in the Agent Hub.**

## 🔑 Identity Management
- `claude-code`: Official Claude CLI
- `copilot-agent`: GitHub Copilot
- `gemini-cursor`: Cursor IDE or Gemini extension
- `iflow-agent`: iFlow SDK agent

## 🛠️ The Synchronization Tool
Script: `scripts/agent_sync.py` (SQLite-backed)

### 🏎️ Workflow Lifecycle
1. **Initialize Session**:
   - `python3 scripts/agent_sync.py status`
   - `python3 scripts/agent_sync.py register <id> <name> "<objective>"`
2. **Resource Acquisition**:
   - `python3 scripts/agent_sync.py lock <id> <file_path>`
   - If blocked, identify the owner from `status` and do not attempt to bypass.
3. **Collaboration (Research Mode)**:
   - If the project mode is `RESEARCH`, prioritize the `note` command.
   - Summarize findings: `python3 scripts/agent_sync.py note <id> "<topic>" "<summary>"`
4. **Cleanup**:
   - `python3 scripts/agent_sync.py unlock <id> <file_path>`

## 📜 Shared Memory
Read `.agent/learnings/` to avoid reinventing the wheel.
