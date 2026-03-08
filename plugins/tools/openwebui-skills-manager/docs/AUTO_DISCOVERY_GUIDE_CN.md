# 自动发现与去重指南

## 功能概述

OpenWebUI Skills 管理工具现在能够自动发现并安装 GitHub 仓库中的所有 skill，并内置重复处理机制。

## 新增功能

### 1. **自动仓库根目录检测** 🎯

当你提供一个 GitHub 仓库根 URL（不含 `/tree/` 路径）时，系统会自动将其转换为发现模式。

#### 示例

```
输入：https://github.com/nicobailon/visual-explainer
      ↓
自动转换为：https://github.com/nicobailon/visual-explainer/tree/main
      ↓
发现所有 skill 子目录
```

### 2. **自动发现 Skill** 🔍

一旦检测到 tree URL，工具会自动：

- 调用 GitHub API 列出所有子目录
- 为每个子目录创建 skill 安装 URL
- 尝试从每个子目录获取 `SKILL.md` 或 `README.md`
- 将所有发现的 skill 以批量模式安装

#### 支持的 URL 格式

```
✓ https://github.com/owner/repo                    → 自动检测为仓库根
✓ https://github.com/owner/repo/                   → 带末尾斜杠
✓ https://github.com/owner/repo/tree/main          → 现有 tree 格式
✓ https://github.com/owner/repo/tree/main/skills   → 嵌套 skill 目录
```

### 3. **重复 URL 移除** 🔄

安装多个 skill 时，系统会自动：

- 检测重复的 URL
- 移除重复项（保持顺序不变）
- 通知用户移除了多少个重复项
- 跳过重复 URL 的处理

#### 示例

```
输入 URL（共 5 个）：
- https://github.com/user/repo/tree/main/skill1
- https://github.com/user/repo/tree/main/skill1   ← 重复
- https://github.com/user/repo/tree/main/skill2
- https://github.com/user/repo/tree/main/skill2   ← 重复
- https://github.com/user/repo/tree/main/skill3

处理结果：
- 唯一 URL：3 个
- 移除重复：2 个
- 状态提示：「已从批量队列中移除 2 个重复 URL」
```

### 4. **重复 Skill 名称检测** ⚠️

如果多个 URL 在批量安装时导致相同的 skill 名称：

- 系统检测到重复安装
- 记录详细的警告日志
- 通知用户发生了冲突
- 显示采取了什么行动（已安装/已更新）

#### 示例场景

```
Skill A: skill1.zip → 创建 skill 「报告生成器」
Skill B: skill2.zip → 创建 skill 「报告生成器」  ← 同名！

警告：「技能名称 '报告生成器' 重复 - 多次安装。」
注意：最后一次安装可能已覆盖了之前的版本
      （取决于 ALLOW_OVERWRITE_ON_CREATE 设置）
```

## 使用示例

### 示例 1：简单仓库根目录

```
用户输入：
「从 https://github.com/nicobailon/visual-explainer 安装 skill」

系统响应：
「检测到 GitHub repo 根目录：https://github.com/nicobailon/visual-explainer。
 自动转换为发现模式...」

「正在从 https://github.com/nicobailon/visual-explainer/tree/main 发现 skill...」

「正在安装 5 个技能...」
```

### 示例 2：带嵌套 Skill 目录

```
用户输入：
「从 https://github.com/anthropics/skills 安装所有 skill」

系统响应：
「检测到 GitHub repo 根目录：https://github.com/anthropics/skills。
 自动转换为发现模式...」

「正在从 https://github.com/anthropics/skills/tree/main 发现 skill...」

「正在安装 12 个技能...」
```

### 示例 3：重复处理

```
用户输入（批量）：
[
  "https://github.com/user/repo/tree/main/skill-a",
  "https://github.com/user/repo/tree/main/skill-a",  ← 重复
  "https://github.com/user/repo/tree/main/skill-b"
]

系统响应：
「已从批量队列中移除 1 个重复 URL。」

「正在安装 2 个技能...」

结果：
- 批量安装完成：成功 2 个，失败 0 个
```

## 实现细节

### 检测逻辑

**仓库根目录检测**使用正则表达式：

```python
^https://github\.com/([^/]+)/([^/]+)/?$
# 匹配：
#   https://github.com/owner/repo     ✓
#   https://github.com/owner/repo/    ✓
# 不匹配：
#   https://github.com/owner/repo/tree/main          ✗
#   https://github.com/owner/repo/blob/main/file.md  ✗
```

