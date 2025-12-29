# Gemini Manifold

<span class="category-badge pipe">Pipe</span>
<span class="version-badge">v1.0.0</span>

Integration pipeline for Google's Gemini models with full streaming support.

---

## Overview

The Gemini Manifold pipe provides seamless integration with Google's Gemini AI models. It exposes Gemini models as selectable options in OpenWebUI, allowing you to use them just like any other model.

## Features

- :material-google: **Full Gemini Support**: Access all Gemini model variants
- :material-stream: **Streaming**: Real-time response streaming
- :material-image: **Multimodal**: Support for images and text
- :material-shield: **Error Handling**: Robust error management
- :material-tune: **Configurable**: Customize model parameters

---

## Installation

1. Download the plugin file: [`gemini_manifold.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/pipes/gemini_mainfold)
2. Upload to OpenWebUI: **Admin Panel** → **Settings** → **Functions**
3. Configure your Gemini API key
4. Select Gemini models from the model dropdown

---

## Configuration

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `GEMINI_API_KEY` | string | Yes | Your Google AI Studio API key |
| `DEFAULT_MODEL` | string | No | Default Gemini model to use |
| `TEMPERATURE` | float | No | Response temperature (0-1) |
| `MAX_TOKENS` | integer | No | Maximum response tokens |

---

## Available Models

When configured, the following models become available:

- `gemini-pro` - Text-only model
- `gemini-pro-vision` - Multimodal model
- `gemini-1.5-pro` - Latest Pro model
- `gemini-1.5-flash` - Fast response model

---

## Usage

1. After installation, go to any chat
2. Open the model selector dropdown
3. Look for models prefixed with your pipe name
4. Select a Gemini model
5. Start chatting!

---

## Getting an API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in the plugin configuration

!!! warning "API Key Security"
    Keep your API key secure. Never share it publicly or commit it to version control.

---

## Companion Filter

For enhanced functionality, consider installing the [Gemini Manifold Companion](../filters/gemini-manifold-companion.md) filter.

---

## Requirements

!!! note "Prerequisites"
    - OpenWebUI v0.3.0 or later
    - Valid Gemini API key
    - Internet access to Google AI APIs

---

## Troubleshooting

??? question "Models not appearing?"
    Ensure your API key is correctly configured and the plugin is enabled.

??? question "API errors?"
    Check your API key validity and quota limits in Google AI Studio.

??? question "Slow responses?"
    Consider using `gemini-1.5-flash` for faster response times.

---

## Source Code

[:fontawesome-brands-github: View on GitHub](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/pipes/gemini_mainfold){ .md-button }
