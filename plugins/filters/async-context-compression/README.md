# Async Context Compression Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **Version:** 1.2.0 | **Project:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **License:** MIT

This filter reduces token consumption in long conversations through intelligent summarization and message compression while keeping conversations coherent.

## What's new in 1.2.0

- **Preflight Context Check**: Before sending to the model, validates that total tokens fit within the context window. Automatically trims or drops oldest messages if exceeded.
- **Structure-Aware Assistant Trimming**: When context exceeds the limit, long AI responses are intelligently collapsed while preserving their structure (headers H1-H6, first line, last line).
- **Native Tool Output Trimming**: Detects and trims native tool outputs (`function_calling: "native"`), extracting only the final answer. Enable via `enable_tool_output_trimming`. **Note**: Non-native tool outputs are not fully injected into context.
- **Consolidated Status Notifications**: Unified "Context Usage" and "Context Summary Updated" notifications with appended warnings (e.g., `| ⚠️ High Usage`) for clearer feedback.
- **Context Usage Warning**: Emits a warning notification when context usage exceeds 90%.
- **Enhanced Header Detection**: Optimized regex (`^#{1,6}\s+`) to avoid false positives like `#hashtag`.
- **Detailed Token Logging**: Logs now show token breakdown for System, Head, Summary, and Tail sections with total.

## What's new in 1.1.3
- **Improved Compatibility**: Changed summary injection role from `user` to `assistant` for better compatibility across different LLMs.
- **Enhanced Stability**: Fixed a race condition in state management that could cause "inlet state not found" warnings in high-concurrency scenarios.
- **Bug Fixes**: Corrected default model handling to prevent misleading logs when no model is specified.

## What's new in 1.1.2

- **Open WebUI v0.7.x Compatibility**: Resolved a critical database session binding error affecting Open WebUI v0.7.x users. The plugin now dynamically discovers the database engine and session context, ensuring compatibility across versions.
- **Enhanced Error Reporting**: Errors during background summary generation are now reported via both the status bar and browser console.
- **Robust Model Handling**: Improved handling of missing or invalid model IDs to prevent crashes.

## What's new in 1.1.1

- **Frontend Debugging**: Added `show_debug_log` option to print debug info to the browser console (F12).
- **Optimized Compression**: Improved token calculation logic to prevent aggressive truncation of history, ensuring more context is retained.



---

## Core Features

- ✅ Automatic compression triggered by token thresholds.
- ✅ Asynchronous summarization that does not block chat responses.
- ✅ Persistent storage via Open WebUI's shared database connection (PostgreSQL, SQLite, etc.).
- ✅ Flexible retention policy to keep the first and last N messages.
- ✅ Smart injection of historical summaries back into the context.
- ✅ Structure-aware trimming that preserves document structure (headers, intro, conclusion).
- ✅ Native tool output trimming for cleaner context when using function calling.
- ✅ Real-time context usage monitoring with warning notifications (>90%).
- ✅ Detailed token logging for precise debugging and optimization.

---

## Installation & Configuration

### 1) Database (automatic)

- Uses Open WebUI's shared database connection; no extra configuration needed.
- The `chat_summary` table is created on first run.

### 2) Filter order

It is recommended to keep this filter early in the chain so it runs before filters that mutate messages:

1. Pre-filters (priority < 10) — e.g., system prompt injectors.
2. This compression filter (priority = 10).
3. Post-filters (priority > 10) — e.g., output formatting.

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
| `max_summary_tokens`           | `4000`   | Maximum tokens for the generated summary.                                                                                                                             |
| `summary_temperature`          | `0.3`    | Randomness for summary generation. Lower is more deterministic.                                                                                                       |
| `model_thresholds`             | `{}`     | Per-model overrides for `compression_threshold_tokens` and `max_context_tokens` (useful for mixed models).                                                            |
| `enable_tool_output_trimming`  | `false`  | When enabled and `function_calling: "native"` is active, trims verbose tool outputs to extract only the final answer.                                                 |
| `debug_mode`                   | `true`   | Log verbose debug info. Set to `false` in production.                                                                                                                 |
| `show_debug_log`               | `false`  | Print debug logs to browser console (F12). Useful for frontend debugging.                                                                                             |

---

- **Initial system prompt is lost**: Keep `keep_first` greater than 0 to protect the initial message.
- **Compression effect is weak**: Raise `compression_threshold_tokens` or lower `keep_first` / `keep_last` to allow more aggressive compression.
- **Submit an Issue**: If you encounter any problems, please submit an issue on GitHub: [Awesome OpenWebUI Issues](https://github.com/Fu-Jie/awesome-openwebui/issues)
