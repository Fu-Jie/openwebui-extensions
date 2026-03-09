# Async Context Compression 核心故障分析与修复总结 (Issue #56)

Report: <https://github.com/Fu-Jie/openwebui-extensions/issues/56>

## 1. 问题分析

### 1.1 Critical: Tool-Calling 结构损坏

- **故障根源**: 插件在压缩历史消息时采用了“消息感知 (Message-Aware)”而非“结构感知 (Structure-Aware)”的策略。大模型的 `tool-calling` 依赖于 `assistant(tool_calls)` 与紧随其后的 `tool(s)` 消息的严格配对。
- **后果**: 如果压缩导致只有 `tool_calls` 被总结，而其对应的 `tool` 结果仍留在上下文，将触发 `No tool call found` 致命错误。

### 1.2 High: 坐标系偏移导致进度错位

- **故障根源**: 插件此前使用 `len(messages)` 计算总结进度。由于总结后消息列表变短，旧的索引无法正确映射回原始历史坐标。
- **后果**: 导致总结逻辑在对话进行中反复处理重叠的区间，或在某些边界条件下停止推进。

### 1.3 Medium: 并发竞态与元数据丢失

- **并发**: 缺乏针对 `chat_id` 的后台任务锁，导致并发请求下可能触发多个 LLM 总结任务。
- **元数据**: 消息被折叠为总结块后，其原始的 `id`、`name` 和扩展 `metadata` 彻底消失，破坏了依赖这些指纹的第三方集成。

---

## 2. 修复方案 (核心重构)

### 2.1 引入原子消息组 (Atomic Grouping)

实现 `_get_atomic_groups` 算法，将 `assistant-tool-assistant` 的调用链识别并标记。确保这些组被**整体保留或整体移除**。

该算法应用于两处截断路径：

1. **inlet 阶段**（有 summary / 无 summary 两条路径均已覆盖）
2. **outlet 后台 summary 任务**中，当 `middle_messages` 超出 summary model 上下文窗口需要截断时，同样使用原子组删除，防止在进入 LLM 总结前产生孤立的 tool result。（2026-03-09 补丁）

具体做法：

- `_get_atomic_groups(messages)` 会把消息扫描成多个“不可拆分单元”。
- 当遇到 `assistant` 且带 `tool_calls` 时，开启一个原子组。
- 后续所有 `tool` 消息都会被并入这个原子组。
- 如果紧跟着出现消费工具结果的 assistant 跟进回复，也会并入同一个原子组。
- 这样做之后，裁剪逻辑不再按“单条消息”删除，而是按“整组消息”删除。

这解决了 Issue #56 最核心的问题：

- 过去：可能删掉 `assistant(tool_calls)`，却留下 `tool` 结果
- 现在：要么整组一起保留，要么整组一起移除

也就是说，发送给模型的历史上下文不再出现孤立的 `tool_call_id`。

### 2.1.1 Tail 边界对齐 (Atomic Boundary Alignment)

除了按组删除之外，还新增了 `_align_tail_start_to_atomic_boundary` 来修正“保留尾部”的起点。

原因是：即使 `compressed_message_count` 本身来自旧数据或原始计数，如果它刚好落在一个工具调用链中间，直接拿来做 `tail` 起点仍然会造成损坏。

修复步骤如下：

1. 先计算理论上的 `raw_start_index`
2. 调用 `_align_tail_start_to_atomic_boundary(messages, raw_start_index, protected_prefix)`
3. 如果该起点落在某个原子组内部，就自动回退到该组起始位置
4. 用修正后的 `start_index` 重建 `tail_messages`

这个逻辑同时用于：

- `inlet` 中已存在 summary 时的 tail 重建
- `outlet` 中计算 `target_compressed_count`
- 后台 summary 任务里计算 `middle_messages` / `tail` 分界线

因此，修复并不只是“删除时按组删除”，而是连“边界落点”本身都改成结构感知。

### 2.2 实现单会话异步锁 (Chat Session Lock)

在 `Filter` 类中维护 `_chat_locks`。在 `outlet` 阶段，如果检测到已有后台任务持有该锁，则自动跳过当前请求，确保一个 `chat_id` 始终只有一个任务在运行。

具体流程：

1. `outlet` 先通过 `_get_chat_lock(chat_id)` 取得当前会话的锁对象
2. 如果 `chat_lock.locked()` 为真，直接跳过本次后台总结任务
3. 如果没有任务在运行，则创建 `_locked_summary_task(...)`
4. `_locked_summary_task` 内部用 `async with lock:` 包裹真正的 `_check_and_generate_summary_async(...)`

这样修复后，同一个会话不会再并发发起多个 summary LLM 调用，也不会出现多个后台任务互相覆盖 `compressed_message_count` 或 summary 内容的情况。

### 2.3 元数据溯源 (Metadata Traceability)

重构总结数据的格式化流程：

