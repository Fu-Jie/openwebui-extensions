# Installation Guide

OpenWebUI Extras provides resources that can be easily integrated into your OpenWebUI instance. No complex environment setup is required for most users.

## Prerequisites

*   A running instance of [OpenWebUI](https://github.com/open-webui/open-webui).

## Installing Plugins

You have two main ways to install plugins: via the OpenWebUI Community (Recommended) or Manually.

### Method 1: OpenWebUI Community (Recommended)

This is the easiest way to keep your plugins updated.

1.  Visit my profile on the OpenWebUI Community: [Fu-Jie's Profile](https://openwebui.com/u/Fu-Jie).
2.  Browse the available plugins and select the one you want to install.
3.  Click the **Get** button.
4.  Follow the prompts to import it directly into your local OpenWebUI instance.

### Method 2: Manual Installation

If you prefer to download the source code or specific versions:

1.  Navigate to the `plugins/` directory in this repository or browse the [Plugins Catalog](../plugins/index.md).
2.  Download the Python file (`.py`) for the plugin you need.
3.  Open your OpenWebUI instance.
4.  Go to **Admin Panel** -> **Settings** -> **Plugins**.
5.  Click the upload button (usually a `+` or import icon) and select the `.py` file you downloaded.
6.  Once uploaded, toggle the switch to enable the plugin.

## Using Prompts

1.  Navigate to the `prompts/` directory or browse the [Prompts Library](../prompts/library.md).
2.  Select a prompt file (`.md`) that suits your task.
3.  Copy the content of the prompt.
4.  In the OpenWebUI chat interface, click the **Prompt** button (usually near the input box).
5.  Paste the content and save it as a new prompt or use it immediately.

## Troubleshooting

If you encounter issues during installation:

*   **Plugin fails to load**: Check the OpenWebUI logs for syntax errors or missing dependencies. Some plugins might require specific Python packages installed in the OpenWebUI environment.
*   **Prompt not working**: Ensure you have copied the entire prompt content.

For more detailed troubleshooting, refer to the [FAQ](faq.md).
