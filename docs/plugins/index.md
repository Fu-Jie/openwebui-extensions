# Plugin Center

Welcome to the OpenWebUI Extras Plugin Center! Here you'll find a comprehensive collection of plugins to enhance your OpenWebUI experience.

## Plugin Types

OpenWebUI supports four types of plugins, each serving a different purpose:

<div class="grid cards" markdown>

-   :material-gesture-tap:{ .lg .middle } **Actions**

    ---

    Add custom buttons below messages to trigger specific actions like generating mind maps, exporting data, or creating visualizations.

    [:octicons-arrow-right-24: Browse Actions](actions/index.md)

-   :material-filter:{ .lg .middle } **Filters**

    ---

    Process and modify messages before they reach the LLM or after responses are generated. Perfect for context enhancement and compression.

    [:octicons-arrow-right-24: Browse Filters](filters/index.md)

-   :material-pipe:{ .lg .middle } **Pipes**

    ---

    Create custom model integrations or transform LLM responses. Connect to external APIs or implement custom model logic.

    [:octicons-arrow-right-24: Browse Pipes](pipes/index.md)

-   :material-pipe-wrench:{ .lg .middle } **Pipelines**

    ---

    Complex workflows that combine multiple processing steps. Ideal for advanced use cases requiring multi-step transformations.

    [:octicons-arrow-right-24: Browse Pipelines](pipelines/index.md)

</div>

---

## All Plugins at a Glance

| Plugin | Type | Description | Version |
|--------|------|-------------|---------|
| [Smart Mind Map](actions/smart-mind-map.md) | Action | Generate interactive mind maps from text | 0.7.2 |
| [Smart Infographic](actions/smart-infographic.md) | Action | Transform text into professional infographics | 1.0.0 |
| [Knowledge Card](actions/knowledge-card.md) | Action | Create beautiful learning flashcards | 0.2.0 |
| [Export to Excel](actions/export-to-excel.md) | Action | Export chat history to Excel files | 1.0.0 |
| [Summary](actions/summary.md) | Action | Text summarization tool | 1.0.0 |
| [Async Context Compression](filters/async-context-compression.md) | Filter | Intelligent context compression | 1.0.0 |
| [Context Enhancement](filters/context-enhancement.md) | Filter | Enhance chat context | 1.0.0 |
| [Gemini Manifold Companion](filters/gemini-manifold-companion.md) | Filter | Companion for Gemini Manifold | 1.0.0 |
| [Gemini Manifold](pipes/gemini-manifold.md) | Pipe | Gemini model integration | 1.0.0 |
| [MoE Prompt Refiner](pipelines/moe-prompt-refiner.md) | Pipeline | Multi-model prompt refinement | 1.0.0 |

---

## Installation Guide

### Step 1: Download the Plugin

Click on any plugin above to view its documentation and download the `.py` file.

### Step 2: Upload to OpenWebUI

1. Open OpenWebUI and navigate to **Admin Panel** → **Settings** → **Functions**
2. Click the **+** button to add a new function
3. Upload the downloaded `.py` file
4. Configure any required settings (API keys, options, etc.)

### Step 3: Enable and Use

1. Refresh the page after uploading
2. For **Actions**: Look for the plugin button in the message action bar
3. For **Filters**: Enable in your chat settings or globally
4. For **Pipes**: Select the custom model from the model dropdown
5. For **Pipelines**: Configure and activate in the pipeline settings

---

## Plugin Compatibility

!!! info "OpenWebUI Version"
    Most plugins in this collection are designed for OpenWebUI **v0.3.0** and later. Please check individual plugin documentation for specific version requirements.

!!! warning "Dependencies"
    Some plugins may require additional Python packages. Check each plugin's documentation for required dependencies.
