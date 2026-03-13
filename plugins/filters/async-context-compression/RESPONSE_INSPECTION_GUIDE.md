# 📋 Response 结构检查指南

## 🎯 新增检查点

在 `_call_summary_llm()` 方法中添加了 **3 个新的响应检查点**，用于前端控制台检查 LLM 调用的完整响应流程。

### 新增检查点位置

| # | 检查点名称 | 位置 | 显示内容 |
|---|-----------|------|--------|
| 1️⃣ | **LLM Response structure** | `generate_chat_completion()` 返回后 | 原始 response 对象的类型、键、结构 |
| 2️⃣ | **LLM Summary extracted & cleaned** | 提取并清理 summary 后 | 摘要长度、字数、格式、是否为空 |
| 3️⃣ | **Summary saved to database** | 保存到 DB 后验证 | 数据库记录是否正确保存、字段一致性 |

---

## 📊 检查点详解

### 1️⃣ LLM Response structure

**显示时机**: `generate_chat_completion()` 返回，处理前  
**用途**: 验证原始响应数据结构

```
📋 [Compression] LLM Response structure (raw from generate_chat_completion)
├─ type: "dict" / "Response" / "JSONResponse"
├─ has_body: true/false (表示是否为 Response 对象)
├─ has_status_code: true/false
├─ is_dict: true/false
├─ keys: ["choices", "usage", "model", ...] (如果是 dict)
├─ first_choice_keys: ["message", "finish_reason", ...]
├─ message_keys: ["role", "content"]
└─ content_length: 1234 (摘要文本长度)
```

**关键验证**:
- ✅ `type` — 应该是 `dict` 或 `JSONResponse`
- ✅ `is_dict` — 最终应该是 `true`（处理完毕后）
- ✅ `keys` — 应该包含 `choices` 和 `usage`
- ✅ `first_choice_keys` — 应该包含 `message`
- ✅ `message_keys` — 应该包含 `role` 和 `content`
- ✅ `content_length` — 摘要不应该为空（> 0）

---

### 2️⃣ LLM Summary extracted & cleaned

**显示时机**: 从 response 中提取并 strip() 后  
**用途**: 验证提取的摘要内容质量

```
📋 [Compression] LLM Summary extracted & cleaned
├─ type: "str"
├─ length_chars: 1234
├─ length_words: 156
├─ first_100_chars: "用户提问关于......"
├─ has_newlines: true
├─ newline_count: 3
└─ is_empty: false
```

**关键验证**:
- ✅ `type` — 应该始终是 `str`
- ✅ `is_empty` — 应该是 `false`（不能为空）
- ✅ `length_chars` — 通常 100-2000 字符（取决于配置）
- ✅ `newline_count` — 多行摘要通常有几个换行符
- ✅ `first_100_chars` — 可视化开头内容，检查是否正确

---

### 3️⃣ Summary saved to database

**显示时机**: 保存到 DB 后，重新加载验证  
**用途**: 确认数据库持久化成功且数据一致

```
📋 [Compression] Summary saved to database (verification)
├─ db_id: 42
├─ db_chat_id: "chat-abc123..."
├─ db_compressed_message_count: 10
├─ db_summary_length_chars: 1234
├─ db_summary_preview_100: "用户提问关于......"
├─ db_created_at: "2024-03-12 15:30:45.123456+00:00"
├─ db_updated_at: "2024-03-12 15:35:20.654321+00:00"
├─ matches_input_chat_id: true
└─ matches_input_compressed_count: true
```

**关键验证** ⭐ 最重要:
- ✅ `matches_input_chat_id` — **必须是 `true`**
- ✅ `matches_input_compressed_count` — **必须是 `true`**
- ✅ `db_summary_length_chars` — 与提取后的长度一致
- ✅ `db_updated_at` — 应该是最新时间戳
- ✅ `db_id` — 应该有有效的数据库 ID

---

## 🔍 如何在前端查看

### 步骤 1: 启用调试模式

在 OpenWebUI 中:
```
Settings → Filters → Async Context Compression
  ↓
找到 valve: "show_debug_log"
  ↓
勾选启用 + Save
```

### 步骤 2: 打开浏览器控制台

- **Windows/Linux**: F12 → Console
- **Mac**: Cmd + Option + I → Console

### 步骤 3: 触发摘要生成

发送足够多的消息使 Filter 触发压缩：
```
1. 发送 15+ 条消息
2. 等待后台摘要任务开始
3. 在 Console 观察 📋 日志
```

### 步骤 4: 观察完整流程

```
[1] 📋 LLM Response structure (raw)
        ↓ (显示原始响应类型、结构)
[2] 📋 LLM Summary extracted & cleaned
        ↓ (显示提取后的文本信息)
[3] 📋 Summary saved to database (verification)
        ↓ (显示数据库保存结果)
```

