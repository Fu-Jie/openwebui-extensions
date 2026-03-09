# 🚀 本地部署脚本指南 (Local Deployment Guide)

## 概述

本目录包含用于将开发中的插件部署到本地 OpenWebUI 实例的自动化脚本。它们可以快速推送代码更改而无需重启 OpenWebUI。

## 前置条件

1. **OpenWebUI 运行中**: 确保 OpenWebUI 在本地运行（默认 `http://localhost:3003`）
2. **API 密钥**: 需要一个有效的 OpenWebUI API 密钥
3. **环境文件**: 在此目录创建 `.env` 文件，包含 API 密钥：
   ```
   api_key=sk-xxxxxxxxxxxxx
   ```

## 快速开始

### 部署 Pipe 插件

```bash
# 部署 GitHub Copilot SDK Pipe
python deploy_pipe.py
```

### 部署 Filter 插件

```bash
# 部署 async_context_compression Filter（默认）
python deploy_filter.py

# 部署指定的 Filter 插件
python deploy_filter.py my-filter-name

# 列出所有可用的 Filter
python deploy_filter.py --list
```

## 脚本说明

### `deploy_filter.py` — Filter 插件部署工具

用于部署 Filter 类型的插件（如消息过滤、上下文压缩等）。

**主要特性**:
- ✅ 从 Python 文件自动提取元数据（版本、作者、描述等）
- ✅ 尝试更新现有插件，若不存在则创建新插件
- ✅ 支持多个 Filter 插件管理
- ✅ 详细的错误提示和连接诊断

**用法**:
```bash
# 默认部署 async_context_compression
python deploy_filter.py

# 部署其他 Filter
python deploy_filter.py async-context-compression
python deploy_filter.py workflow-guide

# 列出所有可用 Filter
python deploy_filter.py --list
python deploy_filter.py -l
```

**工作流程**:
1. 从 `.env` 加载 API 密钥
2. 查找目标 Filter 插件目录
3. 读取 Python 源文件
4. 从 docstring 提取元数据（title, version, author, description, etc.）
5. 构建 API 请求负载
6. 发送更新请求到 OpenWebUI
7. 若更新失败，自动尝试创建新插件
8. 显示结果和诊断信息

### `deploy_pipe.py` — Pipe 插件部署工具

用于部署 Pipe 类型的插件（如 GitHub Copilot SDK）。

**使用**:
```bash
python deploy_pipe.py
```

## 获取 API 密钥

### 方法 1: 使用现有用户令牌（推荐）

1. 打开 OpenWebUI 界面
2. 点击用户头像 → Settings（设置）
3. 找到 API Keys 部分
4. 复制你的 API 密钥（sk-开头）
5. 粘贴到 `.env` 文件中

### 方法 2: 创建长期 API 密钥

在 OpenWebUI 设置中创建专用于部署的长期 API 密钥。

## 故障排除

### "Connection error: Could not reach OpenWebUI at localhost:3003"

**原因**: OpenWebUI 未运行或端口不同

**解决方案**:
- 确保 OpenWebUI 正在运行
- 检查 OpenWebUI 实际监听的端口（通常是 3000 或 3003）
- 根据需要编辑脚本中的 URL

### ".env file not found"

**原因**: 未创建 `.env` 文件

**解决方案**:
```bash
echo "api_key=sk-your-api-key-here" > .env
```

### "Filter 'xxx' not found"

**原因**: Filter 目录名不正确

**解决方案**:
```bash
# 列出所有可用的 Filter
python deploy_filter.py --list
```

### "Failed to update or create. Status: 401"

**原因**: API 密钥无效或过期

**解决方案**:
1. 验证 API 密钥的有效性
2. 获取新的 API 密钥
3. 更新 `.env` 文件

## 工作流示例

### 开发并部署新的 Filter

```bash
# 1. 在 plugins/filters/ 创建新的 Filter 目录
mkdir plugins/filters/my-new-filter

# 2. 创建 my_new_filter.py 文件，包含必要的元数据：
# """
# title: My New Filter
# author: Your Name
# version: 1.0.0
# description: Filter description
# """

# 3. 部署到本地 OpenWebUI
cd scripts
python deploy_filter.py my-new-filter

# 4. 在 OpenWebUI UI 中测试插件

# 5. 继续迭代开发
# ... 修改代码 ...

# 6. 重新部署（自动覆盖）
python deploy_filter.py my-new-filter
```

### 修复 Bug 并快速部署

```bash
# 1. 修改源代码
# vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. 立即部署到本地
python deploy_filter.py async-context-compression

# 3. 在 OpenWebUI 中测试修复
# （无需重启 OpenWebUI）
```

## 安全注意事项

⚠️ **重要**: 
- ✅ 将 `.env` 文件添加到 `.gitignore`（避免提交敏感信息）
- ✅ 不要在版本控制中提交 API 密钥
- ✅ 仅在可信的网络环境中使用
- ✅ 定期轮换 API 密钥

## 文件结构

```
scripts/
├── deploy_filter.py        # Filter 插件部署工具
├── deploy_pipe.py          # Pipe 插件部署工具
├── .env                    # API 密钥（本地，不提交）
├── README.md               # 本文件
└── ...
```

## 参考资源

- [OpenWebUI 文档](https://docs.openwebui.com/)
- [插件开发指南](../docs/development/plugin-guide.md)
- [Filter 插件示例](../plugins/filters/)

---

**最后更新**: 2026-03-09  
**作者**: Fu-Jie
