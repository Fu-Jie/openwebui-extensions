# OpenWebUI Extras
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

English | [中文](./README_CN.md)

A collection of enhancements, plugins, and prompts for [OpenWebUI](https://github.com/open-webui/open-webui), developed and curated for personal use to extend functionality and improve experience.

<!-- STATS_START -->
## 📊 Community Stats

> 🕐 Auto-updated: 2026-01-19 14:15

| 👤 Author | 👥 Followers | ⭐ Points | 🏆 Contributions |
|:---:|:---:|:---:|:---:|
| [Fu-Jie](https://openwebui.com/u/Fu-Jie) | **130** | **133** | **25** |

| 📝 Posts | ⬇️ Downloads | 👁️ Views | 👍 Upvotes | 💾 Saves |
|:---:|:---:|:---:|:---:|:---:|
| **16** | **1789** | **21155** | **119** | **132** |

### 🔥 Top 6 Popular Plugins

> 🕐 Auto-updated: 2026-01-19 14:15

| Rank | Plugin | Version | Downloads | Views | Updated |
|:---:|------|:---:|:---:|:---:|:---:|
| 🥇 | [Smart Mind Map](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a) | 0.9.1 | 531 | 4802 | 2026-01-17 |
| 🥈 | [📊 Smart Infographic (AntV)](https://openwebui.com/posts/smart_infographic_ad6f0c7f) | 1.4.9 | 260 | 2495 | 2026-01-18 |
| 🥉 | [Export to Excel](https://openwebui.com/posts/export_mulit_table_to_excel_244b8f9d) | 0.3.7 | 208 | 795 | 2026-01-07 |
| 4️⃣ | [Async Context Compression](https://openwebui.com/posts/async_context_compression_b1655bc8) | 1.1.3 | 180 | 1969 | 2026-01-17 |
| 5️⃣ | [Export to Word (Enhanced)](https://openwebui.com/posts/export_to_word_enhanced_formatting_fca6a315) | 0.4.3 | 157 | 1363 | 2026-01-17 |
| 6️⃣ | [Flash Card](https://openwebui.com/posts/flash_card_65a2ea8f) | 0.2.4 | 138 | 2324 | 2026-01-17 |

*See full stats in [Community Stats Report](./docs/community-stats.md)*
<!-- STATS_END -->

## 📦 Project Contents

### 🧩 Plugins

Located in the `plugins/` directory, containing Python-based enhancements:

#### Actions
- **Smart Mind Map** (`smart-mind-map`): Generates interactive mind maps from text.
- **Smart Infographic** (`infographic`): Transforms text into professional infographics using AntV.
- **Flash Card** (`flash-card`): Quickly generates beautiful flashcards for learning.
- **Deep Dive** (`deep-dive`): A comprehensive thinking lens that dives deep into any content.
- **Export to Excel** (`export_to_excel`): Exports chat history to Excel files.
- **Export to Word** (`export_to_docx`): Exports chat history to Word documents.

#### Filters
- **Async Context Compression** (`async-context-compression`): Optimizes token usage via context compression.
- **Context Enhancement** (`context_enhancement_filter`): Enhances chat context.
- **Markdown Normalizer** (`markdown_normalizer`): Fixes common Markdown formatting issues in LLM outputs.

#### Pipelines
- **MoE Prompt Refiner** (`moe_prompt_refiner`): Refines prompts for Mixture of Experts (MoE) summary requests to generate high-quality comprehensive reports.

### 🎯 Prompts

Located in the `prompts/` directory, containing fine-tuned System Prompts:

- **Coding**: Programming assistance prompts.
- **Marketing**: Marketing and copywriting prompts.

## 📖 Documentation

Located in the `docs/en/` directory:

- **[Plugin Development Guide](./docs/en/plugin_development_guide.md)** - The authoritative guide covering everything from getting started to advanced patterns and best practices. ⭐

For code examples, please check the `docs/examples/` directory.

## 🚀 Quick Start

This project is a collection of resources and does not require a Python environment. Simply download the files you need and import them into your OpenWebUI instance.

### Using Prompts

1. Browse the `/prompts` directory and select a prompt file (`.md`).
2. Copy the file content.
3. In the OpenWebUI chat interface, click the "Prompt" button above the input box.
4. Paste the content and save.

### Using Plugins

1. **Install from OpenWebUI Community (Recommended)**:
   - Visit my profile: [Fu-Jie's Profile](https://openwebui.com/u/Fu-Jie)
   - Browse the plugins and select the one you like.
   - Click "Get" to import it directly into your OpenWebUI instance.

2. **Manual Installation**:
   - Browse the `/plugins` directory and download the plugin file (`.py`) you need.
   - Go to OpenWebUI **Admin Panel** -> **Settings** -> **Plugins**.
   - Click the upload button and select the `.py` file you just downloaded.
   - Once uploaded, refresh the page to enable the plugin in your chat settings or toolbar.

### Contributing

If you have great prompts or plugins to share:
1. Fork this repository.
2. Add your files to the appropriate `prompts/` or `plugins/` directory.
3. Submit a Pull Request.

[Contributing](./CONTRIBUTING.md)

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/rbb-dev"><img src="https://avatars.githubusercontent.com/u/37469229?v=4?s=100" width="100px;" alt="rbb-dev"/><br /><sub><b>rbb-dev</b></sub></a><br /><a href="#ideas-rbb-dev" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/Fu-Jie/awesome-openwebui/commits?author=rbb-dev" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://trade.xyz/?ref=BZ1RJRXWO"><img src="https://avatars.githubusercontent.com/u/7317522?v=4?s=100" width="100px;" alt="Raxxoor"/><br /><sub><b>Raxxoor</b></sub></a><br /><a href="https://github.com/Fu-Jie/awesome-openwebui/issues?q=author%3Adhaern" title="Bug reports">🐛</a> <a href="#ideas-dhaern" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/i-iooi-i"><img src="https://avatars.githubusercontent.com/u/1827701?v=4?s=100" width="100px;" alt="ZOLO"/><br /><sub><b>ZOLO</b></sub></a><br /><a href="https://github.com/Fu-Jie/awesome-openwebui/issues?q=author%3Ai-iooi-i" title="Bug reports">🐛</a> <a href="#ideas-i-iooi-i" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://perso.crans.org/grande/"><img src="https://avatars.githubusercontent.com/u/469017?v=4?s=100" width="100px;" alt="Johan Grande"/><br /><sub><b>Johan Grande</b></sub></a><br /><a href="#ideas-nahoj" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
