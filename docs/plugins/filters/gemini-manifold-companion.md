# Gemini Manifold Companion

<span class="category-badge filter">Filter</span>
<span class="version-badge">v1.0.0</span>

Companion filter for the Gemini Manifold pipe plugin, providing enhanced functionality.

---

## Overview

The Gemini Manifold Companion works alongside the [Gemini Manifold Pipe](../pipes/gemini-manifold.md) to provide additional processing and enhancement for Gemini model integrations.

## Features

- :material-handshake: **Seamless Integration**: Works with Gemini Manifold pipe
- :material-format-text: **Message Formatting**: Optimizes messages for Gemini
- :material-shield: **Error Handling**: Graceful handling of API issues
- :material-tune: **Fine-tuning**: Additional configuration options

---

## Installation

1. First, install the [Gemini Manifold Pipe](../pipes/gemini-manifold.md)
2. Download the companion filter: [`gemini_manifold_companion.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/filters/gemini_manifold_companion)
3. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
4. Enable the filter

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_format` | boolean | `true` | Auto-format messages for Gemini |
| `handle_errors` | boolean | `true` | Enable error handling |

---

## Requirements

!!! warning "Dependency"
    This filter requires the **Gemini Manifold Pipe** to be installed and configured.

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - Gemini Manifold Pipe installed

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/filters/gemini_manifold_companion){ .md-button }