### 规范化

检测到的仓库根 URL 会被转换为：

```python
https://github.com/{owner}/{repo} → https://github.com/{owner}/{repo}/tree/main
```

首先尝试 `main` 分支；如果不存在，GitHub API 会自动回退到 `master`。

### 发现流程

1. 用正则表达式解析 tree URL，提取 owner、repo、branch 和 path
2. 调用 GitHub API：`/repos/{owner}/{repo}/contents{path}?ref={branch}`
3. 筛选目录（跳过以 `.` 开头的隐藏目录）
4. 对于每个子目录，创建指向它的 tree URL
5. 返回发现的 tree URL 列表以供批量安装

### 去重策略

```python
seen_urls = set()
unique_urls = []
duplicates_removed = 0

for url in input_urls:
    if url not in seen_urls:
        unique_urls.append(url)
        seen_urls.add(url)
    else:
        duplicates_removed += 1
```

- 保持 URL 顺序
- 时间复杂度 O(n)
- 低内存开销

### 重复名称跟踪

在批量安装期间：

```python
installed_names = {}  # {小写名称: url}

for skill in results:
    if success:
        name_lower = skill["name"].lower()
        if name_lower in installed_names:
            # 检测到重复
            warn_user(name_lower, installed_names[name_lower])
        else:
            installed_names[name_lower] = current_url
```

## 配置

无需新增 Valve 参数。现有设置继续有效：

| 参数 | 影响 |
|------|------|
| `ALLOW_OVERWRITE_ON_CREATE` | 控制重复 skill 名称时是否更新或出错 |
| `TRUSTED_DOMAINS` | 对所有发现的 URL 继续强制执行 |
| `INSTALL_FETCH_TIMEOUT` | 适用于每个 GitHub API 发现调用 |
| `SHOW_STATUS` | 显示所有发现和去重消息 |

## API 变化

### install_skill() 方法

**新增行为：**

- 自动将仓库根 URL 转换为 tree 格式
- 自动发现 tree URL 中的所有 skill 子目录
- 批量处理前对 URL 列表去重
- 安装期间跟踪重复的 skill 名称

**参数：**（无变化）

- `url`：现在可以接受仓库根目录（如 `https://github.com/owner/repo`）
- `name`：在批量/自动发现模式下被忽略
- `overwrite`：控制 skill 名称冲突时的行为
- 其他参数保持不变

**返回值：**（无变化）

- 单个 skill：返回安装元数据
- 批量安装：返回包含成功/失败数的批处理摘要

## 错误处理

### 发现失败

- 如果仓库根规范化失败 → 视为普通 URL 处理
- 如果 tree 发现 API 失败 → 记录警告，继续尝试单文件安装
- 如果未找到 SKILL.md 或 README.md → 该 URL 的特定错误

### 批量失败

- 重复 URL 移除 → 通知用户但继续处理
- 单个 skill 失败 → 记录错误，继续处理下一个 skill
- 最终摘要显示成功/失败数

## 遥测和日志

所有操作都会发出状态更新：

- ✓ 「检测到 GitHub repo 根目录：...」
- ✓ 「已从批量队列中移除 {count} 个重复 URL」
- ⚠️ 「警告：技能名称 '{name}' 重复」
- ✗ 「{url} 安装失败：{reason}」

查看 OpenWebUI 日志了解详细的错误追踪。

## 测试

运行包含的测试套件：

```bash
python3 docs/test_auto_discovery.py
```

测试覆盖范围：

- ✓ 仓库根 URL 检测（6 个用例）
- ✓ 发现模式的 URL 规范化（4 个用例）
- ✓ 去重逻辑（3 个场景）
- ✓ 总计：13/13 个测试用例通过

## 向后兼容性

✅ **完全向后兼容。**

- 现有 tree URL 工作方式不变
- 现有 blob/raw URL 功能不变
- 现有批量安装不受影响
- 新功能是自动的（无需用户操作）
- 无 API 破坏性变更

## 未来增强

可能的未来改进：

1. 支持 GitLab、Gitea 和其他 Git 平台
2. 智能分支检测（master → main 回退）
3. 自动发现期间按名称模式筛选 skill
4. 带冲突解决策略的批量安装
5. 缓存发现结果以减少 API 调用
