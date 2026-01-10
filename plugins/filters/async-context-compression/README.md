# Async Context Compression Filter

**Author:** [Fu-Jie](https://github.com/Fu-Jie) | **Version:** 1.1.1 | **License:** MIT

This filter reduces token consumption in long conversations through intelligent summarization and message compression while keeping conversations coherent.

## What's new in 1.1.1

- **Frontend Debugging**: Added `show_debug_log` option to print debug info to the browser console (F12).
- **Optimized Compression**: Improved token calculation logic to prevent aggressive truncation of history, ensuring more context is retained.

## What's new in 1.1.0 

- Reuses Open WebUI's shared database connection by default (no custom engine or env vars required).
- Token-based thresholds (`compression_threshold_tokens`, `max_context_tokens`) for safer long-context handling.
- Per-model overrides via `model_thresholds` for mixed-model workflows.
- Documentation now mirrors the latest async workflow and retention-first injection.

---

## Core Features

- ✅ Automatic compression triggered by token thresholds.
- ✅ Asynchronous summarization that does not block chat responses.
- ✅ Persistent storage via Open WebUI's shared database connection (PostgreSQL, SQLite, etc.).
- ✅ Flexible retention policy to keep the first and last N messages.
- ✅ Smart injection of historical summaries back into the context.

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
| `debug_mode`                   | `true`   | Log verbose debug info. Set to `false` in production.                                                                                                                 |
| `show_debug_log`               | `false`  | Print debug logs to browser console (F12). Useful for frontend debugging.                                                                                             |

---

## Troubleshooting

- **Database table not created**: Ensure Open WebUI is configured with a database and check Open WebUI logs for errors.
- **Summary not generated**: Confirm `compression_threshold_tokens` was hit and `summary_model` is compatible. Review logs for details.
- **Initial system prompt is lost**: Keep `keep_first` greater than 0 to protect the initial message.
- **Compression effect is weak**: Raise `compression_threshold_tokens` or lower `keep_first` / `keep_last` to allow more aggressive compression.
