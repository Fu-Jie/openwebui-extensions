# Fix: OpenAI API Error "messages with role 'tool' must be a response to a preceding message with 'tool_calls'"

## Problem Description
In the `async-context-compression` filter, chat history can be trimmed or summarized when the conversation grows. If the retained tail starts in the middle of a native tool-calling sequence, the next request may begin with a `tool` message whose triggering `assistant` message is no longer present.

That produces the OpenAI API error:
`"messages with role 'tool' must be a response to a preceding message with 'tool_calls'"`

## Root Cause
History compression boundaries were not fully aware of atomic tool-call chains. A valid chain may include:

1. An `assistant` message with `tool_calls`
2. One or more `tool` messages
3. An optional assistant follow-up that consumes the tool results

If truncation happens inside that chain, the request sent to the model becomes invalid.

## Solution: Atomic Boundary Alignment
The fix groups tool-call sequences into atomic units and aligns trim boundaries to those groups.

### 1. `_get_atomic_groups()`
This helper groups message indices into units that must be kept or dropped together. It explicitly recognizes native tool-calling patterns such as:

- `assistant(tool_calls)`
- `tool`
- assistant follow-up response

Conceptually, it treats the whole sequence as one atomic block instead of independent messages.

```python
def _get_atomic_groups(self, messages: List[Dict]) -> List[List[int]]:
    groups = []
    current_group = []

    for i, msg in enumerate(messages):
        role = msg.get("role")
        has_tool_calls = bool(msg.get("tool_calls"))

        if role == "assistant" and has_tool_calls:
            if current_group:
                groups.append(current_group)
            current_group = [i]
        elif role == "tool":
            if not current_group:
                groups.append([i])
            else:
                current_group.append(i)
        elif (
            role == "assistant"
            and current_group
            and messages[current_group[-1]].get("role") == "tool"
        ):
            current_group.append(i)
            groups.append(current_group)
            current_group = []
        else:
            if current_group:
                groups.append(current_group)
                current_group = []
            groups.append([i])

    if current_group:
        groups.append(current_group)

    return groups
```

### 2. `_align_tail_start_to_atomic_boundary()`
This helper checks whether a proposed trim point falls inside one of those atomic groups. If it does, the start index is moved backward to the beginning of that group.

```python
def _align_tail_start_to_atomic_boundary(
    self, messages: List[Dict], raw_start_index: int, protected_prefix: int
) -> int:
    aligned_start = max(raw_start_index, protected_prefix)

    if aligned_start <= protected_prefix or aligned_start >= len(messages):
        return aligned_start

    trimmable = messages[protected_prefix:]
    local_start = aligned_start - protected_prefix

    for group in self._get_atomic_groups(trimmable):
        group_start = group[0]
        group_end = group[-1] + 1

        if local_start == group_start:
            return aligned_start

        if group_start < local_start < group_end:
            return protected_prefix + group_start

    return aligned_start
```

### 3. Applied to Tail Retention and Summary Progress
The aligned boundary is now used when rebuilding the retained tail and when calculating how much history can be summarized safely.

Example from the current implementation:

```python
raw_start_index = max(compressed_count, effective_keep_first)
start_index = self._align_tail_start_to_atomic_boundary(
    messages, raw_start_index, effective_keep_first
)
tail_messages = messages[start_index:]
```

And during summary progress calculation:

```python
raw_target_compressed_count = max(0, len(messages) - self.valves.keep_last)
target_compressed_count = self._align_tail_start_to_atomic_boundary(
    messages, raw_target_compressed_count, effective_keep_first
)
```

## Verification Results
- **First compression boundary**: When history first crosses the compression threshold, the retained tail no longer starts inside a tool-call block.
- **Complex sessions**: Real-world testing with 30+ messages, multiple tool calls, and failed calls remained stable during background summarization.
- **Regression behavior**: The filter now prefers a valid boundary even if that means retaining slightly more context than a naive raw slice would allow.

## Conclusion
The fix prevents orphaned `tool` messages by making history trimming and summary progress aware of atomic tool-call groups. This eliminates the 400 error during long conversations and background compression.
