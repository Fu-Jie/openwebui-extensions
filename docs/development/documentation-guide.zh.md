# 文档编写指南

本文介绍如何为 OpenWebUI Extensions 编写与贡献文档。

---

## 概览

文档基于 [MkDocs](https://www.mkdocs.org/) 与 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 主题构建。了解 Markdown 与 MkDocs 的基础有助于高效贡献。

---

## 开始之前

### 前置条件

1. Python 3.8 及以上
2. Git

### 本地环境搭建

```bash
# 克隆仓库
git clone https://github.com/Fu-Jie/openwebui-extensions.git
cd openwebui-extensions

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
mkdocs serve
```

访问 `http://localhost:8000` 预览文档。

---

## 文档结构

```
docs/
├── index.md              # 首页
├── contributing.md       # 贡献指南
├── plugins/              # 插件文档
│   ├── index.md          # 插件中心概览
│   ├── actions/          # Action 插件
│   ├── filters/          # Filter 插件
│   ├── pipes/            # Pipe 插件
│   └── pipelines/        # Pipeline 插件
├── prompts/              # 提示词库
├── enhancements/         # 增强指南
├── development/          # 开发指南
└── stylesheets/          # 自定义 CSS
```

---

## 编写插件文档

### 模板

新建插件文档可参考以下模板：

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

## Markdown 扩展

### 提示块（Admonitions）

用来突出重要信息：

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

### 可折叠区域

```markdown
??? question "Frequently asked question?"
    This is the answer.

???+ note "Open by default"
    This section is expanded by default.
```

### 代码块

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

## 图标

使用 `:material-icon-name:` 语法调用 Material Design Icons：

- `:material-brain:` :material-brain:
- `:material-puzzle:` :material-puzzle:
- `:material-download:` :material-download:
- `:material-github:` :material-github:

更多图标见 [Material Design Icons](https://pictogrammers.com/library/mdi/)。

### 图标尺寸

```markdown
:material-brain:{ .lg .middle } Large icon
```

---

## 分类徽章

为不同插件类型添加徽章：

```markdown
<span class="category-badge action">Action</span>
<span class="category-badge filter">Filter</span>
<span class="category-badge pipe">Pipe</span>
<span class="category-badge pipeline">Pipeline</span>
```

---

## 表格

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

更好的对齐方式：

```markdown
| Left | Center | Right |
|:-----|:------:|------:|
| L    |   C    |     R |
```

---

## 网格卡片

创建卡片式导航：

```markdown
<div class="grid cards" markdown>

-   :material-icon:{ .lg .middle } **Card Title**

    ---

    Card description goes here.

    [:octicons-arrow-right-24: Link Text](link.md)

</div>
```

---

## 链接

### 内部链接

```markdown
[Link Text](../path/to/page.md)
```

### 外部链接

```markdown
[Link Text](https://example.com){ target="_blank" }
```

### 按钮样式链接

```markdown
[Button Text](link.md){ .md-button }
[Primary Button](link.md){ .md-button .md-button--primary }
```

---

## 图片

```markdown
![Alt text](path/to/image.png)

<!-- With attributes -->
![Alt text](path/to/image.png){ width="300" }
```

---

## 最佳实践

### 写作风格

1. **简洁**：快速切入主题
2. **示例驱动**：展示而不只是说明
3. **一致性**：遵循现有模式
4. **面向新手**：假设读者基础有限

### 格式

1. 使用正确的标题层级（H1 → H2 → H3）
2. 主要段落间添加水平分割线（`---`）
3. 使用列表呈现步骤与特性
4. 需要时提供代码示例

### SEO

1. 使用描述性页面标题
2. 自然融入相关关键词
3. 需要时在前置区添加 meta 描述

---

## 提交修改

1. 创建功能分支
2. 完成文档修改
3. 通过 `mkdocs serve` 本地验证
4. 提交 Pull Request

---

## 其他资源

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
