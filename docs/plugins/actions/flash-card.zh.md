# Knowledge Card（知识卡片）

<span class="category-badge action">Action</span>
<span class="version-badge">v0.2.4</span>

快速生成精美的学习记忆卡片，适合学习和速记。

---

## 概览

Knowledge Card 插件（又名 Flash Card / 闪记卡）会把内容转成视觉友好的记忆卡片，帮助你高效学习和记忆。无论备考、理解新概念或复习要点，都能用它快速生成学习素材。

## 功能特性

- :material-card-text: **精美卡片**：现代简洁的版式，便于阅读
- :material-animation-play: **可交互**：点击翻转查看答案
- :material-export: **可导出**：支持保存离线学习
- :material-palette: **可定制**：多种主题与样式
- :material-translate: **多语言**：支持多语言内容

---

## 安装

1. 下载插件文件：[`knowledge_card.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/knowledge-card)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 启用插件

---

## 使用方法

1. 与 AI 就你想学习的主题进行对话
2. 点击消息操作栏的 **Flash Card** 按钮
3. 插件会分析内容并生成卡片
4. 点击卡片翻面查看答案

---

## 配置项

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `cards_per_message` | integer | `5` | 每条消息最多生成的卡片数量 |
| `theme` | string | `"modern"` | 视觉主题 |
| `show_hints` | boolean | `true` | 是否在卡片上显示提示 |

---

## 示例

=== "问题面"
    ```
    ┌─────────────────────────────┐
    │                             │
    │   What is the capital of    │
    │         France?             │
    │                             │
    │         [Click to flip]     │
    └─────────────────────────────┘
    ```

=== "答案面"
    ```
    ┌─────────────────────────────┐
    │                             │
    │           Paris             │
    │                             │
    │   The city of lights,       │
    │   located on the Seine      │
    │                             │
    └─────────────────────────────┘
    ```

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上
    - 无需额外 Python 依赖

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/knowledge-card){ .md-button }
