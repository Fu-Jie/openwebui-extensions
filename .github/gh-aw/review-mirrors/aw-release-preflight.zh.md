# aw-release-preflight 中文对照

对应源文件：`.github/workflows/aw-release-preflight.md`

用途：这是一份给维护者 review 用的中文对照说明，不是 gh-aw 工作流源文件，也不参与 `gh aw compile`。

## 工作流定位

这个工作流的目标是对触发变更做一次“发布前预检语义审查”。

它不是发布执行器，也不是自动补版本工具，而是用于判断：

- 这次改动是否真的在做 release-prep
- 如果是在做 release-prep，版本同步是否完整
- 双语 README、docs 镜像、release notes 是否齐全
- 是否存在会影响发布质量的说明缺失或文档漂移

如果当前变更并不是发布准备，或者已经足够一致、没有可操作反馈，就执行 `noop`。

## Frontmatter 对照

### 触发方式

- `pull_request`
  - 类型：`opened`、`reopened`、`synchronize`、`ready_for_review`
  - 路径限制：
    - `plugins/**/*.py`
    - `plugins/**/README.md`
    - `plugins/**/README_CN.md`
    - `plugins/**/v*.md`
    - `plugins/**/v*_CN.md`
    - `docs/plugins/**/*.md`
    - `README.md`
    - `README_CN.md`
    - `.github/**`
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

说明：工作流不会发 release、不会推代码、不会改文件。

### Safe Outputs

已配置：

- `add-comment`
  - 目标：当前触发 PR
  - 最多 1 条
  - 隐藏旧评论
  - 不加 footer

最终只能二选一：

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

要求代理检查：

- 版本同步完整性
- 双语 README 与 docs 一致性
- release notes 完整性
- 发布面索引或 badge 漂移
- 用户可见发布是否缺失迁移说明或维护者上下文

明确限制：

- 只做 review
- 不改文件
- 不推代码
- 不创建 release
- 不创建 PR

## 高优先级依据文件

在形成结论前，优先把这些文件当成“发布规则源”：

- `.github/copilot-instructions.md`
- `.github/instructions/commit-message.instructions.md`
- `.github/skills/release-prep/SKILL.md`
- `.github/skills/doc-mirror-sync/SKILL.md`
- `.github/workflows/release.yml`
- `docs/development/gh-aw-integration-plan.md`
- `docs/development/gh-aw-integration-plan.zh.md`

## 审查范围

- 从 PR diff 和 changed files 开始
- 只有在验证发布同步时才扩展到相关 release-facing 文件
- 优先遵循仓库既有 release-prep 规则，而不是泛泛的 release 建议

换句话说，它应该像“合并前最后做一致性复核的维护者”。

## 重点检查项

### 1. 发布相关文件中的版本同步

当某个插件明显在准备发版时，检查这些位置是否同步：

- 插件 Python docstring 的 `version:`
- 插件目录下 `README.md`
- 插件目录下 `README_CN.md`
- `docs/plugins/**` 英文镜像页
- `docs/plugins/**/*.zh.md` 中文镜像页
- `docs/plugins/{type}/index.md` 中该插件的条目或版本 badge
- `docs/plugins/{type}/index.zh.md` 中该插件的条目或版本 badge

但只有在“这次改动明显带有发布意图”时才提示，不要把所有 PR 都按发布处理。

### 2. README 与 docs 镜像一致性

当插件 README 变化时，检查 docs 镜像是否同步。

路径映射：

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

如果是纯文档调整、而且并非发版预备，不要过度报错。

### 3. What's New 与 Release Notes 覆盖度

当这次更新明显是发布面插件更新时，检查：

- `What's New` 是否只反映最新版本
- `最新更新` 是否与英文对应
- 是否存在 `v{version}.md` 和 `v{version}_CN.md`
- release notes 是否覆盖当前 diff 中有意义的功能、修复、文档或迁移变化

对纯内部小改动，不要强制要求 release notes。

### 4. 根 README 与发布面索引漂移

当改动明显面向正式发布时，再检查：

- 根 `README.md` 的日期 badge
- 根 `README_CN.md` 的日期 badge
- `docs/plugins/**/index.md`
- `docs/plugins/**/index.zh.md`

不要把这种检查强加给普通内部 PR。

### 5. 维护者上下文与发布清晰度

检查 PR 描述或发布面文案是否缺少关键上下文：

- 这次到底发布了什么
- 为什么这次发布值得做
- 是否需要迁移或重新配置

只有在缺失信息会明显增加 release review 成本时，才提示。

## 严重级别

只允许三档：

- `Blocking`
  - 高概率发布回归、缺少必要版本同步、发布面更新明显不完整
- `Important`
  - 合并前最好修，避免发布混乱或文档漂移
- `Minor`
  - 可选的发布面清理或一致性建议

并且明确要求：

- 不要为了留言而造问题

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
## Release Preflight Review

### Blocking
- `path/to/file`: specific release-facing problem and why it matters

### Important
- `path/to/file`: missing sync or release-documentation gap

### Minor
- `path/to/file`: optional cleanup or consistency improvement

### Release Readiness
- Ready after the items above are addressed.
```

补充规则：

- 空 section 要省略
- 如果只有一个严重级别，只保留那个 section 和 `Release Readiness`
- 正常情况下控制在约 250 词以内

## No-Comment 规则

如果没有有意义的发布前预检反馈：

- 不要发“看起来不错”这类表扬评论
- 不要复述 checks passed
- 直接走 `noop`

示例：

```json
{"noop": {"message": "No action needed: reviewed the release-facing diff, version-sync expectations, and bilingual documentation coverage, and found no actionable preflight feedback."}}
```

## 建议执行流程

1. 判断这次改动是否真的带有发布意图
2. 检查 PR diff 中的变更文件
3. 读取仓库的 release-prep 规则文件
4. 只有在存在发布意图时，才检查 plugin version sync
5. 检查 README、README_CN、docs 镜像、索引和 release notes 是否漂移
6. 起草最短但有用的维护者总结
7. 最终只执行一次 `add_comment` 或一次 `noop`

## 额外约束

- 不要把完整 release-prep 要求硬套到微小内部改动上
- 非明确发布型 PR，不要强制要求根 README 日期 badge 更新
- 如果这次改动并不现实地构成发版预备，就不要强求 release notes
- 优先给出仓库特定的同步反馈，而不是泛泛的发布建议
- 如果不确定某个 release-facing 同步文件是否必需，把级别降为 `Important`
- 如果问题依赖“推测出来的意图”，要用条件式表述，不要装作确定

## 最终要求

必须以且仅以一次 safe output 结束：

- 有可操作反馈：`add_comment`
- 无可操作反馈：`noop`
