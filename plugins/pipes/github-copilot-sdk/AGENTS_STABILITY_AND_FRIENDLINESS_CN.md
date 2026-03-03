# 🧭 Agents 稳定性与友好性指南

本文聚焦如何提升 `github_copilot_sdk.py` 中 Agent 的**稳定性**与**交互友好性**。

---

## 1）目标

- 降低可避免失败（超时、工具死路、输出不可解析）。
- 在高压场景保持可预期（大上下文、上游不稳定、部分工具失败）。
- 提升交互体验（进度可见、风险操作先澄清、优雅降级）。
- 在不破坏兼容性的前提下逐步增强默认行为。

---

## 2）稳定性模型（4 层）

## A 层：输入安全

- 会话创建前验证关键上下文（user/chat/model/tool 可用性）。
- 对 JSON/配置采用严格解析，不信任自由文本。
- 对不支持的模式组合做前置拦截（例如：任务需要工具但工具被禁用）。

**落地建议**
- `create_session` 前增加 preflight validator。
- 快速失败并返回结构化恢复建议。

## B 层：会话安全

- 使用 profile 驱动默认值（`model`、`reasoning_effort`、`infinite_sessions`）。
- 请求未知 profile 时自动回退到安全默认 profile。
- 每个 chat 使用确定性 workspace 路径隔离。

**落地建议**
- 增加 `AGENT_PROFILE`，未知值回退 `default`。
- 长任务默认开启 `infinite_sessions`。

## C 层：工具调用安全

- 增加 `on_pre_tool_use` 做参数校验与净化。
- 增加高风险操作 allow/deny 规则。
- 按工具类别配置超时预算（文件/网络/命令）。

**落地建议**
- 保留现有 `on_post_tool_use`。
- 先补 `on_pre_tool_use`，再补 `on_error_occurred`。

## D 层：恢复安全

- 仅对幂等操作重试，且有次数上限。
- 区分可恢复/不可恢复错误。
- 提供确定性降级输出（摘要 + 限制说明）。

**落地建议**
- 按错误类型配置重试策略。
- 统一输出“成功了什么 / 失败了什么 / 下一步”。

---

## 3）友好性模型（UX 合约）

## A. 歧义先澄清

通过 `on_user_input_request` 处理：
- 约束缺失（范围、目标路径、输出格式）
- 高风险动作（删除/迁移/覆盖）
- 用户指令互相冲突

**规则**：一次提问给出有限选项，避免反复追问。

## B. 进度可见

按阶段发状态：
1. 上下文检查
2. 规划/分析
3. 工具执行
4. 验证
5. 结果输出

**规则**：超过 8 秒不能无状态输出。

## C. 失败友好

每次失败都要包含：
- 失败点
- 简短原因
- 已完成部分
- 下一步可执行建议

## D. 输出可读

统一最终输出结构：
- `Outcome`
- `Changes`
- `Validation`
- `Limitations`
- `Next Step`

---

## 4）高价值增强项（优先级）

## P0（立即）

1. `on_user_input_request` + 默认答复策略
2. `on_pre_tool_use` 参数检查 + 风险闸门
3. 阶段化状态事件

## P1（短期）

4. 错误分类 + 重试策略（`network/provider/tool/validation`）
5. profile 化 session 工厂 + 安全回退
6. 最终输出质量门（结构校验）

## P2（中期）

7. 传输配置能力（`cli_url/use_stdio/port`）
8. Azure provider 支持完善
9. foreground session 生命周期能力（高级多会话）

---

## 5）建议新增 valves

- `AGENT_PROFILE`: `default | builder | analyst | reviewer`
- `ENABLE_USER_INPUT_REQUEST`: `bool`
- `DEFAULT_USER_INPUT_ANSWER`: `str`
- `TOOL_CALL_TIMEOUT_SECONDS`: `int`
- `MAX_RETRY_ATTEMPTS`: `int`
- `ENABLE_SAFE_TOOL_GUARD`: `bool`
- `ENABLE_PHASE_STATUS_EVENTS`: `bool`
- `ENABLE_FRIENDLY_FAILURE_TEMPLATE`: `bool`

---

## 6）故障应对手册（实用）

## 场景 A：Provider 超时

- 若请求幂等，重试一次。
- 仍超时则降低 reasoning 强度。
- 返回简洁降级结果并保留已有中间成果。

## 场景 B：工具参数不匹配

- 在 `on_pre_tool_use` 阻断。
- 可恢复则提一个澄清问题。
- 不可恢复则跳过工具并说明影响。

## 场景 C：输出过大

- 大输出落盘到 workspace 文件。
- 返回文件路径 + 简要摘要。
- 避免把超大内容直接刷屏。

## 场景 D：用户指令冲突

- 明确指出冲突点。
- 给 2-3 个固定选项。
- 用户选定后再继续。

---

## 7）建议监控指标

- 会话成功率
- 工具调用成功率
- 首次失败后的恢复率
- 澄清率 vs 幻觉率
- 首次可用输出耗时
- 用户不满意信号（如“不是我要的”）

---

## 8）最小落地路径

1. 先加 `on_user_input_request` + `on_pre_tool_use`（功能开关控制）。
2. 增加阶段状态事件和失败友好模板。
3. 增加错误分类与重试策略。
4. 增加 profile 安全回退与传输配置能力。
5. 观察 1-2 周指标，再逐步收紧默认策略。

---

## 9）验收速查

- 仅在必要时澄清，不重复追问。
- 无长时间无状态“沉默”。
- 失败输出包含下一步动作。
- profile/provider 配置异常不导致会话崩溃。
- 超大输出可安全转文件。
- 最终响应结构稳定一致。