- 提取消息 ID (`msg[id]`)、参与者名称 (`msg[name]`) 和关键元数据。
- 将这些身份标识以 `[ID: xxx] [Name: yyy]` 的形式注入 LLM 的总结输入。
- 增强总结提示词 (Prompt)，要求模型按 ID 引用重要行为。

这里的修复目的不是“恢复被压缩消息的原始对象”，而是尽量保留它们的身份痕迹，降低以下风险：

- 压缩后 summary 完全失去消息来源
- 某段关键决策、工具结果或用户要求在总结中无法追溯
- 依赖消息身份的后续分析或人工排查变得困难

当前实现方式是 `_format_messages_for_summary`：

- 把每条消息格式化为 `[序号] Role [ID: ...] [Name: ...] [Meta: ...]: content`
- 多模态内容会先抽出文本部分再汇总
- summary prompt 中明确要求模型保留关键 ID / Name 的可追踪性

这不能等价替代原始消息对象，但比“直接丢掉所有身份信息后只保留一段自然语言总结”安全很多。

### 2.4 `max_context_tokens = 0` 语义统一

Issue #56 里还有一个不太显眼但实际会影响行为的一致性问题：

- `inlet` 路径已经把 `max_context_tokens <= 0` 视为“无限制，不做裁剪”
- 但后台 summary 任务里，之前仍会继续拿 `0` 参与 `estimated_input_tokens > max_context_tokens` 判断

这会造成前台请求和后台总结对同一配置的解释不一致。

修复后：

- `inlet` 与后台 summary 路径统一使用 `<= 0` 表示“no limit”
- 当 `max_context_tokens <= 0` 时，后台任务会直接跳过 `middle_messages` 的截断逻辑
- 并新增回归测试，确保该行为不会再次退化

这一步虽然不如 tool-calling 原子化那么显眼，但它解决了“配置含义前后不一致”的稳定性问题。

### 2.5 tool-output trimming 的风险收敛

Issue #56 提到原先的 tool-output trimming 可能误伤普通 assistant 内容。对此没有继续扩展一套更复杂的启发式规则，而是采用了更保守的收敛策略：

- `enable_tool_output_trimming` 默认保持 `False`
- 当前 trimming 分支不再主动重写普通 assistant 内容

这意味着插件优先保证“不误伤正常消息”，而不是冒险做激进裁剪。对于这个 bug 修复阶段，这是一个刻意的稳定性优先决策。

### 2.6 修复顺序总结

从实现层面看，这次修复不是单点补丁，而是一组按顺序落下去的结构性改动：

1. 先把消息从“单条处理”升级为“原子组处理”
2. 再把 tail / middle 的边界从“裸索引”升级为“结构感知边界”
3. 再加每会话异步锁，堵住并发 summary 覆盖
4. 再补 summary 输入格式，让被压缩历史仍保留可追踪身份信息
5. 最后统一 `max_context_tokens = 0` 的语义，并加测试防回归

因此，Issue #56 的修复本质上是：

把这个过滤器从“按字符串和长度裁剪消息”重构成“按对话结构和上下文契约裁剪消息”。

---

## 3. 修复覆盖范围对照表

| # | 严重级别 | 问题 | 状态 |
|---|----------|------|------|
| 1 | **Critical** | tool-calling 消息被单条压缩 → `No tool call found` | ✅ inlet 两条路径均已原子化 |
| 2 | **High** | `compressed_message_count` 坐标系混用 | ✅ outlet 始终在原始消息空间计算 |
| 3 | **Medium** | 无 per-chat 异步锁 | ✅ `_chat_locks` + `asyncio.Lock()` |
| 4 | **Medium** | tool-output 修剪过于激进 | ✅ 默认 `False`；循环体已置空 |
| 5 | **Medium** | `max_context_tokens = 0` 语义不一致 | ✅ 统一 `<= 0` 表示"无限制" |
| 6 | **Low** | 韩语 i18n 字符串混入俄文字符 | ✅ 已替换为纯韩文 |
| 7 | **(后发现)** | summary 任务内截断不使用原子组 | ✅ 2026-03-09 补丁：改用 `_get_atomic_groups` |

## 4. 验证结论

- **inlet 路径**: `_get_atomic_groups` 贯穿 `inlet` 两条分支，以原子组为单位丢弃消息，永不产生孤立 tool result。
- **summary 任务**: 超出上下文限制时，同样以原子组截断 `middle_messages`，保证进入 LLM 的输入完整性。
- **并发控制**: `chat_lock.locked()` 确保同一 `chat_id` 同时只有一个总结任务运行。
- **元数据**: `_format_messages_for_summary` 以 `[ID: xxx]` 形式保留原始消息身份标识。

## 5. 后置建议

该修复旨在将过滤器从“关键词总结”提升到“结构感知代理”的层面。在后续开发中，应继续保持对 OpenWebUI 原生消息指纹的尊重。
