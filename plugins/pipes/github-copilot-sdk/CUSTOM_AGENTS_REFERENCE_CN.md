# 🤖 自定义 Agents 参考文档（Copilot SDK Python）

本文说明如何基于以下 SDK 创建**可复用的自定义 Agent 配置**：

- `/Users/fujie/app/python/oui/copilot-sdk/python`

并接入当前 Pipe：

- `plugins/pipes/github-copilot-sdk/github_copilot_sdk.py`

---

## 1）这里的“自定义 Agent”是什么？

在 Copilot SDK Python 中，自定义 Agent 通常不是 SDK 里的独立类，而是一个**会话配置组合**：

- 模型与推理强度
- system message / 人设
- tools 暴露范围
- hooks 生命周期行为
- 用户输入策略
- infinite session 压缩策略
- provider（可选）

实际落地方式：

1. 定义 `AgentProfile` 数据结构。
2. 将 profile 转成 `session_config`。
3. 调用 `client.create_session(session_config)`。

---

## 2）SDK 可用于定制 Agent 的能力

根据 `copilot-sdk/python/README.md`，关键可配置项包括：

- `model`
- `reasoning_effort`
- `tools`
- `system_message`
- `streaming`
- `provider`
- `infinite_sessions`
- `on_user_input_request`
- `hooks`

这些能力足够做出多个 agent 人设，而无需复制整套管线代码。

---

## 3）在 Pipe 中推荐的架构

建议采用：**Profile 注册表 + 单一工厂函数**。

```python
from dataclasses import dataclass
from typing import Any, Callable, Optional

@dataclass
class AgentProfile:
    name: str
    model: str
    reasoning_effort: str = "medium"
    system_message: Optional[str] = None
    enable_tools: bool = True
    enable_openwebui_tools: bool = True
    enable_hooks: bool = False
    enable_user_input: bool = False
    infinite_sessions_enabled: bool = True
    compaction_threshold: float = 0.8
    buffer_exhaustion_threshold: float = 0.95
```

profile -> session_config 的工厂函数：

```python
def build_session_config(profile: AgentProfile, tools: list, hooks: dict, user_input_handler: Optional[Callable[..., Any]]):
    config = {
        "model": profile.model,
        "reasoning_effort": profile.reasoning_effort,
        "streaming": True,
        "infinite_sessions": {
            "enabled": profile.infinite_sessions_enabled,
            "background_compaction_threshold": profile.compaction_threshold,
            "buffer_exhaustion_threshold": profile.buffer_exhaustion_threshold,
        },
    }

    if profile.system_message:
        config["system_message"] = {"content": profile.system_message}

    if profile.enable_tools:
        config["tools"] = tools

    if profile.enable_hooks and hooks:
        config["hooks"] = hooks

    if profile.enable_user_input and user_input_handler:
        config["on_user_input_request"] = user_input_handler

    return config
```

---

## 4）示例 Profile 预设

```python
AGENT_PROFILES = {
    "builder": AgentProfile(
        name="builder",
        model="claude-sonnet-4.6",
        reasoning_effort="high",
        system_message="You are a precise coding agent. Prefer minimal, verifiable changes.",
        enable_tools=True,
        enable_hooks=True,
    ),
    "analyst": AgentProfile(
        name="analyst",
        model="gpt-5-mini",
        reasoning_effort="medium",
        system_message="You analyze and summarize with clear evidence mapping.",
        enable_tools=False,
        enable_hooks=False,
    ),
    "reviewer": AgentProfile(
        name="reviewer",
        model="claude-sonnet-4.6",
        reasoning_effort="high",
        system_message="Review diffs, identify risks, and propose minimal fixes.",
        enable_tools=True,
        enable_hooks=True,
    ),
}
```

---

## 5）如何接入当前 Pipe

在 `github_copilot_sdk.py` 中：

1. 新增 Valve：`AGENT_PROFILE`（默认 `builder`）。
2. 运行时从注册表解析 profile。
3. 通过工厂函数生成 `session_config`。
4. 把已有开关（如 `ENABLE_TOOLS`、`ENABLE_OPENWEBUI_TOOLS`）作为最终覆盖层。

推荐优先级：

- 显式运行时参数 > valve 开关 > profile 默认值

