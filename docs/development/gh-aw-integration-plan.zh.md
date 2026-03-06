# gh-aw 集成方案

> 本文档用于为 `openwebui-extensions` 仓库设计一套安全、渐进式的 GitHub Agentic Workflows (`gh-aw`) 接入方案。

---

## 1. 目标

- 在不替换现有稳定 CI 的前提下，引入具备仓库理解能力的 AI 维护层。
- 将 `gh-aw` 用于更适合自然语言推理的任务，而不是机械脚本执行。
- 保留当前发布、部署、发布插件和统计工作流作为执行骨架。
- 为仓库维护引入可观测性、自动诊断和长期记忆能力。

---

## 2. 为什么这个仓库适合 gh-aw

本仓库已经有一套很强的确定性自动化：

- `/.github/workflows/release.yml`
- `/.github/workflows/plugin-version-check.yml`
- `/.github/workflows/deploy.yml`
- `/.github/workflows/publish_plugin.yml`
- `/.github/workflows/community-stats.yml`

这些工作流擅长精确执行，但并不擅长理解仓库规范本身。

`gh-aw` 更适合以下任务：

- 联合阅读代码、文档和 PR 描述后再做判断
- 带语义地应用仓库规范
- 生成结构化的 review 评论
- 自动分析失败的工作流运行
- 在多次运行之间保存维护经验和模式

这与当前仓库的真实需求高度匹配：

- 双语文档同步
- 插件代码、README 与 docs 一致性检查
- 跨多个文件的发布前完整性核查
- Issue 与 PR 的规模化维护

---

## 3. 非目标

第一阶段不建议让 `gh-aw`：

- 替换 `release.yml`
- 替换 `publish_plugin.yml`
- 替换 MkDocs 部署
- 默认自动合并或自动推送代码
- 一开始就拥有过宽的写权限

第一阶段应把它定位为 review、诊断和 preflight 层。

---

## 4. 接入原则

### 4.1 确定性执行继续由 YAML 工作流承担

现有 YAML workflow 继续负责：

- 创建 release
- 发布插件
- 部署文档
- 提取和比较版本号
- 生成社区统计

### 4.2 Agentic workflow 只负责判断和总结

`gh-aw` workflow 优先承担：

- 基于规范的语义审查
- 发布前完整性检查
- 文档漂移巡检
- CI 失败原因分析
- Issue 分流与回复草稿生成

### 4.3 默认只读

优先使用最小权限，并通过 safe outputs 进行受控评论或低风险输出。

### 4.4 逐步扩容

一次只上线一个 agentic workflow，验证质量后再扩大范围。

---

## 5. 建议的仓库结构

### 5.1 新增文件和目录

```text
.github/
├── workflows/
│   ├── release.yml
│   ├── plugin-version-check.yml
│   ├── deploy.yml
│   ├── publish_plugin.yml
│   ├── community-stats.yml
│   ├── aw-pr-maintainer-review.md
│   ├── aw-pr-maintainer-review.lock.yml
│   ├── aw-release-preflight.md
│   ├── aw-release-preflight.lock.yml
│   ├── aw-ci-audit.md
│   ├── aw-ci-audit.lock.yml
│   ├── aw-docs-drift-review.md
│   └── aw-docs-drift-review.lock.yml
├── gh-aw/
│   ├── prompts/
│   │   ├── pr-review-policy.md
│   │   ├── release-preflight-policy.md
│   │   ├── ci-audit-policy.md
│   │   └── docs-drift-policy.md
│   ├── schemas/
│   │   └── review-output-example.json
│   └── README.md
└── copilot-instructions.md
```

### 5.2 命名规范

所有 agentic workflow 源文件统一使用 `aw-` 前缀：

- `aw-pr-maintainer-review.md`
- `aw-release-preflight.md`
- `aw-ci-audit.md`
- `aw-docs-drift-review.md`

这样做的原因：

- 可以和现有手写 YAML 工作流明确区分
- 便于在仓库中快速搜索和定位
- 方便调试和发布时识别来源

