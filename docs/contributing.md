# Contributing Guide

Thank you for your interest in contributing to **OpenWebUI Extras**! We welcome contributions of plugins, prompts, documentation, and more.

---

## 🤝 How to Contribute

### 1. Share Prompts

If you have a useful prompt to share:

1. Browse the `prompts/` directory and find an appropriate category
2. If no suitable category exists, you can create a new folder
3. Create a new `.md` file with your prompt
4. Submit a Pull Request

#### Prompt Format

```markdown
# Prompt Name

Brief description of what this prompt does.

## Use Case

When to use this prompt.

## The Prompt

\```text
Your prompt content here...
\```

## Tips

Any tips for using this prompt effectively.
```

---

### 2. Develop Plugins

If you've developed an OpenWebUI plugin:

#### Plugin Metadata

Ensure your plugin includes complete metadata:

```python
"""
title: Plugin Name
author: Your Name
version: 0.1.0
description: Brief description of what the plugin does
"""
```

#### Directory Structure

Place your plugin in the appropriate directory:

- `plugins/actions/` - Action plugins (buttons below messages)
- `plugins/filters/` - Filter plugins (message processing)
- `plugins/pipes/` - Pipe plugins (custom models)
- `plugins/pipelines/` - Pipeline plugins (complex workflows)

#### Documentation

Please provide documentation for your plugin:

- `README.md` - English documentation
- `README_CN.md` - Chinese documentation (optional but appreciated)

Include:

- Feature description
- Installation steps
- Configuration options
- Usage examples
- Troubleshooting guide

---

### 3. Improve Documentation

Found an error or want to improve the docs?

1. Fork the repository
2. Make your changes in the `docs/` directory
3. Submit a Pull Request

---

## 🛠️ Development Standards

### Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines
- **Comments**: Add comments for complex logic
- **Naming**: Use clear, descriptive names

### Testing

Before submitting:

1. Test your plugin locally in OpenWebUI
2. Verify all features work as documented
3. Check for edge cases and error handling

### Commit Messages

Use clear, descriptive commit messages:

```
Add: Smart Mind Map action plugin
Fix: Context compression token counting
Update: Plugin development guide with new examples
```

---

## 📝 Submitting a Pull Request

### Step-by-Step

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a new branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Make** your changes
5. **Commit** your changes:
   ```bash
   git commit -m 'Add: Amazing feature'
   ```
6. **Push** to your branch:
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open** a Pull Request

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation is included/updated
- [ ] Plugin has been tested locally
- [ ] Commit messages are clear
- [ ] PR description explains the changes

---

## 🐛 Reporting Issues

Found a bug? Please open an issue with:

1. **Description**: Clear description of the problem
2. **Steps to Reproduce**: How to trigger the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OpenWebUI version, browser, OS

---

## 💡 Feature Requests

Have an idea? We'd love to hear it!

1. Check existing issues to avoid duplicates
2. Open a new issue with the "enhancement" label
3. Describe your idea and its use case

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## 🙏 Thank You!

Every contribution, no matter how small, helps make OpenWebUI Extras better for everyone. Thank you for being part of our community!

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui){ .md-button .md-button--primary }
