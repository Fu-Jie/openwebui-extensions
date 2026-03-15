# Plugin Center

Choose the right OpenWebUI plugin by the outcome you want, then scan the current catalog once you know your lane.

> **Recommended route:** start by goal → open the recommended plugin docs → install from OpenWebUI Community or the repo source file.

## Start by Goal

<div class="grid cards" markdown>

- :material-brush-variant:{ .lg .middle } **Visualize and Present**

    ---

    Turn raw chat content into mind maps, infographics, flash cards, and polished explainers.

    **Start with:** [Smart Mind Map](actions/smart-mind-map.md), [Smart Infographic](actions/smart-infographic.md), [Flash Card](actions/flash-card.md), [Deep Dive](actions/deep-dive.md)

- :material-file-export:{ .lg .middle } **Export and Deliver**

    ---

    Convert valuable conversations into Word and Excel files for reports, handoff, or archiving.

    **Start with:** [Export to Word](actions/export-to-word.md), [Export to Excel](actions/export-to-excel.md)

- :material-tune-variant:{ .lg .middle } **Improve Context and Output Quality**

    ---

    Compress long chats, clean up Markdown, inject project rules, and enhance model context.

    **Start with:** [Async Context Compression](filters/async-context-compression.md), [Markdown Normalizer](filters/markdown_normalizer.md), [Folder Memory](filters/folder-memory.md), [Context Enhancement](filters/context-enhancement.md)

- :material-robot-excited-outline:{ .lg .middle } **Build Agent and Tool Workflows**

    ---

    Add autonomous agent behavior, reusable tools, and workflow-oriented integrations to OpenWebUI.

    **Start with:** [GitHub Copilot SDK](pipes/github-copilot-sdk.md), [OpenWebUI Skills Manager Tool](tools/openwebui-skills-manager-tool.md), [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.md), [Smart Mind Map Tool](tools/smart-mind-map-tool.md)

- :material-image-multiple:{ .lg .middle } **Extend Model Capabilities**

    ---

    Add multimodal access, raw-file awareness, and stronger context handling to your model stack.

    **Start with:** [Web Gemini Multimodal Filter](filters/web-gemini-multimodel.md), [Copilot SDK Files Filter](filters/github-copilot-sdk-files-filter.md), [Context Enhancement](filters/context-enhancement.md)

</div>

---

## Curated First Installs

| If you want... | Start with | Why |
| --- | --- | --- |
| One “wow” feature that changes how you use OpenWebUI | [GitHub Copilot SDK](pipes/github-copilot-sdk.md) | Turns OpenWebUI into a richer agent workspace with tools, skills, and structured delivery |
| Fast visual clarity from messy chat content | [Smart Mind Map](actions/smart-mind-map.md) | The quickest way to make a complex answer instantly more understandable |
| Presentation-ready storytelling | [Smart Infographic](actions/smart-infographic.md) | Converts raw text into something polished enough for demos and reports |
| Practical upgrade for long chats | [Async Context Compression](filters/async-context-compression.md) | Saves tokens and keeps conversations easier to manage |
| Shareable output files | [Export to Word](actions/export-to-word.md) | Great for handoff notes, reports, and reusable documents |
| Fast setup across multiple plugin repos | [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.md) | Cuts down repetitive install work when experimenting |

---

## Browse by Type

<div class="grid cards" markdown>

- :material-gesture-tap:{ .lg .middle } **Actions**

    ---

    One-click interactions, exports, visualizations, and message-side experiences.

    [:octicons-arrow-right-24: Browse Actions](actions/index.md)

- :material-filter:{ .lg .middle } **Filters**

    ---

    Message-pipeline upgrades for context, cleanup, formatting, and quality control.

    [:octicons-arrow-right-24: Browse Filters](filters/index.md)

- :material-pipe:{ .lg .middle } **Pipes**

    ---

    Model integrations and advanced agent-style runtime workflows.

    [:octicons-arrow-right-24: Browse Pipes](pipes/index.md)

- :material-tools:{ .lg .middle } **Tools**

    ---

    Native reusable tool plugins that can be called across models and workflows.

    [:octicons-arrow-right-24: Browse Tools](tools/index.md)

- :material-pipe-wrench:{ .lg .middle } **Pipelines / References**

    ---

    Historical or experimental orchestration-oriented references for multi-step workflows.

    [:octicons-arrow-right-24: Browse Pipelines](pipelines/index.md)

</div>

---

## Current Source-backed Catalog

| Plugin | Type | Best for |
| --- | --- | --- |
| [Smart Mind Map](actions/smart-mind-map.md) | Action | Interactive mind maps from conversations |
| [Smart Infographic](actions/smart-infographic.md) | Action | Polished infographic-style storytelling from raw text |
| [Flash Card](actions/flash-card.md) | Action | Study cards and memory-friendly summaries |
| [Export to Excel](actions/export-to-excel.md) | Action | Spreadsheet exports of chat data |
| [Export to Word](actions/export-to-word.md) | Action | High-fidelity Word deliverables |
| [Deep Dive](actions/deep-dive.md) | Action | Structured context → logic → insight analysis |
| [Async Context Compression](filters/async-context-compression.md) | Filter | Long-chat compression and token savings |
| [Context Enhancement](filters/context-enhancement.md) | Filter | Injecting helpful context before generation |
| [Folder Memory](filters/folder-memory.md) | Filter | Extracting and reusing project rules inside folders |
| [Markdown Normalizer](filters/markdown_normalizer.md) | Filter | Fixing Mermaid, LaTeX, code blocks, and Markdown cleanup |
| [Web Gemini Multimodal Filter](filters/web-gemini-multimodel.md) | Filter | Adding multimodal input handling to compatible workflows |
| [Copilot SDK Files Filter](filters/github-copilot-sdk-files-filter.md) | Filter | Sending raw repo files to Copilot SDK agents |
| [GitHub Copilot SDK](pipes/github-copilot-sdk.md) | Pipe | Autonomous agent workflows and tool reuse |
| [Smart Mind Map Tool](tools/smart-mind-map-tool.md) | Tool | Reusable mind-map generation across models |
| [OpenWebUI Skills Manager Tool](tools/openwebui-skills-manager-tool.md) | Tool | Installing and managing workspace skills |
| [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.md) | Tool | Faster onboarding across multiple plugin repositories |

---

## Repo-only Entries

| Plugin | Type | Notes |
| --- | --- | --- |
| [iFlow Official SDK Pipe](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/pipes/iflow-sdk-pipe) | Pipe | Source file and local README exist in the repo, but there is no mirrored docs page yet |
| [Chat Session Mapping Filter](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/chat-session-mapping-filter) | Filter | Lightweight session-tracking helper currently discoverable from the repository only |

> **Note:** Historical or docs-only references such as **Multi-Model Context Merger** and **MoE Prompt Refiner** still exist in the sub-indexes. This page prioritizes the current source-backed catalog and repo-discoverable entries.

---

## Installation Paths

1. **OpenWebUI Community (recommended)** — install directly from [Fu-Jie's profile](https://openwebui.com/u/Fu-Jie)
2. **Docs + repo source file** — read the docs page, then upload the matching `.py` file manually
3. **Bulk install / faster onboarding** — use [Batch Install Plugins from GitHub](tools/batch-install-plugins-tool.md) or `python scripts/install_all_plugins.py` locally
