---
name: plugin-scaffolder
description: Generates a standardized single-file i18n Python plugin template based on project standards. Use when starting a new plugin development to skip boilerplate writing.
---

# Plugin Scaffolder

## Overview
Generates compliant OpenWebUI plugin templates with built-in i18n, common utility methods, and required docstring fields.

## Usage
1. Provide the **Plugin Name** and **Type** (action/filter/pipe).
2. The skill will generate the `.py` file and the bilingual `README` files.

## Template Standard
- `Valves(BaseModel)` with `UPPER_SNAKE_CASE`
- `_get_user_context` with JS fallback and timeout
- `_emit_status` and `_emit_debug_log` methods
- Standardized docstring metadata
