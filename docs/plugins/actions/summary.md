# Summary

<span class="category-badge action">Action</span>
<span class="version-badge">v1.0.0</span>

Generate concise summaries of long text content with key points extraction.

---

## Overview

The Summary plugin helps you quickly understand long pieces of text by generating concise summaries with extracted key points. It's perfect for:

- Summarizing long articles or documents
- Extracting key points from conversations
- Creating quick overviews of complex topics

## Features

- :material-text-box-search: **Smart Summarization**: AI-powered content analysis
- :material-format-list-bulleted: **Key Points**: Extracted important highlights
- :material-content-copy: **Easy Copy**: One-click copying of summaries
- :material-tune: **Adjustable Length**: Control summary detail level

---

## Installation

1. Download the plugin file: [`summary.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/summary)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Enable the plugin

---

## Usage

1. Get a long response from the AI or paste long text
2. Click the **Summary** button in the message action bar
3. View the generated summary with key points

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `summary_length` | string | `"medium"` | Length of summary (short/medium/long) |
| `include_key_points` | boolean | `true` | Extract and list key points |
| `language` | string | `"auto"` | Output language |

---

## Example Output

```markdown
## Summary

This document discusses the implementation of a new feature 
for the application, focusing on user experience improvements 
and performance optimizations.

### Key Points

- ✅ New user interface design improves accessibility
- ✅ Backend optimizations reduce load times by 40%
- ✅ Mobile responsiveness enhanced
- ✅ Integration with third-party services simplified
```

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - Uses the active LLM model for summarization

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/actions/summary){ .md-button }
