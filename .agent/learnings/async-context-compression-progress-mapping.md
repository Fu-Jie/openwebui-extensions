# Async Context Compression Progress Mapping

> Discovered: 2026-03-10

## Context
Applies to `plugins/filters/async-context-compression/async_context_compression.py` once the inlet has already replaced early history with a synthetic summary message.

## Finding
`compressed_message_count` cannot be recalculated from the visible message list length after compression. Once a summary marker is present, the visible list mixes:
- preserved head messages that are still before the saved boundary
- one synthetic summary message
- tail messages that map to original history starting at the saved boundary

## Solution / Pattern
Store the original-history boundary on the injected summary message metadata, then recover future progress using:
- `original_count = covered_until + len(messages_after_summary_marker)`
- `target_progress = max(covered_until, original_count - keep_last)`

When the summary-model window is too small, trim newest atomic groups from the summary input so the saved boundary still matches what the summary actually covers.

## Gotchas
- If you trim from the head of the summary input, the saved progress can overstate coverage and hide messages that were never summarized.
- Status previews for the next context must convert the saved original-history boundary back into the current visible view before rebuilding head/summary/tail.
- `inlet(body["messages"])` and `outlet(body["messages"])` can both represent the full conversation while using different serializations:
	- inlet may receive expanded native tool-call chains (`assistant(tool_calls) -> tool -> assistant`)
	- outlet may receive a compact top-level transcript where tool calls are folded into assistant `<details type="tool_calls">` blocks
- These two views do not share a safe `compressed_message_count` coordinate system. If outlet is in the compact assistant/details view, do not persist summary progress derived from its top-level message count.