### 5.3 为什么不直接替换 `.yml`

当前 `.yml` 文件承担的是生产执行逻辑。第一阶段 `gh-aw` 的角色应该是补充，而不是接管。

---

## 6. 建议优先建设的 workflow 组合

### 6.1 第一阶段：PR 维护者语义审查

**文件**: `/.github/workflows/aw-pr-maintainer-review.md`

**作用**:

- 审查涉及插件、文档或开发规范的 PR
- 对缺失的仓库标准更新给出评论
- 作为 `plugin-version-check.yml` 之上的语义层

**建议检查项**:

- 插件代码修改后是否更新版本号
- 是否同时更新 `README.md` 和 `README_CN.md`
- 是否同步更新 docs 镜像页
- 是否需要更新根 README 的日期 badge
- 插件代码是否遵守 i18n 与 helper 规范
- PR 标题或正文是否符合 Conventional Commits 精神

**建议权限**:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

**建议工具**:

- 只读型 `github:` 工具
- 只开放少量只读 `bash:` 命令
- 第一阶段不开放 `edit:`
- `agentic-workflows:` 可在后续成熟后再启用

### 6.2 第一阶段：发布前预检

**文件**: `/.github/workflows/aw-release-preflight.md`

**作用**:

- 在 release 前或手动触发时执行
- 在 `release.yml` 打包和发布之前，先检查发布完整性

**建议检查项**:

- 代码版本号和文档版本号是否一致
- 双语 README 是否完整更新
- docs 插件镜像页是否存在并匹配当前发布目标
- release notes 来源文件是否齐全
- commit message 与 release 草案是否连贯

**输出方式**:

- 在 PR 或 issue 中写总结评论
- 可附带 checklist artifact
- 不直接执行正式发布

### 6.3 第二阶段：CI 失败自动审计

**文件**: `/.github/workflows/aw-ci-audit.md`

**作用**:

- 分析 `release.yml`、`publish_plugin.yml`、`community-stats.yml` 等关键 workflow 的失败运行
- 输出根因判断和下一步修复建议

**适合 gh-aw 的原因**:

- 可以通过 `gh aw mcp-server` 使用 `logs`、`audit` 等能力
- 原生支持对 workflow 执行痕迹进行事后分析

### 6.4 第二阶段：文档漂移巡检

**文件**: `/.github/workflows/aw-docs-drift-review.md`

**作用**:

- 定期检查插件代码、插件目录 README、本地 docs 镜像和根索引之间是否发生漂移

**建议检查项**:

- 是否缺少 `README_CN.md`
- README 章节顺序是否偏离规范
- 插件更新后 docs 页面是否缺失
- 代码和文档中的版本号是否不一致

### 6.5 第三阶段：Issue 维护助手

**候选文件**: `/.github/workflows/aw-issue-maintainer.md`

**作用**:

- 汇总长期未回复的 issue
- 生成英文或双语回复草稿
- 按插件归类重复问题

这个阶段建议在前面的 review 和 audit 流程稳定后再上线。

---

## 7. 与现有 workflow 的职责映射

| 当前 Workflow | 是否保留 | gh-aw 搭档 | 职责划分 |
|------|------|------|------|
| `/.github/workflows/release.yml` | 保留 | `aw-release-preflight.md` | `release.yml` 负责执行，`gh-aw` 负责判断是否已准备好 |
| `/.github/workflows/plugin-version-check.yml` | 保留 | `aw-pr-maintainer-review.md` | 硬性门禁 + 语义审查 |
| `/.github/workflows/deploy.yml` | 保留 | 初期不加 | 确定性构建和部署 |
| `/.github/workflows/publish_plugin.yml` | 保留 | `aw-ci-audit.md` | 确定性发布 + 失败诊断 |
| `/.github/workflows/community-stats.yml` | 保留 | `aw-ci-audit.md` | 确定性统计 + 异常诊断 |

---

