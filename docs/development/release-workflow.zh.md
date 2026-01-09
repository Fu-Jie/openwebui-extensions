# 插件发布工作流

本文档描述了发布插件更新的工作流程。

---

## 概述

发布工作流包含以下组件：

1. **CHANGELOG.md** - 记录所有重要更改
2. **版本提取脚本** - 自动提取插件版本信息
3. **GitHub Actions 工作流** - 自动化发布流程

---

## 自动发布流程 ⭐

当插件更新的 PR 合并到 `main` 分支时，会**自动触发**发布流程：

### PR 合并要求

修改插件文件的 PR 必须满足以下条件才能合并：

1. ✅ **版本号必须更新** - 插件的 `version` 字段必须有变化
2. ✅ **PR 描述必须包含更新说明** - 至少 20 个字符的描述

如果不满足这些条件，PR 检查会失败，无法合并。

### 自动发布内容

合并成功后，系统会自动：

1. 🔍 检测版本变化（与上次 release 对比）
2. 📝 生成发布说明（包含更新内容和提交记录）
3. 📦 创建 GitHub Release（包含可下载的插件文件）
4. 🏷️ 自动生成版本号（格式：`vYYYY.MM.DD-运行号`）

### Release 包含内容

- **plugins_release.zip** - 本次更新的所有插件文件打包
- **plugin_versions.json** - 所有插件版本信息 (JSON 格式)
- **发布说明** - 包含：
  - 新增/更新的插件列表
  - 相关提交记录
  - 所有插件版本表
  - 安装说明

---

## 发布流程

### 第 1 步：更新插件版本

当您对插件进行更改时，**必须**更新插件文档字符串中的版本号：

```python
"""
title: 我的插件
author: Fu-Jie
version: 0.2.0  # <- 必须更新这里！
...
"""
```

### 第 2 步：创建 PR 并添加更新说明

在 PR 描述中说明更新内容（至少 20 个字符）：

```markdown
## 更新内容

- 新增 XXX 功能
- 修复 YYY 问题
- 优化 ZZZ 性能
```

### 第 3 步：合并 PR

满足检查条件后，合并 PR 到 `main` 分支，系统会自动创建 Release。

---

## 手动发布（可选）

除了自动发布，您也可以手动触发发布：

### 方式 A：手动触发

1. 前往 GitHub Actions → "Plugin Release / 插件发布"
2. 点击 "Run workflow"
3. 填写详细信息：
   - **version**: 例如 `v1.0.0`（留空则自动生成）
   - **release_title**: 例如 "智能思维导图重大更新"
   - **release_notes**: Markdown 格式的附加说明
   - **prerelease**: 如果是预发布版本则勾选

### 方式 B：基于标签的发布

```bash
# 创建并推送版本标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## 版本编号

我们遵循[语义化版本](https://semver.org/lang/zh-CN/)：

- **主版本 (MAJOR)**: 不兼容的 API 变更
- **次版本 (MINOR)**: 向后兼容的新功能
- **补丁版本 (PATCH)**: 向后兼容的 Bug 修复

### 示例

| 变更类型 | 版本变化 |
|---------|---------|
| Bug 修复 | 0.1.0 → 0.1.1 |
| 新功能 | 0.1.1 → 0.2.0 |
| 不兼容变更 | 0.2.0 → 1.0.0 |

---

## GitHub Actions 工作流

### release.yml

**触发条件:**
- ⭐ 推送到 `main` 分支且修改了 `plugins/**/*.py`（自动发布）
- 手动触发 (workflow_dispatch)
- 推送版本标签 (`v*`)

**动作:**
1. 检测与上次 Release 的版本变化
2. 收集更新的插件文件
3. 生成发布说明（含提交记录）
4. 创建 GitHub Release（含可下载附件）

### plugin-version-check.yml

**触发条件:**
- 修改 `plugins/**/*.py` 的 Pull Request

**动作:**
1. 比较基础分支和 PR 的插件版本
2. 检查是否有版本更新
3. 检查 PR 描述是否足够详细
4. ❌ 如果没有版本更新，检查失败
5. ⚠️ 如果 PR 描述过短，检查失败

---

## 脚本使用

### extract_plugin_versions.py

```bash
# 输出到控制台
python scripts/extract_plugin_versions.py

# 输出为 JSON
python scripts/extract_plugin_versions.py --json

# 输出为 Markdown 表格
python scripts/extract_plugin_versions.py --markdown

# 与之前版本比较
python scripts/extract_plugin_versions.py --compare old_versions.json

# 保存到文件
python scripts/extract_plugin_versions.py --json --output versions.json
```

---

## 最佳实践

1. **始终更新版本号** - 对插件进行功能性更改时（必需）
2. **编写清晰的 PR 描述** - 描述更改内容和原因（必需）
3. **本地测试** - 在创建 PR 之前
4. **使用预发布** - 测试新功能
5. **引用 issue** - 在 PR 描述中

---

## 作者

Fu-Jie  
GitHub: [Fu-Jie/awesome-openwebui](https://github.com/Fu-Jie/awesome-openwebui)
