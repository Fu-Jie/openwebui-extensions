# OpenWebUI Extras

English | [中文](./README_CN.md)

A collection of enhancements, plugins, and prompts for [OpenWebUI](https://github.com/open-webui/open-webui), developed and curated for personal use to extend functionality and improve experience.

[Contributing](./CONTRIBUTING.md)

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

1. Browse the `/plugins` directory and download the plugin file (`.py`) you need.
2. Go to OpenWebUI **Admin Panel** -> **Settings** -> **Plugins**.
3. Click the upload button and select the `.py` file you just downloaded.
4. Once uploaded, refresh the page to enable the plugin in your chat settings or toolbar.

### Contributing

If you have great prompts or plugins to share:
1. Fork this repository.
2. Add your files to the appropriate `prompts/` or `plugins/` directory.
3. Submit a Pull Request.
