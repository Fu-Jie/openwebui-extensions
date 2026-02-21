# Multi-Model Context Merger

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.1.0</span>

Automatically merges context from multiple model responses in the previous turn, enabling collaborative answers.

---

## Overview

This filter detects when multiple models have responded in the previous turn (e.g., using "Arena" mode or multiple models selected). It consolidates these responses and injects them as context for the current turn, allowing the next model to see what others have said.

## Features

- :material-merge: **Auto-Merge**: Consolidates responses from multiple models into a single context block.
- :material-format-list-group: **Structured Injection**: Uses XML-like tags (`<response>`) to separate different model outputs.
- :material-robot-confused: **Collaboration**: Enables models to build upon or critique each other's answers.

---

## Installation

1. Download the plugin file: [`multi_model_context_merger.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the filter.

---

## Usage

1. Select **multiple models** in the chat (or use Arena mode).
2. Ask a question. All models will respond.
3. Ask a follow-up question.
4. The filter will inject the previous responses from ALL models into the context of the current model(s).
