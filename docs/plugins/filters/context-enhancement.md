# Context Enhancement

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.2</span>

Enhances chat context with additional information for improved LLM responses.

---

## Overview

The Context Enhancement filter automatically enriches your conversations with contextual information, making LLM responses more relevant and accurate.

## Features

- :material-text-box-plus: **Auto Enhancement**: Automatically adds relevant context
- :material-clock: **Time Awareness**: Includes current date/time information
- :material-account: **User Context**: Incorporates user preferences
- :material-cog: **Customizable**: Configure what context to include

---

## Installation

1. Download the plugin file: [`context_enhancement_filter.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/context_enhancement_filter)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Configure enhancement options
4. Enable the filter

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `include_datetime` | boolean | `true` | Add current date/time |
| `include_user_info` | boolean | `true` | Add user name and preferences |
| `custom_context` | string | `""` | Custom context to always include |

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/context_enhancement_filter){ .md-button }
