# OpenWebUI Extras

English | [中文](./README_CN.md)

A collection of enhancements, plugins, and prompts for [OpenWebUI](https://github.com/open-webui/open-webui), developed and curated for personal use to extend functionality and improve experience.

<!-- STATS_START -->
## 📊 Community Stats

> 🕐 Auto-updated: 2026-01-08 19:09

| 👤 Author | 👥 Followers | ⭐ Points | 🏆 Contributions |
|:---:|:---:|:---:|:---:|
| [Fu-Jie](https://openwebui.com/u/Fu-Jie) | **54** | **67** | **20** |

| 📝 Posts | ⬇️ Downloads | 👁️ Views | 👍 Upvotes | 💾 Saves |
|:---:|:---:|:---:|:---:|:---:|
| **13** | **948** | **10047** | **59** | **52** |

### 🔥 Top 6 Popular Plugins

| Rank | Plugin | Downloads | Views |
|:---:|------|:---:|:---:|
| 🥇 | [Smart Mind Map](https://openwebui.com/posts/turn_any_text_into_beautiful_mind_maps_3094c59a) | 299 | 2627 |
| 🥈 | [Export to Excel](https://openwebui.com/posts/export_mulit_table_to_excel_244b8f9d) | 179 | 521 |
| 🥉 | [Async Context Compression](https://openwebui.com/posts/async_context_compression_b1655bc8) | 120 | 1321 |
| 4️⃣ | [📊 Smart Infographic (AntV)](https://openwebui.com/posts/smart_infographic_ad6f0c7f) | 93 | 1174 |
| 5️⃣ | [Flash Card](https://openwebui.com/posts/flash_card_65a2ea8f) | 87 | 1601 |
| 6️⃣ | [Export to Word (Enhanced)](https://openwebui.com/posts/export_to_word_enhanced_formatting_fca6a315) | 73 | 681 |

*See full stats in [Community Stats Report](./docs/community-stats.md)*
<!-- STATS_END -->

## 📦 Project Contents

### 🧩 Plugins

Located in the `plugins/` directory, containing Python-based enhancements:

#### Actions
- **Smart Mind Map** (`smart-mind-map`): Generates interactive mind maps from text.
- **Smart Infographic** (`infographic`): Transforms text into professional infographics using AntV.
- **Knowledge Card** (`knowledge-card`): Creates beautiful flashcards for learning.
- **Export to Excel** (`export_to_excel`): Exports chat history to Excel files.
- **Export to Word** (`export_to_docx`): Exports chat history to Word documents.
- **Summary** (`summary`): Text summarization tool.

#### Filters
- **Async Context Compression** (`async-context-compression`): Optimizes token usage via context compression.
- **Context Enhancement** (`context_enhancement_filter`): Enhances chat context.
- **Gemini Manifold Companion** (`gemini_manifold_companion`): Companion filter for Gemini Manifold.


#### Pipes
- **Gemini Manifold** (`gemini_mainfold`): Pipeline for Gemini model integration.

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
