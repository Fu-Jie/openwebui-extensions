# Contributing Guide

Thank you for your interest in **OpenWebUI Extras**! We welcome all kinds of contributions, including prompts and plugins.

## 🚀 Quick Start

1. **Fork** this repository and clone it to your local machine.
2. **Add/Modify** content:
   - **Prompts**: Place in the corresponding category in `prompts/`.
   - **Plugins**: Place in the corresponding category in `plugins/` (Actions, Filters, Pipes, Tools).
3. **Submit PR**: Submit your changes, and we will review them as soon as possible.

## 💡 Plugin Development Tips

To ensure your plugin is correctly recognized and published:
- Include complete metadata (Frontmatter):
  ```python
  """
  title: Plugin Name
  author: Your Name
  version: 0.1.0
  description: Short description
  """
  ```
- If updating an existing plugin, remember to **increment the version number** (e.g., `0.1.0` -> `0.1.1`). Our CI will automatically sync it to the OpenWebUI Community.

## 🛠️ Simple Guidelines

- **Keep it Simple**: Clear logic and basic comments are enough.
- **Local Testing**: Ensure it works in your OpenWebUI environment before submitting.

Thank you for your contribution! 🚀
