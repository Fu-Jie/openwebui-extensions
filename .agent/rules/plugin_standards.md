---
description: Standards for OpenWebUI Plugin Development, specifically README formatting.
globs: plugins/**
always_on: true
---
# Plugin Development Standards

## README Documentation

All plugins MUST follow the standard README template.

**Reference Template**: @docs/PLUGIN_README_TEMPLATE.md

### Language Requirements

- **English Version (`README.md`)**: The primary documentation source. Must follow the template strictly.
- **Chinese Version (`README_CN.md`)**: MUST be translated based on the English version (`README.md`) to ensure consistency in structure and content.

### Metadata Requirements

Follow the header table used in the template:
`| By [Fu-Jie](https://github.com/Fu-Jie) · vX.Y.Z | [⭐ Star this repo](https://github.com/Fu-Jie/openwebui-extensions) |`

### Structure Checklist

1. **Title & Description**
2. **Header Metadata Table** (Author, version, repo star link)
3. **Preview** (Screenshot, GIF, or a short note if preview is not ready)
4. **Install with Batch Install Plugins** (Include the fixed prompt block)
   Use the generic prompt `Install plugin from Fu-Jie/openwebui-extensions` instead of hard-coding the plugin name.
5. **What's New** (Keep last 1-3 versions)
6. **Key Features**
7. **How to Use**
8. **Configuration (Valves)**
9. **Troubleshooting** (Must include link to GitHub Issues and mention official-version conflict if relevant)
