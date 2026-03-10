# OpenWebUI Tool Call Context Inflation

> Discovered: 2026-03-11

## Context
When analyzing why the `async_context_compression` plugin sees different array lengths of `messages` between the `inlet` (e.g. 27 items) and `outlet` (e.g. 8 items) phases, especially when native tool calling (Function Calling) is involved in OpenWebUI.

## Finding
There is a fundamental disparity in how OpenWebUI serializes conversational history at different stages of the request lifecycle:

1. **Outlet (UI Rendering View)**:
   After the LLM completes generation and tools have been executed, OpenWebUI's `middleware.py` (and streaming builders) bundles intermediate tool calls and their raw results. It hides them inside an HTML `<details type="tool_calls">...</details>` block within a single `role: assistant` message's `content`. 
   Concurrently, the actual native API tool-calling data is saved in a hidden `output` dict field attached to that message. At this stage, the `messages` array looks short (e.g., 8 items) because tool interactions are visually folded.

2. **Inlet (LLM Native View)**:
   When the user sends the *next* message, the request enters `main.py` -> `process_chat_payload` -> `middleware.py:process_messages_with_output()`.
   Here, OpenWebUI scans historical `assistant` messages for that hidden `output` field. If found, it completely **inflates (unfolds)** the raw data back into an exact sequence of OpenAI-compliant `tool_call` and `tool_result` messages (using `utils/misc.py:convert_output_to_messages`).
   The HTML `<details>` string is entirely discarded before being sent to the LLM.

**Conclusion on Token Consumption**:
In the next turn, tool context is **NOT** compressed at all. It is fully re-expanded to its original verbose state (e.g., back to 27 items) and consumes the maximum amount of tokens required by the raw JSON arguments and results.

## Gotchas
- Any logic operating in the `outlet` phase (like background tasks) that relies on the `messages` array index will be completely misaligned with the array seen in the `inlet` phase.
- Attempting to slice or trim history based on `outlet` array lengths will cause index out-of-bounds errors or destructive cropping of recent messages.
- The only safe way to bridge these two views is either to translate the folded view back into the expanded view using `convert_output_to_messages`, or to rely on unique `id` fields (if available) rather than array indices.