# aw-ci-audit 中文对照

对应源文件：`.github/workflows/aw-ci-audit.md`

用途：这是一份给维护者 review 用的中文对照说明，不是 gh-aw 工作流源文件，也不参与 `gh aw compile`。

## 工作流定位

这个工作流的目标是做“CI / 自动化健康审计”。

它不是日志转储器，也不是自动修复器，而是用于：

- 检查近期仓库自动化是否出现可重复的失败模式
- 分析 release、publish、stats 等关键工作流的薄弱点
- 只在有新且可操作的诊断结论时，创建一条维护 issue

如果没有新的可操作诊断，或者问题已经被现有 issue 覆盖，就执行 `noop`。

## Frontmatter 对照

### 触发方式

- `schedule: daily`
- `workflow_dispatch`
- `roles: all`
- `skip-bots`
  - `github-actions`
  - `copilot`
  - `dependabot`
  - `renovate`

说明：这套设计更适合“定期体检 + 手动补查”，而不是直接绑到不确定的 workflow failure 事件上。

### 权限

当前设计为只读：

- `contents: read`
- `issues: read`
- `pull-requests: read`
- `actions: read`

说明：工作流只做诊断分析，不改代码、不发 release、不创建 PR。

### Safe Outputs

已配置：

- `create-issue`
  - 标题前缀：`[ci-audit] `
  - labels：`ci-audit`、`maintenance`
  - 不自动关闭旧 issue

最终只能二选一：

- 有新且可操作的诊断时执行 `create_issue`
- 无新问题时执行 `noop`

### 工具

- `github`
  - `repos`
  - `issues`
  - `pull_requests`
- `bash`
  - 仅开放只读类命令，如 `pwd`、`ls`、`cat`、`rg`、`git diff`、`git show`

## 正文指令对照

## 主要目标

要求代理审计：

- release 相关 workflow 的失败或波动
- 插件发布失败
- 社区统计更新回归
- 重复出现的 workflow 脆弱点
- 维护者真正可以执行的下一步动作

明确限制：

- 只做诊断
- 不改文件
- 不推代码
- 不开 PR
- 不发 release

## 高优先级依据文件

在形成结论前，优先把这些文件当成“自动化规则源”：

- `.github/copilot-instructions.md`
- `.github/workflows/release.yml`
- `.github/workflows/publish_plugin.yml`
- `.github/workflows/publish_new_plugin.yml`
- `.github/workflows/plugin-version-check.yml`
- `.github/workflows/community-stats.yml`
- `docs/development/gh-aw-integration-plan.md`
- `docs/development/gh-aw-integration-plan.zh.md`

## 重点关注的目标工作流

优先检查：

- `release.yml`
- `publish_plugin.yml`
- `publish_new_plugin.yml`
- `plugin-version-check.yml`
- `community-stats.yml`
- `deploy.yml`

如果这些没有明显问题，不要无限扩大范围。

## 审查范围

聚焦“近期失败或可疑自动化信号”，并优先给出基于本仓库结构的诊断，而不是泛泛的 CI 建议。

它应该像“在看仓库自动化健康趋势的维护者”，而不是普通日志摘要机器人。

## 重点检查项

### 1. Release 与 Publish 失败

检查近期失败是否指向这些可操作问题：

- 版本提取或比较逻辑漂移
- release note 打包缺口
- publish 脚本的认证或环境问题
- workflow 中的结构假设已经不匹配当前仓库
- 如果不改仓库逻辑，就可能持续复现的失败

### 2. Stats 与定时任务稳定性

检查定时维护任务是否出现这些脆弱点：

- community stats 该提交时不再提交
- badge / docs 生成逻辑过时
- 依赖外部 API 的任务反复因同类原因失败
- schedule 驱动任务制造低价值噪音

### 3. 维护者信号质量

只有当结论“真的值得维护者处理”时，才创建 issue。

适合开 issue 的情况：

- 同类失败在多次运行中重复出现
- workflow 逻辑与当前仓库结构不匹配
- 大概率缺 secret / 权限 / 路径假设过时
- 重复出现的低信号失败值得过滤或加固

不要为一次性噪音失败开 issue，除非它很可能复发。

### 4. 已有 Issue 感知

在创建新 issue 前，先判断是否已有 open issue 覆盖同一类 CI 问题。

如果已有 issue 已经足够覆盖，就优先 `noop`，避免制造重复单。

## 严重级别

只允许三档：

- `High`
  - 高概率重复发生，且会持续影响仓库自动化
- `Medium`
  - 建议尽快修，以降低维护成本或 workflow 漂移
- `Low`
  - 可选的稳健性增强或清理建议

并且明确要求：

- 不要为了开 issue 而硬造问题

## Issue 格式

如果要创建 issue，必须只有一条维护 issue。

要求：

- 英文
- 简洁
- 先写 findings，不写空泛表扬
- 带可点击路径引用
- 不用嵌套列表
- 不要粘贴大段原始日志，除非短摘录确实必要

固定结构：

```markdown
## CI Audit

### Summary
Short diagnosis of the failure pattern or automation risk.

### Findings
- `path/to/file`: specific problem or likely root cause

### Suggested Next Steps
- concrete maintainer action
- concrete maintainer action

### Notes
- Mention whether this appears recurring, new, or already partially mitigated.
```

补充规则：

- 正常情况下控制在约 300 词以内
- 如果是相关联的问题，合并成一个 issue，不要拆多个
- 优先提交“单个可执行诊断”，而不是大杂烩

## No-Issue 规则

如果没有值得报告的新诊断：

- 不要创建状态汇报型 issue
- 不要复述 workflows 看起来健康
- 直接走 `noop`

示例：

```json
{"noop": {"message": "No action needed: reviewed recent repository automation signals and found no new actionable CI diagnosis worth opening as a maintenance issue."}}
```

## 建议执行流程

1. 检查近期仓库自动化上下文
2. 优先检查目标工作流
3. 识别可重复或仓库特定的失败模式
4. 判断该问题是否已被 open issue 覆盖
5. 只有在诊断“新且可操作”时，才起草最短有用的维护 issue
6. 最终只执行一次 `create_issue` 或一次 `noop`

## 额外约束

- 不要为单次低信号瞬时失败开 issue
- 除非失败模式非常明确，否则不要顺势要求大规模重构
- 优先给出仓库特定原因，而不是泛泛的“重试试试”
- 如果根因不确定，要把不确定性写明
- 如果现有 issue 已经覆盖，优先 `noop` 而不是重复开单

## 最终要求

必须以且仅以一次 safe output 结束：

- 有新且可操作的诊断：`create_issue`
- 无新问题：`noop`
