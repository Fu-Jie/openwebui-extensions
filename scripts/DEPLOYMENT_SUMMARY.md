# 📦 Async Context Compression — 本地部署工具 (Local Deployment Tools)

## 🎯 功能概述

为 `async_context_compression` Filter 插件添加了完整的本地部署工具链，支持快速迭代开发无需重启 OpenWebUI。

## 📋 新增文件

### 1. **deploy_filter.py** — Filter 插件部署脚本
- **位置**: `scripts/deploy_filter.py`
- **功能**: 自动部署 Filter 类插件到本地 OpenWebUI 实例
- **特性**:
  - ✅ 从 Python docstring 自动提取元数据
  - ✅ 智能版本号识别（semantic versioning）
  - ✅ 支持多个 Filter 插件管理
  - ✅ 自动更新或创建插件
  - ✅ 详细的错误诊断和连接测试
  - ✅ 列表指令查看所有可用 Filter
- **代码行数**: ~300 行

### 2. **DEPLOYMENT_GUIDE.md** — 完整部署指南
- **位置**: `scripts/DEPLOYMENT_GUIDE.md`
- **内容**:
  - 前置条件和快速开始
  - 脚本详细说明
  - API 密钥获取方法
  - 故障排除指南
  - 分步工作流示例

### 3. **QUICK_START.md** — 快速参考卡片
- **位置**: `scripts/QUICK_START.md`
- **内容**:
  - 一行命令部署
  - 前置步骤
  - 常见命令表格
  - 故障诊断速查表
  - CI/CD 集成示例

### 4. **test_deploy_filter.py** — 单元测试套件
- **位置**: `tests/scripts/test_deploy_filter.py`
- **测试覆盖**:
  - ✅ Filter 文件发现 (3 个测试)
  - ✅ 元数据提取 (3 个测试)
  - ✅ API 负载构建 (4 个测试)
- **测试通过率**: 10/10 ✅

## 🚀 使用方式

### 基本部署（一行命令）

```bash
cd scripts
python deploy_filter.py
```

### 列出所有可用 Filter

```bash
python deploy_filter.py --list
```

### 部署指定 Filter

```bash
python deploy_filter.py folder-memory
python deploy_filter.py context_enhancement_filter
```

## 🔧 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 加载 API 密钥 (.env)                                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 2. 查找 Filter 插件文件                                      │
│    - 从名称推断文件路径                                     │
│    - 支持 hyphen-case 和 snake_case 查找                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 3. 读取 Python 源代码                                        │
│    - 提取 docstring 元数据                                  │
│    - title, version, author, description, openwebui_id      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 4. 构建 API 请求负载                                        │
│    - 组装 manifest 和 meta 信息                             │
│    - 包含完整源代码内容                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 5. 发送请求                                                │
│    - POST /api/v1/functions/id/{id}/update （更新）         │
│    - POST /api/v1/functions/create （创建备用）             │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│ 6. 显示结果和诊断                                           │
│    - ✅ 更新/创建成功                                       │
│    - ❌ 错误信息和解决建议                                  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 支持的 Filter 列表

脚本自动发现以下 Filter：

| Filter 名称 | Python 文件 | 版本 |
|-----------|-----------|------|
| async-context-compression | async_context_compression.py | 1.3.0+ |
| chat-session-mapping-filter | chat_session_mapping_filter.py | 0.1.0+ |
| context_enhancement_filter | context_enhancement_filter.py | 0.3+ |
| folder-memory | folder_memory.py | 0.1.0+ |
| github_copilot_sdk_files_filter | github_copilot_sdk_files_filter.py | 0.1.3+ |
| markdown_normalizer | markdown_normalizer.py | 1.2.8+ |
| web_gemini_multimodel_filter | web_gemini_multimodel_filter.py | 0.3.2+ |

## ⚙️ 技术细节

### 元数据提取

脚本从 Python 文件顶部的 docstring 中提取元数据：

```python
"""
title: Async Context Compression
id: async_context_compression
author: Fu-Jie
author_url: https://github.com/Fu-Jie/openwebui-extensions
funding_url: https://github.com/open-webui
description: Reduces token consumption...
version: 1.3.0
openwebui_id: b1655bc8-6de9-4cad-8cb5-a6f7829a02ce
"""
```

**支持的元数据字段**:
- `title` — Filter 显示名称 ✅
- `id` — 唯一标识符 ✅
- `author` — 作者名称 ✅
- `author_url` — 作者主页链接 ✅
- `funding_url` — 项目链接 ✅
- `description` — 功能描述 ✅
- `version` — 语义化版本号 ✅
- `openwebui_id` — OpenWebUI UUID （可选）

### API 集成

脚本使用 OpenWebUI REST API：

```
POST /api/v1/functions/id/{filter_id}/update
- 更新现有 Filter
- HTTP 200: 更新成功
- HTTP 404: Filter 不存在，自动尝试创建

POST /api/v1/functions/create
- 创建新 Filter
- HTTP 200: 创建成功
```

**认证**: Bearer token (API 密钥方式)

## 🔐 安全性

### API 密钥管理