## 8. 工具模型建议

### 8.1 第一阶段建议启用的内建工具

建议从窄权限工具集开始：

```yaml
tools:
  github:
    toolsets: [default]
  bash:
    - echo
    - pwd
    - ls
    - cat
    - head
    - tail
    - grep
    - wc
    - git status
    - git diff
```

第一阶段不要开放完全不受限的 shell。

### 8.2 MCP 使用策略

后续可通过 `gh aw mcp-server` 引入：

- workflow `status`
- workflow `compile`
- workflow `logs`
- workflow `audit`
- `mcp-inspect`

这对 `aw-ci-audit.md` 特别有价值。

### 8.3 Safe output 策略

第一阶段仅开放低风险 safe outputs：

- 给 PR 写评论
- 给 issue 写评论
- 在明确需要时创建低风险维护 issue

一开始不要让 agent 自动提交代码修改。

---

## 9. Repo Memory 策略

`gh-aw` 的 repo memory 很适合本仓库，但必须加限制。

### 9.1 第一批适合保存的内容

- 重复出现的 CI 失败模式
- 常见文档同步遗漏
- 高频 review 提醒项
- 按插件聚类的 issue 模式

### 9.2 推荐配置思路

- 只允许 `.md` 和 `.json`
- 限制 patch size
- 按主题拆成多个 memory stream

建议的逻辑布局：

```text
memory/review-notes/*.md
memory/ci-patterns/*.md
memory/issue-clusters/*.json
```

### 9.3 重要提醒

不要把 secret、token 或未公开敏感信息写入 repo memory。

---

## 10. 分阶段落地顺序

### Phase 0: 准备阶段

- 维护者本地安装 `gh-aw`
- 添加一个简短的 `/.github/gh-aw/README.md`
- 写清楚 workflow 命名规范和 review 预期

### Phase 1: 只读语义审查

- 上线 `aw-pr-maintainer-review.md`
- 上线 `aw-release-preflight.md`
- 输出先限制为总结和评论

### Phase 2: 诊断与记忆

- 上线 `aw-ci-audit.md`
- 在需要的地方启用 `agentic-workflows:`
- 为重复失败模式加入受限 `repo-memory`

### Phase 3: 维护自动化

- 增加文档漂移巡检
- 增加 issue 维护 workflow
- 只有在信号质量足够稳定后，再考虑有限度的代码修改建议

---

## 11. 维护者本地使用建议

### 11.1 安装 CLI

```bash
curl -sL https://raw.githubusercontent.com/github/gh-aw/main/install-gh-aw.sh | bash
```

### 11.2 常用命令

```bash
gh aw version
gh aw compile
gh aw status
gh aw run aw-pr-maintainer-review
gh aw logs
gh aw audit <run-id>
```

### 11.3 VS Code MCP 集成

后续可选增强项是把 `gh aw mcp-server` 加入本地 MCP 配置，这样编辑器内的 agent 会直接具备 workflow 自省能力。

---

## 12. 最小可行落地建议

建议第一步只做这两个 workflow：

1. `aw-pr-maintainer-review.md`
2. `aw-release-preflight.md`

这样可以以最低风险获得最高价值的增强。

---

## 13. 成功标准

如果接入有效，应该看到这些结果：

- PR 评论更具体，更贴合仓库规范
- 发布前能更早发现文档或版本同步遗漏
- CI 失败后更快得到可执行的总结
- 维护者花在重复性规范检查上的时间下降
- 现有确定性 workflow 的核心行为保持稳定

---

## 14. 总结

对 `openwebui-extensions` 来说，`gh-aw` 最合适的定位是智能维护层。

- 现有 YAML workflow 继续负责执行。
- agentic workflow 负责语义审查和诊断。
- 第一阶段默认只读。
- 等输出质量稳定后再逐步放权。

这条路径和仓库现状是匹配的：规范密度高、双语维护复杂、插件生命周期长，而且已经具备成熟的 AI 工程上下文。
