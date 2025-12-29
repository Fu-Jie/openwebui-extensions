# Knowledge Card

<span class="category-badge action">Action</span>
<span class="version-badge">v0.2.0</span>

Quickly generates beautiful learning memory cards, perfect for studying and quick memorization.

---

## Overview

The Knowledge Card plugin (also known as Flash Card / 闪记卡) transforms content into visually appealing flashcards that are perfect for learning and memorization. Whether you're studying for exams, learning new concepts, or reviewing key points, this plugin helps you create effective study materials.

## Features

- :material-card-text: **Beautiful Cards**: Modern, clean design for easy reading
- :material-animation-play: **Interactive**: Flip cards to reveal answers
- :material-export: **Exportable**: Save cards for offline study
- :material-palette: **Customizable**: Multiple themes and styles
- :material-translate: **Multi-language**: Supports various languages

---

## Installation

1. Download the plugin file: [`knowledge_card.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/knowledge-card)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Have a conversation about a topic you want to learn
2. Click the **Flash Card** button in the message action bar
3. The plugin will analyze the content and generate flashcards
4. Click on cards to flip and reveal answers

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cards_per_message` | integer | `5` | Maximum cards to generate |
| `theme` | string | `"modern"` | Visual theme |
| `show_hints` | boolean | `true` | Include hints on cards |

---

## Example

=== "Question Side"
    ```
    ┌─────────────────────────────┐
    │                             │
    │   What is the capital of    │
    │         France?             │
    │                             │
    │         [Click to flip]     │
    └─────────────────────────────┘
    ```

=== "Answer Side"
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

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - No additional Python packages required

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/knowledge-card){ .md-button }
