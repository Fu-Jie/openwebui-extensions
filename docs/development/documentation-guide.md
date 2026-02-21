# Documentation Writing Guide

This guide explains how to write and contribute documentation for OpenWebUI Extensions.

---

## Overview

Our documentation is built with [MkDocs](https://www.mkdocs.org/) and the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme. Understanding the basics of Markdown and MkDocs will help you contribute effectively.

---

## Getting Started

### Prerequisites

1. Python 3.8 or later
2. Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/Fu-Jie/openwebui-extensions.git
cd openwebui-extensions

# Install dependencies
pip install -r requirements.txt

# Start the development server
mkdocs serve
```

Visit `http://localhost:8000` to preview the documentation.

---

## Documentation Structure

```
docs/
├── index.md              # Homepage
├── contributing.md       # Contribution guide
├── plugins/              # Plugin documentation
│   ├── index.md          # Plugin center overview
│   ├── actions/          # Action plugins
│   ├── filters/          # Filter plugins
│   ├── pipes/            # Pipe plugins
│   └── pipelines/        # Pipeline plugins
├── prompts/              # Prompt library
├── enhancements/         # Enhancement guides
├── development/          # Development guides
└── stylesheets/          # Custom CSS
```

---

## Writing Plugin Documentation

### Template

Use this template for new plugin documentation:

```markdown
# Plugin Name

<span class="category-badge action">Action</span>
<span class="version-badge">v1.0.0</span>

Brief description of what the plugin does.

---

## Overview

Detailed explanation of the plugin's purpose and functionality.

## Features

- :material-icon-name: **Feature 1**: Description
- :material-icon-name: **Feature 2**: Description

---

## Installation

1. Download the plugin file
2. Upload to OpenWebUI
3. Configure settings
4. Enable the plugin

---

## Usage

Step-by-step usage instructions.

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `option_name` | type | `default` | Description |

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - Any additional requirements

---

## Troubleshooting

??? question "Common issue?"
    Solution to the issue.

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/...){ .md-button }
```

---

## Markdown Extensions

### Admonitions

Use admonitions to highlight important information:

```markdown
!!! note "Title"
    This is a note.

!!! warning "Caution"
    This is a warning.

!!! tip "Pro Tip"
    This is a helpful tip.

!!! danger "Warning"
    This is a critical warning.
```

### Collapsible Sections

```markdown
??? question "Frequently asked question?"
    This is the answer.

???+ note "Open by default"
    This section is expanded by default.
```

### Code Blocks

````markdown
```python title="example.py" linenums="1"
def hello():
    print("Hello, World!")
```
````

### Tabs

```markdown
=== "Python"

    ```python
    print("Hello")
    ```

=== "JavaScript"

    ```javascript
    console.log("Hello");
    ```
```

---

## Icons

Use Material Design Icons with the `:material-icon-name:` syntax:

- `:material-brain:` :material-brain:
- `:material-puzzle:` :material-puzzle:
- `:material-download:` :material-download:
- `:material-github:` :material-github:

Find more icons at [Material Design Icons](https://pictogrammers.com/library/mdi/).

### Icon Sizing

```markdown
:material-brain:{ .lg .middle } Large icon
```

---

## Category Badges

Use these badges for plugin types:

```markdown
<span class="category-badge action">Action</span>
<span class="category-badge filter">Filter</span>
<span class="category-badge pipe">Pipe</span>
<span class="category-badge pipeline">Pipeline</span>
```

---

## Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

For better alignment:

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L    |   C    |     R |
```

---

## Grid Cards

Create card layouts for navigation:

```markdown
<div class="grid cards" markdown>

-   :material-icon:{ .lg .middle } **Card Title**

    ---

    Card description goes here.

    [:octicons-arrow-right-24: Link Text](link.md)

</div>
```

---

## Links

### Internal Links

```markdown
[Link Text](../path/to/page.md)
```

### External Links

```markdown
[Link Text](https://example.com){ target="_blank" }
```

### Button Links

```markdown
[Button Text](link.md){ .md-button }
[Primary Button](link.md){ .md-button .md-button--primary }
```

---

## Images

```markdown
![Alt text](path/to/image.png)

<!-- With attributes -->
![Alt text](path/to/image.png){ width="300" }
```

---

## Best Practices

### Writing Style

1. **Be concise**: Get to the point quickly
2. **Use examples**: Show, don't just tell
3. **Be consistent**: Follow existing patterns
4. **Write for beginners**: Assume minimal prior knowledge

### Formatting

1. Use proper heading hierarchy (H1 → H2 → H3)
2. Add horizontal rules (`---`) between major sections
3. Use lists for steps and features
4. Include code examples where helpful

### SEO

1. Use descriptive page titles
2. Include relevant keywords naturally
3. Add meta descriptions in frontmatter if needed

---

## Submitting Changes

1. Create a feature branch
2. Make your documentation changes
3. Test locally with `mkdocs serve`
4. Submit a pull request

---

## Additional Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
