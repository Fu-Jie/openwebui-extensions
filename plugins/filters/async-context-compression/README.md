# Async Context Compression Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 1.3.0 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **License:** MIT

This filter reduces token consumption in long conversations through intelligent summarization and message compression while keeping conversations coherent.

## What's new in 1.3.0

- **Internationalization (i18n)**: Complete localization of user-facing messages across 9 languages (English, Chinese, Japanese, Korean, French, German, Spanish, Italian).
- **Smart Status Display**: Added `token_usage_status_threshold` valve (default 80%) to intelligently control when token usage status is shown.
- **Improved Performance**: Frontend language detection and logging are optimized to be completely non-blocking, maintaining lightning-fast TTFB.
- **Copilot SDK Integration**: Automatically detects and skips compression for copilot_sdk based models to prevent conflicts.
- **Configuration**: `debug_mode` is now set to `false` by default for a quieter production experience.

---

## Core Features

- ✅ **Full i18n Support**: Native localization across 9 languages.
- ✅ Automatic compression triggered by token thresholds.
- ✅ Asynchronous summarization that does not block chat responses.
- ✅ Persistent storage via Open WebUI's shared database connection (PostgreSQL, SQLite, etc.).
- ✅ Flexible retention policy to keep the first and last N messages.
- ✅ Smart injection of historical summaries back into the context.
- ✅ Structure-aware trimming that preserves document structure (headers, intro, conclusion).
- ✅ Native tool output trimming for cleaner context when using function calling.
- ✅ Real-time context usage monitoring with warning notifications (>90%).
- ✅ Detailed token logging for precise debugging and optimization.
- ✅ **Smart Model Matching**: Automatically inherits configuration from base models for custom presets.
- ⚠ **Multimodal Support**: Images are preserved but their tokens are **NOT** calculated. Please adjust thresholds accordingly.

---

## Installation & Configuration

### 1) Database (automatic)

- Uses Open WebUI's shared database connection; no extra configuration needed.
- The `chat_summary` table is created on first run.

### 2) Filter order

- Recommended order: pre-filters (<10) → this filter (10) → post-filters (>10).

---

## Configuration Parameters

| Parameter                      | Default  | Description                                                                                                                                                           |
| :----------------------------- | :------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `priority`                     | `10`     | Execution order; lower runs earlier.                                                                                                                                  |
| `compression_threshold_tokens` | `64000`  | Trigger asynchronous summary when total tokens exceed this value. Set to 50%-70% of your model's context window.                                                      |
| `max_context_tokens`           | `128000` | Hard cap for context; older messages (except protected ones) are dropped if exceeded.                                                                                 |
| `keep_first`                   | `1`      | Always keep the first N messages (protects system prompts).                                                                                                           |
| `keep_last`                    | `6`      | Always keep the last N messages to preserve recent context.                                                                                                           |
| `summary_model`                | `None`   | Model for summaries. Strongly recommended to set a fast, economical model (e.g., `gemini-2.5-flash`, `deepseek-v3`). Falls back to the current chat model when empty. |
| `summary_model_max_context`    | `0`      | Max context tokens for the summary model. If 0, falls back to `model_thresholds` or global `max_context_tokens`.                                                      |
| `max_summary_tokens`           | `16384`  | Maximum tokens for the generated summary.                                                                                                                             |
| `summary_temperature`          | `0.3`    | Randomness for summary generation. Lower is more deterministic.                                                                                                       |
| `model_thresholds`             | `{}`     | Per-model overrides for `compression_threshold_tokens` and `max_context_tokens` (useful for mixed models).                                                            |
| `enable_tool_output_trimming`  | `false`  | When enabled and `function_calling: "native"` is active, trims verbose tool outputs to extract only the final answer.                                                 |
| `debug_mode`                   | `false`  | Log verbose debug info. Set to `false` in production.                                                                                                                 |
| `show_debug_log`               | `false`  | Print debug logs to browser console (F12). Useful for frontend debugging.                                                                                             |
| `show_token_usage_status`      | `true`   | Show token usage status notification in the chat interface.                                                                                                           |
| `token_usage_status_threshold` | `80`     | The minimum usage percentage (0-100) required to show a context usage status notification.                                                                            |

---

## ⭐ Support

If this plugin has been useful, a star on [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) is a big motivation for me. Thank you for the support.

## Troubleshooting ❓

- **Initial system prompt is lost**: Keep `keep_first` greater than 0 to protect the initial message.
- **Compression effect is weak**: Raise `compression_threshold_tokens` or lower `keep_first` / `keep_last` to allow more aggressive compression.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [OpenWebUI Extensions Issues](https://github.com/Fu-Jie/openwebui-extensions/issues)

## Changelog

See the full history on GitHub: [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)
