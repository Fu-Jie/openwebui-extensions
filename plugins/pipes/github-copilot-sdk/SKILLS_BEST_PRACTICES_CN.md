# Skills 使用最佳实践

编写、组织和维护 Copilot SDK Skills 的简明指南。

---

## 理解 Skills 的工作机制

Skills **不是命令行工具**，而是**上下文注入的指令集**：

1. Copilot SDK 守护进程读取 `skill_directories` 中每个 `SKILL.md` 文件
2. 提取每个 skill 的 YAML `description` 字段
3. 用户发消息时，SDK 将用户意图与所有 description 进行语义匹配
4. 匹配成功后，SDK 触发 `skill.invoked` 事件，将完整的 **SKILL.md 正文注入对话上下文**
5. Agent 读取这些指令，使用 `bash`、`create_file`、`view_file` 等工具来执行

**关键理解**：永远不要把 skill 的名字当作 bash 命令来运行（例如 `finance-reporting`）。Skill 本身就是指令，而不是可执行文件。

---

## 写好 `description` 字段

`SKILL.md` frontmatter 中的 `description` 是 **主要触发机制**，SDK 用它做语义路由。

### 应该这样做 ✅

- 以动词开头："管理…"、"生成…"、"分析…"
- 明确写出 "Use when:" 场景——这是最可靠的触发信号
- 覆盖用户可能表达同一需求的多种说法

```yaml
description: 根据大纲或主题生成 PowerPoint 演示文稿。
  Use when: 创建幻灯片、制作演讲稿、导出 PPTX 文件、做 PPT。
```

### 不要这样做 ❌

- 模糊描述："一个有用的多功能工具"
- 与其他 skill 描述重叠（会造成误触发）
- 省略 "Use when:" 示例（大幅降低触发准确率）

### 实用经验

如果两个人会用不同方式表达同一需求（如"做个幻灯片"vs"制作一个演讲 deck"），两种说法都应该出现在 description 中。

---

## 目录结构：什么放在哪里

```
skill-name/
├── SKILL.md          ← 必须。Frontmatter + 核心指令
├── .owui_id          ← 自动生成，禁止编辑或删除
├── references/       ← 可选。补充文档，按需加载
│   └── advanced.md
├── scripts/          ← 可选。辅助脚本（Shell/Python）
└── assets/           ← 可选。模板、样例文件、静态数据
```

### 何时用 `references/`

当内容属于以下情况时放入 `references/`：

- 仅边缘场景或高级用法才需要
- 内容太长，每次都注入会浪费上下文（> 约 100 行）
- 纯参考资料（API 规格、格式文档、示例）

使用"渐进式披露"：Agent 先读 `SKILL.md`，仅在任务需要时才加载特定 reference 文件：

```markdown
## 高级导出选项

详见 [references/export-options.md](references/export-options.md)。
```

### 何时内联在 `SKILL.md`

当内容属于以下情况时留在 `SKILL.md`：

- 每次运行 skill 都需要
- 足够短，不会拖慢上下文注入（总计 < 约 150 行）
- 是 skill 主流程的核心内容

---

## 命名约定

| 内容 | 规范 | 示例 |
|---|---|---|
| Skill 目录名 | `kebab-case` | `export-to-pptx` |
| Frontmatter `name` 字段 | `kebab-case`，与目录名一致 | `export-to-pptx` |
| 脚本文件名 | `snake_case.py` 或 `.sh` | `build_slide.py` |
| Reference 文件名 | `kebab-case.md` | `advanced-options.md` |

Skill 目录名避免空格和大写字母——SDK 使用目录名作为 skill 标识符。

---

## 编写高效的 SKILL.md 指令

### 以角色声明开头

告诉 Agent 在这个 skill 上下文中扮演什么角色：

```markdown
# 导出为 PowerPoint

你是一个演示文稿构建器。你的任务是使用本 skill 目录中的脚本，将用户的内容转换为结构清晰的 PPTX 文件。
```

### 使用祈使句步骤

用编号步骤写指令，而不是大段散文：

```markdown
1. 如果用户未提供大纲，先询问。
2. 运行 `python3 {scripts_dir}/build_slide.py --title "..." --output "{cwd}/output.pptx"`
3. 检查文件是否存在，确认成功。
4. 向用户提供文件的下载路径。
```

