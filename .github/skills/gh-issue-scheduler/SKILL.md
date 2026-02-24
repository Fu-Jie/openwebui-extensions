---
name: gh-issue-scheduler
description: Finds all open GitHub issues that haven't been replied to by the owner, summarizes them, and generates a solution plan. Use when the user wants to audit pending tasks or plan maintenance work.
---

# Gh Issue Scheduler

## Overview

The `gh-issue-scheduler` skill helps maintainers track community feedback by identifying unaddressed issues and drafting actionable technical plans to resolve them.

## Workflow

1.  **Identify Unanswered Issues**: Run the bundled script to fetch issues without owner replies.
    *   Command: `bash scripts/find_unanswered.sh`
2.  **Analyze and Summarize**: For each identified issue, summarize the core problem and the user's intent.
3.  **Generate Solution Plans**: Draft a technical "Action Plan" for each issue, including:
    *   **Root Cause Analysis** (if possible)
    *   **Proposed Fix/Implementation**
    *   **Verification Strategy**
4.  **Present to User**: Display a structured report of all pending issues and their respective plans.

## Tool Integration

### Find Unanswered Issues
```bash
bash scripts/find_unanswered.sh
```

## Report Format

When presenting the summary, use the following Markdown structure:

### 📋 Unanswered Issues Audit

#### Issue #[Number]: [Title]
- **Author**: @username
- **Summary**: Concise description of the problem.
- **Action Plan**:
    1. Step 1 (e.g., Investigate file X)
    2. Step 2 (e.g., Apply fix Y)
    3. Verification (e.g., Run test Z)