这样能保持向后兼容，同时支持按 profile 切换 agent 行为。

---

## 6）Hooks 策略（安全默认）

仅在必要时开启 hooks：

- `on_pre_tool_use`：工具调用前 allow/deny、参数净化
- `on_post_tool_use`：补充简要上下文
- `on_user_prompt_submitted`：提示词规范化
- `on_error_occurred`：错误重试/跳过/中止策略

建议先用 no-op，再逐步加策略。

---

## 7）验证清单

- 可通过 valve 选择 profile，且生效。
- session 使用了预期 model / reasoning。
- 工具可用性符合 profile + valve 覆盖后的结果。
- hooks 仅在启用时触发。
- infinite session 的阈值配置已生效。
- 传入未知 profile 时能安全回退到默认 profile。

---

## 8）常见反模式

- 把 profile 逻辑硬编码在多个位置。
- 将工具注册逻辑与提示词格式化耦合。
- 默认给所有 profile 开启高开销 hooks。
- profile 名与模型 ID 强绑定且没有回退方案。

---

## 9）最小落地步骤

1. 增加 profile dataclass + registry。
2. 增加一个 valve：`AGENT_PROFILE`。
3. 增加 session_config 工厂函数。
4. 将现有行为作为 default profile。
5. 再加 `analyst`、`reviewer` 两个 profile 并验证。

---

## 10）当前 Pipe 的 SDK 能力差距（高价值项）

当前 pipe 已实现不少高级能力：

- `SessionConfig` 里的 `tools`、`system_message`、`infinite_sessions`、`provider`、`mcp_servers`
- session 的 resume/create 路径
- `list_models()` 模型缓存路径
- `session.send(...)` 附件传递
- hooks 接入（目前仅 `on_post_tool_use`）

但仍有高价值能力未实现或仅部分实现：

### A. `on_user_input_request`（ask-user 交互回路）

**价值**
- 任务不明确时可主动追问，降低错误假设和幻觉。

**现状**
- 尚未接入 `create_session(...)`。

**实现建议**
- 增加 valves：
    - `ENABLE_USER_INPUT_REQUEST: bool`
    - `DEFAULT_USER_INPUT_ANSWER: str`
- 在 `session_params` 中注入：
    - `session_params["on_user_input_request"] = handler`

### B. 完整生命周期 hooks（不仅 `on_post_tool_use`）

**价值**
- 增强策略控制与可观测性。

**现状**
- 目前只实现了 `on_post_tool_use`。

**实现建议**
- 增加可选 handler：
    - `on_pre_tool_use`
    - `on_user_prompt_submitted`
    - `on_session_start`
    - `on_session_end`
    - `on_error_occurred`

### C. Provider 类型覆盖缺口（`azure`）

**价值**
- 企业 Azure OpenAI 场景可直接接入。

**现状**
- valve 仅支持 `openai | anthropic`。

**实现建议**
- 扩展枚举支持 `azure`。
- 增加 `BYOK_AZURE_API_VERSION`。
- 选择 azure 时构造 provider 的 `azure` 配置块。

### D. Client 传输配置未暴露（`cli_url` / `use_stdio` / `port`）

**价值**
- 支持远程/共享 Copilot 服务，便于部署与调优。

**现状**
- `_build_client_config` 仅设置 `cli_path/cwd/config_dir/log_level/env`。

**实现建议**
- 增加 valves：
    - `COPILOT_CLI_URL`
    - `COPILOT_USE_STDIO`
    - `COPILOT_PORT`
- 在 `client_config` 中按需注入。

### E. 前台会话生命周期 API 未使用

**价值**
- 多会话/运维场景下可增强可控性与可视化。

**现状**
- 尚未显式使用：
    - `get_foreground_session_id()`
    - `set_foreground_session_id()`
    - `client.on("session.foreground", ...)`

**实现建议**
- 作为 debug/admin 高级功能逐步接入。

---

## 11）建议实现优先级

1. `on_user_input_request`（收益高、风险低）
2. 完整 lifecycle hooks（收益高、风险中）
3. Azure provider 支持（企业价值高）
4. client 传输配置 valves（`cli_url/use_stdio/port`）
5. 前台会话生命周期 API（高级可选）
