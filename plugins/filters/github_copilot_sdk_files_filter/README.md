# GitHub Copilot SDK Files Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.1.2 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

This is a dedicated **companion filter plugin** designed specifically for the [GitHub Copilot SDK Pipe](https://openwebui.com/posts/github_copilot_official_sdk_pipe_ce96f7b4).

Its core mission is to **protect user-uploaded files from being "pre-processed" by the OpenWebUI core system, ensuring that the Copilot Agent receives the raw files for autonomous analysis.**

## 🎯 Why is this needed?

In OpenWebUI's default workflow, when you upload a file (e.g., PDF, Excel, Python script), OpenWebUI automatically initiates a **RAG (Retrieval-Augmented Generation)** process: parsing the file, vectorizing it, extracting text, and injecting it into the prompt.

While useful for standard models, this is often disruptive for a **Copilot SDK Agent**:

1. **Agent Needs Raw Files**: The Agent may need to run Python code to read an Excel file or analyze a full directory structure, not chopped-up text fragments.
2. **Context Pollution**: Large amounts of text injected by RAG consume tokens and can confuse the Agent about "where the file is."
3. **Control & Performance**: Bypassing the extraction step speeds up the response and gives the Agent full autonomy over how to handle the data.

**This plugin acts as a "bodyguard" to solve these issues.**

## 🚀 How it Works

When you select a Copilot model (name containing `copilot_sdk`) in OpenWebUI and send a file:

1. **Intercept**: This plugin runs with high priority (Priority 0), before RAG and other filters.
2. **Relocate**: Detecting a Copilot model, it moves the `files` list from the request to a secure custom field `copilot_files`.
3. **Hide**: It clears the original `files` field.
4. **Pass**: The OpenWebUI core sees an empty `files` list and **does not trigger RAG**.
5. **Deliver**: The subsequent Copilot SDK Pipe plugin checks `copilot_files`, retrieves file information, and automatically copies them into the Agent's isolated workspace.

## 📦 Installation & Configuration

### 1. Installation

Import this plugin on the OpenWebUI **Functions** page.

### 2. Enable

Ensure this Filter is enabled globally or in chat settings.

### 3. Configuration (Valves)

Default settings work for most users:

| Parameter | Description | Default |
| :--- | :--- | :--- |
| **priority** | Execution priority. **Must be lower than OpenWebUI RAG priority**. | `0` |
| **target_model_keyword** | Keyword to identify Copilot models for interception. | `copilot_sdk` |

## ⚠️ Important Notes

* **Must be used with Copilot SDK Pipe**: If you install this plugin without the main Pipe plugin, uploaded files will simply "disappear" (as no subsequent plugin will look for them).
* **Gemini Filter Compatibility**: Fully compatible with the Gemini Multimodal Filter. Just ensure priorities don't conflict.
