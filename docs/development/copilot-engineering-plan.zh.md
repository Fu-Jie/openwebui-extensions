# Copilot 工程化配置设计

> 本文档定义面向插件开发的工程化配置方案：支持 GitHub Copilot、兼容 Gemini CLI，并引入“反重力开发”模式。

---

## 1. 目标

- 建立统一、可落地的 AI 协同开发标准。
- 支持双通道助手体系：
  - GitHub Copilot（编辑器内主通道）
  - Gemini CLI（外部补充通道）
- 在高迭代速度下保障可回滚、可审计、可发布。

---

## 2. 适用范围

适用于以下类型开发：

- 插件代码（`actions` / `filters` / `pipes` / `pipelines` / `tools`）
- 文档同步与发布准备
- OpenWebUI 文件创建与交付流程
- 流式输出与工具卡片兼容性

---

## 3. Copilot 工程化主配置

### 3.1 规范来源

- 主规范：`.github/copilot-instructions.md`
- 工作流：`.agent/workflows/plugin-development.md`
- 运行时开发指南：
  - `docs/development/plugin-guide.md`
  - `docs/development/plugin-guide.zh.md`

### 3.2 强制开发契约

- 单文件 i18n 插件源码。
- README 双语（`README.md` + `README_CN.md`）。
- 上下文统一入口（`_get_user_context`、`_get_chat_context`）。
- 事件标准化（`status`、`notification`、`execute`）。
- 禁止静默失败（用户可见状态 + 后端日志）。

### 3.3 Copilot SDK 工具契约

- 参数必须 `pydantic.BaseModel` 显式定义。
- 工具注册必须声明 `params_type`。
- 保留默认值语义，避免把未传参数强制覆盖为 `null`。
- 工具名需可预测、可规范化。

---

## 4. Gemini CLI 兼容配置

Gemini CLI 作为补充通道，而不是替代主规范。

### 4.1 使用边界

- 适合：草案生成、方案对照、迁移校验。
- 不得绕过仓库规范与插件契约。

### 4.2 输出归一化

Gemini CLI 输出合入前必须完成：

- 命名与结构对齐仓库约束。
- 保留 OpenWebUI 插件标准签名与上下文方法。
- 将“建议性文字”转换为可执行、可验证实现点。

### 4.3 冲突决策

Copilot 与 Gemini 建议冲突时按优先级处理：

1. 规范一致性优先
2. 安全回退优先
3. 低集成风险优先

---

## 5. 反重力开发（Antigravity）模式

反重力开发 = 高速迭代 + 强回退能力。

### 5.1 核心原则

- 小步、隔离、可逆变更
- 接口稳定、行为可预测
- 多级回退链路
- 支持前滚与回滚

### 5.2 强制模式

- 前端执行调用必须设置超时保护。
- 工作区文件操作必须做路径沙箱校验。
- 上传链路采用 API 优先 + 本地/DB 回退。
- 长任务必须分阶段状态反馈。

---

## 6. 文件创建与交付标准

### 6.1 创建范围

- 交付文件仅在受控 workspace 内创建。
- 禁止将交付产物写到 workspace 边界之外。

### 6.2 三步交付协议

1. 本地写入
2. 从 workspace 发布
3. 返回并展示 `/api/v1/files/{id}/content`

### 6.3 元数据策略

- 需要绕过检索时为产物标记 `skip_rag=true`。
- 文件名采用确定性策略：`chat_title -> markdown_title -> user+date`。

---

## 7. 多助手并行下的插件开发规范

- 在统一契约下同时兼容 GitHub Copilot 与 Gemini CLI。
- 流式输出保持 OpenWebUI 原生兼容（`<think>`、`<details type="tool_calls">`）。
- 工具卡片属性严格转义（`&quot;`）保证解析稳定。
- 全链路保持异步非阻塞。

---

## 8. 文档同步规则

插件工程化变更发生时，至少同步：

1. 插件代码
2. 插件双语 README
3. docs 详情页（EN/ZH）
4. docs 索引页（EN/ZH）
5. 发布准备阶段同步根 README 日期徽章

---

## 9. 验收清单

- Copilot 配置与工作流引用有效。
- Gemini CLI 输出可无缝合入且不破坏规范。
- 反重力安全机制完整。
- 文件创建/发布流程可复现。
- 流式与工具卡片格式保持 OpenWebUI 兼容。
