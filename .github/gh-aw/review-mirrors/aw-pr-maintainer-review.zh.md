# aw-pr-maintainer-review 中文对照

对应源文件：`.github/workflows/aw-pr-maintainer-review.md`

用途：这是一份给维护者 review 用的中文对照说明，不是 gh-aw 工作流源文件，也不参与 `gh aw compile`。

## 工作流定位

这个工作流的目标是对触发 PR 做一次“维护者语义审查”。

它不是通用 code review 机器人，也不是自动修复器，而是用来检查以下问题：

- 是否违反本仓库插件开发规范
- 是否缺失应同步更新的 README / README_CN / docs 镜像文件
- 是否存在发布准备层面的遗漏
- 是否引入明显的高风险行为回归

如果 PR 已经足够合规，没有可操作的维护者反馈，就不评论，而是执行 `noop`。

## Frontmatter 对照

### 触发方式

- `pull_request`
  - 类型：`opened`、`reopened`、`synchronize`、`ready_for_review`
  - 路径限制：
    - `plugins/**`
    - `docs/**`
    - `.github/**`
    - `README.md`
    - `README_CN.md`
- `workflow_dispatch`
- `roles: all`
- `skip-bots`
  - `github-actions`
  - `copilot`
  - `dependabot`
  - `renovate`

### 权限

当前设计为只读：

- `contents: read`
- `issues: read`
- `pull-requests: read`

说明：工作流不会直接改代码，也不会提交 review comment 之外的写操作。

### Safe Outputs

已配置：

- `add-comment`
  - 目标：当前触发 PR
  - 最多 1 条
  - 隐藏旧评论
  - 不加 footer

同时要求最终必须二选一：

- 有问题时执行 `add_comment`
- 无问题时执行 `noop`

### 工具

- `github`
  - `repos`
  - `issues`
  - `pull_requests`
- `bash`
  - 仅开放只读类命令，如 `pwd`、`ls`、`cat`、`rg`、`git diff`、`git show`

## 正文指令对照

## 主要目标

要求代理审查：

- 仓库标准合规性
- 缺失的同步更新文件
- 发布准备缺口
- 文档漂移
- 插件代码中的高风险回归

明确限制：

- 只做 review
- 不改文件
- 不推代码
- 不创建 PR

## 高优先级依据文件

在形成结论前，优先把这些文件当成“本仓库规则源”：

- `.github/copilot-instructions.md`
- `.github/instructions/code-review.instructions.md`
- `.github/instructions/commit-message.instructions.md`
- `.github/skills/release-prep/SKILL.md`
- `.github/skills/doc-mirror-sync/SKILL.md`
- `docs/development/gh-aw-integration-plan.md`
- `docs/development/gh-aw-integration-plan.zh.md`

## 审查范围

- 先看 PR diff 和 changed files
- 只有在验证一致性时，才扩展读取关联文件
- 优先遵循“仓库特定规则”，而不是泛泛的最佳实践

换句话说，它应该像“熟悉本仓库的维护者”，而不是通用 lint bot。

## 重点检查项

### 1. 插件代码规范

当 `plugins/**/*.py` 变化时，重点看：

- 是否保持单文件 i18n 模式
- 用户可见文本是否进入翻译字典
- 是否使用 `_get_user_context` 和 `_get_chat_context`
- `__event_call__` 的 JS 执行是否具备 timeout 防护和前端兜底
- 是否引入 `print()` 到生产插件代码
- emitter 是否安全判空
- filter 插件是否把请求级可变状态塞到 `self`
- Copilot SDK / OpenWebUI tool 定义是否仍符合仓库规范

### 2. 版本与发布卫生

当 `plugins/**/*.py` 改动时，检查是否“应该同步但没同步”：

- 插件 docstring 的 `version:`
- 插件目录下 `README.md`
- 插件目录下 `README_CN.md`
- `docs/plugins/**` 下的镜像页面
- `docs/plugins/{type}/index.md` 等索引文件
- 如果是明显 release-prep 类型 PR，再看根 `README.md` 和 `README_CN.md` 日期 badge

这里的关键语义是：