```bash
# 1. 创建 .env 文件
echo "api_key=sk-your-key-here" > scripts/.env

# 2. 将 .env 添加到 .gitignore
echo "scripts/.env" >> .gitignore

# 3. 不要提交 API 密钥
git add scripts/.gitignore
git commit -m "chore: add .env to gitignore"
```

### 最佳实践

- ✅ 使用长期认证令牌（而不是短期 JWT）
- ✅ 定期轮换 API 密钥
- ✅ 限制密钥权限范围
- ✅ 在可信网络中使用
- ✅ 生产环境使用 CI/CD 秘密管理

## 🧪 测试验证

### 运行测试套件

```bash
pytest tests/scripts/test_deploy_filter.py -v
```

### 测试覆盖范围

```
✅ TestFilterDiscovery (3 个测试)
   - test_find_async_context_compression
   - test_find_nonexistent_filter
   - test_find_filter_with_underscores

✅ TestMetadataExtraction (3 个测试)
   - test_extract_metadata_from_async_compression
   - test_extract_metadata_empty_file
   - test_extract_metadata_multiline_docstring

✅ TestPayloadBuilding (4 个测试)
   - test_build_filter_payload_basic
   - test_payload_has_required_fields
   - test_payload_with_openwebui_id

✅ TestVersionExtraction (1 个测试)
   - test_extract_valid_version

结果: 10/10 通过 ✅
```

## 💡 常见用例

### 用例 1: 修复 Bug 后快速测试

```bash
# 1. 修改代码
vim plugins/filters/async-context-compression/async_context_compression.py

# 2. 立即部署（不需要重启 OpenWebUI）
cd scripts && python deploy_filter.py

# 3. 在 OpenWebUI 中测试修复
# 4. 重复迭代（返回步骤 1）
```

### 用例 2: 开发新的 Filter

```bash
# 1. 创建新 Filter 目录
mkdir plugins/filters/my-new-filter

# 2. 编写代码（包含必要的 docstring 元数据）
cat > plugins/filters/my-new-filter/my_new_filter.py << 'EOF'
"""
title: My New Filter
author: Your Name
version: 1.0.0
description: Filter description
"""

class Filter:
    # ... implementation ...
EOF

# 3. 首次部署（创建）
cd scripts && python deploy_filter.py my-new-filter

# 4. 在 OpenWebUI UI 测试
# 5. 重复更新
cd scripts && python deploy_filter.py my-new-filter
```

### 用例 3: 版本更新和发布

```bash
# 1. 更新版本号
vim plugins/filters/async-context-compression/async_context_compression.py
# 修改: version: 1.3.0 → version: 1.4.0

# 2. 部署新版本
cd scripts && python deploy_filter.py

# 3. 测试通过后提交
git add plugins/filters/async-context-compression/
git commit -m "feat(filters): update async-context-compression to 1.4.0"
git push
```

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Deploy Filter on Release

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Deploy Filter
        run: |
          cd scripts
          python deploy_filter.py async-context-compression
        env:
          api_key: ${{ secrets.OPENWEBUI_API_KEY }}
```

## 📚 参考文档

- [完整部署指南](DEPLOYMENT_GUIDE.md)
- [快速参考卡片](QUICK_START.md)
- [测试套件](../tests/scripts/test_deploy_filter.py)
- [插件开发指南](../docs/development/plugin-guide.md)
- [OpenWebUI 文档](https://docs.openwebui.com/)

## 🎓 学习资源

### 架构理解

```
OpenWebUI 系统设计
    ↓
Filter 插件类型定义
    ↓
REST API 接口 (/api/v1/functions)
    ↓
本地部署脚本实现 (deploy_filter.py)
    ↓
元数据提取和投递
```

### 调试技巧

1. **启用详细日志**:
   ```bash
   python deploy_filter.py 2>&1 | tee deploy.log
   ```

2. **测试 API 连接**:
   ```bash
   curl -X GET http://localhost:3003/api/v1/functions \
     -H "Authorization: Bearer $API_KEY"
   ```

3. **验证 .env 文件**:
   ```bash
   grep "api_key=" scripts/.env
   ```

## 📞 故障排除

| 问题 | 诊断 | 解决方案 |
|------|------|----------|
| Connection error | OpenWebUI 地址/端口不对 | 检查 localhost:3003；修改 URL 如需要 |
| .env not found | 未创建配置文件 | `echo "api_key=sk-..." > scripts/.env` |
| Filter not found | 插件名称错误 | 运行 `python deploy_filter.py --list` |
| Status 401 | API 密钥无效/过期 | 更新 `.env` 中的密钥 |
| Status 500 | 服务器错误 | 检查 OpenWebUI 服务日志 |

## ✨ 特色功能

| 特性 | 描述 |
|------|------|
| 🔍 自动发现 | 自动查找所有 Filter 插件 |
| 📊 元数据提取 | 从代码自动提取版本和元数据 |
| ♻️ 自动更新 | 智能处理更新或创建 |
| 🛡️ 错误处理 | 详细的错误提示和诊断信息 |
| 🚀 快速迭代 | 秒级部署，无需重启 |
| 🧪 完整测试 | 10 个单元测试覆盖核心功能 |

---

**最后更新**: 2026-03-09  
**作者**: Fu-Jie  
**项目**: [openwebui-extensions](https://github.com/Fu-Jie/openwebui-extensions)
