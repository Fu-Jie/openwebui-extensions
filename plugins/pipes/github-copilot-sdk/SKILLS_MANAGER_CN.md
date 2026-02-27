# manage_skills 工具指南

本文档说明 GitHub Copilot SDK Pipe 中的 `manage_skills` **工具**。

> 重点：`manage_skills` 是工具（tool），不是 skill。

---

## 核心模型

插件只使用**一个** skill 安装/同步目录：

- `OPENWEBUI_SKILLS_SHARED_DIR/shared/`

不存在额外的“manager skill 目录”或按工作区分裂的安装目录。

---

## Skill 目录结构

所有 skills 统一放在同一个目录下：

```text
{OPENWEBUI_SKILLS_SHARED_DIR}/shared/
├── finance-reporting/
│   ├── SKILL.md
│   ├── .owui_id
│   ├── scripts/
│   └── templates/
├── docs-writer/
│   ├── SKILL.md
│   └── .owui_id
└── ...
```

- `SKILL.md` 为必需文件。
- `.owui_id` 用于关联 OpenWebUI 数据库记录。
- `scripts/`、`templates/`、`references/` 等为可选资源文件。

---

## `manage_skills` 可以做什么

`manage_skills` 提供确定性的 skill 生命周期操作：

- `list`
- `install`
- `create`
- `edit`
- `show`
- `delete`

建议将 skill 的增删改查统一通过该工具完成，避免脆弱的临时 shell 流程。

---

## 同步机制 (本地文件 ↔ OpenWebUI 数据库)

SDK 在本地文件系统与 OpenWebUI 数据库之间执行**实时双向同步**，以确保一致性。

### 工作原理

1.  **身份绑定**：每个本地 skill 文件夹内包含一个隐藏的 `.owui_id` 文件。它是将文件夹链接到 OpenWebUI 数据库中特定记录的“粘合剂”。
2.  **冲突处理**：
    -   **内容哈希**：SDK 首先比较本地 `SKILL.md` 与数据库中指令的内容哈希 (MD5)。若一致，则不执行同步。
    -   **时间戳校验**：若内容不同，则比较文件的 `mtime` 与数据库的 `updated_at`。时间较新的一方将覆盖另一方。
3.  **操作同步场景**：
    -   **手动编辑 (文件系统)**：若你通过 VS Code 或终端修改了 `SKILL.md`，下次 SDK 请求时会自动将改动推送到 OpenWebUI 前端。
    -   **界面编辑 (OpenWebUI)**：若你在 OpenWebUI 工作区中修改了指令内容，SDK 会拉取变更并覆写本地的 `SKILL.md`。
    -   **工具操作**：调用 `manage_skills(action="create")` 或 `action="delete"` 会立即触发与数据库的原子同步。

> **警告**：除非你想“取消关联”并强制 SDK 将该技能注册为新条目，否则请勿手动删除 `.owui_id` 文件。

---

## 典型工作流 (典型问题示例)

### 1. 从 GitHub URL 安装 Skill

**用户提问：** "帮我安装这个数据分析 skill：`https://github.com/user/skills/blob/main/data-visualizer/SKILL.md`"
**工具调用：** `manage_skills(action="install", url="https://github.com/user/skills/blob/main/data-visualizer/SKILL.md")`
**结果：**

- 文件下载至 `{OPENWEBUI_SKILLS_SHARED_DIR}/shared/data-visualizer/`
- Skill 元数据自动同步至 OpenWebUI 数据库。

### 2. 一次安装多个来自不同 URL 的 Skills

**用户提问：** "帮我安装这三个 skill：URL1、URL2、URL3"
**工具调用：** `manage_skills(action="install", url=["URL1", "URL2", "URL3"])`
**结果：**

- Agent 将 `url` 传入为列表，SDK 依次下载、解压并安装每个 URL 对应的 skill 到 `shared/` 目录。
- 所有安装完成后，执行一次统一的数据库同步，避免重复触发。
- 若某个 URL 失败，其余 URL 的安装仍会继续，失败信息汇总在 `errors` 字段中返回。

### 3. 从单个仓库一次安装所有 Skills

**用户提问：** "安装 `https://github.com/myorg/skill-pack/tree/main/` 下的所有 skill"
**工具调用：** `manage_skills(action="install", url="https://github.com/myorg/skill-pack/tree/main/")`
**结果：**

- SDK 自动扫描目录下所有包含 `SKILL.md` 的子文件夹，一次性批量安装。

### 4. 从当前对话创建新 Skill

**用户提问：** "把我们刚才讨论的 Python 代码清理逻辑保存为一个名为 'py-clean' 的新 skill"
**工具调用：** `manage_skills(action="create", name="py-clean", content="...")`
**结果：**

- 在 `{OPENWEBUI_SKILLS_SHARED_DIR}/shared/py-clean/` 创建新目录。
- 写入 `SKILL.md` 并同步至数据库。

---

## 推荐配置

- `ENABLE_OPENWEBUI_SKILLS=True`
- `OPENWEBUI_SKILLS_SHARED_DIR=/app/backend/data/cache/copilot-openwebui-skills`
- 可选黑名单：`DISABLED_SKILLS=skill-a,skill-b`

---

## 注意事项

- 不要把 skill 名称当作 shell 命令执行。
- skill 生命周期管理请优先使用 `manage_skills` 工具。
- 所有已安装 skills 统一维护在一个目录：`.../shared/`。
