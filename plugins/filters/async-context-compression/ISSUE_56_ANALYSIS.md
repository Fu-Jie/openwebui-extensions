# Issue #56: Critical tool-calling corruption and multiple reliability issues

## Overview
This document consolidates all reported issues in the async-context-compression filter as described in [GitHub Issue #56](https://github.com/Fu-Jie/openwebui-extensions/issues/56).

---

## Issue List

### 1. 🔴 CRITICAL: Native tool-calling history can be corrupted

**Severity**: Critical  
**Impact**: Conversation integrity

#### Description
The compression logic removes individual messages without preserving native tool-calling structures as atomic units. This can break the relationship between assistant `tool_calls` and their corresponding `tool` result messages.

#### Symptom
```
No tool call found for function call output with call_id ...
```

#### Root Cause
- Assistant messages containing `tool_calls` can be removed while their matching `tool` result messages remain
- This creates orphaned tool outputs that reference non-existent `tool_call_id`s
- The model/provider rejects the request because the `call_id` no longer matches any tool call in history

#### Expected Behavior
Compression must treat tool-calling blocks atomically:
- `assistant(tool_calls)` message
- Corresponding `tool` result message(s)
- Optional assistant follow-up that consumes tool results

Should never be split or partially removed.

---

### 2. 🟠 HIGH: Compression progress mixes original-history and compressed-view semantics

**Severity**: High  
**Impact**: Summary advancement consistency

#### Description
The plugin stores `compressed_message_count` as progress over the original conversation history, but later recalculates it from the already-compressed conversation view. This mixes two different coordinate systems for the same field.

#### Problem
- Original-history progress (before compression)
- Compressed-view progress (after compression)

These two meanings are inconsistent, causing:
- Summary advancement to become inconsistent
- Summary progress to stall after summaries already exist
- Later updates to be measured in a different coordinate system than stored values

#### Expected Behavior
Progress tracking must use a single, consistent coordinate system throughout the lifetime of the conversation.

---

### 3. 🟡 MEDIUM: Async summary generation has no per-chat lock

**Severity**: Medium  
**Impact**: Token usage, race conditions

#### Description
Each response can launch a new background summary task for the same chat, even if one is already in progress.

#### Problems
- Duplicate summary work
- Increased token usage
- Race conditions in saved summary state
- Potential data consistency issues

#### Expected Behavior
Use per-chat locking to ensure only one summary task runs per chat at a time.

---

### 4. 🟡 MEDIUM: Native tool-output trimming is too aggressive

**Severity**: Medium  
**Impact**: Content accuracy in technical conversations

#### Description
The tool-output trimming heuristics can rewrite or trim normal assistant messages if they contain patterns such as:
- Code fences (triple backticks)
- `Arguments:` text
- `<tool_code>` tags

#### Problem
This is risky in technical conversations and may alter valid assistant content unintentionally.

#### Expected Behavior
Trimming logic should be more conservative and avoid modifying assistant messages that are not actually tool-output summaries.

---

### 5. 🟡 MEDIUM: `max_context_tokens = 0` has inconsistent semantics

**Severity**: Medium  
**Impact**: Determinism, configuration clarity

#### Description
The setting `max_context_tokens = 0` behaves inconsistently across different code paths:
- In some paths: behaves like "no threshold" (special mode, no compression)
- In other paths: still triggers reduction/truncation logic

#### Problem
Non-deterministic behavior makes the setting unpredictable and confusing for users.

#### Expected Behavior
- Define clear semantics for `max_context_tokens = 0`
- Apply consistently across all code paths
- Document the intended behavior

---

### 6. 🔵 LOW: Corrupted Korean i18n string

**Severity**: Low  
**Impact**: User experience for Korean speakers

#### Description
One translation string contains broken mixed-language text.

#### Expected Behavior
Clean up the Korean translation string to be properly formatted and grammatically correct.

---

## Related / Broader Context

**Note from issue reporter**: The critical bug is not limited to tool-calling fields alone. Because compression deletes or replaces whole message objects, it can also drop other per-message fields such as:
- Message-level `id`
- `metadata`
- `name`
- Similar per-message attributes

So the issue is broader than native tool-calling: any integration relying on per-message metadata may also be affected when messages are trimmed or replaced.

---

## Reproduction Steps

1. Start a chat with a model using native tool calling
2. Enable the async-context-compression filter
3. Send a conversation long enough to trigger compression / summary generation
4. Let the model perform multiple tool calls across several turns
5. Continue the same chat after the filter has already compressed part of the history

**Expected**: Chat continues normally  
**Actual**: Chat can become desynchronized and fail with errors like `No tool call found for function call output with call_id ...`

**Control Test**:
- With filter disabled: failure does not occur
- With filter enabled: failure reproduces reliably

---

## Suggested Fix Direction

### High Priority (Blocks Issue #56)

1. **Preserve tool-calling atomicity**: Compress history in a way that never separates `assistant(tool_calls)` from its corresponding `tool` messages
2. **Unify progress tracking**: Use a single, consistent coordinate system for `compressed_message_count` throughout
3. **Add per-chat locking**: Ensure only one background summary task runs per chat at a time

### Medium Priority

4. **Conservative trimming**: Refine tool-output trimming heuristics to avoid altering valid assistant content
5. **Define `max_context_tokens = 0` semantics**: Make behavior consistent and predictable
6. **Fix i18n**: Clean up the corrupted Korean translation string

---

## Environment

- **Plugin**: async-context-compression
- **OpenWebUI Version**: 0.8.9
- **OS**: Ubuntu 24.04 LTS ARM64
- **Reported by**: @dhaern
- **Issue Date**: [Recently opened]

---

## References

- [GitHub Issue #56](https://github.com/Fu-Jie/openwebui-extensions/issues/56)
- Plugin: `plugins/filters/async-context-compression/async_context_compression.py`
