# ⚡ 快速部署参考 (Quick Deployment Reference)

## 一行命令部署

```bash
# 部署 async_context_compression Filter（默认）
cd scripts && python deploy_filter.py

# 列出所有可用 Filter
cd scripts && python deploy_filter.py --list
```

## 前置步骤（仅需一次）

```bash
# 1. 进入 scripts 目录
cd scripts

# 2. 创建 .env 文件，包含 OpenWebUI API 密钥
echo "api_key=sk-your-api-key-here" > .env

# 3. 确保 OpenWebUI 运行在 localhost:3003
```

## 获取 API 密钥

1. 打开 OpenWebUI → 用户头像 → Settings
2. 找到 "API Keys" 部分
3. 复制密钥（sk-开头）
4. 粘贴到 `.env` 文件

## 部署流程

```bash
# 1. 编辑插件代码
vim ../plugins/filters/async-context-compression/async_context_compression.py

# 2. 部署到本地
python deploy_filter.py

# 3. 在 OpenWebUI 测试（无需重启）

# 4. 重复部署（自动覆盖）
python deploy_filter.py
```

## 常见命令

| 命令 | 说明 |
|------|------|
| `python deploy_filter.py` | 部署 async_context_compression |
| `python deploy_filter.py filter-name` | 部署指定 Filter |
| `python deploy_filter.py --list` | 列出所有可用 Filter |
| `python deploy_pipe.py` | 部署 GitHub Copilot SDK Pipe |

## 故障诊断

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| Connection error | OpenWebUI 未运行 | 启动 OpenWebUI 或检查端口 |
| .env not found | 未创建配置文件 | `echo "api_key=sk-..." > .env` |
| Filter not found | Filter 名称错误 | 运行 `python deploy_filter.py --list` |
| Status 401 | API 密钥无效 | 更新 `.env` 中的密钥 |

## 文件位置

```
openwebui-extensions/
├── scripts/
│   ├── deploy_filter.py        ← Filter 部署工具
│   ├── deploy_pipe.py          ← Pipe 部署工具
│   ├── .env                    ← API 密钥（不提交）
│   └── DEPLOYMENT_GUIDE.md     ← 完整指南
│
└── plugins/
    └── filters/
        └── async-context-compression/
            ├── async_context_compression.py
            ├── README.md
            └── README_CN.md
```

## 工作流建议

### 快速迭代开发

```bash
# Terminal 1: 启动 OpenWebUI（如果未运行）
docker run -d -p 3003:8080 ghcr.io/open-webui/open-webui:latest

# Terminal 2: 开发环节（重复执行）
cd scripts
code ../plugins/filters/async-context-compression/  # 编辑代码
python deploy_filter.py                             # 部署
# → 在 OpenWebUI 测试
# → 返回编辑，重复
```

### CI/CD 集成

```bash
# 在 GitHub Actions 中
- name: Deploy filter to staging
  run: |
    cd scripts
    python deploy_filter.py async-context-compression
  env:
    api_key: ${{ secrets.OPENWEBUI_API_KEY }}
```

---

📚 **更多帮助**: 查看 `DEPLOYMENT_GUIDE.md`