### 明确处理错误

告诉 Agent 出错时怎么做：

```markdown
如果脚本以非零状态码退出，将 stderr 输出展示给用户并询问如何处理。
```

### 以收尾指令结束

```markdown
任务完成后，总结创建的内容，并提醒用户文件的存放位置。
```

---

## Skill 的适用范围

每个 skill 应该**只做一件事**。以下迹象说明 skill 太宽泛了：

- description 包含 4–5 个以上涵盖不同领域的 "Use when:" 条目
- SKILL.md 超过 300 行
- 已添加超过 3 个 reference 文件

当 skill 变得过大时，进行拆分：一个父 skill 负责路由，各子 skill 负责具体功能。

---

## 管理 `shared/` 目录

`shared/` 目录与 OpenWebUI 数据库**双向同步**：

- 通过 OpenWebUI UI 创建的 skill 会自动导入 `shared/`
- Agent 在 `shared/` 中创建的 skill 在下次会话启动时导出到 OpenWebUI

### 安全操作方式

| 操作 | 方法 |
|---|---|
| 从 URL 安装 | `python3 {scripts_dir}/install_skill.py --url <url> --dest {shared_dir}` |
| 新建 skill | `mkdir -p {shared_dir}/<name>/ && 创建 SKILL.md` |
| 编辑 skill | 读取 → 修改 → 写回 `SKILL.md` |
| 删除 skill | `rm -rf {shared_dir}/<name>/`（不会删除 OpenWebUI UI 中的记录，需单独删除） |
| 列出 skills | `python3 {scripts_dir}/list_skills.py --path {shared_dir}` |

### `.owui_id` 文件

每个与 OpenWebUI 同步的 skill 都有一个 `.owui_id` 文件，里面存储数据库 UUID。**绝对不要编辑或删除此文件**——它是文件系统与 OpenWebUI 数据库之间的关联纽带。一旦删除，下次同步时该 skill 会被视为新建项，可能产生重复。

---

## 会话生命周期意识

Skills 在**会话开始时加载一次**。在会话期间做的修改，**下次会话才会生效**。

| 时间点 | 发生的事 |
|---|---|
| 会话启动 | SDK 守护进程读取所有 `SKILL.md`；`_sync_openwebui_skills` 执行双向 DB↔文件同步 |
| 会话期间 | 新建/编辑/删除的 skill 文件已在磁盘上，但守护进程尚未加载 |
| 用户开启新会话 | 新 skill 生效；修改后的 description 开始触发 |

**每次创建/编辑/删除后，必须告知用户**："此更改将在您开启新会话后生效。"

---

## 需要避免的反模式

| 反模式 | 问题所在 | 解决方式 |
|---|---|---|
| 把 `<skill名>` 当 bash 命令运行 | Skill 不是可执行文件 | 阅读 SKILL.md 指令，用标准工具执行 |
| 编辑 `.owui_id` | 破坏数据库同步 | 永远不要碰这个文件 |
| 在 SKILL.md 中存储会话状态 | SKILL.md 是静态指令，不是状态文件 | 使用工作区中的独立文件保存会话状态 |
| description 过于宽泛 | 对每条消息都误触发 | 用 "Use when:" 缩窄到具体意图 |
| 把所有逻辑写进一个 500 行的 SKILL.md | 上下文注入慢，难以维护 | 拆分为 SKILL.md + `references/*.md` |
| 在 `/tmp` 创建 skill | 不持久，SDK 找不到 | 始终在 `{shared_dir}/` 中创建 |

---

## 新建 Skill 快速检查清单

- [ ] 目录名为 `kebab-case`，与 `name` 字段一致
- [ ] `description` 以动词开头，包含 "Use when:" 示例
- [ ] SKILL.md 以角色声明开头
- [ ] 指令使用祈使句编号步骤
- [ ] 过长的参考内容已移至 `references/`
- [ ] 脚本已放入 `scripts/`
- [ ] 确认：description 与其他已加载 skill 无重叠
- [ ] 已告知用户："新 skill 在下次会话后生效"
