# Contributing Guide

Thank you for your interest in **OpenWebUI Extras**! We welcome all kinds of contributions, including prompts, plugins, and documentation improvements.

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
- **Docs**: For complex features, adding a simple guide in `docs/` is recommended.

---

# 贡献指南

感谢你对 **OpenWebUI Extras** 感兴趣！我们欢迎任何形式的贡献，无论是提示词、插件还是文档改进。

## 🚀 快速贡献流程

1. **Fork** 本仓库并克隆到本地。
2. **修改/添加** 内容：
   - **提示词**: 放入 `prompts/` 对应分类。
   - **插件**: 放入 `plugins/` 对应分类（Actions, Filters, Pipes, Tools）。
3. **提交 PR**: 提交你的修改，我们会尽快审核。

## 💡 插件开发建议

为了让你的插件能被自动识别和发布，请确保：
- 包含完整的元数据（Frontmatter）：
  ```python
  """
  title: 插件名称
  author: 你的名字
  version: 0.1.0
  description: 简短描述
  """
  ```
- 如果是更新已有插件，请记得**增加版本号**（如 `0.1.0` -> `0.1.1`），这样系统会自动同步到 OpenWebUI 社区。

再次感谢你的贡献！🚀
