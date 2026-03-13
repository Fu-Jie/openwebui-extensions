# Filter: async-context-compression 设计模式与工程实践

**日期**: 2026-03-12  
**模块**: `plugins/filters/async-context-compression/async_context_compression.py`  
**关键特性**: 上下文压缩、异步摘要生成、状态管理、LLM 工程优化

---

## 核心工程洞察

### 1. Request 对象的 Filter-to-LLM 传导链

**问题**：Filter 的 `outlet` 阶段启动背景异步任务（`asyncio.create_task`）调用 `generate_chat_completion`（内部 API），但无法直接访问原始 HTTP `request`。早期代码用最小化合成 Request（仅 `{"type": "http", "app": webui_app}`），暴露兼容性风险。

**解决方案**：

- OpenWebUI 对 `outlet` 同样支持 `__request__` 参数注入（即 `inlet` + `outlet` 都支持）
- 透传 `__request__` 通过整个异步调用链：`outlet → _locked_summary_task → _check_and_generate_summary_async → _generate_summary_async → _call_summary_llm`
- 在最终调用处：`request = __request__ or Request(...)`（兜底降级）

**收获**：LLM 调用路径应始终倾向于使用真实请求上下文，而非人工合成。即使后台任务中，`request.app` 的应用级状态仍持续有效。

---

### 2. 异步摘要生成中的上下文完整性

**关键场景分化**：

| 情况 | `summary_index` 值 | 旧摘要位置 | 需要 `previous_summary` |
|------|--------|----------|---------|
| Inlet 已注入旧摘要 | Not None | `messages[0]`（middle_messages 首项） | ❌ 否，已在 conversation_text 中 |
| Outlet 收原始消息（未注入） | None | DB 存档 | ✅ **是**，必须显式读取并透传 |

**问题根源**：`outlet` 收到的消息来自原始数据库查询，未经过 `inlet` 的摘要注入。当 LLM 看不到历史摘要时，已压缩的知识（旧对话、已解决的问题、先前的发现）会被重新处理或遗忘。

**实现要点**：

```python
# 仅当 summary_index is None 时异步加载旧摘要
if summary_index is None:
    previous_summary = await asyncio.to_thread(
        self._load_summary, chat_id, body
    )
else:
    previous_summary = None
```

---

### 3. 上下文压缩的 LLM Prompt 设计

**工程原则**：

1. **Clear Input Boundaries**：用 XML 风格标签（`<previous_working_memory>`, `<new_conversation>`）明确分界，避免 LLM 混淆"指令示例"与"待处理数据"
2. **State-Aware Merging**：不是"保留所有旧事实"，而是**更新状态**——`"bug X exists" → "bug X fixed"` 或彻底移除已解决项
3. **Goal Evolution**：Current Goal 反映**最新**意图；旧目标迁移到 Working Memory 作为上下文
4. **Error Verbatim**：Stack trace、异常类型、错误码必须逐字引用（是调试的一等公民）
5. **Format Strictness**：结构变为 **REQUIRED**（而非 Suggested），允许零内容项省略，但布局一致

**新 Prompt 结构**：

```
[Rules] → [Output Constraints] → [Required Structure Header] → [Boundaries] → <previous_working_memory> → <new_conversation>
```

关键改进：

- 规则 3（Ruthless Denoising） → 新增规则 4（Error Verbatim） + 规则 5（Causal Chain）
- "Suggested" Structure → "Required" Structure with Optional Sections
- 新增 `## Causal Log` 专项，强制单行因果链格式：`[MSG_ID?] action → result`
- Token 预算策略明确：按近期性和紧迫性优先裁剪（RRF）

---

### 4. 异步任务中的错误边界与恢复

**现象**：背景摘要生成任务（`asyncio.create_task`）的异常不会阻塞用户响应，但需要：

- 完整的日志链路（`_log` 调用 + `event_emitter` 通知）
- 数据库事务的原子性（摘要和压缩状态同时保存）
- 前端 UI 反馈（status event: "generating..." → "complete" 或 "error"）

**最佳实践**：

- 用 `asyncio.Lock` 按 chat_id 防止并发摘要任务
- 后台执行繁重操作（tokenize、LLM call）用 `asyncio.to_thread`
- 所有 I/O（DB reads/writes）需包裹异步线程池
- 异常捕获限制在 try-except，日志不要吞掉堆栈信息

---

### 5. Filter 单例与状态设计陷阱

**约束**：Filter 实例是全局单例，所有会话共享同一个 `self`。

**禁忌**：

```python
# ❌ 错误：self.temp_buffer = ... （会被其他并发会话污染）
self.temp_state = body  # 危险！

# ✅ 正确：无状态或使用锁/chat_id 隔离
self._chat_locks[chat_id] = asyncio.Lock()  # 每个 chat 一个锁
```

**设计**：

- Valves（Pydantic BaseModel）保存全局配置 ✅
- 使用 dict 按 `chat_id` 键维护临时状态（lock、计数器）✅
- 传参而非全局变量保存请求级数据 ✅

---

## 集成场景：Filter + Pipe 的配合

**当 Pipe 模型调用 Filter 时**：

1. `inlet` 注入摘要，削减上下文会话消息数
2. Pipe 模型（通常为 Copilot SDK 或自定义内核）处理精简消息
3. `outlet` 触发背景摘要，无阻塞用户响应
4. 下一轮对话时，`inlet` 再次注入最新摘要

**关键约束**：

- `_should_skip_compression` 检测 `__model__.get("pipe")` 或 `copilot_sdk`，必要时跳过注入
- Pipe 模型若有自己的上下文管理（如 Copilot 的 native tool calling），过度压缩会失去工具调用链
- 摘要模型选择（`summary_model` Valve）应兼容当前 Pipe 环境的 API（推荐用通用模型如 gemini-flash）

---

## 内部 API 契约速记

### `generate_chat_completion(request, payload, user)`

- **request**: FastAPI Request；可来自真实 HTTP 或 `__request__` 注入
- **payload**: `{"model": id, "messages": [...], "stream": false, "max_tokens": N, "temperature": T}`
- **user**: UserModel；从 DB 查询或 `__user__` 转换（需 `Users.get_user_by_id()`）
- **返回**: dict 或 JSONResponse；若是后者需 `response.body.decode()` + JSON parse

### Filter 生命周期

```
New Message → inlet (User input) → [Plugins wait] → LLM → outlet (Response) → Summary Task (Background)
```

---

## 调试清单

- [ ] `__request__` 在 `outlet` 签名中声明且被 OpenWebUI 注入（非 None）
- [ ] 异步调用链中每层都透传 `__request__`，最底层兜底合成
- [ ] `summary_index is None` 时从 DB 异步读取 `previous_summary`
- [ ] LLM Prompt 中 `<previous_working_memory>` 和 `<new_conversation>` 有明确边界
- [ ] 错误处理不吞堆栈：`logger.exception()` 或 `exc_info=True`
- [ ] `asyncio.Lock` 按 chat_id 避免并发工作冲突
- [ ] Copilot SDK / Pipe 模型需 `_should_skip_compression()` 检查
- [ ] Token budget 在 max_summary_tokens 下规划，优先保留近期事件

---

## 相关文件

- 核心实现：`plugins/filters/async-context-compression/async_context_compression.py`
- README：`plugins/filters/async-context-compression/README.md` + `README_CN.md`
- OpenWebUI 内部：`open_webui/utils/chat.py` → `generate_chat_completion()`

---

**版本**: 1.0  
**维护者**: Fu-Jie  
**最后更新**: 2026-03-12
