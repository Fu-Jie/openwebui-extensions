# GitHub Copilot SDK Stream Finalization

> Discovered: 2026-03-20

## Context
Applies to `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py` when streaming assistant output, handling `pending_embeds`, and waiting for `session.idle`.

## Finding
Two non-obvious issues can make the pipe feel permanently stuck even when useful work already finished:

1. If the main `queue.get()` wait uses the full user-configured `TIMEOUT` (for example 300s), watchdog logic, "still working" status updates, and synthetic finalization checks only wake up at that same coarse interval.
2. If `pending_embeds` are flushed only in the `session.idle` branch, any timeout/error/missing-idle path can lose already-prepared embeds even though file publishing itself succeeded.

## Solution / Pattern
- Keep the *inactivity limit* controlled by `TIMEOUT`, but poll the local stream queue on a short fixed cadence (for example max 5s) so watchdogs and fallback finalization stay responsive.
- Track `assistant.turn_end`; if `session.idle` does not arrive shortly afterward, synthesize finalization instead of waiting for the full inactivity timeout.
- Flush `pending_embeds` exactly once via a shared helper that can run from both normal idle finalization and error/timeout finalization paths.
- For streamed text/reasoning, use conservative overlap trimming: only strip an overlapping prefix when the incoming chunk still contains new suffix content. Do not drop fully repeated chunks blindly, or legitimate repeated text can be corrupted.

## Gotchas
- RichUI embed success and streamed-text success are separate paths; a file can be published correctly while chat output still hangs or duplicates.
- If `assistant.reasoning_delta` is streamed, the later complete `assistant.reasoning` event must be suppressed just like `assistant.message`, or the thinking block can duplicate.

## 🛠️ Update 2026-03-21
- **Fixed Stream Duplication**: Fixed text stream overlays (e.g., `🎉 删 🎉 删除成功`) when resuming conversation session. Strictly applied `_dedupe_stream_chunk(delta, "message_stream_tail")` inside `assistant.message_delta` event handler to prevent concurrent history re-play or multiple stream delivery bug overlays, solving previous gaps in the deployment pipeline.
