# 修复：OpenAI API 错误 "messages with role 'tool' must be a response to a preceding message with 'tool_calls'"

## 问题描述
在 `async-context-compression` 过滤器中，当对话历史变长时，系统会对消息进行裁剪或摘要。如果保留下来的尾部历史恰好从一个原生工具调用序列的中间开始，那么下一次请求就可能以一条 `tool` 消息开头，而触发它的 `assistant` 消息已经被裁掉。

这就会触发 OpenAI API 的错误：
`"messages with role 'tool' must be a response to a preceding message with 'tool_calls'"`

## 根本原因

真正的缺陷在于历史压缩边界没有完整识别工具调用链的“原子性”。一个合法的工具调用链通常包括：

1. 一条带有 `tool_calls` 的 `assistant` 消息
2. 一条或多条 `tool` 消息
3. 一条可选的 assistant 跟进回复，用于消费工具结果

如果裁剪点落在这段链条内部，发给模型的消息序列就会变成非法格式。

## 解决方案：对齐原子边界
修复通过把工具调用序列分组为原子单元，并使裁剪边界对齐到这些单元。

### 1. `_get_atomic_groups()`
这个辅助函数会把消息索引分组为“必须一起保留或一起丢弃”的原子单元。它显式识别以下原生工具调用模式：

- `assistant(tool_calls)`
- `tool`
- assistant 跟进回复

也就是说，它不再把这些消息看成彼此独立的单条消息，而是把整段序列视为一个原子块。

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
这个辅助函数会检查一个拟定的裁剪起点是否落在某个原子块内部。如果是，它会把起点向前回退到该原子块的开头位置。

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

### 3. 应用于尾部保留和摘要进度计算
这个对齐后的边界现在被用于重建保留尾部消息，以及计算可以安全摘要的历史范围。

当前实现中的示例：

```python
raw_start_index = max(compressed_count, effective_keep_first)
start_index = self._align_tail_start_to_atomic_boundary(
    messages, raw_start_index, effective_keep_first
)
tail_messages = messages[start_index:]
```

在摘要进度计算中同样如此：

```python
raw_target_compressed_count = max(0, len(messages) - self.valves.keep_last)
target_compressed_count = self._align_tail_start_to_atomic_boundary(
    messages, raw_target_compressed_count, effective_keep_first
)
```

## 验证结果

- **首次压缩边界**：当历史第一次越过压缩阈值时，保留尾部不再从工具调用块中间开始。
- **复杂会话验证**：在 30+ 条消息、多个工具调用和失败调用的真实场景下，后台摘要过程保持稳定。
- **回归行为更安全**：过滤器现在会优先选择合法边界，即使这意味着比原始的朴素切片稍微多保留一点上下文。

## 结论
通过让历史裁剪与摘要进度计算具备"工具调用原子块感知"能力，避免孤立的 `tool` 消息出现，消除长对话与后台压缩期间的 400 错误。