- 不是每个 PR 都必须当发布处理
- 只有在“用户可见行为、元数据、版本化文档、发布面内容”发生变化时，才提示缺失同步

### 3. 文档同步

当插件 README 改动时，检查是否应同步 docs 镜像：

- `plugins/actions/{name}/README.md` -> `docs/plugins/actions/{name}.md`
- `plugins/actions/{name}/README_CN.md` -> `docs/plugins/actions/{name}.zh.md`
- `plugins/filters/{name}/README.md` -> `docs/plugins/filters/{name}.md`
- `plugins/filters/{name}/README_CN.md` -> `docs/plugins/filters/{name}.zh.md`
- `plugins/pipes/{name}/README.md` -> `docs/plugins/pipes/{name}.md`
- `plugins/pipes/{name}/README_CN.md` -> `docs/plugins/pipes/{name}.zh.md`
- `plugins/pipelines/{name}/README.md` -> `docs/plugins/pipelines/{name}.md`
- `plugins/pipelines/{name}/README_CN.md` -> `docs/plugins/pipelines/{name}.zh.md`
- `plugins/tools/{name}/README.md` -> `docs/plugins/tools/{name}.md`
- `plugins/tools/{name}/README_CN.md` -> `docs/plugins/tools/{name}.zh.md`

如果是 docs-only 且明显有意为之，不要过度报错。

### 4. PR 质量

只在“确实让维护者审查变难”时，才指出 PR 描述缺失这些内容：

- 改了什么
- 为什么改
- 是否需要迁移或重新配置

## 严重级别

只允许三档：

- `Blocking`
  - 大概率 bug、发布回归、缺少必需同步、严重规范破坏
- `Important`
  - 应该合并前修，但不一定是直接运行时错误
- `Minor`
  - 建议项，可选

并且明确要求：

- 不要为了留言而硬凑问题

## 评论格式

如果要评论，必须只有一条总结评论。

要求：

- 英文
- 简洁
- 先给 findings，不先夸赞
- 带可点击路径引用
- 不使用嵌套列表
- 不要机械复述 diff

固定结构：

```markdown
## PR Maintainer Review

### Blocking
- `path/to/file`: specific issue and why it matters

### Important
- `path/to/file`: specific issue and what sync/check is missing

### Minor
- `path/to/file`: optional improvement or consistency note

### Merge Readiness
- Ready after the items above are addressed.
```

补充规则：

- 空 section 要省略
- 如果只有一个严重级别，只保留那个 section 和 `Merge Readiness`
- 正常情况下控制在约 250 词以内

## No-Comment 规则

如果没有有意义的维护者反馈：

- 不要发“看起来不错”这类表扬评论
- 不要复述 checks passed
- 直接走 `noop`

示例：

```json
{"noop": {"message": "No action needed: reviewed the PR diff and repository sync expectations, and found no actionable maintainer feedback."}}
```

## 建议执行流程

1. 找出变更文件
2. 读取高优先级规则文件
3. 对照插件审查规范检查插件代码
4. 对照 doc mirror 规则检查 README / docs
5. 判断是否缺失 version sync 或 release-facing 文件
6. 先起草最短但有用的维护者总结
7. 最终只执行一次 `add_comment` 或一次 `noop`

## 额外约束

- 不要要求与本 PR 无关的大重构
- 小型内部变更不要强拉成 release-prep
- 明显是私有/内部改动时，不要强制要求 docs sync
- 优先给出“仓库特定”的反馈，而不是通用 code review 废话
- 如果你不确定某个同步文件是否必需，把级别降为 `Important`
- 如果问题依赖 PR 意图但当前信息不足，要把表述写成“条件性判断”，不要装作确定

## 最终要求

必须以且仅以一次 safe output 结束：

- 有可操作反馈：`add_comment`
- 无可操作反馈：`noop`

## Review 结论

这份英文源工作流目前已经可以作为后续 `gh aw compile` 的候选源文件。

中文镜像的目的只有两个：

- 方便你逐段审阅策略是否符合预期
- 避免把中文说明混进真正要编译的 workflow 源文件
