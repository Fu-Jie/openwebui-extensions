# Deep Dive

<span class="category-badge action">Action</span>
<span class="version-badge">v1.0.0</span>

A comprehensive thinking lens that dives deep into any content - from context to logic, insights, and action paths.

---

## Overview

The Deep Dive plugin transforms how you understand complex content by guiding you through a structured thinking process. Rather than just summarizing, it deconstructs content across four phases:

- **🔍 The Context (What?)**: Panoramic view of the situation and background
- **🧠 The Logic (Why?)**: Deconstruction of reasoning and mental models  
- **💎 The Insight (So What?)**: Non-obvious value and hidden implications
- **🚀 The Path (Now What?)**: Specific, prioritized strategic actions

## Features

- :material-brain: **Thinking Chain**: Complete structured analysis process
- :material-eye: **Deep Understanding**: Reveals hidden assumptions and blind spots
- :material-lightbulb-on: **Insight Extraction**: Finds the "Aha!" moments
- :material-rocket-launch: **Action Oriented**: Translates understanding into actionable steps
- :material-theme-light-dark: **Theme Adaptive**: Auto-adapts to OpenWebUI light/dark theme
- :material-translate: **Multi-language**: Outputs in user's preferred language

---

## Installation

1. Download the plugin file: [`deep_dive.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/deep-dive)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Provide any long text, article, or meeting notes in the chat
2. Click the **Deep Dive** button in the message action bar
3. Follow the visual timeline from Context → Logic → Insight → Path

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `SHOW_STATUS` | boolean | `true` | Show status updates during processing |
| `MODEL_ID` | string | `""` | LLM model for analysis (empty = current model) |
| `MIN_TEXT_LENGTH` | integer | `200` | Minimum text length for analysis |
| `CLEAR_PREVIOUS_HTML` | boolean | `true` | Clear previous plugin results |
| `MESSAGE_COUNT` | integer | `1` | Number of recent messages to analyze |

---

## Theme Support

Deep Dive automatically adapts to OpenWebUI's light/dark theme:

- Detects theme from parent document `<meta name="theme-color">` tag
- Falls back to `html/body` class or `data-theme` attribute
- Uses system preference `prefers-color-scheme: dark` as last resort

!!! tip "For Best Results"
    Enable **iframe Sandbox Allow Same Origin** in OpenWebUI:
    **Settings** → **Interface** → **Artifacts** → Check **iframe Sandbox Allow Same Origin**

---

## Example Output

The plugin generates a beautiful structured timeline:

```
┌─────────────────────────────────────┐
│  🌊 Deep Dive Analysis              │
│  👤 User  📅 Date  📊 Word count    │
├─────────────────────────────────────┤
│  🔍 Phase 01: The Context           │
│  [High-level panoramic view]        │
│                                     │
│  🧠 Phase 02: The Logic             │
│  • Reasoning structure...           │
│  • Hidden assumptions...            │
│                                     │
│  💎 Phase 03: The Insight           │
│  • Non-obvious value...             │
│  • Blind spots revealed...          │
│                                     │
│  🚀 Phase 04: The Path              │
│  ▸ Priority Action 1...             │
│  ▸ Priority Action 2...             │
└─────────────────────────────────────┘
```

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - Uses the active LLM model for analysis
    - Requires `markdown` Python package

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/deep-dive){ .md-button }
