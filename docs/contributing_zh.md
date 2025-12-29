# 贡献指南

感谢你对 **OpenWebUI Extras** 的兴趣！我们欢迎各种形式的贡献，包括插件、提示词、文档等。

---

## 🤝 如何贡献

### 1. 分享提示词

如果你有实用的提示词想要分享：

1. 浏览 `prompts/` 目录并找到合适的分类
2. 如果没有合适的分类，可以新建一个文件夹
3. 创建一个新的 `.md` 文件来编写你的提示词
4. 提交 Pull Request

#### 提示词格式

```markdown
# 提示词名称

简短描述这个提示词的功能。

## 使用场景

说明何时使用这个提示词。

## 提示词内容

\```text
你的提示词内容...
\```

## 使用技巧

使用这个提示词的一些建议和技巧。
```

---

### 2. 开发插件

如果你开发了一个 OpenWebUI 插件：

#### 插件元数据

确保你的插件包含完整的元数据：

```python
"""
title: 插件名称
author: 你的名字
version: 0.1.0
description: 简短描述插件的功能
"""
```

#### 目录结构

将插件放在合适的目录下：

- `plugins/actions/` - Action 插件（消息下方的按钮）
- `plugins/filters/` - Filter 插件（消息处理）
- `plugins/pipes/` - Pipe 插件（自定义模型）
- `plugins/pipelines/` - Pipeline 插件（复杂工作流）

#### 文档

请为你的插件提供文档：

- `README.md` - 英文文档
- `README_CN.md` - 中文文档（可选但推荐）

文档应包含：

- 功能描述
- 安装步骤
- 配置选项
- 使用示例
- 故障排除指南

---

### 3. 改进文档

发现错误或想要改进文档？

1. Fork 仓库
2. 在 `docs/` 目录下进行修改
3. 提交 Pull Request

---

## 🛠️ 开发规范

### 代码风格

- **Python**：遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- **注释**：为复杂逻辑添加注释
- **命名**：使用清晰、描述性的名称

### 测试

提交前请确保：

1. 在本地 OpenWebUI 环境中测试插件
2. 验证所有功能按文档所述正常工作
3. 检查边界情况和错误处理

### 提交信息

使用清晰、描述性的提交信息：

```
Add: 智能思维导图 action 插件
Fix: 上下文压缩 token 计数问题
Update: 插件开发指南添加新示例
```

---

## 📝 提交 Pull Request

### 详细步骤

1. **Fork** 本仓库
2. **克隆**你的 fork 到本地
3. **创建**新分支：
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **进行**修改
5. **提交**你的修改：
   ```bash
   git commit -m 'Add: Amazing feature'
   ```
6. **推送**到你的分支：
   ```bash
   git push origin feature/amazing-feature
   ```
7. **创建** Pull Request

### PR 检查清单

- [ ] 代码遵循项目风格指南
- [ ] 包含/更新了文档
- [ ] 插件已在本地测试通过
- [ ] 提交信息清晰
- [ ] PR 描述说明了所做的更改

---

## 🐛 报告问题

发现了 bug？请创建 issue 并包含以下信息：

1. **描述**：清晰描述问题
2. **复现步骤**：如何触发这个问题
3. **预期行为**：应该发生什么
4. **实际行为**：实际发生了什么
5. **环境信息**：OpenWebUI 版本、浏览器、操作系统

---

## 💡 功能请求

有新想法？我们很乐意听取！

1. 先检查是否已有类似的 issue
2. 创建新 issue 并添加 "enhancement" 标签
3. 描述你的想法和使用场景

---

## 📄 许可证

通过贡献，你同意你的贡献将使用与项目相同的许可证。

---

## 🙏 感谢

每一份贡献，无论大小，都有助于让 OpenWebUI Extras 变得更好。感谢你成为我们社区的一员！

[:fontawesome-brands-github: 在 GitHub 上查看](https://github.com/Fu-Jie/awesome-openwebui){ .md-button .md-button--primary }