---

## 📈 完整流程验证

### 优质流程示例 ✅

```
1️⃣ Response structure:
   - type: "dict"
   - is_dict: true
   - has "choices": true
   - has "usage": true

2️⃣ Summary extracted:
   - is_empty: false
   - length_chars: 1500
   - length_words: 200

3️⃣ DB verification:
   - matches_input_chat_id: true ✅
   - matches_input_compressed_count: true ✅
   - db_id: 42 (有效)
```

### 问题流程示例 ❌

```
1️⃣ Response structure:
   - type: "Response" (需要处理)
   - has_body: true
   - (需要解析 body)

2️⃣ Summary extracted:
   - is_empty: true ❌ (摘要为空!)
   - length_chars: 0

3️⃣ DB verification:
   - matches_input_chat_id: false ❌ (chat_id 不匹配!)
   - matches_input_compressed_count: false ❌ (计数不匹配!)
```

---

## 🛠️ 调试技巧

### 快速过滤日志

在 Console 过滤框输入:
```
📋  (搜索所有压缩日志)
LLM Response  (搜索响应相关)
Summary extracted  (搜索提取摘要)
saved to database  (搜索保存验证)
```

### 展开表格/对象查看详情

1. **对象型日志** (console.dir)
   - 点击左边的 ▶ 符号展开
   - 逐级查看嵌套字段

2. **表格型日志** (console.table)
   - 点击上方的 ▶ 展开
   - 查看完整列

### 对比多个日志

```javascript
// 在 Console 中手动对比
检查点1: type = "dict", is_dict = true
检查点2: is_empty = false, length_chars = 1234
检查点3: matches_input_chat_id = true
  ↓
如果所有都符合预期 → ✅ 流程正常
如果有不符的 → ❌ 检查具体问题
```

---

## 🐛 常见问题诊断

### Q: "type" 是 "Response" 而不是 "dict"?

**原因**: 某些后端返回 Response 对象而非 dict  
**解决**: 代码会自动处理，看后续日志是否成功解析

```
检查点1: type = "Response" ← 需要解析
  ↓
代码执行 `response.body` 解析
  ↓
再次检查是否变为 dict
```

### Q: "is_empty" 是 true?

**原因**: LLM 没有返回有效的摘要文本  
**诊断**:
1. 检查 `first_100_chars` — 应该有实际内容
2. 检查模型是否正确配置
3. 检查中间消息是否过多导致 LLM 超时

### Q: "matches_input_chat_id" 是 false?

**原因**: 保存到 DB 时 chat_id 不匹配  
**诊断**:
1. 对比 `db_chat_id` 和输入的 `chat_id`
2. 可能是数据库连接问题
3. 可能是并发修改导致的

### Q: "matches_input_compressed_count" 是 false?

**原因**: 保存的消息计数与预期不符  
**诊断**:
1. 对比 `db_compressed_message_count` 和 `saved_compressed_count`
2. 检查中间消息是否被意外修改
3. 检查原子边界对齐是否正确

---

## 📚 相关代码位置

```python
# 文件: async_context_compression.py

# 检查点 1: 响应结构检查 (L3459)
if self.valves.show_debug_log and __event_call__:
    await self._emit_struct_log(
        __event_call__,
        "LLM Response structure (raw from generate_chat_completion)",
        response_inspection_data,
    )

# 检查点 2: 摘要提取检查 (L3524)
if self.valves.show_debug_log and __event_call__:
    await self._emit_struct_log(
        __event_call__,
        "LLM Summary extracted & cleaned",
        summary_inspection,
    )

# 检查点 3: 数据库保存检查 (L3168)
if self.valves.show_debug_log and __event_call__:
    await self._emit_struct_log(
        __event_call__,
        "Summary saved to database (verification)",
        save_inspection,
    )
```

---

## 🎯 完整检查清单

在前端 Console 中验证:

- [ ] 检查点 1 出现且 `is_dict: true`
- [ ] 检查点 1 显示 `first_choice_keys` 包含 `message`
- [ ] 检查点 2 出现且 `is_empty: false`
- [ ] 检查点 2 显示合理的 `length_chars` (通常 > 100)
- [ ] 检查点 3 出现且 `matches_input_chat_id: true`
- [ ] 检查点 3 显示 `matches_input_compressed_count: true`
- [ ] 所有日志时间戳合理
- [ ] 没有异常或错误信息

---

## 📞 后续步骤

1. ✅ 启用调试模式
2. ✅ 发送消息触发摘要生成
3. ✅ 观察 3 个新检查点
4. ✅ 验证所有字段符合预期
5. ✅ 如有问题，参考本指南诊断

---

**最后更新**: 2024-03-12  
**相关特性**: Response 结构检查 (v1.4.1+)  
**文档**: [async_context_compression.py 第 3459, 3524, 3168 行]
